from __future__ import annotations

import re
from pathlib import Path

import pytest


def test_gallery_specs_are_derived_from_public_template_registry() -> None:
    from axiomfig.gallery import GALLERY_MODES, GALLERY_SPECS
    from axiomfig.templates.registry import public_template_specs

    public = public_template_specs()
    assert GALLERY_MODES == ("sans", "serif")
    assert tuple(spec.template_id for spec in GALLERY_SPECS) == tuple(
        spec.template_id for spec in public
    )
    assert tuple(spec.geometry for spec in GALLERY_SPECS) == tuple(spec.geometry for spec in public)


def test_gallery_declares_semantic_technical_latex_cases() -> None:
    from axiomfig.gallery import TECHNICAL_LATEX_STEMS

    assert TECHNICAL_LATEX_STEMS == ("scientific_typography", "palettes")


def test_expected_gallery_paths_are_registry_projection() -> None:
    from axiomfig.gallery import expected_gallery_stems
    from axiomfig.templates.registry import public_template_specs

    expected = {
        *(
            f"{mode}/{spec.template_id}"
            for mode in ("sans", "serif")
            for spec in public_template_specs()
        ),
        "technical/latex/scientific_typography",
        "technical/latex/palettes",
    }
    assert set(expected_gallery_stems()) == expected
    assert len(expected) == 68


def test_gallery_cli_validates_registry_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from axiomfig import cli
    from axiomfig.gallery import expected_gallery_stems

    captured: dict[str, set[str]] = {}
    monkeypatch.setattr(cli, "build_gallery", lambda *args, **kwargs: [])

    def capture(_gallery: Path, *, expected_stems: object) -> list[object]:
        captured["expected"] = set(expected_stems)  # type: ignore[arg-type]
        return []

    monkeypatch.setattr(cli, "validate_gallery", capture)

    assert cli.gallery_main(["--gallery", str(tmp_path / "gallery")]) == 0
    assert captured["expected"] == set(expected_gallery_stems())


def test_committed_gallery_has_no_numbered_flat_or_orphan_artifacts() -> None:
    from axiomfig.gallery import expected_gallery_stems

    gallery = Path(__file__).resolve().parents[1] / "gallery"
    expected = set(expected_gallery_stems())
    pdfs = {path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")}
    pngs = {path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")}

    assert pdfs == pngs == expected
    assert not any(re.match(r"(?:^|/)\d+_", stem) for stem in pdfs)


@pytest.mark.e2e
def test_gallery_builds_only_registry_pdf_png_pairs(tmp_path: Path) -> None:
    from axiomfig.gallery import build_gallery, expected_gallery_stems
    from axiomfig.validation import validate_gallery

    gallery = tmp_path / "gallery"
    results = build_gallery(gallery, work_root=tmp_path / "work")
    expected = set(expected_gallery_stems())
    entries = validate_gallery(gallery, expected_stems=expected)

    assert len(results) == 68
    assert len(entries) == 68
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")
    } == expected
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")
    } == expected
