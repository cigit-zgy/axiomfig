"""Runtime validation for Figure, Panel, Axes, Artist, and Ornament anatomy."""

from __future__ import annotations

from matplotlib.artist import Artist
from matplotlib.transforms import Bbox

from axiomfig.config import load_contracts
from axiomfig.layout import FigureLayout, PanelFootprint, get_figure_layout


class FigureAnatomyError(RuntimeError):
    """Raised when deterministic figure geometry violates its ownership contract."""


def _inside(inner: Bbox, outer: Bbox, tolerance: float) -> bool:
    return (
        inner.x0 >= outer.x0 - tolerance
        and inner.y0 >= outer.y0 - tolerance
        and inner.x1 <= outer.x1 + tolerance
        and inner.y1 <= outer.y1 + tolerance
    )


def _artist_bbox(artist: Artist, renderer: object) -> Bbox | None:
    if not artist.get_visible() or not hasattr(artist, "get_window_extent"):
        return None
    try:
        bbox = artist.get_window_extent(renderer)  # type: ignore[call-arg]
    except (AttributeError, TypeError, ValueError):
        return None
    return bbox if bbox.width >= 0 and bbox.height >= 0 else None


def _panel_content_boxes(panel: PanelFootprint, renderer: object) -> list[Bbox]:
    axes = [panel.primary_axes, *panel.auxiliary_axes]
    boxes = [
        axis.get_tightbbox(renderer, bbox_extra_artists=[])
        for axis in axes
        if axis is not None and axis.get_visible()
    ]
    boxes.extend(
        bbox for artist in panel.artists if (bbox := _artist_bbox(artist, renderer)) is not None
    )
    return boxes


def _validate_footprints(
    layout: FigureLayout, boxes: list[Bbox], tolerance: float, issues: list[str]
) -> None:
    if max(box.width for box in boxes) - min(box.width for box in boxes) > tolerance:
        issues.append("panel footprints have unequal widths")
    if max(box.height for box in boxes) - min(box.height for box in boxes) > tolerance:
        issues.append("panel footprints have unequal heights")
    for row in range(layout.rows):
        selected = boxes[row * layout.columns : (row + 1) * layout.columns]
        if max(box.y0 for box in selected) - min(box.y0 for box in selected) > tolerance:
            issues.append(f"panel footprint row {row} has misaligned y0")
        if max(box.y1 for box in selected) - min(box.y1 for box in selected) > tolerance:
            issues.append(f"panel footprint row {row} has misaligned y1")
    for column in range(layout.columns):
        selected = boxes[column :: layout.columns]
        if max(box.x0 for box in selected) - min(box.x0 for box in selected) > tolerance:
            issues.append(f"panel footprint column {column} has misaligned x0")
        if max(box.x1 for box in selected) - min(box.x1 for box in selected) > tolerance:
            issues.append(f"panel footprint column {column} has misaligned x1")


def validate_figure_anatomy(figure: object, *, tolerance_pt: float = 0.25) -> None:
    layout = get_figure_layout(figure)  # type: ignore[arg-type]
    if layout is None:
        return
    from axiomfig.layout import solve_panel_layout
    from axiomfig.ornaments import finalize_ornaments

    solve_panel_layout(layout.figure)
    finalize_ornaments(layout.figure)
    layout.figure.canvas.draw()
    renderer = layout.figure.canvas.get_renderer()
    tolerance = tolerance_pt * layout.figure.dpi / 72.0
    output = layout.figure.bbox
    footprints = [panel.bbox().transformed(layout.figure.transFigure) for panel in layout.panels]
    issues: list[str] = []
    _validate_footprints(layout, footprints, tolerance, issues)

    for panel, footprint in zip(layout.panels, footprints, strict=True):
        for auxiliary in panel.auxiliary_axes:
            auxiliary_bbox = auxiliary.get_tightbbox(renderer, bbox_extra_artists=[])
            if not _inside(auxiliary_bbox, footprint, tolerance):
                issues.append(f"panel {panel.index} auxiliary axes outside panel footprint")
        for content in _panel_content_boxes(panel, renderer):
            if not _inside(content, footprint, tolerance):
                issues.append(f"panel {panel.index} content outside panel footprint")
                break
        for annotation in panel.primary_axes.texts if panel.primary_axes is not None else []:
            bbox = _artist_bbox(annotation, renderer)
            if bbox is not None and not _inside(bbox, footprint, tolerance):
                issues.append(f"panel {panel.index} annotation outside panel footprint")

    panel_contract = load_contracts().style["panel"]
    expected_dx = float(panel_contract["left_offset_pt"]) * layout.figure.dpi / 72.0
    expected_dy = float(panel_contract["top_offset_pt"]) * layout.figure.dpi / 72.0
    label_boxes: list[Bbox] = []
    for panel, footprint in zip(layout.panels, footprints, strict=True):
        if layout.panel_labels and panel.panel_label is None:
            issues.append(f"panel {panel.index} label is missing")
            continue
        if panel.panel_label is None:
            continue
        label_bbox = _artist_bbox(panel.panel_label, renderer)
        if label_bbox is None:
            issues.append(f"panel {panel.index} label has no measurable bbox")
            continue
        label_boxes.append(label_bbox)
        if abs(label_bbox.x0 - (footprint.x0 + expected_dx)) > tolerance:
            issues.append(f"panel {panel.index} label x anchor is incorrect")
        if abs(label_bbox.y0 - (footprint.y1 + expected_dy)) > tolerance:
            issues.append(f"panel {panel.index} label y anchor is incorrect")
        if not _inside(label_bbox, output, tolerance):
            issues.append(f"panel {panel.index} label outside output boundary")

    for index, first in enumerate(label_boxes):
        if any(first.overlaps(second) for second in label_boxes[index + 1 :]):
            issues.append("panel-label collision")
    for legend in layout.legends:
        bbox = legend.get_window_extent(renderer)
        if not _inside(bbox, output, tolerance):
            issues.append("figure-level legend outside output boundary")
        if any(bbox.overlaps(axis.bbox) for axis in layout.figure.axes):
            issues.append("figure-level legend collides with axes")
        if any(bbox.overlaps(label) for label in label_boxes):
            issues.append("figure-level legend collides with panel label")
    for ornament in layout.figure_ornaments:
        bbox = _artist_bbox(ornament, renderer)
        if bbox is not None and not _inside(bbox, output, tolerance):
            issues.append("figure-level ornament outside output boundary")

    if issues:
        unique = list(dict.fromkeys(issues))
        raise FigureAnatomyError("; ".join(unique))
