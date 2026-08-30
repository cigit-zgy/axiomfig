from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    FILL_EDGE_PT,
    apply_axis_contract,
    apply_nice_linear_axis,
    series_style,
)


def build_kaplan_meier(
    time: object | None = None,
    survival_probability: object | None = None,
    censoring: object | None = None,
    group: object | None = None,
    lower_ci: object | None = None,
    upper_ci: object | None = None,
    censor_time: object | None = None,
) -> Figure:
    if time is None and survival_probability is None and censoring is None and group is None:
        time_values = np.array([0, 3, 6, 9, 12, 15, 18, 21, 24], dtype=float)
        curves = (
            (
                time_values,
                np.array([1.00, 0.96, 0.92, 0.88, 0.82, 0.77, 0.72, 0.66, 0.61]),
                np.isin(np.arange(time_values.size), [3, 5, 7]),
                None,
                None,
                "Treatment",
            ),
            (
                time_values,
                np.array([1.00, 0.91, 0.84, 0.75, 0.66, 0.57, 0.49, 0.42, 0.35]),
                np.isin(np.arange(time_values.size), [3, 5, 7]),
                None,
                None,
                "Reference",
            ),
        )
        x_limits = (0.0, 24.0)
    elif time is not None and survival_probability is not None:
        time_values = np.asarray(time, dtype=float)
        survival_values = np.asarray(survival_probability, dtype=float)
        censor_values = (
            np.asarray(censoring, dtype=bool)
            if censoring is not None
            else np.zeros(len(time_values), dtype=bool)
        )
        lower_values = None if lower_ci is None else np.asarray(lower_ci, dtype=float)
        upper_values = None if upper_ci is None else np.asarray(upper_ci, dtype=float)
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
            selected_lower = None if lower_values is None else lower_values[mask][order]
            selected_upper = None if upper_values is None else upper_values[mask][order]
            if np.any(np.diff(selected_survival) > 1e-12):
                raise ValueError("Kaplan-Meier survival probabilities must be non-increasing")
            selected_curves.append(
                (
                    selected_time,
                    selected_survival,
                    selected_censor,
                    selected_lower,
                    selected_upper,
                    label,
                )
            )
        if censor_time is not None:
            if len(selected_curves) != 1:
                raise ValueError("censor_time without group labels supports one series")
            selected_time, selected_survival, _, selected_lower, selected_upper, label = (
                selected_curves[0]
            )
            requested_censor = np.asarray(censor_time, dtype=float)
            indices = np.searchsorted(selected_time, requested_censor, side="right") - 1
            if np.any(indices < 0) or np.any(indices >= len(selected_time)):
                raise ValueError("censor_time must lie within the survival time range")
            selected_censor = np.zeros(len(selected_time), dtype=bool)
            selected_censor[np.unique(indices)] = True
            selected_curves[0] = (
                selected_time,
                selected_survival,
                selected_censor,
                selected_lower,
                selected_upper,
                label,
            )
        curves = tuple(selected_curves)
        x_limits = (float(time_values.min()), float(time_values.max()))
    else:
        raise ValueError("Kaplan-Meier requires time and survival_probability together")
    figure, axis = plt.subplots()
    for index, (
        selected_time,
        survival,
        selected_censor,
        selected_lower,
        selected_upper,
        label,
    ) in enumerate(curves):
        style = series_style(index, include_marker=False)
        axis.step(selected_time, survival, where="post", label=label, **style)
        if selected_lower is not None and selected_upper is not None:
            axis.fill_between(
                selected_time,
                selected_lower,
                selected_upper,
                step="post",
                color=style["color"],
                alpha=0.18,
                edgecolor="black",
                linewidth=FILL_EDGE_PT,
            )
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
        request_legend(axis)
    return figure


BUILDERS = {"kaplan_meier": build_kaplan_meier}
