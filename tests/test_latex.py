import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from axiomfig.latex import LatexProbeError, compile_latex_probe
from axiomfig.rendering import render_figure

ROOT = Path(__file__).resolve().parents[1]


def _write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.e2e
def test_latex_probe_typesets_scientific_semantics_with_tectonic(tmp_path: Path) -> None:
    result = compile_latex_probe(tmp_path)
    normalized_text = " ".join(result.extracted_text.split())

    assert result.pdf.is_file()
    assert result.log.is_file()
    assert result.tectonic_command[0].endswith("tectonic")
    assert "Units marker:" in normalized_text
    assert "10 mg L" in normalized_text
    assert "Chemistry markers:" in normalized_text
    assert "+ – 3– Chemistry markers:" in normalized_text
    assert all(species in normalized_text for species in ("NH4", "NO3", "PO4"))
    assert "Math marker:" in normalized_text
    assert "𝜇max" in normalized_text
    assert all(symbol in normalized_text for symbol in ("𝛼", "𝛽"))
    assert result.fonts
    assert all(" yes yes " in f" {row} " for row in result.fonts)
    assert all("Type 3" not in row for row in result.fonts)


@pytest.mark.e2e
def test_check_latex_script_reports_probe_evidence(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_latex.py"),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS Tectonic:" in completed.stdout
    assert "PASS PDF text:" in completed.stdout
    assert "PASS embedded fonts:" in completed.stdout


@pytest.mark.e2e
def test_latex_probe_rejects_stale_pdf_when_tectonic_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = compile_latex_probe(tmp_path)
    original_pdf = result.pdf.read_bytes()
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "tectonic", "#!/bin/sh\nexit 0\n")
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

    with pytest.raises(LatexProbeError, match="fresh non-empty PDF"):
        compile_latex_probe(tmp_path)

    assert result.pdf.read_bytes() == original_pdf


@pytest.mark.e2e
def test_latex_probe_rejects_valid_but_unrelated_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unrelated_tex = tmp_path / "unrelated.tex"
    unrelated_tex.write_text(
        "\\documentclass{article}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n"
        "unrelated document\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    unrelated_compile = subprocess.run(
        [
            "/opt/homebrew/bin/tectonic",
            "--outdir",
            str(tmp_path),
            unrelated_tex.name,
        ],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
    )
    assert unrelated_compile.returncode == 0, unrelated_compile.stdout + unrelated_compile.stderr
    unrelated = tmp_path / "unrelated.pdf"

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "tectonic",
        """#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

output = Path(sys.argv[sys.argv.index("--outdir") + 1])
shutil.copy2(os.environ["AXIOMFIG_UNRELATED_PDF"], output / "probe.pdf")
(output / "probe.log").write_text("fake tectonic output\\n", encoding="utf-8")
""",
    )
    monkeypatch.setenv("AXIOMFIG_UNRELATED_PDF", str(unrelated))
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

    with pytest.raises(LatexProbeError, match="missing expected scientific semantics"):
        compile_latex_probe(tmp_path / "published")


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("font_row", "diagnostic"),
    [
        ("Helvetica Type 1 WinAnsi yes yes yes 4 0", "required Latin Modern fonts"),
        ("LMRoman10 Type 1 Custom yes yes no 4 0", "Unicode mapping"),
        ("LMRoman10 Type 3 Custom yes yes yes 4 0", "Type 3"),
    ],
)
def test_latex_probe_rejects_invalid_font_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    font_row: str,
    diagnostic: str,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "pdffonts",
        "#!/bin/sh\n"
        "echo 'name type encoding emb sub uni object ID'\n"
        "echo '----------------------------------------'\n"
        f"echo '{font_row}'\n",
    )
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

    with pytest.raises(LatexProbeError, match=diagnostic):
        compile_latex_probe(tmp_path / "published")


@pytest.mark.e2e
def test_installed_wheel_can_compile_latex_probe(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    installed = tmp_path / "installed"
    probe = tmp_path / "probe"
    wheelhouse.mkdir()
    build = subprocess.run(
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
        check=False,
        text=True,
        capture_output=True,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    wheel = next(wheelhouse.glob("axiomfig-*.whl"))
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(installed),
            str(wheel),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    isolated = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "import axiomfig; "
                "from axiomfig.latex import compile_latex_probe; "
                f"assert Path(axiomfig.__file__).is_relative_to(Path({str(installed)!r})); "
                f"result = compile_latex_probe(Path({str(probe)!r})); "
                "assert result.pdf.is_file(); "
                "print(result.pdf)"
            ),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(installed)},
        check=False,
        text=True,
        capture_output=True,
    )
    assert isolated.returncode == 0, isolated.stdout + isolated.stderr
    assert str(probe / "probe.pdf") in isolated.stdout


@pytest.mark.e2e
def test_vector_wrapper_rejects_siunitx_macro_in_matplotlib_mathtext(tmp_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    axis.plot([0, 1], [0, 1])
    axis.set_title(r"$\qty{10}{\milli\gram\per\litre}$")

    with pytest.raises(ValueError, match=r"Unknown symbol: \\qty"):
        render_figure(
            figure,
            tmp_path / "matplotlib-macro",
            tectonic="/opt/homebrew/bin/tectonic",
        )

    plt.close(figure)
