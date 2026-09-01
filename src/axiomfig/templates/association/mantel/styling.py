"""Mantel-owned deterministic visual contract access and semantic mappings."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from axiomfig.config import load_contracts
from axiomfig.style import palette_color, palette_reference_color


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _finite_number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _validate_mantel_contract(contract: Mapping[str, Any]) -> None:
    matrix = _mapping(contract.get("matrix"), "plots.mantel.matrix")
    for name in (
        "minimum_cell_side",
        "maximum_cell_side",
        "source_label_gap_pt",
        "source_group_gap_pt",
        "source_boundary_padding_pt",
    ):
        _finite_number(matrix.get(name), f"plots.mantel.matrix.{name}", positive=True)
    minimum_side = float(matrix["minimum_cell_side"])
    maximum_side = float(matrix["maximum_cell_side"])
    if minimum_side >= maximum_side or maximum_side > 1.0:
        raise ValueError("Mantel cell sides must be ordered and no larger than one cell")

    nodes = _mapping(contract.get("nodes"), "plots.mantel.nodes")
    for name in ("source_size_ratio", "target_size_ratio"):
        _finite_number(nodes.get(name), f"plots.mantel.nodes.{name}", positive=True)

    links = _mapping(contract.get("links"), "plots.mantel.links")
    _finite_number(
        links.get("curve_curvature"),
        "plots.mantel.links.curve_curvature",
        positive=True,
    )
    for name in ("significant_alpha", "nonsignificant_alpha"):
        alpha = _finite_number(links.get(name), f"plots.mantel.links.{name}")
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"plots.mantel.links.{name} must be between 0 and 1")

    strength_breaks = tuple(float(value) for value in links.get("strength_breaks", ()))
    widths = tuple(links.get("widths_pt", ()))
    if strength_breaks != tuple(sorted(strength_breaks)) or len(strength_breaks) != 2:
        raise ValueError("Mantel strength breaks must contain two ordered values")
    if len(widths) != 3:
        raise ValueError("Mantel link widths must match their bins")
    for index, width in enumerate(widths):
        _finite_number(width, f"plots.mantel.links.widths_pt[{index}]", positive=True)

    modes = _mapping(links.get("p_value_modes"), "plots.mantel.links.p_value_modes")
    expected_bins = {"canonical": 3, "detailed": 4}
    if set(modes) != set(expected_bins):
        raise ValueError("Mantel P-value modes must contain canonical and detailed")
    for mode, bin_count in expected_bins.items():
        selected = _mapping(modes[mode], f"plots.mantel.links.p_value_modes.{mode}")
        breaks = tuple(float(value) for value in selected.get("breaks", ()))
        colors = tuple(selected.get("colors", ()))
        if breaks != tuple(sorted(breaks)) or len(breaks) != bin_count - 1:
            raise ValueError(f"Mantel {mode} P-value breaks do not match their bins")
        if len(colors) != bin_count:
            raise ValueError(f"Mantel {mode} P-value colors do not match their bins")
    if links.get("nonsignificant_mode") not in {"hide", "fade", "show"}:
        raise ValueError("plots.mantel.links.nonsignificant_mode must be hide, fade, or show")


def mantel_plot_contract() -> Mapping[str, Any]:
    """Return the validated, family-owned deterministic Mantel visual contract."""
    plots = _mapping(load_contracts().style.get("plots"), "plots")
    contract = _mapping(plots.get("mantel"), "plots.mantel")
    _validate_mantel_contract(contract)
    return contract


def mantel_visual_color(name: str) -> str:
    """Resolve a Mantel neutral or structural color through shared palette tokens."""
    matrix = _mapping(mantel_plot_contract().get("matrix"), "plots.mantel.matrix")
    key = f"{name}_color"
    if key not in matrix:
        raise ValueError(f"unknown Mantel visual color: {name!r}")
    reference = matrix[key]
    if isinstance(reference, str):
        return palette_color(reference)
    return palette_reference_color(reference)


def mantel_link_width(mantel_r: float) -> float:
    """Map precomputed Mantel r to the canonical discrete stroke width."""
    if not math.isfinite(mantel_r) or not -1.0 <= mantel_r <= 1.0:
        raise ValueError("mantel_r must be between -1 and 1")
    links = _mapping(mantel_plot_contract().get("links"), "plots.mantel.links")
    breaks = tuple(float(value) for value in links["strength_breaks"])
    widths = tuple(float(value) for value in links["widths_pt"])
    magnitude = abs(mantel_r)
    index = 0 if magnitude < breaks[0] else 1 if magnitude < breaks[1] else 2
    return widths[index]


def mantel_p_style(p_value: float, *, mode: str = "canonical") -> dict[str, Any]:
    """Map precomputed P to the canonical color and opacity tokens."""
    if not math.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
        raise ValueError("p_value must be between 0 and 1")
    links = _mapping(mantel_plot_contract().get("links"), "plots.mantel.links")
    modes = _mapping(links.get("p_value_modes"), "plots.mantel.links.p_value_modes")
    if mode not in modes:
        raise ValueError(f"unknown Mantel P-value mode: {mode!r}")
    selected = _mapping(modes[mode], f"plots.mantel.links.p_value_modes.{mode}")
    breaks = tuple(float(value) for value in selected["breaks"])
    references = tuple(selected["colors"])
    index = next(
        (position for position, boundary in enumerate(breaks) if p_value < boundary), len(breaks)
    )
    palette_name, color_name = references[index]
    color = palette_color(str(color_name), palette_name=str(palette_name))
    significant = index < len(breaks)
    alpha_key = "significant_alpha" if significant else "nonsignificant_alpha"
    labels = (
        ("p<0.01", "0.01<=p<0.05", "p>=0.05")
        if mode == "canonical"
        else ("p<0.001", "0.001<=p<0.01", "0.01<=p<0.05", "p>=0.05")
    )
    return {
        "color": color,
        "alpha": float(links[alpha_key]),
        "significant": significant,
        "bin": labels[index],
    }
