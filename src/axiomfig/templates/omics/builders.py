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


def build_volcano(
    fold_change: object | None = None,
    adjusted_p_value: object | None = None,
    significance_threshold: object | None = None,
    fold_change_threshold: object | None = None,
    feature_label: object | None = None,
) -> Figure:
    if fold_change is None and adjusted_p_value is None and significance_threshold is None:
        rng = np.random.default_rng(181)
        fold_change_values = rng.normal(0.0, 1.2, 160)
        adjusted_p = np.clip(
            np.exp(-0.8 * np.abs(fold_change_values)) * rng.uniform(0.01, 0.9, 160),
            1e-5,
            1.0,
        )
        p_threshold = 0.05
        change_threshold = 1.0
        labels: list[str] | None = None
        limits = ((-3.5, 3.5), (0.0, 5.0))
    elif fold_change is not None and adjusted_p_value is not None and significance_threshold:
        fold_change_values = np.asarray(fold_change, dtype=float)
        adjusted_p = np.asarray(adjusted_p_value, dtype=float)
        if (
            fold_change_values.ndim != 1
            or fold_change_values.shape != adjusted_p.shape
            or fold_change_values.size < 2
        ):
            raise ValueError("volcano fold_change and adjusted_p_value must be equal-length data")
        if np.any(adjusted_p <= 0.0) or np.any(adjusted_p > 1.0):
            raise ValueError("adjusted p-values must lie in (0, 1]")
        p_threshold = float(significance_threshold)
        change_threshold = 1.0 if fold_change_threshold is None else float(fold_change_threshold)
        if not 0.0 < p_threshold < 1.0 or change_threshold <= 0.0:
            raise ValueError("volcano thresholds must be scientifically valid")
        labels = None if feature_label is None else [str(item) for item in feature_label]  # type: ignore[union-attr]
        if labels is not None and len(labels) != fold_change_values.size:
            raise ValueError("volcano feature labels must match data length")
        score_limit = max(float((-np.log10(adjusted_p)).max()) * 1.08, 1.0)
        change_limit = max(float(np.abs(fold_change_values).max()) * 1.08, change_threshold * 1.5)
        limits = ((-change_limit, change_limit), (0.0, score_limit))
    else:
        raise ValueError(
            "volcano requires fold_change, adjusted_p_value, and significance_threshold together"
        )
    score = -np.log10(adjusted_p)
    significant = adjusted_p < p_threshold
    groups = (
        ((fold_change_values < -change_threshold) & significant, "decreased"),
        ((~significant) | (np.abs(fold_change_values) <= change_threshold), "not significant"),
        ((fold_change_values > change_threshold) & significant, "increased"),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    for index, (mask, label) in enumerate(groups):
        collection = axis.scatter(
            fold_change_values[mask],
            score[mask],
            color=colors[(index + 4) % len(colors)],
            label=label,
        )
        apply_scatter_contract(collection)
    axis.axvline(-change_threshold, **reference_line_kwargs())
    axis.axvline(change_threshold, **reference_line_kwargs())
    axis.axhline(-np.log10(p_threshold), **reference_line_kwargs())
    if labels is not None:
        for index in np.argsort(adjusted_p)[:2]:
            axis.text(fold_change_values[index], score[index], labels[index], va="bottom")
    axis.set(xlabel="log2 fold change", ylabel="-log10 adjusted p-value")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *limits[0], coordinate="x")
    apply_nice_linear_axis(axis, *limits[1], coordinate="y")
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
