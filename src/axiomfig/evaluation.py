"""Deterministic v1 evaluation for routing, real data, rendering, and validation."""

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
from axiomfig.intent import build_intent_figure, parse_figure_intent
from axiomfig.rendering import render_figure
from axiomfig.templates import build_template
from axiomfig.templates.registry import load_template_registry, public_template_specs
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

REPEATABILITY_TEMPLATES = (
    "scatter/parity",
    "heatmap/correlation",
    "association/mantel",
    "ordination/pca_biplot",
    "flow/sankey",
    "omics/volcano",
    "survival/kaplan_meier",
)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    scientific_intent: str
    expected_template: str
    fixture_id: str
    expected_validation: str
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
    routing_passed: int
    routing_rate: float
    canonical_rendered: int
    canonical_passed: int
    canonical_render_rate: float
    external_rendered: int
    external_passed: int
    external_render_rate: float
    runtime_validated: int
    runtime_validation_passed: int
    runtime_validation_rate: float
    repeatability_cases: int
    repeatability_passed: int
    repeatable: bool
    gallery_templates_expected: int
    gallery_templates_present: int
    gallery_coverage_rate: float
    artifact_pairs: int
    artifact_pairs_passed: int
    artifact_rate: float
    failures: tuple[str, ...]
    discovery: DiscoveryMetrics


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _first_existing(candidates: tuple[Path, ...], label: str) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"AxiomFig {label} was not found: {candidates}")


def _evaluation_path(filename: str) -> Path:
    return _first_existing(
        (
            _repo_root() / "evaluation" / filename,
            Path(sysconfig.get_path("data")) / "share" / "axiomfig" / "evaluation" / filename,
        ),
        filename,
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
    document = _yaml_mapping(_evaluation_path("cases.yaml"))
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("evaluation cases must be a list")
    cases = []
    for raw in raw_cases:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("figure_intent"), Mapping):
            raise ValueError("each evaluation case must contain a Figure Intent mapping")
        expected_validation = str(raw.get("expected_validation", ""))
        if expected_validation not in {"pass", "error"}:
            raise ValueError("expected_validation must be pass or error")
        cases.append(
            EvaluationCase(
                case_id=str(raw["id"]),
                scientific_intent=str(raw["scientific_intent"]),
                expected_template=str(raw["expected_template"]).replace(".", "/"),
                fixture_id=str(raw["fixture"]),
                expected_validation=expected_validation,
                figure_intent=MappingProxyType(dict(raw["figure_intent"])),
            )
        )
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("evaluation case IDs must be unique")
    return tuple(cases)


def load_evaluation_fixtures() -> Mapping[str, Mapping[str, Any]]:
    document = _yaml_mapping(_evaluation_path("fixtures.yaml"))
    raw_fixtures = document.get("fixtures")
    if not isinstance(raw_fixtures, Mapping):
        raise ValueError("evaluation fixtures must be a mapping")
    fixtures: dict[str, Mapping[str, Any]] = {}
    for name, fixture in raw_fixtures.items():
        if not isinstance(fixture, Mapping):
            raise ValueError(f"evaluation fixture {name!r} must be a mapping")
        fixtures[str(name)] = MappingProxyType(dict(fixture))
    return MappingProxyType(fixtures)


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
    representative = next(case for case in cases if case.expected_template == "scatter/parity")
    intent_text = yaml.safe_dump(dict(representative.figure_intent), sort_keys=False)
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


def _figure_signature(case: EvaluationCase, fixture: Mapping[str, Any]) -> str:
    intent = parse_figure_intent(case.figure_intent)
    params = build_rcparams(
        load_contracts(),
        geometry=intent.geometry,
        typography=intent.typography,
    )
    with mpl.rc_context(rc=params):
        figure = build_intent_figure(intent, fixture)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        figure.canvas.draw()
        digest = hashlib.sha256(figure.canvas.buffer_rgba()).hexdigest()
        plt.close(figure)
    return digest


def _gallery_coverage(gallery_root: Path) -> tuple[int, int]:
    specs = public_template_specs()
    present = 0
    for spec in specs:
        paths = tuple(
            gallery_root / mode / f"{spec.template_id}.{suffix}"
            for mode in ("sans", "serif")
            for suffix in ("pdf", "png")
        )
        if all(path.is_file() and path.stat().st_size > 0 for path in paths):
            present += 1
    return len(specs), present


