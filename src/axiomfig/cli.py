from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from axiomfig.gallery import GALLERY_SPECS, build_gallery
from axiomfig.rendering import render_figure
from axiomfig.styles import StyleSelection, compose_styles, write_composed_style
from axiomfig.templates import TEMPLATE_BUILDERS, build_template
from axiomfig.typography import discover_fonts
from axiomfig.validation import validate_gallery, validate_pair


def _selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--geometry", default="single-column")
    parser.add_argument("--typography", default="sans")
    parser.add_argument("--colors", default="default")
    parser.add_argument("--plot", default="line")
    parser.add_argument("--language", default="multilingual")
    parser.add_argument("--rendering", default="vector")


def _selection(namespace: argparse.Namespace) -> StyleSelection:
    return StyleSelection(
        geometry=namespace.geometry,
        typography=namespace.typography,
        colors=namespace.colors,
        plot=namespace.plot,
        language=namespace.language,
        rendering=namespace.rendering,
    )


def compose_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compose deterministic AxiomFig style modules")
    _selection_arguments(parser)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    path = write_composed_style(_selection(args).paths(), args.output.expanduser().resolve())
    print(path)
    return 0


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
    composed = compose_styles(_selection(args).paths())
    with mpl.rc_context(rc=composed.params):
        figure = build_template(args.template, typography=args.typography)
        figure.set_size_inches(composed.params["figure.figsize"], forward=False)
        result = render_figure(figure, output, work_root=work_root, typography=args.typography)
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
    expected = [spec.stem for spec in GALLERY_SPECS]
    validate_gallery(gallery, expected_stems=expected)
    for result in results:
        print(f"PASS {result.pdf.name} + {result.png.name}")
    return 0
