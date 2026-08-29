from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.contracts import bar_width
from axiomfig.template_helpers import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_boxplot_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_violin_contract,
    confidence_interval_kwargs,
    histogram_kwargs,
    place_legend_above,
    series_style,
)


def _vertical_bar_axes(axis: Axes, labels: list[str], upper: float) -> None:
    axis.set_xticks(np.arange(len(labels)), labels)
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, upper, coordinate="y")


def build_vertical_bar() -> Figure:
    labels = ["COD", "Nitrogen", "Phosphorus"]
    figure, axis = plt.subplots()
    bars = axis.bar(np.arange(3), [0.84, 0.76, 0.71], width=bar_width())
    axis.set(ylabel="Validation score (-)")
    _vertical_bar_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [bars])
    return figure


def build_grouped_bar() -> Figure:
    labels = ["COD", "Nitrogen", "Phosphorus"]
    positions = np.arange(3)
    width = bar_width(2)
    figure, axis = plt.subplots()
    first = axis.bar(positions - width / 2, [0.72, 0.67, 0.61], width, label="Mechanistic")
    second = axis.bar(positions + width / 2, [0.84, 0.76, 0.71], width, label="Hybrid")
    axis.set(ylabel="Validation score (-)")
    _vertical_bar_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [first, second])
    place_legend_above(axis)
    return figure


def build_horizontal_bar() -> Figure:
    labels = ["Mechanistic", "Neural ODE", "Hybrid ODE"]
    positions = np.arange(3)
    figure, axis = plt.subplots()
    bars = axis.barh(positions, [0.66, 0.78, 0.87], height=bar_width())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Explained variance (-)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="x")
    add_bar_value_labels(axis, [bars])
    return figure


def build_stacked_bar() -> Figure:
    labels = ["Baseline", "Calibrated", "Hybrid"]
    positions = np.arange(3)
    first_values = np.array([0.42, 0.50, 0.57])
    second_values = np.array([0.25, 0.28, 0.31])
    figure, axis = plt.subplots()
    width = bar_width()
    first = axis.bar(positions, first_values, width=width, label="Mechanistic")
    second = axis.bar(
        positions,
        second_values,
        width=width,
        bottom=first_values,
        label="Data-driven",
    )
    axis.set(ylabel="Explained contribution (-)")
    _vertical_bar_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [first, second])
    place_legend_above(axis)
    return figure


def _samples(seed: int = 47) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.normal(mean, 0.075, 90) for mean in (0.62, 0.74, 0.82)]


def _distribution_axis(axis: Axes, samples: list[np.ndarray]) -> None:
    axis.set_xticks([1, 2, 3], ["Mechanistic", "Neural ODE", "Hybrid ODE"])
    axis.set(ylabel="Normalized score (-)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    values = np.concatenate(samples)
    padding_fraction = float(load_contracts().style["plots"]["violin"]["limit_padding_fraction"])
    padding = float(np.ptp(values)) * padding_fraction
    apply_nice_linear_axis(
        axis, float(values.min()) - padding, float(values.max()) + padding, coordinate="y"
    )


def build_boxplot() -> Figure:
    samples = _samples(61)
    figure, axis = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    contract = load_contracts().style["plots"]["boxplot"]
    parts = axis.boxplot(samples, patch_artist=True, widths=float(contract["width"]))
    for box, color in zip(parts["boxes"], colors, strict=False):
        box.set_facecolor(color)
    apply_boxplot_contract(parts)
    _distribution_axis(axis, samples)
    return figure


def build_violin() -> Figure:
    samples = _samples()
    figure, axis = plt.subplots()
    parts = axis.violinplot(samples, showmedians=True, showextrema=True)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for body, color in zip(parts["bodies"], colors, strict=False):
        body.set_facecolor(color)
    apply_violin_contract(parts)
    _distribution_axis(axis, samples)
    return figure


def build_box_violin() -> Figure:
    samples = _samples(73)
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
    _distribution_axis(axis, samples)
    return figure


def build_histogram() -> Figure:
    rng = np.random.default_rng(83)
    residuals = rng.normal(0.0, 1.15, 240)
    figure, axis = plt.subplots()
    axis.hist(residuals, bins=np.linspace(-3.5, 3.5, 15), **histogram_kwargs())
    axis.set(xlabel="Residual (mg/L)", ylabel="Frequency")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, -3.5, 3.5, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 50.0, coordinate="y")
    return figure


def build_density() -> Figure:
    rng = np.random.default_rng(89)
    samples = rng.normal(0.2, 0.95, 180)
    grid = np.linspace(-3.2, 3.6, 240)
    bandwidth = 0.38
    density = np.exp(-0.5 * ((grid[:, None] - samples[None, :]) / bandwidth) ** 2).mean(axis=1) / (
        bandwidth * np.sqrt(2.0 * np.pi)
    )
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(grid, 0.0, density, **confidence_interval_kwargs(color))
    axis.plot(grid, density)
    axis.set(xlabel="Standardized residual", ylabel="Density")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, -3.2, 3.6, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, float(density.max()) * 1.08, coordinate="y")
    return figure


def build_ecdf() -> Figure:
    rng = np.random.default_rng(97)
    figure, axis = plt.subplots()
    for index, (mean, label) in enumerate(((0.0, "Baseline"), (0.55, "Hybrid"))):
        values = np.sort(rng.normal(mean, 0.9, 90))
        probability = np.arange(1, values.size + 1) / values.size
        axis.step(values, probability, where="post", label=label, **series_style(index))
    axis.set(xlabel="Standardized score", ylabel="Cumulative probability")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, -3.0, 3.5, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    place_legend_above(axis)
    return figure
