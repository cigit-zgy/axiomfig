from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from types import MappingProxyType
from typing import Any

import matplotlib as mpl
from cycler import cycler

from axiomfig.structured_io import load_yaml

CONFIG_FILENAMES = ("style.yaml", "fonts.yaml", "colors.yaml")


@dataclass(frozen=True)
class Contracts:
    style: Mapping[str, Any]
    fonts: Mapping[str, Any]
    colors: Mapping[str, Any]


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _resolve_root(config_root: Path | None) -> Traversable:
    root: Traversable = (
        Path(config_root).expanduser().resolve()
        if config_root is not None
        else files("axiomfig").joinpath("resources", "styles")
    )
    if all(root.joinpath(name).is_file() for name in CONFIG_FILENAMES):
        return root
    raise FileNotFoundError(f"AxiomFig canonical YAML files were not found in: {root}")


def _load_mapping(path: Traversable) -> Mapping[str, Any]:
    loaded = load_yaml(path.read_text(encoding="utf-8"), source=path.name)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping")
    if loaded.get("version") != 1:
        raise ValueError(f"{path.name} must declare version: 1")
    return _freeze(loaded)


def _finite_number(
    value: Any, name: str, *, positive: bool = False, nonnegative: bool = False
) -> float:
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
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _validate_positive_style_conventions(value: Mapping[str, Any], prefix: str = "") -> None:
    """Validate reusable positive-token naming conventions without family knowledge."""
    for name, selected in value.items():
        dotted = f"{prefix}.{name}" if prefix else str(name)
        if isinstance(selected, Mapping):
            _validate_positive_style_conventions(selected, dotted)
        elif str(name).endswith(("_size_ratio", "_curvature")):
            _finite_number(selected, dotted, positive=True)


