from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.gallery import GALLERY_MODES, GALLERY_SPECS, build_gallery
from axiomfig.rendering import render_figure
from axiomfig.templates import TEMPLATE_BUILDERS, build_template
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_gallery, validate_pair


def _selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--geometry", default="single-column")
    parser.add_argument("--typography", default="sans")


def render_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one AxiomFig template through Tectonic")
    parser.add_argument("template", choices=sorted(TEMPLATE_BUILDERS))
    parser.add_argument("--output", type=Path, required=True, help="Output stem without extension")
    parser.add_argument("--work-root", type=Path, default=Path("tmp/render"))
    _selection_arguments(parser)
    args = parser.parse_args(argv)

    discover_fonts(mode=args.typography)
    output = args.output.expanduser().resolve()
    work_root = args.work_root.expanduser().resolve()
    params = build_rcparams(load_contracts(), geometry=args.geometry, typography=args.typography)
    with mpl.rc_context(rc=params):
        figure = build_template(args.template)
        figure.set_size_inches(params["figure.figsize"], forward=False)
        result = render_figure(
            figure,
            output,
            work_root=work_root,
            typography=args.typography,
            geometry=args.geometry,
        )
        plt.close(figure)
    validate_pair(result.pdf, result.png, tectonic_log=result.log)
    print(result.pdf)
    print(result.png)
    return 0


def validate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an AxiomFig gallery")
    parser.add_argument("gallery", type=Path, nargs="?", default=Path("gallery"))
    args = parser.parse_args(argv)
    entries = validate_gallery(args.gallery.expanduser().resolve())
    for entry in entries:
        print(
            f"PASS {entry.pdf.path.name} {entry.pdf.width_mm:.2f} x "
            f"{entry.pdf.height_mm:.2f} mm {entry.pdf.size_bytes} bytes"
        )
    return 0


def gallery_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild the complete AxiomFig gallery")
    parser.add_argument("--gallery", type=Path, default=Path("gallery"))
    parser.add_argument("--work-root", type=Path, default=Path("tmp/gallery"))
    args = parser.parse_args(argv)
    gallery = args.gallery.expanduser().resolve()
    work_root = args.work_root.expanduser().resolve()
    results = build_gallery(gallery, work_root=work_root)
    expected = [f"{mode}/{spec.stem}" for mode in GALLERY_MODES for spec in GALLERY_SPECS]
    validate_gallery(gallery, expected_stems=expected)
    for result in results:
        print(f"PASS {result.pdf.name} + {result.png.name}")
    return 0
