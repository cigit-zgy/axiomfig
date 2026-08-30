from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agent_protocol_benchmark_is_structurally_valid() -> None:
    from tests.evaluation.agent_protocol import validate_agent_protocol_cases

    result = validate_agent_protocol_cases(ROOT / "tests/evaluation/agent_protocol_cases.yaml")

    assert result.case_count == 72
    assert result.render_count == 55
    assert result.public_families == 13
    assert result.actual_llm_runs == 0


def test_agent_protocol_benchmark_covers_decision_boundaries() -> None:
    from tests.evaluation.agent_protocol import validate_agent_protocol_cases

    result = validate_agent_protocol_cases(ROOT / "tests/evaluation/agent_protocol_cases.yaml")

    assert result.actions == {
        "clarify": 6,
        "render": 55,
        "require_precomputed": 5,
        "unsupported": 6,
    }
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
    } <= result.intent_classes
