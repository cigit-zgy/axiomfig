from __future__ import annotations

from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import Circle, Ellipse, Rectangle, Wedge

from axiomfig.templates import adapt_template_data, build_template
from axiomfig.templates.association.mantel.builder import canonical_mantel_values
from axiomfig.templates.association.mantel.data import (
    CI_MODES,
    GLYPH_METHODS,
    HCLUST_METHODS,
    MATRIX_TYPES,
    ORDERING_MODES,
    SIGNIFICANCE_MODES,
)
from axiomfig.templates.association.mantel.ordering import order_variables
from axiomfig.validation import validate_figure_anatomy


def _case(size: int = 5) -> dict[str, object]:
    labels = [f"V{index + 1:02d}" for index in range(size)]
    coordinates = np.linspace(-1.0, 1.0, size)
    matrix = np.cos(np.subtract.outer(coordinates, coordinates) * 1.35)
    matrix = np.clip(matrix, -1.0, 1.0)
    np.fill_diagonal(matrix, 1.0)
    links = [
        {
            "source": f"Source {index % 3 + 1}",
            "target": labels[index],
            "mantel_r": (-1.0 if index % 4 == 0 else 1.0) * min(0.95, 0.12 + 0.04 * index),
            "p_value": (0.0005, 0.005, 0.025, 0.12)[index % 4],
        }
        for index in range(size)
    ]
    return {"correlation_matrix": matrix, "labels": labels, "links": links}


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


def _build(size: int = 5, **options: object):
    figure = build_template("association/mantel", **_case(size), **options)
    figure.canvas.draw()
    return figure


def test_public_capability_enumerations_match_agreed_surface() -> None:
    assert GLYPH_METHODS == (
        "circle",
        "square",
        "ellipse",
        "number",
        "shade",
        "color",
        "pie",
    )
    assert MATRIX_TYPES == ("full", "upper", "lower", "mixed")
    assert ORDERING_MODES == ("original", "alphabet", "AOE", "FPC", "hclust")
    assert HCLUST_METHODS == (
        "complete",
        "ward",
        "ward.D",
        "ward.D2",
        "single",
        "average",
        "mcquitty",
        "median",
        "centroid",
    )
    assert SIGNIFICANCE_MODES == ("none", "mark", "p_value", "blank", "label_sig")
    assert CI_MODES == ("none", "square", "circle", "rect")


@pytest.mark.parametrize(("method", "matrix_type"), list(product(GLYPH_METHODS, MATRIX_TYPES[:3])))
def test_all_7_by_3_base_matrix_combinations_render(method: str, matrix_type: str) -> None:
    size = 4
    figure = _build(
        size,
        matrix_method=method,
        matrix_type=matrix_type,
        diagonal="hide",
        nonsignificant_links="hide",
    )
    glyphs = _artists(figure, "axiomfig-mantel-glyph")
    expected = size * (size - 1) if matrix_type == "full" else size * (size - 1) // 2
    assert len(glyphs) == expected
    assert {artist._axiomfig_method for artist in glyphs} == {method}
    validate_figure_anatomy(figure)
    plt.close(figure)


@pytest.mark.parametrize(("lower_method", "upper_method"), list(product(GLYPH_METHODS, repeat=2)))
def test_all_7_by_7_mixed_combinations_render(
    lower_method: str,
    upper_method: str,
) -> None:
    size = 3
    figure = _build(
        size,
        matrix_type="mixed",
        lower_method=lower_method,
        upper_method=upper_method,
        diagonal="hide",
        nonsignificant_links="hide",
    )
    glyphs = _artists(figure, "axiomfig-mantel-glyph")
    assert len(glyphs) == size * (size - 1)
    assert {artist._axiomfig_triangle for artist in glyphs} == {"lower", "upper"}
    figure.canvas.draw()
    plt.close(figure)


