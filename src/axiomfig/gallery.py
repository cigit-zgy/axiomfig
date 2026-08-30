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
from axiomfig.latex import LatexGalleryResult, build_latex_gallery
from axiomfig.rendering import RenderResult, render_figure
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.gallery_cases import (
    MANTEL_GALLERY_CASE_IDS,
    MANTEL_GALLERY_GEOMETRIES,
    mantel_gallery_values,
)
from axiomfig.templates.registry import public_template_specs
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

GALLERY_MODES = ("sans", "serif")
TECHNICAL_LATEX_STEMS = ("scientific_typography", "palettes")


@dataclass(frozen=True)
class GallerySpec:
    template_id: str
    geometry: str
    output_id: str
    example_id: str | None = None

    @property
    def family(self) -> str:
        return self.output_id.split("/", maxsplit=1)[0]


def _gallery_specs() -> tuple[GallerySpec, ...]:
    specs: list[GallerySpec] = []
    for spec in public_template_specs():
        if spec.template_id == "association/mantel":
            specs.extend(
                GallerySpec(
                    spec.template_id,
                    MANTEL_GALLERY_GEOMETRIES[case_id],
                    f"association/mantel_{case_id}",
                    case_id,
                )
                for case_id in MANTEL_GALLERY_CASE_IDS
            )
        else:
            specs.append(GallerySpec(spec.template_id, spec.geometry, spec.template_id))
    return tuple(specs)


GALLERY_SPECS = _gallery_specs()


def expected_gallery_stems() -> tuple[str, ...]:
    stems = [f"{mode}/{spec.output_id}" for mode in GALLERY_MODES for spec in GALLERY_SPECS]
    stems.extend(f"technical/latex/{stem}" for stem in TECHNICAL_LATEX_STEMS)
    return tuple(stems)


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


def _assert_generated_tree(path: Path) -> None:
    for artifact in path.rglob("*"):
        if artifact.is_file() and artifact.suffix.lower() not in {".pdf", ".png"}:
            raise RuntimeError(f"unexpected Gallery content: {artifact}")


def _prepare_gallery(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    allowed_roots = {*GALLERY_MODES, "latex", "technical"}
    for path in root.iterdir():
        if not path.is_dir() or path.name not in allowed_roots:
            raise RuntimeError(f"unexpected Gallery content: {path}")
        _assert_generated_tree(path)
        shutil.rmtree(path)
    for mode in GALLERY_MODES:
        (root / mode).mkdir()
    (root / "technical" / "latex").mkdir(parents=True)


def build_gallery(
    gallery: Path, *, work_root: Path | None = None
) -> list[RenderResult | LatexGalleryResult]:
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
    results: list[RenderResult | LatexGalleryResult] = []
    manifest: dict[str, object] = {"figures": []}

    with _deterministic_pdf_environment():
        for mode in GALLERY_MODES:
            fonts = discover_fonts(mode)
            for spec in GALLERY_SPECS:
                params = build_rcparams(contracts, geometry=spec.geometry, typography=mode)
                with mpl.rc_context(rc=params):
                    values = (
                        mantel_gallery_values(spec.example_id)
                        if spec.example_id is not None
                        else {}
                    )
                    figure = build_template(spec.template_id, **values)
                    figure.set_size_inches(params["figure.figsize"], forward=False)
                    result = render_figure(
                        figure,
                        gallery / mode / spec.output_id,
                        work_root=work_root / mode / spec.family,
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
                manifest["figures"].append(  # type: ignore[union-attr]
                    {
                        "mode": mode,
                        "template": spec.template_id,
                        "example": spec.example_id,
                        "geometry": spec.geometry,
                        "pdf_sha256": _sha256(result.pdf),
                        "png_sha256": _sha256(result.png),
                        "font_sources": {role: font.path for role, font in fonts.items()},
                        "font_rows": list(entry.fonts),
                    }
                )
        technical = gallery / "technical" / "latex"
        latex_results = build_latex_gallery(technical, work_root=work_root / "technical" / "latex")
        for result in latex_results:
            entry = validate_pair(result.pdf, result.png, tectonic_log=result.log)
            results.append(result)
            manifest["figures"].append(  # type: ignore[union-attr]
                {
                    "mode": "technical/latex",
                    "template": "tectonic-native",
                    "stem": result.pdf.stem,
                    "geometry": "standalone",
                    "pdf_sha256": _sha256(result.pdf),
                    "png_sha256": _sha256(result.png),
                    "font_rows": list(entry.fonts),
                }
            )
    (work_root / "gallery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return results
