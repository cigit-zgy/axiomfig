from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from matplotlib.collections import LineCollection
from matplotlib.container import BarContainer

from axiomfig.intent import FigureIntentError, build_intent_figure, parse_figure_intent


def _figure(variant, data, **semantics):
    intent = parse_figure_intent(
        {
            "template": f"bar.{variant}",
            "data": {role: role for role in data},
            "semantics": {"value_labels": False, **semantics},
        }
    )
    return build_intent_figure(intent, data)


@pytest.mark.parametrize("variant", ["simple", "grouped"])
@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
def test_endpoint_artists_preserve_asymmetric_zero_and_small_intervals(variant, orientation):
    values = [2.0, 0.0, 1e-12]
    lower, upper = [-1.0, 0.0, 0.9e-12], [2.5, 0.0, 1.3e-12]
    data = {"category": ["C", "A", "B"], "value": values, "lower": lower, "upper": upper}
    if variant == "grouped":
        data["group"] = ["Z", "Z", "Z"]
    figure = _figure(variant, data, uncertainty_type="95% CI", orientation=orientation)
    try:
        axis = figure.axes[0]
        coordinate = int(orientation == "vertical")
        segments = np.concatenate(
            [c.get_segments() for c in axis.collections if isinstance(c, LineCollection)]
        )
        np.testing.assert_allclose(segments[:, 0, coordinate], lower, atol=0, rtol=1e-14)
        np.testing.assert_allclose(segments[:, 1, coordinate], upper, atol=0, rtol=1e-14)
        limits = axis.get_ylim() if coordinate else axis.get_xlim()
        assert limits[0] <= min(lower) <= max(upper) <= limits[1]
    finally:
        plt.close(figure)


@pytest.mark.parametrize("variant", ["simple", "grouped"])
@pytest.mark.parametrize(
    "uncertainty",
    [
        {"lower": [3.0], "upper": [4.0]},
        {"lower": [0.0], "upper": [1.0]},
        {"lower": [0.0]},
        {"upper": [4.0]},
        {"lower": [0.0], "upper": [4.0], "error": [1.0]},
        {"lower": [0.0, 1.0], "upper": [4.0]},
        {"lower": [None], "upper": [4.0]},
        {"lower": ["not numeric"], "upper": [4.0]},
        {"lower": [-1e308], "upper": [1e308]},
        {"lower": [-(10**1000)], "upper": [4.0]},
    ],
)
def test_malformed_endpoint_input_is_bounded(variant, uncertainty):
    data = {"category": ["A"], "value": [2.0], **uncertainty}
    if variant == "grouped":
        data["group"] = ["G"]
    with pytest.raises(FigureIntentError):
        _figure(variant, data, uncertainty_type="CI")


@pytest.mark.parametrize("role", ["value", "lower", "upper"])
@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_nonfinite_endpoint_fields_fail_closed(role, invalid):
    data = {"category": ["A"], "value": [2.0], "lower": [1.0], "upper": [3.0]}
    data[role] = [invalid]
    with pytest.raises(FigureIntentError):
        _figure("simple", data, uncertainty_type="CI")


def test_endpoint_uncertainty_requires_explicit_meaning():
    with pytest.raises(FigureIntentError, match="uncertainty_type"):
        _figure("simple", {"category": ["A"], "value": [2.0], "lower": [1.0], "upper": [3.0]})


