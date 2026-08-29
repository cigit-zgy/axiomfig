"""Vertical and grouped bar grammars."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import add_bar_value_labels, apply_axis_contract, place_legend_above


def build_vertical(decimals: int = 2) -> Figure:
    labels = ["A", "B", "C", "D"]
    values = [0.72, 0.84, 0.77, 0.91]
    figure, axis = plt.subplots()
    container = axis.bar(labels, values)
    axis.set(xlabel="Process configuration", ylabel="Efficiency (-)", ylim=(0.0, 1.0))
    apply_axis_contract(axis, surface="filled")
    add_bar_value_labels(axis, [container], decimals=decimals)
    return figure


def build_grouped(decimals: int = 2) -> Figure:
    labels = ["COD", "NH$_4^+$-N", "TN", "TP"]
    baseline = np.array([0.82, 0.73, 0.61, 0.58])
    hybrid = np.array([0.88, 0.84, 0.72, 0.66])
    positions = np.arange(len(labels))
    width = 0.36
    figure, axis = plt.subplots()
    baseline_bars = axis.bar(positions - width / 2, baseline, width, label="Mechanistic")
    hybrid_bars = axis.bar(positions + width / 2, hybrid, width, label="Hybrid")
    axis.set_xticks(positions, labels)
    axis.set(xlabel="Target variable", ylabel="Validation $R^2$ (-)", ylim=(0.0, 1.0))
    apply_axis_contract(axis, surface="filled")
    add_bar_value_labels(axis, [baseline_bars, hybrid_bars], decimals=decimals)
    place_legend_above(axis)
    return figure


if __name__ == "__main__":
    build_grouped().show()
