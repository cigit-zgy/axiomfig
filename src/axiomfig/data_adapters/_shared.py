from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def numeric_1d(value: object, name: str, *, minimum: int = 1) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1 or array.size < minimum or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite one-dimensional array")
    return array


def labels_1d(value: object, name: str, *, minimum: int = 1) -> np.ndarray:
    array = np.asarray(value, dtype=object)
    if array.ndim != 1 or array.size < minimum:
        raise ValueError(f"{name} must be a one-dimensional label array")
    rendered = np.asarray([str(item) for item in array], dtype=object)
    if any(not item for item in rendered):
        raise ValueError(f"{name} labels must be non-empty")
    return rendered


def numeric_matrix(value: object, name: str, *, minimum: int = 1) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or min(array.shape, default=0) < minimum or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite rectangular matrix")
    return array


def object_matrix(value: object, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=object)
    if array.ndim != 2 or min(array.shape, default=0) < 1:
        raise ValueError(f"{name} must be a rectangular matrix")
    return array


def coordinates(value: object, name: str, *, minimum: int = 2) -> np.ndarray:
    array = numeric_matrix(value, name)
    if array.shape[1] != 2 or array.shape[0] < minimum:
        raise ValueError(f"{name} must be an n by 2 coordinate matrix")
    return array


def equal_length(values: Mapping[str, np.ndarray], *, minimum: int = 1) -> None:
    sizes = {name: array.shape[0] for name, array in values.items()}
    if not sizes or min(sizes.values()) < minimum or len(set(sizes.values())) != 1:
        rendered = ", ".join(sorted(sizes))
        raise ValueError(f"{rendered} must be equal-length one-dimensional data")


def interval(value: object, name: str, count: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape not in {(count,), (count, 2)} or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain one half-width or lower/upper pair per estimate")
    return array


def scalar(value: object, name: str) -> float:
    try:
        selected = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite scalar") from exc
    if not np.isfinite(selected):
        raise ValueError(f"{name} must be a finite scalar")
    return selected


def text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def boolean(value: object, name: str) -> bool:
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be boolean")
    return bool(value)


def pairs(value: object, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=object)
    if array.ndim != 2 or array.shape[1] != 2 or array.shape[0] < 1:
        raise ValueError(f"{name} must be an n by 2 structured pair array")
    return np.asarray([[str(item) for item in row] for row in array], dtype=object)


def optional_text(values: dict[str, object], *names: str) -> None:
    for name in names:
        if name in values:
            values[name] = text(values[name], name)


def optional_boolean(values: dict[str, object], *names: str) -> None:
    for name in names:
        if name in values:
            values[name] = boolean(values[name], name)
