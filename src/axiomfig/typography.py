from __future__ import annotations

import hashlib
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.text import Text


class FontContractError(RuntimeError):
    """Raised when an exact AxiomFig font cannot be resolved."""


@dataclass(frozen=True)
class ResolvedFont:
    family: str
    path: str
    matplotlib_family: str


@dataclass(frozen=True)
class FontSpec:
    display_name: str
    matplotlib_family: str
    filenames: tuple[str, ...]
    variants: tuple[str, ...] = ()


FONT_CONTRACTS = {
    "sans": {
        "latin": "Latin Modern Sans",
        "math": "Fira Math",
        "chinese": "Noto Sans CJK SC",
        "japanese": "Noto Sans CJK JP",
        "mono": "Maple Mono",
    },
    "serif": {
        "latin": "Latin Modern Roman",
        "math": "Latin Modern Math",
        "chinese": "Noto Serif CJK SC",
        "japanese": "Noto Serif CJK JP",
        "mono": "Maple Mono",
    },
}
# Preserve the original default-contract constant for callers that import it.
FONT_CONTRACT = FONT_CONTRACTS["sans"]

FONT_SPECS = {
    "Latin Modern Sans": FontSpec(
        "Latin Modern Sans",
        "LMSans10",
        ("lmsans10-regular.otf",),
        (
            "lmsans10-regular.otf",
            "lmsans10-bold.otf",
            "lmsans10-oblique.otf",
            "lmsans10-boldoblique.otf",
        ),
    ),
    "Latin Modern Roman": FontSpec(
        "Latin Modern Roman",
        "LMRoman10",
        ("lmroman10-regular.otf",),
        (
            "lmroman10-regular.otf",
            "lmroman10-bold.otf",
            "lmroman10-italic.otf",
            "lmroman10-bolditalic.otf",
        ),
    ),
    "Fira Math": FontSpec("Fira Math", "Fira Math", ("FiraMath-Regular.otf",)),
    "Latin Modern Math": FontSpec(
        "Latin Modern Math", "Latin Modern Math", ("latinmodern-math.otf",)
    ),
    "Noto Sans CJK SC": FontSpec(
        "Noto Sans CJK SC", "Noto Sans CJK SC", ("NotoSansCJKsc-Regular.otf", "NotoSansCJK.ttc")
    ),
    "Noto Sans CJK JP": FontSpec(
        "Noto Sans CJK JP", "Noto Sans CJK JP", ("NotoSansCJKjp-Regular.otf", "NotoSansCJK.ttc")
    ),
    "Noto Serif CJK SC": FontSpec(
        "Noto Serif CJK SC", "Noto Serif CJK SC", ("NotoSerifCJKsc-Regular.otf", "NotoSerifCJK.ttc")
    ),
    "Noto Serif CJK JP": FontSpec(
        "Noto Serif CJK JP", "Noto Serif CJK JP", ("NotoSerifCJKjp-Regular.otf", "NotoSerifCJK.ttc")
    ),
    "Maple Mono": FontSpec("Maple Mono", "Maple Mono", ("MapleMono[wght].ttf",)),
}


def _font_search_roots() -> tuple[Path, ...]:
    home = Path.home()
    return (
        home / "Library" / "Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/opt/homebrew/share/fonts"),
    )


def _name_table_family(font: TTFont) -> str:
    return _name_table_value(font, 1, "family")


def _name_table_value(font: TTFont, name_id: int, label: str) -> str:
    names = [name for name in font["name"].names if name.nameID == name_id]
    for name in names:
        try:
            value = name.toUnicode()
        except UnicodeError:
            continue
        if value:
            return value
    raise FontContractError(f"Font has no readable internal {label} name")


def _materialize_collection_face(path: Path, expected_family: str) -> Path:
    collection = TTCollection(path, lazy=True)
    try:
        matching = [
            font
            for font in collection.fonts
            if _name_table_family(font) == expected_family
            and _name_table_value(font, 2, "subfamily") == "Regular"
        ]
        if len(matching) != 1:
            raise FontContractError(
                f"Font collection {path} has no unique {expected_family!r} face; "
                f"found {len(matching)}"
            )
        digest = hashlib.sha256(
            f"{path.resolve()}:{expected_family}:{path.stat().st_mtime_ns}".encode()
        ).hexdigest()[:16]
        target = Path(tempfile.gettempdir()) / "axiomfig-fonts" / f"{digest}.otf"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            matching[0].save(target)
        return target
    finally:
        collection.close()


def _font_file_with_expected_family(path: Path, expected_family: str) -> Path:
    if path.suffix.lower() == ".ttc":
        return _materialize_collection_face(path, expected_family)
    try:
        font = TTFont(path, lazy=True)
        try:
            actual_family = _name_table_family(font)
        finally:
            font.close()
    except FontContractError:
        raise
    except Exception as exc:
        raise FontContractError(f"Cannot inspect font file {path}: {exc}") from exc
    if actual_family != expected_family:
        raise FontContractError(
            f"Font file {path} resolved as {actual_family!r}, expected {expected_family!r}"
        )
    return path


