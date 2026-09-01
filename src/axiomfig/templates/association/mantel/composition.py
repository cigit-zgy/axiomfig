"""Normalized scientific grammar for composable Mantel figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

GlyphMethod = Literal["circle", "square", "ellipse", "number", "shade", "color", "pie"]
MatrixType = Literal["full", "upper", "lower", "mixed"]
CellRegion = Literal["full", "upper", "lower", "diagonal"]

GLYPH_METHODS = ("circle", "square", "ellipse", "number", "shade", "color", "pie")
MATRIX_TYPES = ("full", "upper", "lower", "mixed")
ORDERING_MODES = ("original", "alphabet", "AOE", "FPC", "hclust")
HCLUST_METHODS = (
    "complete",
    "ward",
    "ward.D",
    "ward.D2",
    "single",
    "average",
    "mcquitty",
    "median",
    "centroid",
)
SIGNIFICANCE_MODES = ("none", "mark", "p_value", "blank", "label_sig")
CI_MODES = ("none", "square", "circle", "rect")
NONSIGNIFICANT_MODES = ("hide", "fade", "show")
LINK_WIDTH_MODES = ("binned", "continuous")
P_VALUE_MODES = ("canonical", "detailed")

_CHOICES = {
    "matrix_method": GLYPH_METHODS,
    "matrix_type": MATRIX_TYPES,
    "order": ORDERING_MODES,
    "hclust_method": HCLUST_METHODS,
    "significance_mode": SIGNIFICANCE_MODES,
    "ci_mode": CI_MODES,
    "nonsignificant_links": NONSIGNIFICANT_MODES,
    "link_width_mode": LINK_WIDTH_MODES,
    "p_value_mode": P_VALUE_MODES,
    "lower_method": GLYPH_METHODS,
    "upper_method": GLYPH_METHODS,
    "coefficient_format": ("decimal", "percent"),
}


@dataclass(frozen=True)
class MatrixSpec:
    matrix_type: MatrixType = "lower"
    diagonal: Literal["show", "hide"] = "hide"
    order: str = "original"
    hclust_method: str = "complete"
    clusters: int | None = None


@dataclass(frozen=True)
class GlyphSpec:
    method: GlyphMethod
    region: CellRegion
    number_format: Literal["decimal", "percent"] = "decimal"


@dataclass(frozen=True)
class CoefficientOverlay:
    number_format: Literal["decimal", "percent"] = "decimal"


@dataclass(frozen=True)
class SignificanceOverlay:
    mode: Literal["mark", "p_value", "blank", "label_sig"]
    thresholds: tuple[float, ...] = (0.05, 0.01, 0.001)


@dataclass(frozen=True)
class ConfidenceIntervalOverlay:
    mode: Literal["square", "circle", "rect"]


@dataclass(frozen=True)
class ClusterOutlineOverlay:
    cluster_count: int


StatisticalOverlay = (
    CoefficientOverlay | SignificanceOverlay | ConfidenceIntervalOverlay | ClusterOutlineOverlay
)


@dataclass(frozen=True)
class CouplingSpec:
    enabled: bool = True
    nonsignificant: Literal["hide", "fade", "show"] = "fade"
    width_mode: Literal["binned", "continuous"] = "binned"
    p_value_mode: Literal["canonical", "detailed"] = "canonical"


@dataclass(frozen=True)
class MantelComposition:
    matrix: MatrixSpec
    glyphs: tuple[GlyphSpec, ...]
    overlays: tuple[StatisticalOverlay, ...]
    coupling: CouplingSpec


def _choice(values: Mapping[str, object], name: str, default: str) -> str:
    value = values.get(name, default)
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    aliases = {candidate.lower(): candidate for candidate in _CHOICES[name]}
    try:
        return aliases[value.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"{name} must be one of {_CHOICES[name]}") from exc


def _thresholds(value: object) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("significance_thresholds must be a sequence")
    try:
        thresholds = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ValueError("significance_thresholds must be numeric") from exc
    if not thresholds or any(not 0.0 < item < 1.0 for item in thresholds):
        raise ValueError("significance_thresholds must be between 0 and 1")
    if any(first <= second for first, second in zip(thresholds, thresholds[1:], strict=False)):
        raise ValueError("significance_thresholds must be strictly decreasing")
    return thresholds


def _boolean(values: Mapping[str, object], name: str, default: bool) -> bool:
    value = values.get(name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def normalize_composition(values: Mapping[str, object], *, size: int) -> MantelComposition:
    """Translate flat public scientific semantics into independent immutable layers."""
    region_alias = values.get("matrix_region")
    if region_alias is not None:
        if not isinstance(region_alias, str):
            raise ValueError("matrix_region must be a string")
        region_mapping = {"lower_left": "lower", "upper_right": "upper"}
        try:
            region_matrix_type = region_mapping[region_alias.strip().lower()]
        except KeyError as exc:
            raise ValueError("matrix_region must be lower_left or upper_right") from exc
        if (
            "matrix_type" in values
            and str(values["matrix_type"]).strip().lower() != region_matrix_type
        ):
            raise ValueError("matrix_region and matrix_type must describe the same matrix mask")
        matrix_type = region_matrix_type
    else:
        matrix_type = _choice(values, "matrix_type", "lower")
    diagonal_value = values.get("diagonal", "hide")
    if isinstance(diagonal_value, bool):
        diagonal_value = "show" if diagonal_value else "hide"
    if not isinstance(diagonal_value, str) or diagonal_value.strip().lower() not in {
        "show",
        "hide",
    }:
        raise ValueError("diagonal must be 'show' or 'hide'")
    order = _choice(values, "order", "original")
    hclust_method = _choice(values, "hclust_method", "complete")
    clusters = values.get("clusters")
    if clusters is not None:
        if isinstance(clusters, bool) or not isinstance(clusters, int) or not 2 <= clusters <= size:
            raise ValueError(f"clusters must be an integer between 2 and {size}")
        if order != "hclust":
            raise ValueError("cluster rectangles require order='hclust'")
    matrix = MatrixSpec(
        matrix_type=matrix_type,  # type: ignore[arg-type]
        diagonal=diagonal_value.strip().lower(),  # type: ignore[arg-type]
        order=order,
        hclust_method=hclust_method,
        clusters=clusters,
    )

    number_format = _choice(values, "coefficient_format", "decimal")
    glyphs: tuple[GlyphSpec, ...]
    if matrix_type == "mixed":
        glyphs = (
            GlyphSpec(
                method=_choice(values, "lower_method", "square"),  # type: ignore[arg-type]
                region="lower",
                number_format=number_format,  # type: ignore[arg-type]
            ),
            GlyphSpec(
                method=_choice(values, "upper_method", "number"),  # type: ignore[arg-type]
                region="upper",
                number_format=number_format,  # type: ignore[arg-type]
            ),
        )
        if matrix.diagonal == "show":
            glyphs += (
                GlyphSpec(
                    method=glyphs[0].method,
                    region="diagonal",
                    number_format=number_format,  # type: ignore[arg-type]
                ),
            )
    else:
        region: CellRegion = "full" if matrix_type == "full" else matrix_type  # type: ignore[assignment]
        glyphs = (
            GlyphSpec(
                method=_choice(values, "matrix_method", "circle"),  # type: ignore[arg-type]
                region=region,
                number_format=number_format,  # type: ignore[arg-type]
            ),
        )

    overlays: list[StatisticalOverlay] = []
    ci_mode = _choice(values, "ci_mode", "none")
    if ci_mode != "none":
        overlays.append(ConfidenceIntervalOverlay(mode=ci_mode))  # type: ignore[arg-type]
    if _boolean(values, "coefficients", False):
        overlays.append(CoefficientOverlay(number_format=number_format))  # type: ignore[arg-type]
    significance_mode = _choice(values, "significance_mode", "none")
    if significance_mode != "none":
        thresholds = _thresholds(values.get("significance_thresholds", (0.05, 0.01, 0.001)))
        overlays.append(
            SignificanceOverlay(mode=significance_mode, thresholds=thresholds)  # type: ignore[arg-type]
        )
    if clusters is not None:
        overlays.append(ClusterOutlineOverlay(cluster_count=clusters))

    nonsignificant_default = "fade"
    if "show_nonsignificant" in values and "nonsignificant_links" not in values:
        show = _boolean(values, "show_nonsignificant", False)
        nonsignificant_default = "show" if show else "hide"
    coupling = CouplingSpec(
        enabled=_boolean(values, "coupling", matrix_type in {"lower", "upper"}),
        nonsignificant=_choice(values, "nonsignificant_links", nonsignificant_default),  # type: ignore[arg-type]
        width_mode=_choice(values, "link_width_mode", "binned"),  # type: ignore[arg-type]
        p_value_mode=_choice(values, "p_value_mode", "canonical"),  # type: ignore[arg-type]
    )
    return MantelComposition(matrix, glyphs, tuple(overlays), coupling)


__all__ = [
    "CI_MODES",
    "GLYPH_METHODS",
    "HCLUST_METHODS",
    "LINK_WIDTH_MODES",
    "MATRIX_TYPES",
    "NONSIGNIFICANT_MODES",
    "ORDERING_MODES",
    "P_VALUE_MODES",
    "SIGNIFICANCE_MODES",
    "ClusterOutlineOverlay",
    "CoefficientOverlay",
    "ConfidenceIntervalOverlay",
    "CouplingSpec",
    "GlyphSpec",
    "MantelComposition",
    "MatrixSpec",
    "SignificanceOverlay",
    "normalize_composition",
]
