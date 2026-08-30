"""Explicit Mantel source and target nodes on the shared diagonal composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.patches import Circle

from axiomfig.style import FILL_EDGE_PT, mantel_plot_contract, mantel_visual_color
from axiomfig.templates.association.mantel.geometry import MantelGeometry, source_label_size


@dataclass(frozen=True)
class NodeRenderResult:
    source_nodes: tuple[Circle, ...]
    target_nodes: tuple[Circle, ...]
    source_labels: tuple[object, ...]


def _node(
    axis: Axes,
    center: tuple[float, float],
    *,
    radius: float,
    kind: str,
    identity: str,
) -> Circle:
    artist = Circle(
        center,
        radius,
        facecolor=mantel_visual_color(f"{kind}_node_fill"),
        edgecolor=mantel_visual_color(f"{kind}_node_edge"),
        linewidth=FILL_EDGE_PT if kind == "source" else FILL_EDGE_PT * 0.72,
        zorder=7,
    )
    artist.set_gid(f"axiomfig-mantel-{kind}-node")
    setattr(artist, f"_axiomfig_{kind}", identity)
    axis.add_patch(artist)
    return artist


def render_node_layer(
    axis: Axes,
    geometry: MantelGeometry,
    *,
    source_labels: Mapping[str, str] | None = None,
) -> NodeRenderResult:
    """Render explicit endpoints; target identity remains in matrix-edge labels only."""
    contract = mantel_plot_contract()["matrix"]
    assert isinstance(contract, Mapping)
    source_radius = float(contract["source_node_radius"])
    target_radius = float(contract["target_node_radius"])
    source_label_offset = float(contract["source_label_offset_pt"])

    source_nodes: list[Circle] = []
    rendered_labels: list[object] = []
    for source, center in geometry.source_positions.items():
        source_nodes.append(
            _node(axis, center, radius=source_radius, kind="source", identity=source)
        )
        normal_offset = (
            source_label_offset
            if geometry.coupling_region == "upper-right"
            else -source_label_offset
        )
        label = axis.annotate(
            source_labels.get(source, source) if source_labels is not None else source,
            center,
            xytext=(normal_offset, normal_offset),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=source_label_size(),
            clip_on=True,
            zorder=7,
        )
        label.set_gid("axiomfig-mantel-source-label")
        label._axiomfig_source = source
        rendered_labels.append(label)

    target_nodes = tuple(
        _node(axis, center, radius=target_radius, kind="target", identity=target)
        for target, center in geometry.target_positions.items()
    )
    return NodeRenderResult(tuple(source_nodes), target_nodes, tuple(rendered_labels))


__all__ = ["NodeRenderResult", "render_node_layer"]
