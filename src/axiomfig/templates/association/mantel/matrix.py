"""Structural matrix anatomy: masks, cells, labels, and target rail artists."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.patches import Circle, Rectangle

from axiomfig.style import FILL_EDGE_PT, mantel_plot_contract, mantel_visual_color
from axiomfig.templates.association.mantel.composition import MatrixSpec
from axiomfig.templates.association.mantel.data import MantelData
from axiomfig.templates.association.mantel.geometry import MantelGeometry, cell_center


@dataclass(frozen=True)
class MatrixCell:
    row: int
    column: int
    region: str


@dataclass(frozen=True)
class MatrixRenderResult:
    cells: tuple[MatrixCell, ...]
    target_anchors: tuple[object, ...]

    @property
    def visible_cells(self) -> int:
        return len(self.cells)


def select_matrix_cells(size: int, spec: MatrixSpec) -> tuple[MatrixCell, ...]:
    """Return the structural mask without consulting any glyph primitive."""
    cells: list[MatrixCell] = []
    for row in range(size):
        for column in range(size):
            if row == column and spec.diagonal == "hide":
                continue
            if spec.matrix_type == "full":
                region = "full"
            elif spec.matrix_type == "mixed":
                region = "lower" if row > column else "upper" if row < column else "diagonal"
            elif spec.matrix_type == "lower":
                if row < column:
                    continue
                region = "lower"
            else:
                if row < column:
                    continue
                region = "upper"
            cells.append(MatrixCell(row, column, region))
    return tuple(cells)


def _draw_labels(
    axis: Axes,
    labels: tuple[str, ...],
    geometry: MantelGeometry,
    matrix_type: str,
) -> tuple[object, ...]:
    bounds = geometry.bounds
    label_size = mpl.rcParams["font.size"] * (0.72 if len(labels) >= 15 else 0.80)
    rendered: list[object] = []
    if matrix_type in {"full", "mixed"}:
        for index, label in enumerate(labels):
            x, _ = cell_center(bounds, 0, index, matrix_type=matrix_type)
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
            rendered.append(artist)
            _, y = cell_center(bounds, index, 0, matrix_type=matrix_type)
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
            rendered.append(artist)
        return tuple(rendered)
    for label in labels:
        anchor_x, anchor_y = geometry.target_rail.anchors[label]
        if matrix_type == "lower":
            x, y, horizontal, vertical = anchor_x - 0.10, anchor_y + 0.10, "right", "bottom"
        else:
            x, y, horizontal, vertical = anchor_x + 0.10, anchor_y + 0.08, "left", "bottom"
        artist = axis.text(
            x,
            y,
            label,
            ha=horizontal,
            va=vertical,
            rotation=45 if matrix_type == "lower" else -45,
            fontsize=label_size,
            clip_on=True,
            zorder=5,
            bbox={
                "facecolor": mantel_visual_color("background"),
                "edgecolor": "none",
                "pad": 0.35,
                "alpha": 0.92,
            },
        )
        artist.set_gid("axiomfig-mantel-variable-label")
        rendered.append(artist)
    return tuple(rendered)


def render_matrix_layer(
    axis: Axes,
    data: MantelData,
    spec: MatrixSpec,
    geometry: MantelGeometry,
    *,
    show_target_anchors: bool,
) -> MatrixRenderResult:
    """Render only matrix structure; glyphs, statistics, and coupling are separate layers."""
    cells = select_matrix_cells(len(data.labels), spec)
    grid_color = mantel_visual_color("grid_edge")
    for cell in cells:
        x, y = cell_center(
            geometry.bounds,
            cell.row,
            cell.column,
            matrix_type=spec.matrix_type,
        )
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
        grid._axiomfig_row = cell.row
        grid._axiomfig_column = cell.column
        axis.add_patch(grid)
    _draw_labels(axis, data.labels, geometry, spec.matrix_type)
    anchors: list[object] = []
    if show_target_anchors:
        matrix_contract = mantel_plot_contract()["matrix"]
        assert isinstance(matrix_contract, Mapping)
        radius = float(matrix_contract["target_anchor_radius"])
        for label, (x, y) in geometry.target_rail.anchors.items():
            anchor = Circle(
                (x, y),
                radius,
                facecolor=mantel_visual_color("background"),
                edgecolor=mantel_visual_color("cell_edge"),
                linewidth=FILL_EDGE_PT,
                zorder=5.2,
            )
            anchor.set_gid("axiomfig-mantel-target-anchor")
            anchor._axiomfig_target = label
            axis.add_patch(anchor)
            anchors.append(anchor)
    return MatrixRenderResult(cells, tuple(anchors))


__all__ = ["MatrixCell", "MatrixRenderResult", "render_matrix_layer", "select_matrix_cells"]
