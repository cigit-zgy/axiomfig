"""Small deterministic calculations derived from the YAML visual contract."""

from __future__ import annotations

import math
from dataclasses import dataclass

from axiomfig.config import load_contracts

_CONTRACTS = load_contracts()
MAIN_STROKE_PT = float(_CONTRACTS.style["stroke"]["main_stroke_pt"])
FILL_EDGE_PT = float(_CONTRACTS.style["stroke"]["fill_edge_pt"])


def tick_lengths() -> tuple[float, float]:
    """Return the central Matplotlib major and minor tick lengths in points."""
    geometry = _CONTRACTS.style["ticks"]["geometry"]
    return float(geometry["major_length_pt"]), float(geometry["minor_length_pt"])


def bar_width(series_count: int = 1) -> float:
    """Return the exact central bar width for a single or grouped series."""
    if isinstance(series_count, bool) or not isinstance(series_count, int) or series_count < 1:
        raise ValueError("series_count must be a positive integer")
    contract = _CONTRACTS.style["plots"]["bar"]
    if series_count == 1:
        return float(contract["single_width"])
    return float(contract["group_width"]) / series_count


@dataclass(frozen=True)
class NiceLinearAxis:
    lower: float
    upper: float
    major_step: float
    minor_step: float


def _major_count(lower: float, upper: float, step: float) -> int:
    return math.floor(upper / step + 1e-10) - math.ceil(lower / step - 1e-10) + 1


def _candidate_steps(rough_step: float) -> list[float]:
    exponent = math.floor(math.log10(rough_step))
    mantissas = tuple(_CONTRACTS.style["axes"]["nice_linear"]["step_mantissas"])
    return [
        float(mantissa) * 10.0**power
        for power in range(exponent - 1, exponent + 2)
        for mantissa in mantissas
    ]


def _snapped_candidates(
    data_min: float, data_max: float, step: float, threshold: float
) -> list[tuple[float, float, int, float, bool]]:
    span = data_max - data_min
    whole_lower = math.floor(data_min / step) * step
    whole_upper = math.ceil(data_max / step) * step
    whole_count = _major_count(whole_lower, whole_upper, step)
    whole_blank = ((whole_upper - whole_lower) - span) / span
    candidates = [(whole_lower, whole_upper, whole_count, whole_blank, False)]

    if whole_blank > threshold or not 5 <= whole_count <= 7:
        half_step = step / 2.0
        half_lower = math.floor(data_min / half_step) * half_step
        half_upper = math.ceil(data_max / half_step) * half_step
        half_count = _major_count(half_lower, half_upper, step)
        half_blank = ((half_upper - half_lower) - span) / span
        if (half_lower, half_upper) != (whole_lower, whole_upper):
            candidates.append((half_lower, half_upper, half_count, half_blank, True))
    return candidates


def nice_linear_axis(data_min: float, data_max: float) -> NiceLinearAxis:
    """Return deterministic snapped limits and 1/2 minor spacing for a linear axis."""
    if not math.isfinite(data_min) or not math.isfinite(data_max):
        raise ValueError("linear-axis bounds must be finite")
    if data_max < data_min:
        raise ValueError("linear-axis bounds must be ordered")
    if data_max == data_min:
        half_span = max(abs(data_min) * 0.1, 0.5)
        data_min -= half_span
        data_max += half_span

    span = data_max - data_min
    target_low, target_high = _CONTRACTS.style["axes"]["nice_linear"]["target_major_ticks"]
    target_intervals = (float(target_low) + float(target_high)) / 2.0 - 1.0
    rough_step = span / target_intervals
    threshold = float(_CONTRACTS.style["axes"]["nice_linear"]["whole_step_blank_fraction"])
    candidates = [
        (step, *snapped)
        for step in _candidate_steps(rough_step)
        for snapped in _snapped_candidates(data_min, data_max, step, threshold)
    ]
    feasible = [item for item in candidates if target_low <= item[3] <= target_high]
    pool = feasible or candidates
    target_mid = (float(target_low) + float(target_high)) / 2.0

    def rank(item: tuple[float, float, float, int, float, bool]) -> tuple[float, ...]:
        step, _lower, _upper, count, blank, is_half = item
        count_penalty = (
            0.0
            if target_low <= count <= target_high
            else min(abs(count - float(target_low)), abs(count - float(target_high)))
        )
        return (
            count_penalty,
            blank,
            abs(math.log10(step / rough_step)),
            float(is_half),
            abs(count - target_mid),
            step,
        )

    step, lower, upper, _count, _blank, _is_half = min(pool, key=rank)
    return NiceLinearAxis(lower, upper, step, step / 2.0)
