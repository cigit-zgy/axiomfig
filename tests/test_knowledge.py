from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "references/template-knowledge"


def test_knowledge_index_routes_to_existing_topics_and_templates() -> None:
    from axiomfig.templates.registry import load_template_registry

    document = yaml.safe_load((KNOWLEDGE_ROOT / "index.yaml").read_text(encoding="utf-8"))
    registered = {spec.template_id for spec in load_template_registry()}

    assert document["version"] == 1
    assert 10 <= len(document["intents"]) <= 15
    for route in document["intents"].values():
        assert (KNOWLEDGE_ROOT / route["topic"]).is_file()
        assert {template.replace(".", "/") for template in route["templates"]} <= registered


def test_registry_stays_discovery_only_and_knowledge_stays_compact() -> None:
    registry = ROOT / "src/axiomfig/templates/index.yaml"
    registry_text = registry.read_text(encoding="utf-8")
    knowledge_text = (KNOWLEDGE_ROOT / "index.yaml").read_text(encoding="utf-8")

    assert "recommend" not in registry_text.lower()
    assert "use when" not in registry_text.lower()
    assert registry.stat().st_size < 5000
    assert len(registry_text.splitlines()) < 140
    assert len(knowledge_text.splitlines()) < 40


def test_skill_routes_progressively_without_requiring_all_sources() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "references/template-knowledge/index.yaml" in skill
    assert "src/axiomfig/templates/index.yaml" in skill
    assert "src/axiomfig/templates/<family>/contract.yaml" in skill
    assert "Do not read all builders" in skill
