import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml
from jinja2 import Environment, StrictUndefined

from python_package_copier_template import cli

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
RULESET_NAME = "python-package-template-main"


@pytest.fixture
def github(tmp_path, monkeypatch):
    executable = tmp_path / "bin" / "gh"
    executable.parent.mkdir()
    executable.write_text(
        f"#!{sys.executable}\n"
        + dedent("""\
            import json
            import os
            import sys
            from pathlib import Path

            arguments = sys.argv[1:]
            payload = json.load(sys.stdin) if "--input" in arguments else None
            with Path(os.environ["TEST_GH_LOG"]).open("a") as log:
                log.write(json.dumps({"arguments": arguments, "payload": payload}) + "\\n")
            failure = os.environ.get("TEST_GH_FAILURE")
            if failure and failure in " ".join(arguments):
                print("HTTP 403: denied", file=sys.stderr)
                sys.exit(1)
            if arguments[:2] == ["repo", "view"]:
                if "--json" in arguments:
                    print("example/custom")
                elif os.environ.get("TEST_REPO_EXISTS") != "true":
                    sys.exit(1)
            if arguments[0] != "api":
                sys.exit(0)
            state_path = Path(os.environ["TEST_GH_STATE"])
            rulesets = json.loads(state_path.read_text())
            if "--paginate" in arguments:
                for ruleset in rulesets:
                    if ruleset["name"] == "python-package-template-main":
                        print(ruleset["id"])
            elif payload:
                if arguments[arguments.index("--method") + 1] == "POST":
                    rulesets.append({"id": 42, **payload})
                else:
                    rulesets = [ruleset if ruleset["id"] != 42 else {"id": 42, **payload}
                                for ruleset in rulesets]
                state_path.write_text(json.dumps(rulesets))
            """),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    log = tmp_path / "gh.jsonl"
    state = tmp_path / "rulesets.json"
    state.write_text('[{"id": 9, "name": "stricter-existing-policy", "rules": [{"type": "required_signatures"}]}]')
    monkeypatch.setenv("PATH", f"{executable.parent}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TEST_GH_LOG", str(log))
    monkeypatch.setenv("TEST_GH_STATE", str(state))
    return log, state


def github_calls(log):
    return [json.loads(line) for line in log.read_text().splitlines()]


@pytest.mark.parametrize("explicit_repository", [False, True])
@pytest.mark.parametrize("directory", [".", "project"])
def test_main_protection_is_idempotent(github, directory, explicit_repository):
    log, state = github
    existing_rulesets = json.loads(state.read_text())
    command = ["sh", ".github/configure-main-protection.sh"]
    if explicit_repository:
        command.append("example/custom")
    for _ in range(2):
        result = subprocess.run(command, cwd=TEMPLATE_ROOT / directory, capture_output=True, text=True, check=True)
        assert "Main protection enabled for example/custom" in result.stdout

    calls = github_calls(log)
    writes = [call for call in calls if call["payload"]]
    creation, update = writes
    assert "POST" in creation["arguments"]
    assert "repos/example/custom/rulesets" in creation["arguments"]
    assert "PUT" in update["arguments"]
    assert "repos/example/custom/rulesets/42" in update["arguments"]
    assert creation["payload"] == update["payload"]
    payload = creation["payload"]
    assert payload["name"] == RULESET_NAME
    assert payload["enforcement"] == "active"
    assert payload["target"] == "branch"
    assert payload["bypass_actors"] == []
    assert payload["conditions"] == {"ref_name": {"include": ["refs/heads/main"], "exclude": []}}
    rules = {rule["type"]: rule for rule in payload["rules"]}
    assert set(rules) == {"deletion", "non_fast_forward", "pull_request"}
    assert rules["pull_request"]["parameters"] == {
        "dismiss_stale_reviews_on_push": True,
        "require_code_owner_review": False,
        "require_last_push_approval": False,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": True,
    }
    assert json.loads(state.read_text()) == [*existing_rulesets, {"id": 42, **payload}]
    assert sum(call["arguments"][:2] == ["repo", "view"] for call in calls) == (0 if explicit_repository else 2)
    for call in calls:
        if "--paginate" in call["arguments"]:
            assert "repos/example/custom/rulesets?includes_parents=false&per_page=100" in call["arguments"]
            assert (
                'select(.name == "python-package-template-main" and .source_type == "Repository")'
                in (call["arguments"][-1])
            )


@pytest.mark.parametrize("failure", ["branches/main", "--paginate", "--method"])
def test_main_protection_reports_api_failures(github, monkeypatch, failure):
    log, state = github
    before = state.read_text()
    monkeypatch.setenv("TEST_GH_FAILURE", failure)
    result = subprocess.run(["make", "protect-main"], cwd=TEMPLATE_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "HTTP 403" in result.stderr
    assert "Error:" in result.stderr
    assert "Main protection enabled" not in result.stdout
    assert state.read_text() == before
    writes = [call for call in github_calls(log) if call["payload"]]
    assert len(writes) == (1 if failure == "--method" else 0)
    if failure == "--method":
        assert "make protect-main" in result.stderr


def test_main_protection_rejects_duplicate_managed_rulesets(github):
    log, state = github
    state.write_text(json.dumps([{"id": identifier, "name": RULESET_NAME} for identifier in (42, 43)]))
    result = subprocess.run(
        ["sh", ".github/configure-main-protection.sh", "example/custom"],
        cwd=TEMPLATE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Resolve duplicates" in result.stderr
    assert not any(call["payload"] for call in github_calls(log))


def test_main_protection_reports_missing_gh(monkeypatch):
    shell = shutil.which("sh")
    assert shell is not None
    monkeypatch.setenv("PATH", "/nonexistent")
    result = subprocess.run(
        [shell, ".github/configure-main-protection.sh"], cwd=TEMPLATE_ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "install and authenticate gh" in result.stderr


@pytest.mark.parametrize(
    "scenario",
    [
        ("skip", False, False, ""),
        ("public", False, False, ""),
        ("private", False, False, ""),
        ("public", True, False, ""),
        ("public", True, True, ""),
        ("public", False, False, "--method POST repos/example/custom/rulesets"),
        ("public", False, False, "repo create"),
        ("public", False, False, "push"),
    ],
)
def test_repository_creation_protects_main(tmp_path, github, monkeypatch, scenario):
    visibility, repo_exists, opt_in, failure = scenario
    log, _ = github
    destination = tmp_path / "generated"
    shutil.copytree(TEMPLATE_ROOT / "project/.github", destination / ".github")
    git = tmp_path / "bin/git"
    git.write_text(
        '#!/bin/sh\nprintf \'{"arguments":["git","%s"],"payload":null}\\n\' "$*" >> "$TEST_GH_LOG"\n'
        'if [ "$TEST_GH_FAILURE" = push ] && [ "$1" = push ]; then exit 1; fi\n'
    )
    git.chmod(0o755)
    monkeypatch.setenv("TEST_REPO_EXISTS", str(repo_exists).lower())
    monkeypatch.setenv("TEST_GH_FAILURE", failure)
    config = yaml.safe_load((TEMPLATE_ROOT / "copier.yml").read_text())
    task = next(task for task in config["_tasks"] if "gh repo create" in task["command"])
    command = (
        Environment(autoescape=True, undefined=StrictUndefined)
        .from_string(task["command"])
        .render(
            gh_repo_create=visibility,
            repository_namespace="example",
            repository_name="custom",
            project_description="Example project",
            gh_main_protection_configure=opt_in,
        )
    )
    result = subprocess.run(["sh", "-c", command], cwd=destination, capture_output=True, text=True, check=False)
    if visibility == "skip":
        assert result.returncode == 0
        assert not log.exists()
        return
    calls = github_calls(log)
    protection_calls = [call for call in calls if any("/rulesets" in argument for argument in call["arguments"])]
    if failure in {"repo create", "push"}:
        assert result.returncode != 0
        assert not protection_calls
        return
    assert result.returncode == 0
    assert bool(protection_calls) == (not repo_exists or opt_in)
    if protection_calls:
        push_index = next(
            index for index, call in enumerate(calls) if call["arguments"] == ["git", "push -u origin main"]
        )
        assert push_index < calls.index(protection_calls[0])
    if failure:
        assert "Warning: main protection setup incomplete" in result.stderr
        assert "Main protection enabled" not in result.stdout


@pytest.mark.parametrize("update", [False, True])
@pytest.mark.parametrize("configure", [False, True])
def test_wrapper_main_protection_opt_in(tmp_path, mocker, update, configure):
    if update:
        (tmp_path / ".copier-answers.yml").touch()
    copy = mocker.patch.object(cli, "run_copy")
    update_project = mocker.patch.object(cli, "run_update")
    mocker.patch.object(cli, "resolve_template_target", return_value=cli.TemplateTarget(src_path="local-template"))
    arguments = [str(tmp_path)]
    if configure:
        arguments.append("--configure-main-protection")
    assert cli.main(arguments) == 0
    if update:
        copy.assert_not_called()
        assert update_project.call_args.kwargs["data"] == {
            "gh_dependabot_configure": False,
            "gh_main_protection_configure": configure,
        }
    else:
        update_project.assert_not_called()
        assert copy.call_args.kwargs["data"] == ({"gh_main_protection_configure": True} if configure else None)


def test_main_protection_script_matches_template():
    root_script = TEMPLATE_ROOT / ".github/configure-main-protection.sh"
    template_script = TEMPLATE_ROOT / "project/.github/configure-main-protection.sh"
    assert root_script.read_bytes() == template_script.read_bytes()
    assert os.access(root_script, os.X_OK)
    assert os.access(template_script, os.X_OK)
