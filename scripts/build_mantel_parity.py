#!/usr/bin/env python3
"""Build and validate the non-registry Mantel R-grammar reference atlas."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import yaml
from PIL import Image, ImageDraw

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.rendering import render_figure
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.builder import canonical_mantel_values
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "mantel-r-parity.yaml"
DEFAULT_GALLERY = ROOT / "gallery"
REVIEW_SHEETS: dict[str, tuple[str, ...]] = {
    "01-canonical-coupling.png": (
        "linket/lower-coupling",
        "linket/upper-coupling",
        "coupling/multi-source",
        "coupling/sparse",
        "coupling/dense",
    ),
    "02-correlation-glyphs.png": (
        "corrplot/circle-full",
        "corrplot/square-lower",
        "corrplot/ellipse-upper-aoe",
        "corrplot/number-full",
        "corrplot/shade-aoe",
        "corrplot/color-aoe",
        "corrplot/pie-aoe",
    ),
    "03-mixed-ordering.png": (
        "mixed/circle-ellipse",
        "mixed/square-number",
        "mixed/shade-pie",
        "ordering/original",
        "ordering/alphabet",
        "ordering/aoe",
        "ordering/fpc",
        "ordering/hclust-clusters",
    ),
    "04-significance-ci.png": (
        "corrplot/circle-coefficients",
        "significance/mark",
        "significance/p-value",
        "significance/blank",
        "significance/stars",
        "confidence_interval/square",
        "confidence_interval/circle",
        "confidence_interval/rect",
    ),
}


def load_manifest(path: Path = DEFAULT_MANIFEST) -> tuple[Mapping[str, object], ...]:
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, Mapping) or document.get("version") != 1:
        raise ValueError("Mantel parity manifest must use version 1")
    examples = document.get("examples")
    if not isinstance(examples, Sequence) or isinstance(examples, (str, bytes)):
        raise ValueError("Mantel parity manifest examples must be a sequence")
    normalized: list[Mapping[str, object]] = []
    ids: set[str] = set()
    outputs: set[str] = set()
    for index, example in enumerate(examples):
        if not isinstance(example, Mapping):
            raise ValueError(f"examples[{index}] must be a mapping")
        required = {
            "id",
            "source",
            "source_ref",
            "source_call",
            "fixture",
            "composition",
            "expected_output",
        }
        missing = required - set(example)
        if missing:
            raise ValueError(f"examples[{index}] missing fields: {sorted(missing)}")
        identifier = str(example["id"])
        output = str(example["expected_output"])
        if identifier in ids or output in outputs:
            raise ValueError(f"duplicate parity id or output: {identifier}")
        if not output.startswith("gallery/parity/mantel/"):
            raise ValueError(f"parity output must live under gallery/parity/mantel: {output}")
        ids.add(identifier)
        outputs.add(output)
        normalized.append(example)
    return tuple(normalized)


def _correlation(loadings: np.ndarray, residual: np.ndarray) -> np.ndarray:
    covariance = loadings @ loadings.T + np.diag(residual)
    scale = np.sqrt(np.diag(covariance))
    matrix = covariance / np.outer(scale, scale)
    np.fill_diagonal(matrix, 1.0)
    return matrix


def _minimal_links(labels: tuple[str, ...]) -> tuple[dict[str, object], ...]:
    return (
        {
            "source": "Reference group",
            "target": labels[0],
            "mantel_r": 0.42,
            "p_value": 0.012,
        },
    )


def _mtcars_fixture() -> dict[str, object]:
    labels = ("mpg", "cyl", "disp", "hp", "drat", "wt", "qsec", "carb")
    loadings = np.asarray(
        (
            (-0.86, 0.34, 0.12),
            (0.91, -0.18, 0.08),
            (0.88, 0.10, -0.22),
            (0.72, -0.32, 0.44),
            (-0.58, 0.61, 0.06),
            (0.84, 0.31, -0.12),
            (-0.42, 0.72, -0.24),
            (0.48, -0.51, 0.56),
        )
    )
    return {
        "correlation_matrix": _correlation(loadings, np.linspace(0.18, 0.34, len(labels))),
        "labels": labels,
        "links": _minimal_links(labels),
    }


def _generic_fixture() -> dict[str, object]:
    labels = ("Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta")
    coordinates = np.linspace(-1.15, 1.05, len(labels))
    matrix = np.clip(
        0.82 * np.cos(np.subtract.outer(coordinates, coordinates) * 1.35)
        + 0.12 * np.sin(np.add.outer(coordinates, coordinates) * 2.1),
        -1.0,
        1.0,
    )
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    return {"correlation_matrix": matrix, "labels": labels, "links": _minimal_links(labels)}


def _statistical_arrays(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    size = matrix.shape[0]
    levels = (0.0005, 0.005, 0.025, 0.12)
    p_values = np.empty_like(matrix)
    for row in range(size):
        for column in range(size):
            p_values[row, column] = 0.0 if row == column else levels[(row + column) % 4]
    p_values = np.minimum(p_values, p_values.T)
    lower = np.clip(matrix - 0.09, -1.0, 1.0)
    upper = np.clip(matrix + 0.09, -1.0, 1.0)
    np.fill_diagonal(lower, 1.0)
    np.fill_diagonal(upper, 1.0)
    return p_values, lower, upper


def _dense_fixture() -> dict[str, object]:
    labels = (
        "DO",
        "NH4-N",
        "NO3-N",
        "TN",
        "PO4-P",
        "TP",
        "COD",
        "pH",
        "Temp",
        "ORP",
        "Turbidity",
        "Conductivity",
    )
    coordinates = np.linspace(-1.2, 1.2, len(labels))
    matrix = np.clip(np.cos(np.subtract.outer(coordinates, coordinates) * 1.65), -1.0, 1.0)
    np.fill_diagonal(matrix, 1.0)
    sources = ("Surface", "Water column", "Sediment", "Biofilm")
    target_ranges = (range(0, 6), range(2, 8), range(4, 10), range(6, 12))
    links = tuple(
        {
            "source": source,
            "target": labels[target],
            "mantel_r": 0.15 + 0.055 * ((source_index + target) % 11),
            "p_value": (0.0005, 0.005, 0.025, 0.12)[(source_index + target) % 4],
        }
        for source_index, source in enumerate(sources)
        for target in target_ranges[source_index]
    )
    return {"correlation_matrix": matrix, "labels": labels, "links": links}


def _fixture_values(fixture: str) -> dict[str, object]:
    if fixture == "mtcars":
        values = _mtcars_fixture()
    elif fixture == "generic":
        values = _generic_fixture()
    elif fixture in {"environmental", "statistical", "ci", "sparse"}:
        values = canonical_mantel_values()
    elif fixture == "dense":
        values = _dense_fixture()
    else:
        raise ValueError(f"unknown Mantel atlas fixture: {fixture}")

    if fixture == "sparse":
        values = {**values, "links": tuple(values["links"])[::3]}
    if fixture in {"statistical", "ci"}:
        matrix = np.asarray(values["correlation_matrix"], dtype=float)
        p_values, lower, upper = _statistical_arrays(matrix)
        values = {**values, "p_values": p_values, "lower_ci": lower, "upper_ci": upper}
    return values


def _stem(gallery: Path, expected_output: object) -> Path:
    relative = Path(str(expected_output)).relative_to("gallery")
    return gallery / relative


def expected_stems(
    manifest: Sequence[Mapping[str, object]], gallery: Path = DEFAULT_GALLERY
) -> tuple[Path, ...]:
    return tuple(_stem(Path(gallery), entry["expected_output"]) for entry in manifest)


def _review_paths(gallery: Path) -> set[Path]:
    root = Path(gallery) / "parity" / "mantel" / "review"
    return {root / name for name in REVIEW_SHEETS}


def validate_atlas(
    manifest: Sequence[Mapping[str, object]], gallery: Path = DEFAULT_GALLERY
) -> int:
    expected = set(expected_stems(manifest, gallery))
    root = Path(gallery) / "parity" / "mantel"
    review = _review_paths(Path(gallery))
    pdfs = {path.with_suffix("") for path in root.rglob("*.pdf")} if root.exists() else set()
    png_paths = set(root.rglob("*.png")) if root.exists() else set()
    pngs = {path.with_suffix("") for path in png_paths if path not in review}
    if pdfs != expected or pngs != expected or png_paths & review != review:
        raise RuntimeError(
            "Mantel R-grammar atlas mismatch: "
            f"missing_pdf={sorted(expected - pdfs)}, missing_png={sorted(expected - pngs)}, "
            f"missing_review={sorted(review - png_paths)}, orphan_pdf={sorted(pdfs - expected)}, "
            f"orphan_png={sorted(pngs - expected)}"
        )
    if png_paths - {stem.with_suffix(".png") for stem in expected} - review:
        raise RuntimeError("Mantel R-grammar atlas contains orphan review PNGs")
    for stem in sorted(expected):
        validate_pair(stem.with_suffix(".pdf"), stem.with_suffix(".png"))
    return len(expected)


def _build_contact_sheet(atlas_root: Path, output: Path, stems: Sequence[str]) -> None:
    thumb_size = (420, 315)
    caption_height = 30
    columns = 3
    rows = (len(stems) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * thumb_size[0], rows * (thumb_size[1] + caption_height)),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, stem in enumerate(stems):
        source = atlas_root / f"{stem}.png"
        with Image.open(source) as opened:
            image = opened.convert("RGB")
            image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        column = index % columns
        row = index // columns
        x0 = column * thumb_size[0] + (thumb_size[0] - image.width) // 2
        y0 = row * (thumb_size[1] + caption_height) + (thumb_size[1] - image.height) // 2
        canvas.paste(image, (x0, y0))
        caption = stem.replace("_", " ")
        draw.text((column * thumb_size[0] + 8, y0 + thumb_size[1] + 6), caption, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def _build_review_sheets(gallery: Path) -> None:
    atlas_root = gallery / "parity" / "mantel"
    review_root = atlas_root / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    for name, stems in REVIEW_SHEETS.items():
        _build_contact_sheet(atlas_root, review_root / name, stems)


def build_atlas(
    manifest: Sequence[Mapping[str, object]],
    gallery: Path = DEFAULT_GALLERY,
    *,
    work_root: Path | None = None,
) -> int:
    gallery = Path(gallery).expanduser().resolve()
    atlas_root = gallery / "parity" / "mantel"
    if atlas_root.exists():
        shutil.rmtree(atlas_root)
    atlas_root.mkdir(parents=True)
    work_root = (
        Path(work_root).expanduser().resolve()
        if work_root is not None
        else ROOT / "tmp" / "mantel-parity"
    )
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)

    contracts = load_contracts()
    params = build_rcparams(contracts, geometry="onehalf-column", typography="sans")
    discover_fonts("sans")
    for entry in manifest:
        composition = entry["composition"]
        if not isinstance(composition, Mapping):
            raise ValueError(f"composition must be a mapping: {entry['id']}")
        values = _fixture_values(str(entry["fixture"]))
        with mpl.rc_context(rc=params):
            figure = build_template("association/mantel", **values, **dict(composition))
            figure.set_size_inches(params["figure.figsize"], forward=False)
            stem = _stem(gallery, entry["expected_output"])
            render_figure(
                figure,
                stem,
                work_root=work_root / str(entry["id"]),
                typography="sans",
                geometry="onehalf-column",
            )
            plt.close(figure)
    _build_review_sheets(gallery)
    return validate_atlas(manifest, gallery)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--gallery", type=Path, default=DEFAULT_GALLERY)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    count = (
        validate_atlas(manifest, args.gallery)
        if args.check
        else build_atlas(manifest, args.gallery, work_root=args.work_root)
    )
    print(
        f"PASS Mantel R-grammar atlas: {count}/{len(manifest)} PDF+PNG pairs, "
        f"{len(REVIEW_SHEETS)} review sheets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
