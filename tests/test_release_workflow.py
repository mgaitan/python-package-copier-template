import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml
from jinja2 import Environment

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


def load_workflow(relative_path):
    content = (TEMPLATE_ROOT / relative_path).read_text()
    if relative_path.endswith(".jinja"):
        content = (
            Environment(autoescape=True, keep_trailing_newline=True)
            .from_string(content)
            .render(python_package_import_name="example")
        )
    return yaml.safe_load(content)


@pytest.fixture
def release_cli(tmp_path, monkeypatch):
    executable = tmp_path / "bin" / "gh"
    executable.parent.mkdir()
    executable.write_text(
        f"#!{sys.executable}\n"
        + dedent("""\
            import json
            import os
            import sys
            from pathlib import Path

            tool = Path(sys.argv[0]).name
            arguments = sys.argv[1:]
            with Path(os.environ["TEST_RELEASE_LOG"]).open("a") as log:
                log.write(json.dumps([tool, *arguments]) + "\\n")
            failure = os.environ.get("TEST_RELEASE_FAILURE")
            if failure and failure in " ".join([tool, *arguments]):
                sys.exit(1)
            if tool == "uv":
                print("0.8.0")
            elif tool == "git":
                print("expected-sha" if arguments[0] == "rev-parse" else os.environ.get("TEST_TAG_REFS", ""))
            elif arguments[:2] == ["release", "view"]:
                state = os.environ["TEST_RELEASE_STATE"]
                if state == "missing":
                    sys.exit(1)
                print(state)
            """),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    for name in ("uv", "git"):
        shutil.copy2(executable, executable.parent / name)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{executable.parent}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TEST_RELEASE_LOG", str(log))
    return log


def test_release_workflow_matches_generated_template():
    config = load_workflow(".github/workflows/release-draft.yml")
    assert config == load_workflow("project/.github/workflows/release-draft.yml.jinja")
    assert config[True]["pull_request"]["types"] == ["opened", "reopened", "synchronize", "closed"]
    condition = config["jobs"]["release"]["if"]
    assert "head.repo.full_name == github.repository" in condition
    assert "github.event.action != 'closed' || github.event.pull_request.merged == true" in condition
    assert config["permissions"]["actions"] == "write"


@pytest.mark.parametrize(
    "scenario",
    [
        {"state": "missing", "writes": ["create"]},
        {"state": "true", "writes": ["edit"]},
        {"state": "true", "merged": True, "writes": ["edit", "dispatch"]},
        {"state": "false", "merged": True, "tag": "expected-sha", "writes": ["dispatch"]},
        {"state": "true", "merged": True, "tag": "other-sha", "error": "not integrated commit"},
        {"state": "missing", "merged": True, "error": "Draft release 0.8.0 is missing"},
        {"state": "false", "tag": "expected-sha", "error": "already published"},
        {"state": "missing", "branch": "release/0.9.0", "error": "must match package version"},
    ],
)
def test_release_lifecycle(release_cli, monkeypatch, scenario):
    monkeypatch.setenv("TEST_RELEASE_STATE", scenario["state"])
    monkeypatch.setenv("MERGED", str(scenario.get("merged", False)).lower())
    monkeypatch.setenv("RELEASE_BRANCH", scenario.get("branch", "release/0.8.0"))
    monkeypatch.setenv("TEST_TAG_REFS", f"{scenario['tag']}\trefs/tags/0.8.0" if "tag" in scenario else "")
    config = load_workflow(".github/workflows/release-draft.yml")
    script = config["jobs"]["release"]["steps"][-1]["run"]

    result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], capture_output=True, text=True, check=False)

    calls = [json.loads(line)[1:] for line in release_cli.read_text().splitlines() if json.loads(line)[0] == "gh"]
    writes = [call for call in calls if call[:2] != ["release", "view"]]
    if "error" in scenario:
        assert result.returncode != 0
        assert scenario["error"] in result.stderr
        assert writes == []
        return
    assert result.returncode == 0, result.stderr
    expected = []
    for operation in scenario["writes"]:
        match operation:
            case "create":
                expected.append(
                    ["release", "create", "0.8.0", "--draft", "--generate-notes", "--target", "expected-sha"]
                )
            case "edit":
                edit = ["release", "edit", "0.8.0", "--target", "expected-sha"]
                if scenario.get("merged"):
                    edit.append("--draft=false")
                expected.append(edit)
            case "dispatch":
                expected.append(["workflow", "run", "cd.yml", "--ref", "0.8.0", "-f", "publish=true"])
    assert writes == expected


def test_failed_release_publication_does_not_dispatch_cd(release_cli, monkeypatch):
    monkeypatch.setenv("TEST_RELEASE_STATE", "true")
    monkeypatch.setenv("TEST_RELEASE_FAILURE", "release edit")
    monkeypatch.setenv("MERGED", "true")
    monkeypatch.setenv("RELEASE_BRANCH", "release/0.8.0")
    script = load_workflow(".github/workflows/release-draft.yml")["jobs"]["release"]["steps"][-1]["run"]
    result = subprocess.run(["bash", "-e", "-c", script], capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "workflow" not in release_cli.read_text()


@pytest.mark.parametrize("relative_path", [".github/workflows/cd.yml", "project/.github/workflows/cd.yml.jinja"])
@pytest.mark.parametrize(
    "scenario",
    [
        ("tag", "0.8.0", "false", True),
        ("tag", "0.8.0", "true", False),
        ("branch", "main", "false", False),
        ("tag", "0.9.0", "false", False),
        ("tag", "v0.8.0", "false", True),
    ],
)
def test_cd_requires_a_published_matching_tag(release_cli, monkeypatch, relative_path, scenario):
    ref_type, tag, state, valid = scenario
    monkeypatch.setenv("GITHUB_REF_TYPE", ref_type)
    monkeypatch.setenv("GITHUB_REF_NAME", tag)
    monkeypatch.setenv("TEST_RELEASE_STATE", state)
    config = load_workflow(relative_path)
    assert config[True]["workflow_dispatch"]["inputs"]["publish"]["default"] is False
    job = config["jobs"]["pypi-publish"]
    assert "inputs.publish" in job["if"]
    assert "inputs.publish != true" in config["jobs"]["docs-publish"]["if"]
    step = next(step for step in job["steps"] if step.get("name") == "Verify published release tag")
    assert "git merge-base --is-ancestor HEAD origin/main" in step["run"]
    result = subprocess.run(["bash", "-e", "-c", step["run"]], capture_output=True, text=True, check=False)
    assert (result.returncode == 0) is valid


def test_cd_refuses_a_tag_outside_main(release_cli, monkeypatch):
    monkeypatch.setenv("GITHUB_REF_TYPE", "tag")
    monkeypatch.setenv("GITHUB_REF_NAME", "0.8.0")
    monkeypatch.setenv("TEST_RELEASE_STATE", "false")
    monkeypatch.setenv("TEST_RELEASE_FAILURE", "git merge-base")
    job = load_workflow(".github/workflows/cd.yml")["jobs"]["pypi-publish"]
    step = next(step for step in job["steps"] if step.get("name") == "Verify published release tag")
    result = subprocess.run(["bash", "-e", "-c", step["run"]], capture_output=True, text=True, check=False)
    assert result.returncode != 0
