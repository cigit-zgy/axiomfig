from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.e2e
def test_checkout_render_cli_accepts_relative_output_and_work_paths(tmp_path: Path) -> None:
    _run(
        [
            sys.executable,
            str(ROOT / "scripts/render.py"),
            "line-single",
            "--output",
            "deliverables/line",
            "--work-root",
            "work",
        ],
        cwd=tmp_path,
    )

    assert (tmp_path / "deliverables/line.pdf").is_file()
    assert (tmp_path / "deliverables/line.png").is_file()


@pytest.mark.e2e
def test_clean_wheel_install_runs_every_resource_dependent_cli(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    environment = tmp_path / "environment"
    outside_checkout = tmp_path / "outside-checkout"
    wheelhouse.mkdir()
    outside_checkout.mkdir()

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
        cwd=ROOT,
    )
    wheel = next(wheelhouse.glob("axiomfig-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "axiomfig/resources/styles/base/publication.mplstyle" in names
    assert "axiomfig/resources/templates/line.py" in names

    _run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(environment)],
        cwd=outside_checkout,
    )
    installed_python = environment / "bin/python"
    _run(
        [str(installed_python), "-m", "pip", "install", "--no-deps", str(wheel)],
        cwd=outside_checkout,
    )
    installed_env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    installed_env["PATH"] = f"{environment / 'bin'}{os.pathsep}{installed_env['PATH']}"
    installed_env["PYTHONNOUSERSITE"] = "1"
    _run(
        [
            str(installed_python),
            "-c",
            (
                "from pathlib import Path; import axiomfig; "
                f"assert Path(axiomfig.__file__).is_relative_to(Path({str(environment)!r}))"
            ),
        ],
        cwd=outside_checkout,
        env=installed_env,
    )

    _run(
        ["axiomfig-compose", "--output", "composed.mplstyle"],
        cwd=outside_checkout,
        env=installed_env,
    )
    _run(
        [
            "axiomfig-render",
            "line-single",
            "--output",
            "rendered/line",
            "--work-root",
            "render-work",
        ],
        cwd=outside_checkout,
        env=installed_env,
    )
    _run(
        ["axiomfig-validate", "rendered"],
        cwd=outside_checkout,
        env=installed_env,
    )
    _run(
        [
            "axiomfig-gallery",
            "--gallery",
            "installed-gallery",
            "--work-root",
            "gallery-work",
        ],
        cwd=outside_checkout,
        env=installed_env,
    )

    assert (outside_checkout / "composed.mplstyle").is_file()
    assert (outside_checkout / "rendered/line.pdf").is_file()
    assert (outside_checkout / "rendered/line.png").is_file()
    assert len(list((outside_checkout / "installed-gallery").glob("*.pdf"))) == 10
    assert len(list((outside_checkout / "installed-gallery").glob("*.png"))) == 10
