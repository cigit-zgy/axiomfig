from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "references/template-knowledge"


def test_knowledge_index_routes_to_existing_topics_and_templates() -> None:
    from axiomfig.templates.registry import load_template_registry

    document = yaml.safe_load((KNOWLEDGE_ROOT / "index.yaml").read_text(encoding="utf-8"))
    specs = load_template_registry()
    recommended = {spec.template_id for spec in specs if spec.agent_recommended}

    assert document["version"] == 1
    assert 10 <= len(document["intents"]) <= 15
    for route in document["intents"].values():
        assert (KNOWLEDGE_ROOT / route["topic"]).is_file()
        assert {template.replace(".", "/") for template in route["templates"]} <= recommended
    assert "bar" in document["family_guides"]
    assert set(document["family_guides"]) <= {spec.family for spec in specs if spec.public}
    for guide in document["family_guides"].values():
        assert (KNOWLEDGE_ROOT / guide).is_file()


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


def test_bar_family_guide_covers_each_grammar_without_schema_semantic_leakage() -> None:
    guide = (KNOWLEDGE_ROOT / "families/bar.md").read_text(encoding="utf-8")
    grammars = (
        "simple",
        "grouped",
        "stacked",
        "normalized_stacked",
        "grouped_stacked",
        "diverging_stacked",
        "range",
        "mirrored",
        "waterfall",
    )

    for grammar in grammars:
        assert f"`bar.{grammar}`" in guide
    assert guide.count("|---") >= len(grammars) + 1
    assert "`category`, `component`, `value`, `normalization`" not in guide
    assert "`category`, `side`, `value`, `mirror_side`" not in guide
    for heading in (
        "# Bar charts",
        "## Scientific role",
        "## Canonical tabular/DataFrame contracts",
        "## Selection rules",
        "## Modifiers",
        "## Scientific boundaries",
        "## Neighboring / non-Bar charts",
    ):
        assert heading in guide


def test_bar_family_guide_columns_and_endpoint_intent_match_executable_contracts() -> None:
    from axiomfig.intent import parse_figure_intent
    from axiomfig.templates.registry import load_family_contract, public_template_specs

    guide = (KNOWLEDGE_ROOT / "families/bar.md").read_text(encoding="utf-8")
    contract = load_family_contract("bar")["variants"]
    rows = re.findall(r"^\| `bar\.([^`]+)` \| [^|]+ \| ([^|]+) \|$", guide, re.MULTILINE)
    assert {variant for variant, _ in rows} == {
        spec.variant
        for spec in public_template_specs()
        if spec.family == "bar" and spec.agent_recommended
    }
    for variant, columns in rows:
        declared = set(contract[variant]["required"]) | set(contract[variant]["optional"])
        assert set(re.findall(r"`([^`]+)`", columns)) <= declared

    examples = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert examples
    for example in examples:
        parse_figure_intent(yaml.safe_load(example))
    for variant in ("simple", "grouped"):
        assert {"lower", "upper", "error", "uncertainty_type"} <= set(contract[variant]["optional"])
        data = {"category": "category", "value": "value", "lower": "lower", "upper": "upper"}
        if variant == "grouped":
            data["group"] = "group"
        parsed = parse_figure_intent(
            {
                "template": f"bar.{variant}",
                "data": data,
                "semantics": {"uncertainty_type": "95% CI"},
            }
        )
        assert dict(parsed.data) == data
