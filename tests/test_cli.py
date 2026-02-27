import os
import subprocess
import urllib.error
from email.message import Message
from pathlib import Path

from python_package_copier_template import cli, extensions


def test_cli_copy_and_update(tmp_path: Path, monkeypatch) -> None:
    # Use the template in the repository (current working tree).
    template_src = Path(__file__).resolve().parent.parent
    monkeypatch.setattr(cli, "TEMPLATE_SRC", str(template_src))
    monkeypatch.setenv("COPIER_TEMPLATE_DEFAULTS", "1")

    dest = tmp_path / "proj"
    project_exists_on_pypi = False

    # First run: copy should create the project (defaults provided via env).
    class _DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(_request, timeout):  # noqa: ANN001
        if project_exists_on_pypi:
            return _DummyResponse()
        raise urllib.error.HTTPError("", 404, "not found", Message(), None)

    monkeypatch.setattr(extensions.urllib.request, "urlopen", _fake_urlopen)
    cli.main([str(dest)])
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
