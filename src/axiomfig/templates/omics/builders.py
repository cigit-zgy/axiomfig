from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.colors import semantic_colormap
from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
    apply_filled_collection_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    place_legend_above,
    reference_line_kwargs,
)


def build_volcano() -> Figure:
    rng = np.random.default_rng(181)
    fold_change = rng.normal(0.0, 1.2, 160)
    adjusted_p = np.clip(
        np.exp(-0.8 * np.abs(fold_change)) * rng.uniform(0.01, 0.9, 160),
        1e-5,
        1.0,
    )
    score = -np.log10(adjusted_p)
    significant = adjusted_p < 0.05
    groups = (
        ((fold_change < -1.0) & significant, "decreased"),
        ((~significant) | (np.abs(fold_change) <= 1.0), "not significant"),
        ((fold_change > 1.0) & significant, "increased"),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    for index, (mask, label) in enumerate(groups):
        collection = axis.scatter(
            fold_change[mask],
            score[mask],
            color=colors[(index + 4) % len(colors)],
            label=label,
        )
        apply_scatter_contract(collection)
    axis.axvline(-1.0, **reference_line_kwargs())
    axis.axvline(1.0, **reference_line_kwargs())
    axis.axhline(-np.log10(0.05), **reference_line_kwargs())
    axis.set(xlabel="log2 fold change", ylabel="-log10 adjusted p-value")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, -3.5, 3.5, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 5.0, coordinate="y")
    place_legend_above(axis)
    return figure


def build_enrichment_dot() -> Figure:
    terms = ["Nitrogen cycle", "Carbon fixation", "Stress response", "Transport", "Biofilm"]
    ratio = np.array([0.62, 0.54, 0.47, 0.39, 0.31])
    adjusted_p = np.array([0.001, 0.004, 0.012, 0.027, 0.043])
    count = np.array([42, 35, 28, 24, 18])
    positions = np.arange(len(terms))
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    collection = axis.scatter(
        ratio,
        positions,
        c=-np.log10(adjusted_p),
        s=count * 2.0,
        cmap=semantic_colormap("sequential"),
    )
    apply_filled_collection_contract(collection)
    axis.set_yticks(positions, terms)
    axis.set(xlabel="Enrichment ratio (-)")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.2, 0.7, coordinate="x")
    colorbar = figure.colorbar(
        collection,
        cax=colorbar_axis,
        label="-log10 adjusted p-value",
    )
    apply_colorbar_contract(colorbar)
    return figure


BUILDERS = {"volcano": build_volcano, "enrichment_dot": build_enrichment_dot}
