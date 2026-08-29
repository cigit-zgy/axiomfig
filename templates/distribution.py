"""Boxplot and violin grammars."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def _samples() -> list[np.ndarray]:
    rng = np.random.default_rng(47)
    return [
        rng.normal(mean, 0.08 + 0.01 * index, 80) for index, mean in enumerate((0.62, 0.74, 0.81))
    ]


def build_boxplot() -> Figure:
    figure, axis = plt.subplots()
    axis.boxplot(_samples(), tick_labels=["ASM", "Neural ODE", "Hybrid ODE"], patch_artist=True)
    axis.set(xlabel="Model", ylabel="Normalized score (-)")
    return figure


def build_violin() -> Figure:
    figure, axis = plt.subplots()
    parts = axis.violinplot(_samples(), showmeans=False, showmedians=True, showextrema=True)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for body, color in zip(parts["bodies"], colors, strict=False):
        body.set_facecolor(color)
        body.set_alpha(0.72)
    axis.set_xticks([1, 2, 3], ["ASM", "Neural ODE", "Hybrid ODE"])
    axis.set(xlabel="Model", ylabel="Normalized score (-)")
    return figure


if __name__ == "__main__":
    build_violin().show()
