from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest


def _vertical_reference_values(axis: object) -> list[float]:
    values: list[float] = []
    for line in axis.lines:  # type: ignore[attr-defined]
        x = np.asarray(line.get_xdata(), dtype=float)
        if x.size == 2 and np.allclose(x, x[0]):
            values.append(float(x[0]))
    return values


def _horizontal_reference_values(axis: object) -> list[float]:
    values: list[float] = []
    for line in axis.lines:  # type: ignore[attr-defined]
        y = np.asarray(line.get_ydata(), dtype=float)
        if y.size == 2 and np.allclose(y, y[0]):
            values.append(float(y[0]))
    return values


@pytest.mark.parametrize(
    ("template_id", "supplied"),
    [
        (
            "heatmap/basic",
            {
                "matrix": [[-2.0, 0.0], [1.0, 3.0]],
                "row_labels": ["A", "B"],
                "column_labels": ["C", "D"],
                "color_semantics": "diverging",
            },
        ),
        (
            "heatmap/annotated",
            {
                "matrix": [[-2.0, 0.0], [1.0, 3.0]],
                "row_labels": ["A", "B"],
                "column_labels": ["C", "D"],
                "color_semantics": "diverging",
                "annotations": [["a", "b"], ["c", "d"]],
            },
        ),
        (
            "heatmap/clustered",
            {
                "matrix": [[-2.0, 0.0], [1.0, 3.0]],
                "row_labels": ["A", "B"],
                "column_labels": ["C", "D"],
                "row_order": [1, 0],
                "column_order": [0, 1],
                "color_semantics": "diverging",
            },
        ),
        (
            "field/contour",
            {
                "x_grid": [-1.0, 1.0],
                "y_grid": [-1.0, 1.0],
                "z": [[-2.0, 0.0], [1.0, 3.0]],
                "color_semantics": "diverging",
            },
        ),
    ],
)
def test_diverging_continuous_fields_require_explicit_center(
    template_id: str,
    supplied: dict[str, object],
) -> None:
    from axiomfig.templates import adapt_template_data, build_template

    with pytest.raises(ValueError, match="center"):
        adapt_template_data(template_id, supplied)

    adapted = adapt_template_data(template_id, {**supplied, "center": 0.0})
    figure = build_template(template_id, **adapted)

    assert adapted["center"] == 0.0
    plt.close(figure)


def test_bland_altman_contract_preserves_base_input_and_keeps_limits_precomputed() -> None:
    from axiomfig.intent import FigureIntentError, build_intent_figure, parse_figure_intent
    from axiomfig.templates.registry import load_family_contract

    contract = load_family_contract("diagnostics")["variants"]["bland_altman"]
    assert set(contract["required"]) == {"mean", "difference"}
    assert {"agreement_type", "center", "limits"} <= set(contract["optional"])

    intent = parse_figure_intent(
        {
            "template": "diagnostics.bland_altman",
            "data": {"mean": "mean", "difference": "difference"},
        }
    )
    figure = build_intent_figure(
        intent,
        {"mean": [1.0, 2.0], "difference": [0.2, -0.1]},
    )
    assert _horizontal_reference_values(figure.axes[0]) == []
    plt.close(figure)

    with pytest.raises(
        FigureIntentError,
        match="agreement_type, center, and limits must be supplied together",
    ):
        build_intent_figure(
            parse_figure_intent(
                {
                    "template": "diagnostics.bland_altman",
                    "data": {"mean": "mean", "difference": "difference"},
                    "semantics": {"agreement_type": "95% limits", "center": 0.05},
                }
            ),
            {"mean": [1.0, 2.0], "difference": [0.2, -0.1]},
        )


