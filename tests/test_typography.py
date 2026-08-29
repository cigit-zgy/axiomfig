from pathlib import Path

import pytest

from axiomfig.typography import FontContractError, discover_fonts, font_for_language


def test_font_discovery_resolves_exact_contract() -> None:
    fonts = discover_fonts()

    assert fonts["latin"].family == "Latin Modern Sans"
    assert fonts["math"].family == "Latin Modern Math"
    assert fonts["chinese"].family == "Noto Sans CJK SC"
    assert fonts["japanese"].family == "Noto Sans CJK JP"
    assert all(Path(font.path).is_file() for font in fonts.values())


def test_font_discovery_fails_instead_of_falling_back() -> None:
    with pytest.raises(FontContractError, match="Definitely Missing Font"):
        discover_fonts({"latin": "Definitely Missing Font"})


def test_language_font_mapping_distinguishes_chinese_and_japanese() -> None:
    assert font_for_language("zh").get_name() == "Noto Sans CJK SC"
    assert font_for_language("ja").get_name() == "Noto Sans CJK JP"
