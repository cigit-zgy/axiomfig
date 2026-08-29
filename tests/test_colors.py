import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_default_rc_cycle_is_loaded_from_canonical_colors_yaml() -> None:
    from axiomfig.colors import palettes
    from axiomfig.config import build_rcparams, load_contracts

    contracts = load_contracts(ROOT / "styles")
    params = build_rcparams(contracts, geometry="single-column", typography="sans")

    assert tuple(params["axes.prop_cycle"].by_key()["color"]) == tuple(
        palettes(contracts)["default"].values()
    )


def test_matplotlib_and_xcolor_use_the_same_canonical_rgb_values() -> None:
    from axiomfig.colors import palettes, render_xcolor
    from axiomfig.config import load_contracts

    contracts = load_contracts(ROOT / "styles")
    expected = {
        name: value.removeprefix("#") for name, value in palettes(contracts)["default"].items()
    }
    xcolor_values = dict(
        re.findall(
            r"\\definecolor\{(Axiom\w+)\}\{HTML\}\{([0-9A-F]{6})\}",
            render_xcolor(contracts),
        )
    )

    assert xcolor_values == expected
    assert (ROOT / "src/axiomfig/resources/latex/axiomfig-colors.tex").read_text(
        encoding="utf-8"
    ) == render_xcolor(contracts)
