"""Deterministic correlation-matrix ordering, including pure-Python hclust."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from axiomfig.templates.association.mantel.data import HCLUST_METHODS, ORDERING_MODES


@dataclass(frozen=True)
class OrderingResult:
    indices: np.ndarray
    matrix: np.ndarray
    labels: tuple[str, ...]
    clusters: tuple[tuple[int, ...], ...] = ()


@dataclass(frozen=True)
class _Cluster:
    members: tuple[int, ...]
    leaf_order: tuple[int, ...]

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def tie_key(self) -> tuple[int, ...]:
        return tuple(sorted(self.members))


def _eigenvectors(matrix: np.ndarray) -> np.ndarray:
    safe = np.nan_to_num(matrix, nan=0.0)
    safe = (safe + safe.T) / 2.0
    np.fill_diagonal(safe, 1.0)
    eigenvalues, eigenvectors = np.linalg.eigh(safe)
    vectors = eigenvectors[:, np.argsort(eigenvalues)[::-1]]
    for column in range(vectors.shape[1]):
        vector = vectors[:, column]
        pivot = int(np.argmax(np.abs(vector)))
        if vector[pivot] < 0.0:
            vectors[:, column] *= -1.0
    return vectors


def _aoe_order(matrix: np.ndarray) -> np.ndarray:
    vectors = _eigenvectors(matrix)
    if matrix.shape[0] < 2:
        return np.arange(matrix.shape[0], dtype=int)
    angles = np.mod(np.arctan2(vectors[:, 1], vectors[:, 0]), 2.0 * np.pi)
    return np.argsort(angles, kind="stable")


def _fpc_order(matrix: np.ndarray) -> np.ndarray:
    return np.argsort(_eigenvectors(matrix)[:, 0], kind="stable")


def _distance_key(left: int, right: int) -> tuple[int, int]:
    return (left, right) if left < right else (right, left)


def _updated_distance(
    method: str,
    left: _Cluster,
    right: _Cluster,
    other: _Cluster,
    d_left: float,
    d_right: float,
    d_pair: float,
) -> float:
    if method == "single":
        return min(d_left, d_right)
    if method == "complete":
        return max(d_left, d_right)
    if method == "average":
        return (left.size * d_left + right.size * d_right) / (left.size + right.size)
    if method == "mcquitty":
        return 0.5 * d_left + 0.5 * d_right
    if method == "median":
        return 0.5 * d_left + 0.5 * d_right - 0.25 * d_pair
    if method == "centroid":
        total = left.size + right.size
        return (
            left.size / total * d_left
            + right.size / total * d_right
            - left.size * right.size / total**2 * d_pair
        )
    total = left.size + right.size + other.size
    return (
        (left.size + other.size) * d_left
        + (right.size + other.size) * d_right
        - other.size * d_pair
    ) / total


def _hclust_order(
    matrix: np.ndarray,
    *,
    method: str,
    cluster_count: int | None,
) -> tuple[np.ndarray, tuple[tuple[int, ...], ...]]:
    canonical_method = "ward.D" if method == "ward" else method
    squared = canonical_method == "ward.D2"
    update_method = "ward.D" if squared else canonical_method
    count = matrix.shape[0]
    safe = np.nan_to_num(matrix, nan=0.0)
    dissimilarity = np.clip(1.0 - safe, 0.0, 2.0)
    if squared:
        dissimilarity = dissimilarity**2
    active: dict[int, _Cluster] = {index: _Cluster((index,), (index,)) for index in range(count)}
    distances = {
        (left, right): float(dissimilarity[left, right])
        for left in range(count)
        for right in range(left + 1, count)
    }
    next_id = count
    cut_snapshot: tuple[tuple[int, ...], ...] | None = None
    requested = cluster_count or 1
    if requested == count:
        cut_snapshot = tuple(cluster.members for cluster in active.values())

    while len(active) > 1:
        pair = min(
            distances,
            key=lambda ids: (
                distances[ids],
                active[ids[0]].tie_key,
                active[ids[1]].tie_key,
            ),
        )
        left_id, right_id = pair
        left, right = active[left_id], active[right_id]
        if left.tie_key > right.tie_key:
            left_id, right_id, left, right = right_id, left_id, right, left
            pair = _distance_key(left_id, right_id)
        pair_distance = distances[pair]
        merged = _Cluster(left.members + right.members, left.leaf_order + right.leaf_order)
        other_ids = [identifier for identifier in active if identifier not in {left_id, right_id}]
        updates: dict[tuple[int, int], float] = {}
        for other_id in other_ids:
            other = active[other_id]
            distance = _updated_distance(
                update_method,
                left,
                right,
                other,
                distances[_distance_key(left_id, other_id)],
                distances[_distance_key(right_id, other_id)],
                pair_distance,
            )
            updates[_distance_key(next_id, other_id)] = max(0.0, float(distance))
        distances = {
            ids: value
            for ids, value in distances.items()
            if left_id not in ids and right_id not in ids
        }
        distances.update(updates)
        del active[left_id]
        del active[right_id]
        active[next_id] = merged
        next_id += 1
        if len(active) == requested:
            cut_snapshot = tuple(cluster.members for cluster in active.values())

    order = np.asarray(next(iter(active.values())).leaf_order, dtype=int)
    if cluster_count is None:
        return order, ()
    assert cut_snapshot is not None
    positions = {index: position for position, index in enumerate(order.tolist())}
    clusters = tuple(
        tuple(sorted(cluster, key=positions.__getitem__))
        for cluster in sorted(
            cut_snapshot,
            key=lambda item: min(positions[index] for index in item),
        )
    )
    return order, clusters


def order_variables(
    matrix: np.ndarray,
    labels: tuple[str, ...],
    *,
    mode: str,
    hclust_method: str = "complete",
    clusters: int | None = None,
) -> OrderingResult:
    """Return one synchronized deterministic permutation for every matrix-owned layer."""
    if mode not in ORDERING_MODES:
        raise ValueError(f"order must be one of {ORDERING_MODES}")
    if hclust_method not in HCLUST_METHODS:
        raise ValueError(f"hclust_method must be one of {HCLUST_METHODS}")
    if matrix.shape != (len(labels), len(labels)):
        raise ValueError("matrix and labels must have matching square dimensions")
    if mode == "original":
        indices = np.arange(len(labels), dtype=int)
        cluster_values: tuple[tuple[int, ...], ...] = ()
    elif mode == "alphabet":
        indices = np.asarray(sorted(range(len(labels)), key=lambda index: labels[index]), dtype=int)
        cluster_values = ()
    elif mode == "AOE":
        indices = _aoe_order(matrix)
        cluster_values = ()
    elif mode == "FPC":
        indices = _fpc_order(matrix)
        cluster_values = ()
    else:
        indices, cluster_values = _hclust_order(
            matrix,
            method=hclust_method,
            cluster_count=clusters,
        )
    return OrderingResult(
        indices=indices,
        matrix=matrix[np.ix_(indices, indices)],
        labels=tuple(labels[index] for index in indices),
        clusters=cluster_values,
    )


__all__ = ["OrderingResult", "order_variables"]
