from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from axiomfig.intent import FigureIntentError, load_dataset, parse_figure_intent
from axiomfig.templates._adapter import numeric_1d

PARITY_DATA = {"observed": "measured", "predicted": "modeled"}


@settings(max_examples=25, deadline=None)
@given(
    st.text(min_size=1).filter(
        lambda value: value not in {"template", "data", "geometry", "typography", "semantics"}
    )
)
def test_unknown_top_level_figure_intent_fields_always_fail(field: str) -> None:
    document = {"template": "scatter.parity", "data": PARITY_DATA, field: "value"}
    with pytest.raises(FigureIntentError, match="unknown Figure Intent fields"):
        parse_figure_intent(document)


@settings(max_examples=25, deadline=None)
@given(
    st.sampled_from(
        (
            "font_size",
            "linewidth",
            "tick_length",
            "legend_x",
            "legend_y",
            "panel_offset",
            "bar_width",
            "colorbar_width",
            "subplot_wspace",
            "subplot_hspace",
            "figure_width",
            "figure_height",
        )
    ),
    st.booleans(),
)
def test_low_level_visual_fields_always_fail(field: str, nested: bool) -> None:
    document: dict[str, object] = {"template": "scatter.parity", "data": PARITY_DATA}
    if nested:
        document["semantics"] = {field: 1}
    else:
        document[field] = 1
    with pytest.raises(FigureIntentError, match="deterministic visual field is forbidden"):
        parse_figure_intent(document)


@settings(max_examples=20, deadline=None)
@given(st.permutations(("template", "data", "geometry", "typography", "semantics")))
def test_valid_figure_intent_is_deterministic_across_key_order(order: list[str]) -> None:
    values: dict[str, object] = {
        "template": "scatter.parity",
        "data": PARITY_DATA,
        "geometry": "single-column",
        "typography": "sans",
        "semantics": {"identity_limits": "limits"},
    }
    document = OrderedDict((key, values[key]) for key in order)
    parsed = parse_figure_intent(document)
    assert parsed.template_id == "scatter/parity"
    assert dict(parsed.data) == PARITY_DATA
    assert dict(parsed.semantics) == {"identity_limits": "limits"}


JSON_SCALAR = st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.text(max_size=8),
    st.booleans(),
)


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(
    st.lists(st.fixed_dictionaries({"x": JSON_SCALAR, "y": JSON_SCALAR}), min_size=1, max_size=5)
)
def test_consistent_json_rows_load_deterministically(
    tmp_path: Path, rows: list[dict[str, object]]
) -> None:
    path = tmp_path / "rows.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    first = load_dataset(path)
    second = load_dataset(path)
    assert first == second
    assert tuple(first) == tuple(rows[0])


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(JSON_SCALAR, JSON_SCALAR, st.sampled_from(("missing", "extra")))
def test_heterogeneous_json_rows_fail_with_domain_error(
    tmp_path: Path, first: object, second: object, mutation: str
) -> None:
    row = {"x": second} if mutation == "missing" else {"x": second, "y": second, "z": 1}
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([{"x": first, "y": first}, row]), encoding="utf-8")
    with pytest.raises(FigureIntentError, match="same string keys"):
        load_dataset(path)


@settings(max_examples=20, deadline=None)
@given(st.sampled_from((float("nan"), float("inf"), float("-inf"))))
def test_nonfinite_numeric_arrays_fail_closed(value: float) -> None:
    with pytest.raises(ValueError, match="finite one-dimensional array"):
        numeric_1d([0.0, value], "value", minimum=2)


@settings(max_examples=20, deadline=None)
@given(st.floats(min_value=-1e100, max_value=1e100, allow_nan=False, allow_infinity=False))
def test_finite_numeric_extremes_remain_supported(value: float) -> None:
    result = numeric_1d([0.0, value], "value", minimum=2)
    assert result.shape == (2,)
