from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


def _render_decision(template: str = "scatter.parity") -> dict[str, object]:
    return {
        "action": "render",
        "template": template,
        "input_mode": "direct",
        "mapped_roles": {"observed": "measured", "predicted": "predicted"},
        "scientific_semantics": {},
        "scientific_inferences": [],
        "figure_intent": {
            "template": template,
            "data": {"observed": "measured", "predicted": "predicted"},
        },
    }


def test_render_decision_remains_strict_and_executable() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    parsed = parse_agent_decision(json.dumps(_render_decision()))

    assert parsed["template"] == "scatter/parity"
    assert parsed["mapped_roles"] == {"observed": "measured", "predicted": "predicted"}


@pytest.mark.parametrize("missing", ["template", "figure_intent"])
def test_render_decision_rejects_missing_executable_fields(missing: str) -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision.pop(missing)

    with pytest.raises(ValueError, match=missing):
        parse_agent_decision(json.dumps(decision))


def test_render_decision_rejects_invalid_figure_intent_semantics() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["scientific_semantics"] = {"color_scale": "sequential"}
    intent = decision["figure_intent"]
    assert isinstance(intent, dict)
    intent["semantics"] = {"color_scale": "sequential"}

    with pytest.raises(ValueError, match="invalid Figure Intent"):
        parse_agent_decision(json.dumps(decision))


def test_clarify_decision_requires_only_question_and_scientific_reason() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    parsed = parse_agent_decision(
        json.dumps(
            {
                "action": "clarify",
                "question": "Does error represent SD, SE, a confidence interval, or another type?",
                "reason": "The uncertainty definition changes the scientific interpretation.",
            }
        )
    )

    assert parsed == {
        "action": "clarify",
        "question": "Does error represent SD, SE, a confidence interval, or another type?",
        "reason": "The uncertainty definition changes the scientific interpretation.",
    }


def test_clarify_decision_rejects_missing_question() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="question"):
        parse_agent_decision(json.dumps({"action": "clarify", "reason": "Meaning is missing."}))


def test_clarify_decision_rejects_irrelevant_render_fields() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="unknown"):
        parse_agent_decision(
            json.dumps(
                {
                    "action": "clarify",
                    "question": "What does error mean?",
                    "reason": "Uncertainty is ambiguous.",
                    "mapped_roles": {},
                }
            )
        )


@pytest.mark.parametrize(
    ("candidate", "missing_result"),
    [
        ("ordination.pca_scores", "PCA scores and explained variance"),
        ("association.mantel", "Mantel r and p-value links"),
        ("survival.kaplan_meier", "a visualization-ready survival curve"),
        ("diagnostics.roc", "FPR and TPR curve points"),
        ("heatmap.clustered", "row and column cluster ordering"),
        ("omics.volcano", "differential-analysis effect sizes and adjusted p-values"),
        ("omics.enrichment_dot", "pathway-enrichment results"),
    ],
)
def test_require_precomputed_accepts_known_candidate_without_render_fields(
    candidate: str,
    missing_result: str,
) -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    parsed = parse_agent_decision(
        json.dumps(
            {
                "action": "require_precomputed",
                "candidate_template": candidate,
                "missing_result": missing_result,
                "reason": "The supplied raw data do not contain this upstream scientific result.",
            }
        )
    )

    assert parsed["candidate_template"] == candidate.replace(".", "/")
    assert parsed["missing_result"] == missing_result


def test_require_precomputed_allows_unresolved_target_when_scientifically_legitimate() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    parsed = parse_agent_decision(
        json.dumps(
            {
                "action": "require_precomputed",
                "missing_result": "a study-design-supported causal analysis",
                "reason": "No registered plot can infer causality from the observational table.",
            }
        )
    )

    assert "candidate_template" not in parsed


def test_require_precomputed_rejects_direct_candidate_template() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="precomputed"):
        parse_agent_decision(
            json.dumps(
                {
                    "action": "require_precomputed",
                    "candidate_template": "scatter.simple",
                    "missing_result": "a fitted model",
                    "reason": "A fit is not present.",
                }
            )
        )


def test_require_precomputed_rejects_render_mapping_fields() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="unknown"):
        parse_agent_decision(
            json.dumps(
                {
                    "action": "require_precomputed",
                    "missing_result": "PCA scores",
                    "reason": "Only raw features are supplied.",
                    "mapped_roles": {"features": ["x1", "x2"]},
                }
            )
        )


