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


def build_kaplan_meier() -> Figure:
    time = np.array([0, 3, 6, 9, 12, 15, 18, 21, 24], dtype=float)
    curves = (
        (
            np.array([1.00, 0.96, 0.92, 0.88, 0.82, 0.77, 0.72, 0.66, 0.61]),
            "Treatment",
        ),
        (
            np.array([1.00, 0.91, 0.84, 0.75, 0.66, 0.57, 0.49, 0.42, 0.35]),
            "Reference",
        ),
    )
    figure, axis = plt.subplots()
    for index, (survival, label) in enumerate(curves):
        style = series_style(index, include_marker=False)
        axis.step(time, survival, where="post", label=label, **style)
        censor_index = np.array([3, 5, 7])
        axis.plot(
            time[censor_index],
            survival[censor_index],
            linestyle="none",
            marker="|",
            color=style["color"],
        )
    axis.set(xlabel="Follow-up time (months)", ylabel="Survival probability")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, 0.0, 24.0, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    place_legend_above(axis)
    return figure


BUILDERS = {"kaplan_meier": build_kaplan_meier}