@pytest.mark.parametrize("mode", ORDERING_MODES)
def test_ordering_is_a_deterministic_synchronized_permutation(mode: str) -> None:
    values = _case(6)
    matrix = np.asarray(values["correlation_matrix"])
    labels = tuple(reversed(values["labels"]))
    result_a = order_variables(matrix, labels, mode=mode, hclust_method="complete", clusters=3)
    result_b = order_variables(matrix, labels, mode=mode, hclust_method="complete", clusters=3)
    assert result_a.indices.tolist() == result_b.indices.tolist()
    assert sorted(result_a.indices.tolist()) == list(range(6))
    if mode == "alphabet":
        assert [labels[index] for index in result_a.indices] == sorted(labels)
    np.testing.assert_allclose(
        result_a.matrix,
        matrix[np.ix_(result_a.indices, result_a.indices)],
    )
    assert result_a.labels == tuple(labels[index] for index in result_a.indices)


@pytest.mark.parametrize("method", HCLUST_METHODS)
def test_all_hclust_methods_are_deterministic_and_return_requested_clusters(method: str) -> None:
    values = _case(7)
    result = order_variables(
        np.asarray(values["correlation_matrix"]),
        tuple(values["labels"]),
        mode="hclust",
        hclust_method=method,
        clusters=3,
    )
    assert sorted(result.indices.tolist()) == list(range(7))
    assert len(result.clusters) == 3
    assert sorted(index for cluster in result.clusters for index in cluster) == list(range(7))


@pytest.mark.parametrize("mode", SIGNIFICANCE_MODES)
def test_significance_modes_have_explicit_artist_behavior(mode: str) -> None:
    values = _case(4)
    p_values = np.asarray(
        (
            (0.0, 0.0005, 0.005, 0.08),
            (0.0005, 0.0, 0.02, 0.12),
            (0.005, 0.02, 0.0, 0.03),
            (0.08, 0.12, 0.03, 0.0),
        )
    )
    figure = build_template(
        "association/mantel",
        **values,
        p_values=p_values,
        significance_mode=mode,
        matrix_type="lower",
        diagonal="hide",
    )
    figure.canvas.draw()
    significance = _artists(figure, "axiomfig-mantel-significance")
    glyphs = _artists(figure, "axiomfig-mantel-glyph")
    if mode == "none":
        assert not significance
        assert len(glyphs) == 6
    elif mode == "blank":
        assert not significance
        assert len(glyphs) == 4
    else:
        assert significance
    plt.close(figure)


@pytest.mark.parametrize("mode", CI_MODES)
def test_confidence_interval_modes_are_vector_native(mode: str) -> None:
    values = _case(4)
    matrix = np.asarray(values["correlation_matrix"])
    lower = np.clip(matrix - 0.08, -1.0, 1.0)
    upper = np.clip(matrix + 0.08, -1.0, 1.0)
    np.fill_diagonal(lower, 1.0)
    np.fill_diagonal(upper, 1.0)
    figure = build_template(
        "association/mantel",
        **values,
        lower_ci=lower,
        upper_ci=upper,
        ci_mode=mode,
        matrix_type="lower",
        diagonal="hide",
    )
    figure.canvas.draw()
    intervals = _artists(figure, "axiomfig-mantel-confidence-interval")
    assert len(intervals) == (0 if mode == "none" else 6)
    plt.close(figure)


def test_adapter_accepts_advanced_precomputed_roles_nan_and_negative_mantel_r() -> None:
    values = _case(3)
    matrix = np.asarray(values["correlation_matrix"])
    matrix[0, 1] = matrix[1, 0] = np.nan
    p_values = np.full((3, 3), 0.02)
    np.fill_diagonal(p_values, 0.0)
    adapted = adapt_template_data(
        "association/mantel",
        {
            **values,
            "correlation_matrix": matrix,
            "p_values": p_values,
            "matrix_method": "ELLIPSE",
            "matrix_type": "Lower",
            "diagonal": "hide",
            "order": "AOE",
            "nonsignificant_links": "fade",
        },
    )
    assert np.isnan(adapted["correlation_matrix"][0, 1])
    assert adapted["links"][0]["mantel_r"] < 0.0
    assert adapted["links"][0]["source"] == "Source 1"
    assert adapted["links"][0]["target"] == "V01"
    assert adapted["matrix_method"] == "ellipse"
    assert adapted["matrix_type"] == "lower"


