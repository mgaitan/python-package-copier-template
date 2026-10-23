import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("relative_path", ["prek.toml", "project/prek.toml.jinja"])
def test_uv_lock_hook_matches_upstream(relative_path):
    config = tomllib.loads((TEMPLATE_ROOT / relative_path).read_text())
    hook = next(hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "uv-lock")
    assert hook["entry"] == "uv lock"
    assert hook["language"] == "system"
    assert hook["pass_filenames"] is False
    assert not hook.get("always_run", False)
    for filename in ("pyproject.toml", "uv.lock", "uv.toml"):
        assert re.search(hook["files"], filename)
    for filename in ("README.md", "src/package.py", "other/pyproject.toml"):
        assert not re.search(hook["files"], filename)


@pytest.mark.parametrize("directory", [".github/workflows", "project/.github/workflows"])
def test_ci_reuses_existing_job_for_lockfile_hook(directory):
    path = TEMPLATE_ROOT / directory / ("ci.yml.jinja" if directory.startswith("project/") else "ci.yml")
    content = path.read_text()
    if path.suffix == ".jinja":
        content = Environment(autoescape=True).from_string(content).render()
    jobs = yaml.safe_load(content)["jobs"]
    assert "lockfile" not in jobs
    job = jobs["qa"] if "qa" in jobs else jobs["template-smoke"]
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert commands.index("prek run uv-lock --all-files") < commands.index("uv run ")


def test_template_update_regenerates_lockfile_before_creating_pr():
    path = TEMPLATE_ROOT / "project/.github/workflows/template-update.yml.jinja"
    content = path.read_text()
    assert content.index("name: Refresh from template") < content.index("run: uv lock")
    assert content.index("run: uv lock") < content.index("name: Create pull request")


@pytest.mark.parametrize("directory", [".", "project"])
def test_prek_updates_stale_lockfile_and_fails(tmp_path, monkeypatch, directory):
    uv = shutil.which("uv")
    prek = shutil.which("prek")
    assert uv is not None
    if prek is None:
        pytest.skip("The prek CLI is required to exercise the hook")
    monkeypatch.setenv("UV_OFFLINE", "1")
    monkeypatch.setenv("UV_PYTHON", sys.executable)
    source = TEMPLATE_ROOT / directory
    suffix = ".jinja" if directory == "project" else ""
    shutil.copy2(source / f"prek.toml{suffix}", tmp_path / "prek.toml")
    shutil.copy2(source / f".gitignore{suffix}", tmp_path / ".gitignore")
    project = tmp_path / "pyproject.toml"
    original = '[project]\nname = "lockfile-test"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    project.write_text(original)
    subprocess.run([uv, "lock"], cwd=tmp_path, check=True)
    subprocess.run(["git", "init", "-b", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "ls-files", "--error-unmatch", "uv.lock"], cwd=tmp_path, check=True)
    project.write_text(original.replace('"0.1.0"', '"0.2.0"'))

    skipped = subprocess.run(
        [prek, "run", "uv-lock", "--files", "README.md"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert "Skipped" in skipped.stdout
    command = [prek, "run", "uv-lock", "--files", "pyproject.toml"]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "files were modified by this hook" in result.stdout
    lockfile = tomllib.loads((tmp_path / "uv.lock").read_text())
    assert lockfile["package"][0]["version"] == "0.2.0"
    subprocess.run(command, cwd=tmp_path, check=True)
