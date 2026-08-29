import re
from pathlib import Path

from axiomfig.colors import PALETTES, render_mplstyle, render_xcolor

ROOT = Path(__file__).resolve().parents[1]


def test_generated_matplotlib_palette_matches_the_committed_default_style() -> None:
    assert (ROOT / "styles/colors/default.mplstyle").read_text(encoding="utf-8") == render_mplstyle(
        "default"
    )


def test_matplotlib_and_xcolor_use_exactly_the_same_canonical_rgb_values() -> None:
    xcolor_values = dict(
        re.findall(r"\\definecolor\{(Axiom\w+)\}\{HTML\}\{([0-9A-F]{6})\}", render_xcolor())
    )

    assert xcolor_values == PALETTES["default"]
    assert tuple(xcolor_values.values()) == tuple(PALETTES["default"].values())
    assert (ROOT / "latex/axiomfig-colors.tex").read_text(encoding="utf-8") == render_xcolor()
