from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from math import acos

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import Circle

from axiomfig.style import mantel_p_style
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.composition import normalize_composition
from axiomfig.templates.association.mantel.geometry import cell_center
from axiomfig.templates.association.mantel.glyphs import draw_glyph


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


@pytest.mark.parametrize(
    ("matrix_type", "matrix_region", "coupling_region", "label_edges", "sign"),
    [
        ("lower", "lower-left", "upper-right", ("left", "bottom"), -1),
        ("upper", "upper-right", "lower-left", ("top", "right"), 1),
    ],
)
def test_matrix_mask_owns_filled_label_and_complementary_regions(
    matrix_type: str,
    matrix_region: str,
    coupling_region: str,
    label_edges: tuple[str, str],
    sign: int,
) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    assert geometry.matrix_region == matrix_region
    assert geometry.coupling_region == coupling_region
    assert geometry.label_edges == label_edges

    diagonal = geometry.bounds.x0 + geometry.bounds.y0 + geometry.bounds.size
    for glyph in _artists(figure, "axiomfig-mantel-glyph"):
        x, y = cell_center(
            geometry.bounds,
            glyph._axiomfig_row,
            glyph._axiomfig_column,
            matrix_type=matrix_type,
        )
        assert sign * (x + y - diagonal) >= 0.0

    edges = tuple(
        artist._axiomfig_edge for artist in _artists(figure, "axiomfig-mantel-variable-label")
    )
    assert set(edges) == set(label_edges)
    assert len(edges) == 2 * len(geometry.target_positions)
    plt.close(figure)


@pytest.mark.parametrize(("matrix_type", "source_sign"), [("lower", 1), ("upper", -1)])
def test_node_layer_connects_every_link_inside_the_complementary_triangle(
    matrix_type: str,
    source_sign: int,
) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    diagonal = geometry.bounds.x0 + geometry.bounds.y0 + geometry.bounds.size
    source_nodes = _artists(figure, "axiomfig-mantel-source-node")
    target_nodes = _artists(figure, "axiomfig-mantel-target-node")
    links = _artists(figure, "axiomfig-mantel-link")

    assert len(source_nodes) == len(geometry.source_positions)
    assert len(target_nodes) == len(geometry.target_positions)
    assert not _artists(figure, "axiomfig-mantel-target-label")
    for node in source_nodes:
        x, y = node.center
        assert source_sign * (x + y - diagonal) > 0.0
    for node in target_nodes:
        x, y = node.center
        assert x + y == pytest.approx(diagonal)
    for link in links:
        vertices = link.get_path().vertices
        np.testing.assert_allclose(vertices[0], geometry.source_positions[link._axiomfig_source])
        np.testing.assert_allclose(vertices[-1], geometry.target_positions[link._axiomfig_target])
    plt.close(figure)


def test_source_nodes_are_two_dimensionally_distributed_and_links_fan() -> None:
    figure = build_template("association/mantel")
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    positions = np.asarray(tuple(geometry.source_positions.values()), dtype=float)
    assert np.ptp(positions[:, 0]) > 0.5
    assert np.ptp(positions[:, 1]) > 0.5

    directions: dict[str, list[np.ndarray]] = defaultdict(list)
    for link in _artists(figure, "axiomfig-mantel-link"):
        vertices = np.asarray(link.get_path().vertices, dtype=float)
        vector = vertices[1] - vertices[0]
        directions[link._axiomfig_source].append(vector / np.linalg.norm(vector))
    for vectors in directions.values():
        angles = [
            acos(float(np.clip(np.dot(first, second), -1.0, 1.0)))
            for first, second in combinations(vectors, 2)
        ]
        assert min(angles, default=1.0) > np.deg2rad(1.0)
    plt.close(figure)


def test_canonical_defaults_use_circle_and_three_bin_p_value_grammar() -> None:
    composition = normalize_composition({}, size=5)
    assert composition.glyphs[0].method == "circle"
    assert composition.coupling.p_value_mode == "canonical"

    assert mantel_p_style(0.005)["bin"] == "p<0.01"
    assert mantel_p_style(0.02)["bin"] == "0.01<=p<0.05"
    assert mantel_p_style(0.20)["bin"] == "p>=0.05"
    assert mantel_p_style(0.0005, mode="detailed")["bin"] == "p<0.001"


def test_matrix_region_is_semantic_alias_and_cannot_conflict_with_matrix_type() -> None:
    lower = normalize_composition({"matrix_region": "lower_left"}, size=5)
    upper = normalize_composition({"matrix_region": "upper_right"}, size=5)
    assert lower.matrix.matrix_type == "lower"
    assert upper.matrix.matrix_type == "upper"
    with pytest.raises(ValueError, match="same matrix mask"):
        normalize_composition(
            {"matrix_region": "lower_left", "matrix_type": "upper"},
            size=5,
        )


def test_circle_area_is_proportional_to_absolute_correlation() -> None:
    figure, axis = plt.subplots()
    weak = draw_glyph(
        axis,
        "circle",
        0.0,
        0.0,
        0.25,
        color="black",
        row=0,
        column=0,
        region="full",
    )
    strong = draw_glyph(
        axis,
        "circle",
        1.0,
        0.0,
        -1.0,
        color="black",
        row=0,
        column=1,
        region="full",
    )
    assert isinstance(weak, Circle)
    assert isinstance(strong, Circle)
    assert weak.radius**2 / strong.radius**2 == pytest.approx(0.25)
    plt.close(figure)
