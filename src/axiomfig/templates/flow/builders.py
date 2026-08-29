from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

from axiomfig.contracts import FILL_EDGE_PT


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


def build_sankey() -> Figure:
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    left = (
        (0.10, 0.68, 0.18, "Influent"),
        (0.10, 0.39, 0.14, "Recycle"),
        (0.10, 0.15, 0.11, "Carbon"),
    )
    right = ((0.82, 0.56, 0.24, "Biomass"), (0.82, 0.20, 0.19, "Effluent"))
    flows = (
        (left[0], right[0], 0.12, colors[0]),
        (left[0], right[1], 0.06, colors[0]),
        (left[1], right[0], 0.08, colors[1]),
        (left[1], right[1], 0.06, colors[1]),
        (left[2], right[0], 0.04, colors[2]),
        (left[2], right[1], 0.07, colors[2]),
    )
    left_offsets = [0.0, 0.0, 0.0]
    right_offsets = [0.0, 0.0]
    for source, target, height, color in flows:
        source_index = left.index(source)
        target_index = right.index(target)
        _ribbon(
            axis,
            (source[0] + 0.05, source[1] + left_offsets[source_index], height),
            (target[0], target[1] + right_offsets[target_index], height),
            color,
        )
        left_offsets[source_index] += height
        right_offsets[target_index] += height
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
