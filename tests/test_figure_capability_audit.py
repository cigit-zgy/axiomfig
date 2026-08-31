from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "gallery" / "capability_audit"
ARCHIVE = ROOT / "gallery" / "archive" / "layout_engine_round01"
CASES = ROOT / "tests" / "evaluation" / "figure_capability" / "cases.yaml"


def _case_rows() -> list[dict[str, object]]:
    document = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    cases = document["cases"]
    assert isinstance(cases, list)
    return cases


def _pdf_set(directory: Path) -> set[str]:
    return {path.name for path in directory.glob("*.pdf")}


def _archive_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted(ARCHIVE.rglob("*.pdf")):
        digest.update(path.relative_to(ARCHIVE).as_posix().encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _page_font_rows(path: Path) -> list[tuple[str, str]]:
    page = PdfReader(path).pages[0]
    resources = page["/Resources"].get_object()
    fonts = resources.get("/Font", {})
    return [
        (str(font.get_object().get("/Subtype")), str(font.get_object().get("/BaseFont")))
        for font in fonts.values()
    ]


def test_figure_capability_manifest_has_twenty_unique_cases() -> None:
    cases = _case_rows()
    assert [case["id"] for case in cases] == [f"{index:02d}" for index in range(1, 21)]
    assert len({case["name"] for case in cases}) == 20
    for case in cases:
        assert case["researcher_request"]
        assert case["available_data"]
        assert case["expected_anatomy"]
        assert case["positioning_relations"]
        assert case["publication_geometry"]
        assert "expected_action" not in case


def test_archived_layout_round_is_byte_identical() -> None:
    assert len(list(ARCHIVE.rglob("*.pdf"))) == 50
    assert _archive_digest() == "39e00a68d0c3422103856b5dd81936a6cc7768544ab32eb6a147a6f99f61c9af"


def test_capability_audit_has_exact_original_and_native_projection() -> None:
    names = {f"{case['id']}_{case['name']}.pdf" for case in _case_rows()}
    assert _pdf_set(AUDIT / "original") == names
    assert _pdf_set(AUDIT / "matplotlib_native") == names


def test_capability_pdfs_are_single_page_serif_without_type3() -> None:
    for column in ("original", "matplotlib_native"):
        for path in sorted((AUDIT / column).glob("*.pdf")):
            reader = PdfReader(path)
            assert len(reader.pages) == 1, path
            page = reader.pages[0]
            assert float(page.mediabox.width) > 0
            assert float(page.mediabox.height) > 0
            assert all(subtype != "/Type3" for subtype, _base in _page_font_rows(path)), path
            if column == "matplotlib_native":
                assert any(
                    "XCharter" in base or "Charter" in base
                    for _subtype, base in _page_font_rows(path)
                ), path


def test_native_page_dimensions_match_frozen_publication_geometry() -> None:
    for case in _case_rows():
        path = AUDIT / "matplotlib_native" / f"{case['id']}_{case['name']}.pdf"
        page = PdfReader(path).pages[0]
        geometry = case["publication_geometry"]
        assert abs(float(page.mediabox.width) / 72 - geometry["width_in"]) <= 0.01
        assert abs(float(page.mediabox.height) / 72 - geometry["height_in"]) <= 0.01


def test_committed_attempt_summary_covers_every_native_case_and_budget() -> None:
    text = (AUDIT / "ATTEMPTS.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d{2}) \| (\d+) \|", text, flags=re.MULTILINE)

    assert [case_id for case_id, _attempts in rows] == [f"{index:02d}" for index in range(1, 21)]
    assert all(1 <= int(attempts) <= 10 for _case_id, attempts in rows)
    assert "Material attempts: **39**" in text


def test_native_five_run_repeatability_signatures_are_identical() -> None:
    build_path = ROOT / "scripts" / "build_figure_capability_audit.py"
    spec = importlib.util.spec_from_file_location("build_figure_capability_audit", build_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = {str(case["id"]): case for case in module._cases()}
    module.discover_fonts("serif")
    with module.mpl.rc_context(rc=module._rcparams()):
        for case_id, builder in module.NATIVE_BUILDERS.items():
            signatures = []
            for _repeat in range(5):
                figure = builder()
                geometry = cases[case_id]["publication_geometry"]
                figure.set_size_inches(geometry["width_in"], geometry["height_in"], forward=False)
                signatures.append(module._signature(figure))
                module.plt.close(figure)
            assert len(set(signatures)) == 1, case_id


def test_source_table_has_one_entry_per_case() -> None:
    text = (AUDIT / "SOURCES.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d{2}) \|", text, flags=re.MULTILINE)
    assert rows == [f"{index:02d}" for index in range(1, 21)]


def test_figure_anatomy_defines_four_position_classes_and_relations() -> None:
    text = (ROOT / "references" / "figure-anatomy.md").read_text(encoding="utf-8")
    for heading in (
        "## A — Data-bound",
        "## B — Structurally constrained",
        "## C — Renderer-measured fixed ornaments",
        "## D — Movable annotations",
    ):
        assert heading in text
    for relation in ("containment", "alignment", "non-overlap", "anchor"):
        assert relation in text.lower()