@pytest.mark.parametrize(
    ("template_id", "kwargs"),
    [
        (
            "estimation/forest",
            {
                "label": ["A", "B"],
                "estimate": [0.8, 1.2],
                "interval": [[0.6, 1.0], [1.0, 1.4]],
                "uncertainty_type": "95% CI",
            },
        ),
        (
            "estimation/coefficient",
            {
                "term": ["A", "B"],
                "estimate": [-0.2, 0.3],
                "interval": [[-0.4, 0.0], [0.1, 0.5]],
                "uncertainty_type": "95% CI",
            },
        ),
    ],
)
def test_external_estimation_does_not_invent_null_reference(
    template_id: str,
    kwargs: dict[str, object],
) -> None:
    from axiomfig.templates import build_template

    without_reference = build_template(template_id, **kwargs)
    with_reference = build_template(template_id, **kwargs, reference=1.0)

    assert _vertical_reference_values(without_reference.axes[0]) == []
    assert _vertical_reference_values(with_reference.axes[0]) == [1.0]
    plt.close(without_reference)
    plt.close(with_reference)


def test_external_precision_recall_does_not_invent_prevalence_baseline() -> None:
    from axiomfig.templates import build_template

    kwargs = {"recall": [0.0, 0.5, 1.0], "precision": [1.0, 0.8, 0.5]}
    without_baseline = build_template("diagnostics/precision_recall", **kwargs)
    with_baseline = build_template("diagnostics/precision_recall", **kwargs, baseline=0.2)

    assert _horizontal_reference_values(without_baseline.axes[0]) == []
    assert _horizontal_reference_values(with_baseline.axes[0]) == [0.2]
    plt.close(without_baseline)
    plt.close(with_baseline)


def test_precision_recall_axis_contains_supplied_probability_range() -> None:
    from axiomfig.templates import build_template

    figure = build_template(
        "diagnostics/precision_recall",
        recall=[0.0, 0.5, 1.0],
        precision=[1.0, 0.4, 0.1],
    )

    lower, upper = figure.axes[0].get_ylim()
    assert lower <= 0.1 <= upper
    plt.close(figure)


def test_omics_contract_names_executable_scientific_scales() -> None:
    from axiomfig.templates.registry import load_family_contract

    variants = load_family_contract("omics")["variants"]

    assert variants["volcano"]["role_semantics"] == {
        "effect_size": "log2_fold_change",
        "adjusted_p_value": "adjusted_p_value",
    }
    assert variants["enrichment_dot"]["role_semantics"]["significance"] == "adjusted_p_value"


def test_template_owned_reference_lines_match_scientific_grammar() -> None:
    from axiomfig.templates import build_template

    parity = build_template(
        "scatter/parity",
        observed=[1.0, 2.0, 3.0],
        predicted=[1.1, 1.9, 3.2],
    )
    residual = build_template(
        "diagnostics/residual",
        fitted=[1.0, 2.0, 3.0],
        residual=[-0.1, 0.2, -0.05],
    )
    calibration = build_template(
        "diagnostics/calibration",
        predicted_probability=[0.1, 0.5, 0.9],
        observed_frequency=[0.12, 0.48, 0.85],
    )
    roc = build_template(
        "diagnostics/roc",
        false_positive_rate=[0.0, 0.2, 1.0],
        true_positive_rate=[0.0, 0.8, 1.0],
    )
    bland_altman = build_template(
        "diagnostics/bland_altman",
        mean=[1.0, 2.0, 3.0],
        difference=[-0.2, 0.1, 0.3],
        agreement_type="95% limits",
        center=0.05,
        limits=[-0.4, 0.5],
    )

    parity_reference = parity.axes[0].lines[-1]
    calibration_reference = calibration.axes[0].lines[-1]
    roc_reference = roc.axes[0].lines[-1]
    np.testing.assert_allclose(parity_reference.get_xdata(), parity_reference.get_ydata())
    assert _horizontal_reference_values(residual.axes[0]) == [0.0]
    np.testing.assert_allclose(calibration_reference.get_xdata(), calibration_reference.get_ydata())
    np.testing.assert_allclose(roc_reference.get_xdata(), roc_reference.get_ydata())
    assert _horizontal_reference_values(bland_altman.axes[0]) == [0.05, 0.5, -0.4]

    for figure in (parity, residual, calibration, roc, bland_altman):
        plt.close(figure)
