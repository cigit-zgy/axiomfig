#!/usr/bin/env python3
"""Run the complete v1 external-data release evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.evaluation.run import run_evaluation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tmp/evaluation"))
    parser.add_argument("--gallery", type=Path, default=Path("gallery"))
    args = parser.parse_args()

    result = run_evaluation(
        render=True,
        artifacts_dir=args.output.expanduser().resolve(),
        gallery_root=args.gallery.expanduser().resolve(),
    )
    print(json.dumps(asdict(result), indent=2))
    complete = (
        result.routing_rate == 1.0
        and result.canonical_render_rate == 1.0
        and result.external_render_rate == 1.0
        and result.runtime_validation_rate == 1.0
        and result.repeatable
        and result.gallery_coverage_rate == 1.0
        and result.artifact_rate == 1.0
        and not result.failures
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
