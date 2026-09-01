from __future__ import annotations

import os
import shutil
import subprocess
import sys
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
def test_clean_wheel_installs_resources_and_canonical_template_taxonomy(
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
    assert "axiomfig/resources/styles/style.yaml" in names
    assert "axiomfig/resources/styles/fonts.yaml" in names
    assert "axiomfig/resources/styles/colors.yaml" in names
    assert not any("share/axiomfig/" in name for name in names)
    assert not any("evaluation/" in name for name in names)
    assert not any("template-knowledge/" in name for name in names)
    assert "axiomfig/resources/fonts/XCharter-Roman.otf" in names
    assert "axiomfig/resources/fonts/licenses/Maple-Mono-OFL.txt" in names
    assert "axiomfig/resources/fonts/licenses/OFL-1.1.txt" in names
    assert "axiomfig/resources/latex/axiomfig.sty" in names
    assert "axiomfig/resources/latex/axiomfig-colors.tex" in names
    assert not any("share/axiomfig/fonts/" in name for name in names)
    assert "axiomfig/templates/index.yaml" in names
    for family in (
        "line",
        "scatter",
        "bar",
        "distribution",
        "heatmap",
        "estimation",
        "diagnostics",
        "ordination",
        "association",
        "flow",
        "field",
        "omics",
        "survival",
        "layouts",
    ):
        assert f"axiomfig/templates/{family}/builders.py" in names
        assert f"axiomfig/templates/{family}/contract.yaml" in names
        if family != "layouts":
            assert f"axiomfig/templates/{family}/adapter.py" in names
    assert (
        not {
            "axiomfig/templates/curves.py",
            "axiomfig/templates/distributions.py",
            "axiomfig/templates/surfaces.py",
            "axiomfig/templates/panels.py",
        }
        & names
    )
    assert not any(name.endswith(".mplstyle") for name in names)
    assert "axiomfig/styles.py" not in names
    assert "axiomfig/templates.py" not in names
    assert not any("axiomfig/resources/templates/" in name for name in names)

    _run([sys.executable, "-m", "venv", str(environment)], cwd=outside)
    python = environment / "bin/python"
    _run([str(python), "-m", "pip", "install", str(wheel)], cwd=outside)
    env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    env["PYTHONNOUSERSITE"] = "1"
    _run(
        [
            str(python),
            "-c",
            (
                "from axiomfig.config import load_contracts; "
                "from axiomfig.templates import TEMPLATE_BUILDERS; "
                "from importlib.resources import files; "
                "assert load_contracts().style['stroke']['main_stroke_pt'] == 0.8; "
                "from axiomfig.templates.registry import load_template_registry, "
                "public_template_specs; "
                "assert len(TEMPLATE_BUILDERS) == len(load_template_registry()); "
                "assert len(public_template_specs()) > 0; "
                "assert files('axiomfig.templates').joinpath('index.yaml').is_file(); "
                "from axiomfig.typography import discover_fonts; "
                "assert discover_fonts('serif')['text'].family == 'XCharter'; "
                "root = files('axiomfig').joinpath('resources'); "
                "assert root.joinpath('fonts', 'XCharter-Roman.otf').is_file(); "
                "assert root.joinpath('fonts', 'licenses', 'OFL-1.1.txt').is_file(); "
                "assert root.joinpath('latex', 'axiomfig.sty').is_file(); "
                "from importlib.metadata import version; "
                "assert version('axiomfig') == '1.1.0'"
            ),
        ],
        cwd=outside,
        env=env,
    )
    intent = outside / "intent.yaml"
    data = outside / "data.csv"
    shutil.copy2(ROOT / "examples/parity/intent.yaml", intent)
    shutil.copy2(ROOT / "examples/parity/data.csv", data)
    artifacts = outside / "artifacts"
    artifacts.mkdir()
    _run(
        [
            str(environment / "bin/axiomfig-intent"),
            str(intent),
            "--data",
            str(data),
            "--output",
            str(artifacts / "intent-parity"),
        ],
        cwd=outside,
        env=env,
    )
    _run(
        [
            str(environment / "bin/axiomfig-render"),
            "scatter/parity",
            "--output",
            str(artifacts / "canonical-parity"),
        ],
        cwd=outside,
        env=env,
    )
    assert all(
        (artifacts / f"{stem}.{suffix}").is_file()
        for stem in ("intent-parity", "canonical-parity")
        for suffix in ("pdf", "png")
    )
    _run(
        [str(environment / "bin/axiomfig-validate"), str(artifacts)],
        cwd=outside,
        env=env,
    )
    _run(
        [str(environment / "bin/axiomfig-gallery"), "--help"],
        cwd=outside,
        env=env,
    )
