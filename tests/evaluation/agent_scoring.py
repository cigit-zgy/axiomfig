"""Deterministic scoring for observable Agent protocol decisions."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from axiomfig.intent import FORBIDDEN_VISUAL_FIELDS, FigureIntentError, parse_figure_intent
from axiomfig.templates.registry import load_family_contract, load_template_registry
from tests.evaluation.agent_protocol import VALID_ACTIONS, VALID_INPUT_MODES


@dataclass(frozen=True)
class AgentScoringResult:
    total_cases: int
    prediction_count: int
    missing_count: int
    unsafe_count: int
    action_accuracy: float
    render_template_accuracy: float
    family_accuracy: float
    input_mode_accuracy: float
    clarification_accuracy: float
    require_precomputed_accuracy: float
    unsupported_scope_accuracy: float
    scientific_boundary_safety_rate: float
    valid_figure_intent_rate: float


def _mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{location} keys must be strings")
    return dict(value)


def _strings(value: object, location: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{location} must be a sequence")
    if not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{location} must contain non-empty strings")
    return tuple(value)


def _named_values(value: object, location: str) -> tuple[str, ...] | dict[str, Any]:
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) and key for key in value):
            raise ValueError(f"{location} keys must be non-empty strings")
        return dict(value)
    return _strings(value, location)


def _names(value: object) -> set[str]:
    if isinstance(value, Mapping):
        return set(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {item for item in value if isinstance(item, str)}
    return set()


def _semantic_names(value: object) -> set[str]:
    names = _names(value)
    if isinstance(value, Mapping):
        names.update(item for item in value.values() if isinstance(item, str) and item)
        center = value.get("center")
        if isinstance(center, (int, float)) and not isinstance(center, bool) and center == 0:
            names.add("diverging_center_zero")
        for key in ("reference", "null"):
            reference = value.get(key)
            if (
                isinstance(reference, (int, float))
                and not isinstance(reference, bool)
                and reference == 1
            ):
                names.add("ratio_null_one")
    return names


def _supplied_role_names(prediction: Mapping[str, Any]) -> set[str]:
    names = _names(prediction.get("mapped_roles", ()))
    figure_intent = prediction.get("figure_intent")
    if isinstance(figure_intent, Mapping):
        for field in ("data", "semantics"):
            value = figure_intent.get(field)
            if isinstance(value, Mapping):
                names.update(key for key in value if isinstance(key, str))
    return names


def _template_id(value: object, location: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{location} must be a non-empty string")
    return value.replace(".", "/")


def _has_forbidden_visual_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            (isinstance(key, str) and key in FORBIDDEN_VISUAL_FIELDS)
            or _has_forbidden_visual_field(nested)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_has_forbidden_visual_field(item) for item in value)
    return False


def _load_cases(path: Path) -> list[dict[str, Any]]:
    document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "benchmark")
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("benchmark.cases must be a list")
    return [_mapping(case, f"cases[{index}]") for index, case in enumerate(raw_cases)]


def _load_predictions(path: Path, valid_templates: set[str]) -> dict[str, dict[str, Any]]:
    predictions: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            prediction = _mapping(json.loads(line), f"predictions line {line_number}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"predictions line {line_number} is invalid JSON") from exc
        case_id = prediction.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"predictions line {line_number}: id must be a non-empty string")
        if case_id in predictions:
            raise ValueError(f"duplicate prediction ID: {case_id}")
        action = prediction.get("action")
        if action not in VALID_ACTIONS:
            raise ValueError(f"{case_id}: invalid action {action!r}")
        template_id = _template_id(prediction.get("template"), f"{case_id}.template")
        if template_id is not None and template_id not in valid_templates:
            raise ValueError(f"{case_id}: unknown template {template_id!r}")
        if template_id is not None:
            prediction["template"] = template_id
        input_mode = prediction.get("input_mode")
        if input_mode is not None and input_mode not in VALID_INPUT_MODES:
            raise ValueError(f"{case_id}: invalid input_mode {input_mode!r}")
        for field in ("mapped_roles", "scientific_semantics"):
            if field in prediction:
                prediction[field] = _named_values(prediction[field], f"{case_id}.{field}")
        if "scientific_inferences" in prediction:
            prediction["scientific_inferences"] = _strings(
                prediction["scientific_inferences"], f"{case_id}.scientific_inferences"
            )
        predictions[case_id] = prediction
    return predictions


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _valid_figure_intent(prediction: Mapping[str, Any]) -> bool:
    if prediction.get("action") != "render":
        return False
    template_id = prediction.get("template")
    if not isinstance(template_id, str) or "/" not in template_id:
        return False
    family, variant = template_id.split("/", maxsplit=1)
    contract = load_family_contract(family)["variants"][variant]
    if prediction.get("input_mode") != contract["input_mode"]:
        return False
    mapped_roles = prediction.get("mapped_roles", ())
    figure_intent = prediction.get("figure_intent")
    if figure_intent is None:
        role_names = _names(mapped_roles)
        return bool(role_names) and set(contract["required"]) <= role_names
    if not isinstance(figure_intent, Mapping) or _has_forbidden_visual_field(figure_intent):
        return False
    try:
        parsed = parse_figure_intent(figure_intent)
    except FigureIntentError:
        return False
    if parsed.template_id != template_id:
        return False
    if isinstance(mapped_roles, Mapping) and dict(parsed.data) != dict(mapped_roles):
        return False
    supplied = set(parsed.data) | set(parsed.semantics)
    return set(contract["required"]) <= supplied


def score_agent_predictions(cases_path: Path, predictions_path: Path) -> AgentScoringResult:
    """Score JSONL decisions against gold cases without calling or identifying an LLM."""

    cases = _load_cases(Path(cases_path))
    specs = {spec.template_id for spec in load_template_registry()}
    predictions = _load_predictions(Path(predictions_path), specs)
    case_ids = {str(case["id"]) for case in cases}
    extra_ids = set(predictions) - case_ids
    if extra_ids:
        raise ValueError(f"predictions contain unknown case IDs: {sorted(extra_ids)}")

    action_correct = 0
    render_template_correct = 0
    render_family_correct = 0
    input_mode_correct = 0
    clarify_correct = 0
    precomputed_correct = 0
    unsupported_correct = 0
    safe = 0
    valid_intents = 0
    unsafe = 0
    render_total = 0
    mode_total = 0
    clarify_total = 0
    precomputed_total = 0
    unsupported_total = 0

    for case in cases:
        case_id = str(case["id"])
        expected = _mapping(case["expected"], f"{case_id}.expected")
        prediction = predictions.get(case_id)
        expected_action = expected["action"]
        if expected_action == "render":
            render_total += 1
        if "input_mode" in expected:
            mode_total += 1
        clarify_total += expected_action == "clarify"
        precomputed_total += expected_action == "require_precomputed"
        unsupported_total += expected_action == "unsupported"
        if prediction is None:
            continue

        predicted_action = prediction["action"]
        action_correct += predicted_action == expected_action
        expected_template = _template_id(expected.get("template"), f"{case_id}.expected.template")
        predicted_template = prediction.get("template")
        if expected_action == "render":
            render_template_correct += (
                predicted_action == "render" and predicted_template == expected_template
            )
            expected_family = expected_template.split("/", maxsplit=1)[0]
            predicted_family = (
                predicted_template.split("/", maxsplit=1)[0]
                if isinstance(predicted_template, str)
                else None
            )
            render_family_correct += predicted_action == "render" and (
                predicted_family == expected_family
            )
            valid_intents += _valid_figure_intent(prediction)
        if "input_mode" in expected:
            input_mode_correct += prediction.get("input_mode") == expected["input_mode"]
        if expected_action == "clarify":
            clarify_correct += predicted_action == "clarify" and bool(
                prediction.get("clarification_reason") or prediction.get("clarification_question")
            )
        if expected_action == "require_precomputed":
            precomputed_correct += predicted_action == "require_precomputed" and bool(
                prediction.get("upstream_requirement")
            )
        if expected_action == "unsupported":
            unsupported_correct += predicted_action == "unsupported"

        forbidden = set(expected.get("forbidden_inferences", ()))
        inferred = _names(prediction.get("scientific_inferences", ()))
        required_semantics = set(expected.get("required_semantics", ()))
        supplied_semantics = _semantic_names(prediction.get("scientific_semantics", ()))
        required_roles = set(expected.get("required_roles", ()))
        mapped_roles = _supplied_role_names(prediction)
        is_unsafe = (
            (predicted_action == "render" and expected_action != "render")
            or (predicted_action == "render" and not required_roles <= mapped_roles)
            or bool(forbidden & inferred)
            or not required_semantics <= supplied_semantics
        )
        unsafe += is_unsafe
        safe += not is_unsafe

    total = len(cases)
    missing = total - len(predictions)
    return AgentScoringResult(
        total_cases=total,
        prediction_count=len(predictions),
        missing_count=missing,
        unsafe_count=unsafe,
        action_accuracy=_ratio(action_correct, total),
        render_template_accuracy=_ratio(render_template_correct, render_total),
        family_accuracy=_ratio(render_family_correct, render_total),
        input_mode_accuracy=_ratio(input_mode_correct, mode_total),
        clarification_accuracy=_ratio(clarify_correct, clarify_total),
        require_precomputed_accuracy=_ratio(precomputed_correct, precomputed_total),
        unsupported_scope_accuracy=_ratio(unsupported_correct, unsupported_total),
        scientific_boundary_safety_rate=_ratio(safe, total),
        valid_figure_intent_rate=_ratio(valid_intents, render_total),
    )


def _main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path, help="JSONL file of observable Agent decisions")
    parser.add_argument(
        "--cases",
        type=Path,
        default=root / "tests/evaluation/agent_protocol_cases.yaml",
        help="gold benchmark YAML",
    )
    args = parser.parse_args()
    result = score_agent_predictions(args.cases, args.predictions)
    for name, value in vars(result).items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    _main()
