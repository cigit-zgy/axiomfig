"""Canonical precomputed correlation-network builder."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from axiomfig.ornaments import request_legend
from axiomfig.style import MAIN_STROKE_PT, apply_filled_collection_contract


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
        Line2D([], [], color=colors[0], linewidth=MAIN_STROKE_PT * 2.2, label=f"{prefix}positive"),
        Line2D([], [], color=colors[4], linewidth=MAIN_STROKE_PT * 2.2, label=f"{prefix}negative"),
    )
    for proxy in proxies:
        axis.add_line(proxy)
    request_legend(axis)
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_axis_off()
    return figure


__all__ = ["build_correlation_network"]
