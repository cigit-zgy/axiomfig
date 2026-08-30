from __future__ import annotations

from contextlib import contextmanager
from itertools import pairwise

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.transforms import Bbox

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.layout import apply_output_margin, invalidate_panel_layout
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.gallery_cases import (
    MANTEL_GALLERY_GEOMETRIES,
    mantel_gallery_values,
)
from axiomfig.typography import apply_figure_typography, discover_fonts
from axiomfig.validation import FigureAnatomyError, validate_figure_anatomy


def _artists(figure, gid: str):
    return [
        artist for axis in figure.axes for artist in axis.get_children() if artist.get_gid() == gid
    ]


@contextmanager
def _gallery_figure(case_id: str, typography: str = "sans"):
    geometry = MANTEL_GALLERY_GEOMETRIES[case_id]
    discover_fonts(typography)
    params = build_rcparams(load_contracts(), geometry=geometry, typography=typography)
    with mpl.rc_context(rc=params):
        figure = build_template("association/mantel", **mantel_gallery_values(case_id))
        figure.set_size_inches(params["figure.figsize"], forward=False)
        apply_figure_typography(figure, mode=typography)
        invalidate_panel_layout(figure)
        apply_output_margin(figure)
        apply_figure_typography(figure, mode=typography)
        figure.canvas.draw()
        try:
            yield figure
        finally:
            plt.close(figure)


def _marker_bbox(collection, axis, dpi: float) -> Bbox:
    center = axis.transData.transform(collection.get_offsets()[0])
    radius_pt = float(np.sqrt(collection.get_sizes()[0])) / 2.0
    radius_pt += float(collection.get_linewidths()[0]) / 2.0
    radius_px = radius_pt * dpi / 72.0
    return Bbox.from_extents(
        center[0] - radius_px,
        center[1] - radius_px,
        center[0] + radius_px,
        center[1] + radius_px,
    )


def _circle_to_bbox_gap(marker: Bbox, label: Bbox) -> float:
    center = np.asarray(((marker.x0 + marker.x1) / 2.0, (marker.y0 + marker.y1) / 2.0))
    nearest = np.asarray(
        (
            float(np.clip(center[0], label.x0, label.x1)),
            float(np.clip(center[1], label.y0, label.y1)),
        )
    )
    radius = marker.width / 2.0
    return max(0.0, float(np.linalg.norm(nearest - center) - radius))


def _source_group_boxes(figure) -> dict[str, Bbox]:
    axis = figure.axes[0]
    renderer = figure.canvas.get_renderer()
    node_boxes = {
        node._axiomfig_source: _marker_bbox(node, axis, figure.dpi)
        for node in _artists(figure, "axiomfig-mantel-source-node")
    }
    label_boxes = {
        label._axiomfig_source: label.get_window_extent(renderer)
        for label in _artists(figure, "axiomfig-mantel-source-label")
    }
    return {source: Bbox.union((node_boxes[source], label_boxes[source])) for source in node_boxes}


def _projected_interval(box: Bbox, direction: np.ndarray) -> tuple[float, float]:
    corners = np.asarray(((box.x0, box.y0), (box.x0, box.y1), (box.x1, box.y0), (box.x1, box.y1)))
    projected = corners @ direction
    return float(np.min(projected)), float(np.max(projected))


@pytest.mark.parametrize("case_id", ["canonical", "dense"])
def test_source_label_visible_edge_gap_is_physical_contract(case_id: str) -> None:
    with _gallery_figure(case_id) as figure:
        axis = figure.axes[0]
        renderer = figure.canvas.get_renderer()
        nodes = {
            node._axiomfig_source: node for node in _artists(figure, "axiomfig-mantel-source-node")
        }
        labels = {
            label._axiomfig_source: label
            for label in _artists(figure, "axiomfig-mantel-source-label")
        }
        gaps = [
            _circle_to_bbox_gap(
                _marker_bbox(nodes[source], axis, figure.dpi),
                labels[source].get_window_extent(renderer),
            )
            * 72.0
            / figure.dpi
            for source in nodes
        ]

    assert gaps == pytest.approx([1.5] * len(gaps), abs=0.5)


@pytest.mark.parametrize("case_id", ["canonical", "dense"])
def test_source_group_footprints_are_compactly_packed(case_id: str) -> None:
    with _gallery_figure(case_id) as figure:
        geometry = figure._axiomfig_mantel_geometry
        boxes = _source_group_boxes(figure)
        target = figure.axes[0].transData.transform(
            np.asarray(tuple(geometry.target_positions.values()), dtype=float)
        )
        tangent = target[-1] - target[0]
        tangent /= np.linalg.norm(tangent)
        intervals = sorted(_projected_interval(box, tangent) for box in boxes.values())
        gaps = [(second[0] - first[1]) * 72.0 / figure.dpi for first, second in pairwise(intervals)]

    assert all(gap >= 4.0 - 0.5 for gap in gaps)
    assert all(gap <= 4.0 + 1.0 for gap in gaps)


