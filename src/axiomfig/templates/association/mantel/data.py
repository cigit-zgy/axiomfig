"""Canonical Mantel structures and scientific-input normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from axiomfig.templates.association.mantel.composition import (
    CI_MODES,
    GLYPH_METHODS,
    HCLUST_METHODS,
    LINK_WIDTH_MODES,
    MATRIX_TYPES,
    NONSIGNIFICANT_MODES,
    ORDERING_MODES,
    SIGNIFICANCE_MODES,
    CoefficientOverlay,
    ConfidenceIntervalOverlay,
    MantelComposition,
    SignificanceOverlay,
    normalize_composition,
)


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


def normalize_inputs(values: Mapping[str, object]) -> tuple[MantelData, MantelComposition]:
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
    composition = normalize_composition(values, size=len(labels))
    significance = next(
        (overlay for overlay in composition.overlays if isinstance(overlay, SignificanceOverlay)),
        None,
    )
    confidence_interval = next(
        (
            overlay
            for overlay in composition.overlays
            if isinstance(overlay, ConfidenceIntervalOverlay)
        ),
        None,
    )
    if significance is not None and p_values is None:
        raise ValueError("significance_mode requires precomputed p_values")
    if confidence_interval is not None and lower_ci is None:
        raise ValueError("ci_mode requires precomputed lower_ci and upper_ci")
    return MantelData(matrix, labels, links, p_values, lower_ci, upper_ci), composition


def normalized_public_values(values: Mapping[str, object]) -> dict[str, object]:
    """Return adapter-ready values while preserving top-level role ownership."""
    data, composition = normalize_inputs(values)
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
    normalized_values = {
        "matrix_type": composition.matrix.matrix_type,
        "diagonal": composition.matrix.diagonal,
        "order": composition.matrix.order,
        "hclust_method": composition.matrix.hclust_method,
        "nonsignificant_links": composition.coupling.nonsignificant,
        "link_width_mode": composition.coupling.width_mode,
        "coupling": composition.coupling.enabled,
    }
    normalized_values.update(
        {
            "matrix_method": composition.glyphs[0].method,
            "coefficient_format": composition.glyphs[0].number_format,
        }
    )
    if composition.matrix.matrix_type == "mixed":
        normalized_values.update(
            lower_method=composition.glyphs[0].method,
            upper_method=composition.glyphs[1].method,
        )
    coefficient = next(
        (overlay for overlay in composition.overlays if isinstance(overlay, CoefficientOverlay)),
        None,
    )
    significance = next(
        (overlay for overlay in composition.overlays if isinstance(overlay, SignificanceOverlay)),
        None,
    )
    confidence_interval = next(
        (
            overlay
            for overlay in composition.overlays
            if isinstance(overlay, ConfidenceIntervalOverlay)
        ),
        None,
    )
    normalized_values.update(
        clusters=composition.matrix.clusters,
        coefficients=coefficient is not None,
        significance_mode=(significance.mode if significance is not None else "none"),
        significance_thresholds=(
            significance.thresholds if significance is not None else (0.05, 0.01, 0.001)
        ),
        ci_mode=(confidence_interval.mode if confidence_interval is not None else "none"),
    )
    for name, value in normalized_values.items():
        if name in normalized:
            normalized[name] = value
    return normalized


__all__ = [
    "CI_MODES",
    "GLYPH_METHODS",
    "HCLUST_METHODS",
    "LINK_WIDTH_MODES",
    "MATRIX_TYPES",
    "MantelData",
    "MantelLink",
    "NONSIGNIFICANT_MODES",
    "ORDERING_MODES",
    "SIGNIFICANCE_MODES",
    "normalize_inputs",
    "normalized_public_values",
]
