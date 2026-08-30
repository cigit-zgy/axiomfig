from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pytest

from axiomfig.config import load_contracts
from axiomfig.layout import get_figure_layout
from axiomfig.templates import build_template


def test_hexbin_explains_quantitative_color_with_global_colorbar() -> None:
    figure = build_template("scatter/hexbin")
    try:
        layout = get_figure_layout(figure)
        assert layout is not None
        assert len(figure.axes) == 2
        primary, colorbar = figure.axes
        assert primary.collections
        assert colorbar.get_ylabel() == "Count"
        assert colorbar.yaxis.get_ticks_position() == "right"
        assert colorbar.yaxis.get_label_position() == "right"
    finally:
        plt.close(figure)


def test_quiver_limits_pad_every_vector_anchor() -> None:
    figure = build_template("field/quiver")
    try:
        axis = figure.axes[0]
        arrows = axis.collections[0]
        x_values = arrows.X
        y_values = arrows.Y
        x_limits = axis.get_xlim()
        y_limits = axis.get_ylim()

        assert x_limits[0] < min(x_values)
        assert x_limits[1] > max(x_values)
        assert y_limits[0] < min(y_values)
        assert y_limits[1] > max(y_values)
    finally:
        plt.close(figure)


def test_ecdf_marker_sampling_is_deterministic_and_bounded() -> None:
    figure = build_template("distribution/ecdf")
    try:
        maximum = int(load_contracts().style["plots"]["distribution"]["ecdf_max_markers"])
        for line in figure.axes[0].lines:
            step = line.get_markevery()
            assert isinstance(step, int)
            assert step >= 1
            assert math.ceil(len(line.get_xdata()) / step) <= maximum
    finally:
        plt.close(figure)


@pytest.mark.parametrize("template_id", ("distribution/strip", "distribution/raincloud"))
def test_dense_distribution_points_use_family_marker_area(template_id: str) -> None:
    figure = build_template(template_id)
    try:
        style = load_contracts().style["plots"]
        expected = float(style["distribution"]["raw_point_size_pt2"])
        scatter_default = float(style["scatter"]["marker_size_pt2"])
        point_sizes = [
            float(collection.get_sizes()[0])
            for collection in figure.axes[0].collections
            if len(collection.get_sizes()) == 1
        ]

        assert point_sizes
        assert all(size == pytest.approx(expected) for size in point_sizes)
        assert expected < scatter_default
    finally:
        plt.close(figure)
