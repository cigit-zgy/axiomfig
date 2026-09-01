from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from axiomfig.intent import FigureIntentError, build_intent_figure, parse_figure_intent
from axiomfig.templates import adapt_template_data
from axiomfig.templates.distribution.builders import build_raincloud
from axiomfig.templates.registry import load_family_contract, public_template_specs


@pytest.mark.parametrize("uncertainty_type", ("SD", "SE", "95% CI", "95% PI"))
def test_uncertainty_semantics_are_preserved_without_substitution(
    uncertainty_type: str,
) -> None:
    intent = parse_figure_intent(
        {
            "template": "line.errorbar",
            "data": {"x": "x", "estimate": "mean", "error": "error"},
            "semantics": {"uncertainty_type": uncertainty_type},
        }
    )
    assert intent.semantics["uncertainty_type"] == uncertainty_type


def test_diverging_heatmap_requires_explicit_center() -> None:
    with pytest.raises(FigureIntentError, match="missing required fields.*center"):
        parse_figure_intent(
            {
                "template": "heatmap.correlation",
                "data": {"matrix": "matrix", "labels": "labels"},
            }
        )


def test_center_is_rejected_for_a_template_that_does_not_own_it() -> None:
    with pytest.raises(FigureIntentError, match="unsupported fields.*center"):
        parse_figure_intent(
            {
                "template": "scatter.simple",
                "data": {"x": "x", "y": "y"},
                "semantics": {"center": 0.0},
            }
        )


def test_analysis_request_cannot_enter_plotting_semantics() -> None:
    with pytest.raises(FigureIntentError, match="unsupported fields.*compute_pca"):
        parse_figure_intent(
            {
                "template": "ordination.pca_scores",
                "data": {"coordinates": "raw_matrix", "explained_variance": "variance"},
                "semantics": {"compute_pca": True},
            }
        )


@pytest.mark.parametrize(
    ("template_id", "values", "message"),
    (
        ("line/single", {"x": [1, 2, 3], "y": [1, 2]}, "equal-length"),
        ("scatter/simple", {"x": [1, 2, 3], "y": [1, 2]}, "equal-length"),
        ("bar/vertical", {"category": ["a", "b"], "value": [1]}, "equal-length"),
        (
            "heatmap/basic",
            {
                "matrix": [[1, 2], [3, 4]],
                "row_labels": ["a"],
                "column_labels": ["x", "y"],
                "color_semantics": "sequential",
            },
            "match matrix shape",
        ),
        (
            "estimation/forest",
            {"label": ["a", "b"], "estimate": [1], "interval": [0.1], "uncertainty_type": "SE"},
            "equal-length",
        ),
        (
            "ordination/pca_scores",
            {"coordinates": [[1, 2, 3], [4, 5, 6]], "explained_variance": [50, 20]},
            "n by 2",
        ),
        (
            "association/mantel",
            {"correlation_matrix": [[1, 0], [0, 1]], "labels": ["a"], "links": []},
            "match correlation_matrix",
        ),
        (
            "field/contour",
            {
                "x_grid": [0, 1],
                "y_grid": [0, 1],
                "z": [[1, 2, 3], [4, 5, 6]],
                "color_semantics": "sequential",
            },
            "shape must match",
        ),
        (
            "omics/volcano",
            {
                "effect_size": [1, 2],
                "adjusted_p_value": [0.05, 0.02, 0.01],
                "significance_threshold": 0.05,
                "effect_threshold": 1.0,
            },
            "equal-length",
        ),
    ),
)
def test_representative_family_shape_mismatches_are_bounded(
    template_id: str, values: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        adapt_template_data(template_id, values)


@pytest.mark.parametrize("limits", ([0.0], [0.0, 1.0, 2.0], [1.0, 0.0]))
def test_invalid_parity_identity_limits_fail_closed(limits: list[float]) -> None:
    with pytest.raises(ValueError, match="identity_limits"):
        adapt_template_data(
            "scatter/parity",
            {"observed": [0, 1], "predicted": [0, 1], "identity_limits": limits},
        )


def test_raincloud_supports_the_actual_number_of_categories() -> None:
    categories = np.repeat(["a", "b", "c", "d"], 4)
    figure = build_raincloud(np.linspace(0.0, 1.0, 16), categories)
    try:
        axis = figure.axes[0]
        assert [tick.get_text() for tick in axis.get_xticklabels()] == ["a", "b", "c", "d"]
        assert len(axis.collections) >= 8
    finally:
        plt.close(figure)


def test_malformed_public_data_never_leaks_internal_exception_types() -> None:
    for spec in public_template_specs():
        contract = load_family_contract(spec.family)["variants"][spec.variant]
        required = tuple(contract["required"])
        intent = parse_figure_intent(
            {
                "template": spec.template_id,
                "data": {role: role for role in required},
            }
        )
        dataset = {role: object() for role in required}
        try:
            figure = build_intent_figure(intent, dataset)
        except Exception as exc:  # noqa: BLE001 - the assertion audits the public boundary
            assert isinstance(exc, FigureIntentError), (
                spec.template_id,
                type(exc).__name__,
                str(exc),
            )
        else:
            plt.close(figure)
