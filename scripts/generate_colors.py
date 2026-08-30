"""Generate the LaTeX xcolor artifact from canonical colors.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from axiomfig.style import render_xcolor  # noqa: E402


def artifacts() -> dict[Path, str]:
    """Return all generated color artifact paths and their expected contents."""
    content = render_xcolor()
    return {ROOT / "src/axiomfig/resources/latex/axiomfig-colors.tex": content}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if committed artifacts are stale"
    )
    args = parser.parse_args()
    expected = artifacts()

    if args.check:
        stale = [
            path
            for path, content in expected.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print("Stale generated color artifacts:", *stale, sep="\n", file=sys.stderr)
            return 1
        return 0

    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
