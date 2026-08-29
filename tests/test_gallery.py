from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_STEMS = (
    "01_single_line",
    "02_multi_line",
    "03_line_marker",
    "04_line_ci",
    "05_scatter",
    "06_grouped_scatter",
    "07_parity",
    "08_regression_scatter",
    "09_vertical_bar",
    "10_grouped_bar",
    "11_horizontal_bar",
    "12_stacked_bar",
    "13_boxplot",
    "14_violin",
    "15_box_violin",
    "16_histogram",
    "17_heatmap",
    "18_errorbar",
    "19_model_evaluation",
    "20_multi_panel",
)


def test_gallery_registry_is_two_matching_twenty_case_families() -> None:
    from axiomfig.gallery import GALLERY_MODES, GALLERY_SPECS

    assert GALLERY_MODES == ("sans", "serif")
    assert tuple(spec.stem for spec in GALLERY_SPECS) == EXPECTED_STEMS
    assert tuple(spec.template for spec in GALLERY_SPECS) == tuple(
        stem.split("_", maxsplit=1)[1].replace("_", "-") for stem in EXPECTED_STEMS
    )


@pytest.mark.e2e
def test_gallery_builds_only_canonical_pdf_png_pairs(tmp_path: Path) -> None:
    from axiomfig.gallery import GALLERY_MODES, build_gallery
    from axiomfig.validation import validate_gallery

    gallery = tmp_path / "gallery"
    results = build_gallery(gallery, work_root=tmp_path / "work")
    expected_paths = {f"{mode}/{stem}" for mode in GALLERY_MODES for stem in EXPECTED_STEMS}
    entries = validate_gallery(gallery, expected_stems=expected_paths)

    assert len(results) == 40
    assert len(entries) == 40
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")
    } == expected_paths
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")
    } == expected_paths
