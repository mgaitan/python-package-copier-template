import os
import platform
import subprocess
import tomllib
import urllib.error
from email.message import Message
from importlib.metadata import PackageNotFoundError
from pathlib import Path

from python_package_copier_template import cli, extensions

REQUIRED_RUFF_SELECTORS = {
    "E",
    "F",
    "FBT",
    "S",
    "G",
    "FLY",
    "N",
    "YTT",
    "DTZ",
    "INT",
    "LOG",
    "PYI",
    "PT",
    "TC",
    "PTH",
    "D",
    "PGH",
}


def render_from_clean_template(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    template_src = Path(__file__).resolve().parent.parent
    clean_template = tmp_path / "template-src"
    subprocess.run(["git", "clone", str(template_src), str(clean_template)], check=True)
    monkeypatch.setattr(
        cli,
        "resolve_template_target",
        lambda: cli.TemplateTarget(src_path=str(clean_template)),
    )
    monkeypatch.setenv("COPIER_TEMPLATE_DEFAULTS", "1")
    monkeypatch.setattr(extensions, "command_available", lambda command: command != "prek")

    dest = tmp_path / "proj"
    cli.main([str(dest)])
    return dest, clean_template


def test_cli_copy_and_update(tmp_path: Path, monkeypatch) -> None:
    dest, _ = render_from_clean_template(tmp_path, monkeypatch)
    project_exists_on_pypi = False

    # First run: copy should create the project (defaults provided via env).
    class _DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(_request, timeout):
        if project_exists_on_pypi:
            return _DummyResponse()
        raise urllib.error.HTTPError("", 404, "not found", Message(), None)

    monkeypatch.setattr(extensions.urllib.request, "urlopen", _fake_urlopen)
    answers_file = dest / ".copier-answers.yml"
    assert answers_file.exists()

    # Initialize git so update is allowed.
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "init", "-b", "main"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "add", "."], cwd=dest, check=True, env=env)
    subprocess.run(["git", "commit", "-m", "init"], cwd=dest, check=True, env=env)

    # Second run: update should still succeed even if the saved distribution
    # name now exists on PyPI.
    project_exists_on_pypi = True
    cli.main([str(dest)])


def test_generated_project_files_do_not_keep_jinja_markers(tmp_path: Path, monkeypatch) -> None:
    dest, _ = render_from_clean_template(tmp_path, monkeypatch)

    assert (dest / ".python-version").read_text(encoding="utf-8").strip() == platform.python_version()
    for relative_path in ("README.md", "pyproject.toml", "docs/index.md"):
        text = (dest / relative_path).read_text(encoding="utf-8")
        assert "{{" not in text
        assert "{%" not in text
        assert "%}" not in text


def test_ruff_rules_include_defaults_and_requested_families() -> None:
    template_root = Path(__file__).resolve().parent.parent
    root_config = tomllib.loads((template_root / "pyproject.toml").read_text(encoding="utf-8"))
    assert set(root_config["tool"]["ruff"]["lint"]["select"]) >= REQUIRED_RUFF_SELECTORS

    generated_template = (template_root / "project/pyproject.toml.jinja").read_text(encoding="utf-8")
    for selector in REQUIRED_RUFF_SELECTORS:
        assert f'"{selector}"' in generated_template


