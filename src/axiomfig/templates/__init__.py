from __future__ import annotations

from collections.abc import Callable

from matplotlib.figure import Figure

from axiomfig.templates.curves import build_line, build_scatter
from axiomfig.templates.distributions import build_bar, build_violin
from axiomfig.templates.panels import build_multi_panel
from axiomfig.templates.surfaces import build_heatmap

TEMPLATE_BUILDERS: dict[str, Callable[..., Figure]] = {
    "line": build_line,
    "scatter": build_scatter,
    "bar": build_bar,
    "violin": build_violin,
    "heatmap": build_heatmap,
    "multi-panel": build_multi_panel,
}


def get_template_builder(name: str) -> Callable[..., Figure]:
    try:
        return TEMPLATE_BUILDERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise KeyError(f"unknown template {name!r}; available: {available}") from exc


def build_template(name: str, **kwargs: object) -> Figure:
    return get_template_builder(name)(**kwargs)
