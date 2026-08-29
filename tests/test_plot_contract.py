from __future__ import annotations

import matplotlib.pyplot as plt
import pytest
from matplotlib.ticker import AutoMinorLocator

from axiomfig import template_helpers
from axiomfig.contracts import STROKE_WIDTH_PT


@pytest.mark.parametrize(
    ("surface", "major", "minor"),
    [("open", "inout", "in"), ("filled", "out", "out")],
)
def test_axis_contract_sets_deterministic_ticks(surface: str, major: str, minor: str) -> None:
    figure, axis = plt.subplots()
    template_helpers.apply_axis_contract(axis, surface=surface)

    for coordinate_axis in (axis.xaxis, axis.yaxis):
        locator = coordinate_axis.get_minor_locator()
        assert isinstance(locator, AutoMinorLocator)
        assert locator.ndivs == 2
        assert coordinate_axis._major_tick_kw["tickdir"] == major
        assert coordinate_axis._minor_tick_kw["tickdir"] == minor
    plt.close(figure)


def test_bar_labels_preserve_default_precision_and_reserve_vertical_headroom() -> None:
    figure, axis = plt.subplots()
    container = axis.bar([0, 1], [1.2, 4.0])
    template_helpers.add_bar_value_labels(axis, [container])

    assert [text.get_text() for text in axis.texts] == ["1.20", "4.00"]
    assert axis.get_ylim()[1] > 4.0
    assert all(patch.get_edgecolor()[:3] == (0.0, 0.0, 0.0) for patch in container)
    assert all(patch.get_linewidth() == STROKE_WIDTH_PT for patch in container)
    plt.close(figure)


def test_bar_labels_reserve_horizontal_headroom_and_allow_precision_override() -> None:
    figure, axis = plt.subplots()
    container = axis.barh([0, 1], [1.2, 4.0])
    template_helpers.add_bar_value_labels(axis, [container], decimals=1)

    assert [text.get_text() for text in axis.texts] == ["1.2", "4.0"]
    assert axis.get_xlim()[1] > 4.0
    plt.close(figure)


def test_scatter_contract_uses_black_central_width_edges() -> None:
    figure, axis = plt.subplots()
    collection = axis.scatter([0, 1], [0, 1])
    template_helpers.apply_scatter_contract(collection)

    assert collection.get_edgecolors()[0, :3] == pytest.approx((0.0, 0.0, 0.0))
    assert collection.get_linewidths()[0] == STROKE_WIDTH_PT
    plt.close(figure)
