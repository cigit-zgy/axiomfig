"""Native Matplotlib line-plot grammars; appearance comes from style modules."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def _series() -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(0.0, 10.0, 81)
    y = 1.05 - np.exp(-0.42 * x)
    return x, y


def _labels(axis: plt.Axes) -> None:
    axis.set_xlabel("Time (d)")
    axis.set_ylabel(r"Normalized response, $S/S_0$ (-)")


def build_single() -> Figure:
    x, y = _series()
    figure, axis = plt.subplots()
    axis.plot(x, y)
    _labels(axis)
    return figure


def build_multi() -> Figure:
    x, y = _series()
    figure, axis = plt.subplots()
    for scale, label in [(0.85, "Low"), (1.0, "Nominal"), (1.12, "High")]:
        axis.plot(x, np.clip(scale * y, 0.0, None), label=label)
    _labels(axis)
    axis.legend(loc="lower right")
    return figure


def build_marker() -> Figure:
    x, y = _series()
    figure, axis = plt.subplots()
    axis.plot(x, y, marker="o", markevery=8, label="Estimate")
    _labels(axis)
    axis.legend(loc="lower right")
    return figure


def build_confidence_interval() -> Figure:
    x, y = _series()
    spread = 0.035 + 0.015 * np.exp(-0.25 * x)
    figure, axis = plt.subplots()
    line = axis.plot(x, y, label="Mean estimate")[0]
    axis.fill_between(x, y - spread, y + spread, color=line.get_color(), alpha=0.2, linewidth=0)
    axis.scatter(x[::8], y[::8] + 0.012 * np.sin(x[::8]), s=9, label="Observed")
    _labels(axis)
    axis.legend(loc="lower right")
    return figure


if __name__ == "__main__":
    build_confidence_interval().show()
