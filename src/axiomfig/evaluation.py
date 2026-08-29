"""Deterministic v1 system evaluation for registry, routing, intent, and rendering."""

from __future__ import annotations

import hashlib
import math
import sysconfig
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml

from axiomfig.anatomy import validate_figure_anatomy
from axiomfig.config import build_rcparams, load_contracts
from axiomfig.intent import parse_figure_intent
from axiomfig.layout import get_figure_layout
from axiomfig.templates import build_template
from axiomfig.templates.registry import load_template_registry
from axiomfig.typography import discover_fonts


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    scientific_intent: str
    request: str
    expected_template: str
    figure_intent: Mapping[str, Any]


@dataclass(frozen=True)
class DiscoveryMetrics:
    skill_bytes: int
    registry_bytes: int
    selected_contract_bytes: int
    representative_intent_bytes: int
    approximate_tokens: int


@dataclass(frozen=True)
class EvaluationResult:
    case_count: int
    passed: int
    pass_rate: float
    rendered_templates: int
    render_success_rate: float
    repeatable: bool
    mixed_layout_passed: bool
    discovery: DiscoveryMetrics


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _first_existing(candidates: tuple[Path, ...], label: str) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"AxiomFig {label} was not found: {candidates}")


def _evaluation_path() -> Path:
    return _first_existing(
        (
            _repo_root() / "evaluation/cases.yaml",
            Path(sysconfig.get_path("data")) / "share/axiomfig/evaluation/cases.yaml",
        ),
        "evaluation corpus",
    )


def _knowledge_path() -> Path:
    return _first_existing(
        (
            _repo_root() / "references/template-knowledge/index.yaml",
            Path(sysconfig.get_path("data")) / "share/axiomfig/template-knowledge/index.yaml",
        ),
        "template knowledge index",
    )


def _yaml_mapping(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    if document.get("version") != 1:
        raise ValueError(f"{path} must declare version: 1")
    return document


def load_evaluation_cases() -> tuple[EvaluationCase, ...]:
    document = _yaml_mapping(_evaluation_path())
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("evaluation cases must be a list")
    cases = []
    for raw in raw_cases:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("figure_intent"), Mapping):
            raise ValueError("each evaluation case must contain a Figure Intent mapping")
        cases.append(
            EvaluationCase(
                case_id=str(raw["id"]),
                scientific_intent=str(raw["scientific_intent"]),
                request=str(raw["request"]),
                expected_template=str(raw["expected_template"]).replace(".", "/"),
                figure_intent=MappingProxyType(dict(raw["figure_intent"])),
            )
        )
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("evaluation case IDs must be unique")
    return tuple(cases)


def knowledge_routes() -> Mapping[str, tuple[str, ...]]:
    document = _yaml_mapping(_knowledge_path())
    intents = document.get("intents")
    if not isinstance(intents, Mapping):
        raise ValueError("template knowledge intents must be a mapping")
    routes = {}
    for name, route in intents.items():
        if not isinstance(route, Mapping) or not isinstance(route.get("templates"), list):
            raise ValueError(f"invalid template knowledge route: {name!r}")
        routes[str(name)] = tuple(str(value).replace(".", "/") for value in route["templates"])
    return MappingProxyType(routes)


def _bytes(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def _discovery_metrics(cases: tuple[EvaluationCase, ...]) -> DiscoveryMetrics:
    root = _repo_root()
    registry_resource = files("axiomfig.templates").joinpath("index.yaml")
    contract_resource = files("axiomfig.templates").joinpath("scatter", "contract.yaml")
    registry_text = registry_resource.read_text(encoding="utf-8")
    contract_text = contract_resource.read_text(encoding="utf-8")
    intent_text = yaml.safe_dump(dict(cases[4].figure_intent), sort_keys=False)
    skill_bytes = _bytes(root / "SKILL.md")
    registry_bytes = len(registry_text.encode("utf-8"))
    contract_bytes = len(contract_text.encode("utf-8"))
    intent_bytes = len(intent_text.encode("utf-8"))
    total_bytes = skill_bytes + registry_bytes + contract_bytes + intent_bytes
    return DiscoveryMetrics(
        skill_bytes=skill_bytes,
        registry_bytes=registry_bytes,
        selected_contract_bytes=contract_bytes,
        representative_intent_bytes=intent_bytes,
        approximate_tokens=math.ceil(total_bytes / 4.0),
    )


def _render_signature(template_id: str, geometry: str) -> str:
    params = build_rcparams(load_contracts(), geometry=geometry, typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template(template_id)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        figure.canvas.draw()
        digest = hashlib.sha256(figure.canvas.buffer_rgba()).hexdigest()
        plt.close(figure)
    return digest


def run_evaluation(*, render: bool = True) -> EvaluationResult:
    cases = load_evaluation_cases()
    routes = knowledge_routes()
    specs = {spec.template_id: spec for spec in load_template_registry()}
    passed = 0
    for case in cases:
        try:
            intent = parse_figure_intent(case.figure_intent)
        except ValueError:
            continue
        if (
            intent.template_id == case.expected_template
            and case.expected_template in specs
            and case.expected_template in routes.get(case.scientific_intent, ())
        ):
            passed += 1

    rendered = 0
    render_passed = 0
    mixed_layout_passed = False
    repeatable = False
    if render:
        discover_fonts("sans")
        template_ids = tuple(dict.fromkeys(case.expected_template for case in cases))
        rendered = len(template_ids)
        for template_id in template_ids:
            spec = specs[template_id]
            params = build_rcparams(load_contracts(), geometry=spec.geometry, typography="sans")
            try:
                with mpl.rc_context(rc=params):
                    figure = build_template(template_id)
                    figure.set_size_inches(params["figure.figsize"], forward=False)
                    figure.canvas.draw()
                    validate_figure_anatomy(figure)
                    if template_id == "layouts/grid_2x2":
                        layout = get_figure_layout(figure)
                        mixed_layout_passed = bool(
                            layout is not None
                            and len(layout.panels) == 4
                            and all(panel.primary_axes is not None for panel in layout.panels)
                        )
                    plt.close(figure)
                render_passed += 1
            except Exception:
                plt.close("all")
        parity_geometry = specs["scatter/parity"].geometry
        repeatable = _render_signature("scatter/parity", parity_geometry) == _render_signature(
            "scatter/parity", parity_geometry
        )

    return EvaluationResult(
        case_count=len(cases),
        passed=passed,
        pass_rate=passed / len(cases) if cases else 0.0,
        rendered_templates=rendered,
        render_success_rate=render_passed / rendered if rendered else 0.0,
        repeatable=repeatable,
        mixed_layout_passed=mixed_layout_passed,
        discovery=_discovery_metrics(cases),
    )
