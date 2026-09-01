"""Deterministic visual-contract calculations and artist styling."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Literal

import matplotlib as mpl
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.container import BarContainer
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

from axiomfig.config import Contracts, build_rcparams, load_contracts

_CONTRACTS = load_contracts()
MAIN_STROKE_PT = float(_CONTRACTS.style["stroke"]["main_stroke_pt"])
FILL_EDGE_PT = float(_CONTRACTS.style["stroke"]["fill_edge_pt"])


def palettes(contracts: Contracts | None = None) -> Mapping[str, Mapping[str, str]]:
    selected = contracts or load_contracts()
    return selected.colors["palettes"]


def palette_color(
    color_name: str, *, palette_name: str | None = None, contracts: Contracts | None = None
) -> str:
    """Resolve one canonical color without exposing palette storage to templates."""
    selected = contracts or load_contracts()
    selected_palette = palette_name or str(selected.colors["default"])
    try:
        return palettes(selected)[selected_palette][color_name]
    except KeyError as error:
        raise ValueError(f"unknown palette color: {selected_palette}.{color_name}") from error


def semantic_colormap(semantics: str, contracts: Contracts | None = None) -> str:
    selected = contracts or load_contracts()
    colormaps = selected.colors.get("colormaps")
    if not isinstance(colormaps, Mapping) or semantics not in colormaps:
        raise ValueError(f"unsupported color semantics: {semantics!r}")
    value = colormaps[semantics]
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid colormap for color semantics: {semantics!r}")
    return value


def palette_reference_color(reference: object, *, contracts: Contracts | None = None) -> str:
    """Resolve a ``[palette, token]`` reference from the canonical color contract."""
    if (
        not isinstance(reference, (list, tuple))
        or len(reference) != 2
        or not all(isinstance(item, str) for item in reference)
    ):
        raise ValueError("palette reference must contain palette and token names")
    return palette_color(reference[1], palette_name=reference[0], contracts=contracts)


def axiom_colormap(name: str, contracts: Contracts | None = None) -> LinearSegmentedColormap:
    """Construct an Axiom-native colormap exclusively from ``colors.yaml`` tokens."""
    selected = contracts or load_contracts()
    definitions = selected.colors.get("constructed_colormaps")
    if not isinstance(definitions, Mapping) or name not in definitions:
        raise ValueError(f"unknown Axiom colormap: {name!r}")
    references = definitions[name]
    if not isinstance(references, (list, tuple)) or len(references) < 2:
        raise ValueError(f"invalid Axiom colormap definition: {name!r}")
    colors = [palette_reference_color(reference, contracts=selected) for reference in references]
    return LinearSegmentedColormap.from_list(name, colors, N=257)


def mantel_plot_contract() -> Mapping[str, object]:
    """Return the central deterministic Mantel visual contract."""
    return load_contracts().style["plots"]["mantel"]


def mantel_visual_color(name: str) -> str:
    """Resolve a Mantel neutral/structural color through the shared contracts."""
    matrix = mantel_plot_contract()["matrix"]
    assert isinstance(matrix, Mapping)
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
    links = mantel_plot_contract()["links"]
    assert isinstance(links, Mapping)
    breaks = tuple(float(value) for value in links["strength_breaks"])
    widths = tuple(float(value) for value in links["widths_pt"])
    magnitude = abs(mantel_r)
    index = 0 if magnitude < breaks[0] else 1 if magnitude < breaks[1] else 2
    return widths[index]


def mantel_p_style(p_value: float, *, mode: str = "canonical") -> dict[str, object]:
    """Map precomputed P to the canonical color and opacity tokens."""
    if not math.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
        raise ValueError("p_value must be between 0 and 1")
    links = mantel_plot_contract()["links"]
    assert isinstance(links, Mapping)
    modes = links["p_value_modes"]
    if mode not in modes:
        raise ValueError(f"unknown Mantel P-value mode: {mode!r}")
    selected = modes[mode]
    breaks = tuple(float(value) for value in selected["breaks"])
    references = tuple(selected["colors"])
    index = next(
        (index for index, boundary in enumerate(breaks) if p_value < boundary), len(breaks)
    )
    palette_name, color_name = references[index]
    color = palette_color(str(color_name), palette_name=str(palette_name))
    significant = index < len(breaks)
    alpha_key = "significant_alpha" if significant else "nonsignificant_alpha"
    labels: tuple[str, ...]
    if mode == "canonical":
        labels = ("p<0.01", "0.01<=p<0.05", "p>=0.05")
    else:
        labels = ("p<0.001", "0.001<=p<0.01", "0.01<=p<0.05", "p>=0.05")
    return {
        "color": color,
        "alpha": float(links[alpha_key]),
        "significant": significant,
        "bin": labels[index],
    }


def render_xcolor(contracts: Contracts | None = None) -> str:
    selected = contracts or load_contracts()
    default_name = selected.colors["default"]
    definitions = [
        f"\\definecolor{{{name}}}{{HTML}}{{{value.removeprefix('#')}}}"
        for name, value in palettes(selected)[default_name].items()
    ]
    for palette_name, values in palettes(selected).items():
        if not palette_name.startswith("axiom_"):
            continue
        prefix = palette_name.removeprefix("axiom_").title().replace("_", "")
        definitions.extend(
            f"\\definecolor{{Axiom{prefix}{name.removeprefix('Axiom')}}}"
            f"{{HTML}}{{{value.removeprefix('#')}}}"
            for name, value in values.items()
        )
    return (
        "% Generated from packaged colors.yaml; do not edit manually.\n"
        + "\n".join(definitions)
        + "\n"
    )


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


def apply_axis_contract(axis: Axes, surface: Literal["open", "filled"] = "open") -> None:
    contracts = load_contracts()
    if surface not in {"open", "filled"}:
        raise ValueError("surface must be 'open' or 'filled'")
    policy = contracts.style["ticks"][surface]
    major_length, minor_length = tick_lengths()
    for coordinate_axis in (axis.xaxis, axis.yaxis):
        if coordinate_axis.get_scale() == "linear":
            coordinate_axis.set_minor_locator(AutoMinorLocator(2))
    axis.tick_params(
        axis="both",
        which="major",
        direction=str(policy["major"]["direction"]),
        length=major_length,
        width=MAIN_STROKE_PT,
        top=False,
        right=False,
        labeltop=False,
        labelright=False,
    )
    axis.tick_params(
        axis="both",
        which="minor",
        direction=str(policy["minor"]["direction"]),
        length=minor_length,
        width=MAIN_STROKE_PT,
        top=False,
        right=False,
    )


def apply_categorical_axis(axis: Axes, coordinate: Literal["x", "y"] = "x") -> None:
    axis.tick_params(axis=coordinate, which="both", length=0.0)


def apply_nice_linear_axis(
    axis: Axes, data_min: float, data_max: float, *, coordinate: Literal["x", "y"] = "x"
) -> None:
    result = nice_linear_axis(data_min, data_max)
    coordinate_axis = axis.xaxis if coordinate == "x" else axis.yaxis
    if coordinate_axis.get_scale() != "linear":
        return
    coordinate_axis.set_major_locator(MultipleLocator(result.major_step))
    coordinate_axis.set_minor_locator(MultipleLocator(result.minor_step))
    (axis.set_xlim if coordinate == "x" else axis.set_ylim)(result.lower, result.upper)


def _reserve_bar_label_headroom(axis: Axes, containers: list[BarContainer]) -> None:
    patches = [patch for container in containers for patch in container.patches]
    if not patches:
        return
    orientation = containers[0].orientation
    endpoints = (
        [patch.get_x() + patch.get_width() for patch in patches]
        if orientation == "horizontal"
        else [patch.get_y() + patch.get_height() for patch in patches]
    )
    lower, upper = axis.get_xlim() if orientation == "horizontal" else axis.get_ylim()
    span = max(abs(upper - lower), max(abs(value) for value in endpoints), 1.0)
    padded = (min(lower, min(endpoints) - span * 0.05), max(upper, max(endpoints) + span * 0.05))
    (axis.set_xlim if orientation == "horizontal" else axis.set_ylim)(*padded)


def _stroke_width(token: object) -> float:
    stroke = load_contracts().style["stroke"]
    keys = {"main_stroke": "main_stroke_pt", "fill_edge": "fill_edge_pt"}
    try:
        return float(stroke[keys[str(token)]])
    except KeyError as error:
        raise ValueError(f"unknown stroke token: {token}") from error


def add_bar_value_labels(axis: Axes, containers: Iterable[BarContainer], decimals: int = 2) -> None:
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    selected = list(containers)
    _reserve_bar_label_headroom(axis, selected)
    contract = load_contracts().style["plots"]["bar"]
    for container in selected:
        for patch in container.patches:
            patch.set_alpha(None)
            patch.set_facecolor(_face_rgba(patch.get_facecolor(), float(contract["alpha"])))
            patch.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
            patch.set_linewidth(_stroke_width(contract["edge_width_token"]))
        values = np.asarray(container.datavalues, dtype=float)
        axis.bar_label(
            container,
            labels=[f"{value:.{decimals}f}" for value in values],
            padding=2.0,
        )


def _face_rgba(color: object, alpha: float) -> tuple[float, float, float, float]:
    red, green, blue, _ = mcolors.to_rgba(color)
    return red, green, blue, alpha


def _collection_face_alpha(collection: object, alpha: float) -> None:
    facecolors = collection.get_facecolors()  # type: ignore[attr-defined]
    if len(facecolors):
        collection.set_facecolors(  # type: ignore[attr-defined]
            [_face_rgba(color, alpha) for color in facecolors]
        )
    collection.set_alpha(None)  # type: ignore[attr-defined]


def apply_scatter_contract(collection: PathCollection, *, size_ratio: float = 1.0) -> None:
    if not math.isfinite(size_ratio) or size_ratio <= 0.0:
        raise ValueError("scatter marker size ratio must be positive")
    contract = load_contracts().style["plots"]["scatter"]
    _collection_face_alpha(collection, float(contract["alpha"]))
    collection.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
    collection.set_linewidth(_stroke_width(contract["edge_width_token"]))
    collection.set_sizes([float(contract["marker_size_pt2"]) * size_ratio])


def apply_distribution_point_contract(collection: PathCollection) -> None:
    """Apply the shared contract for dense raw observations in distributions."""
    plots = load_contracts().style["plots"]
    base_size = float(plots["scatter"]["marker_size_pt2"])
    point_size = float(plots["distribution"]["raw_point_size_pt2"])
    apply_scatter_contract(collection, size_ratio=point_size / base_size)


def apply_filled_collection_contract(
    collection: object, *, alpha: float | None = None, edge_width_token: str = "fill_edge"
) -> None:
    """Apply the shared filled-geometry face/edge contract to a collection."""
    if alpha is not None:
        _collection_face_alpha(collection, alpha)
    collection.set_edgecolor(mcolors.to_rgba("black", 1.0))  # type: ignore[attr-defined]
    collection.set_linewidth(_stroke_width(edge_width_token))  # type: ignore[attr-defined]


def line_marker_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["line_marker"]
    return {
        "marker": str(contract["marker"]),
        "markersize": float(contract["marker_size_pt"]),
        "markeredgecolor": str(contract["edge_color"]),
        "markeredgewidth": _stroke_width(contract["edge_width_token"]),
    }


def confidence_interval_kwargs(color: object | None = None) -> dict[str, object]:
    contract = load_contracts().style["plots"]["confidence_interval"]
    selected_color = color or mpl.rcParams["axes.prop_cycle"].by_key()["color"][0]
    return {
        "facecolor": _face_rgba(selected_color, float(contract["alpha"])),
        "edgecolor": mcolors.to_rgba(str(contract["edge_color"]), 1.0),
        "linewidth": _stroke_width(contract["edge_width_token"]),
    }


def _line_style(value: object) -> object:
    aliases: dict[str, object] = {
        "solid": "-",
        "dashdot": "-.",
        "dotted": ":",
    }
    if str(value) == "long-dash":
        pattern = load_contracts().style["series"]["long_dash_pattern"]
        return 0, tuple(float(item) for item in pattern)
    try:
        return aliases[str(value)]
    except KeyError as error:
        raise ValueError(f"unknown line style token: {value}") from error


def series_style(index: int, *, include_marker: bool = True) -> dict[str, object]:
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("series index must be a nonnegative integer")
    contract = load_contracts().style["series"]
    colors = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    line_styles = contract["line_styles"]
    markers = contract["markers"]
    result: dict[str, object] = {
        "color": colors[index % len(colors)],
        "linestyle": _line_style(line_styles[index % len(line_styles)]),
    }
    if include_marker:
        result["marker"] = str(markers[index % len(markers)])
    return result


def reference_line_kwargs() -> dict[str, object]:
    contract = load_contracts().style["series"]
    return {
        "color": "black",
        "linestyle": _line_style(contract["reference_line_style"]),
        "linewidth": MAIN_STROKE_PT,
    }


def errorbar_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["errorbar"]
    return {
        "marker": str(contract["marker"]),
        "markersize": float(contract["marker_size_pt"]),
        "markeredgecolor": str(contract["edge_color"]),
        "markeredgewidth": _stroke_width(contract["edge_width_token"]),
        "capsize": float(contract["cap_size_pt"]),
        "elinewidth": MAIN_STROKE_PT,
        "capthick": MAIN_STROKE_PT,
    }


def apply_boxplot_contract(parts: dict[str, object], *, combined: bool = False) -> None:
    contract = load_contracts().style["plots"]["boxplot"]
    for box in parts["boxes"]:  # type: ignore[index]
        box.set_alpha(None)
        alpha = 1.0 if combined else float(contract["alpha"])
        box.set_facecolor(_face_rgba(box.get_facecolor(), alpha))
        box.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
        box.set_linewidth(_stroke_width(contract["edge_width_token"]))
    for key in ("whiskers", "caps", "medians"):
        for artist in parts[key]:  # type: ignore[index]
            artist.set_color(str(contract["edge_color"]))
            artist.set_linewidth(MAIN_STROKE_PT)


def apply_violin_contract(parts: dict[str, object], *, combined: bool = False) -> None:
    contract = load_contracts().style["plots"]["violin"]
    alpha_token = "combined_alpha" if combined else "alpha"
    for body in parts["bodies"]:  # type: ignore[index]
        _collection_face_alpha(body, float(contract[alpha_token]))
        body.set_edgecolor(mcolors.to_rgba(str(contract["edge_color"]), 1.0))
        body.set_linewidth(_stroke_width(contract["edge_width_token"]))


def histogram_kwargs() -> dict[str, object]:
    contract = load_contracts().style["plots"]["histogram"]
    return {
        "color": _face_rgba(
            mpl.rcParams["axes.prop_cycle"].by_key()["color"][0],
            float(contract["alpha"]),
        ),
        "edgecolor": mcolors.to_rgba(str(contract["edge_color"]), 1.0),
        "linewidth": _stroke_width(contract["edge_width_token"]),
    }


def apply_contract_context(
    *, geometry: str = "single-column", typography: str = "sans"
) -> AbstractContextManager[None]:
    return mpl.rc_context(
        rc=build_rcparams(load_contracts(), geometry=geometry, typography=typography)
    )
