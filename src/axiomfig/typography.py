from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any

from fontTools.ttLib import TTFont
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from axiomfig.config import Contracts, load_contracts


class FontContractError(RuntimeError):
    """Raised when an exact AxiomFig font cannot be resolved."""


@dataclass(frozen=True)
class ResolvedFont:
    family: str
    path: str
    matplotlib_family: str


def _search_roots(contracts: Contracts) -> tuple[Path, ...]:
    bundle = PurePosixPath(str(contracts.fonts["bundle_subdir"]))
    resource = files("axiomfig").joinpath(*bundle.parts)
    bundled_roots = (Path(str(resource)),)
    system_roots = tuple(Path(value).expanduser() for value in contracts.fonts["search_roots"])
    return bundled_roots + system_roots


def _name_value(font: TTFont, name_id: int) -> str:
    for name in font["name"].names:
        if name.nameID == name_id:
            try:
                value = name.toUnicode()
            except UnicodeError:
                continue
            if value:
                return value
    raise FontContractError(f"font has no readable name table entry {name_id}")


def _register(path: Path, expected_family: str) -> str:
    try:
        font = TTFont(path, lazy=True)
        try:
            actual_family = _name_value(font, 1)
        finally:
            font.close()
    except FontContractError:
        raise
    except Exception as exc:
        raise FontContractError(f"cannot inspect font file {path}: {exc}") from exc
    if actual_family != expected_family:
        raise FontContractError(
            f"font file {path} has family {actual_family!r}, expected {expected_family!r}"
        )
    font_manager.fontManager.addfont(path)
    return str(path.resolve())


def _resolve_family(spec: Mapping[str, Any], contracts: Contracts) -> ResolvedFont:
    filenames = spec["filenames"]
    for filename in filenames.values():
        candidate = next(
            (
                root / str(filename)
                for root in _search_roots(contracts)
                if (root / str(filename)).is_file()
            ),
            None,
        )
        if candidate is None:
            raise FontContractError(f"required font {spec['family']!r} is unavailable: {filename}")
        _register(candidate, str(spec["matplotlib_family"]))
    regular = str(filenames["regular"])
    path = next(root / regular for root in _search_roots(contracts) if (root / regular).is_file())
    return ResolvedFont(str(spec["family"]), str(path.resolve()), str(spec["matplotlib_family"]))


def discover_fonts(
    mode: str = "sans", *, contracts: Contracts | None = None
) -> dict[str, ResolvedFont]:
    selected = contracts or load_contracts()
    modes = selected.fonts["modes"]
    if mode not in modes:
        raise ValueError(f"unsupported typography mode: {mode}")
    result: dict[str, ResolvedFont] = {}
    for role, family_key in modes[mode].items():
        result[str(role)] = _resolve_family(selected.fonts["families"][family_key], selected)
    return result


def _variant_path(mode: str, weight: str | int | None, style: str | None) -> str:
    contracts = load_contracts()
    family_key = contracts.fonts["modes"][mode]["text"]
    spec = contracts.fonts["families"][family_key]
    normalized = str(weight).lower().replace("-", "").replace(" ", "")
    bold = normalized in {
        "bold",
        "semibold",
        "demibold",
        "demi",
        "extrabold",
        "ultrabold",
        "heavy",
        "black",
        "600",
        "700",
        "800",
        "900",
        "1000",
    }
    regular = normalized in {"none", "normal", "regular", "book", "400"}
    if not (bold or regular):
        raise FontContractError(f"unsupported exact text weight: {weight!r}")
    italic = style in {"italic", "oblique"}
    if style not in {None, "normal", "italic", "oblique"}:
        raise FontContractError(f"unsupported exact text style: {style!r}")
    key = {
        ("regular", False): "regular",
        ("regular", True): "italic",
        ("bold", False): "bold",
        ("bold", True): "bold_italic",
    }[("bold" if bold else "regular", italic)]
    filename = str(spec["filenames"][key])
    path = next(
        (root / filename for root in _search_roots(contracts) if (root / filename).is_file()),
        None,
    )
    if path is None:
        raise FontContractError(f"required font variant is unavailable: {filename}")
    return _register(path, str(spec["matplotlib_family"]))


def font_properties(
    value: str,
    mode: str = "sans",
    *,
    role: bool = False,
    weight: str | int | None = None,
    style: str | None = None,
) -> font_manager.FontProperties:
    if role:
        if value not in {"text", "math", "mono"}:
            raise ValueError(f"unsupported font role: {value}")
        if value == "text":
            return font_manager.FontProperties(fname=_variant_path(mode, weight, style))
        return font_manager.FontProperties(fname=discover_fonts(mode)[value].path)
    try:
        path = font_manager.findfont(
            font_manager.FontProperties(family=[value]), fallback_to_default=False
        )
    except ValueError as exc:
        raise FontContractError(f"required font {value!r} is unavailable") from exc
    return font_manager.FontProperties(fname=path)


def font_for_language(
    language: str,
    mode: str = "sans",
    *,
    weight: str | int | None = None,
    style: str | None = None,
) -> font_manager.FontProperties:
    role = {"en": "text", "math": "math", "mono": "mono"}.get(language)
    if role is None:
        raise ValueError(f"unsupported font role: {language}; CJK typography is deferred")
    return font_properties(role, mode=mode, role=True, weight=weight, style=style)


def add_language_text(
    axis: Axes,
    x: float,
    y: float,
    text: str,
    language: str,
    mode: str = "sans",
    **kwargs: object,
) -> None:
    """Add text with the font contract for an explicit language role."""
    axis.text(x, y, text, fontproperties=font_for_language(language, mode=mode), **kwargs)


_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")


def _text_artists(figure: Figure) -> list[Text]:
    return list({id(artist): artist for artist in figure.findobj(match=Text)}.values())


def apply_figure_typography(figure: Figure, mode: str = "sans") -> Figure:
    """Assign exact Latin text and math families without system fallback."""
    discover_fonts(mode)
    for artist in _text_artists(figure):
        if _CJK.search(artist.get_text()):
            raise FontContractError("CJK typography is deferred in the active AxiomFig contract")
        properties = artist.get_fontproperties()
        if properties.get_file() is None:
            artist.set_fontproperties(
                font_for_language(
                    "en",
                    mode=mode,
                    weight=properties.get_weight(),
                    style=properties.get_style(),
                )
            )
        artist.set_math_fontfamily("custom")
    return figure