@pytest.mark.parametrize("case_id", ["canonical", "dense"])
def test_source_rail_is_maximized_toward_outer_corner(case_id: str) -> None:
    with _gallery_figure(case_id) as figure:
        geometry = figure._axiomfig_mantel_geometry
        axis = figure.axes[0]
        boxes = tuple(_source_group_boxes(figure).values())
        lower_left, upper_right = axis.transData.transform(
            (
                (geometry.bounds.x0, geometry.bounds.y0),
                (geometry.bounds.x1, geometry.bounds.y1),
            )
        )
        square = Bbox.from_extents(*lower_left, *upper_right)
        clearance_pt = min(
            min(square.x1 - box.x1, square.y1 - box.y1) * 72.0 / figure.dpi for box in boxes
        )

    assert clearance_pt >= 3.0 - 0.5
    assert clearance_pt <= 3.0 + 0.5


def test_source_packing_tokens_replace_center_offset() -> None:
    matrix = load_contracts().style["plots"]["mantel"]["matrix"]

    assert matrix["source_label_gap_pt"] == 1.5
    assert matrix["source_group_gap_pt"] == 4.0
    assert matrix["source_boundary_padding_pt"] == 3.0
    assert "source_label_offset_pt" not in matrix


@pytest.mark.parametrize(
    ("case_id", "typography"),
    (
        ("canonical", "sans"),
        ("dense", "sans"),
        ("long_labels", "sans"),
        ("multigroup", "sans"),
        ("canonical", "serif"),
    ),
)
def test_primary_visual_matrix_is_physically_square(case_id: str, typography: str) -> None:
    with _gallery_figure(case_id, typography) as figure:
        axis = figure.axes[0]
        bounds = figure._axiomfig_mantel_geometry.bounds
        corners = axis.transData.transform(((bounds.x0, bounds.y0), (bounds.x1, bounds.y1)))
        width_px = float(corners[1, 0] - corners[0, 0])
        height_px = float(corners[1, 1] - corners[0, 1])
        cell_width_px = width_px / bounds.size
        cell_height_px = height_px / bounds.size

    assert abs(width_px - height_px) <= 0.5
    assert abs(cell_width_px - cell_height_px) <= 0.1


def test_runtime_validation_rejects_a_distorted_primary_visual_square() -> None:
    with _gallery_figure("canonical") as figure:
        figure.axes[0].set_aspect("auto")
        figure.canvas.draw()

        with pytest.raises(FigureAnatomyError, match="primary visual square"):
            validate_figure_anatomy(figure)


def test_global_vertical_colorbar_contract_is_canonical_source() -> None:
    vertical = load_contracts().style["colorbar"]["vertical"]

    assert vertical["width_pt"] == 9.0
    assert vertical["gap_pt"] == 6.0
    assert vertical["length_fraction"] == 0.72
    assert vertical["alignment"] == "center"
    assert vertical["tick_side"] == "right"
    assert vertical["label_side"] == "right"


@pytest.mark.parametrize("case_id", ["canonical", "dense", "long_labels"])
def test_pearson_colorbar_uses_global_rendered_geometry(case_id: str) -> None:
    with _gallery_figure(case_id) as figure:
        axis, colorbar_axis = figure.axes
        bounds = figure._axiomfig_mantel_geometry.bounds
        lower_left, upper_right = axis.transData.transform(
            ((bounds.x0, bounds.y0), (bounds.x1, bounds.y1))
        )
        square = Bbox.from_extents(*lower_left, *upper_right)
        colorbar = colorbar_axis.bbox
        scale = 72.0 / figure.dpi

        assert colorbar.x0 > square.x1
        assert (colorbar.x0 - square.x1) * scale == pytest.approx(6.0, abs=0.5)
        assert colorbar.width * scale == pytest.approx(9.0, abs=0.5)
        assert colorbar.height / square.height == pytest.approx(0.72, abs=0.01)
        assert (colorbar.y0 + colorbar.y1) / 2.0 == pytest.approx(
            (square.y0 + square.y1) / 2.0,
            abs=0.5,
        )
        assert tuple(colorbar_axis.get_yticks()) == pytest.approx((-1.0, -0.5, 0.0, 0.5, 1.0))
        assert colorbar_axis.get_ylabel() == "Pearson r"
