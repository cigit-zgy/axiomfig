from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "references" / "element-contracts"
TOPICS = ("axes", "marks", "ornaments", "annotations")


def _build(document: dict[str, object], dataset: dict[str, object]):
    from axiomfig.intent import build_intent_figure, parse_figure_intent

    intent = parse_figure_intent(document)
    return intent, build_intent_figure(intent, dataset)


def test_element_contract_files_form_one_progressive_disclosure_route() -> None:
    expected = {"index.md", *(f"{topic}.md" for topic in TOPICS)}
    assert {path.name for path in CONTRACT_ROOT.glob("*.md")} == expected
    index = (CONTRACT_ROOT / "index.md").read_text(encoding="utf-8")
    for topic in TOPICS:
        assert f"{topic}.md" in index
    assert "references/element-contracts/index.md" in (ROOT / "SKILL.md").read_text(
        encoding="utf-8"
    )


def test_element_topics_use_only_the_frozen_status_vocabulary() -> None:
    statuses = {"AVAILABLE", "INTERNAL_ONLY", "PLANNED", "NOT_SUPPORTED"}
    for topic in TOPICS:
        text = (CONTRACT_ROOT / f"{topic}.md").read_text(encoding="utf-8")
        assert "Scientific role" in text
        assert "Default source" in text
        assert "Runtime ownership" in text
        assert "Validation" in text
        found = set(re.findall(r"Adjustment status:\*{0,2}\s*`([A-Z_]+)`", text))
        assert found
        assert found <= statuses


def test_element_docs_do_not_copy_physical_numeric_defaults_or_expose_backends() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in CONTRACT_ROOT.glob("*.md"))
    duplicated_numeric_truth = (
        r"\b36\s*pt²",
        r"\b5\.2\s*pt",
        r"\b0\.8\s*pt",
        r"\b0\.6\s*pt",
        r"\b9\s*pt",
        r"\b6\s*pt",
        r"\b0\.72\b",
        r"\b90\s*mm",
        r"\b140\s*mm",
        r"\b190\s*mm",
    )
    assert not any(re.search(pattern, text) for pattern in duplicated_numeric_truth)
    assert not re.search(r"(use_)?(adjustText|textalloc|Kiwi)\s*[=:]", text, re.IGNORECASE)


def test_available_geometry_and_typography_execute_through_figure_intent() -> None:
    from axiomfig.intent import parse_figure_intent

    intent = parse_figure_intent(
        {"template": "line.single", "geometry": "double-column", "typography": "serif"}
    )
    assert intent.geometry == "double-column"
    assert intent.typography == "serif"


def test_available_axes_step_and_area_surfaces_execute() -> None:
    dataset = {"time": [0.0, 1.0, 2.0], "value": [1.0, 2.0, 1.5]}
    step_intent, step = _build(
        {
            "template": "line.step",
            "data": {"x": "time", "y": "value"},
            "semantics": {"where": "post", "xlabel": "Elapsed time", "ylabel": "State"},
        },
        dataset,
    )
    area_intent, area = _build(
        {
            "template": "line.area",
            "data": {"x": "time", "y": "value"},
            "semantics": {"baseline": 1.0},
        },
        dataset,
    )
    try:
        assert dict(step_intent.semantics)["where"] == "post"
        assert step.axes[0].lines[0].get_drawstyle() == "steps-post"
        assert step.axes[0].get_xlabel() == "Elapsed time"
        assert step.axes[0].get_ylabel() == "State"
        assert dict(area_intent.semantics)["baseline"] == 1.0
        vertices = area.axes[0].collections[0].get_paths()[0].vertices
        assert np.isclose(vertices[:, 1].min(), 1.0)
    finally:
        plt.close(step)
        plt.close(area)


def test_available_interval_and_reference_surfaces_execute() -> None:
    error_intent, errorbar = _build(
        {
            "template": "line.errorbar",
            "data": {"x": "x", "estimate": "estimate", "error": "error"},
            "semantics": {"uncertainty_type": "SE"},
        },
        {"x": [0, 1, 2], "estimate": [1.0, 1.5, 1.2], "error": [0.1, 0.2, 0.1]},
    )
    forest_intent, forest = _build(
        {
            "template": "estimation.forest",
            "data": {"label": "label", "estimate": "estimate", "interval": "interval"},
            "semantics": {"uncertainty_type": "95% CI", "reference": 1.0},
        },
        {"label": ["A", "B"], "estimate": [0.8, 1.3], "interval": [0.2, 0.3]},
    )
    try:
        assert dict(error_intent.semantics)["uncertainty_type"] == "SE"
        assert len(errorbar.axes[0].containers) >= 1
        assert dict(forest_intent.semantics)["reference"] == 1.0
        assert any(np.allclose(line.get_xdata(), [1.0, 1.0]) for line in forest.axes[0].lines)
    finally:
        plt.close(errorbar)
        plt.close(forest)


