from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from axiomfig.templates._adapter import (
    boolean,
    labels_1d,
    numeric_1d,
    numeric_matrix,
    pairs,
    text,
)


def _mantel_links(value: object, labels: np.ndarray) -> tuple[dict[str, object], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise ValueError("links must be a non-empty sequence of mappings")
    required = {"source_group", "target_label", "mantel_r", "p_value"}
    normalized: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    known_labels = set(labels.tolist())
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != required:
            raise ValueError(f"links[{index}] must contain exactly {sorted(required)}")
        source = text(item["source_group"], f"links[{index}].source_group")
        target = text(item["target_label"], f"links[{index}].target_label")
        if target not in known_labels:
            raise ValueError(f"links[{index}] references unknown target_label: {target!r}")
        try:
            mantel_r = float(item["mantel_r"])
            p_value = float(item["p_value"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"links[{index}] mantel_r and p_value must be numeric") from exc
        if not np.isfinite(mantel_r) or not 0.0 <= mantel_r <= 1.0:
            raise ValueError(f"links[{index}].mantel_r must be between 0 and 1")
        if not np.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
            raise ValueError(f"links[{index}].p_value must be between 0 and 1")
        identity = (source, target)
        if identity in seen:
            raise ValueError(f"links contain duplicate source_group/target_label pair: {identity}")
        seen.add(identity)
        normalized.append(
            {
                "source_group": source,
                "target_label": target,
                "mantel_r": mantel_r,
                "p_value": p_value,
            }
        )
    return tuple(normalized)


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant == "mantel":
        matrix = numeric_matrix(values["correlation_matrix"], "correlation_matrix")
        labels = labels_1d(values["labels"], "labels")
        if matrix.shape != (labels.size, labels.size):
            raise ValueError("correlation_matrix must be square and match labels")
        if len(set(labels.tolist())) != labels.size:
            raise ValueError("labels must be unique")
        if np.any(matrix < -1.0) or np.any(matrix > 1.0):
            raise ValueError("correlation_matrix values must be between -1 and 1")
        if not np.allclose(matrix, matrix.T, atol=1e-8, rtol=0.0):
            raise ValueError("correlation_matrix must be symmetric")
        if not np.allclose(np.diag(matrix), 1.0, atol=1e-8, rtol=0.0):
            raise ValueError("correlation_matrix diagonal must equal 1")
        links = _mantel_links(values["links"], labels)
        values.update(
            correlation_matrix=matrix,
            labels=labels,
            links=links,
        )
        if "show_nonsignificant" in values:
            values["show_nonsignificant"] = boolean(
                values["show_nonsignificant"], "show_nonsignificant"
            )
    else:
        nodes = labels_1d(values["nodes"], "nodes")
        edges = pairs(values["edges"], "edges")
        weights = numeric_1d(values["edge_weight"], "edge_weight")
        if edges.shape[0] != weights.size:
            raise ValueError("edges and edge_weight must be equal-length")
        unknown = set(edges.ravel()) - set(nodes)
        if unknown:
            raise ValueError(f"edges reference unknown nodes: {sorted(unknown)}")
        values.update(nodes=nodes, edges=edges, edge_weight=weights)
        if "groups" in values:
            groups = labels_1d(values["groups"], "groups")
            if groups.size != nodes.size:
                raise ValueError("groups must match nodes")
            values["groups"] = groups
        if "significance" in values:
            significance = np.asarray(values["significance"], dtype=bool)
            if significance.shape != (edges.shape[0],):
                raise ValueError("significance must match edges")
            values["significance"] = significance
    if variant != "mantel" and "strength_label" in values:
        values["strength_label"] = text(values["strength_label"], "strength_label")
    return values