@pytest.mark.parametrize(
    "reason",
    [
        "Paired/repeated-measures specialty grammar is not registered.",
        "Causal DAG visualization is outside the registered grammar.",
        "Microscopy segmentation is image analysis, not an AxiomFig plotting grammar.",
    ],
)
def test_unsupported_decision_is_minimal_and_strict(reason: str) -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    parsed = parse_agent_decision(json.dumps({"action": "unsupported", "reason": reason}))

    assert parsed == {"action": "unsupported", "reason": reason}


def test_unsupported_decision_rejects_missing_reason() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="reason"):
        parse_agent_decision(json.dumps({"action": "unsupported"}))


def _score_one(
    tmp_path: Path,
    *,
    required_semantic: str,
    supplied_semantic: str,
) -> object:
    from tests.evaluation.agent_scoring import score_agent_predictions

    cases = tmp_path / "cases.yaml"
    cases.write_text(
        f"""version: 1
cases:
  - id: semantic-case
    request: Render the supplied uncertainty.
    available_data: {{format: csv, columns: [x, estimate, error, uncertainty_type]}}
    expected:
      action: render
      template: line.errorbar
      input_mode: precomputed
      required_roles: [x, estimate, error, uncertainty_type]
      required_semantics: [{required_semantic}]
""",
        encoding="utf-8",
    )
    decision = {
        "id": "semantic-case",
        "action": "render",
        "template": "line.errorbar",
        "input_mode": "precomputed",
        "mapped_roles": {
            "x": "x",
            "estimate": "estimate",
            "error": "error",
            "uncertainty_type": "uncertainty_type",
        },
        "scientific_semantics": {"uncertainty_type": supplied_semantic},
        "scientific_inferences": [],
        "figure_intent": {
            "template": "line.errorbar",
            "data": {
                "x": "x",
                "estimate": "estimate",
                "error": "error",
                "uncertainty_type": "uncertainty_type",
            },
        },
    }
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
    return score_agent_predictions(cases, predictions)


@pytest.mark.parametrize("semantic", ["SE", "standard error"])
def test_scorer_accepts_exact_standard_error_aliases(tmp_path: Path, semantic: str) -> None:
    result = _score_one(
        tmp_path,
        required_semantic="SE",
        supplied_semantic=semantic,
    )

    assert result.scientific_boundary_safety_rate == 1.0


def test_scorer_does_not_conflate_sd_with_se(tmp_path: Path) -> None:
    result = _score_one(
        tmp_path,
        required_semantic="SE",
        supplied_semantic="SD",
    )

    assert result.scientific_boundary_safety_rate == 0.0


@pytest.mark.parametrize(
    "semantic",
    ["prediction_interval", "prediction interval", "95 percent prediction interval"],
)
def test_scorer_accepts_exact_prediction_interval_aliases(
    tmp_path: Path,
    semantic: str,
) -> None:
    result = _score_one(
        tmp_path,
        required_semantic="prediction_interval",
        supplied_semantic=semantic,
    )

    assert result.scientific_boundary_safety_rate == 1.0


def test_scorer_does_not_conflate_confidence_and_prediction_intervals(tmp_path: Path) -> None:
    result = _score_one(
        tmp_path,
        required_semantic="prediction_interval",
        supplied_semantic="confidence interval",
    )

    assert result.scientific_boundary_safety_rate == 0.0


