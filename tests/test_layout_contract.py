from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from axiomfig import template_helpers
from axiomfig.config import build_rcparams, load_contracts
from axiomfig.templates import build_template


def test_single_series_has_no_legend() -> None:
    figure, axis = plt.subplots()
    axis.plot([0, 1], [0, 1], label="Only series")

    assert template_helpers.place_legend_above(axis) is None
    assert axis.get_legend() is None
    plt.close(figure)


def test_normal_legend_is_one_row_frameless_and_right_aligned() -> None:
    figure, axis = plt.subplots(figsize=(4.0, 2.5))
    for index in range(3):
        axis.plot([0, 1], [index, index + 1], label=f"S{index + 1}")

    legend = template_helpers.place_legend_above(axis)
    figure.canvas.draw()
    assert legend is not None
    bbox = legend.get_window_extent(figure.canvas.get_renderer())
    assert legend._ncols == 3
    assert legend.get_frame_on() is False
    assert legend.handlelength == 1.0
    assert legend.columnspacing == 1.0
    assert legend.borderpad == 0.0
    assert legend.borderaxespad == 0.0
    assert bbox.x1 == pytest.approx(axis.bbox.x1, abs=0.02)
    assert bbox.y0 > axis.bbox.y1
    assert bbox.y1 <= figure.bbox.y1
    expected_gap_px = 0.4666666667 * figure.dpi / 72.0
    assert bbox.y0 - axis.bbox.y1 == pytest.approx(expected_gap_px, abs=0.15)
    plt.close(figure)


def test_exact_figure_boundary_legend_is_accepted_without_reducing_columns() -> None:
    figure, axis = plt.subplots(figsize=(4.0, 2.5))
    for index in range(2):
        axis.plot([0, 1], [index, index + 1], label=f"Boundary {index + 1}")
    probe = axis.legend(ncol=2, frameon=False, handlelength=1.0)
    figure.canvas.draw()
    width_fraction = probe.get_window_extent(figure.canvas.get_renderer()).width / figure.bbox.width
    probe.remove()
    position = axis.get_position()
    axis.set_position((1.0 - width_fraction, position.y0, width_fraction, position.height))

    legend = template_helpers.place_legend_above(axis)

    assert legend is not None
    assert legend._ncols == 2
    plt.close(figure)


def test_overflow_reduces_columns_and_irreducible_overflow_errors() -> None:
    figure, axis = plt.subplots(figsize=(3.0, 2.5))
    for index in range(4):
        axis.plot([0, 1], [index, index + 1], label=f"Long label {index + 1}")
    legend = template_helpers.place_legend_above(axis)
    assert legend is not None
    assert legend._ncols < 4
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(3.0, 2.5))
    axis.plot([0, 1], [0, 1], label="W" * 1000)
    axis.plot([0, 1], [1, 2], label="second")
    with pytest.raises(ValueError, match="cannot fit"):
        template_helpers.place_legend_above(axis)
    plt.close(figure)


@pytest.mark.parametrize("dpi", [100, 200])
def test_panel_labels_use_primary_frame_offsets_and_11_point_bold(dpi: int) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(6.0, 2.5), dpi=dpi)
    template_helpers.add_panel_labels(axes)
    figure.canvas.draw()

    for axis, label in zip(axes, figure.texts, strict=True):
        bbox = label.get_window_extent(figure.canvas.get_renderer())
        assert bbox.x0 - axis.bbox.x0 == pytest.approx(-1.0 * dpi / 72.0, abs=0.1)
        assert bbox.y0 - axis.bbox.y1 == pytest.approx(1.0 * dpi / 72.0, abs=0.1)
        assert label.get_fontsize() == 11.0
        assert label.get_fontweight() == "bold"
    plt.close(figure)


