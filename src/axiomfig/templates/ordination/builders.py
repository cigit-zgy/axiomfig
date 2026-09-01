from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    FILL_EDGE_PT,
    apply_axis_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    series_style,
)


def _coordinates(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    first = rng.normal((-1.05, 0.35), (0.48, 0.38), (22, 2))
    second = rng.normal((0.95, -0.25), (0.52, 0.42), (22, 2))
    return first, second


def _scatter_groups(axis: plt.Axes, groups: tuple[np.ndarray, np.ndarray]) -> None:
    labels = ("Reference", "Treatment")
    for index, (values, label) in enumerate(zip(groups, labels, strict=True)):
        style = series_style(index)
        collection = axis.scatter(
            values[:, 0],
            values[:, 1],
            label=label,
            color=style["color"],
            marker=style["marker"],
        )
        apply_scatter_contract(collection)


def _plot_scores(
    axis: plt.Axes,
    coordinates: np.ndarray,
    group: object | None,
    sample_labels: object | None = None,
) -> tuple[tuple[np.ndarray, ...], bool]:
    if group is None:
        collection = axis.scatter(coordinates[:, 0], coordinates[:, 1])
        apply_scatter_contract(collection)
        plotted_groups = (coordinates,)
        legend = False
    else:
        group_values = np.asarray(group, dtype=object).astype(str)
        labels = tuple(dict.fromkeys(group_values))
        plotted_groups = tuple(coordinates[group_values == label] for label in labels)
        for index, (label, subset) in enumerate(zip(labels, plotted_groups, strict=True)):
            style = series_style(index)
            collection = axis.scatter(
                subset[:, 0],
                subset[:, 1],
                color=style["color"],
                marker=style["marker"],
                label=label,
            )
            apply_scatter_contract(collection)
        legend = len(labels) > 1
    if sample_labels is not None:
        for (x_value, y_value), label in zip(
            coordinates,
            np.asarray(sample_labels, dtype=object),
            strict=True,
        ):
            axis.annotate(str(label), (x_value, y_value), xytext=(2, 2), textcoords="offset points")
    return plotted_groups, legend


def _score_limits(coordinates: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]]:
    x_padding = max(float(np.ptp(coordinates[:, 0])) * 0.06, 0.1)
    y_padding = max(float(np.ptp(coordinates[:, 1])) * 0.06, 0.1)
    return (
        (
            float(coordinates[:, 0].min()) - x_padding,
            float(coordinates[:, 0].max()) + x_padding,
        ),
        (
            float(coordinates[:, 1].min()) - y_padding,
            float(coordinates[:, 1].max()) + y_padding,
        ),
    )


