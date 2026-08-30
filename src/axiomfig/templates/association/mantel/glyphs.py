"""Reusable vector correlation glyph primitives and glyph-layer rendering."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Ellipse, Rectangle, Wedge

from axiomfig.style import FILL_EDGE_PT, mantel_plot_contract, mantel_visual_color
from axiomfig.templates.association.mantel.composition import GlyphSpec
from axiomfig.templates.association.mantel.data import MantelData
from axiomfig.templates.association.mantel.geometry import MantelGeometry, cell_center


def _cell_side() -> float:
    matrix = mantel_plot_contract()["matrix"]
    assert isinstance(matrix, Mapping)
    return float(matrix["maximum_cell_side"])


def _tag(artist, *, method: str, row: int, column: int, value: float, region: str):
    artist.set_gid("axiomfig-mantel-glyph")
    artist._axiomfig_method = method
    artist._axiomfig_row = row
    artist._axiomfig_column = column
    artist._axiomfig_value = value
    artist._axiomfig_triangle = region
    return artist


def _square(axis: Axes, x: float, y: float, value: float, color: object, _format: str):
    side = _cell_side() * math.sqrt(abs(value))
    artist = Rectangle(
        (x - side / 2.0, y - side / 2.0),
        side,
        side,
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


def _circle(axis: Axes, x: float, y: float, value: float, color: object, _format: str):
    artist = Circle(
        (x, y),
        _cell_side() / 2.0 * math.sqrt(abs(value)),
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


def _ellipse(axis: Axes, x: float, y: float, value: float, color: object, _format: str):
    major = _cell_side()
    minor = max(0.025, major * math.sqrt((1.0 - abs(value)) / (1.0 + abs(value))))
    artist = Ellipse(
        (x, y),
        width=major,
        height=minor,
        angle=45.0 if value >= 0.0 else -45.0,
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


def _number(axis: Axes, x: float, y: float, value: float, color: object, number_format: str):
    label = f"{value * 100:.0f}%" if number_format == "percent" else f"{value:.2f}"
    return axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        color=color,
        fontsize=mpl.rcParams["font.size"] * 0.80,
        zorder=3,
    )


def _shade(axis: Axes, x: float, y: float, value: float, color: object, _format: str):
    side = _cell_side()
    artist = Rectangle(
        (x - side / 2.0, y - side / 2.0),
        side,
        side,
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        hatch="///" if value >= 0.0 else "\\\\\\",
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


def _color(axis: Axes, x: float, y: float, _value: float, color: object, _format: str):
    side = _cell_side()
    artist = Rectangle(
        (x - side / 2.0, y - side / 2.0),
        side,
        side,
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


def _pie(axis: Axes, x: float, y: float, value: float, color: object, _format: str):
    radius = _cell_side() / 2.0
    axis.add_patch(
        Circle(
            (x, y),
            radius,
            facecolor=mantel_visual_color("background"),
            edgecolor=mantel_visual_color("missing"),
            linewidth=FILL_EDGE_PT,
            zorder=1.8,
        )
    )
    sweep = 360.0 * abs(value)
    theta1, theta2 = (90.0 - sweep, 90.0) if value < 0.0 else (90.0, 90.0 + sweep)
    artist = Wedge(
        (x, y),
        radius,
        theta1,
        theta2,
        facecolor=color,
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=2,
    )
    axis.add_patch(artist)
    return artist


GlyphPrimitive = Callable[[Axes, float, float, float, object, str], object]
GLYPH_PRIMITIVES: Mapping[str, GlyphPrimitive] = {
    "circle": _circle,
    "square": _square,
    "ellipse": _ellipse,
    "number": _number,
    "shade": _shade,
    "color": _color,
    "pie": _pie,
}


def draw_missing_glyph(
    axis: Axes,
    x: float,
    y: float,
    *,
    row: int,
    column: int,
    region: str,
):
    artist = axis.text(
        x,
        y,
        "×",
        ha="center",
        va="center",
        color=mantel_visual_color("missing"),
        fontsize=mpl.rcParams["font.size"] * 0.88,
        zorder=3,
    )
    return _tag(
        artist,
        method="missing",
        row=row,
        column=column,
        value=float("nan"),
        region=region,
    )


def draw_glyph(
    axis: Axes,
    method: str,
    x: float,
    y: float,
    value: float,
    *,
    color: object,
    row: int,
    column: int,
    region: str,
    number_format: str = "decimal",
):
    """Draw one cell-local primitive without knowing matrix masks or ordering."""
    if not math.isfinite(value):
        return draw_missing_glyph(axis, x, y, row=row, column=column, region=region)
    try:
        primitive = GLYPH_PRIMITIVES[method]
    except KeyError as exc:
        raise ValueError(f"unknown correlation glyph method: {method!r}") from exc
    artist = primitive(axis, x, y, value, color, number_format)
    return _tag(
        artist,
        method=method,
        row=row,
        column=column,
        value=value,
        region=region,
    )


def render_glyph_layer(
    axis: Axes,
    data: MantelData,
    cells: Sequence[object],
    spec: GlyphSpec,
    geometry: MantelGeometry,
    *,
    cmap: mpl.colors.Colormap,
    norm: Normalize,
    visible: set[tuple[int, int]],
) -> tuple[object, ...]:
    """Render one glyph primitive over one structural matrix region."""
    rendered: list[object] = []
    for cell in cells:
        row, column, region = cell.row, cell.column, cell.region
        if (row, column) not in visible:
            continue
        if spec.region != "full" and region != spec.region:
            continue
        value = float(data.correlation_matrix[row, column])
        x, y = cell_center(
            geometry.bounds,
            row,
            column,
            matrix_type=geometry.matrix_type,
        )
        color = cmap(norm(value)) if np.isfinite(value) else mantel_visual_color("missing")
        rendered.append(
            draw_glyph(
                axis,
                spec.method,
                x,
                y,
                value,
                color=color,
                row=row,
                column=column,
                region=region,
                number_format=spec.number_format,
            )
        )
    return tuple(rendered)


__all__ = ["GLYPH_PRIMITIVES", "draw_glyph", "render_glyph_layer"]