def test_adapter_accepts_legacy_link_aliases_without_dropping_metadata() -> None:
    adapted = adapt_template_data(
        "association/mantel",
        {
            "correlation_matrix": [[1.0, 0.2], [0.2, 1.0]],
            "labels": ["A", "B"],
            "links": [
                {
                    "source_group": "Surface",
                    "target_label": "A",
                    "mantel_r": 0.4,
                    "p_value": 0.02,
                    "label": "precomputed",
                    "metadata": {"permutations": 999},
                }
            ],
        },
    )
    assert adapted["links"] == (
        {
            "source": "Surface",
            "target": "A",
            "mantel_r": 0.4,
            "p_value": 0.02,
            "label": "precomputed",
            "metadata": {"permutations": 999},
        },
    )


def test_diagonal_show_hide_missing_values_clusters_and_coefficients() -> None:
    values = _case(5)
    matrix = np.asarray(values["correlation_matrix"])
    matrix[1, 3] = matrix[3, 1] = np.nan
    hidden = build_template(
        "association/mantel",
        **{**values, "correlation_matrix": matrix},
        matrix_type="full",
        diagonal="hide",
        order="hclust",
        hclust_method="complete",
        clusters=2,
        coefficients=True,
    )
    shown = build_template(
        "association/mantel",
        **{**values, "correlation_matrix": matrix},
        matrix_type="full",
        diagonal="show",
    )
    hidden.canvas.draw()
    shown.canvas.draw()
    assert len(_artists(hidden, "axiomfig-mantel-glyph")) == 20
    assert len(_artists(shown, "axiomfig-mantel-glyph")) == 25
    assert (
        sum(
            artist._axiomfig_method == "missing"
            for artist in _artists(hidden, "axiomfig-mantel-glyph")
        )
        == 2
    )
    assert len(_artists(hidden, "axiomfig-mantel-cluster-rectangle")) == 2
    assert len(_artists(hidden, "axiomfig-mantel-coefficient")) == 18
    plt.close(hidden)
    plt.close(shown)


def test_glyph_geometry_encodes_area_orientation_and_pie_direction() -> None:
    values = _case(3)
    values["correlation_matrix"] = np.asarray(
        ((1.0, 0.25, -0.81), (0.25, 1.0, 0.64), (-0.81, 0.64, 1.0))
    )
    square = build_template(
        "association/mantel", **values, matrix_method="square", matrix_type="full"
    )
    circle = build_template(
        "association/mantel", **values, matrix_method="circle", matrix_type="full"
    )
    ellipse = build_template(
        "association/mantel", **values, matrix_method="ellipse", matrix_type="full"
    )
    pie = build_template("association/mantel", **values, matrix_method="pie", matrix_type="full")
    for figure in (square, circle, ellipse, pie):
        figure.canvas.draw()
    square_values = {
        round(artist._axiomfig_value, 2): artist
        for artist in _artists(square, "axiomfig-mantel-glyph")
    }
    assert isinstance(square_values[0.25], Rectangle)
    assert square_values[0.25].get_width() ** 2 == pytest.approx(
        square_values[-0.81].get_width() ** 2 * 0.25 / 0.81
    )
    circle_values = {
        round(artist._axiomfig_value, 2): artist
        for artist in _artists(circle, "axiomfig-mantel-glyph")
    }
    assert isinstance(circle_values[0.25], Circle)
    assert circle_values[0.25].radius ** 2 == pytest.approx(
        circle_values[-0.81].radius ** 2 * 0.25 / 0.81
    )
    ellipse_values = [
        artist
        for artist in _artists(ellipse, "axiomfig-mantel-glyph")
        if isinstance(artist, Ellipse) and abs(artist._axiomfig_value) < 1.0
    ]
    assert {artist.angle for artist in ellipse_values} == {-45.0, 45.0}
    pie_values = [
        artist for artist in _artists(pie, "axiomfig-mantel-glyph") if isinstance(artist, Wedge)
    ]
    assert any(artist.theta1 < 90.0 and artist.theta2 == 90.0 for artist in pie_values)
    assert any(artist.theta1 == 90.0 and artist.theta2 > 90.0 for artist in pie_values)
    for figure in (square, circle, ellipse, pie):
        plt.close(figure)