def test_update_preserves_existing_docs_and_adds_new_pages(tmp_path: Path, monkeypatch) -> None:
    dest, clean_template = render_from_clean_template(tmp_path, monkeypatch)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }

    readme = dest / "README.md"
    configuration = dest / "docs/configuration.md"
    python_version = dest / ".python-version"
    readme.write_text("# Custom project\n", encoding="utf-8")
    configuration.write_text("# Custom configuration\n", encoding="utf-8")
    python_version.write_text("3.12.9\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "add", "."], cwd=dest, check=True, env=env)
    subprocess.run(["git", "commit", "-m", "customize docs"], cwd=dest, check=True, env=env)

    new_page = clean_template / "project/docs/new_guide.md.jinja"
    new_page.write_text("# New guide\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=clean_template, check=True, env=env)
    subprocess.run(
        ["git", "commit", "-m", "add a new documentation page"],
        cwd=clean_template,
        check=True,
        env=env,
    )
    with extensions.update_mode():
        cli.run_update(
            dst_path=str(dest),
            defaults=True,
            unsafe=True,
            overwrite=True,
            skip_answered=True,
            vcs_ref="HEAD",
        )

    assert readme.read_text(encoding="utf-8") == "# Custom project\n"
    assert configuration.read_text(encoding="utf-8") == "# Custom configuration\n"
    assert python_version.read_text(encoding="utf-8") == "3.12.9\n"
    assert (dest / "docs/new_guide.md").read_text(encoding="utf-8") == "# New guide\n"


def test_prek_task_runs_on_update_even_with_defaults() -> None:
    copier_yml = Path(__file__).resolve().parent.parent / "copier.yml"
    content = copier_yml.read_text(encoding="utf-8")

    expected_when = (
        "{{ ((((not (defaults | default(false))) and (not '.git' | path_exists)) "
        "or (_copier_operation == 'update')) and ('prek' | command_available)) }}"
    )
    assert expected_when in content


def test_pypi_suggestion_does_not_return_a_known_existing_name(monkeypatch) -> None:
    checked: list[str] = []

    def exists(name: str) -> bool:
        checked.append(name)
        return True

    monkeypatch.setattr(extensions, "MAX_PYPI_SUFFIX", 3)
    monkeypatch.setattr(extensions, "pypi_distribution_exists", exists)

    assert extensions.suggest_pypi_distribution_name("package") == "package-3"
    assert checked == ["package", "package-1", "package-2"]


def test_github_setup_enables_immutable_releases() -> None:
    copier_yml = Path(__file__).resolve().parent.parent / "copier.yml"
    content = copier_yml.read_text(encoding="utf-8")

    assert '"X-GitHub-Api-Version: 2026-03-10"' in content
    assert '"repos/${repo}/immutable-releases"' in content


def test_resolve_template_target_uses_package_version_for_registry_installs(monkeypatch) -> None:
    class _DummyDistribution:
        version = "0.4.2"

        @staticmethod
        def read_text(name: str) -> str | None:
            assert name == "direct_url.json"
            return None

    monkeypatch.setattr(cli, "distribution", lambda _: _DummyDistribution())

    target = cli.resolve_template_target()

    assert target == cli.TemplateTarget(src_path=cli.TEMPLATE_SRC, vcs_ref="0.4.2")


def test_resolve_template_target_uses_commit_for_vcs_installs(monkeypatch) -> None:
    class _DummyDistribution:
        version = "0.4.2"

        @staticmethod
        def read_text(name: str) -> str | None:
            assert name == "direct_url.json"
            return (
                '{"url":"https://github.com/mgaitan/python-package-copier-template",'
                '"vcs_info":{"vcs":"git","requested_revision":"main","commit_id":"abc123"}}'
            )

    monkeypatch.setattr(cli, "distribution", lambda _: _DummyDistribution())

    target = cli.resolve_template_target()

    assert target == cli.TemplateTarget(src_path=cli.TEMPLATE_SRC, vcs_ref="abc123")


def test_resolve_template_target_uses_local_checkout_for_file_installs(monkeypatch) -> None:
    class _DummyDistribution:
        version = "0.4.2"

        @staticmethod
        def read_text(name: str) -> str | None:
            assert name == "direct_url.json"
            return '{"url":"file:///tmp/python-package-copier-template","dir_info":{"editable":true}}'

    monkeypatch.setattr(cli, "distribution", lambda _: _DummyDistribution())
    monkeypatch.setattr(cli, "get_local_git_head", lambda path: "def456")

    target = cli.resolve_template_target()

    assert target == cli.TemplateTarget(
        src_path="/tmp/python-package-copier-template",
        vcs_ref="def456",
    )


def test_resolve_template_target_falls_back_to_plain_path_for_non_git_file_installs(monkeypatch) -> None:
    class _DummyDistribution:
        version = "0.4.2"

        @staticmethod
        def read_text(name: str) -> str | None:
            assert name == "direct_url.json"
            return '{"url":"file:///tmp/python-package-copier-template","dir_info":{"editable":true}}'

    monkeypatch.setattr(cli, "distribution", lambda _: _DummyDistribution())
    monkeypatch.setattr(cli, "get_local_git_head", lambda path: None)

    target = cli.resolve_template_target()

    assert target == cli.TemplateTarget(src_path="/tmp/python-package-copier-template")


def test_resolve_template_target_falls_back_when_distribution_missing(monkeypatch) -> None:
    def _raise(_name: str):
        raise PackageNotFoundError

    monkeypatch.setattr(cli, "distribution", _raise)

    target = cli.resolve_template_target()

    assert target == cli.TemplateTarget(src_path=cli.TEMPLATE_SRC)
