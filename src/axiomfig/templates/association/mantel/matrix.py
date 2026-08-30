"""Correlation matrix composition, masks, labels, significance, and CI layers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Rectangle

from axiomfig.style import FILL_EDGE_PT, palette_color, semantic_colormap
from axiomfig.templates.association.mantel.data import MantelData, MantelOptions
from axiomfig.templates.association.mantel.geometry import MantelGeometry, cell_center
from axiomfig.templates.association.mantel.glyphs import draw_confidence_interval, draw_glyph


@dataclass(frozen=True)
class MatrixRenderResult:
    visible_cells: int
    glyphs: int


def _visible(row: int, column: int, matrix_type: str, diagonal: str) -> bool:
    if diagonal == "hide" and row == column:
        return False
    if matrix_type in {"full", "mixed"}:
        return True
    if matrix_type == "upper":
        return column >= row
    return row >= column


def _method(row: int, column: int, options: MantelOptions) -> tuple[str, str]:
    if options.matrix_type != "mixed":
        return options.matrix_method, options.matrix_type
    if row > column:
        return options.lower_method, "lower"
    if row < column:
        return options.upper_method, "upper"
    return options.lower_method, "diagonal"


def _stars(p_value: float, thresholds: tuple[float, ...]) -> str:
    return "*" * sum(p_value <= threshold for threshold in thresholds)


def _significance_overlay(
    axis: Axes,
    mode: str,
    p_value: float,
    thresholds: tuple[float, ...],
    x: float,
    y: float,
) -> None:
    threshold = thresholds[0]
    label: str | None = None
    if mode == "mark" and p_value > threshold:
        label = "×"
    elif mode == "p_value" and p_value > threshold:
        label = f"{p_value:.3g}"
    elif mode == "label_sig" and p_value <= threshold:
        label = _stars(p_value, thresholds)
    if label is None:
        return
    artist = axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        color="black",
        fontsize=mpl.rcParams["font.size"] * 0.72,
        fontweight="bold" if mode == "label_sig" else "normal",
        zorder=4,
    )
    artist.set_gid("axiomfig-mantel-significance")
    artist._axiomfig_significance_mode = mode


def _coefficient(
    axis: Axes,
    value: float,
    x: float,
    y: float,
    *,
    number_format: str,
) -> None:
    if not np.isfinite(value):
        return
    label = f"{value * 100:.0f}%" if number_format == "percent" else f"{value:.2f}"
    artist = axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        color="black",
        fontsize=mpl.rcParams["font.size"] * 0.62,
        zorder=3.5,
    )
    artist.set_gid("axiomfig-mantel-coefficient")


def _draw_labels(axis: Axes, labels: tuple[str, ...], geometry: MantelGeometry, matrix_type: str):
    bounds = geometry.bounds
    label_size = mpl.rcParams["font.size"] * (0.74 if len(labels) >= 15 else 0.82)
    if matrix_type in {"full", "mixed"}:
        for index, label in enumerate(labels):
            x, _ = cell_center(bounds, 0, index)
            artist = axis.text(
                x,
                bounds.y1 + 0.10,
                label,
                ha="left",
                va="bottom",
                rotation=45,
                fontsize=label_size,
                clip_on=True,
                zorder=5,
            )
            artist.set_gid("axiomfig-mantel-variable-label")
            _, y = cell_center(bounds, index, 0)
            artist = axis.text(
                bounds.x1 + 0.12,
                y,
                label,
                ha="left",
                va="center",
                fontsize=label_size,
                clip_on=True,
                zorder=5,
            )
            artist.set_gid("axiomfig-mantel-variable-label")
        return
    for label in labels:
        anchor_x, anchor_y = geometry.target_positions[label]
        if matrix_type == "upper":
            x, y, horizontal, vertical = anchor_x - 0.06, anchor_y - 0.10, "right", "top"
        elif matrix_type == "mixed":
            x, y, horizontal, vertical = anchor_x - 0.10, anchor_y, "right", "center"
        else:
            x, y, horizontal, vertical = anchor_x + 0.11, anchor_y + 0.05, "left", "bottom"
        artist = axis.text(
            x,
            y,
            label,
            ha=horizontal,
            va=vertical,
            rotation=45 if matrix_type != "mixed" else 0,
            fontsize=label_size,
            clip_on=True,
            zorder=5,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5, "alpha": 0.92},
        )
        artist.set_gid("axiomfig-mantel-variable-label")


def _draw_cluster_rectangles(
    axis: Axes,
    geometry: MantelGeometry,
    cluster_positions: Sequence[Sequence[int]],
) -> None:
    bounds = geometry.bounds
    for cluster in cluster_positions:
        positions = tuple(sorted(cluster))
        first, last = positions[0], positions[-1]
        x0 = bounds.x0 + first
        y0 = bounds.y0 + bounds.size - last - 1
        side = last - first + 1
        artist = Rectangle(
            (x0 + 0.025, y0 + 0.025),
            side - 0.05,
            side - 0.05,
            facecolor="none",
            edgecolor="black",
            linewidth=1.1,
            zorder=4.5,
        )
        artist.set_gid("axiomfig-mantel-cluster-rectangle")
        axis.add_patch(artist)


def render_matrix(
    axis: Axes,
    data: MantelData,
    options: MantelOptions,
    geometry: MantelGeometry,
    *,
    cluster_positions: Sequence[Sequence[int]] = (),
) -> MatrixRenderResult:
    """Render the correlation canvas from synchronized precomputed layers."""
    cmap = mpl.colormaps[semantic_colormap("diverging")]
    norm = Normalize(vmin=-1.0, vmax=1.0)
    grid_color = palette_color("AxiomGrey")
    visible_cells = 0
    glyph_count = 0
    size = len(data.labels)
    for row in range(size):
        for column in range(size):
            if not _visible(row, column, options.matrix_type, options.diagonal):
                continue
            x, y = cell_center(geometry.bounds, row, column)
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
            grid._axiomfig_row = row
            grid._axiomfig_column = column
            axis.add_patch(grid)
            visible_cells += 1
            value = float(data.correlation_matrix[row, column])
            p_value = (
                float(data.p_values[row, column]) if data.p_values is not None else float("nan")
            )
            if (
                options.significance_mode == "blank"
                and np.isfinite(p_value)
                and p_value > options.significance_thresholds[0]
            ):
                continue
            method, triangle = _method(row, column, options)
            if options.ci_mode != "none" and np.isfinite(value):
                assert data.lower_ci is not None and data.upper_ci is not None
                lower = float(data.lower_ci[row, column])
                upper = float(data.upper_ci[row, column])
                if np.isfinite(lower) and np.isfinite(upper):
                    draw_confidence_interval(
                        axis,
                        options.ci_mode,
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
            else:
                draw_glyph(
                    axis,
                    method,
                    x,
                    y,
                    value,
                    cmap=cmap,
                    norm=norm,
                    row=row,
                    column=column,
                    triangle=triangle,
                    number_format=options.coefficient_format,
                )
                glyph_count += 1
            if options.coefficients and method != "number":
                _coefficient(
                    axis,
                    value,
                    x,
                    y,
                    number_format=options.coefficient_format,
                )
            if options.significance_mode not in {"none", "blank"} and np.isfinite(p_value):
                _significance_overlay(
                    axis,
                    options.significance_mode,
                    p_value,
                    options.significance_thresholds,
                    x,
                    y,
                )
    _draw_labels(axis, data.labels, geometry, options.matrix_type)
    for label, (x, y) in geometry.target_positions.items():
        anchor = Circle(
            (x, y),
            0.035,
            facecolor="white",
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=5.2,
        )
        anchor.set_gid("axiomfig-mantel-target-anchor")
        anchor._axiomfig_target = label
        axis.add_patch(anchor)
    if cluster_positions:
        _draw_cluster_rectangles(axis, geometry, cluster_positions)
    return MatrixRenderResult(visible_cells, glyph_count)


__all__ = ["MatrixRenderResult", "render_matrix"]
