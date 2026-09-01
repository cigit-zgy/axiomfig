from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest


def _patch_geometry(figure: object) -> list[tuple[float, float, float, float]]:
    axis = figure.axes[0]  # type: ignore[attr-defined]
    return [
        (patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height())
        for patch in axis.patches
    ]


def test_bar_core_grammar_registry_and_legacy_compatibility() -> None:
    from axiomfig.templates import TEMPLATE_BUILDERS
    from axiomfig.templates.registry import load_family_contract, public_template_specs

    core = {
        "simple",
        "grouped",
        "stacked",
        "normalized_stacked",
        "grouped_stacked",
        "diverging_stacked",
        "range",
        "mirrored",
        "waterfall",
    }
    legacy = {"vertical", "horizontal", "dot"}
    variants = set(load_family_contract("bar")["variants"])

    assert core | legacy <= variants
    assert {f"bar/{variant}" for variant in core | legacy} <= set(TEMPLATE_BUILDERS)
    bar_specs = {spec.variant: spec for spec in public_template_specs() if spec.family == "bar"}
    assert {name for name, spec in bar_specs.items() if spec.agent_recommended} == core
    assert {name for name, spec in bar_specs.items() if not spec.agent_recommended} == legacy


@pytest.mark.parametrize(
    ("variant", "values", "logical_key"),
    [
        ("simple", {"category": ["A", "A"], "value": [1, 2]}, "category"),
        (
            "grouped",
            {"category": ["A", "A"], "group": ["G", "G"], "value": [1, 2]},
            "category, group",
        ),
        (
            "grouped_stacked",
            {
                "category": ["A", "A"],
                "group": ["G", "G"],
                "component": ["C", "C"],
                "value": [1, 2],
            },
            "category, group, component",
        ),
        (
            "stacked",
            {"category": ["A", "A"], "component": ["C", "C"], "value": [1, 2]},
            "category, component",
        ),
        (
            "normalized_stacked",
            {
                "category": ["A", "A"],
                "component": ["C", "C"],
                "value": [0.5, 0.5],
                "normalization": "proportion",
            },
            "category, component",
        ),
        (
            "diverging_stacked",
            {"category": ["A", "A"], "component": ["C", "C"], "value": [1, -1]},
            "category, component",
        ),
        ("range", {"category": ["A", "A"], "lower": [1, 2], "upper": [2, 3]}, "category"),
        (
            "mirrored",
            {
                "category": ["A", "A"],
                "side": ["left", "left"],
                "value": [1, 2],
                "mirror_side": "left",
            },
            "category, side",
        ),
        ("waterfall", {"step": ["A", "A"], "delta": [1, 2], "role": ["change", "total"]}, "step"),
    ],
)
def test_duplicate_logical_rows_fail_closed(
    variant: str, values: dict[str, object], logical_key: str
) -> None:
    from axiomfig.templates.bar.adapter import adapt

    with pytest.raises(ValueError, match=f"duplicate logical key.*{logical_key}"):
        adapt(variant, values)


def test_grouped_geometry_preserves_first_seen_order() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/grouped",
        category=["B", "B", "A", "A"],
        group=["second", "first", "second", "first"],
        value=[2.0, 1.0, 4.0, 3.0],
        value_labels=False,
    )
    try:
        axis = figure.axes[0]
        assert [tick.get_text() for tick in axis.get_xticklabels()] == ["B", "A"]
        assert [text.get_text() for text in axis.get_legend().get_texts()] == ["second", "first"]
        geometry = _patch_geometry(figure)
        assert geometry[0][0] < geometry[2][0]
        assert geometry[0][2] == pytest.approx(geometry[2][2])
    finally:
        plt.close(figure)


def test_stacked_bottoms_are_cumulative() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/stacked",
        category=["A", "B", "A", "B"],
        component=["base", "base", "top", "top"],
        value=[2.0, 3.0, 1.0, 4.0],
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        assert [item[1] for item in geometry[:2]] == pytest.approx([0.0, 0.0])
        assert [item[1] for item in geometry[2:]] == pytest.approx([2.0, 3.0])
    finally:
        plt.close(figure)


