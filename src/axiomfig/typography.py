from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from matplotlib import font_manager


class FontContractError(RuntimeError):
    """Raised when an exact AxiomFig font cannot be resolved."""


@dataclass(frozen=True)
class ResolvedFont:
    family: str
    path: str
    matplotlib_family: str


FONT_CONTRACT = {
    "latin": "Latin Modern Sans",
    "math": "Latin Modern Math",
    "chinese": "Noto Sans CJK SC",
    "japanese": "Noto Sans CJK JP",
}

_FILE_CONTRACT = {
    "Latin Modern Sans": ("lmsans10-regular.otf", "LMSans10"),
    "Latin Modern Math": ("latinmodern-math.otf", "Latin Modern Math"),
}

_FILE_VARIANTS = {
    "Latin Modern Sans": (
        "lmsans10-regular.otf",
        "lmsans10-bold.otf",
        "lmsans10-oblique.otf",
        "lmsans10-boldoblique.otf",
    ),
    "Latin Modern Math": ("latinmodern-math.otf",),
}


def _font_search_roots() -> tuple[Path, ...]:
    home = Path.home()
    return (
        home / "Library" / "Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    )


def _resolve_by_file(display_name: str) -> ResolvedFont:
    filename, expected_family = _FILE_CONTRACT[display_name]
    candidates = [root / filename for root in _font_search_roots()]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        locations = ", ".join(str(candidate) for candidate in candidates)
        raise FontContractError(f"Required font {display_name!r} not found at: {locations}")
    for variant in _FILE_VARIANTS[display_name]:
        variant_path = path.parent / variant
        if not variant_path.is_file():
            raise FontContractError(f"Required font variant is missing: {variant_path}")
        font_manager.fontManager.addfont(variant_path)
    actual_family = font_manager.FontProperties(fname=path).get_name()
    if actual_family != expected_family:
        raise FontContractError(
            f"Font file {path} resolved as {actual_family!r}, expected {expected_family!r}"
        )
    return ResolvedFont(display_name, str(path), actual_family)


def _resolve_by_family(display_name: str) -> ResolvedFont:
    try:
        path = font_manager.findfont(
            font_manager.FontProperties(family=[display_name]), fallback_to_default=False
        )
    except ValueError as exc:
        raise FontContractError(
            f"Required font {display_name!r} is unavailable; implicit fallback is disabled"
        ) from exc
    actual_family = font_manager.FontProperties(fname=path).get_name()
    if actual_family != display_name:
        raise FontContractError(
            f"Required font {display_name!r} resolved as {actual_family!r}; fallback is disabled"
        )
    return ResolvedFont(display_name, path, actual_family)


def discover_fonts(overrides: Mapping[str, str] | None = None) -> dict[str, ResolvedFont]:
    contract = dict(FONT_CONTRACT)
    if overrides:
        contract.update(overrides)

    resolved: dict[str, ResolvedFont] = {}
    for role, family in contract.items():
        if family in _FILE_CONTRACT:
            resolved[role] = _resolve_by_file(family)
        else:
            resolved[role] = _resolve_by_family(family)
    return resolved


def font_for_language(language: str) -> font_manager.FontProperties:
    role_by_language = {"en": "latin", "zh": "chinese", "ja": "japanese", "math": "math"}
    try:
        role = role_by_language[language]
    except KeyError as exc:
        raise ValueError(f"Unsupported language code: {language}") from exc
    font = discover_fonts()[role]
    return font_manager.FontProperties(fname=font.path)
