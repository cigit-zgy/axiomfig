from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.ornaments import request_legend
from axiomfig.style import (
    apply_axis_contract,
    apply_boxplot_contract,
    apply_categorical_axis,
    apply_distribution_point_contract,
    apply_nice_linear_axis,
    apply_violin_contract,
    confidence_interval_kwargs,
    histogram_kwargs,
    series_style,
)


def _samples(seed: int = 47) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.normal(mean, 0.075, 90) for mean in (0.62, 0.74, 0.82)]


def _distribution_axis(
    axis: Axes,
    samples: list[np.ndarray],
    labels: list[str] | None = None,
) -> None:
    selected_labels = labels or ["Mechanistic", "Neural ODE", "Hybrid ODE"]
    axis.set_xticks(np.arange(1, len(selected_labels) + 1), selected_labels)
    axis.set(ylabel="Normalized score (-)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    values = np.concatenate(samples)
    padding_fraction = float(load_contracts().style["plots"]["violin"]["limit_padding_fraction"])
    padding = float(np.ptp(values)) * padding_fraction
    apply_nice_linear_axis(
        axis, float(values.min()) - padding, float(values.max()) + padding, coordinate="y"
    )


def _grouped_samples(value: object, category: object) -> tuple[list[np.ndarray], list[str]]:
    values = np.asarray(value, dtype=float)
    categories = np.asarray(category, dtype=object).astype(str)
    labels = list(dict.fromkeys(categories))
    return [values[categories == label] for label in labels], labels


def build_histogram(
    value: object | None = None,
    bins: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if value is None:
        rng = np.random.default_rng(83)
        residuals = rng.normal(0.0, 1.15, 240)
        selected_bins: object = np.linspace(-3.5, 3.5, 15)
        limits = (-3.5, 3.5)
    else:
        residuals = np.asarray(value, dtype=float)
        selected_bins = 10 if bins is None else bins
        padding = max(float(np.ptp(residuals)) * 0.05, 0.1)
        limits = (float(residuals.min()) - padding, float(residuals.max()) + padding)
    figure, axis = plt.subplots()
    counts, _, _ = axis.hist(residuals, bins=selected_bins, **histogram_kwargs())
    axis.set(
        xlabel="Residual (mg/L)" if xlabel is None else str(xlabel),
        ylabel="Frequency" if ylabel is None else str(ylabel),
    )
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *limits, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, max(float(counts.max()) * 1.12, 1.0), coordinate="y")
    return figure


def build_density(
    x: object | None = None,
    density: object | None = None,
    group: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and density is None:
        rng = np.random.default_rng(89)
        samples = rng.normal(0.2, 0.95, 180)
        grid = np.linspace(-3.2, 3.6, 240)
        bandwidth = 0.38
        selected_density = np.exp(
            -0.5 * ((grid[:, None] - samples[None, :]) / bandwidth) ** 2
        ).mean(axis=1) / (bandwidth * np.sqrt(2.0 * np.pi))
        series = [(grid, selected_density, None)]
        limits = ((-3.2, 3.6), (0.0, float(selected_density.max()) * 1.08))
    elif x is not None and density is not None:
        grid = np.asarray(x, dtype=float)
        selected_density = np.asarray(density, dtype=float)
        if group is None:
            series = [(grid, selected_density, None)]
        else:
            groups = np.asarray(group, dtype=object).astype(str)
            series = [
                (grid[groups == label], selected_density[groups == label], label)
                for label in dict.fromkeys(groups)
            ]
        x_padding = max(float(np.ptp(grid)) * 0.04, 0.1)
        limits = (
            (float(grid.min()) - x_padding, float(grid.max()) + x_padding),
            (0.0, max(float(selected_density.max()) * 1.08, 0.1)),
        )
    else:
        raise ValueError("density requires precomputed x and density together")
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for index, (selected_x, selected_y, label) in enumerate(series):
        order = np.argsort(selected_x)
        color = colors[index % len(colors)]
        axis.fill_between(
            selected_x[order], 0.0, selected_y[order], **confidence_interval_kwargs(color)
        )
        axis.plot(selected_x[order], selected_y[order], label=label, color=color)
    axis.set(
        xlabel="Standardized residual" if xlabel is None else str(xlabel),
        ylabel="Density" if ylabel is None else str(ylabel),
    )
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *limits[0], coordinate="x")
    apply_nice_linear_axis(axis, *limits[1], coordinate="y")
    if any(label is not None for _, _, label in series):
        request_legend(axis)
    return figure


def build_ecdf(
    value: object | None = None,
    group: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if value is None:
        rng = np.random.default_rng(97)
        series = [
            (rng.normal(mean, 0.9, 90), label)
            for mean, label in ((0.0, "Baseline"), (0.55, "Hybrid"))
        ]
        x_limits = (-3.0, 3.5)
    else:
        values = np.asarray(value, dtype=float)
        if group is None:
            series = [(values, None)]
        else:
            groups = np.asarray(group, dtype=object).astype(str)
            series = [(values[groups == label], label) for label in dict.fromkeys(groups)]
        padding = max(float(np.ptp(values)) * 0.05, 0.1)
        x_limits = (float(values.min()) - padding, float(values.max()) + padding)
    figure, axis = plt.subplots()
    maximum_markers = int(load_contracts().style["plots"]["distribution"]["ecdf_max_markers"])
    for index, (selected, label) in enumerate(series):
        ordered = np.sort(selected)
        probability = np.arange(1, ordered.size + 1) / ordered.size
        style = series_style(index)
        style["markevery"] = max(1, math.ceil(ordered.size / maximum_markers))
        axis.step(ordered, probability, where="post", label=label, **style)
    axis.set(
        xlabel="Standardized score" if xlabel is None else str(xlabel),
        ylabel="Cumulative probability" if ylabel is None else str(ylabel),
    )
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *x_limits, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    if any(label is not None for _, label in series):
        request_legend(axis)
    return figure


def build_box(
    value: object | None = None,
    category: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    labels = None
    if value is None and category is None:
        samples = _samples(61)
    elif value is not None and category is not None:
        samples, labels = _grouped_samples(value, category)
    else:
        raise ValueError("box requires value and category together")
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    contract = load_contracts().style["plots"]["boxplot"]
    parts = axis.boxplot(samples, patch_artist=True, widths=float(contract["width"]))
    for box, color in zip(parts["boxes"], colors, strict=False):
        box.set_facecolor(color)
    apply_boxplot_contract(parts)
    _distribution_axis(axis, samples, labels)
    if ylabel is not None:
        axis.set_ylabel(str(ylabel))
    return figure


def build_violin(
    value: object | None = None,
    category: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    labels: list[str] | None = None
    if value is None and category is None:
        samples = _samples()
    elif value is not None and category is not None:
        values = np.asarray(value, dtype=float)
        categories = np.asarray(category, dtype=object)
        if values.ndim != 1 or values.shape != categories.shape or values.size < 2:
            raise ValueError("violin value and category must be equal-length one-dimensional data")
        labels = list(dict.fromkeys(str(item) for item in categories))
        category_text = categories.astype(str)
        samples = [values[category_text == label] for label in labels]
        if any(sample.size < 2 for sample in samples):
            raise ValueError("each violin category requires at least two observations")
    else:
        raise ValueError("violin requires value and category together")
    figure, axis = plt.subplots()
    parts = axis.violinplot(samples, showmedians=True, showextrema=True)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for body, color in zip(parts["bodies"], colors, strict=False):
        body.set_facecolor(color)
    apply_violin_contract(parts)
    _distribution_axis(axis, samples, labels)
    if ylabel is not None:
        axis.set_ylabel(str(ylabel))
    return figure


def build_box_violin(
    value: object | None = None,
    category: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    labels = None
    if value is None and category is None:
        samples = _samples(73)
    elif value is not None and category is not None:
        samples, labels = _grouped_samples(value, category)
    else:
        raise ValueError("box_violin requires value and category together")
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    violin_contract = load_contracts().style["plots"]["violin"]
    box_contract = load_contracts().style["plots"]["boxplot"]
    violins = axis.violinplot(samples, showextrema=False, widths=float(violin_contract["width"]))
    for body, color in zip(violins["bodies"], colors, strict=False):
        body.set_facecolor(color)
    apply_violin_contract(violins, combined=True)
    boxes = axis.boxplot(
        samples,
        patch_artist=True,
        widths=float(box_contract["combined_width"]),
        showfliers=False,
    )
    for box in boxes["boxes"]:
        box.set_facecolor("white")
    apply_boxplot_contract(boxes, combined=True)
    _distribution_axis(axis, samples, labels)
    if ylabel is not None:
        axis.set_ylabel(str(ylabel))
    return figure


def build_strip(
    value: object | None = None,
    category: object | None = None,
    jitter: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    labels = None
    if value is None and category is None:
        samples = _samples(109)
    elif value is not None and category is not None:
        samples, labels = _grouped_samples(value, category)
    else:
        raise ValueError("strip requires value and category together")
    rng = np.random.default_rng(109)
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for position, (values, color) in enumerate(zip(samples, colors, strict=False), start=1):
        amount = 0.13 if jitter is None else float(jitter)
        offsets = rng.uniform(-amount, amount, values.size)
        collection = axis.scatter(np.full(values.size, position) + offsets, values, color=color)
        apply_distribution_point_contract(collection)
    _distribution_axis(axis, samples, labels)
    if ylabel is not None:
        axis.set_ylabel(str(ylabel))
    return figure


def build_raincloud(
    value: object | None = None,
    category: object | None = None,
    jitter: object | None = None,
    summary: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    labels = None
    if value is None and category is None:
        samples = _samples(113)
    elif value is not None and category is not None:
        samples, labels = _grouped_samples(value, category)
    else:
        raise ValueError("raincloud requires value and category together")
    if summary not in {None, "median"}:
        raise ValueError("raincloud summary must be median")
    rng = np.random.default_rng(113)
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    violin_contract = load_contracts().style["plots"]["violin"]
    violins = axis.violinplot(
        samples,
        positions=[1, 2, 3],
        showextrema=False,
        widths=float(violin_contract["width"]),
    )
    for position, body, color in zip((1, 2, 3), violins["bodies"], colors, strict=False):
        body.set_facecolor(color)
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], float(position))
    apply_violin_contract(violins, combined=True)
    for position, (values, color) in enumerate(zip(samples, colors, strict=False), start=1):
        amount = 0.18 if jitter is None else float(jitter)
        offsets = rng.uniform(0.07, 0.07 + amount, values.size)
        collection = axis.scatter(np.full(values.size, position) + offsets, values, color=color)
        apply_distribution_point_contract(collection)
        axis.plot(
            [position - 0.05, position + 0.05],
            [float(np.median(values)), float(np.median(values))],
            color="black",
        )
    _distribution_axis(axis, samples, labels)
    if ylabel is not None:
        axis.set_ylabel(str(ylabel))
    return figure


BUILDERS = {
    "histogram": build_histogram,
    "density": build_density,
    "ecdf": build_ecdf,
    "box": build_box,
    "violin": build_violin,
    "box_violin": build_box_violin,
    "strip": build_strip,
    "raincloud": build_raincloud,
}
