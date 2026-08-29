from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pytest
from matplotlib.collections import PathCollection
from matplotlib.container import BarContainer
from matplotlib.ticker import AutoMinorLocator
from PIL import Image

from axiomfig.colors import PALETTES
from axiomfig.contracts import STROKE_WIDTH_PT
from axiomfig.gallery import GALLERY_SPECS, GEOMETRY_MM, GallerySpec, build_gallery
from axiomfig.styles import compose_styles
from axiomfig.templates import PROJECT_ROOT, TEMPLATE_BUILDERS, build_template
from axiomfig.typography import apply_figure_typography
from axiomfig.validation import extract_pdf_text, out_of_page_words, validate_gallery

EXPECTED_STEMS = [
    "01_line",
    "02_scatter",
    "03_bar",
    "04_violin",
    "05_heatmap",
    "06_model_evaluation",
    "07_multilingual",
    "08_multi_panel",
    "09_serif",
    "10_style_contract",
]


def test_gallery_manifest_is_small_and_complete() -> None:
    assert [spec.stem for spec in GALLERY_SPECS] == EXPECTED_STEMS


def test_gallery_registry_selects_the_required_serif_and_contract_cases() -> None:
    specs = {spec.stem: spec for spec in GALLERY_SPECS}

    assert TEMPLATE_BUILDERS["style-contract"] == ("style_contract.py", "build_style_contract")
    assert specs["09_serif"] == GallerySpec(
        "09_serif", "multilingual", "serif", "onehalf-column", "default", "line"
    )
    assert specs["10_style_contract"] == GallerySpec(
        "10_style_contract", "style-contract", "sans", "double-column", "default", "line"
    )


def test_style_contract_template_exercises_integrated_visual_tokens() -> None:
    spec = next(spec for spec in GALLERY_SPECS if spec.stem == "10_style_contract")
    composed = compose_styles(spec.selection().paths(PROJECT_ROOT / "styles"))

    with mpl.rc_context(rc=composed.params):
        figure = build_template(spec.template, typography=spec.typography)
        figure.set_size_inches(composed.params["figure.figsize"], forward=False)
        apply_figure_typography(figure, mode=spec.typography)
        figure.canvas.draw()

    line_axis, bar_axis, scatter_axis, heatmap_axis = figure.axes[:4]
    panel_pattern = re.compile(r"\([a-d]\)")
    panel_labels = [
        next(text for text in axis.texts if panel_pattern.fullmatch(text.get_text()))
        for axis in figure.axes[:4]
    ]
    panel_gaps = [
        label.get_window_extent(figure.canvas.get_renderer()).y0 - axis.bbox.y1
        for axis, label in zip(figure.axes[:4], panel_labels, strict=True)
    ]

    expected_first_color = f"#{next(iter(PALETTES['default'].values()))}"
    assert mcolors.same_color(line_axis.lines[0].get_color(), expected_first_color)
    assert line_axis.lines[0].get_linewidth() == STROKE_WIDTH_PT
    assert line_axis.xaxis._major_tick_kw["tickdir"] == "inout"
    assert line_axis.xaxis._minor_tick_kw["tickdir"] == "in"

    bar_containers = [
        container for container in bar_axis.containers if isinstance(container, BarContainer)
    ]
    bar_labels = [
        text.get_text() for text in bar_axis.texts if re.fullmatch(r"\d+\.\d{2}", text.get_text())
    ]
    assert len(bar_containers) == 2
    assert len(bar_labels) == 6
    assert all(
        patch.get_edgecolor()[:3] == (0.0, 0.0, 0.0)
        for container in bar_containers
        for patch in container
    )
    assert all(
        patch.get_linewidth() == STROKE_WIDTH_PT
        for container in bar_containers
        for patch in container
    )
    assert bar_axis.xaxis._major_tick_kw["tickdir"] == "out"
    assert bar_axis.xaxis._minor_tick_kw["tickdir"] == "out"

    scatter = next(
        collection
        for collection in scatter_axis.collections
        if isinstance(collection, PathCollection)
    )
    assert scatter.get_edgecolors()[0, :3] == pytest.approx((0.0, 0.0, 0.0))
    assert scatter.get_linewidths()[0] == STROKE_WIDTH_PT
    assert scatter_axis.xaxis._major_tick_kw["tickdir"] == "inout"
    assert scatter_axis.xaxis._minor_tick_kw["tickdir"] == "in"

    assert heatmap_axis.images
    assert heatmap_axis.xaxis._major_tick_kw["tickdir"] == "out"
    assert heatmap_axis.xaxis._minor_tick_kw["tickdir"] == "out"
    for axis in figure.axes[:4]:
        assert isinstance(axis.xaxis.get_minor_locator(), AutoMinorLocator)
        assert axis.xaxis.get_minor_locator().ndivs == 2
        assert all(spine.get_linewidth() == STROKE_WIDTH_PT for spine in axis.spines.values())
    assert max(panel_gaps) - min(panel_gaps) < 0.01

    legend = line_axis.get_legend()
    assert legend is not None
    legend_bbox = legend.get_window_extent(figure.canvas.get_renderer())
    assert legend._ncols == len(legend.get_texts())
    assert legend_bbox.x1 == pytest.approx(line_axis.bbox.x1, abs=0.01)
    plt.close(figure)


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _font_names(rows: tuple[str, ...]) -> set[str]:
    return {re.sub(r"^[A-Z]{6}\+", "", row.split()[0]) for row in rows}


