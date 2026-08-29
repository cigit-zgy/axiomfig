import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_default_rc_cycle_is_loaded_from_canonical_colors_yaml() -> None:
    from axiomfig.colors import palettes
    from axiomfig.config import build_rcparams, load_contracts

    contracts = load_contracts(ROOT / "styles")
    params = build_rcparams(contracts, geometry="single-column", typography="sans")

    assert tuple(params["axes.prop_cycle"].by_key()["color"]) == tuple(
        palettes(contracts)[contracts.colors["default"]].values()
    )


def test_matplotlib_and_xcolor_use_the_same_canonical_rgb_values() -> None:
    from axiomfig.colors import palettes, render_xcolor
    from axiomfig.config import load_contracts

    contracts = load_contracts(ROOT / "styles")
    expected = {
        name: value.removeprefix("#")
        for name, value in palettes(contracts)[contracts.colors["default"]].items()
    }
    xcolor_values = dict(
        re.findall(
            r"\\definecolor\{(Axiom\w+)\}\{HTML\}\{([0-9A-F]{6})\}",
            render_xcolor(contracts),
        )
    )

    assert {name: xcolor_values[name] for name in expected} == expected
    assert (ROOT / "src/axiomfig/resources/latex/axiomfig-colors.tex").read_text(
        encoding="utf-8"
    ) == render_xcolor(contracts)


def test_round04_palettes_are_complete_and_have_stable_axiom_tokens() -> None:
    from axiomfig.colors import palettes
    from axiomfig.config import load_contracts

    contracts = load_contracts(ROOT / "styles")
    available = palettes(contracts)
    assert set(available) == {
        "tol_bright",
        "tol_muted",
        "axiom_classic",
        "axiom_soft",
        "axiom_deep",
        "axiom_warm",
        "axiom_cool",
        "grayscale",
    }
    required = {
        "AxiomBlue",
        "AxiomCyan",
        "AxiomGreen",
        "AxiomYellow",
        "AxiomOrange",
        "AxiomRed",
        "AxiomPurple",
        "AxiomGrey",
    }
    for name in (
        "axiom_classic",
        "axiom_soft",
        "axiom_deep",
        "axiom_warm",
        "axiom_cool",
        "grayscale",
    ):
        assert set(available[name]) == required


def test_all_axiom_palettes_have_palette_qualified_xcolor_names() -> None:
    from axiomfig.colors import render_xcolor

    source = render_xcolor()
    for prefix in ("Classic", "Soft", "Deep", "Warm", "Cool"):
        for suffix in ("Blue", "Cyan", "Green", "Yellow", "Orange", "Red", "Purple", "Grey"):
            assert f"\\definecolor{{Axiom{prefix}{suffix}}}" in source
