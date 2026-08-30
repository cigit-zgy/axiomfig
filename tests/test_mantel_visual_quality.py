from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.quality import measure_mantel_visual_quality


def _density_case(size: int) -> dict[str, object]:
    labels = tuple(f"Variable {index + 1:02d}" for index in range(size))
    coordinates = np.linspace(-1.0, 1.0, size)
    matrix = np.clip(np.cos(np.subtract.outer(coordinates, coordinates) * 1.8), -1.0, 1.0)
    np.fill_diagonal(matrix, 1.0)
    links = tuple(
        {
            "source": ("Water chemistry", "Nutrient profile", "Process state")[index % 3],
            "target": label,
            "mantel_r": 0.16 + 0.04 * (index % 12),
            "p_value": (0.0005, 0.005, 0.025, 0.12)[index % 4],
        }
        for index, label in enumerate(labels)
    )
    return {"correlation_matrix": matrix, "labels": labels, "links": links}


@pytest.mark.parametrize("size", [10, 15, 20])
def test_reference_density_figures_meet_mantel_visual_quality_gates(size: int) -> None:
    figure = build_template("association/mantel", **_density_case(size))
    figure.canvas.draw()
    metrics = measure_mantel_visual_quality(figure)

    assert metrics.matrix_occupancy_ratio >= 0.14
    assert metrics.visible_content_occupancy_ratio >= 0.50
    assert metrics.dead_space_ratio <= 0.50
    assert metrics.source_rail_min_distance_pt >= 7.0
    assert metrics.source_label_clearance_pt >= 1.0
    assert metrics.legend_overlap_count == 0
    assert metrics.legend_matrix_overlap_count == 0
    assert metrics.label_overlap_count == 0
    assert metrics.link_matrix_intersection_count == 0
    assert metrics.link_label_intersection_count == 0
    assert metrics.route_midpoint_separation_pt >= 0.8
    plt.close(figure)
