from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from axiomfig.rendering import RenderError, render_figure, standalone_tex
from axiomfig.typography import FontContractError, apply_figure_typography
from axiomfig.validation import inspect_pdf, validate_pair


def test_standalone_tex_wraps_vector_intermediate() -> None:
    source = standalone_tex("intermediate.pdf")

    assert "\\documentclass[border=0pt]{standalone}" in source
    assert "\\includegraphics{intermediate.pdf}" in source


def test_missing_tectonic_fails_with_diagnostic(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    with pytest.raises(RenderError, match="Tectonic executable"):
        render_figure(fig, tmp_path / "figure", tectonic="/missing/tectonic")

    plt.close(fig)


@pytest.mark.e2e
def test_tectonic_creates_parseable_pdf_and_preview(tmp_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(3.543307, 2.65748))
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("Time (d)")
    ax.set_ylabel(r"$S_{NH4}$ (mg L$^{-1}$)")

    result = render_figure(fig, tmp_path / "figure")
    info = inspect_pdf(result.pdf)

    assert result.pdf.is_file()
    assert result.png.is_file()
    assert result.tectonic_command[0].endswith("tectonic")
    assert info.page_count == 1
    assert info.width_mm == pytest.approx(90.0, abs=0.2)
    assert info.height_mm == pytest.approx(67.5, abs=0.2)
    plt.close(fig)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mode", "expected_fonts"),
    [
        ("sans", ("LMSans10", "NotoSansCJKsc", "NotoSansCJKjp")),
        ("serif", ("LMRoman10", "NotoSerifCJKsc", "NotoSerifCJKjp")),
    ],
)
def test_render_pipeline_assigns_exact_fonts_to_ordinary_multilingual_artists(
    tmp_path: Path, mode: str, expected_fonts: tuple[str, ...]
) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    axis.plot([0, 1], [0, 1], label="硝化效率")
    axis.set(title="Nitrification", xlabel="硝化效率", ylabel="硝化の効率")
    axis.annotate("硝化效率", (0.5, 0.5))
    axis.text(0.5, 0.2, r"$\mu_{\max}$", transform=axis.transAxes)

    result = render_figure(figure, tmp_path / mode, typography=mode)
    entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)

    assert all(any(expected in row for row in entry.fonts) for expected in expected_fonts)
    plt.close(figure)


def test_typography_pass_rejects_unsegmentable_mixed_plain_scripts() -> None:
    figure, axis = plt.subplots()
    axis.set_xlabel("Nitrification 硝化效率")

    with pytest.raises(FontContractError, match="segmented multilingual helper"):
        apply_figure_typography(figure, mode="sans")

    plt.close(figure)
