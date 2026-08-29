from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import matplotlib as mpl
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.colorbar import Colorbar
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.gridspec import SubplotSpec
from matplotlib.legend import Legend
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from matplotlib.transforms import Bbox, ScaledTranslation

from axiomfig.config import load_contracts
from axiomfig.contracts import MAIN_STROKE_PT, nice_linear_axis, tick_lengths
from axiomfig.typography import font_for_language

PANEL_LABEL_GID = "axiomfig-panel-label"


def apply_single_panel_layout(figure: Figure) -> None:
    margins = load_contracts().style["layout"]["single_panel"]["margins"]
    figure.subplots_adjust(**{key: float(value) for key, value in margins.items()})


def apply_output_margin(figure: Figure) -> None:
    """Fit visible artists to physical padding while preserving the page size."""
    contract = load_contracts().style["output"]
    mode = str(contract["margin_mode"])
    if mode == "normal":
        return
    padding_px = float(contract["padding_pt"]) * figure.dpi / 72.0
    tolerance_px = 0.25
    for _ in range(8):
        refresh_panel_labels(figure)
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        tight = figure.get_tightbbox(renderer).transformed(figure.dpi_scale_trans)
        width, height = figure.bbox.width, figure.bbox.height
        delta_left = (padding_px - tight.x0) / width
        delta_right = (tight.x1 - (width - padding_px)) / width
        delta_bottom = (padding_px - tight.y0) / height
        delta_top = (tight.y1 - (height - padding_px)) / height
        if (
            max(
                abs(delta_left * width),
                abs(delta_right * width),
                abs(delta_bottom * height),
                abs(delta_top * height),
            )
            <= tolerance_px
        ):
            break
        subplotpars = figure.subplotpars
        left = max(0.01, subplotpars.left + delta_left)
        right = min(0.99, subplotpars.right - delta_right)
        bottom = max(0.01, subplotpars.bottom + delta_bottom)
        top = min(0.99, subplotpars.top - delta_top)
        if left >= right or bottom >= top:
            raise ValueError("output padding cannot fit visible artists on the physical page")
        figure.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    refresh_panel_labels(figure)


def apply_axis_contract(axis: Axes, surface: Literal["open", "filled"] = "open") -> None:
    contracts = load_contracts()
    if surface not in {"open", "filled"}:
        raise ValueError("surface must be 'open' or 'filled'")
    policy = contracts.style["ticks"][surface]
    major_length, minor_length = tick_lengths()
    for coordinate_axis in (axis.xaxis, axis.yaxis):
        if coordinate_axis.get_scale() == "linear":
            coordinate_axis.set_minor_locator(AutoMinorLocator(2))
    axis.tick_params(
        axis="both",
        which="major",
        direction=str(policy["major"]["direction"]),
        length=major_length,
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
        length=minor_length,
        width=MAIN_STROKE_PT,
        top=False,
        right=False,
    )


def apply_categorical_axis(axis: Axes, coordinate: Literal["x", "y"] = "x") -> None:
    axis.tick_params(axis=coordinate, which="both", length=0.0)


def apply_colorbar_contract(colorbar: Colorbar) -> None:
    policy = load_contracts().style["ticks"]["filled"]
    major_length, minor_length = tick_lengths()
    axis = colorbar.ax
    if colorbar.orientation == "vertical":
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


def outer_panel_bbox(axis: Axes) -> Bbox:
    """Return the top-level GridSpec footprint owned by an axes."""
    try:
        spec = axis.get_subplotspec().get_topmost_subplotspec()
    except AttributeError:
        return axis.get_position()
    return spec.get_position(axis.figure)


def add_colorbar_panel_axes(figure: Figure, outer_spec: SubplotSpec) -> tuple[Axes, Axes]:
    """Create data and colorbar axes inside one immutable outer panel footprint."""
    layout = load_contracts().style["layout"]["multi_panel"]
    colorbar_ratio = float(layout["colorbar_width_ratio"])
    gap_ratio = float(layout["colorbar_gap"])
    inner = outer_spec.subgridspec(
        1,
        3,
        width_ratios=(1.0 - colorbar_ratio - gap_ratio, gap_ratio, colorbar_ratio),
        wspace=0.0,
    )
    return figure.add_subplot(inner[0, 0]), figure.add_subplot(inner[0, 2])


