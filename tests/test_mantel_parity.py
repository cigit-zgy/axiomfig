from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references" / "mantel-r-parity.yaml"


def _entries() -> list[dict[str, object]]:
    document = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert document["version"] == 1
    return document["examples"]


def test_r_parity_manifest_covers_all_reference_projects_and_visual_grammar() -> None:
    entries = _entries()
    assert len(entries) >= 30
    assert {entry["source"] for entry in entries} == {"corrplot", "linkET", "ggcor"}
    assert len({entry["id"] for entry in entries}) == len(entries)
    assert len({entry["expected_output"] for entry in entries}) == len(entries)

    compositions = [entry["composition"] for entry in entries]
    assert {item.get("matrix_method") for item in compositions} >= {
        "circle",
        "square",
        "ellipse",
        "number",
        "shade",
        "color",
        "pie",
    }
    assert {item.get("matrix_type") for item in compositions} >= {"full", "upper", "lower"}
    assert {item.get("order") for item in compositions} >= {
        "original",
        "alphabet",
        "AOE",
        "FPC",
        "hclust",
    }
    assert {item.get("significance_mode") for item in compositions} >= {
        "mark",
        "p_value",
        "blank",
        "label_sig",
    }
    assert {item.get("ci_mode") for item in compositions} >= {"square", "circle", "rect"}


def test_every_manifest_example_has_a_committed_pdf_png_pair() -> None:
    entries = _entries()
    for entry in entries:
        stem = ROOT / str(entry["expected_output"])
        assert stem.with_suffix(".pdf").is_file(), entry["id"]
        assert stem.with_suffix(".png").is_file(), entry["id"]
