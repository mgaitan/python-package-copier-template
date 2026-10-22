import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from copier import run_copy, run_update
from jinja2 import Environment, StrictUndefined
from plumbum import local

from python_package_copier_template import cli, extensions

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def generated_project(tmp_path, mocker):
    template = tmp_path / "template"
    template.mkdir()
    shutil.copy2(TEMPLATE_ROOT / "copier.yml", template / "copier.yml")
    shutil.copytree(TEMPLATE_ROOT / "project", template / "project")
    mocker.patch.object(extensions, "gh_user_login", side_effect=lambda default: default)
    mocker.patch.object(extensions, "pypi_distribution_exists", return_value=False)
    mocker.patch.object(extensions, "command_available", side_effect=lambda command: command == "gh")
    destination = tmp_path / "generated"
    run_copy(
        str(template),
        destination,
        data={"repository_namespace": "example", "repository_name": "custom", "gh_repo_create": "skip"},
        defaults=True,
        unsafe=True,
        skip_tasks=True,
    )
    return destination


@pytest.fixture
def fake_gh(tmp_path, monkeypatch):
    executable = tmp_path / "bin" / "gh"
    executable.parent.mkdir()
    executable.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$TEST_GH_LOG"\n'
        'case "$*" in\n'
        '  "repo view --json nameWithOwner --jq .nameWithOwner") echo example/custom ;;\n'
        '  *"${TEST_GH_FAILURE:-no-failure}"*) echo "HTTP 403: denied" >&2; exit 1 ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    log = tmp_path / "gh.log"
    executable_path = f"{executable.parent}{os.pathsep}{os.environ['PATH']}"
    monkeypatch.setenv("PATH", executable_path)
    monkeypatch.setenv("TEST_GH_LOG", str(log))
    monkeypatch.setitem(local.env, "PATH", executable_path)
    monkeypatch.setitem(local.env, "TEST_GH_LOG", str(log))
    return log


def test_generated_dependabot_configuration(generated_project):
    config_path = generated_project / ".github/dependabot.yml"
    assert config_path.read_bytes() == (TEMPLATE_ROOT / ".github/dependabot.yml").read_bytes()
    assert (generated_project / ".github/configure-dependabot.sh").read_bytes() == (
        TEMPLATE_ROOT / ".github/configure-dependabot.sh"
    ).read_bytes()

    config = yaml.safe_load(config_path.read_text())
    assert {entry["package-ecosystem"] for entry in config["updates"]} == {"uv", "github-actions"}
    for entry in config["updates"]:
        assert entry["directory"] == "/"
        assert entry["schedule"] == {
            "interval": "weekly",
            "day": "monday",
        }
        assert not {"target-branch", "assignees", "reviewers", "allow", "ignore"} & entry.keys()
        groups = {group["applies-to"]: group for group in entry["groups"].values()}
        assert groups["version-updates"]["update-types"] == ["minor", "patch"]
        assert groups["security-updates"] == {"applies-to": "security-updates", "patterns": ["*"]}

    answers = yaml.safe_load((generated_project / ".copier-answers.yml").read_text())
    assert "gh_dependabot_configure" not in answers


@pytest.mark.parametrize("explicit_repository", [False, True])
def test_dependabot_setup_is_repeatable(generated_project, fake_gh, explicit_repository):
    command = ["sh", ".github/configure-dependabot.sh"]
    if explicit_repository:
        command.append("example/custom")
    for _ in range(2):
        result = subprocess.run(command, cwd=generated_project, check=True, capture_output=True, text=True)
        assert "enabled for example/custom" in result.stdout

    calls = fake_gh.read_text().splitlines()
    api_calls = [call for call in calls if call.startswith("api ")]
    expected_features = ["vulnerability-alerts", "automated-security-fixes"] * 2
    assert len(api_calls) == len(expected_features)
    for call, feature in zip(api_calls, expected_features, strict=True):
        assert "--method PUT" in call
        assert call.endswith(f"repos/example/custom/{feature}")
    assert sum(call.startswith("repo view ") for call in calls) == (0 if explicit_repository else 2)


