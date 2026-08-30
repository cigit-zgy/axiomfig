from __future__ import annotations

import numpy as np
import pytest

from axiomfig.layout import get_figure_layout
from axiomfig.templates import build_template
from axiomfig.validation import validate_figure_anatomy


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


def _cross(a: np.ndarray, b: np.ndarray, point: np.ndarray) -> float:
    vector = b - a
    offset = point - a
    return float(vector[0] * offset[1] - vector[1] * offset[0])


@pytest.mark.parametrize(("matrix_type", "relation"), [("upper", "lt"), ("lower", "gt")])
def test_triangular_masks_are_logically_distinct(matrix_type: str, relation: str) -> None:
    figure = build_template(
        "association/mantel",
        matrix_type=matrix_type,
        diagonal="hide",
        coupling=False,
    )
    figure.canvas.draw()
    glyphs = _artists(figure, "axiomfig-mantel-glyph")
    assert glyphs
    pairs = [(artist._axiomfig_row, artist._axiomfig_column) for artist in glyphs]
    if relation == "lt":
        assert all(row < column for row, column in pairs)
    else:
        assert all(row > column for row, column in pairs)


@pytest.mark.parametrize(("matrix_type", "corner"), [("upper", "lower-left"), ("lower", "upper-left")])
def test_sources_live_inside_unused_matrix_triangle(matrix_type: str, corner: str) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    assert geometry.source_region.corner == corner
    bounds = geometry.bounds
    for x, y in geometry.source_positions.values():
        assert bounds.x0 <= x <= bounds.x1
        assert bounds.y0 <= y <= bounds.y1

    rail = np.asarray(tuple(geometry.target_positions.values()), dtype=float)
    source = np.asarray(tuple(geometry.source_positions.values()), dtype=float)
    a, b = rail[0], rail[-1]
    signs = np.asarray([_cross(a, b, point) for point in source])
    assert np.all(np.abs(signs) > 0.25)
    assert np.all(signs > 0) or np.all(signs < 0)
    validate_figure_anatomy(figure)


@pytest.mark.parametrize("matrix_type", ["upper", "lower"])
def test_bezier_control_polygon_stays_in_coupling_half_plane(matrix_type: str) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    rail = np.asarray(tuple(geometry.target_positions.values()), dtype=float)
    a, b = rail[0], rail[-1]
    source_signs = [
        _cross(a, b, np.asarray(point, dtype=float)) for point in geometry.source_positions.values()
    ]
    expected_sign = 1.0 if float(np.mean(source_signs)) > 0 else -1.0

    for link in _artists(figure, "axiomfig-mantel-link"):
        vertices = np.asarray(link.get_path().vertices, dtype=float)
        for point in vertices[:-1]:
            assert expected_sign * _cross(a, b, point) >= -1e-8
        target = np.asarray(geometry.target_positions[link._axiomfig_target], dtype=float)
        np.testing.assert_allclose(vertices[-1], target, atol=1e-12)


@pytest.mark.parametrize("matrix_type", ["upper", "lower"])
def test_canonical_target_anchors_are_geometry_only_and_colorbar_is_auxiliary(matrix_type: str) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    assert not _artists(figure, "axiomfig-mantel-target-anchor")
    layout = get_figure_layout(figure)
    assert layout is not None
    assert len(layout.panels) == 1
    assert len(layout.panels[0].auxiliary_axes) == 1
    validate_figure_anatomy(figure)
