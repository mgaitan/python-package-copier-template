import os
import subprocess
from pathlib import Path

from python_package_copier_template import cli


def test_cli_copy_and_update(tmp_path: Path, monkeypatch) -> None:
    # Use the template in the repository (current working tree).
    template_src = Path(__file__).resolve().parent.parent
    monkeypatch.setattr(cli, "TEMPLATE_SRC", str(template_src))
    monkeypatch.setenv("COPIER_TEMPLATE_DEFAULTS", "1")

    dest = tmp_path / "proj"

    # First run: copy should create the project.
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

    # Second run: update should succeed when answers exist.
    cli.main([str(dest)])
