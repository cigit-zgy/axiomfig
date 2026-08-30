import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_ROOT = ROOT / "src" / "axiomfig" / "resources" / "styles"


def test_default_rc_cycle_is_loaded_from_canonical_colors_yaml() -> None:
    from axiomfig.config import build_rcparams, load_contracts
    from axiomfig.style import palettes

    contracts = load_contracts(STYLE_ROOT)
    params = build_rcparams(contracts, geometry="single-column", typography="sans")

    assert tuple(params["axes.prop_cycle"].by_key()["color"]) == tuple(
        palettes(contracts)[contracts.colors["default"]].values()
    )


def test_scientific_colormap_semantics_are_owned_by_colors_yaml() -> None:
    from axiomfig.config import build_rcparams, load_contracts
    from axiomfig.style import semantic_colormap

    contracts = load_contracts(STYLE_ROOT)

    assert set(contracts.colors["colormaps"]) == {
        "qualitative",
        "sequential",
        "diverging",
        "cyclic",
    }
    assert semantic_colormap("sequential", contracts) == "cividis"
    assert semantic_colormap("diverging", contracts) == "RdBu_r"
    assert build_rcparams(contracts)["image.cmap"] == semantic_colormap("sequential", contracts)


def test_matplotlib_and_xcolor_use_the_same_canonical_rgb_values() -> None:
    from axiomfig.config import load_contracts
    from axiomfig.style import palettes, render_xcolor

    contracts = load_contracts(STYLE_ROOT)
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
    from axiomfig.config import load_contracts
    from axiomfig.style import palettes

    contracts = load_contracts(STYLE_ROOT)
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
    from axiomfig.style import render_xcolor

    source = render_xcolor()
    for prefix in ("Classic", "Soft", "Deep", "Warm", "Cool"):
        for suffix in ("Blue", "Cyan", "Green", "Yellow", "Orange", "Red", "Purple", "Grey"):
            assert f"\\definecolor{{Axiom{prefix}{suffix}}}" in source
