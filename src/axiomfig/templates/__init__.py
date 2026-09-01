from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from matplotlib.figure import Figure

from axiomfig.layout import apply_single_panel_layout, get_figure_layout, solve_panel_layout
from axiomfig.ornaments import finalize_ornaments
from axiomfig.templates.association import (
    BUILDERS as ASSOCIATION_BUILDERS,
)
from axiomfig.templates.association import (
    GALLERY_CASES as ASSOCIATION_GALLERY_CASES,
)
from axiomfig.templates.association.adapter import adapt as adapt_association
from axiomfig.templates.bar import BUILDERS as BAR_BUILDERS
from axiomfig.templates.bar import GALLERY_CASES as BAR_GALLERY_CASES
from axiomfig.templates.bar.adapter import adapt as adapt_bar
from axiomfig.templates.diagnostics import BUILDERS as DIAGNOSTICS_BUILDERS
from axiomfig.templates.diagnostics.adapter import adapt as adapt_diagnostics
from axiomfig.templates.distribution import BUILDERS as DISTRIBUTION_BUILDERS
from axiomfig.templates.distribution.adapter import adapt as adapt_distribution
from axiomfig.templates.estimation import BUILDERS as ESTIMATION_BUILDERS
from axiomfig.templates.estimation.adapter import adapt as adapt_estimation
from axiomfig.templates.field import BUILDERS as FIELD_BUILDERS
from axiomfig.templates.field.adapter import adapt as adapt_field
from axiomfig.templates.flow import BUILDERS as FLOW_BUILDERS
from axiomfig.templates.flow.adapter import adapt as adapt_flow
from axiomfig.templates.heatmap import BUILDERS as HEATMAP_BUILDERS
from axiomfig.templates.heatmap.adapter import adapt as adapt_heatmap
from axiomfig.templates.layouts import BUILDERS as LAYOUT_BUILDERS
from axiomfig.templates.line import BUILDERS as LINE_BUILDERS
from axiomfig.templates.line.adapter import adapt as adapt_line
from axiomfig.templates.omics import BUILDERS as OMICS_BUILDERS
from axiomfig.templates.omics.adapter import adapt as adapt_omics
from axiomfig.templates.ordination import BUILDERS as ORDINATION_BUILDERS
from axiomfig.templates.ordination.adapter import adapt as adapt_ordination
from axiomfig.templates.registry import public_template_specs, validate_registry
from axiomfig.templates.scatter import BUILDERS as SCATTER_BUILDERS
from axiomfig.templates.scatter.adapter import adapt as adapt_scatter
from axiomfig.templates.survival import BUILDERS as SURVIVAL_BUILDERS
from axiomfig.templates.survival.adapter import adapt as adapt_survival


def _qualified(family: str, builders: Mapping[str, Any]) -> dict[str, Callable[..., Figure]]:
    return {f"{family}/{variant}": builder for variant, builder in builders.items()}


TEMPLATE_BUILDERS: dict[str, Callable[..., Figure]] = {
    **_qualified("line", LINE_BUILDERS),
    **_qualified("scatter", SCATTER_BUILDERS),
    **_qualified("bar", BAR_BUILDERS),
    **_qualified("distribution", DISTRIBUTION_BUILDERS),
    **_qualified("heatmap", HEATMAP_BUILDERS),
    **_qualified("estimation", ESTIMATION_BUILDERS),
    **_qualified("diagnostics", DIAGNOSTICS_BUILDERS),
    **_qualified("ordination", ORDINATION_BUILDERS),
    **_qualified("association", ASSOCIATION_BUILDERS),
    **_qualified("flow", FLOW_BUILDERS),
    **_qualified("field", FIELD_BUILDERS),
    **_qualified("omics", OMICS_BUILDERS),
    **_qualified("survival", SURVIVAL_BUILDERS),
    **_qualified("layouts", LAYOUT_BUILDERS),
}

validate_registry(TEMPLATE_BUILDERS)

_FAMILY_ADAPTERS = MappingProxyType(
    {
        "line": adapt_line,
        "scatter": adapt_scatter,
        "bar": adapt_bar,
        "distribution": adapt_distribution,
        "heatmap": adapt_heatmap,
        "estimation": adapt_estimation,
        "diagnostics": adapt_diagnostics,
        "ordination": adapt_ordination,
        "association": adapt_association,
        "flow": adapt_flow,
        "field": adapt_field,
        "omics": adapt_omics,
        "survival": adapt_survival,
    }
)
TEMPLATE_ADAPTERS = MappingProxyType(
    {spec.template_id: _FAMILY_ADAPTERS[spec.family] for spec in public_template_specs()}
)
TEMPLATE_GALLERY_CASES = MappingProxyType({**ASSOCIATION_GALLERY_CASES, **BAR_GALLERY_CASES})


def adapt_template_data(template_id: str, values: dict[str, Any]) -> dict[str, object]:
    """Validate roles and normalize data for one public template."""
    try:
        adapter = TEMPLATE_ADAPTERS[template_id]
    except KeyError as exc:
        raise ValueError(f"no external-data adapter for template {template_id!r}") from exc
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
    adapted = adapter(variant, dict(values))
    if set(adapted) != provided:
        raise RuntimeError(f"adapter for {template_id} changed supplied field ownership")
    return adapted


def get_template_builder(name: str) -> Callable[..., Figure]:
    try:
        return TEMPLATE_BUILDERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise KeyError(f"unknown template {name!r}; available: {available}") from exc


def _apply_family_layout(figure: Figure) -> None:
    if get_figure_layout(figure) is None:
        apply_single_panel_layout(figure)
        return
    solve_panel_layout(figure)
    finalize_ornaments(figure)


def build_template(name: str, **kwargs: Any) -> Figure:
    figure = get_template_builder(name)(**kwargs)
    _apply_family_layout(figure)
    return figure


__all__ = [
    "TEMPLATE_ADAPTERS",
    "TEMPLATE_BUILDERS",
    "TEMPLATE_GALLERY_CASES",
    "adapt_template_data",
    "build_template",
    "get_template_builder",
]