@pytest.mark.e2e
def test_gallery_rebuild_is_deterministic_and_creates_ten_qa_complete_pairs(
    tmp_path: Path,
) -> None:
    gallery = tmp_path / "gallery-a"
    second_gallery = tmp_path / "gallery-b"

    results = build_gallery(gallery, work_root=tmp_path / "work")
    entries = validate_gallery(gallery, expected_stems=EXPECTED_STEMS)
    second_results = build_gallery(second_gallery, work_root=tmp_path / "work-second")
    second_entries = validate_gallery(second_gallery, expected_stems=EXPECTED_STEMS)

    assert len(results) == 10
    assert len(entries) == 10
    assert len(second_results) == 10
    assert len(second_entries) == 10
    multilingual_text = extract_pdf_text(gallery / "07_multilingual.pdf")
    for required in ["Nitrification efficiency", "硝化效率", "硝化効率", "μ", "NH4", "α", "β"]:
        assert required in multilingual_text
    serif_text = extract_pdf_text(gallery / "09_serif.pdf")
    for required in ["Nitrification efficiency", "硝化效率", "硝化効率", "μ", "NH4", "α", "β"]:
        assert required in serif_text
    contract_text = extract_pdf_text(gallery / "10_style_contract.pdf")
    for required in ["Open line", "Mechanistic", "Hybrid", "硝化效率", "硝化の効率"]:
        assert required in contract_text

    entries_by_stem = {entry.pdf.path.stem: entry for entry in entries}
    serif_fonts = _font_names(entries_by_stem["09_serif"].fonts)
    assert any(name.startswith("LMRoman10-") for name in serif_fonts)
    assert "LatinModernMath-Regular" in serif_fonts
    assert "NotoSerifCJKsc-Regular" in serif_fonts
    assert "NotoSerifCJKjp-Regular" in serif_fonts
    assert not any(
        forbidden in name
        for name in serif_fonts
        for forbidden in ("LMSans", "FiraMath", "NotoSans")
    )

    contract_fonts = _font_names(entries_by_stem["10_style_contract"].fonts)
    assert any(name.startswith("LMSans10-") for name in contract_fonts)
    assert "FiraMath-Regular" in contract_fonts
    assert "NotoSansCJKsc-Regular" in contract_fonts
    assert "NotoSansCJKjp-Regular" in contract_fonts
    assert not any("Type 3" in row for entry in entries for row in entry.fonts)

    specs_by_stem = {spec.stem: spec for spec in GALLERY_SPECS}
    for stem in EXPECTED_STEMS:
        assert out_of_page_words(gallery / f"{stem}.pdf") == ()
        width_mm, height_mm = GEOMETRY_MM[specs_by_stem[stem].geometry]
        info = entries_by_stem[stem].pdf
        assert info.width_mm == pytest.approx(width_mm, abs=0.25)
        assert info.height_mm == pytest.approx(height_mm, abs=0.25)
        with Image.open(gallery / f"{stem}.png") as image:
            assert image.format == "PNG"
            assert image.mode == "RGB"
            assert image.size == (
                math.ceil(width_mm / 25.4 * 300),
                math.ceil(height_mm / 25.4 * 300),
            )
        assert _sha256(gallery / f"{stem}.pdf") == _sha256(second_gallery / f"{stem}.pdf")
        assert _sha256(gallery / f"{stem}.png") == _sha256(second_gallery / f"{stem}.png")

    assert sorted(path.name for path in gallery.iterdir()) == sorted(
        [f"{stem}.pdf" for stem in EXPECTED_STEMS] + [f"{stem}.png" for stem in EXPECTED_STEMS]
    )

    manifest = json.loads((tmp_path / "work" / "gallery_manifest.json").read_text())
    manifest_by_stem = {entry["stem"]: entry for entry in manifest["figures"]}
    assert set(manifest_by_stem) == set(EXPECTED_STEMS)
    for stem in EXPECTED_STEMS:
        assert manifest_by_stem[stem]["pdf_sha256"] == _sha256(gallery / f"{stem}.pdf")
        assert manifest_by_stem[stem]["png_sha256"] == _sha256(gallery / f"{stem}.png")
