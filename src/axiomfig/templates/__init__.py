from __future__ import annotations

from collections.abc import Callable

from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.template_helpers import apply_single_panel_layout, refresh_panel_labels
from axiomfig.templates.curves import (
    build_bland_altman,
    build_calibration_curve,
    build_errorbar,
    build_forest_plot,
    build_grouped_scatter,
    build_line_ci,
    build_line_marker,
    build_model_evaluation,
    build_multi_line,
    build_parity,
    build_point_interval,
    build_pr_curve,
    build_regression_scatter,
    build_residual_diagnostics,
    build_roc_curve,
    build_scatter,
    build_single_line,
)
from axiomfig.templates.distributions import (
    build_box_violin,
    build_boxplot,
    build_density,
    build_ecdf,
    build_grouped_bar,
    build_histogram,
    build_horizontal_bar,
    build_stacked_bar,
    build_vertical_bar,
    build_violin,
)
from axiomfig.templates.panels import (
    build_complex_multi_panel,
    build_four_panel,
    build_six_panel,
    build_two_panel,
)
from axiomfig.templates.surfaces import (
    build_clustered_heatmap,
    build_confusion_matrix,
    build_correlation_heatmap,
    build_heatmap,
    build_mantel_test,
)

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
    "density": build_density,
    "ecdf": build_ecdf,
    "heatmap": build_heatmap,
    "correlation-heatmap": build_correlation_heatmap,
    "clustered-heatmap": build_clustered_heatmap,
    "confusion-matrix": build_confusion_matrix,
    "errorbar": build_errorbar,
    "forest-plot": build_forest_plot,
    "point-interval": build_point_interval,
    "bland-altman": build_bland_altman,
    "roc-curve": build_roc_curve,
    "pr-curve": build_pr_curve,
    "calibration-curve": build_calibration_curve,
    "residual-diagnostics": build_residual_diagnostics,
    "mantel-test": build_mantel_test,
    "model-evaluation": build_model_evaluation,
    "two-panel": build_two_panel,
    "four-panel": build_four_panel,
    "six-panel": build_six_panel,
    "complex-multi-panel": build_complex_multi_panel,
}


def get_template_builder(name: str) -> Callable[..., Figure]:
    try:
        return TEMPLATE_BUILDERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise KeyError(f"unknown template {name!r}; available: {available}") from exc


def _apply_family_layout(figure: Figure, name: str) -> None:
    panel_templates = {"two-panel", "four-panel", "six-panel", "complex-multi-panel"}
    if name not in panel_templates:
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
    refresh_panel_labels(figure)
    return figure
