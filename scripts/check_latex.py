#!/usr/bin/env python3
"""Compile and inspect AxiomFig's standalone scientific LaTeX probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from axiomfig.latex import compile_latex_probe  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "tmp" / "latex-probe",
        help="directory for the PDF, TeX source, package copies, and logs",
    )
    args = parser.parse_args()

    result = compile_latex_probe(args.output_dir)
    normalized_text = " ".join(result.extracted_text.split())
    print(f"PASS Tectonic: {' '.join(result.tectonic_command)}")
    print(f"PASS PDF: {result.pdf}")
    print(f"PASS PDF text: {normalized_text}")
    print("PASS embedded fonts:")
    for row in result.fonts:
        print(f"  {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
