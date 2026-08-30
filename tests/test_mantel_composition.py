from __future__ import annotations

import re
from itertools import product
from pathlib import Path as FilePath

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.path import Path
from matplotlib.transforms import Bbox

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.style import axiom_colormap, mantel_p_style, palette_color
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.composition import (
    ClusterOutlineOverlay,
    CoefficientOverlay,
    ConfidenceIntervalOverlay,
    SignificanceOverlay,
    normalize_composition,
)
from axiomfig.templates.association.mantel.data import GLYPH_METHODS
from axiomfig.templates.association.mantel.geometry import solve_geometry
from axiomfig.templates.association.mantel.matrix import select_matrix_cells
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_figure_anatomy


def _case(size: int = 5) -> dict[str, object]:
    labels = tuple(f"V{index + 1:02d}" for index in range(size))
    coordinates = np.linspace(-1.0, 1.0, size)
    matrix = np.clip(np.cos(np.subtract.outer(coordinates, coordinates) * 1.35), -1.0, 1.0)
    np.fill_diagonal(matrix, 1.0)
    links = tuple(
        {
            "source": f"Source {index % 3 + 1}",
            "target": labels[index],
            "mantel_r": min(0.9, 0.18 + 0.05 * index),
            "p_value": (0.0005, 0.005, 0.025, 0.12)[index % 4],
        }
        for index in range(size)
    )
    return {"correlation_matrix": matrix, "labels": labels, "links": links}


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


def test_default_composition_has_explicit_independent_layers() -> None:
    composition = normalize_composition({}, size=5)

    assert composition.matrix.matrix_type == "lower"
    assert composition.matrix.diagonal == "hide"
    assert [(layer.region, layer.method) for layer in composition.glyphs] == [("lower", "square")]
    assert composition.overlays == ()
    assert composition.coupling.enabled is True
    assert composition.coupling.nonsignificant == "fade"


def test_mixed_is_two_glyph_layers_not_a_special_finished_picture() -> None:
    for lower, upper in product(GLYPH_METHODS, repeat=2):
        composition = normalize_composition(
            {
                "matrix_type": "mixed",
                "lower_method": lower,
                "upper_method": upper,
                "diagonal": "hide",
            },
            size=4,
        )
        assert [(layer.region, layer.method) for layer in composition.glyphs] == [
            ("lower", lower),
            ("upper", upper),
        ]


def test_statistical_overlays_are_normalized_as_an_ordered_layer_tuple() -> None:
    composition = normalize_composition(
        {
            "order": "hclust",
            "clusters": 2,
            "coefficients": True,
            "coefficient_format": "percent",
            "significance_mode": "label_sig",
            "ci_mode": "rect",
        },
        size=5,
    )

    assert composition.overlays == (
        ConfidenceIntervalOverlay(mode="rect"),
        CoefficientOverlay(number_format="percent"),
        SignificanceOverlay(mode="label_sig", thresholds=(0.05, 0.01, 0.001)),
        ClusterOutlineOverlay(cluster_count=2),
    )


@pytest.mark.parametrize(
    ("matrix_type", "expected"),
    (("full", 12), ("lower", 6), ("upper", 6), ("mixed", 12)),
)
def test_matrix_mask_is_independent_from_glyph_method(matrix_type: str, expected: int) -> None:
    first = normalize_composition(
        {"matrix_type": matrix_type, "matrix_method": "circle", "diagonal": "hide"},
        size=4,
    )
    second = normalize_composition(
        {"matrix_type": matrix_type, "matrix_method": "pie", "diagonal": "hide"},
        size=4,
    )

    first_cells = select_matrix_cells(4, first.matrix)
    second_cells = select_matrix_cells(4, second.matrix)
    assert [(cell.row, cell.column, cell.region) for cell in first_cells] == [
        (cell.row, cell.column, cell.region) for cell in second_cells
    ]
    assert len(first_cells) == expected


def test_lower_and_upper_target_rails_are_geometric_mirrors() -> None:
    labels = ("A", "B", "C", "D")
    sources = ("Source 1", "Source 2")
    lower = solve_geometry(labels, sources, matrix_type="lower")
    upper = solve_geometry(labels, sources, matrix_type="upper")

    lower_points = np.asarray([lower.target_rail.anchors[label] for label in labels])
    upper_points = np.asarray([upper.target_rail.anchors[label] for label in labels])
    assert np.all(np.diff(lower_points[:, 0]) > 0.0)
    assert np.all(np.diff(lower_points[:, 1]) > 0.0)
    assert np.all(np.diff(upper_points[:, 0]) > 0.0)
    assert np.all(np.diff(upper_points[:, 1]) < 0.0)
    np.testing.assert_allclose(
        lower_points[:, 0] - lower.bounds.x0,
        upper_points[:, 0] - upper.bounds.x0,
    )
    np.testing.assert_allclose(
        lower_points[:, 1] - lower.bounds.y0,
        upper.bounds.y1 - upper_points[:, 1],
    )
    assert lower.source_region.corner == "lower-left"
    assert upper.source_region.corner == "upper-left"


