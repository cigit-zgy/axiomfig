from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from axiomfig.contracts import MAIN_STROKE_PT
from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.template_helpers import (
    apply_filled_collection_contract,
    apply_scatter_contract,
    place_legend_above,
)
from axiomfig.templates.heatmap.builders import CORRELATION, CORRELATION_LABELS, add_matrix


def build_mantel() -> Figure:
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 2, panel_labels=False)
    matrix_axis, _ = add_panel_axes(layout, 0)
    link_axis, _ = add_panel_axes(layout, 1)
    add_matrix(
        matrix_axis,
        CORRELATION,
        CORRELATION_LABELS,
        annotate=True,
        vmin=0.0,
        vmax=1.0,
        color_semantics="sequential",
    )
    matrix_axis.set_title("Environmental correlation")

    left = [(0.12, 0.78, "COD"), (0.12, 0.50, "TN"), (0.12, 0.22, "TP")]
    right = [(0.85, 0.70, "Community"), (0.85, 0.30, "Function")]
    for x, y, label in left + right:
        node = link_axis.scatter([x], [y], facecolor="white")
        apply_scatter_contract(node)
        link_axis.text(x, y + 0.08, label, ha="center", va="bottom")
    links = (
        (left[0], right[0], 0.61, True),
        (left[1], right[0], 0.43, False),
        (left[1], right[1], 0.68, True),
        (left[2], right[1], 0.35, False),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for index, (source, target, correlation, significant) in enumerate(links):
        link_axis.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color=colors[index % 2],
            linewidth=MAIN_STROKE_PT * (1.0 + 2.0 * correlation),
            linestyle="-" if significant else ":",
        )
        midpoint = ((source[0] + target[0]) / 2, (source[1] + target[1]) / 2)
        link_axis.text(*midpoint, f"r={correlation:.2f}", ha="center", va="bottom")
    proxies = (
        Line2D([], [], color=colors[0], linewidth=MAIN_STROKE_PT * 2.2, label="p < 0.05"),
        Line2D(
            [],
            [],
            color=colors[1],
            linewidth=MAIN_STROKE_PT * 1.8,
            linestyle=":",
            label="not significant",
        ),
    )
    for proxy in proxies:
        link_axis.add_line(proxy)
    place_legend_above(link_axis)
    link_axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    link_axis.set_axis_off()
    return figure


def build_correlation_network() -> Figure:
    labels = ["COD", "TN", "TP", "Oxygen", "Community", "Function"]
    angles = [2.62, 2.09, 1.57, 0.52, -0.52, -1.57]
    coordinates = [(0.5 + 0.36 * np.cos(a), 0.5 + 0.36 * np.sin(a)) for a in angles]
    edges = (
        (0, 3, 0.74),
        (0, 4, 0.58),
        (1, 4, -0.61),
        (1, 5, 0.67),
        (2, 5, -0.52),
        (3, 4, 0.45),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    for source, target, value in edges:
        x0, y0 = coordinates[source]
        x1, y1 = coordinates[target]
        axis.plot(
            [x0, x1],
            [y0, y1],
            color=colors[0] if value > 0 else colors[4],
            linewidth=MAIN_STROKE_PT * (1.0 + 2.0 * abs(value)),
        )
    for index, ((x, y), label) in enumerate(zip(coordinates, labels, strict=True)):
        node = axis.scatter([x], [y], color=colors[index % len(colors)])
        apply_filled_collection_contract(node, alpha=0.82)
        axis.text(x, y + 0.06, label, ha="center", va="bottom")
    proxies = (
        Line2D([], [], color=colors[0], linewidth=MAIN_STROKE_PT * 2.2, label="positive"),
        Line2D([], [], color=colors[4], linewidth=MAIN_STROKE_PT * 2.2, label="negative"),
    )
    for proxy in proxies:
        axis.add_line(proxy)
    place_legend_above(axis)
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_axis_off()
    return figure


BUILDERS = {"mantel": build_mantel, "correlation_network": build_correlation_network}
