"""Independent statistical artists composed over normalized matrix cells."""

from __future__ import annotations

import math
from collections.abc import Sequence

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Rectangle

from axiomfig.style import (
    FILL_EDGE_PT,
    MAIN_STROKE_PT,
    mantel_plot_contract,
    mantel_visual_color,
)
from axiomfig.templates.association.mantel.composition import (
    ClusterOutlineOverlay,
    CoefficientOverlay,
    ConfidenceIntervalOverlay,
    SignificanceOverlay,
    StatisticalOverlay,
)
from axiomfig.templates.association.mantel.data import MantelData
from axiomfig.templates.association.mantel.geometry import MantelGeometry, cell_center


def visible_glyph_cells(
    data: MantelData,
    cells: Sequence[object],
    overlays: Sequence[StatisticalOverlay],
) -> set[tuple[int, int]]:
    """Apply overlay visibility policies before any glyph primitive is rendered."""
    blank = next(
        (
            overlay
            for overlay in overlays
            if isinstance(overlay, SignificanceOverlay) and overlay.mode == "blank"
        ),
        None,
    )
    visible: set[tuple[int, int]] = set()
    for cell in cells:
        key = (cell.row, cell.column)
        if blank is None or data.p_values is None:
            visible.add(key)
            continue
        p_value = float(data.p_values[cell.row, cell.column])
        if not np.isfinite(p_value) or p_value <= blank.thresholds[0]:
            visible.add(key)
    return visible


def _stars(p_value: float, thresholds: tuple[float, ...]) -> str:
    return "*" * sum(p_value <= threshold for threshold in thresholds)


def _significance(
    axis: Axes,
    overlay: SignificanceOverlay,
    p_value: float,
    x: float,
    y: float,
) -> object | None:
    threshold = overlay.thresholds[0]
    label: str | None = None
    if overlay.mode == "mark" and p_value > threshold:
        label = "×"
    elif overlay.mode == "p_value" and p_value > threshold:
        label = f"{p_value:.3g}"
    elif overlay.mode == "label_sig" and p_value <= threshold:
        label = _stars(p_value, overlay.thresholds)
    if label is None:
        return None
    artist = axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        color=mantel_visual_color("cell_edge"),
        fontsize=mpl.rcParams["font.size"] * 0.72,
        fontweight="bold" if overlay.mode == "label_sig" else "normal",
        zorder=4,
    )
    artist.set_gid("axiomfig-mantel-significance")
    artist._axiomfig_significance_mode = overlay.mode
    return artist


def _coefficient(
    axis: Axes,
    overlay: CoefficientOverlay,
    value: float,
    x: float,
    y: float,
) -> object | None:
    if not np.isfinite(value):
        return None
    label = f"{value * 100:.0f}%" if overlay.number_format == "percent" else f"{value:.2f}"
    artist = axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        color=mantel_visual_color("cell_edge"),
        fontsize=mpl.rcParams["font.size"] * 0.62,
        zorder=3.5,
    )
    artist.set_gid("axiomfig-mantel-coefficient")
    return artist


def _confidence_interval(
    axis: Axes,
    overlay: ConfidenceIntervalOverlay,
    x: float,
    y: float,
    estimate: float,
    lower: float,
    upper: float,
    *,
    cmap: mpl.colors.Colormap,
    norm: Normalize,
    row: int,
    column: int,
) -> object:
    edge_lower = cmap(norm(lower))
    edge_upper = cmap(norm(upper))
    estimate_color = cmap(norm(estimate))
    matrix_contract = mantel_plot_contract()["matrix"]
    cell_side = float(matrix_contract["maximum_cell_side"])
    if overlay.mode == "square":
        outer = cell_side * math.sqrt(max(abs(lower), abs(upper)))
        artist = Rectangle(
            (x - outer / 2.0, y - outer / 2.0),
            outer,
            outer,
            facecolor="none",
            edgecolor=edge_upper,
            linewidth=MAIN_STROKE_PT,
            zorder=3.0,
        )
        inner = cell_side * math.sqrt(min(abs(lower), abs(upper)))
        axis.add_patch(
            Rectangle(
                (x - inner / 2.0, y - inner / 2.0),
                inner,
                inner,
                facecolor="none",
                edgecolor=edge_lower,
                linewidth=FILL_EDGE_PT,
                zorder=3.1,
            )
        )
    elif overlay.mode == "circle":
        outer = cell_side / 2.0 * math.sqrt(max(abs(lower), abs(upper)))
        artist = Circle(
            (x, y),
            outer,
            facecolor="none",
            edgecolor=edge_upper,
            linewidth=MAIN_STROKE_PT,
            zorder=3.0,
        )
        inner = cell_side / 2.0 * math.sqrt(min(abs(lower), abs(upper)))
        axis.add_patch(
            Circle(
                (x, y),
                inner,
                facecolor="none",
                edgecolor=edge_lower,
                linewidth=FILL_EDGE_PT,
                zorder=3.1,
            )
        )
    else:
        low_y = y + 0.40 * lower
        high_y = y + 0.40 * upper
        artist = Rectangle(
            (x - 0.20, low_y),
            0.40,
            max(high_y - low_y, 0.006),
            facecolor=(*estimate_color[:3], 0.16),
            edgecolor=mantel_visual_color("cell_edge"),
            linewidth=FILL_EDGE_PT,
            zorder=3.0,
        )
        for value, color in ((lower, edge_lower), (estimate, estimate_color), (upper, edge_upper)):
            line_y = y + 0.40 * value
            axis.plot(
                [x - 0.24, x + 0.24],
                [line_y, line_y],
                color=color,
                linewidth=MAIN_STROKE_PT,
                zorder=3.2,
            )
    axis.add_patch(artist)
    axis.add_patch(
        Circle(
            (x, y),
            0.035,
            facecolor=estimate_color,
            edgecolor=mantel_visual_color("cell_edge"),
            linewidth=FILL_EDGE_PT,
            zorder=3.4,
        )
    )
    artist.set_gid("axiomfig-mantel-confidence-interval")
    artist._axiomfig_ci_mode = overlay.mode
    artist._axiomfig_row = row
    artist._axiomfig_column = column
    return artist


