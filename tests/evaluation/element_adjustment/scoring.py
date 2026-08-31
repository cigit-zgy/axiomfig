"""Validate and score observable element-adjustment decisions."""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

TOPICS = frozenset({"none", "axes", "marks", "ornaments", "annotations"})
STATUSES = frozenset({"DEFAULT", "AVAILABLE", "INTERNAL_ONLY", "PLANNED", "NOT_SUPPORTED"})
LEVELS = frozenset({"none", "public", "runtime"})
DECISION_FIELDS = frozenset(
    {
        "element",
        "needs_nondefault",
        "topic",
        "recommended_surface",
        "surface_status",
        "implementation_level",
        "default_retained_elsewhere",
        "low_level_parameters_proposed",
        "backend_names_exposed",
        "scientific_anchor_preserved",
        "reason",
    }
)
GOLD_FIELDS = tuple(
    field
    for field in DECISION_FIELDS
    if field not in {"low_level_parameters_proposed", "backend_names_exposed", "reason"}
)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a non-empty string")
    return value.strip()


def _string_list(value: object, location: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{location} must be an array")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{location} must contain non-empty strings")
    return [item.strip() for item in value]


def parse_adjustment_decision(payload: str) -> dict[str, Any]:
    """Parse one final Agent decision without accepting extra fields."""

    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent response must be one JSON object") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Agent response must be one JSON object")
    unknown = set(raw) - DECISION_FIELDS
    missing = DECISION_FIELDS - set(raw)
    if unknown or missing:
        raise ValueError(
            f"decision fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    decision = dict(raw)
    decision["element"] = _text(decision["element"], "element")
    decision["recommended_surface"] = _text(decision["recommended_surface"], "recommended_surface")
    decision["reason"] = _text(decision["reason"], "reason")
    for field in ("needs_nondefault", "default_retained_elsewhere", "scientific_anchor_preserved"):
        if not isinstance(decision[field], bool):
            raise ValueError(f"{field} must be boolean")
    if decision["topic"] not in TOPICS:
        raise ValueError(f"invalid topic {decision['topic']!r}")
    if decision["surface_status"] not in STATUSES:
        raise ValueError(f"invalid surface_status {decision['surface_status']!r}")
    if decision["implementation_level"] not in LEVELS:
        raise ValueError(f"invalid implementation_level {decision['implementation_level']!r}")
    decision["low_level_parameters_proposed"] = _string_list(
        decision["low_level_parameters_proposed"], "low_level_parameters_proposed"
    )
    decision["backend_names_exposed"] = _string_list(
        decision["backend_names_exposed"], "backend_names_exposed"
    )
    return decision


def _records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{number}") from exc
        if not isinstance(record, Mapping):
            raise ValueError(f"record at {path}:{number} must be an object")
        records.append(dict(record))
    return records


def _quantile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction + 0.5)))
    return float(ordered[index])


def _summary(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "p90": None, "max": None}
    return {
        "mean": float(statistics.fmean(values)),
        "median": float(statistics.median(values)),
        "p90": _quantile(values, 0.9),
        "max": float(max(values)),
    }


