from __future__ import annotations

from itertools import combinations

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.legend import Legend
from matplotlib.patches import Circle, PathPatch

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.style import mantel_link_width, mantel_p_style
from axiomfig.templates import adapt_template_data, build_template
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_figure_anatomy

SPARSE: dict[str, object] = {
    "correlation_matrix": [
        [1.0, 0.62, -0.31, 0.18],
        [0.62, 1.0, -0.48, 0.27],
        [-0.31, -0.48, 1.0, -0.54],
        [0.18, 0.27, -0.54, 1.0],
    ],
    "labels": ["Oxygen", "Ammonium", "Nitrate", "Phosphate"],
    "links": [
        {
            "source_group": "Surface",
            "target_label": "Oxygen",
            "mantel_r": 0.62,
            "p_value": 0.0006,
        },
        {
            "source_group": "Surface",
            "target_label": "Nitrate",
            "mantel_r": 0.41,
            "p_value": 0.008,
        },
        {
            "source_group": "Deep",
            "target_label": "Ammonium",
            "mantel_r": 0.33,
            "p_value": 0.032,
        },
        {
            "source_group": "Deep",
            "target_label": "Phosphate",
            "mantel_r": 0.18,
            "p_value": 0.21,
        },
    ],
}

DENSE: dict[str, object] = {
    "correlation_matrix": [
        [1.0, 0.61, -0.33, 0.22, 0.47, -0.18],
        [0.61, 1.0, -0.52, 0.35, 0.28, -0.31],
        [-0.33, -0.52, 1.0, -0.58, -0.26, 0.44],
        [0.22, 0.35, -0.58, 1.0, 0.19, -0.36],
        [0.47, 0.28, -0.26, 0.19, 1.0, 0.39],
        [-0.18, -0.31, 0.44, -0.36, 0.39, 1.0],
    ],
    "labels": ["Oxygen", "Ammonium", "Nitrate", "Phosphate", "Temperature", "pH"],
    "links": [
        {"source_group": "Surface", "target_label": "Oxygen", "mantel_r": 0.67, "p_value": 0.0004},
        {"source_group": "Surface", "target_label": "Nitrate", "mantel_r": 0.48, "p_value": 0.004},
        {
            "source_group": "Surface",
            "target_label": "Temperature",
            "mantel_r": 0.23,
            "p_value": 0.09,
        },
        {"source_group": "Deep", "target_label": "Ammonium", "mantel_r": 0.55, "p_value": 0.008},
        {"source_group": "Deep", "target_label": "Phosphate", "mantel_r": 0.37, "p_value": 0.026},
        {"source_group": "Deep", "target_label": "pH", "mantel_r": 0.19, "p_value": 0.18},
        {
            "source_group": "Sediment",
            "target_label": "Nitrate",
            "mantel_r": 0.51,
            "p_value": 0.0008,
        },
        {
            "source_group": "Sediment",
            "target_label": "Phosphate",
            "mantel_r": 0.42,
            "p_value": 0.014,
        },
        {
            "source_group": "Sediment",
            "target_label": "Temperature",
            "mantel_r": 0.31,
            "p_value": 0.07,
        },
    ],
    "show_nonsignificant": True,
}


def _build(values: dict[str, object]):
    discover_fonts("sans")
    params = build_rcparams(load_contracts(), geometry="onehalf-column", typography="sans")
    adapted = adapt_template_data("association/mantel", values)
    with mpl.rc_context(rc=params):
        figure = build_template("association/mantel", **adapted)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        figure.canvas.draw()
    return figure


