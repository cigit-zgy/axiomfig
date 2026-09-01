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


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _string_sequence(container: Mapping[str, Any], key: str, prefix: str) -> tuple[str, ...]:
    values = _required_sequence(container, key, prefix)
    if not values or not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"{prefix}.{key} must contain non-empty strings")
    return values


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
        "series",
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
    axes = _required_mapping(style, "axes", "style")
    nice_linear = _required_mapping(axes, "nice_linear", "axes")
    layout = _required_mapping(style, "layout", "style")
    single_panel = _required_mapping(layout, "single_panel", "layout")
    margins = _required_mapping(single_panel, "margins", "layout.single_panel")
    _required_mapping(layout, "multi_panel", "layout")
    series = _required_mapping(style, "series", "style")
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
        "heatmap",
    ):
        _required_mapping(plots, name, "plots")

    target_ticks = _required_sequence(nice_linear, "target_major_ticks", "axes.nice_linear")
    if len(target_ticks) != 2:
        raise ValueError("axes.nice_linear.target_major_ticks must contain two values")
    target_low = _finite_number(
        target_ticks[0], "axes.nice_linear.target_major_ticks[0]", positive=True
    )
    target_high = _finite_number(
        target_ticks[1], "axes.nice_linear.target_major_ticks[1]", positive=True
    )
    if target_low > target_high:
        raise ValueError("axes.nice_linear.target_major_ticks must be ordered")
    step_mantissas = _required_sequence(nice_linear, "step_mantissas", "axes.nice_linear")
    if not step_mantissas:
        raise ValueError("axes.nice_linear.step_mantissas must not be empty")
    for index, value in enumerate(step_mantissas):
        _finite_number(value, f"axes.nice_linear.step_mantissas[{index}]", positive=True)
    _finite_number(
        nice_linear.get("minor_divisor"), "axes.nice_linear.minor_divisor", positive=True
    )
    _finite_number(
        nice_linear.get("whole_step_blank_fraction"),
        "axes.nice_linear.whole_step_blank_fraction",
        nonnegative=True,
    )

    for name in ("left", "right", "bottom", "top"):
        _finite_number(margins.get(name), f"layout.single_panel.margins.{name}")
    if not 0.0 <= float(margins["left"]) < float(margins["right"]) <= 1.0:
        raise ValueError("single-panel horizontal margins must be ordered within the figure")
    if not 0.0 <= float(margins["bottom"]) < float(margins["top"]) <= 1.0:
        raise ValueError("single-panel vertical margins must be ordered within the figure")

    line_styles = _string_sequence(series, "line_styles", "series")
    _string_sequence(series, "markers", "series")
    dash_pattern = _required_sequence(series, "long_dash_pattern", "series")
    if len(dash_pattern) != 2:
        raise ValueError("series.long_dash_pattern must contain two values")
    for index, value in enumerate(dash_pattern):
        _finite_number(value, f"series.long_dash_pattern[{index}]", positive=True)
    reference_style = _nonempty_string(
        series.get("reference_line_style"), "series.reference_line_style"
    )
    if reference_style not in line_styles:
        raise ValueError("series.reference_line_style must be present in series.line_styles")

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


def _validate_fonts(fonts: Mapping[str, Any]) -> None:
    modes = _required_mapping(fonts, "modes", "fonts")
    families = _required_mapping(fonts, "families", "fonts")
    _nonempty_string(fonts.get("bundle_subdir"), "fonts.bundle_subdir")
    _string_sequence(fonts, "search_roots", "fonts")
    default = _nonempty_string(fonts.get("default"), "fonts.default")
    if default not in modes:
        raise ValueError("fonts.default must name a typography mode")

    referenced: set[str] = set()
    for mode_name, _value in modes.items():
        mode = _required_mapping(modes, str(mode_name), "fonts.modes")
        for role in ("text", "math", "mono"):
            referenced.add(_nonempty_string(mode.get(role), f"fonts.modes.{mode_name}.{role}"))
    for family_name, _value in families.items():
        family = _required_mapping(families, str(family_name), "fonts.families")
        _nonempty_string(family.get("family"), f"fonts.families.{family_name}.family")
        _nonempty_string(
            family.get("matplotlib_family"), f"fonts.families.{family_name}.matplotlib_family"
        )
        filenames = _required_mapping(family, "filenames", f"fonts.families.{family_name}")
        _nonempty_string(
            filenames.get("regular"), f"fonts.families.{family_name}.filenames.regular"
        )
        for variant, filename in filenames.items():
            _nonempty_string(filename, f"fonts.families.{family_name}.filenames.{variant}")
    missing = referenced - set(families)
    if missing:
        raise ValueError(f"font modes reference unknown families: {sorted(missing)}")


def _validate_colors(colors: Mapping[str, Any]) -> None:
    palettes = _required_mapping(colors, "palettes", "colors")
    colormaps = _required_mapping(colors, "colormaps", "colors")
    constructed = _required_mapping(colors, "constructed_colormaps", "colors")
    default = _nonempty_string(colors.get("default"), "colors.default")
    if default not in palettes:
        raise ValueError("colors.default must name a palette")

    for palette_name, _value in palettes.items():
        palette = _required_mapping(palettes, str(palette_name), "colors.palettes")
        if not palette:
            raise ValueError(f"colors.palettes.{palette_name} must not be empty")
        for token, color in palette.items():
            selected = _nonempty_string(color, f"colors.palettes.{palette_name}.{token}")
            if len(selected) != 7 or not selected.startswith("#"):
                raise ValueError(f"colors.palettes.{palette_name}.{token} must be #RRGGBB")
            try:
                int(selected[1:], 16)
            except ValueError as exc:
                raise ValueError(f"colors.palettes.{palette_name}.{token} must be #RRGGBB") from exc
    for name, value in colormaps.items():
        _nonempty_string(value, f"colors.colormaps.{name}")
    if "sequential" not in colormaps:
        raise ValueError("colors.colormaps.sequential is required")
    for name in constructed:
        references = _required_sequence(constructed, str(name), "colors.constructed_colormaps")
        if len(references) < 2:
            raise ValueError(f"colors.constructed_colormaps.{name} needs at least two colors")
        for index, reference in enumerate(references):
            if (
                isinstance(reference, (str, bytes))
                or not isinstance(reference, Sequence)
                or len(reference) != 2
            ):
                raise ValueError(f"colors.constructed_colormaps.{name}[{index}] is invalid")
            palette_name = _nonempty_string(
                reference[0], f"colors.constructed_colormaps.{name}[{index}].palette"
            )
            token = _nonempty_string(
                reference[1], f"colors.constructed_colormaps.{name}[{index}].token"
            )
            if palette_name not in palettes or token not in palettes[palette_name]:
                raise ValueError(
                    f"colors.constructed_colormaps.{name}[{index}] references an unknown color"
                )


@lru_cache(maxsize=16)
def load_contracts(config_root: Path | None = None) -> Contracts:
    """Load immutable contracts once per resource root for repeated deterministic rendering."""
    root = _resolve_root(config_root)
    style = _load_mapping(root.joinpath("style.yaml"))
    fonts = _load_mapping(root.joinpath("fonts.yaml"))
    colors = _load_mapping(root.joinpath("colors.yaml"))
    _validate_style(style)
    _validate_fonts(fonts)
    _validate_colors(colors)
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
