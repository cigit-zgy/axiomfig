from __future__ import annotations

import json
import shutil
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
    geometry: str
    colors: str
    plot: str

    def selection(self) -> StyleSelection:
        return StyleSelection(
            geometry=self.geometry,
            colors=self.colors,
            plot=self.plot,
        )


GALLERY_SPECS = (
    GallerySpec("01_line", "line-ci", "single-column", "default", "line"),
    GallerySpec("02_scatter", "scatter-grouped", "single-column", "colorblind", "scatter"),
    GallerySpec("03_bar", "bar-grouped", "single-column", "default", "bar"),
    GallerySpec("04_violin", "violin", "single-column", "muted", "distribution"),
    GallerySpec("05_heatmap", "heatmap", "single-column", "default", "heatmap"),
    GallerySpec(
        "06_model_evaluation", "model-evaluation", "double-column", "colorblind", "scatter"
    ),
    GallerySpec("07_multilingual", "multilingual", "onehalf-column", "default", "line"),
    GallerySpec("08_multi_panel", "layout-4-panel", "double-column", "default", "line"),
)


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

    fonts = discover_fonts()
    style_root = PROJECT_ROOT / "styles"
    results: list[RenderResult] = []
    manifest: dict[str, object] = {
        "fonts": {role: font.__dict__ for role, font in fonts.items()},
        "figures": [],
    }

    for spec in GALLERY_SPECS:
        composed = compose_styles(spec.selection().paths(style_root))
        with mpl.rc_context(rc=composed.params):
            figure = build_template(spec.template)
            figure.set_size_inches(composed.params["figure.figsize"], forward=False)
            result = render_figure(
                figure,
                gallery / spec.stem,
                work_root=work_root,
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
        if spec.stem == "07_multilingual":
            extracted = extract_pdf_text(result.pdf)
            missing = [text for text in MULTILINGUAL_REQUIRED if text not in extracted]
            if missing:
                raise ValidationError(f"multilingual PDF is missing required text: {missing}")
        results.append(result)
        manifest["figures"].append(
            {
                "stem": spec.stem,
                "template": spec.template,
                "style_paths": [str(path.relative_to(PROJECT_ROOT)) for path in composed.paths],
                "tectonic_command": list(result.tectonic_command),
                "intermediate_pdf": str(result.intermediate_pdf),
                "pdf_bytes": entry.pdf.size_bytes,
                "width_mm": entry.pdf.width_mm,
                "height_mm": entry.pdf.height_mm,
                "font_rows": list(entry.fonts),
            }
        )

    (work_root / "gallery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return results
