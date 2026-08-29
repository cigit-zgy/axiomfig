"""Explicit external-data adapters for the frozen public template surface."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

from axiomfig.templates.registry import public_template_specs

from . import (
    association,
    bar,
    diagnostics,
    distribution,
    estimation,
    field,
    flow,
    heatmap,
    line,
    omics,
    ordination,
    scatter,
    survival,
)

_PRECOMPUTED = frozenset(
    {
        "line/confidence_band",
        "line/errorbar",
        "scatter/regression",
        "distribution/density",
        "heatmap/correlation",
        "heatmap/clustered",
        "heatmap/confusion_matrix",
        "estimation/forest",
        "estimation/point_interval",
        "estimation/coefficient",
        "diagnostics/residual",
        "diagnostics/bland_altman",
        "diagnostics/calibration",
        "diagnostics/roc",
        "diagnostics/precision_recall",
        "diagnostics/learning_curve",
        "diagnostics/qq",
        "diagnostics/feature_importance",
        "ordination/pca_scores",
        "ordination/pca_biplot",
        "ordination/pcoa",
        "ordination/nmds",
        "association/mantel",
        "association/correlation_network",
        "omics/volcano",
        "omics/enrichment_dot",
        "survival/kaplan_meier",
    }
)

DATA_ADAPTERS = frozenset(spec.template_id for spec in public_template_specs())
OPERABILITY = MappingProxyType(
    {
        template_id: "precomputed" if template_id in _PRECOMPUTED else "direct"
        for template_id in sorted(DATA_ADAPTERS)
    }
)

_FAMILY_ADAPTERS = MappingProxyType(
    {
        "line": line.adapt,
        "scatter": scatter.adapt,
        "bar": bar.adapt,
        "distribution": distribution.adapt,
        "heatmap": heatmap.adapt,
        "estimation": estimation.adapt,
        "diagnostics": diagnostics.adapt,
        "ordination": ordination.adapt,
        "association": association.adapt,
        "flow": flow.adapt,
        "field": field.adapt,
        "omics": omics.adapt,
        "survival": survival.adapt,
    }
)


def adapt_template_data(template_id: str, values: dict[str, Any]) -> dict[str, object]:
    if template_id not in DATA_ADAPTERS:
        raise ValueError(f"no external-data adapter for template {template_id!r}")
    from axiomfig.templates.registry import load_family_contract

    family, variant = template_id.split("/", maxsplit=1)
    contract = load_family_contract(family)["variants"][variant]
    required = set(contract["required"])
    permitted = required | set(contract.get("optional", ()))
    provided = set(values)
    missing = required - provided
    if missing:
        raise ValueError(f"missing required fields for {template_id}: {sorted(missing)}")
    unknown = provided - permitted
    if unknown:
        raise ValueError(f"{template_id} does not accept: {sorted(unknown)}")
    adapted = _FAMILY_ADAPTERS[family](variant, dict(values))
    if set(adapted) != provided:
        raise RuntimeError(f"adapter for {template_id} changed supplied field ownership")
    return adapted


__all__ = ["DATA_ADAPTERS", "OPERABILITY", "adapt_template_data"]