@pytest.mark.parametrize("normalization", ["normalize", "proportion"])
def test_normalized_stacked_totals_equal_one(normalization: str) -> None:
    from axiomfig.templates import build_template

    values = [2.0, 1.0, 3.0, 3.0] if normalization == "normalize" else [0.4, 0.25, 0.6, 0.75]
    figure = build_template(
        "bar/normalized_stacked",
        category=["A", "B", "A", "B"],
        component=["x", "x", "y", "y"],
        value=values,
        normalization=normalization,
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        totals = np.zeros(2)
        for index, (_, _, _, height) in enumerate(geometry):
            totals[index % 2] += height
        np.testing.assert_allclose(totals, 1.0)
    finally:
        plt.close(figure)


def test_grouped_stacked_hierarchy_uses_group_offsets_and_component_bottoms() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/grouped_stacked",
        category=["A", "A", "A", "A"],
        group=["G1", "G1", "G2", "G2"],
        component=["base", "top", "base", "top"],
        value=[2.0, 1.0, 4.0, 3.0],
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        assert geometry[0][0] != pytest.approx(geometry[1][0])
        assert sorted(item[1] for item in geometry) == pytest.approx([0.0, 0.0, 2.0, 4.0])
        assert [text.get_text() for text in figure.axes[0].get_legend().get_texts()] == [
            "G1 · base",
            "G2 · base",
            "G1 · top",
            "G2 · top",
        ]
    finally:
        plt.close(figure)


def test_diverging_stacked_accumulates_positive_and_negative_values_independently() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/diverging_stacked",
        category=["A", "A", "A", "A"],
        component=["p1", "n1", "p2", "n2"],
        value=[2.0, -1.0, 3.0, -4.0],
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        assert [item[1] for item in geometry] == pytest.approx([0.0, -1.0, 2.0, -5.0])
    finally:
        plt.close(figure)


@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
def test_range_bars_encode_supplied_lower_and_upper_endpoints(orientation: str) -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/range",
        category=["B", "A"],
        lower=[2.0, -1.0],
        upper=[5.0, 3.0],
        orientation=orientation,
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        if orientation == "vertical":
            assert [(item[1], item[3]) for item in geometry] == pytest.approx(
                [(2.0, 3.0), (-1.0, 4.0)]
            )
        else:
            assert [(item[0], item[2]) for item in geometry] == pytest.approx(
                [(2.0, 3.0), (-1.0, 4.0)]
            )
    finally:
        plt.close(figure)


def test_mirrored_bar_applies_sign_only_to_explicit_mirror_side() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/mirrored",
        category=["A", "A", "B", "B"],
        side=["left", "right", "left", "right"],
        value=[2.0, 3.0, 4.0, 5.0],
        mirror_side="left",
        value_labels=False,
    )
    try:
        heights = [patch.get_height() for patch in figure.axes[0].patches]
        assert heights == pytest.approx([-2.0, -4.0, 3.0, 5.0])
    finally:
        plt.close(figure)


def test_waterfall_cumulative_roles_are_explicit_and_deterministic() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "bar/waterfall",
        step=["Start", "Gain", "Loss", "Total"],
        delta=[5.0, 3.0, -2.0, 6.0],
        role=["subtotal", "change", "change", "total"],
        value_labels=False,
    )
    try:
        geometry = _patch_geometry(figure)
        assert [(item[1], item[3]) for item in geometry] == pytest.approx(
            [(0.0, 5.0), (5.0, 3.0), (6.0, 2.0), (0.0, 6.0)]
        )
        assert [line.get_ydata().tolist() for line in figure.axes[0].lines] == [
            [5.0, 5.0],
            [8.0, 8.0],
            [6.0, 6.0],
        ]
    finally:
        plt.close(figure)


