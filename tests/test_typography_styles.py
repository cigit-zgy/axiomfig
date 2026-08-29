from pathlib import Path

import matplotlib as mpl

from axiomfig.styles import StyleSelection, compose_styles


def test_sans_and_serif_styles_select_their_complete_text_and_math_families() -> None:
    root = Path(__file__).resolve().parents[1] / "styles"
    sans = compose_styles(StyleSelection(typography="sans").paths(root)).params
    serif = compose_styles(StyleSelection(typography="serif").paths(root)).params

    assert sans["font.family"] == ["LMSans10"]
    assert sans["font.sans-serif"] == ["LMSans10", "Noto Sans CJK SC", "Noto Sans CJK JP"]
    assert sans["mathtext.rm"] == "Fira Math"
    assert sans["mathtext.tt"] == "Maple Mono"

    assert serif["font.family"] == ["LMRoman10"]
    assert serif["font.serif"] == ["LMRoman10", "Noto Serif CJK SC", "Noto Serif CJK JP"]
    assert serif["mathtext.rm"] == "Latin Modern Math"
    assert serif["mathtext.tt"] == "Maple Mono"

    assert mpl.rcParams["font.family"] != serif["font.family"]
