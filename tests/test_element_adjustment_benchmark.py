from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests" / "evaluation" / "element_adjustment" / "cases.yaml"


def test_element_adjustment_corpus_is_balanced_and_has_thirty_two_cases() -> None:
    document = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    cases = document["cases"]
    assert len(cases) == 32
    assert len({case["id"] for case in cases}) == 32
    assert {group: sum(case["group"] == group for case in cases) for group in "ABCDE"} == {
        "A": 6,
        "B": 8,
        "C": 8,
        "D": 6,
        "E": 4,
    }
    assert {case["expected"]["topic"] for case in cases} == {
        "none",
        "axes",
        "marks",
        "ornaments",
        "annotations",
    }


def test_adjustment_decision_parser_rejects_unknown_and_low_quality_shapes() -> None:
    from tests.evaluation.element_adjustment.scoring import parse_adjustment_decision

    valid = {
        "element": "axis scale",
        "needs_nondefault": True,
        "topic": "axes",
        "recommended_surface": "semantic axis-scale request",
        "surface_status": "PLANNED",
        "implementation_level": "none",
        "default_retained_elsewhere": True,
        "low_level_parameters_proposed": [],
        "backend_names_exposed": [],
        "scientific_anchor_preserved": True,
        "reason": "The requested scale is semantic but no public field exists.",
    }
    assert parse_adjustment_decision(json.dumps(valid))["topic"] == "axes"
    with pytest.raises(ValueError, match="unknown"):
        parse_adjustment_decision(json.dumps({**valid, "surprise": 1}))
    with pytest.raises(ValueError, match="surface_status"):
        parse_adjustment_decision(json.dumps({**valid, "surface_status": "PUBLIC"}))


