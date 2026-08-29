"""Stable visual tokens shared by AxiomFig styles and helpers."""

STROKE_WIDTH_PT: float = 0.6

# Matplotlib rcParams cannot express distinct major and minor directions.  The
# helper in ``styles`` applies these per-axis values after a plot type is known.
OPEN_TICK_PARAMS = {"major": "inout", "minor": "in"}
FILLED_TICK_PARAMS = {"major": "out", "minor": "out"}
