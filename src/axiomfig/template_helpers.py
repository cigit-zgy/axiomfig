from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.colorbar import Colorbar
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from matplotlib.transforms import ScaledTranslation

from axiomfig.config import load_contracts
from axiomfig.contracts import FILL_EDGE_PT, MAIN_STROKE_PT, nice_linear_axis
from axiomfig.typography import font_for_language

PANEL_LABEL_GID = "axiomfig-panel-label"


def apply_single_panel_layout(figure: Figure) -> None:
    margins = load_contracts().style["layout"]["single_panel"]["margins"]
    figure.subplots_adjust(**{key: float(value) for key, value in margins.items()})


def apply_axis_contract(axis: Axes, surface: Literal["open", "filled"] = "open") -> None:
    contracts = load_contracts()
    if surface not in {"open", "filled"}:
        raise ValueError("surface must be 'open' or 'filled'")
    policy = contracts.style["ticks"][surface]
    for coordinate_axis in (axis.xaxis, axis.yaxis):
        if coordinate_axis.get_scale() == "linear":
            coordinate_axis.set_minor_locator(AutoMinorLocator(2))
    axis.tick_params(
        axis="both",
        which="major",
        direction=str(policy["major"]["direction"]),
        length=float(policy["major"]["length_pt"]),
        width=MAIN_STROKE_PT,
        top=False,
        right=False,
        labeltop=False,
        labelright=False,
    )
    axis.tick_params(
        axis="both",
        which="minor",
        direction=str(policy["minor"]["direction"]),
        length=float(policy["minor"]["length_pt"]),
        width=MAIN_STROKE_PT,
        top=False,
        right=False,
    )


def apply_categorical_axis(axis: Axes, coordinate: Literal["x", "y"] = "x") -> None:
    axis.tick_params(axis=coordinate, which="both", length=0.0)


def apply_colorbar_contract(colorbar: Colorbar) -> None:
    policy = load_contracts().style["ticks"]["filled"]
    axis = colorbar.ax
    if colorbar.orientation == "vertical":
        axis.yaxis.set_minor_locator(AutoMinorLocator(2))
        axis.tick_params(
            axis="y",
            which="major",
            direction=str(policy["major"]["direction"]),
            length=float(policy["major"]["length_pt"]),
            width=MAIN_STROKE_PT,
            left=False,
            right=True,
            labelleft=False,
            labelright=True,
        )
        axis.tick_params(
            axis="y",
            which="minor",
            direction=str(policy["minor"]["direction"]),
            length=float(policy["minor"]["length_pt"]),
            width=MAIN_STROKE_PT,
            left=False,
            right=True,
        )
    else:
        axis.xaxis.set_minor_locator(AutoMinorLocator(2))
        axis.tick_params(
            axis="x",
            which="major",
            direction=str(policy["major"]["direction"]),
            length=float(policy["major"]["length_pt"]),
            width=MAIN_STROKE_PT,
            bottom=True,
            top=False,
            labelbottom=True,
            labeltop=False,
        )
        axis.tick_params(
            axis="x",
            which="minor",
            direction=str(policy["minor"]["direction"]),
            length=float(policy["minor"]["length_pt"]),
            width=MAIN_STROKE_PT,
            bottom=True,
            top=False,
        )


def apply_nice_linear_axis(
    axis: Axes, data_min: float, data_max: float, *, coordinate: Literal["x", "y"] = "x"
) -> None:
    result = nice_linear_axis(data_min, data_max)
    coordinate_axis = axis.xaxis if coordinate == "x" else axis.yaxis
    if coordinate_axis.get_scale() != "linear":
        return
    coordinate_axis.set_major_locator(MultipleLocator(result.major_step))
    coordinate_axis.set_minor_locator(MultipleLocator(result.minor_step))
    (axis.set_xlim if coordinate == "x" else axis.set_ylim)(result.lower, result.upper)


def add_panel_labels(axes: Iterable[Axes]) -> None:
    contract = load_contracts().style["panel"]
    for index, axis in enumerate(axes):
        offset = ScaledTranslation(
            float(contract["left_offset_pt"]) / 72.0,
            float(contract["top_offset_pt"]) / 72.0,
            axis.figure.dpi_scale_trans,
        )
        label = axis.text(
            0.0,
            1.0,
            str(contract["format"]).format(letter=chr(ord("a") + index)),
            transform=axis.transAxes + offset,
            ha="left",
            va="bottom",
            fontsize=float(contract["font_size_pt"]),
            fontweight=str(contract["font_weight"]),
            clip_on=False,
        )
        label.set_gid(PANEL_LABEL_GID)


def _panel_collision(axis: Axes, legend: Legend) -> bool:
    renderer = axis.figure.canvas.get_renderer()
    legend_bbox = legend.get_window_extent(renderer)
    return any(
        legend_bbox.overlaps(text.get_window_extent(renderer))
        for text in axis.texts
        if text.get_gid() == PANEL_LABEL_GID
    )


