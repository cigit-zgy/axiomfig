from __future__ import annotations

import numpy as np

_LINEAR_LIMIT_PADDING_FRACTION = 0.14


def linear_limits(*arrays: np.ndarray) -> tuple[float, float]:
    """Return finite padded bounds for Bar value geometry."""
    values = np.concatenate([np.asarray(array, dtype=float).ravel() for array in arrays])
    lower = min(float(values.min()), 0.0)
    upper = max(float(values.max()), 0.0)
    with np.errstate(over="ignore", invalid="ignore"):
        span = max(upper - lower, 0.1)
        limits = (
            lower - span * _LINEAR_LIMIT_PADDING_FRACTION,
            upper + span * _LINEAR_LIMIT_PADDING_FRACTION,
        )
    if not np.all(np.isfinite(limits)):
        raise ValueError("bar values must produce finite derived geometry")
    return limits


__all__ = ["linear_limits"]
