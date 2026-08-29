from __future__ import annotations

import matplotlib.pyplot as plt
import pytest
from matplotlib.transforms import ScaledTranslation

from axiomfig import template_helpers


def test_panel_labels_use_the_same_physical_gap_above_each_top_spine() -> None:
    figure, axes = plt.subplots(1, 2, figsize=(6.0, 2.5))
    template_helpers.add_panel_labels(axes, gap_pt=2.0)
    figure.canvas.draw()

    offsets = [
        label.get_window_extent(figure.canvas.get_renderer()).y0 - axis.bbox.y1
        for axis, label in zip(axes, (axis.texts[0] for axis in axes), strict=True)
    ]
    assert offsets[0] == pytest.approx(offsets[1], abs=0.01)
    assert offsets[0] == pytest.approx(2.0 * figure.dpi / 72.0, abs=0.01)
    plt.close(figure)


def test_panel_labels_align_with_each_axes_left_spine() -> None:
    figure, axes = plt.subplots(1, 2, figsize=(6.0, 2.5))
    template_helpers.add_panel_labels(axes)
    figure.canvas.draw()

    for axis, label in zip(axes, (axis.texts[0] for axis in axes), strict=True):
        label_bbox = label.get_window_extent(figure.canvas.get_renderer())
        assert label_bbox.x0 == pytest.approx(axis.bbox.x0)
    plt.close(figure)


def test_legend_is_responsive_frameless_and_right_aligned_to_the_spine() -> None:
    figure, axis = plt.subplots(figsize=(3.0, 2.0))
    for index in range(4):
        axis.plot([0, 1], [index, index + 1], label=f"Long label {index}")

    legend = template_helpers.place_legend_above(axis, gap_pt=2.0)
    figure.canvas.draw()
    assert legend is not None
    bbox = legend.get_window_extent(figure.canvas.get_renderer())
    assert legend.get_frame_on() is False
    assert legend._ncols < 4
    assert bbox.x1 == pytest.approx(axis.bbox.x1, abs=0.01)
    assert bbox.y0 - axis.bbox.y1 == pytest.approx(2.0 * figure.dpi / 72.0, abs=0.01)
    assert bbox.x0 >= figure.bbox.x0
    assert bbox.x1 <= figure.bbox.x1
    assert bbox.y1 <= figure.bbox.y1
    plt.close(figure)


def test_legend_rejects_add_axes_when_figure_top_space_cannot_be_reserved() -> None:
    figure = plt.figure(figsize=(3.0, 2.0))
    axis = figure.add_axes((0.125, 0.11, 0.775, 0.77))
    for index in range(4):
        axis.plot([0, 1], [index, index + 1], label=f"Long label {index}")

    with pytest.raises(ValueError, match="cannot fit"):
        template_helpers.place_legend_above(axis, gap_pt=2.0)
    plt.close(figure)


def test_legend_rejects_an_irreducibly_wide_single_column() -> None:
    figure, axis = plt.subplots(figsize=(3.0, 2.0))
    axis.plot([0, 1], [0, 1], label="W" * 1000)

    with pytest.raises(ValueError, match="cannot fit"):
        template_helpers.place_legend_above(axis, gap_pt=2.0)
    plt.close(figure)


def test_legend_rejects_a_rendered_collision_with_a_tagged_panel_label() -> None:
    figure, axis = plt.subplots(figsize=(5.0, 2.5))
    axis.plot([0, 1], [0, 1], label="W" * 23)
    template_helpers.add_panel_labels([axis])
    transform = axis.transAxes + ScaledTranslation(0.0, 2.0 / 72.0, figure.dpi_scale_trans)
    candidate = axis.legend(
        loc="lower right",
        bbox_to_anchor=(1.0, 1.0),
        bbox_transform=transform,
        frameon=False,
        borderaxespad=0.0,
    )
    figure.canvas.draw()
    assert candidate.get_window_extent(figure.canvas.get_renderer()).overlaps(
        axis.texts[0].get_window_extent(figure.canvas.get_renderer())
    )
    candidate.remove()

    with pytest.raises(ValueError, match="panel label"):
        template_helpers.place_legend_above(axis)
    plt.close(figure)


def test_panel_labels_reject_a_preexisting_colliding_legend() -> None:
    figure, axis = plt.subplots(figsize=(5.0, 2.5))
    axis.plot([0, 1], [0, 1], label="W" * 23)
    template_helpers.place_legend_above(axis)

    with pytest.raises(ValueError, match="panel label"):
        template_helpers.add_panel_labels([axis])
    plt.close(figure)
