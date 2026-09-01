from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_agent_protocol_benchmark_is_structurally_valid() -> None:
    from axiomfig.templates.registry import public_template_specs
    from tests.evaluation.agent_protocol import validate_agent_protocol_cases

    path = ROOT / "tests/evaluation/agent_protocol_cases.yaml"
    result = validate_agent_protocol_cases(path)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = document["cases"]

    assert result.case_count == len(cases)
    assert result.render_count == sum(case["expected"]["action"] == "render" for case in cases)
    assert result.public_families == len(
        {spec.family for spec in public_template_specs() if spec.agent_recommended}
    )
    assert sum(result.languages.values()) == result.case_count
    assert result.languages["zh"] >= 12
    assert result.actual_llm_runs == 0


def test_agent_protocol_benchmark_covers_decision_boundaries() -> None:
    from tests.evaluation.agent_protocol import validate_agent_protocol_cases

    result = validate_agent_protocol_cases(ROOT / "tests/evaluation/agent_protocol_cases.yaml")

    assert set(result.actions) == {
        "clarify",
        "render",
        "require_precomputed",
        "unsupported",
    }
    assert result.actions["render"] == result.render_count
    assert all(count >= 10 for count in result.actions.values())
    assert {
        "ambiguous",
        "column_mapping",
        "composition",
        "direct_data",
        "explicit_template",
        "forbidden_inference",
        "geometry",
        "implicit_template",
        "invalid",
        "missing_precomputed",
        "precomputed_result",
        "typography",
        "unsupported_domain",
        "causality",
        "scientific_boundary",
        "scale_semantics",
        "unit_compatibility",
    } <= result.intent_classes
