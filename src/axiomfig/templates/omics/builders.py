from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.ornaments import apply_colorbar_contract, request_legend
from axiomfig.style import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_filled_collection_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    reference_line_kwargs,
    semantic_colormap,
)
from axiomfig.templates._adapter import scalar


def build_volcano(
    effect_size: object | None = None,
    adjusted_p_value: object | None = None,
    significance_threshold: object | None = None,
    effect_threshold: object | None = None,
    feature_label: object | None = None,
) -> Figure:
    if effect_size is None and adjusted_p_value is None and significance_threshold is None:
        rng = np.random.default_rng(181)
        effect_values = rng.normal(0.0, 1.2, 160)
        adjusted_p = np.clip(
            np.exp(-0.8 * np.abs(effect_values)) * rng.uniform(0.01, 0.9, 160),
            1e-5,
            1.0,
        )
        p_threshold = 0.05
        change_threshold = 1.0
        labels: list[str] | None = None
        limits = ((-3.5, 3.5), (0.0, 5.0))
    elif effect_size is not None and adjusted_p_value is not None and significance_threshold:
        effect_values = np.asarray(effect_size, dtype=float)
        adjusted_p = np.asarray(adjusted_p_value, dtype=float)
        if (
            effect_values.ndim != 1
            or effect_values.shape != adjusted_p.shape
            or effect_values.size < 2
        ):
            raise ValueError("volcano effect_size and adjusted_p_value must be equal-length data")
        if np.any(adjusted_p <= 0.0) or np.any(adjusted_p > 1.0):
            raise ValueError("adjusted p-values must lie in (0, 1]")
        p_threshold = scalar(significance_threshold, "significance_threshold")
        change_threshold = (
            1.0 if effect_threshold is None else scalar(effect_threshold, "effect_threshold")
        )
        if not 0.0 < p_threshold < 1.0 or change_threshold <= 0.0:
            raise ValueError("volcano thresholds must be scientifically valid")
        labels = (
            None
            if feature_label is None
            else [str(item) for item in np.asarray(feature_label, dtype=object).ravel()]
        )
        if labels is not None and len(labels) != effect_values.size:
            raise ValueError("volcano feature labels must match data length")
        score_limit = max(float((-np.log10(adjusted_p)).max()) * 1.08, 1.0)
        change_limit = max(
            float(np.abs(effect_values).max()) * 1.08,
            change_threshold * 1.5,
        )
        limits = ((-change_limit, change_limit), (0.0, score_limit))
    else:
        raise ValueError(
            "volcano requires effect_size, adjusted_p_value, and both thresholds together"
        )
    score = -np.log10(adjusted_p)
    significant = adjusted_p < p_threshold
    groups = (
        ((effect_values < -change_threshold) & significant, "decreased"),
        ((~significant) | (np.abs(effect_values) <= change_threshold), "not significant"),
        ((effect_values > change_threshold) & significant, "increased"),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    figure, axis = plt.subplots()
    for index, (mask, label) in enumerate(groups):
        collection = axis.scatter(
            effect_values[mask],
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
            axis.text(effect_values[index], score[index], labels[index], va="bottom")
    axis.set(xlabel="log2 fold change", ylabel="-log10 adjusted p-value")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *limits[0], coordinate="x")
    apply_nice_linear_axis(axis, *limits[1], coordinate="y")
    request_legend(axis)
    return figure


def build_enrichment_dot(
    term: object | None = None,
    enrichment: object | None = None,
    significance: object | None = None,
    size: object | None = None,
    colorbar_label: str = "-log10 adjusted p-value",
    size_label: str | None = None,
) -> Figure:
    if term is None and enrichment is None and significance is None and size is None:
        terms = [
            "Nitrogen cycle",
            "Carbon fixation",
            "Stress response",
            "Transport",
            "Biofilm",
        ]
        ratio = np.array([0.62, 0.54, 0.47, 0.39, 0.31])
        adjusted_p = np.array([0.001, 0.004, 0.012, 0.027, 0.043])
        count = np.array([42, 35, 28, 24, 18])
    elif (
        term is not None
        and enrichment is not None
        and significance is not None
        and size is not None
    ):
        terms = [str(value) for value in np.asarray(term)]
        ratio = np.asarray(enrichment, dtype=float)
        adjusted_p = np.asarray(significance, dtype=float)
        count = np.asarray(size, dtype=float)
    else:
        raise ValueError("enrichment dot requires term, enrichment, significance, and size")
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
    padding = max(float(np.ptp(ratio)) * 0.12, 0.05)
    apply_nice_linear_axis(
        axis,
        float(ratio.min()) - padding,
        float(ratio.max()) + padding,
        coordinate="x",
    )
    colorbar = figure.colorbar(
        collection,
        cax=colorbar_axis,
        label=colorbar_label,
    )
    apply_colorbar_contract(colorbar)
    if size_label is not None:
        axis.text(0.98, 0.04, size_label, transform=axis.transAxes, ha="right")
    return figure


BUILDERS = {"volcano": build_volcano, "enrichment_dot": build_enrichment_dot}
