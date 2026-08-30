from __future__ import annotations

import pytest


def test_all_public_templates_have_an_external_operability_class() -> None:
    from axiomfig.templates import TEMPLATE_ADAPTERS
    from axiomfig.templates.registry import public_template_operability, public_template_specs

    public_ids = {spec.template_id for spec in public_template_specs()}
    operability = public_template_operability()

    assert public_ids == set(TEMPLATE_ADAPTERS)
    assert set(operability) == public_ids
    assert sum(value == "direct" for value in operability.values()) == 28
    assert sum(value == "precomputed" for value in operability.values()) == 27
    assert set(operability.values()) == {"direct", "precomputed"}


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
            {"correlation_matrix", "labels", "links"},
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

    from axiomfig.templates import adapt_template_data

    adapted = adapt_template_data(
        "line/single",
        {"x": [0, 1, 2], "y": [0.2, 0.5, 0.9], "xlabel": "Time"},
    )

    assert set(adapted) == {"x", "y", "xlabel"}
    np.testing.assert_allclose(adapted["x"], [0.0, 1.0, 2.0])
    np.testing.assert_allclose(adapted["y"], [0.2, 0.5, 0.9])
    assert adapted["xlabel"] == "Time"


def test_adapter_rejects_mismatched_vectors_before_builder_execution() -> None:
    from axiomfig.templates import adapt_template_data

    with pytest.raises(ValueError, match="equal-length"):
        adapt_template_data("scatter/simple", {"x": [1, 2, 3], "y": [1, 2]})


def test_adapter_rejects_unknown_roles_instead_of_silently_dropping_them() -> None:
    from axiomfig.templates import adapt_template_data

    with pytest.raises(ValueError, match="does not accept"):
        adapt_template_data("bar/vertical", {"category": ["A"], "value": [1], "mystery": [2]})


def test_adapter_validates_rectangular_heatmap_and_label_shapes() -> None:
    from axiomfig.templates import adapt_template_data

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
    import numpy as np

    from axiomfig.templates import adapt_template_data

    adapted = adapt_template_data(
        "association/mantel",
        {
            "correlation_matrix": [[1.0, 0.2], [0.2, 1.0]],
            "labels": ["A", "B"],
            "links": [
                {
                    "source_group": "Surface",
                    "target_label": "A",
                    "mantel_r": 0.61,
                    "p_value": 0.004,
                },
                {
                    "source_group": "Deep",
                    "target_label": "B",
                    "mantel_r": 0.34,
                    "p_value": 0.08,
                },
            ],
        },
    )

    assert set(adapted) == {"correlation_matrix", "labels", "links"}
    np.testing.assert_allclose(adapted["correlation_matrix"], [[1.0, 0.2], [0.2, 1.0]])
    assert adapted["labels"].tolist() == ["A", "B"]
    assert tuple(adapted["links"]) == (
        {
            "source": "Surface",
            "target": "A",
            "mantel_r": 0.61,
            "p_value": 0.004,
        },
        {
            "source": "Deep",
            "target": "B",
            "mantel_r": 0.34,
            "p_value": 0.08,
        },
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"correlation_matrix": [[1.0, 0.2, 0.3], [0.2, 1.0, 0.4]]}, "square"),
        ({"correlation_matrix": [[1.0, 1.2], [1.2, 1.0]]}, "between -1 and 1"),
        ({"correlation_matrix": [[1.0, 0.3], [0.2, 1.0]]}, "symmetric"),
        ({"labels": ["A", "A"]}, "unique"),
        (
            {
                "links": [
                    {
                        "source_group": "Surface",
                        "target_label": "unknown",
                        "mantel_r": 0.5,
                        "p_value": 0.01,
                    }
                ]
            },
            "unknown target",
        ),
        (
            {
                "links": [
                    {
                        "source_group": "Surface",
                        "target_label": "A",
                        "mantel_r": 1.2,
                        "p_value": 0.01,
                    }
                ]
            },
            "mantel_r",
        ),
        (
            {
                "links": [
                    {
                        "source_group": "Surface",
                        "target_label": "A",
                        "mantel_r": 0.5,
                        "p_value": -0.01,
                    }
                ]
            },
            "p_value",
        ),
    ],
)
def test_mantel_adapter_rejects_malformed_precomputed_results(
    change: dict[str, object], message: str
) -> None:
    from axiomfig.templates import adapt_template_data

    values: dict[str, object] = {
        "correlation_matrix": [[1.0, 0.2], [0.2, 1.0]],
        "labels": ["A", "B"],
        "links": [
            {
                "source_group": "Surface",
                "target_label": "A",
                "mantel_r": 0.5,
                "p_value": 0.01,
            }
        ],
    }
    values.update(change)

    with pytest.raises(ValueError, match=message):
        adapt_template_data("association/mantel", values)