def place_legend_above(axis: Axes) -> Legend | None:
    handles, labels = axis.get_legend_handles_labels()
    existing = axis.get_legend()
    if len(handles) <= 1:
        if existing is not None:
            existing.remove()
        return None

    contract = load_contracts().style["legend"]
    figure = axis.figure
    figure.canvas.draw()
    transform = axis.transAxes + ScaledTranslation(
        0.0, float(contract["gap_pt"]) / 72.0, figure.dpi_scale_trans
    )
    legend: Legend | None = None
    tolerance = 0.5
    for ncol in range(len(handles), 0, -1):
        legend = axis.legend(
            handles,
            labels,
            ncol=ncol,
            loc="lower right",
            bbox_to_anchor=(1.0, 1.0),
            bbox_transform=transform,
            frameon=False,
            handlelength=float(contract["handlelength"]),
            borderaxespad=0.0,
        )
        figure.canvas.draw()
        bbox = legend.get_window_extent(figure.canvas.get_renderer())
        if bbox.width <= axis.bbox.width + tolerance and not _panel_collision(axis, legend):
            break
    else:  # pragma: no cover - the loop always has at least one candidate.
        legend = None
    if legend is None:
        raise ValueError("legend cannot fit above the axes")
    bbox = legend.get_window_extent(figure.canvas.get_renderer())
    if bbox.width > axis.bbox.width + tolerance:
        legend.remove()
        raise ValueError("legend cannot fit above the axes")

    overflow = bbox.y1 - figure.bbox.y1
    if overflow > 0:
        top = figure.subplotpars.top - overflow / figure.bbox.height
        if top <= figure.subplotpars.bottom:
            legend.remove()
            raise ValueError("legend cannot fit above the axes")
        figure.subplots_adjust(top=top)
        figure.canvas.draw()
    bbox = legend.get_window_extent(figure.canvas.get_renderer())
    if (
        bbox.x0 < figure.bbox.x0 - tolerance
        or bbox.x1 > figure.bbox.x1 + tolerance
        or bbox.y1 > figure.bbox.y1 + tolerance
        or _panel_collision(axis, legend)
    ):
        legend.remove()
        raise ValueError("legend cannot fit above the axes")
    return legend


def _reserve_bar_label_headroom(axis: Axes, containers: list[BarContainer]) -> None:
    patches = [patch for container in containers for patch in container.patches]
    if not patches:
        return
    orientation = containers[0].orientation
    endpoints = (
        [patch.get_x() + patch.get_width() for patch in patches]
        if orientation == "horizontal"
        else [patch.get_y() + patch.get_height() for patch in patches]
    )
    lower, upper = axis.get_xlim() if orientation == "horizontal" else axis.get_ylim()
    span = max(abs(upper - lower), max(abs(value) for value in endpoints), 1.0)
    padded = (min(lower, min(endpoints) - span * 0.05), max(upper, max(endpoints) + span * 0.05))
    (axis.set_xlim if orientation == "horizontal" else axis.set_ylim)(*padded)


def add_bar_value_labels(axis: Axes, containers: Iterable[BarContainer], decimals: int = 2) -> None:
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    selected = list(containers)
    _reserve_bar_label_headroom(axis, selected)
    for container in selected:
        for patch in container.patches:
            patch.set_edgecolor("black")
            patch.set_linewidth(FILL_EDGE_PT)
        axis.bar_label(
            container,
            labels=[f"{value:.{decimals}f}" for value in container.datavalues],
            padding=2.0,
        )


def apply_scatter_contract(collection: PathCollection) -> None:
    contract = load_contracts().style["plots"]["scatter"]
    collection.set_edgecolor(str(contract["edge_color"]))
    collection.set_linewidth(FILL_EDGE_PT)
    collection.set_alpha(float(contract["alpha"]))
    collection.set_sizes([float(contract["marker_size_pt2"])])


def apply_violin_contract(parts: dict[str, object]) -> None:
    for body in parts["bodies"]:  # type: ignore[index]
        body.set_edgecolor("black")
        body.set_linewidth(FILL_EDGE_PT)


def add_language_text(
    axis: Axes,
    x: float,
    y: float,
    text: str,
    language: str,
    mode: str = "sans",
    **kwargs: object,
) -> None:
    axis.text(
        x,
        y,
        text,
        fontproperties=font_for_language(language, mode=mode),
        **kwargs,
    )


def apply_contract_context(
    *, geometry: str = "single-column", typography: str = "sans"
) -> mpl.rc_context:
    from axiomfig.config import build_rcparams

    return mpl.rc_context(
        rc=build_rcparams(load_contracts(), geometry=geometry, typography=typography)
    )
