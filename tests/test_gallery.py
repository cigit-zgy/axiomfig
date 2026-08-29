from pathlib import Path

import pytest

from axiomfig.gallery import GALLERY_SPECS, build_gallery
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
]


def test_gallery_manifest_is_small_and_complete() -> None:
    assert [spec.stem for spec in GALLERY_SPECS] == EXPECTED_STEMS


@pytest.mark.e2e
def test_gallery_rebuild_creates_eight_valid_pdf_png_pairs(tmp_path: Path) -> None:
    gallery = tmp_path / "gallery"

    results = build_gallery(gallery, work_root=tmp_path / "work")
    entries = validate_gallery(gallery, expected_stems=EXPECTED_STEMS)

    assert len(results) == 8
    assert len(entries) == 8
    multilingual_text = extract_pdf_text(gallery / "07_multilingual.pdf")
    for required in ["Nitrification efficiency", "硝化效率", "硝化効率", "μ", "NH4", "α", "β"]:
        assert required in multilingual_text
    for stem in EXPECTED_STEMS:
        assert out_of_page_words(gallery / f"{stem}.pdf") == ()
    assert sorted(path.name for path in gallery.iterdir()) == sorted(
        [f"{stem}.pdf" for stem in EXPECTED_STEMS] + [f"{stem}.png" for stem in EXPECTED_STEMS]
    )
