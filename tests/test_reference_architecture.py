from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_skill_reference_map_is_compact_and_routable() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    reference_map = (ROOT / "references" / "README.md").read_text(encoding="utf-8")

    assert "references/element-contracts/index.md" in skill
    assert "references/template-knowledge/index.yaml" in skill
    assert "Figure Intent" in reference_map
    assert "element-contracts/index.md" in reference_map
    assert "template-knowledge/index.yaml" in reference_map
    assert "src/axiomfig/resources/" in reference_map
    assert "src/axiomfig/templates/" in reference_map


def test_low_level_visual_requests_preserve_semantic_goal_and_grammar() -> None:
    index = (ROOT / "references" / "element-contracts" / "index.md").read_text(encoding="utf-8")

    assert "Translate implementation wording into semantic intent" in index
    assert "Preserve the current scientific representation" in index
    assert "must not silently change scientific encoding" in index
    assert "Only an `AVAILABLE` surface may be emitted" in index
    assert "Matplotlib argument" in index
    assert "backend option" in index
