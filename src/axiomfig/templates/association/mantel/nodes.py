"""Explicit Mantel source and target nodes on the shared diagonal composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.text import Annotation

from axiomfig.style import (
    apply_scatter_contract,
    palette_color,
    series_style,
)
from axiomfig.templates.association.mantel.geometry import MantelGeometry, source_label_size
from axiomfig.templates.association.mantel.styling import mantel_plot_contract


@dataclass(frozen=True)
class NodeRenderResult:
    source_nodes: tuple[PathCollection, ...]
    target_nodes: tuple[PathCollection, ...]
    source_labels: tuple[Annotation, ...]


def _node(
    axis: Axes,
    center: tuple[float, float],
    *,
    color: object,
    size_ratio: float,
    kind: str,
    identity: str,
) -> PathCollection:
    artist = axis.scatter(
        [center[0]],
        [center[1]],
        color=color,
        marker="o",
        zorder=7,
    )
    apply_scatter_contract(artist, size_ratio=size_ratio)
    artist.set_gid(f"axiomfig-mantel-{kind}-node")
    setattr(artist, f"_axiomfig_{kind}", identity)
    return artist


def render_node_layer(
    axis: Axes,
    geometry: MantelGeometry,
    *,
    source_labels: Mapping[str, str] | None = None,
) -> NodeRenderResult:
    """Render explicit endpoints; target identity remains in matrix-edge labels only."""
    nodes = mantel_plot_contract()["nodes"]
    assert isinstance(nodes, Mapping)
    source_size_ratio = float(nodes["source_size_ratio"])
    target_size_ratio = float(nodes["target_size_ratio"])

    source_nodes: list[PathCollection] = []
    rendered_labels: list[Annotation] = []
    for source_index, (source, center) in enumerate(geometry.source_positions.items()):
        source_nodes.append(
            _node(
                axis,
                center,
                color=series_style(source_index, include_marker=False)["color"],
                size_ratio=source_size_ratio,
                kind="source",
                identity=source,
            )
        )
        label_offset = geometry.source_rail.label_offsets_pt[source]
        horizontal_alignment, vertical_alignment = geometry.source_rail.label_alignments[source]
        label = axis.annotate(
            source_labels.get(source, source) if source_labels is not None else source,
            center,
            xytext=label_offset,
            textcoords="offset points",
            ha=horizontal_alignment,
            va=vertical_alignment,
            fontsize=source_label_size(),
            clip_on=False,
            zorder=7,
        )
        label.set_gid("axiomfig-mantel-source-label")
        label.__dict__["_axiomfig_source"] = source
        rendered_labels.append(label)

    target_nodes = tuple(
        _node(
            axis,
            center,
            color=palette_color("AxiomWhite", palette_name="axiom_neutral"),
            size_ratio=target_size_ratio,
            kind="target",
            identity=target,
        )
        for target, center in geometry.target_positions.items()
    )
    return NodeRenderResult(tuple(source_nodes), target_nodes, tuple(rendered_labels))


__all__ = ["NodeRenderResult", "render_node_layer"]
