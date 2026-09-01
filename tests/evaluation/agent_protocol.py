"""Structural validation for the Agent protocol benchmark specification."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from axiomfig.intent import FORBIDDEN_VISUAL_FIELDS
from axiomfig.structured_io import load_yaml
from axiomfig.templates.registry import (
    load_family_contract,
    load_template_registry,
    public_template_specs,
)

VALID_ACTIONS = frozenset({"render", "clarify", "require_precomputed", "unsupported"})
VALID_INPUT_MODES = frozenset({"direct", "precomputed"})


@dataclass(frozen=True)
class AgentProtocolBenchmarkResult:
    case_count: int
    render_count: int
    public_families: int
    actions: dict[str, int]
    languages: dict[str, int]
    intent_classes: frozenset[str]
    actual_llm_runs: int = 0


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


def _find_forbidden_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key in FORBIDDEN_VISUAL_FIELDS:
                found.add(key)
            found.update(_find_forbidden_keys(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            found.update(_find_forbidden_keys(nested))
    return found


def _normalize_template(value: object, case_id: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{case_id}: expected.template must be a string")
    return value.replace(".", "/")


def validate_agent_protocol_cases(path: Path) -> AgentProtocolBenchmarkResult:
    """Validate benchmark coverage without claiming an executed LLM evaluation."""

    document = _mapping(
        load_yaml(Path(path).read_text(encoding="utf-8"), source=str(path)),
        "benchmark",
    )
    if document.get("version") != 1:
        raise ValueError("unsupported Agent protocol benchmark version")
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("benchmark.cases must be a list")
    if not 110 <= len(raw_cases) <= 130:
        raise ValueError("Agent protocol benchmark must contain 110-130 cases")

    specs = {spec.template_id: spec for spec in load_template_registry()}
    public_ids = {spec.template_id for spec in public_template_specs()}
    public_families = {spec.family for spec in public_template_specs()}
    ids: set[str] = set()
    actions: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    classes: set[str] = set()
    rendered_templates: set[str] = set()

    for index, raw_case in enumerate(raw_cases):
        case = _mapping(raw_case, f"cases[{index}]")
        case_id = case.get("id")
        request = case.get("request")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"cases[{index}].id must be a non-empty string")
        if case_id in ids:
            raise ValueError(f"duplicate benchmark case ID: {case_id}")
        ids.add(case_id)
        if not isinstance(request, str) or not request.strip():
            raise ValueError(f"{case_id}: request must be non-empty")
        language = case.get("language", "en")
        if language not in {"en", "zh"}:
            raise ValueError(f"{case_id}: unsupported benchmark language {language!r}")
        languages[str(language)] += 1
        case_classes = set(_strings(case.get("classes"), f"{case_id}.classes"))
        if not case_classes:
            raise ValueError(f"{case_id}: classes must not be empty")
        classes.update(case_classes)

        expected = _mapping(case.get("expected"), f"{case_id}.expected")
        for field in ("required_semantics", "forbidden_inferences"):
            if field in expected:
                _strings(expected[field], f"{case_id}.expected.{field}")
        action = expected.get("action")
        if action not in VALID_ACTIONS:
            raise ValueError(f"{case_id}: invalid action {action!r}")
        actions[str(action)] += 1
        template_id = _normalize_template(expected.get("template"), case_id)
        if template_id is not None and template_id not in specs:
            raise ValueError(f"{case_id}: unknown template {template_id!r}")

        forbidden = _find_forbidden_keys(case)
        if forbidden:
            raise ValueError(f"{case_id}: forbidden visual fields {sorted(forbidden)}")

        if action in {"render", "require_precomputed"} and template_id is None:
            raise ValueError(f"{case_id}: {action} requires a template")
        if template_id in public_ids:
            family, variant = template_id.split("/", maxsplit=1)
            contract = load_family_contract(family)["variants"][variant]
            contract_mode = contract["input_mode"]
            expected_mode = expected.get("input_mode")
            if expected_mode not in VALID_INPUT_MODES:
                raise ValueError(f"{case_id}: public template requires expected.input_mode")
            if expected_mode != contract_mode:
                raise ValueError(
                    f"{case_id}: input_mode {expected_mode!r} does not match {contract_mode!r}"
                )
            required_roles = set(
                _strings(expected.get("required_roles"), f"{case_id}.expected.required_roles")
            )
            contract_required = set(contract["required"])
            contract_roles = contract_required | set(contract["optional"])
            if not contract_required <= required_roles:
                raise ValueError(f"{case_id}: required roles omit contract roles for {template_id}")
            unknown_roles = required_roles - contract_roles
            if unknown_roles:
                raise ValueError(
                    f"{case_id}: required roles are not declared by {template_id}: "
                    f"{sorted(unknown_roles)}"
                )
            if action == "require_precomputed" and contract_mode != "precomputed":
                raise ValueError(f"{case_id}: require_precomputed targets a direct-data template")

        if action == "render":
            if template_id not in public_ids:
                raise ValueError(f"{case_id}: render must target a public template")
            rendered_templates.add(template_id)
            available = _mapping(case.get("available_data"), f"{case_id}.available_data")
            supplied = available.get("columns", available.get("keys"))
            supplied_roles = set(_strings(supplied, f"{case_id}.available_data fields"))
            required_roles = set(expected["required_roles"])
            if not required_roles <= supplied_roles:
                raise ValueError(f"{case_id}: render fixture omits required roles")
        elif action == "clarify" and not expected.get("clarification_reason"):
            raise ValueError(f"{case_id}: clarify requires clarification_reason")
        elif action in {"require_precomputed", "unsupported"} and not expected.get("reason"):
            raise ValueError(f"{case_id}: {action} requires reason")

    if rendered_templates != public_ids:
        raise ValueError(
            "render cases must cover every public template; "
            f"missing={sorted(public_ids - rendered_templates)}, "
            f"extra={sorted(rendered_templates - public_ids)}"
        )
    rendered_families = {
        template_id.split("/", maxsplit=1)[0] for template_id in rendered_templates
    }
    if rendered_families != public_families:
        raise ValueError("render cases do not cover every public family")

    return AgentProtocolBenchmarkResult(
        case_count=len(raw_cases),
        render_count=actions["render"],
        public_families=len(rendered_families),
        actions=dict(sorted(actions.items())),
        languages=dict(sorted(languages.items())),
        intent_classes=frozenset(classes),
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    result = validate_agent_protocol_cases(root / "tests/evaluation/agent_protocol_cases.yaml")
    print(
        "PASS Agent protocol benchmark: "
        f"{result.case_count} cases, {result.render_count} public-template render specifications, "
        "0 LLM runs claimed"
    )
