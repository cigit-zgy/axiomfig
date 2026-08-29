from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_STEMS = (
    "01_line",
    "02_scatter",
    "03_bar",
    "04_violin",
    "05_heatmap",
    "06_multi_panel",
)


def test_gallery_registry_is_two_matching_six_case_families() -> None:
    from axiomfig.gallery import GALLERY_MODES, GALLERY_SPECS

    assert GALLERY_MODES == ("sans", "serif")
    assert tuple(spec.stem for spec in GALLERY_SPECS) == EXPECTED_STEMS
    assert tuple(spec.template for spec in GALLERY_SPECS) == (
        "line",
        "scatter",
        "bar",
        "violin",
        "heatmap",
        "multi-panel",
    )


@pytest.mark.e2e
def test_gallery_builds_only_canonical_pdf_png_pairs(tmp_path: Path) -> None:
    from axiomfig.gallery import GALLERY_MODES, build_gallery
    from axiomfig.validation import validate_gallery

    gallery = tmp_path / "gallery"
    results = build_gallery(gallery, work_root=tmp_path / "work")
    expected_paths = {f"{mode}/{stem}" for mode in GALLERY_MODES for stem in EXPECTED_STEMS}
    entries = validate_gallery(gallery, expected_stems=expected_paths)

    assert len(results) == 12
    assert len(entries) == 12
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")
    } == expected_paths
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")
    } == expected_paths
