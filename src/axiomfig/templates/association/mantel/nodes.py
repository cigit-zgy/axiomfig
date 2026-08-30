"""Explicit Mantel source and target nodes on the shared diagonal composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection

from axiomfig.style import (
    apply_scatter_contract,
    mantel_plot_contract,
    palette_color,
    series_style,
)
from axiomfig.templates.association.mantel.geometry import MantelGeometry, source_label_size


@dataclass(frozen=True)
class NodeRenderResult:
    source_nodes: tuple[PathCollection, ...]
    target_nodes: tuple[PathCollection, ...]
    source_labels: tuple[object, ...]


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


def _source_label_placement(
    geometry: MantelGeometry,
    center: tuple[float, float],
    offset: float,
) -> tuple[tuple[float, float], str, str]:
    """Place labels diagonally outward from the route fan inside the measured source margin."""
    del center
    if geometry.coupling_region == "upper-right":
        return (offset, offset), "left", "bottom"
    if geometry.coupling_region == "lower-left":
        return (-offset, -offset), "right", "top"
    return (offset, 0.0), "left", "center"


def render_node_layer(
    axis: Axes,
    geometry: MantelGeometry,
    *,
    source_labels: Mapping[str, str] | None = None,
) -> NodeRenderResult:
    """Render explicit endpoints; target identity remains in matrix-edge labels only."""
    contract = mantel_plot_contract()["matrix"]
    assert isinstance(contract, Mapping)
    source_label_offset = float(contract["source_label_offset_pt"])
    nodes = mantel_plot_contract()["nodes"]
    assert isinstance(nodes, Mapping)
    source_size_ratio = float(nodes["source_size_ratio"])
    target_size_ratio = float(nodes["target_size_ratio"])

    source_nodes: list[PathCollection] = []
    rendered_labels: list[object] = []
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
        label_offset, horizontal_alignment, vertical_alignment = _source_label_placement(
            geometry,
            center,
            source_label_offset,
        )
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
        label._axiomfig_source = source
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
