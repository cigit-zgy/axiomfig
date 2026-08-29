"""Vertical and grouped bar grammars."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def build_vertical() -> Figure:
    labels = ["A", "B", "C", "D"]
    values = [0.72, 0.84, 0.77, 0.91]
    figure, axis = plt.subplots()
    axis.bar(labels, values)
    axis.set(xlabel="Process configuration", ylabel="Efficiency (-)", ylim=(0.0, 1.0))
    return figure


def build_grouped() -> Figure:
    labels = ["COD", "NH$_4^+$-N", "TN", "TP"]
    baseline = np.array([0.82, 0.73, 0.61, 0.58])
    hybrid = np.array([0.88, 0.84, 0.72, 0.66])
    positions = np.arange(len(labels))
    width = 0.36
    figure, axis = plt.subplots()
    axis.bar(positions - width / 2, baseline, width, label="Mechanistic")
    axis.bar(positions + width / 2, hybrid, width, label="Hybrid")
    axis.set_xticks(positions, labels)
    axis.set(xlabel="Target variable", ylabel="Validation $R^2$ (-)", ylim=(0.0, 1.0))
    axis.legend(loc="upper left")
    return figure


if __name__ == "__main__":
    build_grouped().show()
