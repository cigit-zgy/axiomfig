from pathlib import Path

import matplotlib as mpl
import pytest

from axiomfig import typography
from axiomfig.template_helpers import add_language_text
from axiomfig.typography import FontContractError, discover_fonts, font_for_language


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (
            "sans",
            {
                "latin": "Latin Modern Sans",
                "math": "Fira Math",
                "chinese": "Noto Sans CJK SC",
                "japanese": "Noto Sans CJK JP",
                "mono": "Maple Mono",
            },
        ),
        (
            "serif",
            {
                "latin": "Latin Modern Roman",
                "math": "Latin Modern Math",
                "chinese": "Noto Serif CJK SC",
                "japanese": "Noto Serif CJK JP",
                "mono": "Maple Mono",
            },
        ),
    ],
)
def test_font_discovery_resolves_exact_mode_contract(mode: str, expected: dict[str, str]) -> None:
    fonts = discover_fonts(mode=mode)

    assert {role: font.family for role, font in fonts.items()} == expected
    assert {role: font.matplotlib_family for role, font in fonts.items()} == {
        "latin": "LMSans10" if mode == "sans" else "LMRoman10",
        "math": expected["math"],
        "chinese": expected["chinese"],
        "japanese": expected["japanese"],
        "mono": "Maple Mono",
    }
    assert all(Path(font.path).is_file() for font in fonts.values())


def test_font_discovery_fails_instead_of_falling_back() -> None:
    with pytest.raises(FontContractError, match="Definitely Missing Font"):
        discover_fonts({"latin": "Definitely Missing Font"})


def test_font_discovery_rejects_cross_family_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    fallback_path = discover_fonts(mode="sans")["latin"].path

    monkeypatch.setattr(typography.font_manager, "findfont", lambda *args, **kwargs: fallback_path)

    with pytest.raises(FontContractError, match="expected 'Required Test Family'"):
        discover_fonts({"latin": "Required Test Family"})


def test_font_discovery_does_not_mutate_rcparams() -> None:
    keys = ("font.family", "font.sans-serif", "font.serif", "mathtext.rm", "mathtext.tt")
    before = {key: mpl.rcParams[key] for key in keys}

    discover_fonts(mode="sans")
    discover_fonts(mode="serif")

    assert {key: mpl.rcParams[key] for key in keys} == before


@pytest.mark.parametrize(
    ("mode", "language", "expected"),
    [
        ("sans", "zh", "Noto Sans CJK SC"),
        ("sans", "ja", "Noto Sans CJK JP"),
        ("sans", "math", "Fira Math"),
        ("sans", "mono", "Maple Mono"),
        ("serif", "zh", "Noto Serif CJK SC"),
        ("serif", "ja", "Noto Serif CJK JP"),
        ("serif", "math", "Latin Modern Math"),
        ("serif", "mono", "Maple Mono"),
    ],
)
def test_language_font_mapping_uses_the_selected_mode(
    mode: str, language: str, expected: str
) -> None:
    assert font_for_language(language, mode=mode).get_name() == expected


@pytest.mark.parametrize("weight", ["light", "medium", 500])
def test_latin_weights_without_an_exact_file_hard_fail(weight: str | int) -> None:
    with pytest.raises(FontContractError, match="Unsupported Latin weight"):
        font_for_language("en", weight=weight)


@pytest.mark.parametrize("mode", ["sans", "serif"])
@pytest.mark.parametrize("language", ["zh", "ja"])
def test_explicit_cjk_helper_rejects_nonregular_weight(mode: str, language: str) -> None:
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots()
    with pytest.raises(FontContractError, match="refusing regular fallback"):
        add_language_text(axis, 0.5, 0.5, "硝化效率", language, mode=mode, fontweight="bold")
    plt.close(figure)