def test_available_marker_binning_and_value_label_surfaces_execute() -> None:
    _bubble_intent, bubble = _build(
        {
            "template": "scatter.bubble",
            "data": {"x": "x", "y": "y", "size": "size"},
            "semantics": {"size_label": "Biomass"},
        },
        {"x": [1, 2, 3], "y": [2, 1, 4], "size": [2, 4, 8]},
    )
    _hex_intent, hexbin = _build(
        {
            "template": "scatter.hexbin",
            "data": {"x": "x", "y": "y"},
            "semantics": {"gridsize": 7, "count_label": "Observations"},
        },
        {"x": np.linspace(0, 1, 30), "y": np.linspace(0, 1, 30) ** 2},
    )
    _bar_intent, bar = _build(
        {
            "template": "bar.vertical",
            "data": {"category": "category", "value": "value"},
            "semantics": {"value_labels": False},
        },
        {"category": ["A", "B"], "value": [1.0, 2.0]},
    )
    _hist_intent, histogram = _build(
        {
            "template": "distribution.histogram",
            "data": {"value": "value"},
            "semantics": {"bins": 4},
        },
        {"value": [0.0, 0.2, 0.4, 0.7, 0.9]},
    )
    try:
        sizes = bubble.axes[0].collections[0].get_sizes()
        assert len(np.unique(sizes)) == 3
        assert hexbin.axes[1].get_ylabel() == "Observations"
        assert not bar.axes[0].texts
        assert len(histogram.axes[0].patches) == 4
    finally:
        for figure in (bubble, hexbin, bar, histogram):
            plt.close(figure)


def test_available_color_annotation_and_label_surfaces_execute() -> None:
    _heatmap_intent, heatmap = _build(
        {
            "template": "heatmap.basic",
            "data": {
                "matrix": "matrix",
                "row_labels": "rows",
                "column_labels": "columns",
                "annotations": "annotations",
            },
            "semantics": {
                "color_semantics": "diverging",
                "center": 0.0,
                "colorbar_label": "Signed response",
            },
        },
        {
            "matrix": [[-1.0, 0.2], [0.5, 1.0]],
            "rows": ["R1", "R2"],
            "columns": ["C1", "C2"],
            "annotations": [["low", "mid"], ["mid", "high"]],
        },
    )
    _ordination_intent, ordination = _build(
        {
            "template": "ordination.pca_scores",
            "data": {
                "coordinates": "coordinates",
                "explained_variance": "variance",
                "sample_labels": "labels",
            },
        },
        {
            "coordinates": [[-1.0, 0.2], [0.5, 1.0], [1.1, -0.4]],
            "variance": [0.55, 0.25],
            "labels": ["S1", "S2", "S3"],
        },
    )
    try:
        assert heatmap.axes[0].images[0].norm.vcenter == 0.0
        assert heatmap.axes[1].get_ylabel() == "Signed response"
        assert {text.get_text() for text in heatmap.axes[0].texts} == {
            "low",
            "mid",
            "high",
        }
        assert {text.get_text() for text in ordination.axes[0].texts} >= {"S1", "S2", "S3"}
    finally:
        plt.close(heatmap)
        plt.close(ordination)


def test_available_contour_level_and_group_legend_surfaces_execute() -> None:
    _contour_intent, contour = _build(
        {
            "template": "field.contour",
            "data": {"x_grid": "x", "y_grid": "y", "z": "z"},
            "semantics": {
                "color_semantics": "sequential",
                "levels": [0.0, 0.5, 1.0],
                "colorbar_label": "Concentration",
            },
        },
        {"x": [0.0, 1.0], "y": [0.0, 1.0], "z": [[0.0, 0.5], [0.5, 1.0]]},
    )
    _group_intent, grouped = _build(
        {
            "template": "scatter.grouped",
            "data": {"x": "x", "y": "y", "group": "group"},
        },
        {"x": [1, 2, 3, 4], "y": [1, 3, 2, 4], "group": ["A", "A", "B", "B"]},
    )
    try:
        assert contour.axes[1].get_ylabel() == "Concentration"
        assert len(contour.axes[0].collections) >= 2
        grouped.canvas.draw()
        from axiomfig.ornaments import finalize_ornaments

        finalize_ornaments(grouped)
        legend = grouped.axes[0].get_legend()
        assert legend is not None
        assert {text.get_text() for text in legend.get_texts()} == {"A", "B"}
    finally:
        plt.close(contour)
        plt.close(grouped)


def test_available_mantel_adjustment_surface_executes() -> None:
    intent, figure = _build(
        {
            "template": "association.mantel",
            "data": {
                "correlation_matrix": "matrix",
                "labels": "labels",
                "links": "links",
            },
            "semantics": {
                "matrix_method": "ellipse",
                "matrix_region": "upper_right",
                "diagonal": "show",
                "coupling": False,
            },
        },
        {
            "matrix": [[1.0, 0.3], [0.3, 1.0]],
            "labels": ["A", "B"],
            "links": [{"source": "S", "target": "A", "mantel_r": 0.4, "p_value": 0.01}],
        },
    )
    try:
        assert dict(intent.semantics)["matrix_method"] == "ellipse"
        methods = {
            artist._axiomfig_method
            for artist in figure.axes[0].get_children()
            if artist.get_gid() == "axiomfig-mantel-glyph"
        }
        assert methods == {"ellipse"}
    finally:
        plt.close(figure)


def test_element_contract_manual_routing_fixture_has_twelve_cases() -> None:
    path = ROOT / "tests" / "evaluation" / "element_adjustment" / "manual_routing.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert len(document["cases"]) == 12
    assert {case["topic"] for case in document["cases"]} == {
        "none",
        "axes",
        "marks",
        "ornaments",
        "annotations",
    }