def run_evaluation(
    *,
    render: bool = True,
    artifacts_dir: Path | None = None,
    gallery_root: Path | None = None,
) -> EvaluationResult:
    cases = load_evaluation_cases()
    fixtures = load_evaluation_fixtures()
    routes = knowledge_routes()
    specs = {spec.template_id: spec for spec in load_template_registry() if spec.public}
    failures: list[str] = []

    routing_passed = 0
    for case in cases:
        try:
            intent = parse_figure_intent(case.figure_intent)
        except ValueError as exc:
            failures.append(f"routing:{case.case_id}:{exc}")
            continue
        if (
            intent.template_id == case.expected_template
            and case.expected_template in specs
            and case.expected_template in routes.get(case.scientific_intent, ())
            and case.fixture_id in fixtures
        ):
            routing_passed += 1
        else:
            failures.append(f"routing:{case.case_id}:contract mismatch")

    canonical_rendered = 0
    canonical_passed = 0
    external_rendered = 0
    external_passed = 0
    runtime_validated = 0
    runtime_validation_passed = 0
    artifact_pairs = 0
    artifact_pairs_passed = 0
    repeatability_passed = 0

    if render:
        discover_fonts("sans")
        contracts = load_contracts()
        for case in cases:
            spec = specs[case.expected_template]
            canonical_rendered += 1
            canonical_figure = None
            try:
                canonical_params = build_rcparams(
                    contracts,
                    geometry=spec.geometry,
                    typography="sans",
                )
                with mpl.rc_context(rc=canonical_params):
                    canonical_figure = build_template(case.expected_template)
                    canonical_figure.set_size_inches(
                        canonical_params["figure.figsize"], forward=False
                    )
                    canonical_figure.canvas.draw()
                canonical_passed += 1
            except Exception as exc:  # noqa: BLE001 - evaluation records failures
                failures.append(f"canonical:{case.case_id}:{exc}")
            finally:
                if canonical_figure is not None:
                    plt.close(canonical_figure)

            external_rendered += 1
            runtime_validated += 1
            if artifacts_dir is not None:
                artifact_pairs += 1
            external_figure = None
            try:
                intent = parse_figure_intent(case.figure_intent)
                external_params = build_rcparams(
                    contracts,
                    geometry=intent.geometry,
                    typography=intent.typography,
                )
                with mpl.rc_context(rc=external_params):
                    external_figure = build_intent_figure(intent, fixtures[case.fixture_id])
                    external_figure.set_size_inches(
                        external_params["figure.figsize"], forward=False
                    )
                    external_figure.canvas.draw()
                    external_passed += 1
                    validate_figure_anatomy(external_figure)
                    runtime_validation_passed += 1
                    if artifacts_dir is not None:
                        result = render_figure(
                            external_figure,
                            Path(artifacts_dir) / case.expected_template,
                            work_root=Path(artifacts_dir) / "_work" / spec.family,
                            typography=intent.typography,
                            geometry=intent.geometry,
                        )
                        validate_pair(result.pdf, result.png, tectonic_log=result.log)
                        artifact_pairs_passed += 1
            except Exception as exc:  # noqa: BLE001 - evaluation records failures
                failures.append(f"external:{case.case_id}:{exc}")
            finally:
                if external_figure is not None:
                    plt.close(external_figure)

        by_template = {case.expected_template: case for case in cases}
        for template_id in REPEATABILITY_TEMPLATES:
            case = by_template[template_id]
            fixture = fixtures[case.fixture_id]
            try:
                if _figure_signature(case, fixture) == _figure_signature(case, fixture):
                    repeatability_passed += 1
                else:
                    failures.append(f"repeatability:{case.case_id}:signature mismatch")
            except Exception as exc:  # noqa: BLE001 - evaluation records failures
                failures.append(f"repeatability:{case.case_id}:{exc}")

    expected_gallery, present_gallery = _gallery_coverage(
        Path(gallery_root) if gallery_root is not None else _repo_root() / "gallery"
    )
    case_count = len(cases)
    return EvaluationResult(
        case_count=case_count,
        routing_passed=routing_passed,
        routing_rate=routing_passed / case_count if case_count else 0.0,
        canonical_rendered=canonical_rendered,
        canonical_passed=canonical_passed,
        canonical_render_rate=(
            canonical_passed / canonical_rendered if canonical_rendered else 0.0
        ),
        external_rendered=external_rendered,
        external_passed=external_passed,
        external_render_rate=(external_passed / external_rendered if external_rendered else 0.0),
        runtime_validated=runtime_validated,
        runtime_validation_passed=runtime_validation_passed,
        runtime_validation_rate=(
            runtime_validation_passed / runtime_validated if runtime_validated else 0.0
        ),
        repeatability_cases=len(REPEATABILITY_TEMPLATES) if render else 0,
        repeatability_passed=repeatability_passed,
        repeatable=(repeatability_passed == len(REPEATABILITY_TEMPLATES) if render else False),
        gallery_templates_expected=expected_gallery,
        gallery_templates_present=present_gallery,
        gallery_coverage_rate=(present_gallery / expected_gallery if expected_gallery else 0.0),
        artifact_pairs=artifact_pairs,
        artifact_pairs_passed=artifact_pairs_passed,
        artifact_rate=artifact_pairs_passed / artifact_pairs if artifact_pairs else 0.0,
        failures=tuple(failures),
        discovery=_discovery_metrics(cases),
    )
