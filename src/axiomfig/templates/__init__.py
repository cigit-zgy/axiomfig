from __future__ import annotations

from collections.abc import Callable

from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.template_helpers import apply_single_panel_layout
from axiomfig.templates.curves import (
    build_errorbar,
    build_grouped_scatter,
    build_line_ci,
    build_line_marker,
    build_model_evaluation,
    build_multi_line,
    build_parity,
    build_regression_scatter,
    build_scatter,
    build_single_line,
)
from axiomfig.templates.distributions import (
    build_box_violin,
    build_boxplot,
    build_grouped_bar,
    build_histogram,
    build_horizontal_bar,
    build_stacked_bar,
    build_vertical_bar,
    build_violin,
)
from axiomfig.templates.panels import build_multi_panel
from axiomfig.templates.surfaces import build_heatmap

TEMPLATE_BUILDERS: dict[str, Callable[..., Figure]] = {
    "single-line": build_single_line,
    "multi-line": build_multi_line,
    "line-marker": build_line_marker,
    "line-ci": build_line_ci,
    "scatter": build_scatter,
    "grouped-scatter": build_grouped_scatter,
    "parity": build_parity,
    "regression-scatter": build_regression_scatter,
    "vertical-bar": build_vertical_bar,
    "grouped-bar": build_grouped_bar,
    "horizontal-bar": build_horizontal_bar,
    "stacked-bar": build_stacked_bar,
    "boxplot": build_boxplot,
    "violin": build_violin,
    "box-violin": build_box_violin,
    "histogram": build_histogram,
    "heatmap": build_heatmap,
    "errorbar": build_errorbar,
    "model-evaluation": build_model_evaluation,
    "multi-panel": build_multi_panel,
}


def get_template_builder(name: str) -> Callable[..., Figure]:
    try:
        return TEMPLATE_BUILDERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise KeyError(f"unknown template {name!r}; available: {available}") from exc


def _apply_family_layout(figure: Figure, name: str) -> None:
    if name != "multi-panel":
        apply_single_panel_layout(figure)
        return
    layout = load_contracts().style["layout"]["multi_panel"]
    figure.subplots_adjust(
        **{key: float(value) for key, value in layout["margins"].items()},
        wspace=float(layout["wspace"]),
        hspace=float(layout["hspace"]),
    )


def build_template(name: str, **kwargs: object) -> Figure:
    figure = get_template_builder(name)(**kwargs)
    _apply_family_layout(figure, name)
    return figure