def test_orientation_is_semantic_and_does_not_change_simple_schema() -> None:
    from axiomfig.intent import parse_figure_intent
    from axiomfig.templates.registry import load_family_contract

    required = load_family_contract("bar")["variants"]["simple"]["required"]
    vertical = parse_figure_intent(
        {"template": "bar.simple", "data": {"category": "name", "value": "score"}}
    )
    horizontal = parse_figure_intent(
        {
            "template": "bar.simple",
            "data": {"category": "name", "value": "score"},
            "semantics": {"orientation": "horizontal"},
        }
    )

    assert required == ["category", "value"]
    assert dict(vertical.data) == dict(horizontal.data)
    assert horizontal.semantics["orientation"] == "horizontal"


def test_orientation_is_one_modifier_on_every_core_bar_schema() -> None:
    from axiomfig.templates.registry import load_family_contract

    contract = load_family_contract("bar")["variants"]
    core = {
        "simple",
        "grouped",
        "stacked",
        "normalized_stacked",
        "grouped_stacked",
        "diverging_stacked",
        "range",
        "mirrored",
        "waterfall",
    }

    assert all("orientation" not in contract[name]["required"] for name in core)
    assert all("orientation" in contract[name]["optional"] for name in core)


def _build_public_bar(
    template: str,
    data: dict[str, object],
    *,
    semantics: dict[str, object] | None = None,
) -> object:
    from axiomfig.intent import build_intent_figure, parse_figure_intent

    mapping = {name: name for name in data}
    intent = parse_figure_intent(
        {
            "template": template,
            "data": mapping,
            "semantics": {} if semantics is None else semantics,
        }
    )
    return build_intent_figure(intent, data)


@pytest.mark.parametrize(
    ("template", "data", "semantics"),
    [
        ("bar.simple", {"category": [None], "value": [1.0]}, {}),
        (
            "bar.grouped",
            {"category": ["A"], "group": [None], "value": [1.0]},
            {},
        ),
        (
            "bar.stacked",
            {"category": ["A"], "component": [None], "value": [1.0]},
            {},
        ),
        (
            "bar.mirrored",
            {
                "category": ["A", "A"],
                "side": [None, "right"],
                "value": [1.0, 2.0],
            },
            {"mirror_side": "left"},
        ),
        (
            "bar.waterfall",
            {
                "step": [None, "Final"],
                "delta": [1.0, 1.0],
                "role": ["subtotal", "total"],
            },
            {},
        ),
        (
            "bar.waterfall",
            {
                "step": ["Initial", "Final"],
                "delta": [1.0, 1.0],
                "role": [None, "total"],
            },
            {},
        ),
    ],
)
def test_public_bar_rejects_null_identifier_roles(
    template: str,
    data: dict[str, object],
    semantics: dict[str, object],
) -> None:
    from axiomfig.intent import FigureIntentError

    with pytest.raises(FigureIntentError, match="labels must be non-null and non-empty"):
        _build_public_bar(template, data, semantics=semantics)


@pytest.mark.parametrize(
    ("template", "data", "semantics"),
    [
        (
            "bar.grouped",
            {
                "category": ["A", "A", "B"],
                "group": ["G1", "G2", "G1"],
                "value": [1.0, 2.0, 3.0],
            },
            {},
        ),
        (
            "bar.stacked",
            {
                "category": ["A", "A", "B"],
                "component": ["C1", "C2", "C1"],
                "value": [1.0, 2.0, 3.0],
            },
            {},
        ),
        (
            "bar.normalized_stacked",
            {
                "category": ["A", "A", "B"],
                "component": ["C1", "C2", "C1"],
                "value": [0.5, 0.5, 1.0],
            },
            {"normalization": "proportion"},
        ),
        (
            "bar.diverging_stacked",
            {
                "category": ["A", "A", "B"],
                "component": ["C1", "C2", "C1"],
                "value": [1.0, -1.0, 2.0],
            },
            {},
        ),
        (
            "bar.mirrored",
            {
                "category": ["A", "A", "B"],
                "side": ["left", "right", "left"],
                "value": [1.0, 2.0, 3.0],
            },
            {"mirror_side": "left"},
        ),
        (
            "bar.grouped_stacked",
            {
                "category": ["A", "A", "A"],
                "group": ["G1", "G1", "G2"],
                "component": ["C1", "C2", "C1"],
                "value": [1.0, 2.0, 3.0],
            },
            {},
        ),
    ],
)
def test_public_bar_incomplete_logical_grids_fail_at_adapter_boundary(
    template: str,
    data: dict[str, object],
    semantics: dict[str, object],
) -> None:
    from axiomfig.intent import FigureIntentError

    with pytest.raises(FigureIntentError, match="complete logical grid"):
        _build_public_bar(template, data, semantics=semantics)


