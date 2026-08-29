import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt

from axiomfig.styles import StyleSelection, compose_styles
from axiomfig.typography import discover_fonts, font_for_language


def test_sans_and_serif_styles_select_their_complete_text_and_math_families() -> None:
    sans = compose_styles(StyleSelection(typography="sans").paths()).params
    serif = compose_styles(StyleSelection(typography="serif").paths()).params

    assert sans["font.family"] == ["sans-serif"]
    assert sans["font.sans-serif"] == ["LMSans10", "Noto Sans CJK SC", "Noto Sans CJK JP"]
    assert sans["mathtext.rm"] == "Fira Math"
    assert sans["mathtext.tt"] == "Maple Mono"

    assert serif["font.family"] == ["serif"]
    assert serif["font.serif"] == ["LMRoman10", "Noto Serif CJK SC", "Noto Serif CJK JP"]
    assert serif["mathtext.rm"] == "Latin Modern Math"
    assert serif["mathtext.tt"] == "Maple Mono"

    assert mpl.rcParams["font.family"] != serif["font.family"]


def test_cjk_artists_use_explicit_selected_noto_family_without_glyph_warnings() -> None:
    for mode in ("sans", "serif"):
        discover_fonts(mode=mode)
        params = compose_styles(StyleSelection(typography=mode).paths()).params
        with mpl.rc_context(rc=params), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            figure, axis = plt.subplots()
            axis.plot([0, 1], [0, 1], label="硝化效率")
            axis.set(title="硝化效率", xlabel="时间", ylabel="效率")
            legend = axis.legend()
            properties = font_for_language("zh", mode=mode)
            for text in (axis.title, axis.xaxis.label, axis.yaxis.label, *legend.get_texts()):
                text.set_fontproperties(properties)
            figure.canvas.draw()
            plt.close(figure)
        assert not [warning for warning in caught if "Glyph" in str(warning.message)]
