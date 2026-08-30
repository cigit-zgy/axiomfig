"""Vector-native corrplot-style correlation glyph grammars."""

from __future__ import annotations

import math
from collections.abc import Mapping

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Ellipse, Rectangle, Wedge

from axiomfig.style import FILL_EDGE_PT, MAIN_STROKE_PT, mantel_plot_contract


def _cell_side() -> float:
    matrix = mantel_plot_contract()["matrix"]
    assert isinstance(matrix, Mapping)
    return float(matrix["maximum_cell_side"])


def _tag(artist, *, method: str, row: int, column: int, value: float, triangle: str):
    artist.set_gid("axiomfig-mantel-glyph")
    artist._axiomfig_method = method
    artist._axiomfig_row = row
    artist._axiomfig_column = column
    artist._axiomfig_value = value
    artist._axiomfig_triangle = triangle
    return artist


def _signed_color(cmap: mpl.colors.Colormap, norm: Normalize, value: float):
    return cmap(norm(value))


def draw_missing_glyph(
    axis: Axes,
    x: float,
    y: float,
    *,
    row: int,
    column: int,
    triangle: str,
):
    artist = axis.text(
        x,
        y,
        "×",
        ha="center",
        va="center",
        color="#777777",
        fontsize=mpl.rcParams["font.size"] * 0.88,
        zorder=3,
    )
    return _tag(
        artist,
        method="missing",
        row=row,
        column=column,
        value=float("nan"),
        triangle=triangle,
    )


def draw_glyph(
    axis: Axes,
    method: str,
    x: float,
    y: float,
    value: float,
    *,
    cmap: mpl.colors.Colormap,
    norm: Normalize,
    row: int,
    column: int,
    triangle: str,
    number_format: str = "decimal",
):
    """Draw one correlation glyph and return its primary traceable artist."""
    if not math.isfinite(value):
        return draw_missing_glyph(
            axis,
            x,
            y,
            row=row,
            column=column,
            triangle=triangle,
        )
    magnitude = abs(value)
    color = _signed_color(cmap, norm, value)
    cell_side = _cell_side()
    if method == "square":
        side = cell_side * math.sqrt(magnitude)
        artist = Rectangle(
            (x - side / 2.0, y - side / 2.0),
            side,
            side,
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
    elif method == "circle":
        artist = Circle(
            (x, y),
            cell_side / 2.0 * math.sqrt(magnitude),
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
    elif method == "ellipse":
        major = cell_side
        minor = max(0.025, major * math.sqrt((1.0 - magnitude) / (1.0 + magnitude)))
        artist = Ellipse(
            (x, y),
            width=major,
            height=minor,
            angle=45.0 if value >= 0.0 else -45.0,
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
    elif method == "number":
        label = f"{value * 100:.0f}%" if number_format == "percent" else f"{value:.2f}"
        artist = axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            color=color,
            fontsize=mpl.rcParams["font.size"] * 0.80,
            zorder=3,
        )
    elif method == "shade":
        artist = Rectangle(
            (x - cell_side / 2.0, y - cell_side / 2.0),
            cell_side,
            cell_side,
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            hatch="///" if value >= 0.0 else "\\\\\\",
            zorder=2,
        )
    elif method == "color":
        artist = Rectangle(
            (x - cell_side / 2.0, y - cell_side / 2.0),
            cell_side,
            cell_side,
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
    elif method == "pie":
        outline = Circle(
            (x, y),
            cell_side / 2.0,
            facecolor="white",
            edgecolor="#777777",
            linewidth=FILL_EDGE_PT,
            zorder=1.8,
        )
        axis.add_patch(outline)
        sweep = 360.0 * magnitude
        theta1, theta2 = (90.0 - sweep, 90.0) if value < 0.0 else (90.0, 90.0 + sweep)
        artist = Wedge(
            (x, y),
            cell_side / 2.0,
            theta1,
            theta2,
            facecolor=color,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
    else:
        raise ValueError(f"unknown correlation glyph method: {method!r}")
    if hasattr(axis, "add_patch") and isinstance(artist, (Rectangle, Circle, Ellipse, Wedge)):
        axis.add_patch(artist)
    return _tag(
        artist,
        method=method,
        row=row,
        column=column,
        value=value,
        triangle=triangle,
    )


def draw_confidence_interval(
    axis: Axes,
    mode: str,
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
):
    """Draw one precomputed correlation interval using vector artists only."""
    edge_lower = _signed_color(cmap, norm, lower)
    edge_upper = _signed_color(cmap, norm, upper)
    estimate_color = _signed_color(cmap, norm, estimate)
    cell_side = _cell_side()
    if mode == "square":
        outer = cell_side * math.sqrt(max(abs(lower), abs(upper)))
        artist = Rectangle(
            (x - outer / 2.0, y - outer / 2.0),
            outer,
            outer,
            facecolor="none",
            edgecolor=edge_upper,
            linewidth=MAIN_STROKE_PT,
            zorder=2,
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
                zorder=2.1,
            )
        )
    elif mode == "circle":
        outer = cell_side / 2.0 * math.sqrt(max(abs(lower), abs(upper)))
        artist = Circle(
            (x, y),
            outer,
            facecolor="none",
            edgecolor=edge_upper,
            linewidth=MAIN_STROKE_PT,
            zorder=2,
        )
        inner = cell_side / 2.0 * math.sqrt(min(abs(lower), abs(upper)))
        axis.add_patch(
            Circle(
                (x, y),
                inner,
                facecolor="none",
                edgecolor=edge_lower,
                linewidth=FILL_EDGE_PT,
                zorder=2.1,
            )
        )
    elif mode == "rect":
        low_y = y + 0.40 * lower
        high_y = y + 0.40 * upper
        artist = Rectangle(
            (x - 0.20, low_y),
            0.40,
            max(high_y - low_y, 0.006),
            facecolor=(*estimate_color[:3], 0.16),
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=2,
        )
        for value, color in ((lower, edge_lower), (estimate, estimate_color), (upper, edge_upper)):
            line_y = y + 0.40 * value
            axis.plot(
                [x - 0.24, x + 0.24],
                [line_y, line_y],
                color=color,
                linewidth=MAIN_STROKE_PT,
                zorder=2.2,
            )
    else:
        raise ValueError(f"unknown CI mode: {mode!r}")
    axis.add_patch(artist)
    center = Circle(
        (x, y),
        0.035,
        facecolor=estimate_color,
        edgecolor="black",
        linewidth=FILL_EDGE_PT,
        zorder=2.4,
    )
    axis.add_patch(center)
    artist.set_gid("axiomfig-mantel-confidence-interval")
    artist._axiomfig_ci_mode = mode
    artist._axiomfig_row = row
    artist._axiomfig_column = column
    return artist


__all__ = ["draw_confidence_interval", "draw_glyph"]