def add_panel_labels(axes: Iterable[Axes]) -> None:
    contract = load_contracts().style["panel"]
    for index, axis in enumerate(axes):
        footprint = outer_panel_bbox(axis)
        offset = ScaledTranslation(
            float(contract["left_offset_pt"]) / 72.0,
            float(contract["top_offset_pt"]) / 72.0,
            axis.figure.dpi_scale_trans,
        )
        label = axis.figure.text(
            footprint.x0,
            footprint.y1,
            str(contract["format"]).format(letter=chr(ord("a") + index)),
            transform=axis.figure.transFigure + offset,
            ha="left",
            va="bottom",
            fontsize=float(contract["font_size_pt"]),
            fontweight=str(contract["font_weight"]),
            clip_on=False,
        )
        label.set_gid(PANEL_LABEL_GID)
        label.__dict__["_axiomfig_panel_axis"] = axis


def refresh_panel_labels(figure: Figure) -> None:
    """Re-anchor panel labels after any change to subplot geometry."""
    for label in figure.texts:
        if label.get_gid() != PANEL_LABEL_GID:
            continue
        axis = getattr(label, "_axiomfig_panel_axis", None)
        if axis is None:
            continue
        footprint = outer_panel_bbox(axis)
        label.set_position((footprint.x0, footprint.y1))


