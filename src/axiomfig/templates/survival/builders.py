from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    place_legend_above,
    series_style,
)


def build_kaplan_meier(
    time: object | None = None,
    survival_probability: object | None = None,
    censoring: object | None = None,
    group: object | None = None,
) -> Figure:
    if time is None and survival_probability is None and censoring is None and group is None:
        time_values = np.array([0, 3, 6, 9, 12, 15, 18, 21, 24], dtype=float)
        curves = (
            (
                time_values,
                np.array([1.00, 0.96, 0.92, 0.88, 0.82, 0.77, 0.72, 0.66, 0.61]),
                np.isin(np.arange(time_values.size), [3, 5, 7]),
                "Treatment",
            ),
            (
                time_values,
                np.array([1.00, 0.91, 0.84, 0.75, 0.66, 0.57, 0.49, 0.42, 0.35]),
                np.isin(np.arange(time_values.size), [3, 5, 7]),
                "Reference",
            ),
        )
        x_limits = (0.0, 24.0)
    elif time is not None and survival_probability is not None and censoring is not None:
        time_values = np.asarray(time, dtype=float)
        survival_values = np.asarray(survival_probability, dtype=float)
        censor_values = np.asarray(censoring, dtype=bool)
        if (
            time_values.ndim != 1
            or time_values.shape != survival_values.shape
            or time_values.shape != censor_values.shape
            or time_values.size < 2
        ):
            raise ValueError("survival time, probability, and censoring must be equal-length data")
        if np.any(survival_values < 0.0) or np.any(survival_values > 1.0):
            raise ValueError("survival probabilities must lie between 0 and 1")
        group_values = (
            np.full(time_values.size, "Series", dtype=object)
            if group is None
            else np.asarray(group, dtype=object)
        )
        if group_values.shape != time_values.shape:
            raise ValueError("survival group must match time data")
        labels = tuple(dict.fromkeys(str(item) for item in group_values))
        group_text = group_values.astype(str)
        selected_curves = []
        for label in labels:
            mask = group_text == label
            order = np.argsort(time_values[mask])
            selected_time = time_values[mask][order]
            selected_survival = survival_values[mask][order]
            selected_censor = censor_values[mask][order]
            if np.any(np.diff(selected_survival) > 1e-12):
                raise ValueError("Kaplan-Meier survival probabilities must be non-increasing")
            selected_curves.append((selected_time, selected_survival, selected_censor, label))
        curves = tuple(selected_curves)
        x_limits = (float(time_values.min()), float(time_values.max()))
    else:
        raise ValueError("Kaplan-Meier requires time, survival_probability, and censoring together")
    figure, axis = plt.subplots()
    for index, (selected_time, survival, selected_censor, label) in enumerate(curves):
        style = series_style(index, include_marker=False)
        axis.step(selected_time, survival, where="post", label=label, **style)
        axis.plot(
            selected_time[selected_censor],
            survival[selected_censor],
            linestyle="none",
            marker="|",
            color=style["color"],
        )
    axis.set(xlabel="Follow-up time (months)", ylabel="Survival probability")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *x_limits, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    if len(curves) > 1:
        place_legend_above(axis)
    return figure


BUILDERS = {"kaplan_meier": build_kaplan_meier}
