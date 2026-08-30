from __future__ import annotations

from collections.abc import Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, PathPatch, Rectangle
from matplotlib.path import Path

from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.ornaments import request_legend
from axiomfig.style import (
    FILL_EDGE_PT,
    MAIN_STROKE_PT,
    apply_filled_collection_contract,
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
    palette_color,
    semantic_colormap,
)

_CANONICAL_MANTEL_MATRIX = np.asarray(
    (
        (1.00, 0.62, -0.31, 0.18, 0.44),
        (0.62, 1.00, -0.48, 0.27, 0.29),
        (-0.31, -0.48, 1.00, -0.54, -0.22),
        (0.18, 0.27, -0.54, 1.00, 0.36),
        (0.44, 0.29, -0.22, 0.36, 1.00),
    )
)
_CANONICAL_MANTEL_LABELS = ("Oxygen", "Ammonium", "Nitrate", "Phosphate", "Temperature")
_CANONICAL_MANTEL_LINKS = (
    {"source_group": "Surface", "target_label": "Oxygen", "mantel_r": 0.62, "p_value": 0.0006},
    {"source_group": "Surface", "target_label": "Nitrate", "mantel_r": 0.41, "p_value": 0.008},
    {"source_group": "Surface", "target_label": "Temperature", "mantel_r": 0.22, "p_value": 0.12},
    {"source_group": "Deep", "target_label": "Ammonium", "mantel_r": 0.33, "p_value": 0.032},
    {"source_group": "Deep", "target_label": "Phosphate", "mantel_r": 0.18, "p_value": 0.21},
)


def _mantel_inputs(
    correlation_matrix: object | None,
    labels: object | None,
    links: object | None,
) -> tuple[np.ndarray, list[str], tuple[Mapping[str, object], ...]]:
    if correlation_matrix is None and labels is None and links is None:
        return (
            _CANONICAL_MANTEL_MATRIX,
            list(_CANONICAL_MANTEL_LABELS),
            _CANONICAL_MANTEL_LINKS,
        )
    if correlation_matrix is None or labels is None or links is None:
        raise ValueError("Mantel requires correlation_matrix, labels, and links together")
    matrix = np.asarray(correlation_matrix, dtype=float)
    rendered_labels = [str(label) for label in np.asarray(labels, dtype=object)]
    if isinstance(links, (str, bytes)) or not isinstance(links, Sequence):
        raise ValueError("Mantel links must be a sequence of mappings")
    rendered_links = tuple(links)
    if any(not isinstance(link, Mapping) for link in rendered_links):
        raise ValueError("Mantel links must be mappings")
    return matrix, rendered_labels, rendered_links


def _mantel_matrix(
    axis: Axes,
    matrix: np.ndarray,
    labels: list[str],
    *,
    matrix_x0: float,
    matrix_y0: float,
    target_anchor_x: float,
    target_label_x: float,
) -> dict[str, tuple[float, float]]:
    contract = mantel_plot_contract()
    matrix_contract = contract["matrix"]
    assert isinstance(matrix_contract, Mapping)
    grid_color = palette_color(str(matrix_contract["grid_edge_color"]))
    cmap = mpl.colormaps[semantic_colormap(str(matrix_contract["color_semantics"]))]
    norm = Normalize(vmin=-1.0, vmax=1.0)
    minimum_side = float(matrix_contract["minimum_cell_side"])
    maximum_side = float(matrix_contract["maximum_cell_side"])
    count = len(labels)
    target_positions: dict[str, tuple[float, float]] = {}

    for row, row_label in enumerate(labels):
        y = matrix_y0 + count - row - 0.5
        target_positions[row_label] = (target_anchor_x, y)
        anchor = Circle(
            (target_anchor_x, y),
            0.045,
            facecolor="white",
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=4,
        )
        anchor.set_gid("axiomfig-mantel-target-anchor")
        axis.add_patch(anchor)
        label = axis.text(target_label_x, y, row_label, ha="left", va="center", zorder=4)
        label.set_gid("axiomfig-mantel-variable-label")
        for column in range(row, count):
            x = matrix_x0 + column + 0.5
            value = float(matrix[row, column])
            grid = Rectangle(
                (x - 0.46, y - 0.46),
                0.92,
                0.92,
                facecolor="none",
                edgecolor=grid_color,
                linewidth=FILL_EDGE_PT,
                zorder=1,
            )
            grid.set_gid("axiomfig-mantel-grid-cell")
            axis.add_patch(grid)
            side = minimum_side + (maximum_side - minimum_side) * abs(value)
            cell = Rectangle(
                (x - side / 2.0, y - side / 2.0),
                side,
                side,
                facecolor=cmap(norm(value)),
                edgecolor=str(matrix_contract["cell_edge_color"]),
                linewidth=FILL_EDGE_PT,
                zorder=2,
            )
            cell.set_gid("axiomfig-mantel-cell")
            cell._axiomfig_row = row
            cell._axiomfig_column = column
            cell._axiomfig_value = value
            axis.add_patch(cell)

    for column, label_text in enumerate(labels):
        label = axis.text(
            matrix_x0 + column + 0.5,
            matrix_y0 - 0.18,
            label_text,
            ha="right",
            va="top",
            rotation=45,
            fontsize=mpl.rcParams["font.size"] * 0.88,
            zorder=4,
        )
        label.set_gid("axiomfig-mantel-variable-label")
    axis.text(
        matrix_x0 + count / 2.0,
        matrix_y0 + count + 0.34,
        "Pearson correlation",
        ha="center",
        va="bottom",
        fontsize=mpl.rcParams["axes.titlesize"],
        fontweight="bold",
    )
    return target_positions


