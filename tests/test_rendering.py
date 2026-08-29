from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib import font_manager

from axiomfig.rendering import RenderError, render_figure, standalone_tex
from axiomfig.typography import FontContractError, apply_figure_typography, font_for_language
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
    axis.legend(title="硝化效率")

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


def test_typography_pass_preserves_artist_metrics_while_replacing_font_file() -> None:
    figure, axis = plt.subplots()
    title = axis.set_title("Nitrification", fontsize=8.5, fontweight="bold", fontstyle="italic")
    title.set_fontstretch("condensed")
    before = title.get_fontproperties()

    apply_figure_typography(figure, mode="sans")

    after = title.get_fontproperties()
    assert after.get_file() is not None
    assert after.get_size_in_points() == before.get_size_in_points()
    assert after.get_weight() == before.get_weight()
    assert after.get_style() == before.get_style()
    assert after.get_stretch() == before.get_stretch()
    plt.close(figure)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mode", "expected_math"),
    [("sans", "FiraMath"), ("serif", "LatinModernMath")],
)
def test_render_pipeline_uses_exact_math_for_pure_math_artist(
    tmp_path: Path, mode: str, expected_math: str
) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    axis.text(0.5, 0.5, r"$\mu_{\max}$", transform=axis.transAxes)

    result = render_figure(figure, tmp_path / mode, typography=mode)
    entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)

    assert any(expected_math in row for row in entry.fonts)
    plt.close(figure)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mode", "expected_bold"),
    [("sans", "LMSans10-Bold"), ("serif", "LMRoman10-Bold")],
)
def test_render_pipeline_embeds_exact_bold_latin_artist_variant(
    tmp_path: Path, mode: str, expected_bold: str
) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    axis.text(0.0, 1.0, "(a)", transform=axis.transAxes, fontweight="bold")

    result = render_figure(figure, tmp_path / mode, typography=mode)
    entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)

    assert any(expected_bold in row for row in entry.fonts)
    plt.close(figure)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mode", "expected_variant"),
    [("sans", "LMSans10-BoldOblique"), ("serif", "LMRoman10-BoldItalic")],
)
def test_render_pipeline_embeds_bold_italic_variant_for_semibold_numeric_weight(
    tmp_path: Path, mode: str, expected_variant: str
) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    axis.text(0.0, 1.0, "(a)", transform=axis.transAxes, fontweight=600, fontstyle="italic")

    result = render_figure(figure, tmp_path / mode, typography=mode)
    entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)

    assert any(expected_variant in row for row in entry.fonts)
    plt.close(figure)


@pytest.mark.e2e
def test_render_pipeline_assigns_serif_font_to_figure_level_legend(tmp_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(3.543307, 2.65748))
    line = axis.plot([0, 1], [0, 1])[0]
    figure.legend([line], ["Model estimate"])

    result = render_figure(figure, tmp_path / "figure-legend", typography="serif")
    entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)

    assert any("LMRoman10-Regular" in row for row in entry.fonts)
    plt.close(figure)


def test_typography_pass_rejects_cross_mode_explicit_font_before_render() -> None:
    figure, axis = plt.subplots()
    axis.set_title("Title", fontproperties=font_for_language("en", mode="sans"))

    with pytest.raises(FontContractError, match="not the exact allowed"):
        apply_figure_typography(figure, mode="serif")
    plt.close(figure)


def test_typography_pass_rejects_mixed_script_even_with_explicit_font() -> None:
    figure, axis = plt.subplots()
    axis.set_title("Title 硝化效率", fontproperties=font_for_language("en", mode="sans"))

    with pytest.raises(FontContractError, match="segmented multilingual helper"):
        apply_figure_typography(figure, mode="sans")
    plt.close(figure)


def test_typography_pass_rejects_dejavu_explicit_font() -> None:
    figure, axis = plt.subplots()
    dejavu = font_manager.FontProperties(
        fname=font_manager.findfont(font_manager.FontProperties(family=["DejaVu Sans"]))
    )
    axis.set_title("Title", fontproperties=dejavu)

    with pytest.raises(FontContractError, match="not the exact allowed"):
        apply_figure_typography(figure, mode="serif")
    plt.close(figure)
