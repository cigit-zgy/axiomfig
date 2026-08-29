from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from matplotlib.figure import Figure

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_BUILDERS: dict[str, tuple[str, str]] = {
    "line-single": ("line.py", "build_single"),
    "line-multi": ("line.py", "build_multi"),
    "line-marker": ("line.py", "build_marker"),
    "line-ci": ("line.py", "build_confidence_interval"),
    "scatter-basic": ("scatter.py", "build_basic"),
    "scatter-grouped": ("scatter.py", "build_grouped"),
    "scatter-parity": ("scatter.py", "build_parity"),
    "bar-vertical": ("bar.py", "build_vertical"),
    "bar-grouped": ("bar.py", "build_grouped"),
    "boxplot": ("distribution.py", "build_boxplot"),
    "violin": ("distribution.py", "build_violin"),
    "heatmap": ("heatmap.py", "build_heatmap"),
    "model-evaluation": ("model_evaluation.py", "build_summary"),
    "residual": ("model_evaluation.py", "build_residual"),
    "layout-2-panel": ("layout.py", "build_two_panel"),
    "layout-4-panel": ("layout.py", "build_four_panel"),
    "multilingual": ("multilingual.py", "build_multilingual"),
}


def _load_module(filename: str) -> ModuleType:
    path = PROJECT_ROOT / "templates" / filename
    spec = importlib.util.spec_from_file_location(f"axiomfig_user_template_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load template module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_template_builder(name: str) -> Callable[..., Figure]:
    try:
        filename, function_name = TEMPLATE_BUILDERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise KeyError(f"Unknown template {name!r}; available: {available}") from exc
    builder = getattr(_load_module(filename), function_name)
    return builder


def build_template(name: str, **kwargs: object) -> Figure:
    return get_template_builder(name)(**kwargs)
