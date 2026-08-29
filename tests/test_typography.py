from pathlib import Path

import matplotlib as mpl
import pytest

from axiomfig.config import load_contracts
from axiomfig.typography import FontContractError, discover_fonts

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (
            "sans",
            {
                "text": "Latin Modern Sans",
                "math": "Latin Modern Sans",
                "mono": "Maple Mono",
            },
        ),
        (
            "serif",
            {
                "text": "XCharter",
                "math": "XCharter Math",
                "mono": "Maple Mono",
            },
        ),
    ],
)
def test_font_discovery_uses_only_latin_math_and_mono_roles(
    mode: str, expected: dict[str, str]
) -> None:
    fonts = discover_fonts(mode=mode)

    assert {role: font.family for role, font in fonts.items()} == expected
    assert all(Path(font.path).is_file() for font in fonts.values())


def test_sans_mode_maps_all_mathtext_roles_to_latin_modern_sans() -> None:
    from axiomfig.config import build_rcparams

    params = build_rcparams(load_contracts(ROOT / "styles"), typography="sans")

    assert params["mathtext.fontset"] == "custom"
    assert params["mathtext.rm"] == "Latin Modern Sans"
    assert params["mathtext.it"] == "Latin Modern Sans"
    assert params["mathtext.bf"] == "Latin Modern Sans"


def test_font_metadata_declares_optional_commercial_system_fonts_unbundled() -> None:
    contracts = load_contracts(ROOT / "styles")
    optional = contracts.fonts["optional_system_fonts"]

    assert {entry["family"] for entry in optional.values()} == {
        "Arial",
        "Times New Roman",
        "SimSun",
        "Yu Gothic",
    }
    assert all(entry["bundled"] is False for entry in optional.values())
    assert all(entry["bundled"] is True for entry in contracts.fonts["families"].values())
    assert optional["arial"]["proprietary"] is True
    assert optional["times-new-roman"]["proprietary"] is True
    assert optional["arial"]["source"] == "system"
    assert optional["times-new-roman"]["source"] == "system"


def test_open_font_metadata_preserves_verified_license_attribution() -> None:
    contracts = load_contracts(ROOT / "styles")

    for entry in contracts.fonts["families"].values():
        assert entry["source"].startswith("https://")
        assert entry["license"]
        assert entry["license_url"].startswith("https://")
        assert entry["copyright"]


def test_bundled_font_assets_and_attributions_exist() -> None:
    contracts = load_contracts(ROOT / "styles")
    font_root = ROOT / "fonts"

    for entry in contracts.fonts["families"].values():
        assert entry["bundled"] is True
        for filename in entry["filenames"].values():
            assert (font_root / filename).is_file(), filename
        assert (font_root / "licenses" / entry["attribution_file"]).is_file()
        assert (font_root / "licenses" / entry["license_file"]).is_file()

    ofl = (font_root / "licenses" / "OFL-1.1.txt").read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in ofl


def test_font_discovery_fails_instead_of_using_fallback() -> None:
    from axiomfig.typography import font_properties

    with pytest.raises(FontContractError, match="unavailable"):
        font_properties("Definitely Missing Font")


def test_font_discovery_does_not_mutate_global_rcparams() -> None:
    before = {key: list(mpl.rcParams[key]) for key in ("font.sans-serif", "font.serif")}

    discover_fonts("sans")
    discover_fonts("serif")

    assert {key: list(mpl.rcParams[key]) for key in before} == before


def test_cjk_roles_are_not_part_of_the_active_default_contract() -> None:
    from axiomfig.typography import font_properties

    assert set(discover_fonts("sans")) == {"text", "math", "mono"}
    with pytest.raises(ValueError, match="unsupported font role"):
        font_properties("zh", mode="sans", role=True)
