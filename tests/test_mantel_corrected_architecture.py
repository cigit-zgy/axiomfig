from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import colors as mcolors
from matplotlib.collections import PathCollection
from matplotlib.patches import Circle

from axiomfig.config import load_contracts
from axiomfig.style import apply_contract_context, series_style
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.composition import normalize_composition
from axiomfig.templates.association.mantel.geometry import cell_center
from axiomfig.templates.association.mantel.glyphs import draw_glyph
from axiomfig.templates.association.mantel.styling import mantel_p_style


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


def _node_center(node: PathCollection) -> tuple[float, float]:
    x, y = node.get_offsets()[0]
    return float(x), float(y)


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


@pytest.mark.parametrize(
    ("matrix_type", "source_sign", "label_offset_sign", "horizontal", "vertical"),
    [
        ("lower", 1, 1, "left", "bottom"),
        ("upper", -1, -1, "right", "top"),
    ],
)
def test_node_layer_connects_every_link_inside_the_complementary_triangle(
    matrix_type: str,
    source_sign: int,
    label_offset_sign: int,
    horizontal: str,
    vertical: str,
) -> None:
    figure = build_template("association/mantel", matrix_type=matrix_type)
    figure.canvas.draw()
    geometry = figure._axiomfig_mantel_geometry
    diagonal = geometry.bounds.x0 + geometry.bounds.y0 + geometry.bounds.size
    source_nodes = _artists(figure, "axiomfig-mantel-source-node")
    target_nodes = _artists(figure, "axiomfig-mantel-target-node")
    source_labels = _artists(figure, "axiomfig-mantel-source-label")
    links = _artists(figure, "axiomfig-mantel-link")

    assert len(source_nodes) == len(geometry.source_positions)
    assert len(target_nodes) == len(geometry.target_positions)
    assert len(source_labels) == len(geometry.source_positions)
    assert not _artists(figure, "axiomfig-mantel-target-label")
    for node in source_nodes:
        x, y = _node_center(node)
        assert source_sign * (x + y - diagonal) > 0.0
    for node in target_nodes:
        x, y = _node_center(node)
        assert x + y == pytest.approx(diagonal)
    label_positions = {tuple(label.get_position()) for label in source_labels}
    assert len(label_positions) == 1
    label_x, label_y = label_positions.pop()
    assert label_x * label_offset_sign > 0.0
    assert label_y * label_offset_sign > 0.0
    for label in source_labels:
        assert label.get_horizontalalignment() == horizontal
        assert label.get_verticalalignment() == vertical
    for link in links:
        vertices = link.get_path().vertices
        np.testing.assert_allclose(vertices[0], geometry.source_positions[link._axiomfig_source])
        np.testing.assert_allclose(vertices[-1], geometry.target_positions[link._axiomfig_target])
    plt.close(figure)


def test_node_layer_reuses_physical_scatter_contract() -> None:
    with apply_contract_context(geometry="onehalf-column", typography="sans"):
        figure = build_template("association/mantel")
        figure.canvas.draw()
        source_nodes = _artists(figure, "axiomfig-mantel-source-node")
        target_nodes = _artists(figure, "axiomfig-mantel-target-node")
        expected_source_colors = [
            mcolors.to_rgba(str(series_style(index, include_marker=False)["color"]))[:3]
            for index in range(len(source_nodes))
        ]

    scatter = load_contracts().style["plots"]["scatter"]
    assert all(isinstance(node, PathCollection) for node in (*source_nodes, *target_nodes))
    assert [node.get_sizes()[0] for node in source_nodes] == pytest.approx(
        [float(scatter["marker_size_pt2"]) * 1.35] * len(source_nodes)
    )
    assert [node.get_sizes()[0] for node in target_nodes] == pytest.approx(
        [float(scatter["marker_size_pt2"])] * len(target_nodes)
    )
    assert [tuple(node.get_facecolors()[0, :3]) for node in source_nodes] == pytest.approx(
        expected_source_colors
    )
    for node in (*source_nodes, *target_nodes):
        assert node.get_facecolors()[0, 3] == pytest.approx(float(scatter["alpha"]))
        assert tuple(node.get_edgecolors()[0]) == pytest.approx((0.0, 0.0, 0.0, 1.0))
        assert node.get_linewidths()[0] == pytest.approx(0.6)
    plt.close(figure)


def test_canonical_defaults_use_circle_and_three_bin_p_value_grammar() -> None:
    composition = normalize_composition({}, size=5)
    assert composition.glyphs[0].method == "circle"
    assert composition.coupling.p_value_mode == "canonical"

    assert mantel_p_style(0.005)["bin"] == "p<0.01"
    assert mantel_p_style(0.02)["bin"] == "0.01<=p<0.05"
    assert mantel_p_style(0.20)["bin"] == "p>=0.05"
    assert mantel_p_style(0.0005, mode="detailed")["bin"] == "p<0.001"


def test_mantel_legend_bins_follow_the_executable_style_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legend samples and labels must not maintain a parallel bin table."""
    from axiomfig.templates.association.mantel import legends, styling

    contract = styling.mantel_plot_contract()
    custom = {
        **contract,
        "links": {
            **contract["links"],
            "strength_breaks": [0.2, 0.6],
            "p_value_modes": {
                **contract["links"]["p_value_modes"],
                "canonical": {
                    **contract["links"]["p_value_modes"]["canonical"],
                    "breaks": [0.02, 0.08],
                },
            },
        },
    }
    monkeypatch.setattr(styling, "mantel_plot_contract", lambda: custom)

    strength, p_values = legends._legend_handles("canonical")

    assert [handle.get_label() for handle in strength] == [
        "< 0.20",
        "0.20-0.60",
        ">= 0.60",
    ]
    assert [handle.get_label() for handle in p_values] == ["< 0.02", "0.02-0.08", ">= 0.08"]


def test_mantel_legend_spacing_comes_from_global_and_family_yaml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from axiomfig import ornaments
    from axiomfig.templates.association.mantel import legends, styling

    contracts = load_contracts()
    style = dict(contracts.style)
    style["legend"] = {
        **contracts.style["legend"],
        "handlelength": 2.3,
        "borderaxespad": 0.7,
    }
    monkeypatch.setattr(ornaments, "load_contracts", lambda: SimpleNamespace(style=style))

    contract = styling.mantel_plot_contract()
    custom = {
        **contract,
        "ornaments": {
            **contract["ornaments"],
            "legend": {
                "borderpad": 0.4,
                "labelspacing": 0.31,
                "handletextpad": 0.46,
                "columnspacing": 0.76,
            },
        },
    }
    monkeypatch.setattr(legends, "mantel_plot_contract", lambda: custom)

    figure, axis = plt.subplots()
    strength, p_values = legends._create_link_legends(
        axis,
        strength_anchor=(0.0, 0.0),
        p_anchor=(0.0, 0.2),
        transform=axis.transAxes,
        p_value_mode="canonical",
    )

    for legend in (strength, p_values):
        assert legend.handlelength == pytest.approx(2.3)
        assert legend.borderaxespad == pytest.approx(0.7)
        assert legend.borderpad == pytest.approx(0.4)
        assert legend.labelspacing == pytest.approx(0.31)
        assert legend.handletextpad == pytest.approx(0.46)
        assert legend.columnspacing == pytest.approx(0.76)
    plt.close(figure)


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
