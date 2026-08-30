"""Structural Mantel matrix anatomy: masks, subtle scaffold, labels, and target rail."""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from axiomfig.style import FILL_EDGE_PT, mantel_visual_color
from axiomfig.templates.association.mantel.composition import MatrixSpec
from axiomfig.templates.association.mantel.data import MantelData
from axiomfig.templates.association.mantel.geometry import (
    MantelGeometry,
    cell_center,
    variable_label_size,
)


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
    """Return a logical structural mask independent from presentation and glyph primitives."""
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
                if row > column:
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
    """Place variable identity only on the two edges adjacent to colored matrix cells."""
    bounds = geometry.bounds
    size = variable_label_size(len(labels))
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
                fontsize=size,
                clip_on=True,
                zorder=5,
            )
            artist.set_gid("axiomfig-mantel-variable-label")
            artist._axiomfig_edge = "top"
            rendered.append(artist)
            _, y = cell_center(bounds, index, 0, matrix_type=matrix_type)
            artist = axis.text(
                bounds.x0 - 0.10,
                y,
                label,
                ha="right",
                va="center",
                fontsize=size,
                clip_on=True,
                zorder=5,
            )
            artist.set_gid("axiomfig-mantel-variable-label")
            artist._axiomfig_edge = "left"
            rendered.append(artist)
        return tuple(rendered)

    for index, label in enumerate(labels):
        x, y = cell_center(bounds, index, index, matrix_type=matrix_type)
        for edge in geometry.label_edges:
            if edge == "left":
                position = (bounds.x0 - 0.12, y)
                options = {"ha": "right", "va": "center", "rotation": 0}
            elif edge == "bottom":
                position = (x, bounds.y0 - 0.12)
                options = {"ha": "right", "va": "center", "rotation": 90}
            elif edge == "top":
                position = (x, bounds.y1 + 0.12)
                options = {"ha": "left", "va": "center", "rotation": 90}
            else:
                position = (bounds.x1 + 0.12, y)
                options = {"ha": "left", "va": "center", "rotation": 0}
            artist = axis.text(
                *position,
                label,
                rotation_mode="anchor",
                fontsize=size,
                clip_on=True,
                zorder=5,
                **options,
            )
            artist.set_gid("axiomfig-mantel-variable-label")
            artist._axiomfig_edge = edge
            rendered.append(artist)
    return tuple(rendered)


def render_matrix_layer(
    axis: Axes,
    data: MantelData,
    spec: MatrixSpec,
    geometry: MantelGeometry,
) -> MatrixRenderResult:
    """Render matrix scaffold and labels; glyph/statistical/coupling layers remain independent."""
    cells = select_matrix_cells(len(data.labels), spec)
    grid_color = mantel_visual_color("grid_edge")
    for cell in cells:
        x, y = cell_center(
            geometry.bounds,
            cell.row,
            cell.column,
            matrix_type=geometry.matrix_type,
        )
        grid = Rectangle(
            (x - 0.48, y - 0.48),
            0.96,
            0.96,
            facecolor="none",
            edgecolor=grid_color,
            linewidth=FILL_EDGE_PT * 0.32,
            alpha=0.24,
            zorder=1,
        )
        grid.set_gid("axiomfig-mantel-grid-cell")
        grid._axiomfig_row = cell.row
        grid._axiomfig_column = cell.column
        axis.add_patch(grid)

    _draw_labels(axis, data.labels, geometry, spec.matrix_type)
    return MatrixRenderResult(cells, ())


__all__ = ["MatrixCell", "MatrixRenderResult", "render_matrix_layer", "select_matrix_cells"]
