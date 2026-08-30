"""Orchestrate normalized Mantel data through independent visual layers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from axiomfig.layout import add_panel_axes, create_panel_grid, solve_panel_layout
from axiomfig.style import axiom_colormap, mantel_plot_contract
from axiomfig.templates.association.mantel.coupling import render_coupling_layer
from axiomfig.templates.association.mantel.data import MantelData, normalize_inputs
from axiomfig.templates.association.mantel.geometry import (
    MantelLayoutMeasurements,
    measure_text_extents,
    solve_geometry,
)
from axiomfig.templates.association.mantel.glyphs import render_glyph_layer
from axiomfig.templates.association.mantel.legends import (
    measure_link_legends,
    render_colorbar,
    render_ornament_layer,
)
from axiomfig.templates.association.mantel.matrix import render_matrix_layer
from axiomfig.templates.association.mantel.nodes import render_node_layer
from axiomfig.templates.association.mantel.ordering import order_variables
from axiomfig.templates.association.mantel.overlays import (
    render_statistical_layers,
    visible_glyph_cells,
)

_CANONICAL_LABELS = (
    "DO",
    "NH4-N",
    "NO3-N",
    "TN",
    "PO4-P",
    "TP",
    "COD",
    "pH",
    "Temperature",
    "ORP",
)
_CANONICAL_LOADINGS = np.asarray(
    (
        (0.90, -0.20, 0.10),
        (-0.78, 0.42, 0.06),
        (0.64, 0.48, -0.12),
        (-0.58, 0.68, 0.18),
        (-0.44, 0.22, 0.72),
        (-0.50, 0.30, 0.66),
        (-0.74, -0.18, 0.34),
        (0.28, -0.56, 0.18),
        (0.20, 0.08, -0.78),
        (0.72, -0.38, -0.08),
    )
)


def _canonical_correlation() -> np.ndarray:
    covariance = _CANONICAL_LOADINGS @ _CANONICAL_LOADINGS.T + np.diag(
        np.linspace(0.20, 0.34, len(_CANONICAL_LABELS))
    )
    scale = np.sqrt(np.diag(covariance))
    correlation = covariance / np.outer(scale, scale)
    np.fill_diagonal(correlation, 1.0)
    return correlation


_CANONICAL_LINKS = (
    {"source": "Water chemistry", "target": "DO", "mantel_r": 0.67, "p_value": 0.0004},
    {"source": "Water chemistry", "target": "NH4-N", "mantel_r": -0.53, "p_value": 0.004},
    {"source": "Water chemistry", "target": "NO3-N", "mantel_r": 0.43, "p_value": 0.018},
    {"source": "Water chemistry", "target": "TN", "mantel_r": 0.31, "p_value": 0.071},
    {"source": "Water chemistry", "target": "pH", "mantel_r": 0.19, "p_value": 0.21},
    {"source": "Nutrient profile", "target": "NH4-N", "mantel_r": 0.58, "p_value": 0.0008},
    {"source": "Nutrient profile", "target": "NO3-N", "mantel_r": -0.46, "p_value": 0.006},
    {"source": "Nutrient profile", "target": "TN", "mantel_r": 0.71, "p_value": 0.024},
    {"source": "Nutrient profile", "target": "PO4-P", "mantel_r": 0.23, "p_value": 0.083},
    {"source": "Nutrient profile", "target": "TP", "mantel_r": 0.39, "p_value": 0.031},
    {"source": "Process state", "target": "COD", "mantel_r": 0.62, "p_value": 0.0002},
    {"source": "Process state", "target": "pH", "mantel_r": 0.36, "p_value": 0.009},
    {"source": "Process state", "target": "Temperature", "mantel_r": -0.42, "p_value": 0.044},
    {"source": "Process state", "target": "ORP", "mantel_r": 0.56, "p_value": 0.062},
    {"source": "Process state", "target": "DO", "mantel_r": 0.21, "p_value": 0.14},
)


def canonical_mantel_values() -> dict[str, object]:
    return {
        "correlation_matrix": _canonical_correlation(),
        "labels": _CANONICAL_LABELS,
        "links": _CANONICAL_LINKS,
    }


def _provided(name: str, value: object | None, target: dict[str, object]) -> None:
    if value is not None:
        target[name] = value


def _ordered_data(data: MantelData, indices: np.ndarray) -> MantelData:
    return MantelData(
        correlation_matrix=data.correlation_matrix[np.ix_(indices, indices)],
        labels=tuple(data.labels[index] for index in indices),
        links=data.links,
        p_values=(data.p_values[np.ix_(indices, indices)] if data.p_values is not None else None),
        lower_ci=(data.lower_ci[np.ix_(indices, indices)] if data.lower_ci is not None else None),
        upper_ci=(data.upper_ci[np.ix_(indices, indices)] if data.upper_ci is not None else None),
    )


def _source_groups(data: MantelData) -> tuple[str, ...]:
    target_order = {label: index for index, label in enumerate(data.labels)}
    grouped: dict[str, list[int]] = defaultdict(list)
    first_seen: dict[str, int] = {}
    for link in data.links:
        first_seen.setdefault(link.source, len(first_seen))
        grouped[link.source].append(target_order[link.target])
    return tuple(
        sorted(
            grouped,
            key=lambda source: (
                float(np.mean(grouped[source])),
                first_seen[source],
                source,
            ),
        )
    )


def build_mantel(
    correlation_matrix: object | None = None,
    labels: object | None = None,
    links: object | None = None,
    p_values: object | None = None,
    lower_ci: object | None = None,
    upper_ci: object | None = None,
    matrix_method: object | None = None,
    matrix_type: object | None = None,
    matrix_region: object | None = None,
    diagonal: object | None = None,
    order: object | None = None,
    hclust_method: object | None = None,
    clusters: object | None = None,
    lower_method: object | None = None,
    upper_method: object | None = None,
    coefficients: object | None = None,
    coefficient_format: object | None = None,
    significance_mode: object | None = None,
    significance_thresholds: object | None = None,
    ci_mode: object | None = None,
    nonsignificant_links: object | None = None,
    link_width_mode: object | None = None,
    p_value_mode: object | None = None,
    show_nonsignificant: object | None = None,
    coupling: object | None = None,
) -> Figure:
    if correlation_matrix is None and labels is None and links is None:
        values = canonical_mantel_values()
    elif correlation_matrix is None or labels is None or links is None:
        raise ValueError("Mantel requires correlation_matrix, labels, and links together")
    else:
        values = {"correlation_matrix": correlation_matrix, "labels": labels, "links": links}
    for name, value in (
        ("p_values", p_values),
        ("lower_ci", lower_ci),
        ("upper_ci", upper_ci),
        ("matrix_method", matrix_method),
        ("matrix_type", matrix_type),
        ("matrix_region", matrix_region),
        ("diagonal", diagonal),
        ("order", order),
        ("hclust_method", hclust_method),
        ("clusters", clusters),
        ("lower_method", lower_method),
        ("upper_method", upper_method),
        ("coefficients", coefficients),
        ("coefficient_format", coefficient_format),
        ("significance_mode", significance_mode),
        ("significance_thresholds", significance_thresholds),
        ("ci_mode", ci_mode),
        ("nonsignificant_links", nonsignificant_links),
        ("link_width_mode", link_width_mode),
        ("p_value_mode", p_value_mode),
        ("show_nonsignificant", show_nonsignificant),
        ("coupling", coupling),
    ):
        _provided(name, value, values)

    data, composition = normalize_inputs(values)
    ordering = order_variables(
        data.correlation_matrix,
        data.labels,
        mode=composition.matrix.order,
        hclust_method=composition.matrix.hclust_method,
        clusters=composition.matrix.clusters,
    )
    ordered = _ordered_data(data, ordering.indices)
    original_to_position = {
        original: position for position, original in enumerate(ordering.indices.tolist())
    }
    cluster_positions = tuple(
        tuple(original_to_position[index] for index in cluster) for cluster in ordering.clusters
    )
    source_groups = _source_groups(ordered) if composition.coupling.enabled else ()
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    colorbar = render_colorbar(axis, colorbar_axis)
    solve_panel_layout(figure)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    text = measure_text_extents(figure, renderer, ordered.labels, source_groups)
    legends = measure_link_legends(axis, composition.coupling.p_value_mode)
    scale = 72.0 / figure.dpi
    geometry = solve_geometry(
        ordered.labels,
        source_groups,
        matrix_type=composition.matrix.matrix_type,
        measurements=MantelLayoutMeasurements(
            available_width_pt=axis.bbox.width * scale,
            available_height_pt=axis.bbox.height * scale,
            variable_width_pt=text.variable_width_pt,
            variable_height_pt=text.variable_height_pt,
            source_width_pt=text.source_width_pt,
            source_height_pt=text.source_height_pt,
            strength_legend_width_pt=legends.strength_width_pt,
            strength_legend_height_pt=legends.strength_height_pt,
            p_legend_width_pt=legends.p_width_pt,
            p_legend_height_pt=legends.p_height_pt,
        ),
    )
    matrix_result = render_matrix_layer(
        axis,
        ordered,
        composition.matrix,
        geometry,
    )
    matrix_contract = mantel_plot_contract()["matrix"]
    assert isinstance(matrix_contract, Mapping)
    cmap = axiom_colormap(str(matrix_contract["colormap"]))
    norm = Normalize(vmin=-1.0, vmax=1.0)
    visible = visible_glyph_cells(ordered, matrix_result.cells, composition.overlays)
    for glyph in composition.glyphs:
        render_glyph_layer(
            axis,
            ordered,
            matrix_result.cells,
            glyph,
            geometry,
            cmap=cmap,
            norm=norm,
            visible=visible,
        )
    render_statistical_layers(
        axis,
        ordered,
        matrix_result.cells,
        composition.overlays,
        geometry,
        matrix_type=composition.matrix.matrix_type,
        cmap=cmap,
        norm=norm,
        cluster_positions=cluster_positions,
    )
    axis.set_xlim(*geometry.x_limits)
    axis.set_ylim(*geometry.y_limits)
    axis.set_aspect("equal", adjustable="box")
    axis.set_axis_off()
    if composition.coupling.enabled:
        render_node_layer(
            axis,
            geometry,
            source_labels=dict(zip(source_groups, text.source_labels, strict=True)),
        )
    render_coupling_layer(
        axis,
        ordered.links,
        composition.coupling,
        geometry,
    )
    render_ornament_layer(
        axis,
        colorbar_axis,
        geometry,
        coupling_enabled=composition.coupling.enabled,
        colorbar=colorbar,
        p_value_mode=composition.coupling.p_value_mode,
    )
    figure._axiomfig_mantel_composition = composition
    figure._axiomfig_mantel_geometry = geometry
    return figure


__all__ = ["build_mantel", "canonical_mantel_values"]
