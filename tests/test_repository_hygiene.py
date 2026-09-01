from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

from axiomfig.structured_io import load_yaml

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TEXT_ROOTS = (
    ROOT / "src",
    ROOT / "scripts",
    ROOT / "examples",
    ROOT / "references",
    ROOT / "README.md",
    ROOT / "SKILL.md",
    ROOT / "CONTRIBUTING.md",
)
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".csv", ".json", ".sh"}
INTENTIONAL_LARGE_PREFIXES = ("gallery/", "src/axiomfig/resources/fonts/")


def _tracked_paths() -> tuple[Path, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return tuple(ROOT / name.decode() for name in completed.stdout.split(b"\0") if name)


def _public_text_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for root in PUBLIC_TEXT_ROOTS:
        candidates = root.rglob("*") if root.is_dir() else (root,)
        files.extend(path for path in candidates if path.is_file() and path.suffix in TEXT_SUFFIXES)
    return tuple(files)


def test_public_and_production_text_contains_no_local_absolute_user_paths() -> None:
    """Catch release-facing code/docs depending on a maintainer's home directory."""
    pattern = re.compile(r"/(?:Users|home)/[^/\s]+/")
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in _public_text_files()
        if pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    ]

    assert violations == []


def test_tracked_tree_contains_no_generated_environment_or_private_data_paths() -> None:
    """Catch caches, build products, environments, and private-data-looking paths."""
    forbidden_parts = {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".hypothesis",
        ".venv",
        "venv",
        "site-packages",
        "egg-info",
        "private_data",
        "client_data",
    }
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in _tracked_paths()
        if forbidden_parts.intersection(path.relative_to(ROOT).parts)
    ]

    assert violations == []


def test_unexpected_large_tracked_files_are_rejected() -> None:
    """Catch unexplained release payloads while allowing fonts and Gallery evidence."""
    threshold = 5 * 1024 * 1024
    violations = []
    for path in _tracked_paths():
        relative = path.relative_to(ROOT).as_posix()
        if path.stat().st_size <= threshold or relative.startswith(INTENTIONAL_LARGE_PREFIXES):
            continue
        violations.append((relative, path.stat().st_size))

    assert violations == []


def test_benchmark_outputs_do_not_enter_production_package() -> None:
    """Catch evaluation results or gold answers leaking into the installed runtime."""
    forbidden_names = {"predictions.jsonl", "agent_protocol_cases.yaml", "agent_scoring.py"}
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/axiomfig").rglob("*")
        if path.is_file() and path.name in forbidden_names
    ]

    assert violations == []


def test_all_tracked_project_yaml_has_unambiguous_mapping_keys() -> None:
    yaml_paths = [path for path in _tracked_paths() if path.suffix.lower() in {".yaml", ".yml"}]
    for path in yaml_paths:
        load_yaml(path.read_text(encoding="utf-8"), source=path.as_posix())


def test_core_public_markdown_has_no_broken_local_links() -> None:
    markdown_files = tuple(
        path
        for root in (ROOT / "README.md", ROOT / "SKILL.md", ROOT / "references")
        for path in (root.rglob("*.md") if root.is_dir() else (root,))
    )
    broken: list[tuple[str, str]] = []
    for path in markdown_files:
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            selected = target.strip("<>").split("#", maxsplit=1)[0]
            if not selected or re.match(r"^(?:https?://|mailto:)", selected):
                continue
            resolved = (path.parent / unquote(selected)).resolve()
            if not resolved.exists():
                broken.append((path.relative_to(ROOT).as_posix(), target))
    assert broken == []


def test_public_tree_contains_no_private_key_or_live_token_shapes() -> None:
    patterns = (
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"\bgh[opsu]_[A-Za-z0-9]{30,}\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    )
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in _public_text_files()
        if any(
            pattern.search(path.read_text(encoding="utf-8", errors="replace"))
            for pattern in patterns
        )
    ]
    assert violations == []
