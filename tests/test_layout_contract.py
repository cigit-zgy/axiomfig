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
    assert bbox.x1 == pytest.approx(axis.bbox.x1, abs=0.02)
    assert bbox.y0 > axis.bbox.y1
    assert bbox.y1 <= figure.bbox.y1
    plt.close(figure)


def test_exact_boundary_legend_is_accepted_without_reducing_columns() -> None:
    figure, axis = plt.subplots(figsize=(4.0, 2.5))
    for index in range(2):
        axis.plot([0, 1], [index, index + 1], label=f"Boundary {index + 1}")
    probe = axis.legend(ncol=2, frameon=False, handlelength=1.0)
    figure.canvas.draw()
    width_fraction = probe.get_window_extent(figure.canvas.get_renderer()).width / figure.bbox.width
    probe.remove()
    position = axis.get_position()
    axis.set_position((position.x0, position.y0, width_fraction, position.height))

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
def test_panel_labels_use_fixed_physical_offsets_and_10_point_bold(dpi: int) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(6.0, 2.5), dpi=dpi)
    template_helpers.add_panel_labels(axes)
    figure.canvas.draw()

    for axis, label in zip(axes, (axis.texts[0] for axis in axes), strict=True):
        bbox = label.get_window_extent(figure.canvas.get_renderer())
        assert bbox.x0 - axis.bbox.x0 == pytest.approx(-2.0 * dpi / 72.0, abs=0.1)
        assert bbox.y0 - axis.bbox.y1 == pytest.approx(2.0 * dpi / 72.0, abs=0.1)
        assert label.get_fontsize() == 10.0
        assert label.get_fontweight() == "bold"
    plt.close(figure)


def test_multi_panel_data_axes_are_equal_and_colorbar_is_independent() -> None:
    figure = build_template("multi-panel")
    figure.canvas.draw()
    data_axes = figure.axes[:4]
    colorbar_axis = figure.axes[4]

    widths = [axis.bbox.width for axis in data_axes]
    heights = [axis.bbox.height for axis in data_axes]
    assert max(widths) - min(widths) < 0.02
    assert max(heights) - min(heights) < 0.02
    assert colorbar_axis.bbox.x0 > max(axis.bbox.x1 for axis in data_axes)
    assert colorbar_axis.yaxis._major_tick_kw["tickdir"] == "out"
    assert colorbar_axis.yaxis._minor_tick_kw["tickdir"] == "out"
    assert colorbar_axis.yaxis._major_tick_kw["tick1On"] is False
    assert colorbar_axis.yaxis._major_tick_kw["tick2On"] is True
    plt.close(figure)


@pytest.mark.parametrize("template", ["line", "scatter", "bar", "violin", "heatmap"])
def test_single_panel_layout_keeps_visible_text_inside_the_figure(template: str) -> None:
    params = build_rcparams(load_contracts(), geometry="single-column", typography="sans")
    with mpl.rc_context(rc=params):
        figure = build_template(template)
        figure.set_size_inches(params["figure.figsize"], forward=False)
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
