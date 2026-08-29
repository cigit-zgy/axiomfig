from pathlib import Path

from axiomfig.rendering import standalone_tex

ROOT = Path(__file__).resolve().parents[1]


def test_latex_contract_records_exact_general_scientific_macros() -> None:
    source = (ROOT / "references" / "latex-contract.md").read_text(encoding="utf-8")

    required = (
        r"\unit{\milli\gram\per\litre}",
        r"\qty{10}{\milli\gram\per\litre}",
        r"\ce{NH4+}",
        r"\begin{align}",
        r"\operatorname{growth}",
        r"\setmathfont{XCharter Math}",
        r"\symup{Re}",
        r"\symbf{x}",
        r"\definecolor{AxiomBlue}{HTML}{315A7D}",
        r"\textcolor{AxiomBlue}",
    )
    assert all(fragment in source for fragment in required)


def test_vector_wrapper_is_honest_about_non_tex_native_plot_text() -> None:
    source = standalone_tex("intermediate.pdf")

    assert r"\includegraphics{intermediate.pdf}" in source
    assert r"\usepackage{axiomfig}" not in source
    assert r"\qty" not in source
    assert r"\ce" not in source


def test_repository_latex_package_matches_packaged_generic_infrastructure() -> None:
    repository_style = ROOT / "latex" / "axiomfig.sty"
    repository_colors = ROOT / "latex" / "axiomfig-colors.tex"
    packaged = ROOT / "src" / "axiomfig" / "resources" / "latex"

    assert repository_style.read_bytes() == (packaged / "axiomfig.sty").read_bytes()
    assert repository_colors.read_bytes() == (packaged / "axiomfig-colors.tex").read_bytes()
    assert (ROOT / "latex" / "README.md").is_file()


def test_xcharter_probe_text_preserves_unit_chemistry_and_math_semantics() -> None:
    from axiomfig.latex import _validate_semantics

    extracted = (
        "Units marker: 10 mg L−1 .\n"
        "Chemistry markers: NH4 + ; NO3 – ; PO4 3 – .\n"
        "Math marker: 𝜇max , 𝛼, 𝛽.\n"
    )
    _validate_semantics(extracted)