@pytest.mark.parametrize("feature", ["vulnerability-alerts", "automated-security-fixes"])
def test_dependabot_setup_reports_api_failures(generated_project, fake_gh, monkeypatch, feature):
    monkeypatch.setenv("TEST_GH_FAILURE", feature)
    result = subprocess.run(["make", "dependabot"], cwd=generated_project, check=False, capture_output=True, text=True)
    assert result.returncode != 0
    assert "HTTP 403" in result.stderr
    assert f"could not enable {feature}" in result.stderr
    assert "make dependabot" in result.stderr
    assert "enabled for" not in result.stdout
    if feature == "vulnerability-alerts":
        assert "automated-security-fixes" not in fake_gh.read_text()


def test_dependabot_setup_reports_missing_gh(generated_project, monkeypatch):
    shell = shutil.which("sh")
    assert shell is not None
    monkeypatch.setenv("PATH", "/nonexistent")
    result = subprocess.run(
        [shell, ".github/configure-dependabot.sh"],
        cwd=generated_project,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "install and authenticate gh" in result.stderr


@pytest.mark.parametrize("configure", [False, True])
def test_wrapper_dependabot_update_opt_in(tmp_path, mocker, configure):
    (tmp_path / ".copier-answers.yml").touch()
    update = mocker.patch.object(cli, "run_update")
    arguments = [str(tmp_path)]
    if configure:
        arguments.append("--configure-dependabot")
    assert cli.main(arguments) == 0
    update.assert_called_once_with(
        dst_path=str(tmp_path),
        data={"gh_dependabot_configure": configure},
        defaults=True,
        unsafe=True,
        overwrite=True,
        skip_answered=True,
        vcs_ref="HEAD",
    )


def test_copier_update_does_not_persist_dependabot_opt_in(generated_project, fake_gh, monkeypatch):
    for variable, value in {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }.items():
        monkeypatch.setenv(variable, value)
    template = generated_project.parent / "template"
    subprocess.run(["git", "init", "-b", "main", str(template)], check=True)
    subprocess.run(["git", "-C", str(template), "add", "."], check=True)
    subprocess.run(["git", "-C", str(template), "commit", "-m", "init"], check=True)
    run_copy(
        str(template),
        generated_project,
        data={"repository_namespace": "example", "repository_name": "custom", "gh_repo_create": "skip"},
        defaults=True,
        overwrite=True,
        unsafe=True,
        skip_tasks=True,
        vcs_ref="HEAD",
    )
    subprocess.run(["git", "init", "-b", "main", str(generated_project)], check=True)
    subprocess.run(["git", "-C", str(generated_project), "add", "."], check=True)
    subprocess.run(["git", "-C", str(generated_project), "commit", "-m", "init"], check=True)

    cli.main([str(generated_project)])
    assert not fake_gh.exists()
    cli.main(["--configure-dependabot", str(generated_project)])
    calls = fake_gh.read_text()
    assert "repos/example/custom/vulnerability-alerts" in calls
    assert "repos/example/custom/automated-security-fixes" in calls
    answers = yaml.safe_load((generated_project / ".copier-answers.yml").read_text())
    assert "gh_dependabot_configure" not in answers
    with extensions.update_mode():
        run_update(str(generated_project), defaults=True, unsafe=True, overwrite=True, vcs_ref="HEAD")
    assert fake_gh.read_text() == calls


@pytest.mark.parametrize(
    ("visibility", "api_fails"), [("skip", False), ("public", False), ("private", False), ("private", True)]
)
def test_repository_creation_configures_dependabot(generated_project, fake_gh, monkeypatch, visibility, api_fails):
    if api_fails:
        monkeypatch.setenv("TEST_GH_FAILURE", "automated-security-fixes")
    executable = fake_gh.parent / "bin" / "git"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    config = yaml.safe_load((TEMPLATE_ROOT / "copier.yml").read_text())
    task = config["_tasks"][-2]
    command = (
        Environment(autoescape=True, undefined=StrictUndefined)
        .from_string(task["command"])
        .render(
            gh_repo_create=visibility,
            repository_namespace="example",
            repository_name="custom",
            project_description="Example project",
        )
    )
    result = subprocess.run(["sh", "-c", command], cwd=generated_project, check=True, capture_output=True, text=True)
    if visibility == "skip":
        assert not fake_gh.exists()
    else:
        calls = fake_gh.read_text()
        assert "repos/example/custom/vulnerability-alerts" in calls
        assert "repos/example/custom/automated-security-fixes" in calls
        if api_fails:
            assert "Warning: Dependabot setup incomplete" in result.stderr
            assert "Dependabot alerts, dependency graph, and security updates enabled" not in result.stdout
        else:
            assert "enabled for example/custom" in result.stdout