def test_scorer_accepts_minimal_non_render_variants(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    cases = tmp_path / "cases.yaml"
    cases.write_text(
        """version: 1
cases:
  - id: clarify-case
    request: What does error mean?
    available_data: {format: csv, columns: [error]}
    expected: {action: clarify, clarification_reason: uncertainty type is unknown}
  - id: precomputed-case
    request: Compute PCA.
    available_data: {format: csv, columns: [x1, x2]}
    expected: {action: require_precomputed, reason: PCA results are missing}
  - id: unsupported-case
    request: Draw a causal DAG.
    available_data: {format: csv, columns: [x, y]}
    expected: {action: unsupported, reason: causal DAG grammar is unavailable}
""",
        encoding="utf-8",
    )
    predictions = tmp_path / "predictions.jsonl"
    records = [
        {
            "id": "clarify-case",
            "action": "clarify",
            "question": "Does error denote SD, SE, CI, or another uncertainty type?",
            "reason": "The uncertainty type is scientifically material.",
        },
        {
            "id": "precomputed-case",
            "action": "require_precomputed",
            "candidate_template": "ordination.pca_scores",
            "missing_result": "PCA scores and explained variance",
            "reason": "Only raw features are supplied.",
        },
        {
            "id": "unsupported-case",
            "action": "unsupported",
            "reason": "Causal DAG grammar is not registered.",
        },
    ]
    predictions.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    result = score_agent_predictions(cases, predictions)

    assert result.action_accuracy == 1.0
    assert result.clarification_accuracy == 1.0
    assert result.require_precomputed_accuracy == 1.0
    assert result.unsupported_scope_accuracy == 1.0


def test_scorer_reads_zero_center_from_valid_figure_intent(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    cases = tmp_path / "cases.yaml"
    cases.write_text(
        """version: 1
cases:
  - id: center-case
    request: Plot a signed correlation matrix centered at zero.
    available_data: {format: json, keys: [matrix, labels, center]}
    expected:
      action: render
      template: heatmap.correlation
      input_mode: precomputed
      required_roles: [matrix, labels, center]
      required_semantics: [diverging_center_zero]
""",
        encoding="utf-8",
    )
    prediction = {
        "id": "center-case",
        "action": "render",
        "template": "heatmap.correlation",
        "input_mode": "precomputed",
        "mapped_roles": {"matrix": "matrix", "labels": "labels", "center": "center"},
        "scientific_semantics": {"neutral_center": 0},
        "scientific_inferences": [],
        "figure_intent": {
            "template": "heatmap.correlation",
            "data": {"matrix": "matrix", "labels": "labels", "center": "center"},
            "semantics": {"center": 0},
        },
    }
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(json.dumps(prediction) + "\n", encoding="utf-8")

    result = score_agent_predictions(cases, predictions)

    assert result.scientific_boundary_safety_rate == 1.0


def test_scorer_recognizes_explicit_numeric_null_reference(tmp_path: Path) -> None:
    from tests.evaluation.agent_scoring import score_agent_predictions

    cases = tmp_path / "cases.yaml"
    cases.write_text(
        """version: 1
cases:
  - id: ratio-case
    request: Plot risk ratios with null one.
    available_data: {format: csv, columns: [label, estimate, interval, uncertainty_type, reference]}
    expected:
      action: render
      template: estimation.forest
      input_mode: precomputed
      required_roles: [label, estimate, interval, uncertainty_type, reference]
      required_semantics: [ratio_null_one]
""",
        encoding="utf-8",
    )
    prediction = {
        "id": "ratio-case",
        "action": "render",
        "template": "estimation.forest",
        "input_mode": "precomputed",
        "mapped_roles": {
            "label": "label",
            "estimate": "estimate",
            "interval": "interval",
            "uncertainty_type": "uncertainty_type",
            "reference": "reference",
        },
        "scientific_semantics": {"null_reference": 1},
        "scientific_inferences": [],
        "figure_intent": {
            "template": "estimation.forest",
            "data": {
                "label": "label",
                "estimate": "estimate",
                "interval": "interval",
                "uncertainty_type": "uncertainty_type",
                "reference": "reference",
            },
        },
    }
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(json.dumps(prediction) + "\n", encoding="utf-8")

    result = score_agent_predictions(cases, predictions)

    assert result.scientific_boundary_safety_rate == 1.0


def test_independent_nonrender_corpus_has_frozen_action_and_language_mix() -> None:
    root = Path(__file__).resolve().parents[1]
    document = yaml.safe_load(
        (root / "tests/evaluation/nonrender_decision_cases.yaml").read_text(encoding="utf-8")
    )
    cases = document["cases"]
    actions: dict[str, int] = {}
    languages: dict[str, int] = {}
    for case in cases:
        action = case["expected"]["action"]
        language = case.get("language", "en")
        actions[action] = actions.get(action, 0) + 1
        languages[language] = languages.get(language, 0) + 1

    assert len(cases) == 30
    assert actions == {
        "render": 6,
        "clarify": 8,
        "require_precomputed": 10,
        "unsupported": 6,
    }
    assert languages == {"en": 24, "zh": 6}


def test_line_multi_contract_excludes_long_subject_paired_mapping() -> None:
    from axiomfig.templates.registry import load_family_contract

    semantics = load_family_contract("line")["variants"]["multi"]["role_semantics"]

    assert semantics["series_values"] == "series_by_shared_x_matrix"
    assert semantics["series_labels"] == "one_label_per_series_row"
