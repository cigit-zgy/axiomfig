import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from axiomfig.latex import compile_latex_probe
from axiomfig.rendering import render_figure

ROOT = Path(__file__).resolve().parents[1]


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
