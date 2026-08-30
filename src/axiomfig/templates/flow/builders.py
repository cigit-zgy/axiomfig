from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

from axiomfig.style import FILL_EDGE_PT


def _ribbon(
    axis: plt.Axes,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    color: str,
) -> None:
    x0, y0, height0 = start
    x1, y1, height1 = end
    control = (x1 - x0) * 0.48
    vertices = [
        (x0, y0),
        (x0 + control, y0),
        (x1 - control, y1),
        (x1, y1),
        (x1, y1 + height1),
        (x1 - control, y1 + height1),
        (x0 + control, y0 + height0),
        (x0, y0 + height0),
        (x0, y0),
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    axis.add_patch(
        PathPatch(
            Path(vertices, codes),
            facecolor=mcolors.to_rgba(color, 0.55),
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
        )
    )


def _nodes(
    labels: list[str],
    totals: dict[str, float],
    *,
    x_value: float,
    scale: float,
) -> tuple[tuple[float, float, float, str], ...]:
    gap = 0.06
    top = 0.86
    nodes: list[tuple[float, float, float, str]] = []
    cursor = top
    for label in labels:
        height = totals[label] * scale
        y_value = cursor - height
        nodes.append((x_value, y_value, height, label))
        cursor = y_value - gap
    return tuple(nodes)


def build_sankey(
    source: object | None = None,
    target: object | None = None,
    value: object | None = None,
    node_labels: object | None = None,
    flow_labels: object | None = None,
) -> Figure:
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    if source is None and target is None and value is None:
        source_values = np.asarray(
            ("Influent", "Influent", "Recycle", "Recycle", "Carbon", "Carbon")
        )
        target_values = np.asarray(
            ("Biomass", "Effluent", "Biomass", "Effluent", "Biomass", "Effluent")
        )
        value_values = np.asarray((0.12, 0.06, 0.08, 0.06, 0.04, 0.07))
        left_labels = ["Influent", "Recycle", "Carbon"]
        right_labels = ["Biomass", "Effluent"]
        left = (
            (0.10, 0.68, 0.18, "Influent"),
            (0.10, 0.39, 0.14, "Recycle"),
            (0.10, 0.15, 0.11, "Carbon"),
        )
        right = (
            (0.82, 0.56, 0.24, "Biomass"),
            (0.82, 0.20, 0.19, "Effluent"),
        )
        scale = 1.0
    elif source is not None and target is not None and value is not None:
        source_values = np.asarray(source, dtype=object).astype(str)
        target_values = np.asarray(target, dtype=object).astype(str)
        value_values = np.asarray(value, dtype=float)
        ordered = (
            [str(label) for label in np.asarray(node_labels)]
            if node_labels is not None
            else list(dict.fromkeys(np.concatenate((source_values, target_values))))
        )
        left_labels = [label for label in ordered if label in set(source_values)]
        right_labels = [label for label in ordered if label in set(target_values)]
        source_totals = {
            label: float(value_values[source_values == label].sum()) for label in left_labels
        }
        target_totals = {
            label: float(value_values[target_values == label].sum()) for label in right_labels
        }
        available = min(
            0.72 - 0.06 * (len(left_labels) - 1),
            0.72 - 0.06 * (len(right_labels) - 1),
        )
        scale = available / float(value_values.sum())
        left = _nodes(left_labels, source_totals, x_value=0.10, scale=scale)
        right = _nodes(right_labels, target_totals, x_value=0.82, scale=scale)
    else:
        raise ValueError("Sankey requires source, target, and value together")
    left_by_label = {item[3]: item for item in left}
    right_by_label = {item[3]: item for item in right}
    left_offsets = {label: 0.0 for label in left_labels}
    right_offsets = {label: 0.0 for label in right_labels}
    flow_label_values = (
        np.asarray(flow_labels, dtype=object)
        if flow_labels is not None
        else np.full(len(value_values), "", dtype=object)
    )
    for source_label, target_label, flow_value, flow_label in zip(
        source_values,
        target_values,
        value_values,
        flow_label_values,
        strict=True,
    ):
        source_node = left_by_label[source_label]
        target_node = right_by_label[target_label]
        height = float(flow_value) * scale
        start = (
            source_node[0] + 0.05,
            source_node[1] + left_offsets[source_label],
            height,
        )
        end = (
            target_node[0],
            target_node[1] + right_offsets[target_label],
            height,
        )
        _ribbon(
            axis,
            start,
            end,
            colors[left_labels.index(source_label) % len(colors)],
        )
        if str(flow_label):
            axis.text(
                (start[0] + end[0]) / 2,
                (start[1] + end[1] + height) / 2,
                str(flow_label),
                ha="center",
                va="center",
            )
        left_offsets[source_label] += height
        right_offsets[target_label] += height
    for x, y, height, label in (*left, *right):
        axis.add_patch(
            Rectangle(
                (x, y),
                0.05,
                height,
                facecolor="white",
                edgecolor="black",
                linewidth=FILL_EDGE_PT,
            )
        )
        label_x = x - 0.02 if x < 0.5 else x + 0.07
        axis.text(
            label_x,
            y + height / 2,
            label,
            ha="right" if x < 0.5 else "left",
            va="center",
        )
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_axis_off()
    return figure


BUILDERS = {"sankey": build_sankey}