def test_perfect_predictions_score_every_metric_without_leakage(tmp_path: Path) -> None:
    from tests.evaluation.element_adjustment.scoring import score_adjustment_predictions

    cases = {
        "version": 1,
        "cases": [
            {
                "id": "A01",
                "group": "A",
                "request": "Draw a parity plot with defaults.",
                "available_data": {"columns": ["observed", "predicted"]},
                "expected": {
                    "element": "figure",
                    "needs_nondefault": False,
                    "topic": "none",
                    "recommended_surface": "deterministic defaults",
                    "surface_status": "DEFAULT",
                    "implementation_level": "none",
                    "default_retained_elsewhere": True,
                    "scientific_anchor_preserved": True,
                },
            },
            {
                "id": "B01",
                "group": "B",
                "request": "Use a log axis.",
                "available_data": {"columns": ["x", "y"]},
                "expected": {
                    "element": "axis scale",
                    "needs_nondefault": True,
                    "topic": "axes",
                    "recommended_surface": "semantic axis-scale request",
                    "surface_status": "PLANNED",
                    "implementation_level": "none",
                    "default_retained_elsewhere": True,
                    "scientific_anchor_preserved": True,
                },
            },
        ],
    }
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(yaml.safe_dump(cases, sort_keys=False), encoding="utf-8")
    predictions = tmp_path / "predictions.jsonl"
    records = []
    for case in cases["cases"]:
        records.append(
            {
                "id": case["id"],
                "condition": "treatment",
                "replicate": 1,
                **case["expected"],
                "low_level_parameters_proposed": [],
                "backend_names_exposed": [],
                "reason": "Observable decision.",
            }
        )
    predictions.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    disclosure = tmp_path / "disclosure.jsonl"
    disclosure.write_text(
        "".join(
            json.dumps(
                {
                    "id": record["id"],
                    "condition": "treatment",
                    "replicate": 1,
                    "files": [],
                    "read_count": 0,
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                }
            )
            + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    result = score_adjustment_predictions(cases_path, predictions, disclosure)

    assert result["decision_accuracy"] == 1.0
    assert result["fabricated_api_rate"] == 0.0
    assert result["low_level_parameter_leakage_rate"] == 0.0
    assert result["numeric_visual_invention_rate"] == 0.0
    assert result["backend_leakage_rate"] == 0.0
    assert result["median_reads"] == 0.0
    assert result["median_total_tokens"] == 120.0


def test_condition_workspace_is_fail_closed_and_treatment_only(tmp_path: Path) -> None:
    from tests.evaluation.element_adjustment.runner import prepare_condition_workspace

    destination = tmp_path / "workspace"
    copied = prepare_condition_workspace(ROOT, destination)
    relative = {path.relative_to(destination).as_posix() for path in copied}
    assert "SKILL.md" in relative
    assert "references/element-contracts/index.md" in relative
    assert not any(path.startswith("tests/") for path in relative)
    assert not any(path.startswith("reports/") for path in relative)
    assert ".git" not in relative


def test_token_parser_reads_actual_codex_usage_and_session_id() -> None:
    from tests.evaluation.element_adjustment.runner import parse_codex_metadata

    metadata = parse_codex_metadata(
        "OpenAI Codex\nsession id: 01a00000-0000-7000-8000-000000000001\ntokens used\n1,234\n"
    )
    assert metadata == {
        "session_id": "01a00000-0000-7000-8000-000000000001",
        "total_tokens": 1234,
    }


def test_scoring_rejects_duplicate_or_missing_condition_replicates(tmp_path: Path) -> None:
    from tests.evaluation.element_adjustment.scoring import score_adjustment_predictions

    case = {
        "id": "A01",
        "group": "A",
        "request": "Default plot.",
        "available_data": {},
        "expected": {
            "element": "figure",
            "needs_nondefault": False,
            "topic": "none",
            "recommended_surface": "deterministic defaults",
            "surface_status": "DEFAULT",
            "implementation_level": "none",
            "default_retained_elsewhere": True,
            "scientific_anchor_preserved": True,
        },
    }
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(yaml.safe_dump({"version": 1, "cases": [case]}), encoding="utf-8")
    decision = {
        "id": "A01",
        "condition": "baseline",
        "replicate": 1,
        **case["expected"],
        "low_level_parameters_proposed": [],
        "backend_names_exposed": [],
        "reason": "Defaults suffice.",
    }
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(json.dumps(decision) + "\n" + json.dumps(decision) + "\n")
    disclosure = tmp_path / "disclosure.jsonl"
    disclosure.write_text("")
    with pytest.raises(ValueError, match="duplicate"):
        score_adjustment_predictions(cases_path, predictions, disclosure)


def test_runner_uses_fresh_replicates_and_writes_observable_evidence(tmp_path: Path) -> None:
    from tests.evaluation.element_adjustment.runner import run_condition

    one_case = {
        "version": 1,
        "cases": [
            {
                "id": "A01",
                "group": "A",
                "request": "Use the registered parity plot without a visual exception.",
                "available_data": {"columns": ["observed", "predicted"]},
                "expected": {
                    "element": "figure",
                    "needs_nondefault": False,
                    "topic": "none",
                    "recommended_surface": "deterministic defaults",
                    "surface_status": "DEFAULT",
                    "implementation_level": "none",
                    "default_retained_elsewhere": True,
                    "scientific_anchor_preserved": True,
                },
            }
        ],
    }
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(yaml.safe_dump(one_case), encoding="utf-8")
    decision = {
        **one_case["cases"][0]["expected"],
        "low_level_parameters_proposed": [],
        "backend_names_exposed": [],
        "reason": "No exception is requested.",
    }
    command = [sys.executable, "-c", f"print({json.dumps(json.dumps(decision))})"]
    output = tmp_path / "predictions.jsonl"
    parsed, failed = run_condition(
        ROOT,
        cases_path,
        "treatment",
        2,
        command,
        output,
        tmp_path / "workspace",
        jobs=2,
    )
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert (parsed, failed) == (2, 0)
    assert {record["replicate"] for record in records} == {1, 2}
    assert all(record["condition"] == "treatment" for record in records)
    disclosures = [
        json.loads(line)
        for line in output.with_suffix(".disclosure.jsonl").read_text().splitlines()
    ]
    assert len(disclosures) == 2
    assert all(record["process_count"] == 1 for record in disclosures)
