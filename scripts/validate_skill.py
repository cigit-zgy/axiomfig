#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import yaml


def validate_skill(path: Path) -> None:
    source = Path(path).read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        frontmatter, body = source[4:].split("\n---\n", maxsplit=1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter must end with ---") from exc
    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict) or set(metadata) != {"name", "description"}:
        raise ValueError("SKILL.md frontmatter requires only name and description")
    name = metadata["name"]
    description = metadata["description"]
    if not isinstance(name, str) or re.fullmatch(r"[a-z0-9-]{1,64}", name) is None:
        raise ValueError("Skill name must be 1-64 lowercase letters, digits, or hyphens")
    if (
        not isinstance(description, str)
        or not description.strip()
        or len(description) > 1024
        or "<" in description
        or ">" in description
    ):
        raise ValueError("Skill description is empty, too long, or contains angle brackets")
    if not body.strip():
        raise ValueError("SKILL.md body must not be empty")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    validate_skill(root / "SKILL.md")
    print("PASS SKILL.md")
