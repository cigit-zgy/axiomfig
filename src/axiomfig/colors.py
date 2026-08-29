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
    definitions = "\n".join(
        f"\\definecolor{{{name}}}{{HTML}}{{{value.removeprefix('#')}}}"
        for name, value in palettes(selected)[default_name].items()
    )
    return "% Generated from styles/colors.yaml; do not edit manually.\n" + definitions + "\n"
