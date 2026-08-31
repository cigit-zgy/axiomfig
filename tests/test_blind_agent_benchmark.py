from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _render_decision() -> dict[str, object]:
    return {
        "action": "render",
        "template": "scatter.parity",
        "input_mode": "direct",
        "mapped_roles": {"observed": "measured", "predicted": "predicted"},
        "scientific_semantics": {},
        "scientific_inferences": [],
        "clarification_question": None,
        "upstream_requirement": None,
        "unsupported_reason": None,
        "figure_intent": {
            "template": "scatter.parity",
            "data": {"observed": "measured", "predicted": "predicted"},
        },
    }


def test_sanitized_workspace_exposes_only_the_agent_surface(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    copied = prepare_sanitized_workspace(ROOT, destination)

    assert destination / "SKILL.md" in copied
    assert destination / "references/agent-protocol.md" in copied
    assert destination / "references/figure-intent.md" in copied
    assert destination / "references/template-knowledge/index.yaml" in copied
    assert destination / "src/axiomfig/templates/index.yaml" in copied
    assert len(list(destination.glob("src/axiomfig/templates/*/contract.yaml"))) == 14
    assert not (destination / "tests").exists()
    assert not (destination / "reports").exists()
    assert not (destination / ".git").exists()
    assert not any(path.is_symlink() for path in destination.rglob("*"))


def test_case_prompt_excludes_gold_metadata_and_case_identifier(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import build_agent_prompt, prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    case = {
        "id": "SECRET-CASE-ID",
        "request": "Compare measured and predicted nitrate concentrations.",
        "available_data": {"format": "csv", "columns": ["measured", "predicted"]},
        "language": "en",
        "classes": ["SECRET-CLASS"],
        "expected": {"action": "render", "reason": "GOLD-ANSWER-SENTINEL"},
    }

    prompt = build_agent_prompt(destination, case)

    assert case["request"] in prompt
    assert '"measured"' in prompt
    assert "SECRET-CASE-ID" not in prompt
    assert "SECRET-CLASS" not in prompt
    assert "GOLD-ANSWER-SENTINEL" not in prompt
    assert "agent_protocol_cases.yaml" not in prompt
    assert "agent_scoring.py" not in prompt
    assert "reports/" not in prompt
    assert ".git/" not in prompt


def test_agent_decision_parser_accepts_one_valid_render_decision() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = parse_agent_decision(json.dumps(_render_decision()))

    assert decision["template"] == "scatter/parity"
    assert decision["mapped_roles"] == {
        "observed": "measured",
        "predicted": "predicted",
    }


@pytest.mark.parametrize("payload", ["", "not json", "{}\n{}"])
def test_agent_decision_parser_rejects_missing_invalid_or_multiple_results(payload: str) -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="single JSON object"):
        parse_agent_decision(payload)


def test_agent_decision_parser_rejects_unknown_action() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["action"] = "guess"

    with pytest.raises(ValueError, match="invalid action"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_unknown_template() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["template"] = "scatter.unknown"
    figure_intent = decision["figure_intent"]
    assert isinstance(figure_intent, dict)
    figure_intent["template"] = "scatter.unknown"

    with pytest.raises(ValueError, match="unknown template"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_role_mapping_that_differs_from_intent() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["mapped_roles"] = {"observed": "predicted", "predicted": "measured"}

    with pytest.raises(ValueError, match="mapped_roles must match Figure Intent data"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_requires_material_clarification_question() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        **_render_decision(),
        "action": "clarify",
        "template": None,
        "input_mode": None,
        "mapped_roles": {},
        "clarification_question": "",
        "figure_intent": None,
    }

    with pytest.raises(ValueError, match="clarification_question"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_accepts_safe_candidate_on_clarification() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        **_render_decision(),
        "action": "clarify",
        "template": "line.single",
        "input_mode": "direct",
        "mapped_roles": None,
        "scientific_semantics": {"candidate": "ordered trajectory"},
        "clarification_question": "Should x map to time and y map to concentration?",
        "figure_intent": None,
    }

    parsed = parse_agent_decision(json.dumps(decision))

    assert parsed["template"] == "line/single"
    assert parsed["mapped_roles"] == {}


def test_agent_decision_parser_accepts_null_semantics_when_clarifying() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        **_render_decision(),
        "action": "clarify",
        "template": "estimation.forest",
        "input_mode": "precomputed",
        "scientific_semantics": None,
        "clarification_question": "Are these differences or ratios, and what null applies?",
        "figure_intent": None,
    }

    parsed = parse_agent_decision(json.dumps(decision))

    assert parsed["scientific_semantics"] == {}


def test_agent_decision_parser_accepts_provisional_direct_mapping_on_clarification() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        **_render_decision(),
        "action": "clarify",
        "template": None,
        "input_mode": "direct",
        "mapped_roles": {"x": "x", "y": "y"},
        "scientific_semantics": {"x": "dose", "y": "response"},
        "clarification_question": "Does dose order represent a trajectory?",
        "figure_intent": None,
    }

    parsed = parse_agent_decision(json.dumps(decision))

    assert parsed["input_mode"] == "direct"
    assert parsed["mapped_roles"] == {"x": "x", "y": "y"}


def test_scoring_record_attaches_hidden_case_id_after_agent_response() -> None:
    from tests.evaluation.blind_agent import scoring_record

    record = scoring_record("S04-unrelated-quantities-scatter", _render_decision())

    assert record["id"] == "S04-unrelated-quantities-scatter"
    assert record["clarification_reason"] is None
    assert "clarification_question" not in record


def test_blind_runner_hides_id_from_external_agent_and_attaches_it_afterward(
    tmp_path: Path,
) -> None:
    from tests.evaluation.blind_agent import run_blind_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render, template: scatter.parity, gold: GOLD-SENTINEL}
""",
        encoding="utf-8",
    )
    decision = json.dumps(_render_decision())
    fake_agent = (
        "import sys; prompt=sys.stdin.read(); "
        "assert 'hidden-case' not in prompt; assert 'GOLD-SENTINEL' not in prompt; "
        f"print({decision!r})"
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_blind_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", fake_agent],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (1, 0)
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["id"] == "hidden-case"
    assert not output.with_suffix(".failures.jsonl").read_text(encoding="utf-8")


def test_blind_runner_preserves_raw_stdout_for_parser_failures(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import run_blind_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render}
""",
        encoding="utf-8",
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_blind_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", "print('not-json')"],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (0, 1)
    assert (tmp_path / "run/logs/001.stdout").read_text(encoding="utf-8") == "not-json\n"
