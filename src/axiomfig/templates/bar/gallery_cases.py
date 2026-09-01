"""Curated serif-only formal Gallery cases for the Bar family."""

from __future__ import annotations

from functools import partial

from axiomfig.templates.gallery_support import TemplateGalleryCase


def _simple(
    *, orientation: str = "vertical", negative: bool = False, labels: bool = False
) -> dict[str, object]:
    values: dict[str, object] = {
        "category": ["Control", "Low dose", "High dose"],
        "value": [2.8, -1.1 if negative else 3.7, 4.4],
        "orientation": orientation,
        "value_labels": labels,
    }
    values["ylabel" if orientation == "vertical" else "xlabel"] = "Response (mg/L)"
    return values


def _grouped(*, orientation: str = "vertical", uncertainty: bool = False) -> dict[str, object]:
    values: dict[str, object] = {
        "category": ["Influent", "Influent", "Effluent", "Effluent", "Reuse", "Reuse"],
        "group": ["Control", "Treatment"] * 3,
        "value": [5.2, 4.7, 2.9, 2.1, 1.8, 1.3],
        "orientation": orientation,
        "value_labels": False,
    }
    if uncertainty:
        values.update(error=[0.3, 0.25, 0.2, 0.18, 0.14, 0.12], uncertainty_type="SE")
    return values


def _stacked(*, orientation: str = "vertical") -> dict[str, object]:
    return {
        "category": ["R1", "R2", "R3", "R1", "R2", "R3"],
        "component": ["Soluble"] * 3 + ["Particulate"] * 3,
        "value": [3.2, 3.7, 4.0, 1.8, 1.5, 1.2],
        "orientation": orientation,
        "value_labels": False,
    }


def _normalized() -> dict[str, object]:
    return {**_stacked(), "normalization": "normalize"}


def _grouped_stacked() -> dict[str, object]:
    rows = [
        (category, group, component, value)
        for category, base in (("R1", 2.0), ("R2", 2.5), ("R3", 3.0))
        for group, shift in (("Control", 0.0), ("Treatment", 0.5))
        for component, fraction in (("Soluble", 1.0), ("Particulate", 0.55))
        for value in (base * fraction + shift,)
    ]
    return {
        "category": [row[0] for row in rows],
        "group": [row[1] for row in rows],
        "component": [row[2] for row in rows],
        "value": [row[3] for row in rows],
        "value_labels": False,
    }


def _diverging() -> dict[str, object]:
    return {
        "category": ["Site A"] * 4 + ["Site B"] * 4 + ["Site C"] * 4,
        "component": ["Gain 1", "Loss 1", "Gain 2", "Loss 2"] * 3,
        "value": [2.8, -1.2, 1.1, -0.6, 3.4, -1.8, 0.8, -0.7, 2.2, -1.0, 1.5, -0.9],
        "value_labels": False,
    }


def _range(*, orientation: str = "vertical") -> dict[str, object]:
    return {
        "category": ["Scenario A", "Scenario B", "Scenario C", "Scenario D"],
        "lower": [1.2, 1.8, 2.4, 2.1],
        "upper": [2.6, 3.4, 4.1, 3.7],
        "orientation": orientation,
        "value_labels": False,
    }


def _mirrored() -> dict[str, object]:
    return {
        "category": ["0-9", "10-19", "20-29"] * 2,
        "side": ["Female"] * 3 + ["Male"] * 3,
        "value": [12.0, 18.0, 15.0, 11.0, 16.0, 17.0],
        "mirror_side": "Female",
        "orientation": "horizontal",
        "value_labels": False,
    }


def _waterfall() -> dict[str, object]:
    return {
        "step": ["Initial", "Aeration", "Recovery", "Loss", "Final"],
        "delta": [5.0, 2.2, 1.4, -1.1, 7.5],
        "role": ["subtotal", "change", "change", "change", "total"],
        "value_labels": False,
    }


_CASE_DEFINITIONS = (
    ("simple", "simple_vertical", partial(_simple, orientation="vertical")),
    ("simple", "simple_horizontal", partial(_simple, orientation="horizontal")),
    ("simple", "simple_negative", partial(_simple, negative=True)),
    ("simple", "simple_value_labels", partial(_simple, labels=True)),
    ("grouped", "grouped_vertical", partial(_grouped, orientation="vertical")),
    ("grouped", "grouped_horizontal", partial(_grouped, orientation="horizontal")),
    ("grouped", "grouped_uncertainty", partial(_grouped, uncertainty=True)),
    ("stacked", "stacked_vertical", partial(_stacked, orientation="vertical")),
    ("stacked", "stacked_horizontal", partial(_stacked, orientation="horizontal")),
    ("normalized_stacked", "normalized_stacked", _normalized),
    ("grouped_stacked", "grouped_stacked", _grouped_stacked),
    ("diverging_stacked", "diverging_stacked", _diverging),
    ("range", "range_vertical", partial(_range, orientation="vertical")),
    ("range", "range_horizontal", partial(_range, orientation="horizontal")),
    ("mirrored", "mirrored", _mirrored),
    ("waterfall", "waterfall", _waterfall),
)

GALLERY_CASES = {
    f"bar/{template}": tuple(
        TemplateGalleryCase(
            example_id=output,
            geometry="single-column",
            output_id=f"bar/{output}",
            values=values,
        )
        for selected_template, output, values in _CASE_DEFINITIONS
        if selected_template == template
    )
    for template in {item[0] for item in _CASE_DEFINITIONS}
}

BAR_GALLERY_CASE_IDS = tuple(item[1] for item in _CASE_DEFINITIONS)

__all__ = ["BAR_GALLERY_CASE_IDS", "GALLERY_CASES"]