@pytest.mark.parametrize("matrix_type", ["lower", "upper"])
def test_coupling_uses_one_rail_normal_cubic_and_exact_target_endpoints(
    matrix_type: str,
) -> None:
    figure = build_template("association/mantel", **_case(6), matrix_type=matrix_type)
    figure.canvas.draw()
    links = _artists(figure, "axiomfig-mantel-link")
    anchors = {
        artist._axiomfig_target: tuple(artist.center)
        for artist in _artists(figure, "axiomfig-mantel-target-anchor")
    }

    assert links
    for link in links:
        assert tuple(link.get_path().codes) == (
            Path.MOVETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
        )
        assert link._axiomfig_route_model == "rail-normal-cubic"
        np.testing.assert_allclose(link.get_path().vertices[-1], anchors[link._axiomfig_target])
    plt.close(figure)


@pytest.mark.parametrize("matrix_type", ["lower", "upper"])
def test_coupling_routes_clear_visible_matrix_glyphs(matrix_type: str) -> None:
    figure = build_template("association/mantel", **_case(8), matrix_type=matrix_type)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    cell_boxes = [
        artist.get_window_extent(renderer) for artist in _artists(figure, "axiomfig-mantel-glyph")
    ]

    for link in _artists(figure, "axiomfig-mantel-link"):
        route_points = [
            tuple(vertices[-2:])
            for vertices, _ in link.get_path().iter_segments(
                transform=link.get_transform(),
                curves=False,
                simplify=False,
            )
        ]
        for cell in cell_boxes:
            interior = Bbox.from_extents(cell.x0 + 1.0, cell.y0 + 1.0, cell.x1 - 1.0, cell.y1 - 1.0)
            assert not any(interior.contains(*point) for point in route_points)
    plt.close(figure)


def test_pearson_and_mantel_colors_resolve_from_axiom_palette_tokens() -> None:
    cmap = axiom_colormap("axiom_diverging")
    np.testing.assert_allclose(cmap(0.0), (*_rgba("axiom_classic", "AxiomRed")[:3], 1.0))
    np.testing.assert_allclose(cmap(0.5), (*_rgba("axiom_neutral", "AxiomWhite")[:3], 1.0))
    np.testing.assert_allclose(cmap(1.0), (*_rgba("axiom_classic", "AxiomBlue")[:3], 1.0))

    expected = (
        (0.0005, "AxiomOrange"),
        (0.005, "AxiomGreen"),
        (0.025, "AxiomPurple"),
        (0.10, "AxiomGrey"),
    )
    for value, token in expected:
        assert mantel_p_style(value)["color"] == palette_color(token)


def test_mantel_engine_contains_no_raw_hex_or_matplotlib_rdbu_palette() -> None:
    root = (
        FilePath(__file__).resolve().parents[1]
        / "src"
        / "axiomfig"
        / "templates"
        / "association"
        / "mantel"
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.py")))

    assert "RdBu" not in source
    assert re.search(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?\b", source) is None


def _rgba(palette: str, token: str) -> tuple[float, float, float, float]:
    from matplotlib.colors import to_rgba

    return to_rgba(palette_color(token, palette_name=palette))


def test_ci_and_glyph_are_composed_in_the_same_cells() -> None:
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
        ci_mode="rect",
        matrix_type="lower",
        diagonal="hide",
        coupling=False,
    )
    figure.canvas.draw()
    assert len(_artists(figure, "axiomfig-mantel-glyph")) == 6
    assert len(_artists(figure, "axiomfig-mantel-confidence-interval")) == 6
    plt.close(figure)


def test_full_matrix_long_labels_fit_the_owned_panel_footprint() -> None:
    values = _case(10)
    values["labels"] = (
        "Dissolved oxygen",
        "Ammonium nitrogen",
        "Nitrate nitrogen",
        "Total nitrogen",
        "Orthophosphate",
        "Total phosphorus",
        "Chemical oxygen demand",
        "Acidity",
        "Temperature",
        "Redox potential",
    )
    values["links"] = (
        {
            "source": "Source 1",
            "target": "Dissolved oxygen",
            "mantel_r": 0.4,
            "p_value": 0.01,
        },
    )

    params = build_rcparams(load_contracts(), geometry="onehalf-column", typography="sans")
    discover_fonts("sans")
    with mpl.rc_context(rc=params):
        figure = build_template(
            "association/mantel",
            **values,
            matrix_type="full",
            matrix_method="circle",
            diagonal="show",
            coupling=False,
        )
        figure.set_size_inches(params["figure.figsize"], forward=False)
        validate_figure_anatomy(figure)
        plt.close(figure)