@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("uncertainty", ["none", "error", "endpoints"])
def test_sparse_grouped_preserves_global_slots_missing_zero_order_and_uncertainty(
    orientation, uncertainty
):
    data = {"category": ["B", "A", "A"], "group": ["Y", "X", "Y"], "value": [3.0, 0.0, 4.0]}
    semantics = {"orientation": orientation}
    if uncertainty == "error":
        data["error"] = [0.25, 0.0, 0.5]
        semantics["uncertainty_type"] = "SE"
    elif uncertainty == "endpoints":
        data.update(lower=[2.0, 0.0, 3.5], upper=[3.5, 0.0, 6.0])
        semantics["uncertainty_type"] = "95% PI"
    figure = _figure("grouped", data, **semantics)
    try:
        axis = figure.axes[0]
        bars = [c for c in axis.containers if isinstance(c, BarContainer)]
        assert [c.get_label() for c in bars] == ["Y", "X"]
        assert [len(c) for c in bars] == [2, 1]  # No B/X artist; A/X exists at zero.
        coordinate = int(orientation == "vertical")

        def center(p):
            return p.get_x() + p.get_width() / 2 if coordinate else p.get_y() + p.get_height() / 2

        width = bars[0][0].get_width() if coordinate else bars[0][0].get_height()
        np.testing.assert_allclose([center(p) for p in bars[0]], [-width / 2, 1 - width / 2])
        assert center(bars[1][0]) == pytest.approx(1 + width / 2)

        def magnitude(p):
            return p.get_height() if coordinate else p.get_width()

        assert [magnitude(p) for c in bars for p in c] == [3.0, 4.0, 0.0]
        ticks = axis.get_xticklabels() if coordinate else axis.get_yticklabels()
        assert [t.get_text() for t in ticks] == ["B", "A"]
        assert [t.get_text() for t in axis.get_legend().get_texts()] == ["Y", "X"]
        if uncertainty != "none":
            segments = np.concatenate(
                [c.get_segments() for c in axis.collections if isinstance(c, LineCollection)]
            )[:, :, coordinate]
            expected = (
                [[2.75, 3.25], [3.5, 4.5], [0.0, 0.0]]
                if uncertainty == "error"
                else [[2, 3.5], [3.5, 6], [0, 0]]
            )
            np.testing.assert_allclose(segments, expected)
    finally:
        plt.close(figure)


def test_sparse_grouped_duplicate_is_not_aggregated():
    with pytest.raises(FigureIntentError, match="duplicate logical key"):
        _figure("grouped", {"category": ["A", "A"], "group": ["G", "G"], "value": [1.0, 2.0]})


def test_endpoint_adapter_normalizes_only_declared_roles():
    from axiomfig.templates import adapt_template_data

    result = adapt_template_data(
        "bar/simple",
        {
            "category": ["A"],
            "value": [2.0],
            "lower": [1.5],
            "upper": [4.0],
            "uncertainty_type": "PI",
        },
    )
    assert set(result) == {"category", "value", "error", "uncertainty_type"}
    np.testing.assert_allclose(result["error"], [[0.5, 2.0]])


@pytest.mark.parametrize(
    "output", [{"category": ["A"]}, {"category": ["A"], "value": [1.0], "control_point": 1}]
)
def test_adapter_cannot_drop_required_or_introduce_undeclared_roles(monkeypatch, output):
    import axiomfig.templates as templates

    monkeypatch.setattr(
        templates, "TEMPLATE_ADAPTERS", {"bar/simple": lambda variant, values: output}
    )
    with pytest.raises(RuntimeError):
        templates.adapt_template_data("bar/simple", {"category": ["A"], "value": [1.0]})


@settings(max_examples=16, deadline=None)
@given(
    st.lists(
        st.tuples(st.sampled_from(["C", "A", "B"]), st.sampled_from(["Y", "X", "Z"])),
        min_size=1,
        max_size=9,
        unique=True,
    ),
    st.sampled_from(["vertical", "horizontal"]),
)
def test_sparse_row_permutations_preserve_supplied_artist_inventory(keys, orientation):
    categories, groups = zip(*keys, strict=True)
    # Supplied zero and asymmetric endpoint intervals must survive any sparse subset/order.
    values = list(range(len(keys)))
    data = {
        "category": categories,
        "group": groups,
        "value": values,
        "lower": values,
        "upper": [v + 0.25 for v in values],
    }
    figure = _figure("grouped", data, orientation=orientation, uncertainty_type="PI")
    try:
        axis = figure.axes[0]
        containers = [c for c in axis.containers if isinstance(c, BarContainer)]
        category_order, group_order = list(dict.fromkeys(categories)), list(dict.fromkeys(groups))
        assert [c.get_label() for c in containers] == group_order
        assert len(axis.patches) == len(keys)
        for index, container in enumerate(containers):
            expected = [
                (category_order.index(c), v)
                for (c, g), v in zip(keys, values, strict=True)
                if g == group_order[index]
            ]
            for patch, (category_index, value) in zip(container, expected, strict=True):
                if orientation == "vertical":
                    span, center, magnitude = (
                        patch.get_width(),
                        patch.get_x() + patch.get_width() / 2,
                        patch.get_height(),
                    )
                else:
                    span, center, magnitude = (
                        patch.get_height(),
                        patch.get_y() + patch.get_height() / 2,
                        patch.get_width(),
                    )
                assert center == pytest.approx(
                    category_index + (index - (len(group_order) - 1) / 2) * span
                )
                assert magnitude == value
    finally:
        plt.close(figure)
