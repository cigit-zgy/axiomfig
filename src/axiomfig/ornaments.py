"""Deterministic placement for legends, panel labels, and colorbars."""

from __future__ import annotations

from collections.abc import Iterable

from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.legend import Legend
from matplotlib.transforms import ScaledTranslation

from axiomfig.config import load_contracts
from axiomfig.layout import get_figure_layout, register_figure_ornament
from axiomfig.style import MAIN_STROKE_PT, tick_lengths

PANEL_LABEL_GID = "axiomfig-panel-label"


def apply_colorbar_contract(colorbar: Colorbar) -> None:
    policy = load_contracts().style["ticks"]["filled"]
    normal_major_total, minor_length = tick_lengths()
    major_length = normal_major_total / 2.0
    axis = colorbar.ax
    if colorbar.orientation == "vertical":
        from matplotlib.ticker import AutoMinorLocator

        contract = load_contracts().style["colorbar"]["vertical"]
        axis.yaxis.set_ticks_position(str(contract["tick_side"]))
        axis.yaxis.set_label_position(str(contract["label_side"]))
        axis.yaxis.set_minor_locator(AutoMinorLocator(2))
        axis.tick_params(
            axis="y",
            which="major",
            direction=str(policy["major"]["direction"]),
            length=major_length,
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
            length=minor_length,
            width=MAIN_STROKE_PT,
            left=False,
            right=True,
        )
    else:
        from matplotlib.ticker import AutoMinorLocator

        axis.xaxis.set_minor_locator(AutoMinorLocator(2))
        axis.tick_params(
            axis="x",
            which="major",
            direction=str(policy["major"]["direction"]),
            length=major_length,
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
            length=minor_length,
            width=MAIN_STROKE_PT,
            bottom=True,
            top=False,
        )


def _legend_kwargs(ncol: int) -> dict[str, object]:
    contract = load_contracts().style["legend"]
    return {
        "ncol": ncol,
        "frameon": False,
        "handlelength": float(contract["handlelength"]),
        "columnspacing": float(contract["columnspacing"]),
        "handletextpad": float(contract["handletextpad"]),
        "labelspacing": float(contract["labelspacing"]),
        "borderpad": float(contract["borderpad"]),
        "borderaxespad": float(contract["borderaxespad"]),
    }


def requested_legend_height_pt(axis: Axes) -> float:
    handles, labels = axis.get_legend_handles_labels()
    if len(handles) <= 1:
        return 0.0
    figure = axis.figure
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    layout = get_figure_layout(figure)
    label_right = figure.bbox.x0
    if layout is not None and layout.panel_labels:
        panel = layout.panel_for_axis(axis)
        assert panel is not None
        contract = load_contracts().style["panel"]
        properties = FontProperties(
            size=float(contract["font_size_pt"]), weight=str(contract["font_weight"])
        )
        text = str(contract["format"]).format(letter=chr(ord("a") + panel.index))
        label_width = renderer.get_text_width_height_descent(text, properties, ismath=False)[0]
        offset = float(contract["left_offset_pt"]) * figure.dpi / 72.0
        label_right = axis.bbox.x0 + offset + label_width
    for ncol in range(len(handles), 0, -1):
        probe = axis.legend(handles, labels, loc="lower right", **_legend_kwargs(ncol))
        figure.canvas.draw()
        bbox = probe.get_window_extent(renderer)
        fits = bbox.x0 >= label_right - 0.5 and bbox.x1 <= figure.bbox.x1 + 0.5
        height = bbox.height
        probe.remove()
        if fits:
            return height * 72.0 / figure.dpi
    raise ValueError("legend cannot fit above the axes")


def _label_collision(figure: Figure, legend: Legend) -> bool:
    renderer = figure.canvas.get_renderer()
    legend_bbox = legend.get_window_extent(renderer)
    return any(
        legend_bbox.overlaps(text.get_window_extent(renderer))
        for text in figure.texts
        if text.get_gid() == PANEL_LABEL_GID
    )


def _data_collision(figure: Figure, owner: Axes, legend: Legend) -> bool:
    legend_bbox = legend.get_window_extent(figure.canvas.get_renderer())
    return any(legend_bbox.overlaps(axis.bbox) for axis in figure.axes if axis is not owner)