@pytest.mark.parametrize(
    ("normalization", "values", "message"),
    [
        ("normalize", [0.0, 0.0], "positive category totals"),
        ("proportion", [0.5, 0.50000002], "within absolute tolerance"),
    ],
)
def test_public_normalized_stack_rejects_malformed_totals_with_bounded_error(
    normalization: str,
    values: list[float],
    message: str,
) -> None:
    from axiomfig.intent import FigureIntentError

    with pytest.raises(FigureIntentError, match=message):
        _build_public_bar(
            "bar.normalized_stacked",
            {
                "category": ["A", "A"],
                "component": ["x", "y"],
                "value": values,
            },
            semantics={"normalization": normalization},
        )


def test_proportion_absolute_tolerance_accepts_boundary_without_relative_slack() -> None:
    figure = _build_public_bar(
        "bar.normalized_stacked",
        {
            "category": ["A", "A"],
            "component": ["x", "y"],
            "value": [0.5, 0.50000001],
        },
        semantics={"normalization": "proportion"},
    )
    plt.close(figure)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("variant", "values", "message"),
    [
        ("simple", {"category": ["A", "B"], "value": [1.0]}, "equal-length"),
        ("simple", {"category": ["A"], "value": [np.inf]}, "finite"),
        (
            "simple",
            {"category": ["A"], "value": [1.0], "orientation": "diagonal"},
            "vertical or horizontal",
        ),
        (
            "mirrored",
            {
                "category": ["A"],
                "side": ["left"],
                "value": [1.0],
                "mirror_side": "left",
            },
            "exactly two side labels",
        ),
        (
            "mirrored",
            {
                "category": ["A", "A"],
                "side": ["left", "right"],
                "value": [1.0, 2.0],
                "mirror_side": "unknown",
            },
            "identify one supplied side",
        ),
        (
            "waterfall",
            {"step": ["A", "B"], "delta": [1.0, 1.0], "role": ["bad", "total"]},
            "change, subtotal, or total",
        ),
        (
            "waterfall",
            {"step": ["A", "B"], "delta": [1.0, 2.0], "role": ["subtotal", "total"]},
            "equal the cumulative value",
        ),
        (
            "grouped",
            {
                "category": ["A"],
                "group": ["G"],
                "value": [1.0],
                "error": [0.1],
            },
            "uncertainty_type is required",
        ),
    ],
)
def test_bar_required_negative_input_matrix(
    variant: str,
    values: dict[str, object],
    message: str,
) -> None:
    from axiomfig.templates.bar.adapter import adapt

    with pytest.raises(ValueError, match=message):
        adapt(variant, values)


@pytest.mark.parametrize(
    "template",
    [
        "bar/simple",
        "bar/grouped",
        "bar/stacked",
        "bar/normalized_stacked",
        "bar/grouped_stacked",
        "bar/diverging_stacked",
        "bar/range",
        "bar/mirrored",
        "bar/waterfall",
    ],
)
@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
def test_bar_builders_consume_both_axis_labels(template: str, orientation: str) -> None:
    from axiomfig.templates import build_template

    values: dict[str, object] = {
        "orientation": orientation,
        "xlabel": "Explicit x label",
        "ylabel": "Explicit y label",
    }
    if template == "bar/normalized_stacked":
        values["normalization"] = "normalize"
    figure = build_template(template, **values)
    try:
        axis = figure.axes[0]
        assert axis.get_xlabel() == "Explicit x label"
        assert axis.get_ylabel() == "Explicit y label"
    finally:
        plt.close(figure)
