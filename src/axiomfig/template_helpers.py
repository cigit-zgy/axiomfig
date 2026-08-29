from __future__ import annotations

from collections.abc import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.typography import font_for_language


def add_panel_labels(axes: Iterable[Axes]) -> None:
    for index, axis in enumerate(axes):
        label = f"({chr(ord('a') + index)})"
        axis.text(
            -0.14,
            1.04,
            label,
            transform=axis.transAxes,
            ha="left",
            va="bottom",
            fontweight="bold",
            clip_on=False,
        )


def add_language_text(
    axis: Axes,
    x: float,
    y: float,
    text: str,
    language: str,
    **kwargs: object,
) -> None:
    axis.text(x, y, text, fontproperties=font_for_language(language), **kwargs)


def close_secondary_spines(figure: Figure) -> Figure:
    for axis in figure.axes:
        axis.tick_params(which="both", top=True, right=True)
    return figure
