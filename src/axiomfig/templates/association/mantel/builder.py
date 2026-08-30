"""Orchestration for the canonical Mantel visualization engine."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.templates.association.mantel.coupling import render_coupling
from axiomfig.templates.association.mantel.data import MantelData, normalize_inputs
from axiomfig.templates.association.mantel.geometry import solve_geometry
from axiomfig.templates.association.mantel.legends import render_colorbar, render_link_legends
from axiomfig.templates.association.mantel.matrix import render_matrix
from axiomfig.templates.association.mantel.ordering import order_variables

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


def build_mantel(
    correlation_matrix: object | None = None,
    labels: object | None = None,
    links: object | None = None,
    p_values: object | None = None,
    lower_ci: object | None = None,
    upper_ci: object | None = None,
    matrix_method: object | None = None,
    matrix_type: object | None = None,
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
    show_nonsignificant: object | None = None,
) -> Figure:
    if correlation_matrix is None and labels is None and links is None:
        values = canonical_mantel_values()
    elif correlation_matrix is None or labels is None or links is None:
        raise ValueError("Mantel requires correlation_matrix, labels, and links together")
    else:
        values = {
            "correlation_matrix": correlation_matrix,
            "labels": labels,
            "links": links,
        }
    for name, value in (
        ("p_values", p_values),
        ("lower_ci", lower_ci),
        ("upper_ci", upper_ci),
        ("matrix_method", matrix_method),
        ("matrix_type", matrix_type),
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
        ("show_nonsignificant", show_nonsignificant),
    ):
        _provided(name, value, values)
    data, options = normalize_inputs(values)
    ordering = order_variables(
        data.correlation_matrix,
        data.labels,
        mode=options.order,
        hclust_method=options.hclust_method,
        clusters=options.clusters,
    )
    ordered = _ordered_data(data, ordering.indices)
    original_to_position = {
        original: position for position, original in enumerate(ordering.indices.tolist())
    }
    cluster_positions = tuple(
        tuple(original_to_position[index] for index in cluster) for cluster in ordering.clusters
    )
    source_groups = tuple(dict.fromkeys(link.source for link in ordered.links))
    geometry = solve_geometry(ordered.labels, source_groups, matrix_type=options.matrix_type)

    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, _ = add_panel_axes(layout, 0)
    render_matrix(
        axis,
        ordered,
        options,
        geometry,
        cluster_positions=cluster_positions,
    )
    render_coupling(axis, ordered.links, options, geometry)
    render_colorbar(axis, geometry)
    render_link_legends(axis)
    axis.set_xlim(*geometry.x_limits)
    axis.set_ylim(*geometry.y_limits)
    axis.set_aspect("equal", adjustable="box")
    axis.set_axis_off()
    return figure


__all__ = ["build_mantel", "canonical_mantel_values"]
