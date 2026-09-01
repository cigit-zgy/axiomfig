from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout


@pytest.mark.e2e
def test_clean_checkout_executes_documented_quick_start(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    environment = tmp_path / "environment"
    outside = tmp_path / "outside"
    outside.mkdir()
    _run(
        ["git", "clone", "--no-local", "--no-hardlinks", str(ROOT), str(checkout)],
        cwd=tmp_path,
    )
    expected_sha = _run(["git", "rev-parse", "HEAD"], cwd=ROOT).strip()
    _run(["git", "checkout", "--detach", expected_sha], cwd=checkout)
    _run([sys.executable, "-m", "venv", str(environment)], cwd=outside)
    python = environment / "bin/python"
    _run([str(python), "-m", "pip", "install", str(checkout)], cwd=outside)
    env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    env["PYTHONNOUSERSITE"] = "1"
    _run([str(python), "scripts/validate_skill.py"], cwd=checkout, env=env)
    artifacts = outside / "artifacts"
    artifacts.mkdir()
    output = artifacts / "parity"
    _run(
        [
            str(environment / "bin/axiomfig-intent"),
            str(checkout / "examples/parity/intent.yaml"),
            "--data",
            str(checkout / "examples/parity/data.csv"),
            "--output",
            str(output),
        ],
        cwd=outside,
        env=env,
    )
    assert output.with_suffix(".pdf").is_file()
    assert output.with_suffix(".png").is_file()
    _run(
        [str(environment / "bin/axiomfig-validate"), str(artifacts)],
        cwd=outside,
        env=env,
    )
