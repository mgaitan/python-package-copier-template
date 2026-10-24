import os
import subprocess
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


def load_workflow(directory):
    suffix = ".jinja" if directory == "project" else ""
    content = (TEMPLATE_ROOT / directory / f".github/workflows/cd.yml{suffix}").read_text()
    if suffix:
        content = Environment(autoescape=True).from_string(content).render(python_package_import_name="example")
    return yaml.safe_load(content)


@pytest.mark.parametrize("directory", [".", "project"])
def test_release_is_published_in_one_workflow(directory):
    config = load_workflow(directory)
    events = config[True]
    assert "closed" in events["pull_request"]["types"]
    assert "pyproject.toml" in events["pull_request"]["paths"]
    assert events["workflow_dispatch"] is None
    assert "release" not in events
    job = config["jobs"]["pypi-publish"]
    assert "merged == true" in job["if"]
    assert "startsWith(github.event.pull_request.head.ref, 'release/')" in job["if"]
    assert "head.repo.full_name == github.repository" in job["if"]
    assert job["steps"][0]["with"]["ref"] == "${{ github.event.pull_request.merge_commit_sha }}"
    assert job["permissions"] == {"id-token": "write", "contents": "write"}
    assert "github.event.action != 'closed'" in config["jobs"]["docs-publish"]["if"]
    steps = job["steps"]
    build = next(index for index, step in enumerate(steps) if step.get("run") == "uv build")
    publish = next(index for index, step in enumerate(steps) if step.get("run") == "uv publish")
    release = next(index for index, step in enumerate(steps) if step.get("name") == "Create GitHub release")
    assert build < publish < release
    assert not any("gh workflow run" in step.get("run", "") for step in steps)
    suffix = ".jinja" if directory == "project" else ""
    assert not (TEMPLATE_ROOT / directory / f".github/workflows/release-draft.yml{suffix}").exists()
    makefile = (TEMPLATE_ROOT / directory / f"Makefile{suffix}").read_text()
    assert makefile.index("releases/generate-notes") < makefile.index("gh pr create")
    assert '--body-file "$$notes_file"' in makefile
    if directory == ".":
        demo = next(step["run"] for step in steps if step.get("name") == "Refresh demo repository")
        assert demo.index("uv lock") < demo.index("git diff --quiet")


@pytest.fixture
def release_cli(tmp_path, monkeypatch):
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    commands = {
        "uv": 'if [ "$1" = version ]; then echo 0.8.0; '
        'elif [ "$1" = publish ] && [ "${TEST_PUBLISH_FAILURE:-0}" = 1 ]; then exit 1; fi\n',
        "git": 'if [ "$1" = rev-parse ]; then echo merged-sha; else\n'
        '  [ "${TEST_GIT_FAILURE:-0}" = 0 ] || exit 1\n'
        '  printf "%s" "${TEST_TAG_REF:-}"\nfi\n',
        "gh": 'printf "%s\\n" "$@" > "$TEST_GH_LOG"\n',
    }
    for name, command in commands.items():
        executable = executable_directory / name
        executable.write_text(f"#!/bin/sh\n{command}")
        executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{executable_directory}{os.pathsep}{os.environ['PATH']}")
    for name, value in {
        "RELEASE_BRANCH": "release/0.8.0",
        "RELEASE_VERSION": "0.8.0",
        "RELEASE_NOTES": "## Changes\n- Keep $(printf unsafe) literally.",
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "TEST_GH_LOG": str(tmp_path / "gh.log"),
    }.items():
        monkeypatch.setenv(name, value)
    return tmp_path


@pytest.mark.parametrize("directory", [".", "project"])
@pytest.mark.parametrize(
    "failure",
    [
        None,
        ("RELEASE_BRANCH", "release/0.9.0"),
        ("TEST_TAG_REF", "existing-tag"),
        ("TEST_GIT_FAILURE", "1"),
        ("TEST_PUBLISH_FAILURE", "1"),
    ],
)
def test_publish_uses_reviewed_notes_and_merged_commit(release_cli, monkeypatch, directory, failure):
    if failure:
        monkeypatch.setenv(*failure)
    steps = load_workflow(directory)["jobs"]["pypi-publish"]["steps"]
    script = "\n".join(
        step["run"]
        for step in steps
        if step.get("name") in {"Validate release version", "Create GitHub release"} or step.get("run") == "uv publish"
    )
    result = subprocess.run(["bash", "-e", "-c", script], capture_output=True, text=True, check=False)
    log = release_cli / "gh.log"
    if failure:
        assert result.returncode != 0
        assert not log.exists()
        return
    assert result.returncode == 0, result.stderr
    notes = release_cli / "release-notes.md"
    assert notes.read_text() == f"{os.environ['RELEASE_NOTES']}\n"
    assert log.read_text().splitlines() == [
        "release",
        "create",
        "0.8.0",
        "--target",
        "merged-sha",
        "--notes-file",
        str(notes),
    ]
