from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse

from axiomfig.contracts import FILL_EDGE_PT
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    place_legend_above,
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
        if group is None:
            collection = axis.scatter(values[:, 0], values[:, 1])
            apply_scatter_contract(collection)
            legend = False
        else:
            groups_values = np.asarray(group, dtype=object)
            if groups_values.shape != (values.shape[0],):
                raise ValueError("ordination group must match coordinate rows")
            labels = tuple(dict.fromkeys(str(item) for item in groups_values))
            group_text = groups_values.astype(str)
            for index, label in enumerate(labels):
                style = series_style(index)
                subset = values[group_text == label]
                collection = axis.scatter(
                    subset[:, 0],
                    subset[:, 1],
                    color=style["color"],
                    marker=style["marker"],
                    label=label,
                )
                apply_scatter_contract(collection)
            legend = len(labels) > 1
        x_padding = max(float(np.ptp(values[:, 0])) * 0.06, 0.1)
        y_padding = max(float(np.ptp(values[:, 1])) * 0.06, 0.1)
        limits = (
            (float(values[:, 0].min()) - x_padding, float(values[:, 0].max()) + x_padding),
            (float(values[:, 1].min()) - y_padding, float(values[:, 1].max()) + y_padding),
        )
    else:
        raise ValueError("PCA scores require coordinates and explained_variance together")
    _ordination_axes(axis, f"PC1 ({variance[0]:.1f}%)", f"PC2 ({variance[1]:.1f}%)", limits)
    if legend:
        place_legend_above(axis)
    return figure


def build_pca_biplot() -> Figure:
    groups = _coordinates(163)
    loadings = ((1.35, 0.62, "COD"), (-0.72, 1.12, "TN"), (0.48, -1.18, "Oxygen"))
    figure, axis = plt.subplots()
    _scatter_groups(axis, groups)
    for x, y, label in loadings:
        axis.annotate("", xy=(x, y), xytext=(0.0, 0.0), arrowprops={"arrowstyle": "->"})
        axis.text(x, y, label, ha="left" if x >= 0 else "right", va="bottom")
    _ordination_axes(axis, "PC1 (46.2%)", "PC2 (21.4%)")
    place_legend_above(axis)
    return figure


def build_pcoa() -> Figure:
    groups = _coordinates(167)
    figure, axis = plt.subplots()
    _scatter_groups(axis, groups)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for values, color in zip(groups, colors, strict=False):
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
    _ordination_axes(axis, "PCoA1 (39.7%)", "PCoA2 (18.6%)")
    place_legend_above(axis)
    return figure


def build_nmds() -> Figure:
    groups = _coordinates(173)
    figure, axis = plt.subplots()
    _scatter_groups(axis, groups)
    axis.text(0.04, 0.92, "stress = 0.09", transform=axis.transAxes)
    _ordination_axes(axis, "NMDS1", "NMDS2")
    place_legend_above(axis)
    return figure


BUILDERS = {
    "pca_scores": build_pca_scores,
    "pca_biplot": build_pca_biplot,
    "pcoa": build_pcoa,
    "nmds": build_nmds,
}
