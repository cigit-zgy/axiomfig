"""Required English, Simplified Chinese, Japanese, and mathematics sample."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import add_language_text, apply_axis_contract, place_legend_above


def build_multilingual(mode: str = "sans") -> Figure:
    x = np.linspace(0.0, 24.0, 60)
    efficiency = 0.45 + 0.46 * (1.0 - np.exp(-x / 7.0))
    figure, axis = plt.subplots()
    axis.plot(x, efficiency, label="Model estimate")
    axis.set(xlabel="Time (h)", ylabel="Efficiency (-)", ylim=(0.4, 1.0))
    apply_axis_contract(axis)
    place_legend_above(axis)

    family_label = {"sans": "Sans", "serif": "Serif"}[mode]
    add_language_text(
        axis,
        0.04,
        0.92,
        f"{family_label} - Nitrification efficiency",
        "en",
        mode=mode,
        transform=axis.transAxes,
    )
    add_language_text(axis, 0.04, 0.82, "硝化效率", "zh", mode=mode, transform=axis.transAxes)
    add_language_text(axis, 0.04, 0.72, "硝化効率", "ja", mode=mode, transform=axis.transAxes)
    axis.text(
        0.04,
        0.57,
        r"$\mu_{\max}$, $S_{NH4}$ (mg L$^{-1}$), $\pm\,\alpha,\,\beta$",
        transform=axis.transAxes,
    )
    return figure


if __name__ == "__main__":
    build_multilingual().show()
