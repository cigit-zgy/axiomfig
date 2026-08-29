"""Scatter and observed-versus-predicted grammars."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def build_basic() -> Figure:
    rng = np.random.default_rng(13)
    x = np.linspace(0.1, 1.0, 36)
    y = 0.15 + 0.78 * x + rng.normal(0.0, 0.045, x.size)
    figure, axis = plt.subplots()
    axis.scatter(x, y, s=17)
    axis.set(xlabel="Loading rate (kg m$^{-3}$ d$^{-1}$)", ylabel="Removal efficiency (-)")
    return figure


def build_grouped() -> Figure:
    rng = np.random.default_rng(23)
    figure, axis = plt.subplots()
    for offset, marker, label in [(0.0, "o", "Train"), (0.07, "s", "Test")]:
        x = np.linspace(0.1, 1.0, 24)
        y = 0.12 + 0.82 * x + offset + rng.normal(0.0, 0.035, x.size)
        axis.scatter(x, y, s=18, marker=marker, label=label)
    axis.set(xlabel="Influent fraction (-)", ylabel="Predicted response (-)")
    axis.legend(loc="upper left")
    return figure


def build_parity() -> Figure:
    rng = np.random.default_rng(31)
    observed = np.linspace(4.0, 30.0, 42)
    predicted = observed + rng.normal(0.0, 1.6, observed.size)
    figure, axis = plt.subplots()
    axis.scatter(observed, predicted, s=18)
    limits = (0.0, 32.0)
    axis.plot(limits, limits, color="0.25", linestyle="--", label="1:1")
    axis.set(
        xlim=limits, ylim=limits, xlabel="Observed (mg L$^{-1}$)", ylabel="Predicted (mg L$^{-1}$)"
    )
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="upper left")
    return figure


if __name__ == "__main__":
    build_grouped().show()