def _cluster_outlines(
    axis: Axes,
    geometry: MantelGeometry,
    matrix_type: str,
    cluster_positions: Sequence[Sequence[int]],
) -> tuple[object, ...]:
    rendered: list[object] = []
    for cluster in cluster_positions:
        positions = tuple(sorted(cluster))
        first, last = positions[0], positions[-1]
        centers = [
            cell_center(geometry.bounds, index, index, matrix_type=matrix_type)
            for index in (first, last)
        ]
        x0 = min(point[0] for point in centers) - 0.475
        y0 = min(point[1] for point in centers) - 0.475
        side = last - first + 0.95
        artist = Rectangle(
            (x0, y0),
            side,
            side,
            facecolor="none",
            edgecolor=mantel_visual_color("cell_edge"),
            linewidth=MAIN_STROKE_PT * 1.35,
            zorder=4.5,
        )
        artist.set_gid("axiomfig-mantel-cluster-rectangle")
        axis.add_patch(artist)
        rendered.append(artist)
    return tuple(rendered)


def render_statistical_layers(
    axis: Axes,
    data: MantelData,
    cells: Sequence[object],
    overlays: Sequence[StatisticalOverlay],
    geometry: MantelGeometry,
    *,
    matrix_type: str,
    cmap: mpl.colors.Colormap,
    norm: Normalize,
    cluster_positions: Sequence[Sequence[int]] = (),
) -> tuple[object, ...]:
    """Compose independent overlay artists over one shared cell coordinate system."""
    rendered: list[object] = []
    for overlay in overlays:
        if isinstance(overlay, ClusterOutlineOverlay):
            rendered.extend(_cluster_outlines(axis, geometry, matrix_type, cluster_positions))
            continue
        if isinstance(overlay, SignificanceOverlay) and overlay.mode == "blank":
            continue
        for cell in cells:
            row, column = cell.row, cell.column
            x, y = cell_center(geometry.bounds, row, column, matrix_type=matrix_type)
            value = float(data.correlation_matrix[row, column])
            artist: object | None = None
            if isinstance(overlay, CoefficientOverlay):
                artist = _coefficient(axis, overlay, value, x, y)
            elif isinstance(overlay, SignificanceOverlay):
                if data.p_values is not None:
                    p_value = float(data.p_values[row, column])
                    if np.isfinite(p_value):
                        artist = _significance(axis, overlay, p_value, x, y)
            elif (
                isinstance(overlay, ConfidenceIntervalOverlay)
                and data.lower_ci is not None
                and data.upper_ci is not None
                and np.isfinite(value)
            ):
                lower = float(data.lower_ci[row, column])
                upper = float(data.upper_ci[row, column])
                if np.isfinite(lower) and np.isfinite(upper):
                    artist = _confidence_interval(
                        axis,
                        overlay,
                        x,
                        y,
                        value,
                        lower,
                        upper,
                        cmap=cmap,
                        norm=norm,
                        row=row,
                        column=column,
                    )
            if artist is not None:
                rendered.append(artist)
    return tuple(rendered)


__all__ = ["render_statistical_layers", "visible_glyph_cells"]
