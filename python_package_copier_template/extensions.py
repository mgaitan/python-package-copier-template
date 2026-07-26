"""Jinja extensions and filters used while rendering the template."""

import platform
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from jinja2 import Environment
from jinja2.ext import Extension

_UPDATE_MODE: ContextVar[bool] = ContextVar("copier_template_update_mode", default=False)
MAX_PYPI_SUFFIX = 50
MIN_PROJECT_PYTHON = (3, 12)


class UnsupportedPythonError(RuntimeError):
    """Raised when Copier runs below the generated project's Python minimum."""

    def __init__(self, minimum: str, running: str) -> None:
        """Describe the required and running Python versions."""
        super().__init__(
            f"Python {minimum} or newer is required to generate a project; Copier is running on Python {running}."
        )


@contextmanager
def update_mode() -> Iterator[None]:
    """Mark the current execution context as an update operation."""
    token = _UPDATE_MODE.set(True)
    try:
        yield
    finally:
        _UPDATE_MODE.reset(token)


def git_user_name(default: str) -> str:
    """Return the configured Git author name or a fallback."""
    return _git_config_value("user.name", default)


def git_user_email(default: str) -> str:
    """Return the configured Git author email or a fallback."""
    return _git_config_value("user.email", default)


def _git_config_value(key: str, default: str) -> str:
    if not (git := shutil.which("git")):
        return default

    try:
        completed = subprocess.run(  # noqa: S603 - arguments are passed without a shell
            [git, "config", key],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return default

    return completed.stdout.strip() or default


def gh_user_login(default: str) -> str:
    """Return the authenticated GitHub username via the GH CLI when available."""
    if not (gh := shutil.which("gh")):
        return default

    try:
        completed = subprocess.run(  # noqa: S603 - arguments are passed without a shell
            [gh, "api", "user", "-q", ".login"],
            check=True,
            capture_output=True,
            text=True,
        )
        login = completed.stdout.strip()
        if login:
            return login
    except subprocess.CalledProcessError:
        return default

    return default


def command_available(command: str) -> bool:
    """Return True if the command exists on PATH."""
    return shutil.which(command) is not None


def slugify(value: object, separator: str = "-") -> str:
    """Normalize a value for use in package and repository names."""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", separator, value).strip("-_")


def path_exists(path: str) -> bool:
    """Return True when ``path`` exists relative to the destination."""
    return Path(path).expanduser().exists()


def is_update(defaults: bool | None = None) -> bool:  # noqa: FBT001 - Jinja filters receive positional values
    """Return True when running under `copier update`."""
    return bool(defaults)


def pypi_distribution_exists(name: str) -> bool:
    """Return True if a distribution with ``name`` is present on PyPI.

    Uses the lightweight JSON endpoint and handles network failures gracefully
    by treating them as "not found" so template execution is not blocked.
    """
    # During updates we keep the previously selected distribution name and
    # should not block on global PyPI availability checks.
    if _UPDATE_MODE.get():
        return False

    if not name:
        return False

    url = f"https://pypi.org/pypi/{name}/json"
    request = urllib.request.Request(url, method="HEAD")  # noqa: S310 - URL is a fixed HTTPS PyPI endpoint
    try:
        with urllib.request.urlopen(request, timeout=3):  # noqa: S310 - request URL is restricted above
            return True
    except (urllib.error.HTTPError, OSError):
        return False


def suggest_pypi_distribution_name(name: str) -> str:
    """Return a PyPI-safe distribution name, adding a suffix if needed."""
    base = slugify(name)
    if not base:
        base = "package"

    candidate = base
    for suffix in range(1, MAX_PYPI_SUFFIX + 1):
        if not pypi_distribution_exists(candidate):
            return candidate
        candidate = f"{base}-{suffix}"
    return candidate


class GitExtension(Extension):
    """Register Git, GitHub, command, and path filters."""

    def __init__(self, environment: Environment) -> None:
        """Register filters in a Jinja environment."""
        super().__init__(environment)
        environment.filters["git_user_name"] = git_user_name
        environment.filters["git_user_email"] = git_user_email
        environment.filters["gh_user_login"] = gh_user_login
        environment.filters["command_available"] = command_available
        environment.filters["path_exists"] = path_exists
        environment.filters["is_update"] = is_update


class SlugifyExtension(Extension):
    """Register slug and PyPI name filters."""

    def __init__(self, environment: Environment) -> None:
        """Register filters in a Jinja environment."""
        super().__init__(environment)
        environment.filters["slugify"] = slugify
        environment.filters["pypi_exists"] = pypi_distribution_exists
        environment.filters["pypi_suggest_name"] = suggest_pypi_distribution_name


class CurrentYearExtension(Extension):
    """Expose the current UTC year to templates."""

    def __init__(self, environment: Environment) -> None:
        """Register the current year in a Jinja environment."""
        super().__init__(environment)
        cast("dict[str, object]", environment.globals)["current_year"] = datetime.now(tz=UTC).year


class PythonVersionExtension(Extension):
    """Expose the running Python version to templates."""

    def __init__(self, environment: Environment) -> None:
        """Register the running Python version in a Jinja environment."""
        super().__init__(environment)
        running_python = (sys.version_info.major, sys.version_info.minor)
        if running_python < MIN_PROJECT_PYTHON:
            minimum = ".".join(str(part) for part in MIN_PROJECT_PYTHON)
            raise UnsupportedPythonError(minimum, platform.python_version())
        cast("dict[str, object]", environment.globals)["python_version"] = platform.python_version()
