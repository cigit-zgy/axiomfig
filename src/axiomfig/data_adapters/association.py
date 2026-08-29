from __future__ import annotations

import numpy as np

from ._shared import equal_length, labels_1d, numeric_1d, numeric_matrix, pairs, text


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant == "mantel":
        matrix = numeric_matrix(values["correlation_matrix"], "correlation_matrix")
        labels = labels_1d(values["matrix_labels"], "matrix_labels")
        if matrix.shape != (labels.size, labels.size):
            raise ValueError("correlation_matrix must be square and match matrix_labels")
        links = pairs(values["links"], "links")
        strength = numeric_1d(values["link_strength"], "link_strength")
        significance = np.asarray(values["significance"], dtype=bool)
        if significance.ndim != 1:
            raise ValueError("significance must be one-dimensional")
        equal_length({"links": links, "link_strength": strength, "significance": significance})
        if np.any(strength < 0):
            raise ValueError("link_strength must be non-negative")
        values.update(
            correlation_matrix=matrix,
            matrix_labels=labels,
            links=links,
            link_strength=strength,
            significance=significance,
        )
        if "node_labels" in values:
            values["node_labels"] = labels_1d(values["node_labels"], "node_labels")
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
    if "strength_label" in values:
        values["strength_label"] = text(values["strength_label"], "strength_label")
    return values
