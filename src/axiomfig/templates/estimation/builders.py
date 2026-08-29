from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    errorbar_kwargs,
    place_legend_above,
    reference_line_kwargs,
    series_style,
)


def build_forest() -> Figure:
    labels = ["Hybrid ODE", "Neural ODE", "ASM baseline", "Linear model"]
    estimates = np.array([0.84, 0.73, 0.59, 0.46])
    errors = np.array([0.07, 0.09, 0.08, 0.11])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.errorbar(estimates, positions, xerr=errors, **errorbar_kwargs())
    axis.axvline(0.5, **reference_line_kwargs())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Effect estimate (95% CI)")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.25, 1.0, coordinate="x")
    return figure


def build_point_interval() -> Figure:
    labels = ["COD", "TN", "TP"]
    values = np.array([[0.78, 0.69, 0.64], [0.87, 0.79, 0.73]])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    for index, label in enumerate(("Mechanistic", "Hybrid")):
        offset = (index - 0.5) * 0.16
        style = series_style(index)
        axis.errorbar(
            values[index],
            positions + offset,
            xerr=0.045 + 0.01 * index,
            label=label,
            color=style["color"],
            marker=style["marker"],
            linestyle="none",
            **{key: value for key, value in errorbar_kwargs().items() if key != "marker"},
        )
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Validation score (95% CI)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.5, 1.0, coordinate="x")
    place_legend_above(axis)
    return figure


BUILDERS = {"forest": build_forest, "point_interval": build_point_interval}
