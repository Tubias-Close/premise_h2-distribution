import os
import shutil
import subprocess
from itertools import combinations
from pathlib import Path

import pytest
import yaml


REQUIRED_SECRETS = ("IAM_FILES_KEY", "EI_USERNAME", "EI_PASSWORD")
MISSING_COMBINATIONS = [
    missing
    for count in range(len(REQUIRED_SECRETS) + 1)
    for missing in combinations(REQUIRED_SECRETS, count)
]


@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
@pytest.mark.parametrize("missing", MISSING_COMBINATIONS)
def test_certification_credential_check(event, missing, tmp_path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("The certification credential check requires Bash.")
    workflow = yaml.safe_load(
        (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/validation-certification.yml"
        ).read_text(encoding="utf-8")
    )
    check = next(
        step
        for step in workflow["jobs"]["credentials"]["steps"]
        if step.get("id") == "check"
    )
    output = tmp_path / "output"
    summary = tmp_path / "summary"
    credentials = {
        name: f"fake-secret-{name}-$value-with spaces"
        for name in REQUIRED_SECRETS
        if name not in missing
    }
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-eo", "pipefail", "-c", check["run"]],
        cwd=tmp_path,
        env={
            "PATH": os.defpath,
            "GITHUB_EVENT_NAME": event,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
            **{name: "" for name in REQUIRED_SECRETS},
            **credentials,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == int(bool(missing) and event == "workflow_dispatch")
    assert output.read_text().strip() == (
        "available=false" if missing else "available=true"
    )
    message = summary.read_text()
    if missing:
        for name in missing:
            assert name in result.stdout
            assert name in message
        if event == "schedule":
            assert "::notice::" in result.stdout
            assert "no certification tests or profiling ran" in message
        else:
            assert "::error::" in result.stdout
            assert "could not start" in message
    else:
        assert "credentials are available" in message
        assert "::error::" not in result.stdout

    logs = result.stdout + result.stderr + message + output.read_text()
    for value in credentials.values():
        assert value not in logs
