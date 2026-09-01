"""Small formal Gallery surface for the canonical Mantel grammar."""

from __future__ import annotations

from functools import partial

import numpy as np

from axiomfig.templates.association.mantel.builder import canonical_mantel_values
from axiomfig.templates.gallery_support import TemplateGalleryCase

MANTEL_GALLERY_CASE_IDS = (
    "canonical",
    "dense",
    "long_labels",
    "multigroup",
)

MANTEL_GALLERY_GEOMETRIES = {
    "canonical": "onehalf-column",
    "dense": "onehalf-column",
    "long_labels": "double-column",
    "multigroup": "onehalf-column",
}


def _correlation(size: int, *, phase: float) -> np.ndarray:
    coordinates = np.linspace(-1.2, 1.2, size)
    matrix = np.clip(
        0.82 * np.cos(np.subtract.outer(coordinates, coordinates) * 1.55 + phase)
        + 0.12 * np.sin(np.add.outer(coordinates, coordinates) * 1.8),
        -1.0,
        1.0,
    )
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    return matrix


def _links(
    labels: tuple[str, ...],
    targets_by_source: tuple[tuple[str, tuple[int, ...]], ...],
) -> tuple[dict[str, object], ...]:
    p_values = (0.004, 0.018, 0.12, 0.007, 0.032)
    return tuple(
        {
            "source": source,
            "target": labels[target],
            "mantel_r": 0.18 + 0.055 * ((source_index * 3 + rank) % 9),
            "p_value": p_values[(source_index + rank) % len(p_values)],
        }
        for source_index, (source, targets) in enumerate(targets_by_source)
        for rank, target in enumerate(targets)
    )


def _canonical_semantics(values: dict[str, object]) -> dict[str, object]:
    return {
        **values,
        "matrix_region": "lower_left",
        "matrix_method": "circle",
        "diagonal": "hide",
        "p_value_mode": "canonical",
        "nonsignificant_links": "fade",
    }


def _dense_values() -> dict[str, object]:
    labels = (
        "N",
        "P",
        "K",
        "Ca",
        "Mg",
        "S",
        "Al",
        "Fe",
        "Mn",
        "Zn",
        "Mo",
        "Bare soil",
        "Humus depth",
        "pH",
    )
    targets = (
        ("Spec01", (0, 1, 2, 3, 4, 5, 6)),
        ("Spec02", (2, 3, 4, 5, 6, 7, 8)),
        ("Spec03", (5, 6, 7, 8, 9, 10, 11)),
        ("Spec04", (7, 8, 9, 10, 11, 12, 13)),
    )
    return _canonical_semantics(
        {
            "correlation_matrix": _correlation(len(labels), phase=0.12),
            "labels": labels,
            "links": _links(labels, targets),
        }
    )


def _long_label_values() -> dict[str, object]:
    labels = (
        "Dissolved oxygen",
        "Ammonium nitrogen",
        "Nitrate nitrogen",
        "Total nitrogen",
        "Orthophosphate",
        "Total phosphorus",
        "Chemical oxygen demand",
        "Acidity",
        "Temperature",
        "Redox potential",
    )
    targets = (
        ("Water chemistry", (0, 1, 2, 3, 7)),
        ("Nutrient profile", (1, 2, 3, 4, 5)),
        ("Process state", (0, 6, 8, 9, 7)),
    )
    return _canonical_semantics(
        {
            "correlation_matrix": _correlation(len(labels), phase=-0.08),
            "labels": labels,
            "links": _links(labels, targets),
        }
    )


def _multigroup_values() -> dict[str, object]:
    labels = (
        "N",
        "P",
        "K",
        "Ca",
        "Mg",
        "S",
        "Fe",
        "Mn",
        "Zn",
        "Soil pH",
        "Moisture",
        "Organic carbon",
    )
    targets = (
        ("Bacteria", (0, 1, 2, 3, 4)),
        ("Fungi", (2, 3, 4, 5, 6)),
        ("Archaea", (5, 6, 7, 8, 9)),
        ("Protists", (7, 8, 9, 10, 11)),
    )
    return _canonical_semantics(
        {
            "correlation_matrix": _correlation(len(labels), phase=0.22),
            "labels": labels,
            "links": _links(labels, targets),
        }
    )


def mantel_gallery_values(case_id: str) -> dict[str, object]:
    """Return a fresh deterministic fixture for one formal Mantel Gallery case."""
    if case_id == "canonical":
        return _canonical_semantics(canonical_mantel_values())
    if case_id == "dense":
        return _dense_values()
    if case_id == "long_labels":
        return _long_label_values()
    if case_id == "multigroup":
        return _multigroup_values()
    raise ValueError(f"unknown formal Mantel Gallery case: {case_id}")


MANTEL_GALLERY_CASES = tuple(
    TemplateGalleryCase(
        example_id=case_id,
        geometry=MANTEL_GALLERY_GEOMETRIES[case_id],
        output_id=f"association/mantel_{case_id}",
        values=partial(mantel_gallery_values, case_id),
    )
    for case_id in MANTEL_GALLERY_CASE_IDS
)


__all__ = [
    "MANTEL_GALLERY_CASE_IDS",
    "MANTEL_GALLERY_CASES",
    "MANTEL_GALLERY_GEOMETRIES",
    "mantel_gallery_values",
]
