#!/usr/bin/env python3
"""Build and validate the non-registry Mantel R-grammar parity atlas."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import yaml

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.rendering import render_figure
from axiomfig.templates import build_template
from axiomfig.templates.association.mantel.builder import canonical_mantel_values
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_pair

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "mantel-r-parity.yaml"
DEFAULT_GALLERY = ROOT / "gallery"


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


def _statistical_values(fixture: str) -> dict[str, object]:
    values = canonical_mantel_values()
    matrix = np.asarray(values["correlation_matrix"], dtype=float)
    size = matrix.shape[0]
    p_values = np.empty_like(matrix)
    levels = (0.0005, 0.005, 0.025, 0.12)
    for row in range(size):
        for column in range(size):
            p_values[row, column] = 0.0 if row == column else levels[(row + column) % 4]
    p_values = np.minimum(p_values, p_values.T)
    lower = np.clip(matrix - 0.09, -1.0, 1.0)
    upper = np.clip(matrix + 0.09, -1.0, 1.0)
    np.fill_diagonal(lower, 1.0)
    np.fill_diagonal(upper, 1.0)
    links = tuple(values["links"])
    if fixture == "sparse":
        links = links[::3]
    return {
        **values,
        "links": links,
        "p_values": p_values,
        "lower_ci": lower,
        "upper_ci": upper,
    }


def _stem(gallery: Path, expected_output: object) -> Path:
    relative = Path(str(expected_output)).relative_to("gallery")
    return gallery / relative


def expected_stems(
    manifest: Sequence[Mapping[str, object]], gallery: Path = DEFAULT_GALLERY
) -> tuple[Path, ...]:
    return tuple(_stem(Path(gallery), entry["expected_output"]) for entry in manifest)


def validate_atlas(
    manifest: Sequence[Mapping[str, object]], gallery: Path = DEFAULT_GALLERY
) -> int:
    expected = set(expected_stems(manifest, gallery))
    root = Path(gallery) / "parity" / "mantel"
    pdfs = {path.with_suffix("") for path in root.rglob("*.pdf")} if root.exists() else set()
    pngs = {path.with_suffix("") for path in root.rglob("*.png")} if root.exists() else set()
    if pdfs != expected or pngs != expected:
        raise RuntimeError(
            "Mantel parity atlas mismatch: "
            f"missing_pdf={sorted(expected - pdfs)}, missing_png={sorted(expected - pngs)}, "
            f"orphan_pdf={sorted(pdfs - expected)}, orphan_png={sorted(pngs - expected)}"
        )
    for stem in sorted(expected):
        validate_pair(stem.with_suffix(".pdf"), stem.with_suffix(".png"))
    return len(expected)


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
        values = _statistical_values(str(entry["fixture"]))
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
    print(f"PASS Mantel R-parity atlas: {count}/{len(manifest)} PDF+PNG pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
