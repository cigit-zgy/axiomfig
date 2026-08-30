from __future__ import annotations

import math

import pytest


@pytest.mark.parametrize(
    ("data_min", "data_max", "expected"),
    [
        (0.3, 9.1, (0.0, 10.0, 2.0, 1.0)),
        (-2.2, 3.1, (-2.5, 3.5, 1.0, 0.5)),
        (120.0, 880.0, (0.0, 1000.0, 200.0, 100.0)),
        (0.0012, 0.0088, (0.0, 0.01, 0.002, 0.001)),
        (0.3, 17.8, (0.0, 20.0, 5.0, 2.5)),
    ],
)
def test_nice_linear_axis_uses_hand_derived_snapped_steps(
    data_min: float, data_max: float, expected: tuple[float, float, float, float]
) -> None:
    from axiomfig.style import nice_linear_axis

    result = nice_linear_axis(data_min, data_max)

    assert (result.lower, result.upper, result.major_step, result.minor_step) == pytest.approx(
        expected
    )
    major_count = (
        math.floor(result.upper / result.major_step + 1e-9)
        - math.ceil(result.lower / result.major_step - 1e-9)
        + 1
    )
    assert 5 <= major_count <= 7


def test_nice_linear_axis_expands_a_constant_range_deterministically() -> None:
    from axiomfig.style import nice_linear_axis

    first = nice_linear_axis(4.0, 4.0)
    second = nice_linear_axis(4.0, 4.0)

    assert first == second
    assert first.lower < 4.0 < first.upper
    assert first.minor_step == first.major_step / 2


@pytest.mark.parametrize("bounds", [(float("nan"), 1.0), (0.0, float("inf")), (2.0, 1.0)])
def test_nice_linear_axis_rejects_invalid_bounds(bounds: tuple[float, float]) -> None:
    from axiomfig.style import nice_linear_axis

    with pytest.raises(ValueError, match="finite|ordered"):
        nice_linear_axis(*bounds)