def _mantel_colorbar(axis: Axes, *, x: float, y: float, height: float, width: float) -> None:
    contract = mantel_plot_contract()["matrix"]
    assert isinstance(contract, Mapping)
    cmap = mpl.colormaps[semantic_colormap(str(contract["color_semantics"]))]
    image = axis.imshow(
        np.linspace(-1.0, 1.0, 256).reshape(-1, 1),
        extent=(x, x + width, y, y + height),
        origin="lower",
        cmap=cmap,
        vmin=-1.0,
        vmax=1.0,
        interpolation="nearest",
        zorder=2,
    )
    image.set_gid("axiomfig-mantel-colorbar")
    axis.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor="none",
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=3,
        )
    )
    for value in (-1.0, -0.5, 0.0, 0.5, 1.0):
        tick_y = y + (value + 1.0) * height / 2.0
        axis.plot(
            [x + width, x + width + 0.08],
            [tick_y, tick_y],
            color="black",
            linewidth=FILL_EDGE_PT,
            clip_on=True,
        )
        axis.text(x + width + 0.12, tick_y, f"{value:g}", ha="left", va="center", fontsize=7)
    axis.text(
        x + width + 0.72,
        y + height / 2.0,
        "Pearson r",
        rotation=90,
        ha="center",
        va="center",
        fontsize=7,
    )


def _mantel_links(
    axis: Axes,
    links: tuple[Mapping[str, object], ...],
    target_positions: Mapping[str, tuple[float, float]],
    *,
    matrix_y0: float,
    matrix_size: int,
    source_x: float,
    show_nonsignificant: bool,
) -> None:
    source_groups = list(dict.fromkeys(str(link["source_group"]) for link in links))
    source_y = np.linspace(matrix_y0 + matrix_size - 0.5, matrix_y0 + 0.5, len(source_groups))
    source_positions = dict(zip(source_groups, source_y, strict=True))
    for source, y in source_positions.items():
        node = Circle(
            (source_x, float(y)),
            0.085,
            facecolor="white",
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=5,
        )
        node.set_gid("axiomfig-mantel-source-node")
        axis.add_patch(node)
        label = axis.text(source_x - 0.12, y, source, ha="right", va="center", zorder=5)
        label.set_gid("axiomfig-mantel-source-label")

    for link in links:
        source = str(link["source_group"])
        target = str(link["target_label"])
        mantel_r = float(link["mantel_r"])
        p_value = float(link["p_value"])
        p_style = mantel_p_style(p_value)
        if not p_style["significant"] and not show_nonsignificant:
            continue
        start = (source_x + 0.10, float(source_positions[source]))
        end = target_positions[target]
        x_span = end[0] - start[0]
        path = Path(
            (
                start,
                (start[0] + x_span * 0.34, start[1]),
                (start[0] + x_span * 0.70, end[1]),
                end,
            ),
            (Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4),
        )
        patch = PathPatch(
            path,
            facecolor="none",
            edgecolor=p_style["color"],
            alpha=float(p_style["alpha"]),
            linewidth=mantel_link_width(mantel_r),
            capstyle="round",
            clip_on=True,
            zorder=3,
        )
        patch.set_gid("axiomfig-mantel-link")
        patch._axiomfig_source_group = source
        patch._axiomfig_target_label = target
        patch._axiomfig_mantel_r = mantel_r
        patch._axiomfig_p_value = p_value
        axis.add_patch(patch)


