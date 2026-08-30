"""Canonical Mantel structures and scientific-input normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

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

_CHOICES: dict[str, tuple[str, ...]] = {
    "matrix_method": GLYPH_METHODS,
    "matrix_type": MATRIX_TYPES,
    "order": ORDERING_MODES,
    "hclust_method": HCLUST_METHODS,
    "significance_mode": SIGNIFICANCE_MODES,
    "ci_mode": CI_MODES,
    "nonsignificant_links": NONSIGNIFICANT_MODES,
    "link_width_mode": LINK_WIDTH_MODES,
    "lower_method": GLYPH_METHODS,
    "upper_method": GLYPH_METHODS,
    "coefficient_format": ("decimal", "percent"),
}


@dataclass(frozen=True)
class MantelLink:
    source: str
    target: str
    mantel_r: float
    p_value: float
    label: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MantelData:
    correlation_matrix: np.ndarray
    labels: tuple[str, ...]
    links: tuple[MantelLink, ...]
    p_values: np.ndarray | None = None
    lower_ci: np.ndarray | None = None
    upper_ci: np.ndarray | None = None


@dataclass(frozen=True)
class MantelOptions:
    matrix_method: str = "square"
    matrix_type: str = "lower"
    diagonal: str = "hide"
    order: str = "original"
    hclust_method: str = "complete"
    clusters: int | None = None
    lower_method: str = "square"
    upper_method: str = "number"
    coefficients: bool = False
    coefficient_format: str = "decimal"
    significance_mode: str = "none"
    significance_thresholds: tuple[float, ...] = (0.05, 0.01, 0.001)
    ci_mode: str = "none"
    nonsignificant_links: str = "fade"
    link_width_mode: str = "binned"


def _choice(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    aliases = {candidate.lower(): candidate for candidate in _CHOICES[name]}
    try:
        return aliases[value.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"{name} must be one of {_CHOICES[name]}") from exc


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _matrix(
    value: object,
    name: str,
    *,
    size: int | None = None,
    symmetric: bool = True,
    unit_interval: bool = False,
) -> np.ndarray:
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{name} must be square")
    if size is not None and matrix.shape != (size, size):
        raise ValueError(f"{name} must match correlation_matrix shape")
    if np.isinf(matrix).any():
        raise ValueError(f"{name} must not contain infinite values")
    if symmetric and not np.allclose(matrix, matrix.T, atol=1e-8, rtol=0.0, equal_nan=True):
        raise ValueError(f"{name} must be symmetric")
    finite = matrix[np.isfinite(matrix)]
    lower, upper = (0.0, 1.0) if unit_interval else (-1.0, 1.0)
    if finite.size and (np.any(finite < lower) or np.any(finite > upper)):
        raise ValueError(f"{name} values must be between {lower:g} and {upper:g}")
    return matrix


def _labels(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("labels must be a one-dimensional sequence")
    array = np.asarray(value, dtype=object)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("labels must be a non-empty one-dimensional sequence")
    labels = tuple(_text(item, f"labels[{index}]") for index, item in enumerate(array.tolist()))
    if len(set(labels)) != len(labels):
        raise ValueError("labels must be unique")
    return labels


def _links(value: object, labels: tuple[str, ...]) -> tuple[MantelLink, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise ValueError("links must be a non-empty sequence of mappings")
    known = set(labels)
    seen: set[tuple[str, str]] = set()
    normalized: list[MantelLink] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"links[{index}] must be a mapping")
        keys = set(item)
        canonical = {"source", "target", "mantel_r", "p_value"}
        legacy = {"source_group", "target_label", "mantel_r", "p_value"}
        optional = {"label", "metadata"}
        if not (canonical <= keys or legacy <= keys) or keys - (canonical | legacy | optional):
            raise ValueError(f"links[{index}] must contain source, target, mantel_r, and p_value")
        if canonical <= keys and ({"source_group", "target_label"} & keys):
            raise ValueError(f"links[{index}] must not mix canonical and legacy endpoint fields")
        source_key, target_key = (
            ("source", "target") if canonical <= keys else ("source_group", "target_label")
        )
        source = _text(item[source_key], f"links[{index}].{source_key}")
        target = _text(item[target_key], f"links[{index}].{target_key}")
        if target not in known:
            raise ValueError(f"links[{index}] references unknown target: {target!r}")
        try:
            mantel_r = float(item["mantel_r"])
            p_value = float(item["p_value"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"links[{index}] mantel_r and p_value must be numeric") from exc
        if not np.isfinite(mantel_r) or not -1.0 <= mantel_r <= 1.0:
            raise ValueError(f"links[{index}].mantel_r must be between -1 and 1")
        if not np.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
            raise ValueError(f"links[{index}].p_value must be between 0 and 1")
        identity = (source, target)
        if identity in seen:
            raise ValueError(f"links contain duplicate source/target pair: {identity}")
        seen.add(identity)
        label = _text(item["label"], f"links[{index}].label") if "label" in item else None
        metadata = item.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError(f"links[{index}].metadata must be a mapping")
        normalized.append(MantelLink(source, target, mantel_r, p_value, label, dict(metadata)))
    return tuple(normalized)


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


def normalize_options(values: Mapping[str, object], *, size: int) -> MantelOptions:
    normalized: dict[str, Any] = {}
    for name in _CHOICES:
        if name in values:
            normalized[name] = _choice(values[name], name)
    diagonal = values.get("diagonal", "hide")
    if isinstance(diagonal, bool):
        diagonal = "show" if diagonal else "hide"
    if not isinstance(diagonal, str) or diagonal.strip().lower() not in {"show", "hide"}:
        raise ValueError("diagonal must be 'show' or 'hide'")
    normalized["diagonal"] = diagonal.strip().lower()
    if "coefficients" in values:
        if not isinstance(values["coefficients"], bool):
            raise ValueError("coefficients must be boolean")
        normalized["coefficients"] = values["coefficients"]
    if "significance_thresholds" in values:
        normalized["significance_thresholds"] = _thresholds(values["significance_thresholds"])
    if "clusters" in values:
        clusters = values["clusters"]
        if isinstance(clusters, bool) or not isinstance(clusters, int) or not 2 <= clusters <= size:
            raise ValueError(f"clusters must be an integer between 2 and {size}")
        normalized["clusters"] = clusters
    if "show_nonsignificant" in values and "nonsignificant_links" not in values:
        show = values["show_nonsignificant"]
        if not isinstance(show, bool):
            raise ValueError("show_nonsignificant must be boolean")
        normalized["nonsignificant_links"] = "show" if show else "hide"
    options = MantelOptions(**normalized)
    if options.clusters is not None and options.order != "hclust":
        raise ValueError("cluster rectangles require order='hclust'")
    return options


def normalize_inputs(values: Mapping[str, object]) -> tuple[MantelData, MantelOptions]:
    labels = _labels(values["labels"])
    matrix = _matrix(values["correlation_matrix"], "correlation_matrix", size=len(labels))
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-8, rtol=0.0):
        raise ValueError("correlation_matrix diagonal must equal 1")
    links = _links(values["links"], labels)
    p_values = (
        _matrix(values["p_values"], "p_values", size=len(labels), unit_interval=True)
        if "p_values" in values
        else None
    )
    lower_ci = (
        _matrix(values["lower_ci"], "lower_ci", size=len(labels)) if "lower_ci" in values else None
    )
    upper_ci = (
        _matrix(values["upper_ci"], "upper_ci", size=len(labels)) if "upper_ci" in values else None
    )
    if (lower_ci is None) != (upper_ci is None):
        raise ValueError("lower_ci and upper_ci must be supplied together")
    if lower_ci is not None and upper_ci is not None:
        finite = np.isfinite(lower_ci) & np.isfinite(upper_ci) & np.isfinite(matrix)
        if np.any(lower_ci[finite] > upper_ci[finite]):
            raise ValueError("CI lower bounds must not exceed upper bounds")
        if np.any(lower_ci[finite] > matrix[finite]) or np.any(matrix[finite] > upper_ci[finite]):
            raise ValueError("correlation estimates must lie within CI bounds")
    options = normalize_options(values, size=len(labels))
    if options.significance_mode != "none" and p_values is None:
        raise ValueError("significance_mode requires precomputed p_values")
    if options.ci_mode != "none" and lower_ci is None:
        raise ValueError("ci_mode requires precomputed lower_ci and upper_ci")
    return MantelData(matrix, labels, links, p_values, lower_ci, upper_ci), options


def normalized_public_values(values: Mapping[str, object]) -> dict[str, object]:
    """Return adapter-ready values while preserving top-level role ownership."""
    data, options = normalize_inputs(values)
    normalized = dict(values)
    normalized["correlation_matrix"] = data.correlation_matrix
    normalized["labels"] = np.asarray(data.labels, dtype=object)
    normalized["links"] = tuple(
        {
            "source": link.source,
            "target": link.target,
            "mantel_r": link.mantel_r,
            "p_value": link.p_value,
            **({"label": link.label} if link.label is not None else {}),
            **({"metadata": dict(link.metadata)} if link.metadata else {}),
        }
        for link in data.links
    )
    if data.p_values is not None:
        normalized["p_values"] = data.p_values
    if data.lower_ci is not None:
        normalized["lower_ci"] = data.lower_ci
        normalized["upper_ci"] = data.upper_ci
    option_values = {
        "matrix_method": options.matrix_method,
        "matrix_type": options.matrix_type,
        "diagonal": options.diagonal,
        "order": options.order,
        "hclust_method": options.hclust_method,
        "lower_method": options.lower_method,
        "upper_method": options.upper_method,
        "coefficient_format": options.coefficient_format,
        "significance_mode": options.significance_mode,
        "ci_mode": options.ci_mode,
        "nonsignificant_links": options.nonsignificant_links,
        "link_width_mode": options.link_width_mode,
    }
    for name in option_values:
        if name in normalized:
            normalized[name] = option_values[name]
    if "significance_thresholds" in normalized:
        normalized["significance_thresholds"] = options.significance_thresholds
    return normalized


__all__ = [
    "CI_MODES",
    "GLYPH_METHODS",
    "HCLUST_METHODS",
    "LINK_WIDTH_MODES",
    "MATRIX_TYPES",
    "MantelData",
    "MantelLink",
    "MantelOptions",
    "NONSIGNIFICANT_MODES",
    "ORDERING_MODES",
    "SIGNIFICANCE_MODES",
    "normalize_inputs",
    "normalized_public_values",
]
