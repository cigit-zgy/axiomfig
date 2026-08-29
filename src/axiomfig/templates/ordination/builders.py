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


def _ordination_axes(axis: plt.Axes, xlabel: str, ylabel: str) -> None:
    axis.set(xlabel=xlabel, ylabel=ylabel)
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, -2.5, 2.5, coordinate="x")
    apply_nice_linear_axis(axis, -2.0, 2.0, coordinate="y")


def build_pca_scores() -> Figure:
    groups = _coordinates(157)
    figure, axis = plt.subplots()
    _scatter_groups(axis, groups)
    _ordination_axes(axis, "PC1 (46.2%)", "PC2 (21.4%)")
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
