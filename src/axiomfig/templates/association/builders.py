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


def _node_positions(
    labels: list[str],
    *,
    x_value: float,
) -> dict[str, tuple[float, float]]:
    y_values = np.linspace(0.78, 0.22, len(labels))
    return {
        label: (x_value, float(y_value)) for label, y_value in zip(labels, y_values, strict=True)
    }


def build_mantel(
    correlation_matrix: object | None = None,
    matrix_labels: object | None = None,
    links: object | None = None,
    link_strength: object | None = None,
    significance: object | None = None,
    node_labels: object | None = None,
    strength_label: object | None = None,
) -> Figure:
    if correlation_matrix is None:
        canonical = True
        matrix_values = CORRELATION
        matrix_label_values = list(CORRELATION_LABELS)
        link_values = np.asarray(
            (
                ("COD", "Community"),
                ("TN", "Community"),
                ("TN", "Function"),
                ("TP", "Function"),
            ),
            dtype=object,
        )
        strength_values = np.asarray((0.61, 0.43, 0.68, 0.35))
        significance_values = np.asarray((True, False, True, False))
        ordered_nodes = ["COD", "TN", "TP", "Community", "Function"]
    elif all(value is not None for value in (matrix_labels, links, link_strength, significance)):
        canonical = False
        matrix_values = np.asarray(correlation_matrix, dtype=float)
        matrix_label_values = [str(label) for label in np.asarray(matrix_labels)]
        link_values = np.asarray(links, dtype=object).astype(str)
        strength_values = np.asarray(link_strength, dtype=float)
        significance_values = np.asarray(significance, dtype=bool)
        ordered_nodes = (
            [str(label) for label in np.asarray(node_labels)]
            if node_labels is not None
            else list(dict.fromkeys(link_values.ravel()))
        )
    else:
        raise ValueError("Mantel requires its matrix and link inputs together")
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 2, panel_labels=False)
    matrix_axis, _ = add_panel_axes(layout, 0)
    link_axis, _ = add_panel_axes(layout, 1)
    add_matrix(
        matrix_axis,
        matrix_values,
        matrix_label_values,
        annotate=True,
        vmin=float(min(0.0, matrix_values.min())),
        vmax=float(max(1.0, matrix_values.max())),
        color_semantics="diverging" if matrix_values.min() < 0 else "sequential",
        center=0.0 if matrix_values.min() < 0 else None,
    )
    matrix_axis.set_title("Environmental correlation")

    left_labels = [label for label in ordered_nodes if label in matrix_label_values]
    right_labels = [label for label in ordered_nodes if label not in matrix_label_values]
    positions = {
        **_node_positions(left_labels, x_value=0.12),
        **_node_positions(right_labels, x_value=0.85),
    }
    referenced = set(link_values.ravel())
    if referenced - set(positions):
        raise ValueError("Mantel links reference nodes outside node_labels")
    for label, (x_value, y_value) in positions.items():
        node = link_axis.scatter([x_value], [y_value], facecolor="white")
        apply_scatter_contract(node)
        link_axis.text(x_value, y_value + 0.08, label, ha="center", va="bottom")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for index, ((source_name, target_name), correlation, significant) in enumerate(
        zip(link_values, strength_values, significance_values, strict=True)
    ):
        source = positions[str(source_name)]
        target = positions[str(target_name)]
        link_axis.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color=colors[index % 2],
            linewidth=MAIN_STROKE_PT * (1.0 + 2.0 * correlation),
            linestyle="-" if significant else ":",
        )
        midpoint = ((source[0] + target[0]) / 2, (source[1] + target[1]) / 2)
        link_axis.text(*midpoint, f"r={correlation:.2f}", ha="center", va="bottom")
    prefix = f"{strength_label}; " if strength_label is not None else ""
    significant_label = "p < 0.05" if canonical else f"{prefix}significant"
    proxies = (
        Line2D(
            [],
            [],
            color=colors[0],
            linewidth=MAIN_STROKE_PT * 2.2,
            label=significant_label,
        ),
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


def build_correlation_network(
    nodes: object | None = None,
    edges: object | None = None,
    edge_weight: object | None = None,
    groups: object | None = None,
    significance: object | None = None,
    strength_label: object | None = None,
) -> Figure:
    if nodes is None and edges is None and edge_weight is None:
        labels = ["COD", "TN", "TP", "Oxygen", "Community", "Function"]
        edge_values = np.asarray(
            (
                ("COD", "Oxygen"),
                ("COD", "Community"),
                ("TN", "Community"),
                ("TN", "Function"),
                ("TP", "Function"),
                ("Oxygen", "Community"),
            ),
            dtype=object,
        )
        weight_values = np.asarray((0.74, 0.58, -0.61, 0.67, -0.52, 0.45))
        group_values = None
        significance_values = np.ones(len(edge_values), dtype=bool)
    elif nodes is not None and edges is not None and edge_weight is not None:
        labels = [str(label) for label in np.asarray(nodes)]
        edge_values = np.asarray(edges, dtype=object).astype(str)
        weight_values = np.asarray(edge_weight, dtype=float)
        group_values = np.asarray(groups, dtype=object).astype(str) if groups is not None else None
        significance_values = (
            np.asarray(significance, dtype=bool)
            if significance is not None
            else np.ones(len(edge_values), dtype=bool)
        )
    else:
        raise ValueError("correlation network requires nodes, edges, and edge_weight")
    angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, len(labels), endpoint=False)
    coordinates = [(0.5 + 0.36 * np.cos(a), 0.5 + 0.36 * np.sin(a)) for a in angles]
    coordinate_by_label = dict(zip(labels, coordinates, strict=True))
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    for (source, target), value, significant in zip(
        edge_values, weight_values, significance_values, strict=True
    ):
        x0, y0 = coordinate_by_label[str(source)]
        x1, y1 = coordinate_by_label[str(target)]
        axis.plot(
            [x0, x1],
            [y0, y1],
            color=colors[0] if value > 0 else colors[4],
            linewidth=MAIN_STROKE_PT * (1.0 + 2.0 * abs(value)),
            linestyle="-" if significant else ":",
        )
    for index, ((x, y), label) in enumerate(zip(coordinates, labels, strict=True)):
        color_index = index
        if group_values is not None:
            unique_groups = list(dict.fromkeys(group_values))
            color_index = unique_groups.index(group_values[index])
        node = axis.scatter([x], [y], color=colors[color_index % len(colors)])
        apply_filled_collection_contract(node, alpha=0.82)
        axis.text(x, y + 0.06, label, ha="center", va="bottom")
    prefix = f"{strength_label}: " if strength_label is not None else ""
    proxies = (
        Line2D(
            [],
            [],
            color=colors[0],
            linewidth=MAIN_STROKE_PT * 2.2,
            label=f"{prefix}positive",
        ),
        Line2D(
            [],
            [],
            color=colors[4],
            linewidth=MAIN_STROKE_PT * 2.2,
            label=f"{prefix}negative",
        ),
    )
    for proxy in proxies:
        axis.add_line(proxy)
    place_legend_above(axis)
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_axis_off()
    return figure


BUILDERS = {"mantel": build_mantel, "correlation_network": build_correlation_network}
