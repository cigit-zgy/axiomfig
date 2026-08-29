from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, LogLocator

from axiomfig import template_helpers
from axiomfig.templates import build_template


def _rendered_inward_projection_pt(direction: str, length_pt: float) -> float:
    dpi = 1440
    figure = Figure(figsize=(1.0, 1.0), dpi=dpi)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    axis.set_xticks([0.5], [""])
    axis.set_yticks([])
    for name, spine in axis.spines.items():
        spine.set_visible(name == "bottom")
    axis.spines["bottom"].set_color("red")
    axis.spines["bottom"].set_linewidth(0.2)
    axis.tick_params(axis="x", direction=direction, length=length_pt, width=0.8, colors="black")
    figure.canvas.draw()
    pixels = np.asarray(figure.canvas.buffer_rgba())[:, :, :3]
    x_px, y_px = axis.transData.transform((0.5, 0.0))
    rows = np.where(np.all(pixels[:, round(x_px) - 2 : round(x_px) + 3] < 64, axis=2))[0]
    display_y = figure.canvas.get_width_height()[1] - 1 - rows
    inward_px = max(display_y) - y_px
    return inward_px * 72.0 / dpi


def test_rendered_inout_geometry_sets_the_golden_minor_inward_projection() -> None:
    major_inward = _rendered_inward_projection_pt("inout", 4.0)
    minor_inward = _rendered_inward_projection_pt("in", 1.236)

    assert major_inward == pytest.approx(2.0, abs=0.15)
    assert minor_inward == pytest.approx(1.236, abs=0.10)
    assert minor_inward / major_inward == pytest.approx(0.618, abs=0.04)


@pytest.mark.parametrize(
    ("surface", "major", "minor"),
    [("open", "inout", "in"), ("filled", "out", "out")],
)
def test_axis_contract_sets_one_minor_and_deterministic_directions(
    surface: str, major: str, minor: str
) -> None:
    figure, axis = plt.subplots()
    template_helpers.apply_axis_contract(axis, surface=surface)

    for coordinate_axis in (axis.xaxis, axis.yaxis):
        assert isinstance(coordinate_axis.get_minor_locator(), AutoMinorLocator)
        assert coordinate_axis.get_minor_locator().ndivs == 2
        assert coordinate_axis._major_tick_kw["tickdir"] == major
        assert coordinate_axis._minor_tick_kw["tickdir"] == minor
    plt.close(figure)


def test_axis_contract_preserves_logarithmic_locator() -> None:
    figure, axis = plt.subplots()
    axis.set_xscale("log")
    locator = axis.xaxis.get_minor_locator()
    assert isinstance(locator, LogLocator)

    template_helpers.apply_axis_contract(axis, surface="open")

    assert axis.xaxis.get_minor_locator() is locator
    plt.close(figure)


def test_categorical_axis_removes_tick_lines_but_keeps_labels() -> None:
    figure, axis = plt.subplots()
    axis.set_xticks([0, 1], ["A", "B"])

    template_helpers.apply_categorical_axis(axis, coordinate="x")
    figure.canvas.draw()

    assert [label.get_text() for label in axis.get_xticklabels()] == ["A", "B"]
    assert all(tick.tick1line.get_markersize() == 0 for tick in axis.xaxis.majorTicks)
    plt.close(figure)


def test_bar_scatter_and_violin_use_fill_edge_contract() -> None:
    figure, axes = plt.subplots(1, 3)
    bars = axes[0].bar([0, 1], [1.2, 4.0])
    template_helpers.add_bar_value_labels(axes[0], [bars])
    scatter = axes[1].scatter([0, 1], [0, 1], s=3, alpha=1.0)
    template_helpers.apply_scatter_contract(scatter)
    violin = axes[2].violinplot([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    template_helpers.apply_violin_contract(violin)

    assert [text.get_text() for text in axes[0].texts] == ["1.20", "4.00"]
    assert all(patch.get_edgecolor()[:3] == (0.0, 0.0, 0.0) for patch in bars)
    assert all(patch.get_linewidth() == 0.6 for patch in bars)
    assert scatter.get_edgecolors()[0, :3] == pytest.approx((0.0, 0.0, 0.0))
    assert scatter.get_linewidths()[0] == 0.6
    assert scatter.get_alpha() == 0.55
    assert scatter.get_sizes() == pytest.approx([36.0])
    assert all(body.get_linewidths()[0] == 0.6 for body in violin["bodies"])
    plt.close(figure)


def test_violin_geometry_has_deterministic_headroom() -> None:
    figure = build_template("violin")
    axis = figure.axes[0]
    body_top = max(
        path.vertices[:, 1].max() for body in axis.collections for path in body.get_paths()
    )

    assert axis.get_ylim()[1] - body_top >= 0.01
    plt.close(figure)


@pytest.mark.parametrize("name", ["vertical-bar", "violin"])
def test_bar_and_violin_use_open_numeric_ticks_and_no_category_marks(name: str) -> None:
    figure = build_template(name)
    axis = figure.axes[0]

    assert axis.xaxis._major_tick_kw["size"] == 0.0
    assert axis.yaxis._major_tick_kw["tickdir"] == "inout"
    assert axis.yaxis._minor_tick_kw["tickdir"] == "in"
    plt.close(figure)


def test_heatmap_uses_outward_ticks_on_image_and_colorbar() -> None:
    figure = build_template("heatmap")

    for axis in figure.axes:
        assert axis.yaxis._major_tick_kw["tickdir"] == "out"
        assert axis.yaxis._minor_tick_kw["tickdir"] == "out"
    plt.close(figure)


def test_plot_artist_defaults_are_consumed_from_style_tokens() -> None:
    from axiomfig.config import load_contracts

    plots = load_contracts().style["plots"]
    line_marker = build_template("line-marker").axes[0].lines[0]
    ci_axis = build_template("line-ci").axes[0]
    violin_axis = build_template("violin").axes[0]

    assert line_marker.get_markersize() == plots["line_marker"]["marker_size_pt"]
    assert line_marker.get_markeredgecolor() == plots["line_marker"]["edge_color"]
    assert ci_axis.collections[0].get_alpha() == plots["confidence_interval"]["alpha"]
    assert violin_axis.collections[0].get_alpha() == plots["violin"]["alpha"]
    plt.close(line_marker.figure)
    plt.close(ci_axis.figure)
    plt.close(violin_axis.figure)


@pytest.mark.parametrize("name", ["line-marker", "regression-scatter", "errorbar"])
def test_marker_examples_keep_data_strictly_inside_axes(name: str) -> None:
    figure = build_template(name)
    axis = figure.axes[0]
    x_lower, x_upper = sorted(axis.get_xlim())
    y_lower, y_upper = sorted(axis.get_ylim())
    points: list[tuple[float, float]] = []
    for line in axis.lines:
        if line.get_marker() not in {"None", "none", "", " ", None}:
            points.extend(zip(line.get_xdata(), line.get_ydata(), strict=False))
    for collection in axis.collections:
        if isinstance(collection, PathCollection):
            points.extend(tuple(point) for point in collection.get_offsets())

    assert points
    assert all(x_lower < x < x_upper and y_lower < y < y_upper for x, y in points)
    plt.close(figure)