@pytest.mark.parametrize(("mode", "expected"), [("hide", 4), ("fade", 5), ("show", 5)])
def test_nonsignificant_modes_and_continuous_width(mode: str, expected: int) -> None:
    figure = _build(5, nonsignificant_links=mode, link_width_mode="continuous")
    links = _artists(figure, "axiomfig-mantel-link")
    assert len(links) == expected
    if mode == "fade":
        assert max(link.get_alpha() for link in links if link._axiomfig_p_value >= 0.05) < min(
            link.get_alpha() for link in links if link._axiomfig_p_value < 0.05
        )
    if mode == "show":
        assert {link.get_alpha() for link in links} == {0.9}
    assert len({round(link.get_linewidth(), 3) for link in links}) > 1
    plt.close(figure)


def test_canonical_fixture_is_valid_compact_and_exercises_all_link_bins() -> None:
    values = canonical_mantel_values()
    matrix = np.asarray(values["correlation_matrix"])
    links = values["links"]
    assert matrix.shape == (10, 10)
    assert np.linalg.eigvalsh(matrix).min() >= -1e-10
    assert len({link["source"] for link in links}) == 3
    assert 12 <= len(links) <= 20
    assert any(link["mantel_r"] < 0.0 for link in links)
    assert {
        0 if abs(link["mantel_r"]) < 0.25 else 1 if abs(link["mantel_r"]) < 0.5 else 2
        for link in links
    } == {0, 1, 2}
    assert {
        0
        if link["p_value"] < 0.001
        else 1
        if link["p_value"] < 0.01
        else 2
        if link["p_value"] < 0.05
        else 3
        for link in links
    } == {0, 1, 2, 3}
    figure = build_template("association/mantel")
    figure.canvas.draw()
    assert len(_artists(figure, "axiomfig-mantel-variable-label")) == 10
    assert len(_artists(figure, "axiomfig-mantel-source-node")) == 3
    assert len(_artists(figure, "axiomfig-mantel-link")) == len(links)
    rendered_links = _artists(figure, "axiomfig-mantel-link")
    rendered_glyphs = _artists(figure, "axiomfig-mantel-glyph")
    assert not any(
        link.get_path()
        .transformed(link.get_transform())
        .intersects_path(glyph.get_path().transformed(glyph.get_transform()), filled=False)
        for link in rendered_links
        for glyph in rendered_glyphs
        if hasattr(glyph, "get_path")
    )
    validate_figure_anatomy(figure)
    plt.close(figure)


@pytest.mark.parametrize("size", [5, 10, 15, 20])
def test_density_cases_are_contained_and_routing_is_repeatable(size: int) -> None:
    first = _build(size, matrix_type="lower", diagonal="hide", nonsignificant_links="fade")
    second = _build(size, matrix_type="lower", diagonal="hide", nonsignificant_links="fade")
    validate_figure_anatomy(first)
    validate_figure_anatomy(second)
    first_signature = [
        link._axiomfig_route_signature for link in _artists(first, "axiomfig-mantel-link")
    ]
    second_signature = [
        link._axiomfig_route_signature for link in _artists(second, "axiomfig-mantel-link")
    ]
    assert first_signature == second_signature
    assert not any(link.get_clip_on() is False for link in _artists(first, "axiomfig-mantel-link"))
    plt.close(first)
    plt.close(second)