def score_adjustment_predictions(
    cases_path: Path, predictions_path: Path, disclosure_path: Path
) -> dict[str, Any]:
    """Score decisions and disclosure cost without collapsing metrics into one number."""

    document = yaml.safe_load(Path(cases_path).read_text(encoding="utf-8"))
    cases = document.get("cases") if isinstance(document, Mapping) else None
    if not isinstance(cases, list):
        raise ValueError("cases document must contain a list")
    indexed = {str(case["id"]): case for case in cases}
    if len(indexed) != len(cases):
        raise ValueError("duplicate case ID in gold")

    predictions = _records(predictions_path)
    seen: set[tuple[str, str, int]] = set()
    parsed: list[tuple[dict[str, Any], Mapping[str, Any]]] = []
    for record in predictions:
        case_id = _text(record.get("id"), "id")
        condition = _text(record.get("condition"), "condition")
        replicate = record.get("replicate")
        if not isinstance(replicate, int) or replicate < 1:
            raise ValueError("replicate must be a positive integer")
        key = (case_id, condition, replicate)
        if key in seen:
            raise ValueError(f"duplicate prediction {key}")
        seen.add(key)
        if case_id not in indexed:
            raise ValueError(f"unknown case ID {case_id!r}")
        decision = parse_adjustment_decision(
            json.dumps({key: value for key, value in record.items() if key in DECISION_FIELDS})
        )
        parsed.append((decision, indexed[case_id]))

    total = len(parsed)
    exact = 0
    fabricated = low_level = numeric = backend = unnecessary = 0
    per_group: dict[str, Counter[str]] = {}
    for decision, case in parsed:
        expected = case["expected"]
        correct = all(decision[field] == expected[field] for field in GOLD_FIELDS)
        exact += int(correct)
        group = str(case["group"])
        counts = per_group.setdefault(group, Counter())
        counts["total"] += 1
        counts["correct"] += int(correct)
        is_fabricated = decision["surface_status"] == "AVAILABLE" and (
            expected["surface_status"] != "AVAILABLE"
            or decision["recommended_surface"] != expected["recommended_surface"]
        )
        fabricated += int(is_fabricated)
        has_low = bool(decision["low_level_parameters_proposed"])
        low_level += int(has_low)
        numeric += int(
            any(re.search(r"\d", item) for item in decision["low_level_parameters_proposed"])
        )
        backend += int(bool(decision["backend_names_exposed"]))
        unnecessary += int(
            group == "A"
            and (
                decision["needs_nondefault"]
                or decision["surface_status"] != "DEFAULT"
                or bool(decision["low_level_parameters_proposed"])
            )
        )

    disclosures = _records(disclosure_path)
    disclosure_index = {
        (str(record["id"]), str(record["condition"]), int(record["replicate"])): record
        for record in disclosures
    }
    if len(disclosure_index) != len(disclosures):
        raise ValueError("duplicate disclosure record")
    reads = [
        float(record["read_count"])
        for record in disclosures
        if record.get("read_count") is not None
    ]
    total_tokens = [
        float(record["total_tokens"])
        for record in disclosures
        if isinstance(record.get("total_tokens"), (int, float))
    ]
    read_stats = _summary(reads)
    token_stats = _summary(total_tokens)
    input_tokens = [
        float(record["input_tokens"])
        for record in disclosures
        if isinstance(record.get("input_tokens"), (int, float))
    ]
    output_tokens = [
        float(record["output_tokens"])
        for record in disclosures
        if isinstance(record.get("output_tokens"), (int, float))
    ]
    default_disclosures = [
        record for record in disclosures if indexed[str(record["id"])]["group"] == "A"
    ]
    exception_disclosures = [
        record for record in disclosures if indexed[str(record["id"])]["group"] != "A"
    ]

    def topic_paths(record: Mapping[str, Any]) -> set[str]:
        files = record.get("files", [])
        if not isinstance(files, list):
            return set()
        return {
            path
            for path in files
            if isinstance(path, str) and path.startswith("references/element-contracts/")
        }

    default_element_reads = sum(bool(topic_paths(record)) for record in default_disclosures)
    exception_multi_topic = sum(
        len({path for path in topic_paths(record) if not path.endswith("/index.md")}) > 1
        for record in exception_disclosures
    )
    reference_fanout = [
        len({path for path in record.get("files", []) if str(path).startswith("references/")})
        for record in disclosures
    ]
    denominator = total or 1
    group_metrics = {
        group: {
            "cases": counts["total"],
            "decision_accuracy": counts["correct"] / counts["total"],
        }
        for group, counts in sorted(per_group.items())
    }
    distinct_low_level = [
        len(decision["low_level_parameters_proposed"]) for decision, _case in parsed
    ]
    return {
        "predictions": total,
        "decision_accuracy": exact / denominator,
        "fabricated_api_rate": fabricated / denominator,
        "low_level_parameter_leakage_rate": low_level / denominator,
        "numeric_visual_invention_rate": numeric / denominator,
        "backend_leakage_rate": backend / denominator,
        "unnecessary_default_override_rate": unnecessary / denominator,
        "mean_distinct_low_level_choices": (
            statistics.fmean(distinct_low_level) if distinct_low_level else 0.0
        ),
        "mean_reads": read_stats["mean"],
        "median_reads": read_stats["median"],
        "p90_reads": read_stats["p90"],
        "max_reads": read_stats["max"],
        "mean_reference_topic_fanout": (
            statistics.fmean(reference_fanout) if reference_fanout else None
        ),
        "default_element_doc_read_rate": (
            default_element_reads / len(default_disclosures) if default_disclosures else None
        ),
        "exception_multi_element_topic_rate": (
            exception_multi_topic / len(exception_disclosures) if exception_disclosures else None
        ),
        "input_tokens": _summary(input_tokens),
        "output_tokens": _summary(output_tokens),
        "mean_total_tokens": token_stats["mean"],
        "median_total_tokens": token_stats["median"],
        "p90_total_tokens": token_stats["p90"],
        "max_total_tokens": token_stats["max"],
        "default_total_tokens": _summary(
            [
                float(record["total_tokens"])
                for record in default_disclosures
                if isinstance(record.get("total_tokens"), (int, float))
            ]
        ),
        "exception_total_tokens": _summary(
            [
                float(record["total_tokens"])
                for record in exception_disclosures
                if isinstance(record.get("total_tokens"), (int, float))
            ]
        ),
        "by_group": group_metrics,
    }