def _gid_children(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


def test_mantel_evaluation_includes_sparse_and_dense_fixtures() -> None:
    from tests.evaluation.run import load_evaluation_fixtures

    fixtures = load_evaluation_fixtures()
    for fixture_id, expected_links in (
        ("association_mantel_sparse", 4),
        ("association_mantel_dense", 9),
    ):
        fixture = fixtures[fixture_id]
        adapted = adapt_template_data(
            "association/mantel",
            {
                "correlation_matrix": fixture["correlation_matrix"],
                "labels": fixture["labels"],
                "links": fixture["mantel_links"],
                **(
                    {"nonsignificant_links": fixture["nonsignificant_links"]}
                    if "nonsignificant_links" in fixture
                    else {}
                ),
            },
        )
        assert len(adapted["links"]) == expected_links


def test_mantel_style_bins_are_deterministic_at_exact_boundaries() -> None:
    assert [mantel_link_width(value) for value in (0.249, 0.25, 0.499, 0.5)] == [
        0.8,
        1.4,
        1.4,
        2.2,
    ]
    assert [mantel_p_style(value)["significant"] for value in (0.0009, 0.009, 0.049, 0.05)] == [
        True,
        True,
        True,
        False,
    ]


def test_mantel_uses_one_lower_triangular_circle_matrix() -> None:
    figure = _build(SPARSE)
    cells = _gid_children(figure, "axiomfig-mantel-glyph")

    assert len(cells) == 4 * 3 // 2
    assert all(isinstance(cell, Circle) for cell in cells)
    assert len({round(cell.radius, 3) for cell in cells}) > 2
    assert all(cell._axiomfig_row > cell._axiomfig_column for cell in cells)
    plt.close(figure)


def test_mantel_links_are_traceable_and_fade_nonsignificant_by_default() -> None:
    figure = _build(SPARSE)
    links = _gid_children(figure, "axiomfig-mantel-link")

    assert len(links) == 4
    assert all(isinstance(link, PathPatch) for link in links)
    assert {(link._axiomfig_source_group, link._axiomfig_target_label) for link in links} == {
        ("Surface", "Oxygen"),
        ("Surface", "Nitrate"),
        ("Deep", "Ammonium"),
        ("Deep", "Phosphate"),
    }
    plt.close(figure)


def test_mantel_dense_case_keeps_nonsignificant_links_faint_and_contained() -> None:
    figure = _build({**DENSE, "show_nonsignificant": False, "nonsignificant_links": "fade"})
    links = _gid_children(figure, "axiomfig-mantel-link")

    assert len(links) == 9
    assert max(link.get_alpha() for link in links if link._axiomfig_p_value >= 0.05) < min(
        link.get_alpha() for link in links if link._axiomfig_p_value < 0.05
    )
    validate_figure_anatomy(figure)
    plt.close(figure)


@pytest.mark.parametrize("matrix_type", ["lower", "upper"])
def test_mantel_legends_labels_and_matrix_have_disjoint_footprints(matrix_type: str) -> None:
    figure = _build({**DENSE, "matrix_type": matrix_type})
    renderer = figure.canvas.get_renderer()
    legends = _gid_children(figure, "axiomfig-mantel-legend")
    cells = _gid_children(figure, "axiomfig-mantel-glyph")
    labels = _gid_children(figure, "axiomfig-mantel-variable-label")
    source_labels = _gid_children(figure, "axiomfig-mantel-source-label")

    assert len(legends) == 2
    assert all(isinstance(legend, Legend) for legend in legends)
    legend_boxes = [legend.get_window_extent(renderer) for legend in legends]
    cell_boxes = [cell.get_window_extent(renderer) for cell in cells]
    label_boxes = [label.get_window_extent(renderer) for label in labels]
    assert not legend_boxes[0].overlaps(legend_boxes[1])
    assert not any(legend.overlaps(cell) for legend in legend_boxes for cell in cell_boxes)
    assert not any(
        legend.overlaps(source.get_window_extent(renderer))
        for legend in legend_boxes
        for source in source_labels
    )
    assert not any(first.overlaps(second) for first, second in combinations(label_boxes, 2))
    source_boxes = [label.get_window_extent(renderer) for label in source_labels]
    assert not any(first.overlaps(second) for first, second in combinations(source_boxes, 2))
    plt.close(figure)


@pytest.mark.parametrize("matrix_type", ["lower", "upper"])
def test_mantel_renderer_layout_contains_long_scientific_labels(matrix_type: str) -> None:
    labels = [
        "Dissolved oxygen",
        "Ammonium nitrogen",
        "Nitrate nitrogen",
        "Total phosphorus",
        "Chemical oxygen demand",
        "Redox potential",
    ]
    values = {
        **DENSE,
        "labels": labels,
        "links": [
            {
                **link,
                "target_label": labels[index],
                "source_group": ("Surface biofilm", "Suspended biomass", "Sediment community")[
                    index % 3
                ],
            }
            for index, link in enumerate(DENSE["links"][:6])
        ],
    }
    figure = _build({**values, "matrix_type": matrix_type})
    renderer = figure.canvas.get_renderer()
    layout = figure._axiomfig_figure_layout
    footprint = layout.panels[0].bbox().transformed(figure.transFigure)
    labels_and_sources = [
        *_gid_children(figure, "axiomfig-mantel-variable-label"),
        *_gid_children(figure, "axiomfig-mantel-column-label"),
        *_gid_children(figure, "axiomfig-mantel-source-label"),
    ]

    for artist in labels_and_sources:
        bbox = artist.get_window_extent(renderer)
        assert footprint.contains(bbox.x0, bbox.y0)
        assert footprint.contains(bbox.x1, bbox.y1)
        assert figure.axes[0].bbox.contains(bbox.x0, bbox.y0)
        assert figure.axes[0].bbox.contains(bbox.x1, bbox.y1)
    validate_figure_anatomy(figure)
    plt.close(figure)
