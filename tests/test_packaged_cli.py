from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=env, check=False, text=True, capture_output=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout


@pytest.mark.e2e
def test_clean_wheel_installs_package_resources_and_four_template_families(
    tmp_path: Path,
) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    environment = tmp_path / "environment"
    outside = tmp_path / "outside"
    source = tmp_path / "source"
    wheelhouse.mkdir()
    outside.mkdir()
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(
            ".git",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
            "*.egg-info",
            "build",
            "dist",
            "gallery",
            "tmp",
        ),
    )
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheelhouse),
        ],
        cwd=source,
    )
    wheel = next(wheelhouse.glob("axiomfig-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert any(name.endswith("share/axiomfig/styles/style.yaml") for name in names)
    assert "axiomfig/resources/fonts/XCharter-Roman.otf" in names
    assert "axiomfig/resources/fonts/licenses/Maple-Mono-OFL.txt" in names
    assert "axiomfig/resources/fonts/licenses/OFL-1.1.txt" in names
    assert "axiomfig/resources/latex/axiomfig.sty" in names
    assert "axiomfig/resources/latex/axiomfig-colors.tex" in names
    assert not any("share/axiomfig/fonts/" in name for name in names)
    assert "axiomfig/templates/curves.py" in names
    assert "axiomfig/templates/distributions.py" in names
    assert "axiomfig/templates/surfaces.py" in names
    assert "axiomfig/templates/panels.py" in names
    assert not any(name.endswith(".mplstyle") for name in names)
    assert "axiomfig/styles.py" not in names
    assert "axiomfig/templates.py" not in names
    assert not any("axiomfig/resources/styles/" in name for name in names)
    assert not any("axiomfig/resources/templates/" in name for name in names)

    _run([sys.executable, "-m", "venv", str(environment)], cwd=outside)
    python = environment / "bin/python"
    _run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], cwd=outside)
    env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONPATH"] = sysconfig.get_path("purelib")
    _run(
        [
            str(python),
            "-c",
            (
                "from axiomfig.config import load_contracts; "
                "from axiomfig.templates import TEMPLATE_BUILDERS; "
                "from importlib.resources import files; "
                "assert load_contracts().style['stroke']['main_stroke_pt'] == 0.8; "
                "assert len(TEMPLATE_BUILDERS) == 36; "
                "from axiomfig.typography import discover_fonts; "
                "assert discover_fonts('serif')['text'].family == 'XCharter'; "
                "root = files('axiomfig').joinpath('resources'); "
                "assert root.joinpath('fonts', 'XCharter-Roman.otf').is_file(); "
                "assert root.joinpath('fonts', 'licenses', 'OFL-1.1.txt').is_file(); "
                "assert root.joinpath('latex', 'axiomfig.sty').is_file()"
            ),
        ],
        cwd=outside,
        env=env,
    )
