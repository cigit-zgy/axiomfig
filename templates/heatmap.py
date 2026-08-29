"""Annotated matrix heatmap grammar."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def build_heatmap() -> Figure:
    matrix = np.array(
        [
            [1.00, 0.72, 0.48, 0.31],
            [0.72, 1.00, 0.63, 0.44],
            [0.48, 0.63, 1.00, 0.79],
            [0.31, 0.44, 0.79, 1.00],
        ]
    )
    labels = ["DO", "NH$_4^+$", "NO$_3^-$", "COD"]
    figure, axis = plt.subplots()
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, aspect="equal", rasterized=True)
    axis.set_xticks(range(4), labels)
    axis.set_yticks(range(4), labels)
    for row in range(4):
        for column in range(4):
            color = "white" if matrix[row, column] < 0.5 else "black"
            axis.text(
                column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", color=color
            )
    colorbar = figure.colorbar(image, ax=axis, pad=0.04)
    colorbar.set_label("Correlation (-)")
    return figure


if __name__ == "__main__":
    build_heatmap().show()
