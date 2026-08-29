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

from axiomfig.rendering import RenderResult, render_figure
from axiomfig.styles import StyleSelection, compose_styles
from axiomfig.templates import PROJECT_ROOT, build_template
from axiomfig.typography import discover_fonts
from axiomfig.validation import ValidationError, extract_pdf_text, validate_pair

GEOMETRY_MM = {
    "single-column": (90.0, 67.5),
    "onehalf-column": (140.0, 105.0),
    "double-column": (190.0, 142.5),
}

MULTILINGUAL_REQUIRED = (
    "Nitrification efficiency",
    "硝化效率",
    "硝化効率",
    "μ",
    "NH4",
    "α",
    "β",
)


@dataclass(frozen=True)
class GallerySpec:
    stem: str
    template: str
    typography: str
    geometry: str
    colors: str
    plot: str

    def selection(self) -> StyleSelection:
        return StyleSelection(
            geometry=self.geometry,
            typography=self.typography,
            colors=self.colors,
            plot=self.plot,
        )


GALLERY_SPECS = (
    GallerySpec("01_line", "line-ci", "sans", "single-column", "default", "line"),
    GallerySpec("02_scatter", "scatter-grouped", "sans", "single-column", "colorblind", "scatter"),
    GallerySpec("03_bar", "bar-grouped", "sans", "single-column", "default", "bar"),
    GallerySpec("04_violin", "violin", "sans", "single-column", "muted", "distribution"),
    GallerySpec("05_heatmap", "heatmap", "sans", "single-column", "default", "heatmap"),
    GallerySpec(
        "06_model_evaluation", "model-evaluation", "sans", "double-column", "colorblind", "scatter"
    ),
    GallerySpec("07_multilingual", "multilingual", "sans", "onehalf-column", "default", "line"),
    GallerySpec("08_multi_panel", "layout-4-panel", "sans", "double-column", "default", "line"),
    GallerySpec("09_serif", "multilingual", "serif", "onehalf-column", "default", "line"),
    GallerySpec("10_style_contract", "style-contract", "sans", "double-column", "default", "line"),
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


def _prepare_gallery(gallery: Path) -> None:
    gallery.mkdir(parents=True, exist_ok=True)
    unexpected = [path for path in gallery.iterdir() if path.suffix.lower() not in {".pdf", ".png"}]
    if unexpected:
        names = ", ".join(path.name for path in unexpected)
        raise RuntimeError(f"gallery contains non-output files; refusing to remove them: {names}")
    for path in gallery.iterdir():
        path.unlink()


def build_gallery(gallery: Path, *, work_root: Path | None = None) -> list[RenderResult]:
    gallery = Path(gallery)
    work_root = Path(work_root) if work_root is not None else PROJECT_ROOT / "tmp" / "gallery"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    _prepare_gallery(gallery)

    fonts_by_mode = {
        spec.typography: discover_fonts(mode=spec.typography) for spec in GALLERY_SPECS
    }
    style_root = PROJECT_ROOT / "styles"
    results: list[RenderResult] = []
    manifest: dict[str, object] = {
        "fonts": {
            mode: {role: font.__dict__ for role, font in fonts.items()}
            for mode, fonts in fonts_by_mode.items()
        },
        "figures": [],
    }

    with _deterministic_pdf_environment():
        for spec in GALLERY_SPECS:
            composed = compose_styles(spec.selection().paths(style_root))
            with mpl.rc_context(rc=composed.params):
                figure = build_template(spec.template, typography=spec.typography)
                figure.set_size_inches(composed.params["figure.figsize"], forward=False)
                result = render_figure(
                    figure,
                    gallery / spec.stem,
                    work_root=work_root,
                    typography=spec.typography,
                )
                plt.close(figure)
            width_mm, height_mm = GEOMETRY_MM[spec.geometry]
            entry = validate_pair(
                result.pdf,
                result.png,
                expected_width_mm=width_mm,
                expected_height_mm=height_mm,
                tectonic_log=result.log,
            )
            if spec.template == "multilingual":
                extracted = extract_pdf_text(result.pdf)
                missing = [text for text in MULTILINGUAL_REQUIRED if text not in extracted]
                if missing:
                    raise ValidationError(f"multilingual PDF is missing required text: {missing}")
            results.append(result)
            manifest["figures"].append(
                {
                    "stem": spec.stem,
                    "template": spec.template,
                    "typography": spec.typography,
                    "style_paths": [str(path.relative_to(PROJECT_ROOT)) for path in composed.paths],
                    "tectonic_command": list(result.tectonic_command),
                    "intermediate_pdf": str(result.intermediate_pdf),
                    "pdf_bytes": entry.pdf.size_bytes,
                    "pdf_sha256": _sha256(result.pdf),
                    "png_sha256": _sha256(result.png),
                    "width_mm": entry.pdf.width_mm,
                    "height_mm": entry.pdf.height_mm,
                    "font_rows": list(entry.fonts),
                }
            )

    (work_root / "gallery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return results
