"""Mantel-owned deterministic visual contract access and semantic mappings."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from itertools import pairwise
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
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _finite_numbers(value: object, name: str) -> tuple[float, ...]:
    values = _sequence(value, name)
    return tuple(_finite_number(item, f"{name}[{index}]") for index, item in enumerate(values))


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a sequence")
    return tuple(value)


def _validate_mantel_contract(contract: Mapping[str, Any]) -> None:
    matrix = _mapping(contract.get("matrix"), "plots.mantel.matrix")
    for name in (
        "minimum_cell_side",
        "maximum_cell_side",
        "source_label_gap_pt",
        "source_group_gap_pt",
        "source_boundary_padding_pt",
        "source_label_max_width_pt",
    ):
        _finite_number(matrix.get(name), f"plots.mantel.matrix.{name}", positive=True)
    _finite_number(matrix.get("target_rail_offset"), "plots.mantel.matrix.target_rail_offset")
    minimum_side = float(matrix["minimum_cell_side"])
    maximum_side = float(matrix["maximum_cell_side"])
    if minimum_side >= maximum_side or maximum_side > 1.0:
        raise ValueError("Mantel cell sides must be ordered and no larger than one cell")

    nodes = _mapping(contract.get("nodes"), "plots.mantel.nodes")
    for name in ("source_size_ratio", "target_size_ratio"):
        _finite_number(nodes.get(name), f"plots.mantel.nodes.{name}", positive=True)

    ornaments = _mapping(contract.get("ornaments"), "plots.mantel.ornaments")
    if set(ornaments) != {"legend"}:
        raise ValueError("plots.mantel.ornaments must contain only legend")
    legend_layout = _mapping(ornaments.get("legend"), "plots.mantel.ornaments.legend")
    for name in ("borderpad", "labelspacing", "handletextpad", "columnspacing"):
        value = _finite_number(legend_layout.get(name), f"plots.mantel.ornaments.legend.{name}")
        if value < 0.0:
            raise ValueError(f"plots.mantel.ornaments.legend.{name} must be nonnegative")

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
    legend = _mapping(links.get("legend"), "plots.mantel.links.legend")
    legend_alpha = _finite_number(
        legend.get("nonsignificant_alpha"),
        "plots.mantel.links.legend.nonsignificant_alpha",
    )
    if not 0.0 <= legend_alpha <= 1.0:
        raise ValueError("Mantel legend nonsignificant alpha must be between 0 and 1")
    _finite_number(
        legend.get("linewidth_ratio"),
        "plots.mantel.links.legend.linewidth_ratio",
        positive=True,
    )

    strength_breaks = _finite_numbers(
        links.get("strength_breaks"), "plots.mantel.links.strength_breaks"
    )
    widths = _finite_numbers(links.get("widths_pt"), "plots.mantel.links.widths_pt")
    if (
        strength_breaks != tuple(sorted(strength_breaks))
        or len(strength_breaks) != 2
        or any(not 0.0 < value < 1.0 for value in strength_breaks)
    ):
        raise ValueError("Mantel strength breaks must contain two ordered values")
    if len(widths) != 3:
        raise ValueError("Mantel link widths must match their bins")
    if any(width <= 0.0 for width in widths):
        raise ValueError("Mantel link widths must be positive")

    modes = _mapping(links.get("p_value_modes"), "plots.mantel.links.p_value_modes")
    expected_bins = {"canonical": 3, "detailed": 4}
    if set(modes) != set(expected_bins):
        raise ValueError("Mantel P-value modes must contain canonical and detailed")
    for mode, bin_count in expected_bins.items():
        selected = _mapping(modes[mode], f"plots.mantel.links.p_value_modes.{mode}")
        breaks = _finite_numbers(
            selected.get("breaks"), f"plots.mantel.links.p_value_modes.{mode}.breaks"
        )
        colors = _sequence(
            selected.get("colors"), f"plots.mantel.links.p_value_modes.{mode}.colors"
        )
        if (
            breaks != tuple(sorted(breaks))
            or len(breaks) != bin_count - 1
            or any(not 0.0 < value < 1.0 for value in breaks)
        ):
            raise ValueError(f"Mantel {mode} P-value breaks do not match their bins")
        if len(colors) != bin_count:
            raise ValueError(f"Mantel {mode} P-value colors do not match their bins")
        for reference in colors:
            if (
                not isinstance(reference, Sequence)
                or isinstance(reference, (str, bytes))
                or len(reference) != 2
                or not all(isinstance(token, str) and token for token in reference)
            ):
                raise ValueError(f"Mantel {mode} P-value palette reference is invalid")
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


def _legend_samples(breaks: tuple[float, ...]) -> tuple[float, ...]:
    edges = (0.0, *breaks, 1.0)
    return tuple((lower + upper) / 2.0 for lower, upper in pairwise(edges))


def mantel_strength_legend_bins() -> tuple[tuple[float, str], ...]:
    """Return strength legend samples and labels from the executable break contract."""
    links = _mapping(mantel_plot_contract().get("links"), "plots.mantel.links")
    breaks = tuple(float(value) for value in links["strength_breaks"])
    labels = (
        f"< {breaks[0]:.2f}",
        *(f"{lower:.2f}-{upper:.2f}" for lower, upper in pairwise(breaks)),
        f">= {breaks[-1]:.2f}",
    )
    return tuple(zip(_legend_samples(breaks), labels, strict=True))


def mantel_p_legend_bins(mode: str) -> tuple[tuple[float, str], ...]:
    """Return P-value legend samples and labels from the selected break contract."""
    links = _mapping(mantel_plot_contract().get("links"), "plots.mantel.links")
    modes = _mapping(links.get("p_value_modes"), "plots.mantel.links.p_value_modes")
    if mode not in modes:
        raise ValueError(f"unknown Mantel P-value mode: {mode!r}")
    selected = _mapping(modes[mode], f"plots.mantel.links.p_value_modes.{mode}")
    breaks = tuple(float(value) for value in selected["breaks"])
    labels = (
        f"< {breaks[0]:g}",
        *(f"{lower:g}-{upper:g}" for lower, upper in pairwise(breaks)),
        f">= {breaks[-1]:g}",
    )
    return tuple(zip(_legend_samples(breaks), labels, strict=True))


def mantel_legend_visuals() -> Mapping[str, Any]:
    """Return the family-owned visual contract for Mantel legend handles."""
    links = _mapping(mantel_plot_contract().get("links"), "plots.mantel.links")
    return _mapping(links.get("legend"), "plots.mantel.links.legend")


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
        f"p<{breaks[0]:g}",
        *(f"{lower:g}<=p<{upper:g}" for lower, upper in pairwise(breaks)),
        f"p>={breaks[-1]:g}",
    )
    return {
        "color": color,
        "alpha": float(links[alpha_key]),
        "significant": significant,
        "bin": labels[index],
    }