def _mantel_legends(axis: Axes) -> None:
    layout_contract = mantel_plot_contract()["layout"]
    assert isinstance(layout_contract, Mapping)
    legend_y = float(layout_contract["legend_y_fraction"])
    strength_handles = [
        Line2D([], [], color="black", linewidth=mantel_link_width(value), label=label)
        for value, label in ((0.1, "< 0.25"), (0.35, "0.25-0.50"), (0.65, ">= 0.50"))
    ]
    p_handles = [
        Line2D(
            [],
            [],
            color=mantel_p_style(value)["color"],
            alpha=float(mantel_p_style(value)["alpha"]),
            linewidth=MAIN_STROKE_PT * 1.8,
            label=label,
        )
        for value, label in (
            (0.0005, "< 0.001"),
            (0.005, "0.001-0.01"),
            (0.025, "0.01-0.05"),
            (0.10, ">= 0.05"),
        )
    ]
    common = {
        "frameon": False,
        "handlelength": 1.0,
        "borderaxespad": 0.0,
        "labelspacing": 0.35,
        "handletextpad": 0.6,
    }
    strength_legend = axis.legend(
        handles=strength_handles,
        title="Mantel r",
        loc="lower left",
        bbox_to_anchor=(float(layout_contract["strength_legend_x_fraction"]), legend_y),
        ncol=1,
        **common,
    )
    strength_legend.set_gid("axiomfig-mantel-legend")
    axis.add_artist(strength_legend)
    p_legend = axis.legend(
        handles=p_handles,
        title="P value",
        loc="lower left",
        bbox_to_anchor=(float(layout_contract["p_legend_x_fraction"]), legend_y),
        ncol=2,
        columnspacing=0.9,
        **common,
    )
    p_legend.set_gid("axiomfig-mantel-legend")


def build_mantel(
    correlation_matrix: object | None = None,
    labels: object | None = None,
    links: object | None = None,
    show_nonsignificant: object | None = None,
) -> Figure:
    matrix_values, label_values, link_values = _mantel_inputs(correlation_matrix, labels, links)
    contract = mantel_plot_contract()
    layout_contract = contract["layout"]
    link_contract = contract["links"]
    assert isinstance(layout_contract, Mapping)
    assert isinstance(link_contract, Mapping)
    show_nonsignificant_value = (
        bool(link_contract["show_nonsignificant"])
        if show_nonsignificant is None
        else bool(show_nonsignificant)
    )
    count = len(label_values)
    matrix_x0 = float(layout_contract["matrix_x0"])
    matrix_y0 = float(layout_contract["matrix_y0"])
    source_x = float(layout_contract["source_x"])
    target_anchor_x = matrix_x0 - float(layout_contract["target_anchor_offset"])
    target_label_x = matrix_x0 - float(layout_contract["target_label_offset"])
    colorbar_x = matrix_x0 + count + float(layout_contract["colorbar_gap"])
    colorbar_width = float(layout_contract["colorbar_width"])

    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, _ = add_panel_axes(layout, 0)
    target_positions = _mantel_matrix(
        axis,
        matrix_values,
        label_values,
        matrix_x0=matrix_x0,
        matrix_y0=matrix_y0,
        target_anchor_x=target_anchor_x,
        target_label_x=target_label_x,
    )
    _mantel_links(
        axis,
        link_values,
        target_positions,
        matrix_y0=matrix_y0,
        matrix_size=count,
        source_x=source_x,
        show_nonsignificant=show_nonsignificant_value,
    )
    _mantel_colorbar(
        axis,
        x=colorbar_x,
        y=matrix_y0,
        height=float(count),
        width=colorbar_width,
    )
    _mantel_legends(axis)
    axis.set_xlim(0.0, colorbar_x + colorbar_width + 1.05)
    axis.set_ylim(0.0, matrix_y0 + count + 0.82)
    axis.set_aspect("equal", adjustable="box")
    axis.set_axis_off()
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
    request_legend(axis)
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_axis_off()
    return figure


BUILDERS = {"mantel": build_mantel, "correlation_network": build_correlation_network}