def test_multi_panel_data_axes_are_equal_and_colorbar_is_independent() -> None:
    figure = build_template("layouts/grid_2x2")
    figure.canvas.draw()
    data_axes = figure.axes[:4]
    colorbar_axis = figure.axes[4]

    outer = [template_helpers.outer_panel_bbox(axis) for axis in data_axes]
    widths = [bbox.width for bbox in outer]
    heights = [bbox.height for bbox in outer]
    assert max(widths) - min(widths) < 0.02
    assert max(heights) - min(heights) < 0.02
    assert outer[1].x0 == pytest.approx(outer[3].x0, abs=0.02)
    assert colorbar_axis.bbox.x0 > data_axes[3].bbox.x1
    assert colorbar_axis.get_position().x1 <= outer[3].x1 + 0.0001
    assert colorbar_axis.bbox.y0 == pytest.approx(data_axes[3].bbox.y0, abs=0.02)
    assert colorbar_axis.bbox.y1 == pytest.approx(data_axes[3].bbox.y1, abs=0.02)
    assert colorbar_axis.yaxis._major_tick_kw["tickdir"] == "out"
    assert colorbar_axis.yaxis._minor_tick_kw["tickdir"] == "out"
    assert colorbar_axis.yaxis._major_tick_kw["tick1On"] is False
    assert colorbar_axis.yaxis._major_tick_kw["tick2On"] is True
    plt.close(figure)


@pytest.mark.parametrize(
    ("template", "rows", "columns"),
    [
        ("layouts/grid_2x2", 2, 2),
        ("layouts/grid_2x3", 2, 3),
        ("layouts/grid_3x2", 3, 2),
    ],
)
def test_registered_outer_footprints_are_exact_and_owned(
    template: str, rows: int, columns: int
) -> None:
    from axiomfig.layout import get_figure_layout

    figure = build_template(template)
    figure.canvas.draw()
    layout = get_figure_layout(figure)

    assert layout is not None
    assert (layout.rows, layout.columns) == (rows, columns)
    assert len(layout.panels) == rows * columns
    assert all(panel.primary_axes.figure is figure for panel in layout.panels)
    boxes = [panel.bbox().transformed(figure.transFigure) for panel in layout.panels]
    assert max(box.width for box in boxes) - min(box.width for box in boxes) < 1e-6
    assert max(box.height for box in boxes) - min(box.height for box in boxes) < 1e-6
    for row in range(rows):
        row_boxes = boxes[row * columns : (row + 1) * columns]
        assert max(box.y0 for box in row_boxes) - min(box.y0 for box in row_boxes) < 1e-6
        assert max(box.y1 for box in row_boxes) - min(box.y1 for box in row_boxes) < 1e-6
    for column in range(columns):
        column_boxes = boxes[column::columns]
        assert max(box.x0 for box in column_boxes) - min(box.x0 for box in column_boxes) < 1e-6
        assert max(box.x1 for box in column_boxes) - min(box.x1 for box in column_boxes) < 1e-6
    plt.close(figure)


@pytest.mark.parametrize("template", ["layouts/grid_2x2", "layouts/grid_2x3", "layouts/grid_3x2"])
def test_registered_panel_content_is_contained(template: str) -> None:
    from axiomfig.anatomy import validate_figure_anatomy

    figure = build_template(template)
    validate_figure_anatomy(figure)
    plt.close(figure)


@pytest.mark.parametrize(
    ("template", "rows", "columns"),
    [
        ("layouts/grid_2x2", 2, 2),
        ("layouts/grid_2x3", 2, 3),
        ("layouts/grid_3x2", 3, 2),
    ],
)
def test_outer_panel_footprints_are_symmetric(template: str, rows: int, columns: int) -> None:
    figure = build_template(template)
    figure.canvas.draw()
    data_axes = figure.axes[: rows * columns]
    boxes = [template_helpers.outer_panel_bbox(axis) for axis in data_axes]

    assert max(box.width for box in boxes) - min(box.width for box in boxes) < 0.02
    assert max(box.height for box in boxes) - min(box.height for box in boxes) < 0.02
    assert len(figure.texts) == rows * columns
    plt.close(figure)


