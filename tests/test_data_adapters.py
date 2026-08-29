from __future__ import annotations

import pytest


def test_all_public_templates_have_an_external_operability_class() -> None:
    from axiomfig.data_adapters import DATA_ADAPTERS, OPERABILITY
    from axiomfig.templates.registry import public_template_specs

    public_ids = {spec.template_id for spec in public_template_specs()}

    assert public_ids == DATA_ADAPTERS
    assert set(OPERABILITY) == public_ids
    assert sum(value == "direct" for value in OPERABILITY.values()) == 28
    assert sum(value == "precomputed" for value in OPERABILITY.values()) == 27
    assert set(OPERABILITY.values()) == {"direct", "precomputed"}


@pytest.mark.parametrize(
    ("template_id", "required"),
    [
        ("line/multi", {"x", "series_values", "series_labels"}),
        ("distribution/density", {"x", "density"}),
        (
            "heatmap/clustered",
            {
                "matrix",
                "row_labels",
                "column_labels",
                "row_order",
                "column_order",
                "color_semantics",
            },
        ),
        (
            "association/mantel",
            {"correlation_matrix", "matrix_labels", "links", "link_strength", "significance"},
        ),
        ("association/correlation_network", {"nodes", "edges", "edge_weight"}),
        ("flow/sankey", {"source", "target", "value"}),
        ("field/contour", {"x_grid", "y_grid", "z", "color_semantics"}),
        (
            "omics/volcano",
            {"effect_size", "adjusted_p_value", "significance_threshold", "effect_threshold"},
        ),
        ("omics/enrichment_dot", {"term", "enrichment", "significance", "size"}),
        ("survival/kaplan_meier", {"time", "survival_probability"}),
    ],
)
def test_external_contracts_use_scientifically_explicit_roles(
    template_id: str,
    required: set[str],
) -> None:
    from axiomfig.templates.registry import load_family_contract

    family, variant = template_id.split("/", maxsplit=1)
    contract = load_family_contract(family)["variants"][variant]

    assert set(contract["required"]) == required


def test_adapter_normalizes_equal_length_line_data_without_dropping_roles() -> None:
    import numpy as np

    from axiomfig.data_adapters import adapt_template_data

    adapted = adapt_template_data(
        "line/single",
        {"x": [0, 1, 2], "y": [0.2, 0.5, 0.9], "xlabel": "Time"},
    )

    assert set(adapted) == {"x", "y", "xlabel"}
    np.testing.assert_allclose(adapted["x"], [0.0, 1.0, 2.0])
    np.testing.assert_allclose(adapted["y"], [0.2, 0.5, 0.9])
    assert adapted["xlabel"] == "Time"


def test_adapter_rejects_mismatched_vectors_before_builder_execution() -> None:
    from axiomfig.data_adapters import adapt_template_data

    with pytest.raises(ValueError, match="equal-length"):
        adapt_template_data("scatter/simple", {"x": [1, 2, 3], "y": [1, 2]})


def test_adapter_rejects_unknown_roles_instead_of_silently_dropping_them() -> None:
    from axiomfig.data_adapters import adapt_template_data

    with pytest.raises(ValueError, match="does not accept"):
        adapt_template_data("bar/vertical", {"category": ["A"], "value": [1], "mystery": [2]})


def test_adapter_validates_rectangular_heatmap_and_label_shapes() -> None:
    from axiomfig.data_adapters import adapt_template_data

    with pytest.raises(ValueError, match="row_labels"):
        adapt_template_data(
            "heatmap/basic",
            {
                "matrix": [[1.0, 2.0], [3.0, 4.0]],
                "row_labels": ["only-one"],
                "column_labels": ["A", "B"],
                "color_semantics": "sequential",
            },
        )


def test_adapter_validates_structured_mantel_links() -> None:
    from axiomfig.data_adapters import adapt_template_data

    with pytest.raises(ValueError, match="links"):
        adapt_template_data(
            "association/mantel",
            {
                "correlation_matrix": [[1.0, 0.2], [0.2, 1.0]],
                "matrix_labels": ["A", "B"],
                "links": [["A", "Community"], ["B"]],
                "link_strength": [0.6, 0.4],
                "significance": [True, False],
            },
        )
