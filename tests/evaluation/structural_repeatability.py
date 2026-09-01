"""Release-only structural repeatability gate for all public templates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.templates import build_template
from axiomfig.templates.registry import public_template_specs
from axiomfig.typography import discover_fonts

MODULE_NAME = "tests.evaluation.structural_repeatability"


def _rounded(values: object, digits: int = 7) -> list[float | str]:
    array = np.asarray(values, dtype=float).ravel()
    return [
        "nan"
        if np.isnan(value)
        else "inf"
        if np.isposinf(value)
        else "-inf"
        if np.isneginf(value)
        else round(float(value), digits)
        for value in array
    ]


def figure_signature(figure: mpl.figure.Figure) -> str:
    """Return a deterministic signature of scientific and rendered structure."""

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    payload: dict[str, Any] = {
        "size_inches": _rounded(figure.get_size_inches()),
        "axes": [],
        "texts": [],
    }
    for axis in figure.axes:
        legend = axis.get_legend()
        axis_payload = {
            "position": _rounded(axis.get_position().bounds),
            "bbox": _rounded(axis.bbox.bounds),
            "xlim": _rounded(axis.get_xlim()),
            "ylim": _rounded(axis.get_ylim()),
            "lines": [
                {
                    "xy": _rounded(line.get_xydata()),
                    "marker": line.get_marker(),
                    "linestyle": line.get_linestyle(),
                }
                for line in axis.lines
            ],
            "collections": [
                {
                    "offsets": _rounded(collection.get_offsets()),
                    "paths": len(collection.get_paths()),
                }
                for collection in axis.collections
            ],
            "patches": [
                {
                    "type": type(patch).__name__,
                    "bbox": _rounded(patch.get_window_extent(renderer).bounds),
                }
                for patch in axis.patches
            ],
            "legend": None
            if legend is None
            else {
                "bbox": _rounded(legend.get_window_extent(renderer).bounds),
                "entries": [text.get_text() for text in legend.get_texts()],
                "title": legend.get_title().get_text(),
            },
        }
        payload["axes"].append(axis_payload)
    for text in figure.findobj(mpl.text.Text):
        if text.get_visible() and text.get_text():
            payload["texts"].append(
                {
                    "text": text.get_text(),
                    "position": _rounded(text.get_position()),
                    "bbox": _rounded(text.get_window_extent(renderer).bounds),
                }
            )
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_signatures() -> dict[str, str]:
    """Build one canonical structural signature for each public template."""

    signatures: dict[str, str] = {}
    contracts = load_contracts()
    discover_fonts("sans", contracts=contracts)
    for spec in public_template_specs():
        params = build_rcparams(contracts, geometry=spec.geometry, typography="sans")
        with mpl.rc_context(rc=params):
            figure = build_template(spec.template_id)
            figure.set_size_inches(params["figure.figsize"], forward=False)
            try:
                signatures[spec.template_id] = figure_signature(figure)
            finally:
                plt.close(figure)
    return signatures


def _write_worker(path: Path) -> int:
    path.write_text(json.dumps(build_signatures(), sort_keys=True), encoding="utf-8")
    return 0


def run_gate(*, repeats: int = 3, fresh_processes: int = 2) -> dict[str, object]:
    """Compare repeated same-process and fresh-process signatures."""

    if repeats < 3:
        raise ValueError("structural repeatability requires at least three in-process runs")
    if fresh_processes < 1:
        raise ValueError("structural repeatability requires a fresh-process control")
    runs = [build_signatures() for _ in range(repeats)]
    with tempfile.TemporaryDirectory(prefix="axiomfig-repeatability-") as temporary:
        root = Path(temporary)
        for index in range(fresh_processes):
            output = root / f"fresh-{index}.json"
            subprocess.run(
                [sys.executable, "-m", MODULE_NAME, "--worker", str(output)],
                check=True,
            )
            runs.append(json.loads(output.read_text(encoding="utf-8")))
    template_ids = tuple(sorted(runs[0]))
    mismatches = {
        template_id: [run[template_id] for run in runs]
        for template_id in template_ids
        if len({run[template_id] for run in runs}) != 1
    }
    return {
        "public_templates": len(template_ids),
        "in_process_runs": repeats,
        "fresh_process_runs": fresh_processes,
        "passed": len(template_ids) - len(mismatches),
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--fresh-processes", type=int, default=2)
    args = parser.parse_args()
    if args.worker is not None:
        return _write_worker(args.worker)
    result = run_gate(repeats=args.repeats, fresh_processes=args.fresh_processes)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["public_templates"] == result["passed"] == 55 else 1


if __name__ == "__main__":
    raise SystemExit(main())
