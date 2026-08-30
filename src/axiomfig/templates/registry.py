"""Small YAML-backed registry for canonical AxiomFig templates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Any

import yaml
from matplotlib.figure import Figure


@dataclass(frozen=True)
class TemplateSpec:
    family: str
    variant: str
    geometry: str
    public: bool

    @property
    def template_id(self) -> str:
        return f"{self.family}/{self.variant}"


def _read_yaml(resource: object) -> dict[str, Any]:
    text = resource.read_text(encoding="utf-8")  # type: ignore[attr-defined]
    value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError("template YAML root must be a mapping")
    return value


def load_template_registry() -> tuple[TemplateSpec, ...]:
    document = _read_yaml(files("axiomfig.templates").joinpath("index.yaml"))
    if document.get("version") != 1:
        raise ValueError("unsupported template registry version")
    specs: list[TemplateSpec] = []
    for section, public in (("families", True), ("layouts", False)):
        groups = document.get(section)
        if not isinstance(groups, dict):
            raise ValueError(f"template registry {section!r} must be a mapping")
        for family, family_data in groups.items():
            if not isinstance(family, str) or not isinstance(family_data, dict):
                raise ValueError(f"invalid template family in {section!r}")
            variants = family_data.get("variants")
            if not isinstance(variants, dict) or not variants:
                raise ValueError(f"template family {family!r} has no variants")
            for variant, variant_data in variants.items():
                if not isinstance(variant, str) or not isinstance(variant_data, dict):
                    raise ValueError(f"invalid variant in template family {family!r}")
                geometry = variant_data.get("geometry")
                if not isinstance(geometry, str):
                    raise ValueError(f"template {family}/{variant} has no geometry")
                specs.append(TemplateSpec(family, variant, geometry, public))
    ids = [spec.template_id for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate template ID in registry")
    return tuple(specs)


def public_template_specs() -> tuple[TemplateSpec, ...]:
    return tuple(spec for spec in load_template_registry() if spec.public)


def load_family_contract(family: str) -> dict[str, Any]:
    resource = files("axiomfig.templates").joinpath(family, "contract.yaml")
    try:
        contract = _read_yaml(resource)
    except FileNotFoundError as exc:
        raise ValueError(f"missing contract for template family {family!r}") from exc
    if contract.get("family") != family:
        raise ValueError(f"contract family mismatch for {family!r}")
    variants = contract.get("variants")
    if not isinstance(variants, dict) or not variants:
        raise ValueError(f"contract for template family {family!r} has no variants")
    for variant, spec in variants.items():
        if not isinstance(spec, dict):
            raise ValueError(f"contract for {family}/{variant} must be a mapping")
        if family != "layouts" and spec.get("input_mode") not in {"direct", "precomputed"}:
            raise ValueError(f"contract for {family}/{variant} has invalid input_mode")
    return contract


def public_template_operability() -> Mapping[str, str]:
    """Return public input modes derived only from family contracts."""
    result: dict[str, str] = {}
    for spec in public_template_specs():
        contract = load_family_contract(spec.family)["variants"][spec.variant]
        result[spec.template_id] = str(contract["input_mode"])
    return MappingProxyType(result)


def validate_registry(
    builders: Mapping[str, Callable[..., Figure]],
) -> tuple[TemplateSpec, ...]:
    specs = load_template_registry()
    registered_ids = {spec.template_id for spec in specs}
    builder_ids = set(builders)
    if registered_ids != builder_ids:
        raise ValueError(
            "template registry/builder mismatch; "
            f"missing_builders={sorted(registered_ids - builder_ids)}, "
            f"undocumented_builders={sorted(builder_ids - registered_ids)}"
        )
    families = dict.fromkeys(spec.family for spec in specs)
    for family in families:
        contract = load_family_contract(family)
        contract_variants = set(contract["variants"])
        registry_variants = {spec.variant for spec in specs if spec.family == family}
        if contract_variants != registry_variants:
            raise ValueError(
                f"template registry/contract mismatch for {family!r}; "
                f"missing={sorted(registry_variants - contract_variants)}, "
                f"undocumented={sorted(contract_variants - registry_variants)}"
            )
    return specs
