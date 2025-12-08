from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
import unicodedata
from datetime import date

from jinja2.ext import Extension


def git_user_name(default: str) -> str:
    return subprocess.getoutput("git config user.name").strip() or default


def git_user_email(default: str) -> str:
    return subprocess.getoutput("git config user.email").strip() or default


def gh_user_login(default: str) -> str:
    """Return the authenticated GitHub username via the GH CLI when available."""

    try:
        completed = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            check=True,
            capture_output=True,
            text=True,
        )
        login = completed.stdout.strip()
        if login:
            return login
    except (FileNotFoundError, subprocess.CalledProcessError):
        return default

    return default


def slugify(value, separator="-"):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", separator, value).strip("-_")


def pypi_distribution_exists(name: str) -> bool:
    """Return True if a distribution with ``name`` is present on PyPI.

    Uses the lightweight JSON endpoint and handles network failures gracefully
    by treating them as "not found" so template execution is not blocked.
    """

    if not name:
        return False

    url = f"https://pypi.org/pypi/{name}/json"
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=3):
            return True
    except (urllib.error.HTTPError, OSError):
        return False


def suggest_pypi_distribution_name(name: str) -> str:
    """Return a PyPI-safe distribution name, adding a suffix if needed."""

    base = slugify(name)
    if not base:
        base = "package"

    candidate = base
    suffix = 1
    while pypi_distribution_exists(candidate) and suffix < 50:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


class GitExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["git_user_name"] = git_user_name
        environment.filters["git_user_email"] = git_user_email
        environment.filters["gh_user_login"] = gh_user_login


class SlugifyExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["slugify"] = slugify
        environment.filters["pypi_exists"] = pypi_distribution_exists
        environment.filters["pypi_suggest_name"] = suggest_pypi_distribution_name


class CurrentYearExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["current_year"] = date.today().year
