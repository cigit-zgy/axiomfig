"""In-memory Figure, rendered artifact, and Gallery validation."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from matplotlib.artist import Artist
from matplotlib.transforms import Bbox
from pypdf import PdfReader

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
    """Validate in-memory Figure, Panel, Axes, Artist, and Ornament ownership."""
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
        assert panel.primary_axes is not None
        primary_bbox = panel.primary_axes.bbox
        if abs(label_bbox.x0 - (primary_bbox.x0 + expected_dx)) > tolerance:
            issues.append(f"panel {panel.index} label x anchor is incorrect")
        if abs(label_bbox.y0 - (primary_bbox.y1 + expected_dy)) > tolerance:
            issues.append(f"panel {panel.index} label y anchor is incorrect")
        if not _inside(label_bbox, footprint, tolerance):
            issues.append(f"panel {panel.index} label outside panel footprint")
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


class ValidationError(RuntimeError):
    """Raised when a rendered figure violates an observable contract."""


@dataclass(frozen=True)
class PdfInfo:
    path: Path
    page_count: int
    width_mm: float
    height_mm: float
    size_bytes: int


@dataclass(frozen=True)
class GalleryEntry:
    pdf: PdfInfo
    png: Path
    fonts: tuple[str, ...]


def inspect_pdf(path: Path) -> PdfInfo:
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValidationError(f"missing or empty PDF: {path}")
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise ValidationError(f"PDF cannot be parsed: {path}: {exc}") from exc
    if not reader.pages:
        raise ValidationError(f"PDF has no pages: {path}")
    media_box = reader.pages[0].mediabox
    width_pt = float(media_box.width)
    height_pt = float(media_box.height)
    return PdfInfo(
        path=path,
        page_count=len(reader.pages),
        width_mm=width_pt * 25.4 / 72.0,
        height_mm=height_pt * 25.4 / 72.0,
        size_bytes=path.stat().st_size,
    )


def extract_pdf_text(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        raise ValidationError("pdftotext is required for content validation")
    completed = subprocess.run(
        [pdftotext, str(path), "-"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise ValidationError(f"pdftotext failed for {path}:\n{completed.stderr}")
    return completed.stdout


def out_of_page_words(path: Path, *, tolerance_pt: float = 0.5) -> tuple[str, ...]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        raise ValidationError("pdftotext is required for text-boundary validation")
    with tempfile.TemporaryDirectory(prefix="axiomfig-bbox-") as directory:
        bbox = Path(directory) / "bbox.html"
        completed = subprocess.run(
            [pdftotext, "-bbox", str(path), str(bbox)],
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0 or not bbox.is_file():
            raise ValidationError(f"pdftotext -bbox failed for {path}:\n{completed.stderr}")
        root = ET.parse(bbox).getroot()

    outside: list[str] = []
    for page in root.iter("{*}page"):
        width = float(page.attrib["width"])
        height = float(page.attrib["height"])
        for word in page.iter("{*}word"):
            x_min = float(word.attrib["xMin"])
            y_min = float(word.attrib["yMin"])
            x_max = float(word.attrib["xMax"])
            y_max = float(word.attrib["yMax"])
            if (
                x_min < -tolerance_pt
                or y_min < -tolerance_pt
                or x_max > width + tolerance_pt
                or y_max > height + tolerance_pt
            ):
                outside.append("".join(word.itertext()))
    return tuple(outside)


def _font_rows(path: Path) -> tuple[str, ...]:
    pdffonts = shutil.which("pdffonts")
    if pdffonts is None:
        raise ValidationError("pdffonts is required for deterministic font validation")
    completed = subprocess.run(
        [pdffonts, str(path)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise ValidationError(f"pdffonts failed for {path}:\n{completed.stdout}")
    lines = completed.stdout.splitlines()
    divider = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("--------------------------------")
        ),
        None,
    )
    if divider is None:
        raise ValidationError(f"cannot parse pdffonts output for {path}:\n{completed.stdout}")
    rows = tuple(line for line in lines[divider + 1 :] if line.strip())
    for row in rows:
        columns = row.split()
        if len(columns) < 5 or columns[-5:-3] != ["yes", "yes"]:
            raise ValidationError(f"font is not embedded and subset in {path}: {row}")
        if "Type 3" in row:
            raise ValidationError(f"Type 3 font is forbidden in {path}: {row}")
    return rows


def _check_log(log: Path) -> None:
    if not log.is_file():
        raise ValidationError(f"missing Tectonic log: {log}")
    text = log.read_text(encoding="utf-8", errors="replace")
    bad = re.compile(r"missing character|missing glyph|font .* not found", re.IGNORECASE)
    match = bad.search(text)
    if match:
        raise ValidationError(f"font/glyph diagnostic in {log}: {match.group(0)}")


def validate_pair(
    pdf: Path,
    png: Path,
    *,
    expected_width_mm: float | None = None,
    expected_height_mm: float | None = None,
    tolerance_mm: float = 0.25,
    tectonic_log: Path | None = None,
) -> GalleryEntry:
    info = inspect_pdf(pdf)
    if info.page_count != 1:
        raise ValidationError(f"expected one PDF page, got {info.page_count}: {pdf}")
    if expected_width_mm is not None and abs(info.width_mm - expected_width_mm) > tolerance_mm:
        raise ValidationError(
            f"PDF width {info.width_mm:.3f} mm != {expected_width_mm:.3f} mm: {pdf}"
        )
    if expected_height_mm is not None and abs(info.height_mm - expected_height_mm) > tolerance_mm:
        raise ValidationError(
            f"PDF height {info.height_mm:.3f} mm != {expected_height_mm:.3f} mm: {pdf}"
        )
    png = Path(png)
    if not png.is_file() or png.stat().st_size == 0:
        raise ValidationError(f"missing PNG preview: {png}")
    if tectonic_log is not None:
        _check_log(tectonic_log)
    fonts = _font_rows(Path(pdf))
    outside = out_of_page_words(Path(pdf))
    if outside:
        raise ValidationError(f"text extends outside the PDF page in {pdf}: {outside}")
    return GalleryEntry(pdf=info, png=png, fonts=fonts)


def validate_gallery(
    gallery: Path,
    *,
    expected_stems: Iterable[str] | None = None,
) -> list[GalleryEntry]:
    gallery = Path(gallery)
    pdfs = sorted(gallery.rglob("*.pdf"))
    selected_pdfs = pdfs
    if expected_stems is not None:
        expected = {f"{stem}.pdf" for stem in expected_stems}
        official_pdfs = [
            path for path in pdfs if not path.relative_to(gallery).as_posix().startswith("parity/")
        ]
        actual = {path.relative_to(gallery).as_posix() for path in official_pdfs}
        if actual != expected:
            raise ValidationError(
                f"gallery PDF set mismatch; missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
        selected_pdfs = official_pdfs
    entries = []
    for pdf in selected_pdfs:
        png = pdf.with_suffix(".png")
        if not png.exists():
            raise ValidationError(f"missing PNG preview for {pdf.name}: {png}")
        entries.append(validate_pair(pdf, png))
    return entries
