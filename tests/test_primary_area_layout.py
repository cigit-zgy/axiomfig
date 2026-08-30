from __future__ import annotations

from contextlib import contextmanager

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

import axiomfig.layout as layout_module
from axiomfig.config import build_rcparams, load_contracts
from axiomfig.layout import (
    add_panel_axes,
    apply_output_margin,
    create_panel_grid,
    get_figure_layout,
    invalidate_panel_layout,
    outer_panel_bbox,
)
from axiomfig.ornaments import apply_colorbar_contract
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.gallery_cases import (
    MANTEL_GALLERY_GEOMETRIES,
    mantel_gallery_values,
)
from axiomfig.templates.registry import load_template_registry
from axiomfig.typography import apply_figure_typography, discover_fonts
from axiomfig.validation import FigureAnatomyError, validate_figure_anatomy


@contextmanager
def _rendered_template(template_id: str, *, geometry: str | None = None):
    selected_geometry = geometry or next(
        spec.geometry for spec in load_template_registry() if spec.template_id == template_id
    )
    discover_fonts("sans")
    params = build_rcparams(load_contracts(), geometry=selected_geometry, typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template(template_id)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        apply_figure_typography(figure, mode="sans")
        invalidate_panel_layout(figure)
        apply_output_margin(figure)
        apply_figure_typography(figure, mode="sans")
        figure.canvas.draw()
        try:
            yield figure
        finally:
            plt.close(figure)


@contextmanager
def _rendered_mantel(case_id: str = "canonical"):
    geometry = MANTEL_GALLERY_GEOMETRIES[case_id]
    discover_fonts("sans")
    params = build_rcparams(load_contracts(), geometry=geometry, typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template("association/mantel", **mantel_gallery_values(case_id))
        figure.set_size_inches(params["figure.figsize"], forward=False)
        apply_figure_typography(figure, mode="sans")
        invalidate_panel_layout(figure)
        apply_output_margin(figure)
        apply_figure_typography(figure, mode="sans")
        figure.canvas.draw()
        try:
            yield figure
        finally:
            plt.close(figure)


def _blank_panel(*, colorbar: bool):
    figure = plt.figure(figsize=(4.0, 3.0), dpi=100)
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=colorbar)
    axis.set_axis_off()
    if colorbar_axis is not None:
        scalar = ScalarMappable(norm=Normalize(0.0, 1.0), cmap="viridis")
        bar = figure.colorbar(scalar, cax=colorbar_axis, label="Measured scale")
        apply_colorbar_contract(bar)
    apply_output_margin(figure)
    figure.canvas.draw()
    return figure, axis, colorbar_axis


def test_vertical_colorbar_consumes_right_width_but_not_primary_height() -> None:
    plain_figure, plain_axis, _ = _blank_panel(colorbar=False)
    color_figure, color_axis, _ = _blank_panel(colorbar=True)
    try:
        assert color_axis.bbox.height == pytest.approx(plain_axis.bbox.height, abs=0.5)
        assert color_axis.bbox.width < plain_axis.bbox.width
    finally:
        plt.close(plain_figure)
        plt.close(color_figure)


def test_non_mantel_vertical_colorbar_uses_global_compact_geometry() -> None:
    with _rendered_template("heatmap/correlation") as figure:
        primary, colorbar = figure.axes
        scale = 72.0 / figure.dpi

        assert colorbar.bbox.width * scale == pytest.approx(9.0, abs=0.5)
        assert (colorbar.bbox.x0 - primary.bbox.x1) * scale == pytest.approx(6.0, abs=0.5)
        assert colorbar.bbox.height / primary.bbox.height == pytest.approx(0.72, abs=0.01)
        assert colorbar.bbox.y0 + colorbar.bbox.y1 == pytest.approx(
            primary.bbox.y0 + primary.bbox.y1,
            abs=0.5,
        )
        assert colorbar.yaxis.get_ticks_position() == "right"
        assert colorbar.yaxis.get_label_position() == "right"


def test_no_fixed_ratio_colorbar_layout_remains() -> None:
    single_panel = load_contracts().style["layout"]["single_panel"]

    assert "colorbar_width_ratio" not in single_panel
    assert "colorbar_wspace" not in single_panel


def test_colorbar_decorations_are_contained_by_the_outer_panel() -> None:
    with _rendered_template("heatmap/correlation") as figure:
        primary, colorbar = figure.axes
        renderer = figure.canvas.get_renderer()
        footprint = outer_panel_bbox(primary).transformed(figure.transFigure)
        decorated = colorbar.get_tightbbox(renderer, bbox_extra_artists=[])

        assert decorated.x0 >= footprint.x0 - 0.5
        assert decorated.y0 >= footprint.y0 - 0.5
        assert decorated.x1 <= footprint.x1 + 0.5
        assert decorated.y1 <= footprint.y1 + 0.5
        assert not colorbar.bbox.overlaps(primary.bbox)


@pytest.mark.parametrize(
    "template_id",
    (
        "heatmap/basic",
        "heatmap/correlation",
        "heatmap/clustered",
        "heatmap/confusion_matrix",
        "heatmap/annotated",
        "field/contour",
        "field/quiver",
        "omics/enrichment_dot",
        "layouts/grid_2x2",
        "layouts/grid_3x2",
    ),
)
def test_every_generic_vertical_colorbar_consumer_uses_one_solver(template_id: str) -> None:
    with _rendered_template(template_id) as figure:
        layout = get_figure_layout(figure)
        assert layout is not None
        panels = [panel for panel in layout.panels if panel.auxiliary_axes]
        assert len(panels) == 1
        panel = panels[0]
        assert panel.primary_axes is not None
        primary = panel.primary_axes
        colorbar = panel.auxiliary_axes[0]
        renderer = figure.canvas.get_renderer()
        footprint = panel.bbox().transformed(figure.transFigure)
        decorated = colorbar.get_tightbbox(renderer, bbox_extra_artists=[])
        scale = 72.0 / figure.dpi

        assert colorbar.bbox.width * scale == pytest.approx(9.0, abs=0.5)
        assert (colorbar.bbox.x0 - primary.bbox.x1) * scale == pytest.approx(6.0, abs=0.5)
        assert colorbar.bbox.height / primary.bbox.height == pytest.approx(0.72, abs=0.01)
        assert colorbar.bbox.y0 + colorbar.bbox.y1 == pytest.approx(
            primary.bbox.y0 + primary.bbox.y1,
            abs=0.5,
        )
        assert decorated.x0 >= footprint.x0 - 0.5
        assert decorated.y0 >= footprint.y0 - 0.5
        assert decorated.x1 <= footprint.x1 + 0.5
        assert decorated.y1 <= footprint.y1 + 0.5


def test_mantel_primary_area_diagnostic_proves_no_avoidable_shrinkage() -> None:
    assert hasattr(layout_module, "primary_area_diagnostic")
    with _rendered_mantel() as figure:
        diagnostic = layout_module.primary_area_diagnostic(figure.axes[0])

        assert diagnostic.maximum_side_with_aux_pt <= (
            diagnostic.maximum_side_without_aux_pt + 1e-6
        )
        assert diagnostic.primary_area_efficiency >= 0.98
        assert diagnostic.actual_side_pt == pytest.approx(
            diagnostic.maximum_side_with_aux_pt,
            abs=0.5,
        )
        assert diagnostic.outer_width_pt == pytest.approx(
            diagnostic.left_pt
            + diagnostic.right_pt
            + diagnostic.unused_horizontal_pt
            + diagnostic.intrinsic_left_pt
            + diagnostic.actual_side_pt
            + diagnostic.intrinsic_right_pt,
            abs=0.5,
        )
        assert diagnostic.outer_height_pt == pytest.approx(
            diagnostic.bottom_pt
            + diagnostic.top_pt
            + diagnostic.unused_vertical_pt
            + diagnostic.intrinsic_bottom_pt
            + diagnostic.actual_side_pt
            + diagnostic.intrinsic_top_pt,
            abs=0.5,
        )
        assert diagnostic.shrinkage_reason


def test_runtime_validation_rejects_avoidable_primary_area_shrinkage() -> None:
    with _rendered_mantel() as figure:
        axis = figure.axes[0]
        original = axis.get_position(original=True)
        axis.set_position((original.x0, original.y0, original.width * 0.90, original.height * 0.90))
        figure.canvas.draw()

        with pytest.raises(FigureAnatomyError, match="primary area efficiency"):
            validate_figure_anatomy(figure)


def test_impossible_primary_and_colorbar_constraints_raise_specific_error() -> None:
    assert hasattr(layout_module, "LayoutConstraintError")
    figure = plt.figure(figsize=(0.45, 0.45), dpi=100)
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    _axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    scalar = ScalarMappable(norm=Normalize(0.0, 1.0), cmap="viridis")
    bar = figure.colorbar(scalar, cax=colorbar_axis, label="Impossible label")
    apply_colorbar_contract(bar)
    try:
        with pytest.raises(layout_module.LayoutConstraintError, match="physical"):
            apply_output_margin(figure)
    finally:
        plt.close(figure)