def _register_exact_font(path: Path, expected_family: str) -> str:
    registered_path = _font_file_with_expected_family(path, expected_family)
    font_manager.fontManager.addfont(registered_path)
    actual_family = font_manager.FontProperties(fname=registered_path).get_name()
    if actual_family != expected_family:
        raise FontContractError(
            f"Font file {registered_path} resolved as {actual_family!r}, "
            f"expected {expected_family!r}"
        )
    return str(registered_path)


def _resolve_by_spec(spec: FontSpec) -> ResolvedFont:
    candidates = [root / filename for root in _font_search_roots() for filename in spec.filenames]
    source_path = next((path for path in candidates if path.is_file()), None)
    if source_path is None:
        locations = ", ".join(str(path) for path in candidates)
        raise FontContractError(f"Required font {spec.display_name!r} not found at: {locations}")

    if spec.variants:
        for variant in spec.variants:
            variant_path = source_path.parent / variant
            if not variant_path.is_file():
                raise FontContractError(f"Required font variant is missing: {variant_path}")
            _register_exact_font(variant_path, spec.matplotlib_family)

    path = _register_exact_font(source_path, spec.matplotlib_family)
    return ResolvedFont(spec.display_name, path, spec.matplotlib_family)


def _resolve_override_family(display_name: str) -> ResolvedFont:
    try:
        path = Path(
            font_manager.findfont(
                font_manager.FontProperties(family=[display_name]), fallback_to_default=False
            )
        )
    except ValueError as exc:
        raise FontContractError(
            f"Required font {display_name!r} is unavailable; implicit fallback is disabled"
        ) from exc
    registered_path = _font_file_with_expected_family(path, display_name)
    actual_family = font_manager.FontProperties(fname=registered_path).get_name()
    if actual_family != display_name:
        raise FontContractError(
            f"Required font {display_name!r} resolved as {actual_family!r}; fallback is disabled"
        )
    return ResolvedFont(display_name, str(registered_path), actual_family)


def _contract_for_mode(mode: str) -> dict[str, str]:
    try:
        return dict(FONT_CONTRACTS[mode])
    except KeyError as exc:
        available = ", ".join(sorted(FONT_CONTRACTS))
        raise ValueError(f"Unsupported typography mode {mode!r}; available: {available}") from exc


def discover_fonts(
    mode: str | Mapping[str, str] = "sans", overrides: Mapping[str, str] | None = None
) -> dict[str, ResolvedFont]:
    """Register and return the exact font files required by one typography mode.

    Passing a mapping as the first positional argument preserves the original
    ``discover_fonts({"latin": "..."})`` override API.
    """
    if isinstance(mode, Mapping):
        if overrides is not None:
            raise TypeError("Pass font overrides either positionally or by keyword, not both")
        overrides = mode
        mode = "sans"
    contract = _contract_for_mode(mode)
    if overrides:
        contract.update(overrides)

    resolved: dict[str, ResolvedFont] = {}
    for role, family in contract.items():
        spec = FONT_SPECS.get(family)
        resolved[role] = (
            _resolve_by_spec(spec) if spec is not None else _resolve_override_family(family)
        )
    return resolved


def font_for_language(language: str, mode: str = "sans") -> font_manager.FontProperties:
    role_by_language = {
        "en": "latin",
        "zh": "chinese",
        "ja": "japanese",
        "math": "math",
        "mono": "mono",
    }
    try:
        role = role_by_language[language]
    except KeyError as exc:
        raise ValueError(f"Unsupported language code: {language}") from exc
    font = discover_fonts(mode=mode)[role]
    return font_manager.FontProperties(fname=font.path)


_MATH_SPAN = re.compile(r"\$.*?\$")
_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_JAPANESE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
_LATIN = re.compile(r"[A-Za-z]")


def _language_for_text(text: str) -> str | None:
    plain = _MATH_SPAN.sub("", text)
    has_cjk = bool(_HAN.search(plain) or _JAPANESE.search(plain))
    if has_cjk and _LATIN.search(plain):
        raise FontContractError(
            "Mixed plain scripts require the segmented multilingual helper "
            "(add_language_text) so each run has an exact font family"
        )
    if _JAPANESE.search(plain):
        return "ja"
    if _HAN.search(plain):
        return "zh"
    return "en" if plain else None


def _figure_text_artists(figure: Figure) -> list[Text]:
    artists: list[Text] = list(figure.texts)
    for axis in figure.axes:
        artists.extend((axis.title, axis._left_title, axis._right_title))
        artists.extend((axis.xaxis.label, axis.yaxis.label))
        artists.extend(axis.get_xticklabels(which="both"))
        artists.extend(axis.get_yticklabels(which="both"))
        artists.extend(axis.texts)
        legend = axis.get_legend()
        if legend is not None:
            artists.extend(legend.get_texts())
    return list({id(artist): artist for artist in artists}.values())


def apply_figure_typography(figure: Figure, mode: str = "sans") -> Figure:
    """Assign exact regional fonts to all ordinary figure text before rendering."""
    for artist in _figure_text_artists(figure):
        if artist.get_fontproperties().get_file() is not None:
            continue
        language = _language_for_text(artist.get_text())
        if language is not None:
            artist.set_fontproperties(font_for_language(language, mode=mode))
            artist.set_math_fontfamily("custom")
    return figure
