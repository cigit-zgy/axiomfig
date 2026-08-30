"""External/precomputed input adapters for association templates."""

from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import labels_1d, numeric_1d, pairs, text
from axiomfig.templates.association.mantel.data import normalized_public_values


def _adapt_correlation_network(values: dict[str, object]) -> dict[str, object]:
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


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    if variant == "mantel":
        return normalized_public_values(supplied)
    return _adapt_correlation_network(dict(supplied))


__all__ = ["adapt"]
