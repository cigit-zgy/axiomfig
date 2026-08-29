from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


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
    if expected_stems is not None:
        expected = {f"{stem}.pdf" for stem in expected_stems}
        actual = {path.relative_to(gallery).as_posix() for path in pdfs}
        if actual != expected:
            raise ValidationError(
                f"gallery PDF set mismatch; missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
    entries = []
    for pdf in pdfs:
        png = pdf.with_suffix(".png")
        if not png.exists():
            raise ValidationError(f"missing PNG preview for {pdf.name}: {png}")
        entries.append(validate_pair(pdf, png))
    return entries
