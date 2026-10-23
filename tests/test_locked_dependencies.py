import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("directory", [".github/workflows", "project/.github/workflows"])
def test_ci_dependency_jobs_require_lockfile_check(directory):
    path = TEMPLATE_ROOT / directory / ("ci.yml.jinja" if directory.startswith("project/") else "ci.yml")
    content = path.read_text()
    if path.suffix == ".jinja":
        content = Environment(autoescape=True).from_string(content).render()
    jobs = yaml.safe_load(content)["jobs"]
    assert any(step.get("run") == "uv lock --check" for step in jobs["lockfile"]["steps"])
    if "qa" in jobs:
        assert jobs["qa"]["needs"] == "lockfile"
        assert jobs["test"]["needs"] == "qa"
    else:
        for job in ("docs", "template-smoke", "generated-docs"):
            assert "lockfile" in jobs[job]["needs"]


@pytest.mark.parametrize(
    "relative_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/cd.yml",
        "project/.github/workflows/ci.yml.jinja",
        "project/.github/workflows/cd.yml.jinja",
        "Makefile",
        "project/Makefile.jinja",
    ],
)
def test_project_uv_run_commands_are_locked(relative_path):
    for line in (TEMPLATE_ROOT / relative_path).read_text().splitlines():
        if "uv run " in line and "--no-project" not in line:
            assert "uv run --locked " in line


def test_template_update_regenerates_lockfile_before_creating_pr():
    path = TEMPLATE_ROOT / "project/.github/workflows/template-update.yml.jinja"
    content = path.read_text()
    assert content.index("name: Refresh from template") < content.index("run: uv lock")
    assert content.index("run: uv lock") < content.index("name: Create pull request")


@pytest.mark.parametrize(
    "command", [["lock", "--check", "--offline"], ["run", "--locked", "--offline", "python", "-c", "pass"]]
)
def test_stale_lockfile_fails_without_modifying_it(tmp_path, command):
    uv = shutil.which("uv")
    assert uv is not None
    project = tmp_path / "pyproject.toml"
    original = '[project]\nname = "lockfile-test"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    project.write_text(original)
    subprocess.run([uv, "lock", "--offline", "--python", sys.executable], cwd=tmp_path, check=True)
    lockfile = tmp_path / "uv.lock"
    locked = lockfile.read_bytes()
    project.write_text(original.replace('"0.1.0"', '"0.2.0"'))

    result = subprocess.run(
        [uv, *command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "lockfile" in result.stderr.lower()
    assert "needs to be updated" in result.stderr
    assert lockfile.read_bytes() == locked
