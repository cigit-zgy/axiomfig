from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests/evaluation/agent_protocol_cases.yaml"


def _render_prediction(case: dict[str, object]) -> dict[str, object]:
    expected = case["expected"]
    assert isinstance(expected, dict)
    roles = list(expected["required_roles"])
    mapped_roles = {role: role for role in roles}
    semantics = {name: name for name in expected.get("required_semantics", [])}
    intent_semantics: dict[str, object] = {}
    if "ratio_null_one" in expected.get("required_semantics", []):
        semantics = {"reference": 1}
        intent_semantics["reference"] = 1
    figure_intent: dict[str, object] = {
        "template": expected["template"],
        "data": mapped_roles,
    }
    if intent_semantics:
        figure_intent["semantics"] = intent_semantics
    return {
        "id": case["id"],
        "action": "render",
        "template": expected["template"],
        "input_mode": expected["input_mode"],
        "mapped_roles": mapped_roles,
        "scientific_semantics": semantics,
        "scientific_inferences": [],
        "figure_intent": figure_intent,
    }


def _predictions() -> list[dict[str, object]]:
    document = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    predictions: list[dict[str, object]] = []
    for case in document["cases"]:
        expected = case["expected"]
        action = expected["action"]
        if action == "render":
            prediction = _render_prediction(case)
        elif action == "clarify":
            prediction = {
                "id": case["id"],
                "action": "clarify",
                "question": "What scientifically material meaning is missing?",
                "reason": expected["clarification_reason"],
            }
        elif action == "require_precomputed":
            prediction = {
                "id": case["id"],
                "action": "require_precomputed",
                "candidate_template": expected["template"],
                "missing_result": expected["reason"],
                "reason": "The supplied input does not contain the required upstream result.",
            }
        else:
            prediction = {
                "id": case["id"],
                "action": "unsupported",
                "reason": expected["reason"],
            }
        predictions.append(prediction)
    return predictions


def _write_predictions(tmp_path: Path, predictions: list[dict[str, object]]) -> Path:
    path = tmp_path / "predictions.jsonl"
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in predictions),
        encoding="utf-8",
    )
    return path


def _case(predictions: list[dict[str, object]], case_id: str) -> dict[str, object]:
    return next(item for item in predictions if item["id"] == case_id)


def test_agent_scorer_reports_perfect_predictions(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, _predictions()))

    assert result.total_cases == 120
    assert result.prediction_count == 120
    assert result.missing_count == 0
    assert result.unsafe_count == 0
    assert result.action_accuracy == 1.0
    assert result.render_template_accuracy == 1.0
    assert result.family_accuracy == 1.0
    assert result.input_mode_accuracy == 1.0
    assert result.clarification_accuracy == 1.0
    assert result.require_precomputed_accuracy == 1.0
    assert result.unsupported_scope_accuracy == 1.0
    assert result.scientific_boundary_safety_rate == 1.0
    assert result.valid_figure_intent_rate == 1.0


def test_agent_scorer_separates_wrong_template_from_family(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S04-unrelated-quantities-scatter")
    selected["template"] = "scatter.grouped"
    selected["mapped_roles"] = {"x": "x", "y": "y", "group": "group"}
    selected["figure_intent"] = {
        "template": "scatter.grouped",
        "data": {"x": "x", "y": "y", "group": "group"},
    }

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == 1.0
    assert result.render_template_accuracy == pytest.approx(69 / 70)
    assert result.family_accuracy == 1.0
    assert result.valid_figure_intent_rate == 1.0


def test_agent_scorer_marks_unsafe_render_instead_of_clarification(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "C13-zh-uncertainty-unknown")
    selected.clear()
    selected.update(
        id="C13-zh-uncertainty-unknown",
        action="render",
        template="line.errorbar",
        input_mode="precomputed",
        mapped_roles={
            "x": "x",
            "estimate": "estimate",
            "error": "error",
            "uncertainty_type": "error",
        },
        scientific_semantics={"uncertainty_type": "SD"},
        scientific_inferences=["uncertainty_type"],
        figure_intent={
            "template": "line.errorbar",
            "data": {
                "x": "x",
                "estimate": "estimate",
                "error": "error",
                "uncertainty_type": "error",
            },
        },
    )

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == pytest.approx(119 / 120)
    assert result.clarification_accuracy == pytest.approx(19 / 20)
    assert result.unsafe_count == 1


def test_agent_scorer_marks_unsafe_render_instead_of_upstream_analysis(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "P08-zh-mantel-raw")
    selected.clear()
    selected.update(
        id="P08-zh-mantel-raw",
        action="render",
        template="heatmap.basic",
        input_mode="direct",
        mapped_roles={
            "matrix": "abundance_matrix",
            "row_labels": "sample_labels",
            "column_labels": "feature_labels",
            "color_semantics": "color_semantics",
        },
        scientific_semantics={},
        scientific_inferences=["mantel_statistics"],
        figure_intent={
            "template": "heatmap.basic",
            "data": {
                "matrix": "abundance_matrix",
                "row_labels": "sample_labels",
                "column_labels": "feature_labels",
                "color_semantics": "color_semantics",
            },
        },
    )

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.require_precomputed_accuracy == pytest.approx(19 / 20)
    assert result.unsafe_count == 1


def test_agent_scorer_marks_missing_required_scientific_semantic_unsafe(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    _case(predictions, "S09-zh-volcano-results")["scientific_semantics"] = {
        "adjusted_p_value": "adjusted_p_value"
    }

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 1


def test_agent_scorer_marks_missing_case_required_optional_role_unsafe(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S05-precomputed-agreement")
    roles = selected["mapped_roles"]
    intent = selected["figure_intent"]
    assert isinstance(roles, dict) and isinstance(intent, dict)
    roles.pop("center")

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 1


def test_agent_scorer_counts_unnecessary_clarification_as_routing_error(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S01-raw-replicates-visible")
    selected.clear()
    selected.update(
        id="S01-raw-replicates-visible",
        action="clarify",
        question="Should raw observations be shown?",
        reason="Confirm the already explicit request.",
    )

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == pytest.approx(119 / 120)
    assert result.unsafe_count == 0


def test_agent_scorer_reports_missing_prediction(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    result = score_agent_predictions(
        CASES_PATH,
        _write_predictions(tmp_path, _predictions()[:-1]),
    )

    assert result.prediction_count == 119
    assert result.missing_count == 1
    assert result.action_accuracy == pytest.approx(119 / 120)


def test_agent_scorer_rejects_duplicate_prediction_id(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    predictions.append(deepcopy(predictions[0]))

    with pytest.raises(ValueError, match="duplicate prediction ID"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))


def test_agent_scorer_rejects_unknown_template(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S04-unrelated-quantities-scatter")
    selected["template"] = "scatter.unknown"
    intent = selected["figure_intent"]
    assert isinstance(intent, dict)
    intent["template"] = "scatter.unknown"

    with pytest.raises(ValueError, match="unknown template"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))


def test_agent_scorer_rejects_invalid_action(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    _case(predictions, "S04-unrelated-quantities-scatter")["action"] = "guess"

    with pytest.raises(ValueError, match="invalid action"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))