def _ordination_axes(
    axis: plt.Axes,
    xlabel: str,
    ylabel: str,
    limits: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> None:
    axis.set(xlabel=xlabel, ylabel=ylabel)
    apply_axis_contract(axis, surface="open")
    selected = limits or ((-2.5, 2.5), (-2.0, 2.0))
    apply_nice_linear_axis(axis, *selected[0], coordinate="x")
    apply_nice_linear_axis(axis, *selected[1], coordinate="y")


def build_pca_scores(
    coordinates: object | None = None,
    explained_variance: object | None = None,
    group: object | None = None,
    sample_labels: object | None = None,
) -> Figure:
    figure, axis = plt.subplots()
    if coordinates is None and explained_variance is None and group is None:
        groups = _coordinates(157)
        _scatter_groups(axis, groups)
        variance = (46.2, 21.4)
        limits = None
        legend = True
    elif coordinates is not None and explained_variance is not None:
        values = np.asarray(coordinates, dtype=float)
        variance_values = np.asarray(explained_variance, dtype=float)
        if values.ndim != 2 or values.shape[1] != 2 or values.shape[0] < 2:
            raise ValueError("ordination coordinates must be an n by 2 matrix")
        if variance_values.shape != (2,):
            raise ValueError("PCA explained_variance must contain two values")
        variance = (float(variance_values[0]), float(variance_values[1]))
        _, legend = _plot_scores(axis, values, group, sample_labels)
        limits = _score_limits(values)
    else:
        raise ValueError("PCA scores require coordinates and explained_variance together")
    _ordination_axes(axis, f"PC1 ({variance[0]:.1f}%)", f"PC2 ({variance[1]:.1f}%)", limits)
    if legend:
        request_legend(axis)
    return figure


def build_pca_biplot(
    coordinates: object | None = None,
    loadings: object | None = None,
    explained_variance: object | None = None,
    group: object | None = None,
    feature_labels: object | None = None,
) -> Figure:
    figure, axis = plt.subplots()
    if coordinates is None and loadings is None and explained_variance is None:
        groups = _coordinates(163)
        values = np.vstack(groups)
        loading_values = np.asarray(((1.35, 0.62), (-0.72, 1.12), (0.48, -1.18)))
        labels = np.asarray(("COD", "TN", "Oxygen"), dtype=object)
        _scatter_groups(axis, groups)
        variance = (46.2, 21.4)
        limits = None
        legend = True
    elif coordinates is not None and loadings is not None and explained_variance is not None:
        values = np.asarray(coordinates, dtype=float)
        loading_values = np.asarray(loadings, dtype=float)
        variance_values = np.asarray(explained_variance, dtype=float)
        labels = (
            np.asarray(feature_labels, dtype=object)
            if feature_labels is not None
            else np.asarray([f"Feature {index + 1}" for index in range(len(loading_values))])
        )
        _, legend = _plot_scores(axis, values, group)
        variance = (float(variance_values[0]), float(variance_values[1]))
        combined = np.vstack((values, loading_values, np.zeros((1, 2))))
        limits = _score_limits(combined)
    else:
        raise ValueError(
            "PCA biplot requires coordinates, loadings, and explained_variance together"
        )
    for (x_value, y_value), label in zip(loading_values, labels, strict=True):
        axis.annotate(
            "",
            xy=(x_value, y_value),
            xytext=(0.0, 0.0),
            arrowprops={"arrowstyle": "->"},
        )
        axis.text(
            x_value,
            y_value,
            str(label),
            ha="left" if x_value >= 0 else "right",
            va="bottom",
        )
    _ordination_axes(
        axis,
        f"PC1 ({variance[0]:.1f}%)",
        f"PC2 ({variance[1]:.1f}%)",
        limits,
    )
    if legend:
        request_legend(axis)
    return figure


def build_pcoa(
    coordinates: object | None = None,
    explained_variance: object | None = None,
    distance_metric: object | None = None,
    group: object | None = None,
    sample_labels: object | None = None,
) -> Figure:
    figure, axis = plt.subplots()
    if coordinates is None and explained_variance is None and distance_metric is None:
        groups: tuple[np.ndarray, ...] = _coordinates(167)
        values = np.vstack(groups)
        _scatter_groups(axis, groups)
        variance = (39.7, 18.6)
        limits = None
        legend = True
        metric_label = None
    elif coordinates is not None and explained_variance is not None and distance_metric is not None:
        values = np.asarray(coordinates, dtype=float)
        groups, legend = _plot_scores(axis, values, group, sample_labels)
        variance_values = np.asarray(explained_variance, dtype=float)
        variance = (float(variance_values[0]), float(variance_values[1]))
        limits = _score_limits(values)
        metric_label = str(distance_metric)
    else:
        raise ValueError(
            "PCoA requires coordinates, explained_variance, and distance_metric together"
        )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for values, color in zip(groups, colors, strict=False):
        if len(values) < 2:
            continue
        center = values.mean(axis=0)
        ellipse = Ellipse(
            center,
            width=2.0 * values[:, 0].std(ddof=1),
            height=2.0 * values[:, 1].std(ddof=1),
            facecolor=mcolors.to_rgba(color, 0.18),
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
        )
        axis.add_patch(ellipse)
    _ordination_axes(
        axis,
        f"PCoA1 ({variance[0]:.1f}%)",
        f"PCoA2 ({variance[1]:.1f}%)",
        limits,
    )
    if metric_label is not None:
        axis.text(0.04, 0.92, f"distance: {metric_label}", transform=axis.transAxes)
    if legend:
        request_legend(axis)
    return figure


def build_nmds(
    coordinates: object | None = None,
    stress: object | None = None,
    distance_metric: object | None = None,
    group: object | None = None,
    sample_labels: object | None = None,
) -> Figure:
    figure, axis = plt.subplots()
    if coordinates is None and stress is None and distance_metric is None:
        groups = _coordinates(173)
        _scatter_groups(axis, groups)
        stress_value = 0.09
        metric_label = None
        limits = None
        legend = True
    elif coordinates is not None and stress is not None and distance_metric is not None:
        values = np.asarray(coordinates, dtype=float)
        _, legend = _plot_scores(axis, values, group, sample_labels)
        stress_value = float(stress)
        metric_label = str(distance_metric)
        limits = _score_limits(values)
    else:
        raise ValueError("NMDS requires coordinates, stress, and distance_metric together")
    detail = f"stress = {stress_value:.2f}"
    if metric_label is not None:
        detail += f"; {metric_label}"
    axis.text(0.04, 0.92, detail, transform=axis.transAxes)
    _ordination_axes(axis, "NMDS1", "NMDS2", limits)
    if legend:
        request_legend(axis)
    return figure


BUILDERS = {
    "pca_scores": build_pca_scores,
    "pca_biplot": build_pca_biplot,
    "pcoa": build_pcoa,
    "nmds": build_nmds,
}