def _panel_collision(axis: Axes, legend: Legend) -> bool:
    renderer = axis.figure.canvas.get_renderer()
    legend_bbox = legend.get_window_extent(renderer)
    return any(
        legend_bbox.overlaps(text.get_window_extent(renderer))
        for text in axis.figure.texts
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
        0.0, float(contract["top_gap_pt"]) / 72.0, figure.dpi_scale_trans
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
        if (
            bbox.x0 >= figure.bbox.x0 - tolerance
            and bbox.x1 <= figure.bbox.x1 + tolerance
            and not _panel_collision(axis, legend)
        ):
            break
    else:  # pragma: no cover - the loop always has at least one candidate.
        legend = None
    if legend is None:
        raise ValueError("legend cannot fit above the axes")
    bbox = legend.get_window_extent(figure.canvas.get_renderer())
    if bbox.x0 < figure.bbox.x0 - tolerance or bbox.x1 > figure.bbox.x1 + tolerance:
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


def _stroke_width(token: object) -> float:
    stroke = load_contracts().style["stroke"]
    keys = {"main_stroke": "main_stroke_pt", "fill_edge": "fill_edge_pt"}
    try:
        return float(stroke[keys[str(token)]])
    except KeyError as error:
        raise ValueError(f"unknown stroke token: {token}") from error


def add_bar_value_labels(axis: Axes, containers: Iterable[BarContainer], decimals: int = 2) -> None:
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    selected = list(containers)
    _reserve_bar_label_headroom(axis, selected)
    contract = load_contracts().style["plots"]["bar"]
    for container in selected:
        for patch in container.patches:
            patch.set_alpha(None)
            patch.set_facecolor(_face_rgba(patch.get_facecolor(), float(contract["alpha"])))
            patch.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
            patch.set_linewidth(_stroke_width(contract["edge_width_token"]))
        axis.bar_label(
            container,
            labels=[f"{value:.{decimals}f}" for value in container.datavalues],
            padding=2.0,
        )


def _face_rgba(color: object, alpha: float) -> tuple[float, float, float, float]:
    red, green, blue, _ = mcolors.to_rgba(color)
    return red, green, blue, alpha


def _collection_face_alpha(collection: object, alpha: float) -> None:
    facecolors = collection.get_facecolors()  # type: ignore[attr-defined]
    if len(facecolors):
        collection.set_facecolors(  # type: ignore[attr-defined]
            [_face_rgba(color, alpha) for color in facecolors]
        )
    collection.set_alpha(None)  # type: ignore[attr-defined]


def apply_scatter_contract(collection: PathCollection) -> None:
    contract = load_contracts().style["plots"]["scatter"]
    _collection_face_alpha(collection, float(contract["alpha"]))
    collection.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
    collection.set_linewidth(_stroke_width(contract["edge_width_token"]))
    collection.set_sizes([float(contract["marker_size_pt2"])])


def line_marker_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["line_marker"]
    return {
        "marker": str(contract["marker"]),
        "markersize": float(contract["marker_size_pt"]),
        "markeredgecolor": str(contract["edge_color"]),
        "markeredgewidth": _stroke_width(contract["edge_width_token"]),
    }


def confidence_interval_kwargs(color: object | None = None) -> dict[str, object]:
    contract = load_contracts().style["plots"]["confidence_interval"]
    selected_color = color or mpl.rcParams["axes.prop_cycle"].by_key()["color"][0]
    return {
        "facecolor": _face_rgba(selected_color, float(contract["alpha"])),
        "edgecolor": mcolors.to_rgba(str(contract["edge_color"]), 1.0),
        "linewidth": _stroke_width(contract["edge_width_token"]),
    }


def _line_style(value: object) -> object:
    aliases: dict[str, object] = {
        "solid": "-",
        "dashdot": "-.",
        "dotted": ":",
    }
    if str(value) == "long-dash":
        pattern = load_contracts().style["series"]["long_dash_pattern"]
        return 0, tuple(float(item) for item in pattern)
    try:
        return aliases[str(value)]
    except KeyError as error:
        raise ValueError(f"unknown line style token: {value}") from error


def series_style(index: int, *, include_marker: bool = True) -> dict[str, object]:
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("series index must be a nonnegative integer")
    contract = load_contracts().style["series"]
    colors = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    line_styles = contract["line_styles"]
    markers = contract["markers"]
    result: dict[str, object] = {
        "color": colors[index % len(colors)],
        "linestyle": _line_style(line_styles[index % len(line_styles)]),
    }
    if include_marker:
        result["marker"] = str(markers[index % len(markers)])
    return result


def reference_line_kwargs() -> dict[str, object]:
    contract = load_contracts().style["series"]
    return {
        "color": "black",
        "linestyle": _line_style(contract["reference_line_style"]),
        "linewidth": MAIN_STROKE_PT,
    }


def errorbar_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["errorbar"]
    return {
        "marker": str(contract["marker"]),
        "markersize": float(contract["marker_size_pt"]),
        "markeredgecolor": str(contract["edge_color"]),
        "markeredgewidth": _stroke_width(contract["edge_width_token"]),
        "capsize": float(contract["cap_size_pt"]),
        "elinewidth": MAIN_STROKE_PT,
        "capthick": MAIN_STROKE_PT,
    }


def apply_boxplot_contract(parts: dict[str, object], *, combined: bool = False) -> None:
    contract = load_contracts().style["plots"]["boxplot"]
    for box in parts["boxes"]:  # type: ignore[index]
        box.set_alpha(None)
        alpha = 1.0 if combined else float(contract["alpha"])
        box.set_facecolor(_face_rgba(box.get_facecolor(), alpha))
        box.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
        box.set_linewidth(_stroke_width(contract["edge_width_token"]))
    for key in ("whiskers", "caps", "medians"):
        for artist in parts[key]:  # type: ignore[index]
            artist.set_color(str(contract["edge_color"]))
            artist.set_linewidth(MAIN_STROKE_PT)


def apply_violin_contract(parts: dict[str, object], *, combined: bool = False) -> None:
    contract = load_contracts().style["plots"]["violin"]
    alpha_token = "combined_alpha" if combined else "alpha"
    for body in parts["bodies"]:  # type: ignore[index]
        _collection_face_alpha(body, float(contract[alpha_token]))
        body.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
        body.set_linewidth(_stroke_width(contract["edge_width_token"]))


def histogram_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["histogram"]
    return {
        "color": _face_rgba(
            mpl.rcParams["axes.prop_cycle"].by_key()["color"][0],
            float(contract["alpha"]),
        ),
        "edgecolor": mcolors.to_rgba(str(contract["edge_color"]), 1.0),
        "linewidth": _stroke_width(contract["edge_width_token"]),
    }


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
