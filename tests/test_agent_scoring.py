from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests/evaluation/agent_protocol_cases.yaml"


def _predictions() -> list[dict[str, object]]:
    document = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    predictions: list[dict[str, object]] = []
    for case in document["cases"]:
        expected = case["expected"]
        prediction: dict[str, object] = {
            "id": case["id"],
            "action": expected["action"],
            "scientific_inferences": [],
        }
        for field in ("template", "input_mode"):
            if field in expected:
                prediction[field] = expected[field]
        if "required_roles" in expected:
            prediction["mapped_roles"] = expected["required_roles"]
        if "required_semantics" in expected:
            prediction["scientific_semantics"] = expected["required_semantics"]
        if expected["action"] == "clarify":
            prediction["clarification_reason"] = expected["clarification_reason"]
        if expected["action"] == "require_precomputed":
            prediction["upstream_requirement"] = expected.get(
                "upstream_requirement", expected["reason"]
            )
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
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == 1.0
    assert result.render_template_accuracy == pytest.approx(69 / 70)
    assert result.family_accuracy == 1.0
    assert result.valid_figure_intent_rate == pytest.approx(69 / 70)


def test_agent_scorer_marks_unsafe_render_instead_of_clarification(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "C13-zh-uncertainty-unknown")
    selected.update(
        action="render",
        mapped_roles=["x", "estimate", "error", "uncertainty_type"],
        scientific_inferences=["uncertainty_type"],
    )
    selected.pop("clarification_reason")
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == pytest.approx(119 / 120)
    assert result.clarification_accuracy == pytest.approx(19 / 20)
    assert result.unsafe_count == 1
    assert result.scientific_boundary_safety_rate == pytest.approx(119 / 120)


def test_agent_scorer_marks_unsafe_render_instead_of_upstream_analysis(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "P08-zh-mantel-raw")
    selected.update(action="render", scientific_inferences=["mantel_statistics"])
    selected.pop("upstream_requirement")
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.require_precomputed_accuracy == pytest.approx(19 / 20)
    assert result.unsafe_count == 1
    assert result.scientific_boundary_safety_rate == pytest.approx(119 / 120)


def test_agent_scorer_marks_missing_required_scientific_semantic_unsafe(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    _case(predictions, "S09-zh-volcano-results")["scientific_semantics"] = ["adjusted_p_value"]
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 1
    assert result.scientific_boundary_safety_rate == pytest.approx(119 / 120)


def test_agent_scorer_marks_missing_case_required_optional_role_unsafe(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S05-precomputed-agreement")
    mapped_roles = selected["mapped_roles"]
    assert isinstance(mapped_roles, list)
    selected["mapped_roles"] = [role for role in mapped_roles if role != "center"]
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 1
    assert result.scientific_boundary_safety_rate == pytest.approx(119 / 120)


def test_agent_scorer_accepts_observable_role_and_semantic_mappings(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S09-zh-volcano-results")
    roles = selected["mapped_roles"]
    semantics = selected["scientific_semantics"]
    assert isinstance(roles, list)
    assert isinstance(semantics, list)
    selected["mapped_roles"] = {role: f"source_{role}" for role in roles}
    selected["scientific_semantics"] = {semantic: True for semantic in semantics}

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 0
    assert result.valid_figure_intent_rate == 1.0


def test_agent_scorer_accepts_required_role_supplied_as_figure_intent_semantic(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S07-signed-correlation-center")
    roles = selected["mapped_roles"]
    assert isinstance(roles, list)
    selected["mapped_roles"] = {role: role for role in roles if role != "center"}
    selected["figure_intent"] = {
        "template": "heatmap.correlation",
        "data": {"matrix": "matrix", "labels": "labels"},
        "semantics": {"center": 0},
    }

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 0
    assert result.valid_figure_intent_rate == 1.0


def test_agent_scorer_reads_scientific_semantic_names_from_mapping_values(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S09-zh-volcano-results")
    selected["scientific_semantics"] = {
        "effect_size": "log2_fold_change",
        "adjusted_p_value": "adjusted_p_value",
    }

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 0
    assert result.scientific_boundary_safety_rate == 1.0


def test_agent_scorer_derives_zero_center_semantic_from_valid_figure_intent(
    tmp_path: Path,
) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S07-signed-correlation-center")
    selected["mapped_roles"] = {"matrix": "matrix", "labels": "labels"}
    selected["scientific_semantics"] = {"quantity": "signed correlation", "center": 0}
    selected["figure_intent"] = {
        "template": "heatmap.correlation",
        "data": {"matrix": "matrix", "labels": "labels"},
        "semantics": {"center": 0},
    }

    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.unsafe_count == 0
    assert result.scientific_boundary_safety_rate == 1.0


def test_agent_scorer_counts_unnecessary_clarification_as_routing_error(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    selected = _case(predictions, "S01-raw-replicates-visible")
    selected.update(
        action="clarify",
        clarification_reason="Ask whether raw observations should be shown.",
    )
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.action_accuracy == pytest.approx(119 / 120)
    assert result.unsafe_count == 0
    assert result.scientific_boundary_safety_rate == 1.0


def test_agent_scorer_reports_missing_prediction(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()[:-1]
    result = score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))

    assert result.prediction_count == 119
    assert result.missing_count == 1
    assert result.action_accuracy == pytest.approx(119 / 120)
    assert result.scientific_boundary_safety_rate == pytest.approx(119 / 120)


def test_agent_scorer_rejects_duplicate_prediction_id(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    predictions.append(deepcopy(predictions[0]))

    with pytest.raises(ValueError, match="duplicate prediction ID"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))


def test_agent_scorer_rejects_unknown_template(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    _case(predictions, "S04-unrelated-quantities-scatter")["template"] = "scatter.unknown"

    with pytest.raises(ValueError, match="unknown template"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))


def test_agent_scorer_rejects_invalid_action(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    predictions = _predictions()
    _case(predictions, "S04-unrelated-quantities-scatter")["action"] = "guess"

    with pytest.raises(ValueError, match="invalid action"):
        score_agent_predictions(CASES_PATH, _write_predictions(tmp_path, predictions))
