"""Template-owned bindings consumed by the generic formal Gallery builder."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateGalleryCase:
    """One non-canonical formal example owned by its template family."""

    example_id: str
    geometry: str
    output_id: str
    values: Callable[[], dict[str, object]]


__all__ = ["TemplateGalleryCase"]
