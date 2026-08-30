"""Deterministic physical layout and explicit panel ownership."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.gridspec import GridSpec, SubplotSpec
from matplotlib.transforms import Bbox

from axiomfig.config import load_contracts

if TYPE_CHECKING:
    from matplotlib.legend import Legend

_LAYOUT_KEY = "_axiomfig_figure_layout"


class LayoutConstraintError(ValueError):
    """Raised when physical panel constraints cannot be satisfied."""


@dataclass(frozen=True)
class PanelSpaceAccounting:
    """Physical reservations around one Primary Visual Area, in points."""

    left_pt: float
    right_pt: float
    bottom_pt: float
    top_pt: float
    primary_right_without_aux_pt: float
    colorbar_width_pt: float = 0.0
    colorbar_gap_pt: float = 0.0
    colorbar_right_overhang_pt: float = 0.0


@dataclass(frozen=True)
class PrimaryAreaDiagnostic:
    """Renderer-derived capacity and efficiency for a square scientific area."""

    outer_width_pt: float
    outer_height_pt: float
    actual_side_pt: float
    maximum_side_without_aux_pt: float
    maximum_side_with_aux_pt: float
    primary_area_efficiency: float
    shrinkage_reason: str
    left_pt: float
    right_pt: float
    bottom_pt: float
    top_pt: float
    intrinsic_left_pt: float
    intrinsic_right_pt: float
    intrinsic_bottom_pt: float
    intrinsic_top_pt: float
    unused_horizontal_pt: float
    unused_vertical_pt: float


@dataclass
class PanelFootprint:
    """One equal top-level GridSpec slot and everything owned by that panel."""

    figure: Figure
    index: int
    row: int
    column: int
    spec: SubplotSpec
    primary_axes: Axes | None = None
    auxiliary_axes: list[Axes] = field(default_factory=list)
    artists: list[Artist] = field(default_factory=list)
    panel_label: Artist | None = None
    vertical_colorbar_reference: tuple[Axes, tuple[float, float, float, float]] | None = None
    space_accounting: PanelSpaceAccounting | None = None

    def bbox(self) -> Bbox:
        return self.spec.get_position(self.figure)


@dataclass
class FigureLayout:
    """Small registry for a regular panel grid and its ornaments."""

    figure: Figure
    rows: int
    columns: int
    grid: GridSpec
    panels: list[PanelFootprint]
    panel_labels: bool
    legend_requests: list[Axes] = field(default_factory=list)
    legends: list[Legend] = field(default_factory=list)
    figure_ornaments: list[Artist] = field(default_factory=list)
    post_solve_callbacks: list[Callable[[Figure], None]] = field(default_factory=list)
    solved_size_pt: tuple[float, float] | None = None

    def panel_for_axis(self, axis: Axes) -> PanelFootprint | None:
        for panel in self.panels:
            if axis is panel.primary_axes or axis in panel.auxiliary_axes:
                return panel
        return None


def apply_single_panel_layout(figure: Figure) -> None:
    """Apply the canonical margins for one ordinary panel."""
    margins = load_contracts().style["layout"]["single_panel"]["margins"]
    figure.subplots_adjust(**{key: float(value) for key, value in margins.items()})


def apply_output_margin(figure: Figure) -> None:
    """Fit visible artists to physical padding while preserving the page size."""
    from axiomfig.ornaments import finalize_ornaments, refresh_panel_labels

    if get_figure_layout(figure) is not None:
        solve_panel_layout(figure)
        finalize_ornaments(figure)
        return
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
        legends = [
            legend
            for axis in figure.axes
            if (legend := axis.get_legend()) is not None and legend.get_visible()
        ]
        tight = figure.get_tightbbox(renderer, bbox_extra_artists=legends).transformed(
            figure.dpi_scale_trans
        )
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


def _figure_size_pt(figure: Figure) -> tuple[float, float]:
    return figure.get_figwidth() * 72.0, figure.get_figheight() * 72.0


def _physical_grid_parameters(
    figure: Figure, rows: int, columns: int, *, panel_labels: bool
) -> dict[str, float]:
    style = load_contracts().style
    width_pt, height_pt = _figure_size_pt(figure)
    padding = float(style["output"]["padding_pt"])
    layout = style["layout"]["multi_panel"]
    horizontal_gap = float(layout["horizontal_gap_pt"])
    vertical_gap = float(layout["vertical_gap_pt"])
    left_margin = padding
    top_margin = padding
    del panel_labels
    available_width = width_pt - left_margin - padding - horizontal_gap * (columns - 1)
    available_height = height_pt - padding - top_margin - vertical_gap * (rows - 1)
    if available_width <= 0 or available_height <= 0:
        raise ValueError("physical panel grid does not fit on the requested page")
    cell_width = available_width / columns
    cell_height = available_height / rows
    return {
        "left": left_margin / width_pt,
        "right": 1.0 - padding / width_pt,
        "bottom": padding / height_pt,
        "top": 1.0 - top_margin / height_pt,
        "wspace": 0.0 if columns == 1 else horizontal_gap / cell_width,
        "hspace": 0.0 if rows == 1 else vertical_gap / cell_height,
    }


def create_panel_grid(
    figure: Figure, rows: int, columns: int, *, panel_labels: bool = True
) -> FigureLayout:
    if rows < 1 or columns < 1:
        raise ValueError("panel grid dimensions must be positive")
    if get_figure_layout(figure) is not None:
        raise ValueError("figure already owns a panel layout")
    parameters = _physical_grid_parameters(figure, rows, columns, panel_labels=panel_labels)
    grid = figure.add_gridspec(rows, columns, **parameters)
    panels = [
        PanelFootprint(
            figure=figure,
            index=index,
            row=index // columns,
            column=index % columns,
            spec=grid[index],
        )
        for index in range(rows * columns)
    ]
    layout = FigureLayout(figure, rows, columns, grid, panels, panel_labels)
    figure.__dict__[_LAYOUT_KEY] = layout
    return layout


def get_figure_layout(figure: Figure) -> FigureLayout | None:
    value = figure.__dict__.get(_LAYOUT_KEY)
    return value if isinstance(value, FigureLayout) else None


def invalidate_panel_layout(figure: Figure) -> None:
    layout = get_figure_layout(figure)
    if layout is not None:
        layout.solved_size_pt = None


def register_post_layout_callback(figure: Figure, callback: Callable[[Figure], None]) -> None:
    layout = get_figure_layout(figure)
    if layout is None:
        raise ValueError("post-layout callback requires a registered panel layout")
    if callback not in layout.post_solve_callbacks:
        layout.post_solve_callbacks.append(callback)


def add_panel_axes(
    layout: FigureLayout, index: int, *, colorbar: bool = False
) -> tuple[Axes, Axes | None]:
    panel = layout.panels[index]
    if panel.primary_axes is not None:
        raise ValueError(f"panel {index} already has primary axes")
    if colorbar:
        primary = layout.figure.add_subplot(panel.spec)
        auxiliary = layout.figure.add_subplot(panel.spec)
        panel.auxiliary_axes.append(auxiliary)
    else:
        primary = layout.figure.add_subplot(panel.spec)
        auxiliary = None
    panel.primary_axes = primary
    return primary, auxiliary


def _vertical_colorbar_reference_bbox(panel: PanelFootprint) -> Bbox:
    if panel.primary_axes is None:
        raise LayoutConstraintError("physical Colorbar layout requires a Primary Axes")
    if panel.vertical_colorbar_reference is None:
        return panel.primary_axes.bbox
    primary, (x0, y0, x1, y1) = panel.vertical_colorbar_reference
    lower_left, upper_right = primary.transData.transform(((x0, y0), (x1, y1)))
    return Bbox.from_extents(*lower_left, *upper_right)


def _place_vertical_colorbar(panel: PanelFootprint) -> None:
    if not panel.auxiliary_axes:
        return
    auxiliary = panel.auxiliary_axes[0]
    figure = panel.figure
    reference = _vertical_colorbar_reference_bbox(panel)
    contract = load_contracts().style["colorbar"]["vertical"]
    width_px = float(contract["width_pt"]) * figure.dpi / 72.0
    gap_px = float(contract["gap_pt"]) * figure.dpi / 72.0
    height_px = float(contract["length_fraction"]) * reference.height
    center_y = (reference.y0 + reference.y1) / 2.0
    display = Bbox.from_extents(
        reference.x1 + gap_px,
        center_y - height_px / 2.0,
        reference.x1 + gap_px + width_px,
        center_y + height_px / 2.0,
    )
    footprint = panel.bbox().transformed(figure.transFigure)
    if display.width <= 0.0 or display.height <= 0.0:
        raise LayoutConstraintError("physical Colorbar dimensions must be positive")
    if (
        display.x1 > footprint.x1 + 0.5
        or display.y0 < footprint.y0 - 0.5
        or display.y1 > (footprint.y1 + 0.5)
    ):
        raise LayoutConstraintError(
            "physical panel cannot contain the vertical Colorbar beside its Primary Visual Area"
        )
    auxiliary.set_position(display.transformed(figure.transFigure.inverted()))


def register_vertical_colorbar_layout(
    primary: Axes,
    auxiliary: Axes,
    reference_bounds: tuple[float, float, float, float],
) -> None:
    """Attach one global vertical Colorbar contract to a data-space reference box."""
    layout = get_figure_layout(primary.figure)
    if layout is None:
        raise ValueError("vertical colorbar layout requires a registered panel layout")
    panel = layout.panel_for_axis(primary)
    if panel is None or auxiliary not in panel.auxiliary_axes:
        raise ValueError("vertical colorbar axes is not owned by the primary panel")
    panel.vertical_colorbar_reference = (primary, reference_bounds)
    primary.figure.canvas.draw()
    _place_vertical_colorbar(panel)
    primary.figure.canvas.draw()


def primary_area_diagnostic(primary: Axes) -> PrimaryAreaDiagnostic:
    """Explain the maximum square scientific area within the current panel."""
    figure = primary.figure
    layout = get_figure_layout(figure)
    if layout is None:
        raise ValueError("primary-area diagnostic requires a registered panel layout")
    panel = layout.panel_for_axis(primary)
    if panel is None or panel.primary_axes is not primary:
        raise ValueError("axis is not the registered Primary Axes")
    if panel.vertical_colorbar_reference is None:
        raise ValueError("primary-area diagnostic requires a square reference registration")
    if panel.space_accounting is None:
        raise ValueError("panel layout must be solved before primary-area diagnosis")

    figure.canvas.draw()
    accounting = panel.space_accounting
    footprint = panel.bbox().transformed(figure.transFigure)
    allocation = primary.get_position(original=True).transformed(figure.transFigure)
    reference = _vertical_colorbar_reference_bbox(panel)
    _axis, (x0, y0, x1, y1) = panel.vertical_colorbar_reference
    reference_width = abs(x1 - x0)
    reference_height = abs(y1 - y0)
    x_limits = primary.get_xlim()
    y_limits = primary.get_ylim()
    x_span = abs(x_limits[1] - x_limits[0])
    y_span = abs(y_limits[1] - y_limits[0])
    if min(reference_width, reference_height, x_span, y_span) <= 0.0:
        raise LayoutConstraintError("physical square diagnostic received degenerate data bounds")

    scale = 72.0 / figure.dpi
    available_height_pt = footprint.height * scale - accounting.bottom_pt - accounting.top_pt
    available_width_with_pt = footprint.width * scale - accounting.left_pt - accounting.right_pt
    available_width_without_pt = (
        footprint.width * scale - accounting.left_pt - accounting.primary_right_without_aux_pt
    )
    maximum_with = min(
        available_width_with_pt * reference_width / x_span,
        available_height_pt * reference_height / y_span,
    )
    maximum_without = min(
        available_width_without_pt * reference_width / x_span,
        available_height_pt * reference_height / y_span,
    )
    actual = min(reference.width, reference.height) * scale
    intrinsic_left = max(0.0, reference.x0 - primary.bbox.x0) * scale
    intrinsic_right = max(0.0, primary.bbox.x1 - reference.x1) * scale
    intrinsic_bottom = max(0.0, reference.y0 - primary.bbox.y0) * scale
    intrinsic_top = max(0.0, primary.bbox.y1 - reference.y1) * scale
    if maximum_with <= 0.0:
        raise LayoutConstraintError("physical constraints leave no positive Primary Visual Area")
    efficiency = (actual / maximum_with) ** 2
    penalty = maximum_without - maximum_with
    if penalty <= 0.5:
        reason = "height-limited; the right-side Colorbar strip does not reduce the square side"
    else:
        reason = f"right-side Colorbar strip reduces the width-limited square by {penalty:.3f} pt"
    return PrimaryAreaDiagnostic(
        outer_width_pt=footprint.width * scale,
        outer_height_pt=footprint.height * scale,
        actual_side_pt=actual,
        maximum_side_without_aux_pt=maximum_without,
        maximum_side_with_aux_pt=maximum_with,
        primary_area_efficiency=efficiency,
        shrinkage_reason=reason,
        left_pt=accounting.left_pt,
        right_pt=accounting.right_pt,
        bottom_pt=accounting.bottom_pt,
        top_pt=accounting.top_pt,
        intrinsic_left_pt=intrinsic_left,
        intrinsic_right_pt=intrinsic_right,
        intrinsic_bottom_pt=intrinsic_bottom,
        intrinsic_top_pt=intrinsic_top,
        unused_horizontal_pt=max(0.0, (allocation.width - primary.bbox.width) * scale),
        unused_vertical_pt=max(0.0, (allocation.height - primary.bbox.height) * scale),
    )


def register_panel_artist(axis: Axes, artist: Artist) -> None:
    layout = get_figure_layout(axis.figure)
    if layout is None:
        return
    panel = layout.panel_for_axis(axis)
    if panel is None:
        raise ValueError("artist axes is not registered to an outer panel footprint")
    if artist not in panel.artists:
        panel.artists.append(artist)


def register_figure_ornament(figure: Figure, artist: Artist) -> None:
    layout = get_figure_layout(figure)
    if layout is None:
        raise ValueError("figure has no registered panel layout")
    if artist not in layout.figure_ornaments:
        layout.figure_ornaments.append(artist)


def outer_panel_bbox(axis: Axes) -> Bbox:
    layout = get_figure_layout(axis.figure)
    if layout is not None:
        panel = layout.panel_for_axis(axis)
        if panel is None:
            raise ValueError("axes is not owned by the registered figure layout")
        return panel.bbox()
    try:
        spec = axis.get_subplotspec().get_topmost_subplotspec()
    except AttributeError:
        return axis.get_position()
    return spec.get_position(axis.figure)


def _axis_overhang_pt(axis: Axes, renderer: object) -> tuple[float, float, float, float]:
    tight = axis.get_tightbbox(renderer, bbox_extra_artists=[])
    bbox = axis.bbox
    scale = 72.0 / axis.figure.dpi
    return (
        max(0.0, bbox.x0 - tight.x0) * scale,
        max(0.0, tight.x1 - bbox.x1) * scale,
        max(0.0, bbox.y0 - tight.y0) * scale,
        max(0.0, tight.y1 - bbox.y1) * scale,
    )


def _panel_label_height_pt(figure: Figure, renderer: object, count: int) -> float:
    contract = load_contracts().style["panel"]
    properties = FontProperties(
        size=float(contract["font_size_pt"]), weight=str(contract["font_weight"])
    )
    heights = [
        renderer.get_text_width_height_descent(  # type: ignore[attr-defined]
            str(contract["format"]).format(letter=chr(ord("a") + index)),
            properties,
            ismath=False,
        )[1]
        for index in range(count)
    ]
    return max(heights, default=0.0) * 72.0 / figure.dpi


def _set_position_pt(axis: Axes, bbox: Bbox, insets: tuple[float, float, float, float]) -> None:
    figure_width, figure_height = _figure_size_pt(axis.figure)
    left, right, bottom, top = insets
    available_width = bbox.width * figure_width - left - right
    available_height = bbox.height * figure_height - bottom - top
    if available_width <= 0.0 or available_height <= 0.0:
        raise LayoutConstraintError(
            "physical panel constraints leave no positive Primary Visual Area "
            f"({available_width:.3f} x {available_height:.3f} pt)"
        )
    axis.set_position(
        Bbox.from_extents(
            bbox.x0 + left / figure_width,
            bbox.y0 + bottom / figure_height,
            bbox.x1 - right / figure_width,
            bbox.y1 - top / figure_height,
        )
    )


def solve_panel_layout(figure: Figure) -> None:
    """Measure decorations once and solve all panel positions from physical points."""
    layout = get_figure_layout(figure)
    if layout is None:
        return
    size_pt = _figure_size_pt(figure)
    if layout.solved_size_pt == size_pt:
        return
    style = load_contracts().style
    vertical_colorbar = style["colorbar"]["vertical"]
    colorbar_width = float(vertical_colorbar["width_pt"])
    colorbar_fraction = float(vertical_colorbar["length_fraction"])
    figure_width, figure_height = size_pt
    for legend in tuple(layout.legends):
        legend.remove()
    layout.legends.clear()
    for panel in layout.panels:
        if panel.panel_label is not None:
            panel.panel_label.remove()
            panel.panel_label = None
        if panel.primary_axes is None:
            raise ValueError(f"panel {panel.index} has no primary axes")
        footprint = panel.bbox()
        panel.primary_axes.set_position(footprint)
        for auxiliary in panel.auxiliary_axes:
            center_y = (footprint.y0 + footprint.y1) / 2.0
            probe_height = colorbar_fraction * footprint.height
            auxiliary.set_position(
                Bbox.from_extents(
                    footprint.x1 - colorbar_width / figure_width,
                    center_y - probe_height / 2.0,
                    footprint.x1,
                    center_y + probe_height / 2.0,
                )
            )
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    padding = float(style["layout"]["multi_panel"]["containment_padding_pt"])
    ordinary = [panel for panel in layout.panels if not panel.auxiliary_axes]
    ordinary_overhangs = [
        _axis_overhang_pt(panel.primary_axes, renderer)  # type: ignore[arg-type]
        for panel in ordinary
    ]
    if ordinary_overhangs:
        common_left = max(value[0] for value in ordinary_overhangs) + padding
        common_right = max(value[1] for value in ordinary_overhangs) + padding
    else:
        common_left = common_right = padding
    primary_overhangs = [
        _axis_overhang_pt(panel.primary_axes, renderer)  # type: ignore[arg-type]
        for panel in layout.panels
    ]
    common_bottom = max(value[2] for value in primary_overhangs) + padding
    common_top = max(value[3] for value in primary_overhangs) + padding
    if layout.panel_labels:
        panel_contract = style["panel"]
        label_gutter = (
            _panel_label_height_pt(figure, renderer, len(layout.panels))
            + max(0.0, float(panel_contract["top_offset_pt"]))
            + padding
        )
        common_top = max(common_top, label_gutter)

    from axiomfig.ornaments import requested_legend_height_pt

    legend_height = max(
        (requested_legend_height_pt(axis) for axis in layout.legend_requests), default=0.0
    )
    if legend_height:
        common_top += legend_height + float(style["legend"]["top_gap_pt"])

    colorbar_gap = float(style["colorbar"]["vertical"]["gap_pt"])
    for panel, overhang in zip(layout.panels, primary_overhangs, strict=True):
        assert panel.primary_axes is not None
        footprint = panel.bbox()
        if not panel.auxiliary_axes:
            panel.space_accounting = PanelSpaceAccounting(
                left_pt=common_left,
                right_pt=common_right,
                bottom_pt=common_bottom,
                top_pt=common_top,
                primary_right_without_aux_pt=common_right,
            )
            _set_position_pt(
                panel.primary_axes,
                footprint,
                (common_left, common_right, common_bottom, common_top),
            )
            continue
        auxiliary = panel.auxiliary_axes[0]
        auxiliary_overhang = _axis_overhang_pt(auxiliary, renderer)
        left = overhang[0] + padding
        primary_right_without_aux = overhang[1] + padding
        right = colorbar_gap + colorbar_width + auxiliary_overhang[1] + padding
        bottom = common_bottom
        top = common_top
        x0 = footprint.x0 + left / figure_width
        primary_x1 = footprint.x1 - right / figure_width
        y0 = footprint.y0 + bottom / figure_height
        y1 = footprint.y1 - top / figure_height
        if primary_x1 <= x0 or y1 <= y0:
            raise LayoutConstraintError(
                f"physical panel {panel.index} cannot contain its Primary Visual Area and "
                "measured right Colorbar strip"
            )
        panel.primary_axes.set_position(Bbox.from_extents(x0, y0, primary_x1, y1))
        panel.space_accounting = PanelSpaceAccounting(
            left_pt=left,
            right_pt=right,
            bottom_pt=bottom,
            top_pt=top,
            primary_right_without_aux_pt=primary_right_without_aux,
            colorbar_width_pt=colorbar_width,
            colorbar_gap_pt=colorbar_gap,
            colorbar_right_overhang_pt=auxiliary_overhang[1],
        )
    layout.solved_size_pt = size_pt
    figure.canvas.draw()
    for panel in layout.panels:
        _place_vertical_colorbar(panel)
    figure.canvas.draw()

    # A compact final Colorbar can select different tick text than the initial probe.
    # One bounded renderer correction makes the right strip match that actual bbox.
    renderer = figure.canvas.get_renderer()
    for panel in layout.panels:
        if not panel.auxiliary_axes:
            continue
        assert panel.primary_axes is not None
        assert panel.space_accounting is not None
        actual_overhang = _axis_overhang_pt(panel.auxiliary_axes[0], renderer)[1]
        accounting = panel.space_accounting
        if abs(actual_overhang - accounting.colorbar_right_overhang_pt) <= 0.05:
            continue
        corrected_right = colorbar_gap + colorbar_width + actual_overhang + padding
        corrected = replace(
            accounting,
            right_pt=corrected_right,
            colorbar_right_overhang_pt=actual_overhang,
        )
        _set_position_pt(
            panel.primary_axes,
            panel.bbox(),
            (corrected.left_pt, corrected.right_pt, corrected.bottom_pt, corrected.top_pt),
        )
        panel.space_accounting = corrected
    figure.canvas.draw()
    for panel in layout.panels:
        _place_vertical_colorbar(panel)
    for callback in layout.post_solve_callbacks:
        callback(figure)
    figure.canvas.draw()
