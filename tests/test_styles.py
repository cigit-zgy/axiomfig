from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STYLE_ROOT = ROOT / "src" / "axiomfig" / "resources" / "styles"


def test_repository_has_exactly_three_canonical_style_sources() -> None:
    assert sorted(path.name for path in STYLE_ROOT.iterdir() if path.is_file()) == [
        "colors.yaml",
        "fonts.yaml",
        "style.yaml",
    ]
    assert not list((ROOT / "src").rglob("*.mplstyle"))
    assert not list(STYLE_ROOT.rglob("*.mplstyle"))
    assert not (ROOT / "styles").exists()


def test_default_contract_loader_uses_packaged_style_resources() -> None:
    from importlib.resources import files

    from axiomfig.config import load_contracts

    root = files("axiomfig").joinpath("resources", "styles")
    assert root.joinpath("style.yaml").is_file()
    assert root.joinpath("fonts.yaml").is_file()
    assert root.joinpath("colors.yaml").is_file()
    assert load_contracts().style["stroke"]["main_stroke_pt"] == 0.8
    assert load_contracts() is load_contracts()


@pytest.mark.parametrize(
    ("name", "width_mm", "height_mm"),
    [
        ("single-column", 90.0, 67.5),
        ("onehalf-column", 140.0, 105.0),
        ("double-column", 190.0, 142.5),
    ],
)
def test_geometry_presets_are_four_to_three_in_physical_units(
    name: str, width_mm: float, height_mm: float
) -> None:
    from axiomfig.config import build_rcparams, load_contracts

    contracts = load_contracts(STYLE_ROOT)
    params = build_rcparams(contracts, geometry=name, typography="sans")

    assert params["figure.figsize"] == pytest.approx((width_mm / 25.4, height_mm / 25.4), abs=1e-9)
    assert math.isclose(width_mm / height_mm, 4 / 3, rel_tol=0, abs_tol=1e-12)


def test_font_point_sizes_do_not_scale_with_figure_width() -> None:
    from axiomfig.config import build_rcparams, load_contracts

    contracts = load_contracts(STYLE_ROOT)
    keys = ("font.size", "axes.labelsize", "axes.titlesize", "xtick.labelsize", "ytick.labelsize")
    narrow = build_rcparams(contracts, geometry="single-column", typography="sans")
    wide = build_rcparams(contracts, geometry="double-column", typography="sans")

    assert {key: narrow[key] for key in keys} == {key: wide[key] for key in keys}


def test_visual_stroke_tokens_are_distinct_and_positive() -> None:
    from axiomfig.config import get_token, load_contracts

    contracts = load_contracts(STYLE_ROOT)

    assert get_token(contracts, "style.stroke.main_stroke_pt") == 0.8
    assert get_token(contracts, "style.stroke.fill_edge_pt") == 0.6


def test_tick_geometry_is_centralized_and_phi_derived() -> None:
    from axiomfig.config import load_contracts

    ticks = load_contracts(STYLE_ROOT).style["ticks"]
    phi = float(ticks["geometry"]["minor_to_major_inward_ratio"])
    minor = float(ticks["geometry"]["minor_length_pt"])
    major = float(ticks["geometry"]["major_length_pt"])

    assert phi == pytest.approx(0.6180339887)
    assert minor == pytest.approx(1.236 * 1.5)
    assert major / 2.0 == pytest.approx(minor / phi)
    assert ticks["open"]["major"]["length_token"] == "major"
    assert ticks["filled"]["major"]["length_token"] == "major"
    assert ticks["open"]["minor"]["length_token"] == "minor"
    assert ticks["filled"]["minor"]["length_token"] == "minor"


def test_bar_width_and_redundant_series_cycle_are_central_tokens() -> None:
    from axiomfig.config import load_contracts

    style = load_contracts(STYLE_ROOT).style

    assert style["plots"]["bar"]["single_width"] == 0.60
    assert style["plots"]["bar"]["group_width"] == 0.76
    assert tuple(style["series"]["line_styles"]) == (
        "solid",
        "dashdot",
        "dotted",
        "long-dash",
    )
    assert tuple(style["series"]["markers"][:4]) == ("o", "s", "^", "D")
    assert style["series"]["reference_line_style"] == "dashdot"


def test_output_margin_contract_is_centralized_and_physical() -> None:
    from axiomfig.config import load_contracts

    output = load_contracts(STYLE_ROOT).style["output"]

    assert output["margin_mode"] == "tight"
    assert output["allowed_margin_modes"] == ("tight", "normal", "custom")
    assert output["padding_pt"] == 1.5


def test_unknown_geometry_and_missing_token_fail_explicitly() -> None:
    from axiomfig.config import build_rcparams, get_token, load_contracts

    contracts = load_contracts(STYLE_ROOT)

    with pytest.raises(ValueError, match="unknown geometry"):
        build_rcparams(contracts, geometry="journal-magic", typography="sans")
    with pytest.raises(KeyError, match="style.not.real"):
        get_token(contracts, "style.not.real")


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("stroke", "main_stroke_pt"), -0.8),
        (("typography", "sizes_pt", "base"), float("nan")),
        (("ticks", "geometry", "minor_length_pt"), -1.0),
        (("output", "padding_pt"), -0.1),
        (("plots", "mantel", "nodes", "source_size_ratio"), 0.0),
        (("plots", "mantel", "links", "curve_curvature"), -0.1),
    ],
)
def test_loader_rejects_invalid_physical_tokens(
    tmp_path: Path, path: tuple[str, ...], value: float
) -> None:
    for source in STYLE_ROOT.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())
    style_path = tmp_path / "style.yaml"
    style = yaml.safe_load(style_path.read_text(encoding="utf-8"))
    target = style
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    style_path.write_text(yaml.safe_dump(style, sort_keys=False), encoding="utf-8")

    from axiomfig.config import load_contracts

    with pytest.raises(ValueError, match="finite|positive|nonnegative"):
        load_contracts(tmp_path)
