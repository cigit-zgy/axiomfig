from __future__ import annotations

import importlib.util
from collections.abc import Callable
from importlib.resources import as_file, files
from types import ModuleType

from matplotlib.figure import Figure

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
    "style-contract": ("style_contract.py", "build_style_contract"),
}


def _load_module(filename: str) -> ModuleType:
    resource = files("axiomfig").joinpath("resources", "templates", filename)
    if not resource.is_file():
        raise FileNotFoundError(f"Packaged template resource is missing: {filename}")
    with as_file(resource) as path:
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


def build_template(name: str, *, typography: str = "sans", **kwargs: object) -> Figure:
    builder = get_template_builder(name)
    if name == "multilingual":
        return builder(mode=typography, **kwargs)
    return builder(**kwargs)
