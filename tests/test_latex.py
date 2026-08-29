from pathlib import Path

from axiomfig.rendering import standalone_tex

ROOT = Path(__file__).resolve().parents[1]


def test_latex_contract_records_exact_general_scientific_macros() -> None:
    source = (ROOT / "references" / "latex-contract.md").read_text(encoding="utf-8")

    required = (
        r"\unit{\milli\gram\per\liter}",
        r"\qty{10}{\milli\gram\per\liter}",
        r"\ce{NH4+}",
        r"\begin{align}",
        r"\operatorname{growth}",
        r"\setmathfont{Latin Modern Math}",
        r"\symup{Re}",
        r"\symbf{x}",
        r"\definecolor{AxiomBlue}{HTML}{4477AA}",
        r"\textcolor{AxiomBlue}",
    )
    assert all(fragment in source for fragment in required)


def test_vector_wrapper_is_honest_about_non_tex_native_plot_text() -> None:
    source = standalone_tex("intermediate.pdf")

    assert r"\includegraphics{intermediate.pdf}" in source
    assert r"\usepackage{axiomfig}" not in source
    assert r"\qty" not in source
    assert r"\ce" not in source
