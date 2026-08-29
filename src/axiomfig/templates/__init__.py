from __future__ import annotations

from collections.abc import Callable, Mapping

from matplotlib.figure import Figure

from axiomfig.layout import get_figure_layout, solve_panel_layout
from axiomfig.ornaments import finalize_ornaments
from axiomfig.template_helpers import apply_single_panel_layout
from axiomfig.templates.association import BUILDERS as ASSOCIATION_BUILDERS
from axiomfig.templates.bar import BUILDERS as BAR_BUILDERS
from axiomfig.templates.diagnostics import BUILDERS as DIAGNOSTICS_BUILDERS
from axiomfig.templates.distribution import BUILDERS as DISTRIBUTION_BUILDERS
from axiomfig.templates.estimation import BUILDERS as ESTIMATION_BUILDERS
from axiomfig.templates.field import BUILDERS as FIELD_BUILDERS
from axiomfig.templates.heatmap import BUILDERS as HEATMAP_BUILDERS
from axiomfig.templates.layouts import BUILDERS as LAYOUT_BUILDERS
from axiomfig.templates.line import BUILDERS as LINE_BUILDERS
from axiomfig.templates.registry import validate_registry
from axiomfig.templates.scatter import BUILDERS as SCATTER_BUILDERS


def _qualified(
    family: str, builders: Mapping[str, Callable[..., Figure]]
) -> dict[str, Callable[..., Figure]]:
    return {f"{family}/{variant}": builder for variant, builder in builders.items()}


TEMPLATE_BUILDERS: dict[str, Callable[..., Figure]] = {
    **_qualified("line", LINE_BUILDERS),
    **_qualified("scatter", SCATTER_BUILDERS),
    **_qualified("bar", BAR_BUILDERS),
    **_qualified("distribution", DISTRIBUTION_BUILDERS),
    **_qualified("heatmap", HEATMAP_BUILDERS),
    **_qualified("estimation", ESTIMATION_BUILDERS),
    **_qualified("diagnostics", DIAGNOSTICS_BUILDERS),
    **_qualified("association", ASSOCIATION_BUILDERS),
    **_qualified("field", FIELD_BUILDERS),
    **_qualified("layouts", LAYOUT_BUILDERS),
}

validate_registry(TEMPLATE_BUILDERS)


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


def build_template(name: str, **kwargs: object) -> Figure:
    figure = get_template_builder(name)(**kwargs)
    _apply_family_layout(figure)
    return figure


__all__ = ["TEMPLATE_BUILDERS", "build_template", "get_template_builder"]
