from __future__ import annotations

import re
from pathlib import Path

import pytest


def test_gallery_is_serif_only_family_first_and_curated() -> None:
    from axiomfig.gallery import GALLERY_SPECS, GALLERY_TYPOGRAPHY
    from axiomfig.templates.bar.gallery_cases import BAR_GALLERY_CASE_IDS
    from axiomfig.templates.registry import public_template_specs

    assert GALLERY_TYPOGRAPHY == "serif"
    assert len(BAR_GALLERY_CASE_IDS) == 16
    compatibility = {
        spec.template_id for spec in public_template_specs() if not spec.agent_recommended
    }
    assert compatibility == {"bar/vertical", "bar/horizontal", "bar/dot"}
    assert not ({spec.template_id for spec in GALLERY_SPECS} & compatibility)
    assert {spec.template_id for spec in GALLERY_SPECS if spec.family == "bar"} == {
        "bar/simple",
        "bar/grouped",
        "bar/stacked",
        "bar/normalized_stacked",
        "bar/grouped_stacked",
        "bar/diverging_stacked",
        "bar/range",
        "bar/mirrored",
        "bar/waterfall",
    }
    assert all(spec.output_id.count("/") == 1 for spec in GALLERY_SPECS)


def test_expected_gallery_paths_are_curated_registry_projection() -> None:
    from axiomfig.gallery import GALLERY_SPECS, expected_gallery_stems

    assert set(expected_gallery_stems()) == {spec.output_id for spec in GALLERY_SPECS}
    assert len(expected_gallery_stems()) == len(GALLERY_SPECS)


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


def test_committed_gallery_is_flat_complete_and_has_no_retired_namespaces() -> None:
    from axiomfig.gallery import expected_gallery_stems

    gallery = Path(__file__).resolve().parents[1] / "gallery"
    expected = set(expected_gallery_stems())
    pdfs = {path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")}
    pngs = {path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")}

    assert pdfs == pngs == expected
    assert not any(re.match(r"(?:^|/)\d+_", stem) for stem in pdfs)
    assert not {
        "sans",
        "serif",
        "technical",
        "capability_audit",
        "archive",
    } & {path.name for path in gallery.iterdir() if path.is_dir()}
    assert {path.name for path in gallery.iterdir() if path.is_dir()} == {
        stem.split("/", maxsplit=1)[0] for stem in expected
    }


def test_maintenance_scripts_do_not_recreate_retired_gallery_namespaces() -> None:
    root = Path(__file__).resolve().parents[1]
    retired = tuple(
        f"gallery/{name}" for name in ("sans", "serif", "technical", "capability_audit", "archive")
    )
    for path in (root / "scripts").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(namespace in text for namespace in retired), path


def test_gallery_prepare_accepts_only_family_directories(tmp_path: Path) -> None:
    from axiomfig.gallery import _prepare_gallery

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / "README.md").write_text("Gallery\n", encoding="utf-8")
    retired = gallery / "sans"
    retired.mkdir()

    with pytest.raises(RuntimeError, match="unexpected Gallery content"):
        _prepare_gallery(gallery)


@pytest.mark.e2e
def test_gallery_builds_only_curated_pdf_png_pairs(tmp_path: Path) -> None:
    from axiomfig.gallery import build_gallery, expected_gallery_stems
    from axiomfig.validation import validate_gallery

    gallery = tmp_path / "gallery"
    results = build_gallery(gallery, work_root=tmp_path / "work")
    expected = set(expected_gallery_stems())
    entries = validate_gallery(gallery, expected_stems=expected)

    assert len(results) == len(expected)
    assert len(entries) == len(expected)
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")
    } == expected
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")
    } == expected