@pytest.mark.parametrize(
    "template",
    [
        "layouts/horizontal_2",
        "layouts/grid_2x2",
        "layouts/grid_2x3",
        "layouts/grid_3x2",
    ],
)
def test_canonical_panel_labels_follow_primary_frames_after_family_layout(
    template: str,
) -> None:
    figure = build_template(template)
    figure.canvas.draw()
    data_axes = figure.axes[: len(figure.texts)]
    renderer = figure.canvas.get_renderer()
    offset_px = figure.dpi / 72.0

    for axis, label in zip(data_axes, figure.texts, strict=True):
        label_box = label.get_window_extent(renderer)
        assert label_box.x0 == pytest.approx(axis.bbox.x0 - offset_px, abs=0.15)
        assert label_box.y0 == pytest.approx(axis.bbox.y1 + offset_px, abs=0.15)
    plt.close(figure)


@pytest.mark.parametrize(
    "template",
    ["line/single", "scatter/simple", "bar/vertical", "distribution/violin", "heatmap/basic"],
)
def test_single_panel_layout_keeps_visible_text_inside_the_figure(template: str) -> None:
    params = build_rcparams(load_contracts(), geometry="single-column", typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template(template)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        template_helpers.apply_output_margin(figure)
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        artists = []
        for axis in figure.axes:
            artists.extend((axis.xaxis.label, axis.yaxis.label))
            x_lower, x_upper = sorted(axis.get_xlim())
            y_lower, y_upper = sorted(axis.get_ylim())
            artists.extend(
                label
                for location, label in zip(axis.get_xticks(), axis.get_xticklabels(), strict=False)
                if x_lower <= location <= x_upper
            )
            artists.extend(
                label
                for location, label in zip(axis.get_yticks(), axis.get_yticklabels(), strict=False)
                if y_lower <= location <= y_upper
            )
            if axis.get_legend() is not None:
                artists.append(axis.get_legend())
        visible = [
            artist
            for artist in artists
            if artist.get_visible() and (not hasattr(artist, "get_text") or artist.get_text())
        ]

        for artist in visible:
            bbox = artist.get_window_extent(renderer)
            label = artist.get_text() if hasattr(artist, "get_text") else "legend"
            assert bbox.x0 >= figure.bbox.x0 - 0.5, (template, label, bbox)
            assert bbox.y0 >= figure.bbox.y0 - 0.5, (template, label, bbox)
            assert bbox.x1 <= figure.bbox.x1 + 0.5, (template, label, bbox)
            assert bbox.y1 <= figure.bbox.y1 + 0.5, (template, label, bbox)
        plt.close(figure)


def test_tight_output_margin_handles_an_outside_multi_series_legend() -> None:
    params = build_rcparams(load_contracts(), geometry="single-column", typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template("line/multi")
        figure.set_size_inches(params["figure.figsize"], forward=False)
        template_helpers.apply_output_margin(figure)
        figure.canvas.draw()
        legend = figure.axes[0].get_legend()
        assert legend is not None
        renderer = figure.canvas.get_renderer()
        tight = figure.get_tightbbox(renderer, bbox_extra_artists=[legend]).transformed(
            figure.dpi_scale_trans
        )
        padding = 1.5 * figure.dpi / 72.0
        assert tight.x0 == pytest.approx(padding, abs=0.5)
        assert tight.y0 == pytest.approx(padding, abs=0.5)
        assert figure.bbox.width - tight.x1 == pytest.approx(padding, abs=0.5)
        assert figure.bbox.height - tight.y1 == pytest.approx(padding, abs=0.5)
        legend_bbox = legend.get_window_extent(renderer)
        assert figure.bbox.y1 - legend_bbox.y1 == pytest.approx(padding, abs=0.5)
        plt.close(figure)