def _place_legend(axis: Axes) -> Legend | None:
    handles, labels = axis.get_legend_handles_labels()
    existing = axis.get_legend()
    if existing is not None:
        existing.remove()
    if len(handles) <= 1:
        return None
    contract = load_contracts().style["legend"]
    figure = axis.figure
    transform = axis.transAxes + ScaledTranslation(
        0.0, float(contract["top_gap_pt"]) / 72.0, figure.dpi_scale_trans
    )
    registered_layout = get_figure_layout(figure)
    tolerance = 0.5
    selected: Legend | None = None
    for ncol in range(len(handles), 0, -1):
        legend = axis.legend(
            handles,
            labels,
            loc="lower right",
            bbox_to_anchor=(1.0, 1.0),
            bbox_transform=transform,
            **_legend_kwargs(ncol),
        )
        legend.set_in_layout(False)
        figure.canvas.draw()
        bbox = legend.get_window_extent(figure.canvas.get_renderer())
        if (
            bbox.x0 >= figure.bbox.x0 - tolerance
            and bbox.x1 <= figure.bbox.x1 + tolerance
            and not _label_collision(figure, legend)
            and not _data_collision(figure, axis, legend)
        ):
            selected = legend
            break
        legend.remove()
    if selected is None:
        raise ValueError("legend cannot fit above the axes")
    bbox = selected.get_window_extent(figure.canvas.get_renderer())
    overflow = bbox.y1 - figure.bbox.y1
    if overflow > tolerance and registered_layout is None:
        position = axis.get_position()
        shift = overflow / figure.bbox.height
        if position.y0 - shift <= 0.0:
            selected.remove()
            raise ValueError("legend cannot fit above the axes")
        axis.set_position((position.x0, position.y0 - shift, position.width, position.height))
        figure.canvas.draw()
        bbox = selected.get_window_extent(figure.canvas.get_renderer())
    if bbox.y1 > figure.bbox.y1 + tolerance:
        selected.remove()
        raise ValueError("legend cannot fit above the axes")
    return selected


def request_legend(axis: Axes) -> Legend | None:
    handles, _labels = axis.get_legend_handles_labels()
    existing = axis.get_legend()
    if len(handles) <= 1:
        if existing is not None:
            existing.remove()
        return None
    layout = get_figure_layout(axis.figure)
    if layout is None:
        return _place_legend(axis)
    if axis not in layout.legend_requests:
        layout.legend_requests.append(axis)
    return None


def add_panel_labels(target: Figure | Iterable[Axes]) -> None:
    if isinstance(target, Figure):
        figure = target
        layout = get_figure_layout(figure)
        if layout is None or not layout.panel_labels:
            return
        axes = [panel.primary_axes for panel in layout.panels]
    else:
        axes = list(target)
        figure = axes[0].figure if axes else None
        layout = get_figure_layout(figure) if figure is not None else None
    if figure is None:
        return
    contract = load_contracts().style["panel"]
    for index, axis in enumerate(axes):
        if axis is None:
            continue
        frame = axis.get_position()
        offset = ScaledTranslation(
            float(contract["left_offset_pt"]) / 72.0,
            float(contract["top_offset_pt"]) / 72.0,
            figure.dpi_scale_trans,
        )
        label = figure.text(
            frame.x0,
            frame.y1,
            str(contract["format"]).format(letter=chr(ord("a") + index)),
            transform=figure.transFigure + offset,
            ha="left",
            va="bottom",
            fontsize=float(contract["font_size_pt"]),
            fontweight=str(contract["font_weight"]),
            clip_on=False,
        )
        label.set_gid(PANEL_LABEL_GID)
        label.__dict__["_axiomfig_panel_axis"] = axis
        if layout is not None:
            panel = layout.panel_for_axis(axis)
            assert panel is not None
            panel.panel_label = label


def refresh_panel_labels(figure: Figure) -> None:
    for label in figure.texts:
        if label.get_gid() != PANEL_LABEL_GID:
            continue
        axis = getattr(label, "_axiomfig_panel_axis", None)
        if axis is None:
            continue
        frame = axis.get_position()
        label.set_position((frame.x0, frame.y1))


def finalize_ornaments(figure: Figure) -> None:
    layout = get_figure_layout(figure)
    if layout is None:
        return
    stale_legends = tuple(layout.legends)
    layout.figure_ornaments[:] = [
        ornament for ornament in layout.figure_ornaments if ornament not in stale_legends
    ]
    for legend in stale_legends:
        legend.remove()
    layout.legends.clear()
    for panel in layout.panels:
        if panel.panel_label is not None:
            panel.panel_label.remove()
            panel.panel_label = None
    add_panel_labels(figure)
    figure.canvas.draw()
    for axis in layout.legend_requests:
        legend = _place_legend(axis)
        if legend is not None:
            layout.legends.append(legend)
            register_figure_ornament(figure, legend)
    figure.canvas.draw()
