"""Canonical Paul Tol palettes and deterministic renderers."""

from collections.abc import Mapping

PALETTES: dict[str, dict[str, str]] = {
    "default": {
        "AxiomBlue": "4477AA",
        "AxiomRed": "EE6677",
        "AxiomGreen": "228833",
        "AxiomYellow": "CCBB44",
        "AxiomCyan": "66CCEE",
        "AxiomPurple": "AA3377",
        "AxiomGrey": "BBBBBB",
    },
    "colorblind": {
        "AxiomBlue": "004488",
        "AxiomYellow": "DDAA33",
        "AxiomRed": "BB5566",
    },
    "muted": {
        "AxiomRed": "CC6677",
        "AxiomPurple": "332288",
        "AxiomYellow": "DDCC77",
        "AxiomGreen": "117733",
        "AxiomCyan": "88CCEE",
        "AxiomWine": "882255",
        "AxiomTeal": "44AA99",
        "AxiomOlive": "999933",
        "AxiomMagenta": "AA4499",
    },
}


def _palette(name: str) -> Mapping[str, str]:
    try:
        return PALETTES[name]
    except KeyError as error:
        choices = ", ".join(PALETTES)
        raise ValueError(f"Unknown palette {name!r}; choose one of: {choices}") from error


def render_mplstyle(name: str) -> str:
    """Render a Matplotlib color style from its canonical Paul Tol palette."""
    colors = ", ".join(f"'{value}'" for value in _palette(name).values())
    header = "# Generated from axiomfig.colors.PALETTES; do not edit manually.\n"
    return f"{header}axes.prop_cycle: cycler(color=[{colors}])\n"


def render_xcolor() -> str:
    """Render the default canonical palette as xcolor HTML definitions."""
    definitions = "\n".join(
        f"\\definecolor{{{name}}}{{HTML}}{{{value}}}" for name, value in _palette("default").items()
    )
    return f"% Generated from axiomfig.colors.PALETTES; do not edit manually.\n{definitions}\n"
