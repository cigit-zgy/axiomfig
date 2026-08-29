"""Canonical scientific palettes loaded from ``styles/colors.yaml``."""

from __future__ import annotations

from collections.abc import Mapping

from axiomfig.config import Contracts, load_contracts


def palettes(contracts: Contracts | None = None) -> Mapping[str, Mapping[str, str]]:
    selected = contracts or load_contracts()
    return selected.colors["palettes"]


def render_xcolor(contracts: Contracts | None = None) -> str:
    selected = contracts or load_contracts()
    default_name = selected.colors["default"]
    definitions = [
        f"\\definecolor{{{name}}}{{HTML}}{{{value.removeprefix('#')}}}"
        for name, value in palettes(selected)[default_name].items()
    ]
    for palette_name, values in palettes(selected).items():
        if not palette_name.startswith("axiom_"):
            continue
        prefix = palette_name.removeprefix("axiom_").title().replace("_", "")
        definitions.extend(
            f"\\definecolor{{Axiom{prefix}{name.removeprefix('Axiom')}}}"
            f"{{HTML}}{{{value.removeprefix('#')}}}"
            for name, value in values.items()
        )
    return (
        "% Generated from styles/colors.yaml; do not edit manually.\n"
        + "\n".join(definitions)
        + "\n"
    )