def _required_mapping(container: Mapping[str, Any], key: str, prefix: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{prefix}.{key} must be a mapping")
    return value


def _required_sequence(container: Mapping[str, Any], key: str, prefix: str) -> tuple[Any, ...]:
    value = container.get(key)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{prefix}.{key} must be a sequence")
    return tuple(value)


def _validate_style_values(style: Mapping[str, Any]) -> None:
    required = (
        "geometry",
        "typography",
        "stroke",
        "ticks",
        "axes",
        "legend",
        "colorbar",
        "panel",
        "output",
        "layout",
        "plots",
        "rendering",
    )
    for key in required:
        if not isinstance(style.get(key), Mapping):
            raise ValueError(f"style.yaml is missing mapping: {key}")
    _validate_positive_style_conventions(style)

    geometry_root = _required_mapping(style, "geometry", "style")
    for name in geometry_root:
        _required_mapping(geometry_root, str(name), "geometry")
    typography = _required_mapping(style, "typography", "style")
    _required_mapping(typography, "sizes_pt", "typography")
    ticks = _required_mapping(style, "ticks", "style")
    _required_mapping(ticks, "geometry", "ticks")
    _required_mapping(ticks, "categorical", "ticks")
    for surface in ("open", "filled"):
        selected = _required_mapping(ticks, surface, "ticks")
        for level in ("major", "minor"):
            _required_mapping(selected, level, f"ticks.{surface}")
    colorbar = _required_mapping(style, "colorbar", "style")
    _required_mapping(colorbar, "vertical", "colorbar")
    layout = _required_mapping(style, "layout", "style")
    _required_mapping(layout, "multi_panel", "layout")
    plots = _required_mapping(style, "plots", "style")
    for name in (
        "confidence_interval",
        "line_marker",
        "scatter",
        "errorbar",
        "boxplot",
        "violin",
        "bar",
        "histogram",
    ):
        _required_mapping(plots, name, "plots")

    positive: list[tuple[Any, str]] = []
    for name, geometry in style["geometry"].items():
        positive.extend(
            (geometry[token], f"geometry.{name}.{token}") for token in ("width_mm", "aspect")
        )
    positive.extend(
        (value, f"typography.sizes_pt.{name}")
        for name, value in style["typography"]["sizes_pt"].items()
    )
    positive.extend(
        (style["stroke"][name], f"stroke.{name}") for name in ("main_stroke_pt", "fill_edge_pt")
    )
    for surface in ("open", "filled"):
        for level in ("major", "minor"):
            token = style["ticks"][surface][level]["length_token"]
            if token not in {"major", "minor"}:
                raise ValueError(f"ticks.{surface}.{level}.length_token is invalid")
    positive.extend(
        (
            (
                style["ticks"]["geometry"]["minor_to_major_inward_ratio"],
                "ticks.geometry.minor_to_major_inward_ratio",
            ),
            (style["ticks"]["geometry"]["minor_length_pt"], "ticks.geometry.minor_length_pt"),
            (style["ticks"]["geometry"]["major_length_pt"], "ticks.geometry.major_length_pt"),
            (style["legend"]["handlelength"], "legend.handlelength"),
            (style["legend"]["columnspacing"], "legend.columnspacing"),
            (style["legend"]["handletextpad"], "legend.handletextpad"),
            (style["legend"]["labelspacing"], "legend.labelspacing"),
            (style["panel"]["font_size_pt"], "panel.font_size_pt"),
            (style["plots"]["line_marker"]["marker_size_pt"], "plots.line_marker.marker_size_pt"),
            (style["plots"]["scatter"]["marker_size_pt2"], "plots.scatter.marker_size_pt2"),
            (style["plots"]["errorbar"]["marker_size_pt"], "plots.errorbar.marker_size_pt"),
            (style["plots"]["errorbar"]["cap_size_pt"], "plots.errorbar.cap_size_pt"),
            (style["plots"]["boxplot"]["width"], "plots.boxplot.width"),
            (style["plots"]["boxplot"]["combined_width"], "plots.boxplot.combined_width"),
            (style["plots"]["violin"]["width"], "plots.violin.width"),
            (style["plots"]["bar"]["single_width"], "plots.bar.single_width"),
            (style["plots"]["bar"]["group_width"], "plots.bar.group_width"),
            (style["colorbar"]["vertical"]["width_pt"], "colorbar.vertical.width_pt"),
            (style["colorbar"]["vertical"]["gap_pt"], "colorbar.vertical.gap_pt"),
            (
                style["colorbar"]["vertical"]["length_fraction"],
                "colorbar.vertical.length_fraction",
            ),
            (style["rendering"]["dpi"], "rendering.dpi"),
        )
    )
    for value, name in positive:
        _finite_number(value, name, positive=True)
    for value, name in (
        (style["ticks"]["categorical"]["length_pt"], "ticks.categorical.length_pt"),
        (style["legend"]["top_gap_pt"], "legend.top_gap_pt"),
        (style["legend"]["borderpad"], "legend.borderpad"),
        (style["legend"]["borderaxespad"], "legend.borderaxespad"),
        (style["output"]["padding_pt"], "output.padding_pt"),
        (
            style["layout"]["multi_panel"]["horizontal_gap_pt"],
            "layout.multi_panel.horizontal_gap_pt",
        ),
        (
            style["layout"]["multi_panel"]["vertical_gap_pt"],
            "layout.multi_panel.vertical_gap_pt",
        ),
        (
            style["layout"]["multi_panel"]["containment_padding_pt"],
            "layout.multi_panel.containment_padding_pt",
        ),
        (
            style["plots"]["violin"]["limit_padding_fraction"],
            "plots.violin.limit_padding_fraction",
        ),
    ):
        _finite_number(value, name, nonnegative=True)
    margin_mode = style["output"]["margin_mode"]
    allowed_modes = _required_sequence(style["output"], "allowed_margin_modes", "output")
    if not all(isinstance(mode, str) for mode in allowed_modes):
        raise ValueError("output.allowed_margin_modes must contain strings")
    if margin_mode not in allowed_modes or set(allowed_modes) != {"tight", "normal", "custom"}:
        raise ValueError("output margin mode must be tight, normal, or custom")
    for value, name in (
        (style["panel"]["left_offset_pt"], "panel.left_offset_pt"),
        (style["panel"]["top_offset_pt"], "panel.top_offset_pt"),
    ):
        _finite_number(value, name)
    vertical_colorbar = style["colorbar"]["vertical"]
    if vertical_colorbar["alignment"] != "center":
        raise ValueError("colorbar.vertical.alignment must be center")
    if vertical_colorbar["tick_side"] != "right":
        raise ValueError("colorbar.vertical.tick_side must be right")
    if vertical_colorbar["label_side"] != "right":
        raise ValueError("colorbar.vertical.label_side must be right")
    if float(vertical_colorbar["length_fraction"]) > 1.0:
        raise ValueError("colorbar.vertical.length_fraction must not exceed one")
    for dotted, alpha in (
        ("plots.confidence_interval.alpha", style["plots"]["confidence_interval"]["alpha"]),
        ("plots.scatter.alpha", style["plots"]["scatter"]["alpha"]),
        ("plots.boxplot.alpha", style["plots"]["boxplot"]["alpha"]),
        ("plots.violin.alpha", style["plots"]["violin"]["alpha"]),
        ("plots.violin.combined_alpha", style["plots"]["violin"]["combined_alpha"]),
        ("plots.bar.alpha", style["plots"]["bar"]["alpha"]),
        ("plots.histogram.alpha", style["plots"]["histogram"]["alpha"]),
    ):
        value = _finite_number(alpha, dotted)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{dotted} must be between 0 and 1")
    decimals = style["plots"]["bar"]["decimals"]
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        raise ValueError("plots.bar.decimals must be a nonnegative integer")


def _validate_style(style: Mapping[str, Any]) -> None:
    try:
        _validate_style_values(style)
    except KeyError as exc:
        raise ValueError(f"style.yaml is missing required field: {exc.args[0]}") from exc


@lru_cache(maxsize=16)
def load_contracts(config_root: Path | None = None) -> Contracts:
    """Load immutable contracts once per resource root for repeated deterministic rendering."""
    root = _resolve_root(config_root)
    style = _load_mapping(root.joinpath("style.yaml"))
    fonts = _load_mapping(root.joinpath("fonts.yaml"))
    colors = _load_mapping(root.joinpath("colors.yaml"))
    _validate_style(style)
    return Contracts(style=style, fonts=fonts, colors=colors)


def get_token(contracts: Contracts, dotted_path: str) -> Any:
    current: Any = contracts
    for part in dotted_path.split("."):
        if isinstance(current, Contracts):
            if part not in {"style", "fonts", "colors"}:
                raise KeyError(dotted_path)
            current = getattr(current, part)
        elif isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            raise KeyError(dotted_path)
    return current


def _positive_number(value: Any, name: str) -> float:
    return _finite_number(value, name, positive=True)


def build_rcparams(
    contracts: Contracts, *, geometry: str = "single-column", typography: str = "sans"
) -> dict[Any, Any]:
    geometries = contracts.style["geometry"]
    if geometry not in geometries:
        raise ValueError(f"unknown geometry: {geometry}")
    modes = contracts.fonts["modes"]
    if typography not in modes:
        raise ValueError(f"unknown typography: {typography}")
    geometry_spec = geometries[geometry]
    width_mm = _positive_number(geometry_spec["width_mm"], f"geometry.{geometry}.width_mm")
    aspect = _positive_number(geometry_spec["aspect"], f"geometry.{geometry}.aspect")
    sizes = contracts.style["typography"]["sizes_pt"]
    stroke = contracts.style["stroke"]
    ticks = contracts.style["ticks"]
    mode = modes[typography]
    text_family = contracts.fonts["families"][mode["text"]]
    math_family = contracts.fonts["families"][mode["math"]]
    mono_family = contracts.fonts["families"][mode["mono"]]
    color_map = contracts.colors["palettes"][contracts.colors["default"]]
    params: dict[str, object] = {
        "figure.figsize": (width_mm / 25.4, width_mm / aspect / 25.4),
        "font.family": "sans-serif" if typography == "sans" else "serif",
        "font.sans-serif": [text_family["matplotlib_family"]],
        "font.serif": [text_family["matplotlib_family"]],
        "font.monospace": [mono_family["matplotlib_family"]],
        "font.size": float(sizes["base"]),
        "axes.labelsize": float(sizes["label"]),
        "axes.titlesize": float(sizes["title"]),
        "xtick.labelsize": float(sizes["small"]),
        "ytick.labelsize": float(sizes["small"]),
        "legend.fontsize": float(sizes["small"]),
        "axes.linewidth": float(stroke["main_stroke_pt"]),
        "lines.linewidth": float(stroke["main_stroke_pt"]),
        "xtick.major.width": float(stroke["main_stroke_pt"]),
        "ytick.major.width": float(stroke["main_stroke_pt"]),
        "patch.linewidth": float(stroke["fill_edge_pt"]),
        "lines.markeredgewidth": float(stroke["fill_edge_pt"]),
        "xtick.major.size": float(ticks["geometry"]["major_length_pt"]),
        "ytick.major.size": float(ticks["geometry"]["major_length_pt"]),
        "xtick.minor.size": float(ticks["geometry"]["minor_length_pt"]),
        "ytick.minor.size": float(ticks["geometry"]["minor_length_pt"]),
        "xtick.direction": str(ticks["open"]["major"]["direction"]),
        "ytick.direction": str(ticks["open"]["major"]["direction"]),
        "xtick.top": False,
        "ytick.right": False,
        "xtick.labeltop": False,
        "ytick.labelright": False,
        "legend.frameon": bool(contracts.style["legend"]["frame"]),
        "legend.handlelength": float(contracts.style["legend"]["handlelength"]),
        "axes.prop_cycle": cycler(color=tuple(color_map.values())),
        "image.cmap": str(contracts.colors["colormaps"]["sequential"]),
        "image.interpolation": str(contracts.style["plots"]["heatmap"]["interpolation"]),
        "mathtext.fontset": "custom",
        "mathtext.rm": str(math_family["matplotlib_family"]),
        "mathtext.it": str(math_family["matplotlib_family"]),
        "mathtext.bf": str(math_family["matplotlib_family"]),
        "mathtext.fallback": None,
        "pdf.fonttype": int(contracts.style["rendering"]["pdf_fonttype"]),
        "ps.fonttype": int(contracts.style["rendering"]["ps_fonttype"]),
        "savefig.dpi": int(contracts.style["rendering"]["dpi"]),
        "savefig.transparent": bool(contracts.style["rendering"]["transparent"]),
    }
    validated = mpl.RcParams(params)
    return {key: value for key, value in validated.items()}
