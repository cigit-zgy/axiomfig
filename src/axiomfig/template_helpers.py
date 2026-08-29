from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.ticker import AutoMinorLocator
from matplotlib.transforms import ScaledTranslation

from axiomfig.contracts import FILLED_TICK_PARAMS, OPEN_TICK_PARAMS, STROKE_WIDTH_PT
from axiomfig.typography import font_for_language


def apply_axis_contract(axis: Axes, surface: Literal["open", "filled"] = "open") -> None:
    """Apply deterministic ticks for an open or filled plotting surface."""
    try:
        policy = {"open": OPEN_TICK_PARAMS, "filled": FILLED_TICK_PARAMS}[surface]
    except KeyError as exc:
        raise ValueError("surface must be 'open' or 'filled'") from exc

    for coordinate_axis in (axis.xaxis, axis.yaxis):
        if coordinate_axis.get_scale() == "linear":
            coordinate_axis.set_minor_locator(AutoMinorLocator(2))
    axis.tick_params(axis="both", which="major", direction=policy["major"])
    axis.tick_params(axis="both", which="minor", direction=policy["minor"])


def add_panel_labels(axes: Iterable[Axes], gap_pt: float = 2.0) -> None:
    """Place sequential panel labels at a uniform physical offset above each axes."""
    for index, axis in enumerate(axes):
        offset = ScaledTranslation(0.0, gap_pt / 72.0, axis.figure.dpi_scale_trans)
        transform = axis.transAxes + offset
        axis.text(
            0.0,
            1.0,
            f"({chr(ord('a') + index)})",
            transform=transform,
            ha="left",
            va="bottom",
            fontweight="bold",
            clip_on=False,
        )


def place_legend_above(axis: Axes, gap_pt: float = 2.0) -> Legend | None:
    """Place a frameless legend above an axes, measured before choosing its columns."""
    handles, labels = axis.get_legend_handles_labels()
    if not handles:
        return None

    figure = axis.figure
    figure.canvas.draw()
    transform = axis.transAxes + ScaledTranslation(0.0, gap_pt / 72.0, figure.dpi_scale_trans)
    legend: Legend | None = None
    for ncol in range(len(handles), 0, -1):
        legend = axis.legend(
            handles,
            labels,
            ncol=ncol,
            loc="lower right",
            bbox_to_anchor=(1.0, 1.0),
            bbox_transform=transform,
            frameon=False,
            borderaxespad=0.0,
        )
        figure.canvas.draw()
        if legend.get_window_extent(figure.canvas.get_renderer()).width <= axis.bbox.width:
            break
    if legend is None:  # pragma: no cover - non-empty handles always enter the loop.
        raise RuntimeError("legend creation did not produce a legend")
    legend_bbox = legend.get_window_extent(figure.canvas.get_renderer())
    overflow = legend_bbox.y1 - figure.bbox.y1
    if overflow > 0:
        top = figure.subplotpars.top - overflow / figure.bbox.height
        if top <= figure.subplotpars.bottom:
            raise ValueError("legend cannot fit above the axes within the figure bounds")
        figure.subplots_adjust(top=top)
        figure.canvas.draw()
    final_bbox = legend.get_window_extent(figure.canvas.get_renderer())
    if final_bbox.y1 > figure.bbox.y1 + 1e-6:
        raise ValueError("legend cannot fit above the axes within the figure bounds")
    return legend


def _reserve_bar_label_headroom(axis: Axes, containers: list[BarContainer]) -> None:
    patches = [patch for container in containers for patch in container.patches]
    if not patches:
        return
    orientation = containers[0].orientation
    if orientation == "horizontal":
        endpoints = [patch.get_x() + patch.get_width() for patch in patches]
        lower, upper = axis.get_xlim()
        span = max(abs(upper - lower), max(abs(value) for value in endpoints), 1.0)
        padding = span * 0.05
        axis.set_xlim(min(lower, min(endpoints) - padding), max(upper, max(endpoints) + padding))
    else:
        endpoints = [patch.get_y() + patch.get_height() for patch in patches]
        lower, upper = axis.get_ylim()
        span = max(abs(upper - lower), max(abs(value) for value in endpoints), 1.0)
        padding = span * 0.05
        axis.set_ylim(min(lower, min(endpoints) - padding), max(upper, max(endpoints) + padding))


def add_bar_value_labels(axis: Axes, containers: Iterable[BarContainer], decimals: int = 2) -> None:
    """Style bars and add fixed-precision, padded value labels with headroom."""
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    bar_containers = list(containers)
    _reserve_bar_label_headroom(axis, bar_containers)
    for container in bar_containers:
        for patch in container.patches:
            patch.set_edgecolor("black")
            patch.set_linewidth(STROKE_WIDTH_PT)
        labels = [f"{value:.{decimals}f}" for value in container.datavalues]
        axis.bar_label(container, labels=labels, padding=2.0)


def apply_scatter_contract(collection: PathCollection) -> None:
    """Give scatter markers the shared black, 0.6 pt edge treatment."""
    collection.set_edgecolor("black")
    collection.set_linewidth(STROKE_WIDTH_PT)


def add_language_text(
    axis: Axes,
    x: float,
    y: float,
    text: str,
    language: str,
    mode: str = "sans",
    **kwargs: object,
) -> None:
    axis.text(x, y, text, fontproperties=font_for_language(language, mode=mode), **kwargs)


def close_secondary_spines(figure: Figure) -> Figure:
    for axis in figure.axes:
        axis.tick_params(which="both", top=True, right=True)
    return figure
