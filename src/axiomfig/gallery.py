from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.rendering import RenderResult, render_figure
from axiomfig.templates import build_template
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

GALLERY_MODES = ("sans", "serif")


@dataclass(frozen=True)
class GallerySpec:
    stem: str
    template: str
    geometry: str


GALLERY_SPECS = (
    GallerySpec("01_line", "line", "single-column"),
    GallerySpec("02_scatter", "scatter", "single-column"),
    GallerySpec("03_bar", "bar", "single-column"),
    GallerySpec("04_violin", "violin", "single-column"),
    GallerySpec("05_heatmap", "heatmap", "single-column"),
    GallerySpec("06_multi_panel", "multi-panel", "double-column"),
)


@contextmanager
def _deterministic_pdf_environment() -> Iterator[None]:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = "0"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _prepare_gallery(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for path in root.iterdir():
        if path.is_file() and path.suffix.lower() in {".pdf", ".png"}:
            path.unlink()
        elif path.is_dir() and path.name in GALLERY_MODES:
            for artifact in path.iterdir():
                if not artifact.is_file() or artifact.suffix.lower() not in {".pdf", ".png"}:
                    raise RuntimeError(f"unexpected Gallery content: {artifact}")
                artifact.unlink()
        else:
            raise RuntimeError(f"unexpected Gallery content: {path}")
    for mode in GALLERY_MODES:
        (root / mode).mkdir(exist_ok=True)


def build_gallery(gallery: Path, *, work_root: Path | None = None) -> list[RenderResult]:
    gallery = Path(gallery).expanduser().resolve()
    work_root = (
        Path(work_root).expanduser().resolve()
        if work_root is not None
        else (Path.cwd() / "tmp" / "gallery").resolve()
    )
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    _prepare_gallery(gallery)
    contracts = load_contracts()
    results: list[RenderResult] = []
    manifest: dict[str, object] = {"figures": []}

    with _deterministic_pdf_environment():
        for mode in GALLERY_MODES:
            fonts = discover_fonts(mode)
            for spec in GALLERY_SPECS:
                params = build_rcparams(contracts, geometry=spec.geometry, typography=mode)
                with mpl.rc_context(rc=params):
                    figure = build_template(spec.template)
                    figure.set_size_inches(params["figure.figsize"], forward=False)
                    result = render_figure(
                        figure,
                        gallery / mode / spec.stem,
                        work_root=work_root / mode,
                        typography=mode,
                        geometry=spec.geometry,
                    )
                    plt.close(figure)
                geometry = contracts.style["geometry"][spec.geometry]
                width_mm = float(geometry["width_mm"])
                height_mm = width_mm / float(geometry["aspect"])
                entry = validate_pair(
                    result.pdf,
                    result.png,
                    expected_width_mm=width_mm,
                    expected_height_mm=height_mm,
                    tectonic_log=result.log,
                )
                results.append(result)
                manifest["figures"].append(
                    {
                        "mode": mode,
                        "stem": spec.stem,
                        "template": spec.template,
                        "geometry": spec.geometry,
                        "pdf_sha256": _sha256(result.pdf),
                        "png_sha256": _sha256(result.png),
                        "font_sources": {role: font.path for role, font in fonts.items()},
                        "font_rows": list(entry.fonts),
                    }
                )
    (work_root / "gallery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return results
