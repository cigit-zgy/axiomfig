"""Observed-predicted and residual evaluation grammars."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import add_panel_labels, apply_axis_contract, apply_scatter_contract


def _evaluation_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(61)
    observed = np.linspace(2.0, 30.0, 50)
    predicted = observed * 0.97 + 0.6 + rng.normal(0.0, 1.45, observed.size)
    return observed, predicted


def build_residual() -> Figure:
    observed, predicted = _evaluation_data()
    figure, axis = plt.subplots()
    residuals = predicted - observed
    apply_scatter_contract(axis.scatter(predicted, residuals, s=16))
    axis.axhline(0.0, color="0.25", linestyle="--")
    axis.set(xlabel="Predicted (mg L$^{-1}$)", ylabel="Residual (mg L$^{-1}$)")
    apply_axis_contract(axis)
    return figure


def build_summary() -> Figure:
    observed, predicted = _evaluation_data()
    figure, axes = plt.subplots(1, 2)
    limits = (0.0, 32.0)
    apply_scatter_contract(axes[0].scatter(observed, predicted, s=16))
    axes[0].plot(limits, limits, color="0.25", linestyle="--")
    axes[0].set(
        xlim=limits, ylim=limits, xlabel="Observed (mg L$^{-1}$)", ylabel="Predicted (mg L$^{-1}$)"
    )
    apply_scatter_contract(axes[1].scatter(predicted, predicted - observed, s=16))
    axes[1].axhline(0.0, color="0.25", linestyle="--")
    axes[1].set(xlabel="Predicted (mg L$^{-1}$)", ylabel="Residual (mg L$^{-1}$)")
    for axis in axes:
        apply_axis_contract(axis)
    add_panel_labels(axes)
    return figure


if __name__ == "__main__":
    build_summary().show()
