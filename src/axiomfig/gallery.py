from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import matplotlib as mpl
import matplotlib.pyplot as plt

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.rendering import RenderResult, render_figure
from axiomfig.templates import TEMPLATE_GALLERY_CASES, build_template
from axiomfig.templates.registry import public_template_specs
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

GALLERY_TYPOGRAPHY = "serif"


@dataclass(frozen=True)
class GallerySpec:
    template_id: str
    geometry: str
    output_id: str
    example_id: str | None = None
    values: Callable[[], dict[str, object]] | None = None

    @property
    def family(self) -> str:
        return self.output_id.split("/", maxsplit=1)[0]


def _gallery_specs() -> tuple[GallerySpec, ...]:
    specs: list[GallerySpec] = []
    for spec in public_template_specs():
        if not spec.agent_recommended:
            continue
        cases = TEMPLATE_GALLERY_CASES.get(spec.template_id)
        if cases is not None:
            specs.extend(
                GallerySpec(
                    spec.template_id,
                    case.geometry,
                    case.output_id,
                    case.example_id,
                    case.values,
                )
                for case in cases
            )
        else:
            specs.append(GallerySpec(spec.template_id, spec.geometry, spec.template_id))
    return tuple(specs)


GALLERY_SPECS = _gallery_specs()


def expected_gallery_stems() -> tuple[str, ...]:
    return tuple(spec.output_id for spec in GALLERY_SPECS)


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
    expected_families = {spec.family for spec in GALLERY_SPECS}
    for path in root.iterdir():
        if path.is_file() and path.name == "README.md":
            continue
        if not path.is_dir() or path.name not in expected_families:
            raise RuntimeError(f"unexpected Gallery content: {path}")
        _assert_generated_tree(path)
        shutil.rmtree(path)
    for family in sorted(expected_families):
        (root / family).mkdir()


def build_gallery(gallery: Path, *, work_root: Path) -> list[RenderResult]:
    gallery = Path(gallery).expanduser().resolve()
    work_root = Path(work_root).expanduser().resolve()
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    _prepare_gallery(gallery)
    contracts = load_contracts()
    results: list[RenderResult] = []
    manifest: dict[str, Any] = {"typography": GALLERY_TYPOGRAPHY, "figures": []}

    with _deterministic_pdf_environment():
        fonts = discover_fonts(GALLERY_TYPOGRAPHY)
        for spec in GALLERY_SPECS:
            params = build_rcparams(
                contracts,
                geometry=spec.geometry,
                typography=GALLERY_TYPOGRAPHY,
            )
            with mpl.rc_context(rc=params):
                values = spec.values() if spec.values is not None else {}
                figure = build_template(spec.template_id, **values)
                figure.set_size_inches(
                    cast(tuple[float, float], params["figure.figsize"]), forward=False
                )
                result = render_figure(
                    figure,
                    gallery / spec.output_id,
                    work_root=work_root / spec.family,
                    typography=GALLERY_TYPOGRAPHY,
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
                    "template": spec.template_id,
                    "example": spec.example_id,
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
