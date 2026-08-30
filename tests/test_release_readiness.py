from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_project_metadata_declares_v1_and_public_repository() -> None:
    document = __import__("tomllib").loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert document["project"]["version"] == "1.1.0"
    assert document["project"]["license"] == "MIT"
    assert document["project"]["urls"]["Repository"].endswith("/axiomfig-skill")
    assert "dev" in document["project"]["optional-dependencies"]
    assert "axiomfig-intent" in document["project"]["scripts"]


def test_ci_is_least_privilege_and_pins_third_party_actions() -> None:
    path = ROOT / ".github/workflows/ci.yml"
    source = path.read_text(encoding="utf-8")
    document = yaml.load(source, Loader=yaml.BaseLoader)
    uses = re.findall(r"uses:\s*([^\s#]+)", source)

    assert document["permissions"] == {"contents": "read"}
    assert 'python -m pytest -q -m "not e2e"' in source
    assert "tests/test_external_data_surface.py" in source
    assert "python scripts/validate_skill.py" in source
    assert uses
    assert all(re.search(r"@[0-9a-f]{40}$", value) for value in uses)


def test_release_support_files_exist_and_no_production_local_paths() -> None:
    for name in (
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".editorconfig",
        ".github/dependabot.yml",
    ):
        assert (ROOT / name).is_file()

    production = [ROOT / "src", ROOT / "scripts", ROOT / "README.md", ROOT / "SKILL.md"]
    matches = []
    local_prefix = "/Users/" + "wenv/"
    for target in production:
        paths = target.rglob("*") if target.is_dir() else (target,)
        for path in paths:
            if path.suffix not in {".py", ".md", ".yaml", ".yml", ".toml", ".sh"}:
                continue
            if path.is_file() and local_prefix in path.read_text(encoding="utf-8", errors="ignore"):
                matches.append(path)
    assert not matches


def test_v1_architecture_has_no_development_or_parallel_runtime_layers() -> None:
    assert not (ROOT / "docs").exists()
    assert not (ROOT / "evaluation").exists()
    assert not (ROOT / "styles").exists()
    assert not (ROOT / "src/axiomfig/data_adapters").exists()
    obsolete_modules = (
        "anatomy.py",
        "colors.py",
        "contracts.py",
        "evaluation.py",
        "template_helpers.py",
    )
    for obsolete in obsolete_modules:
        assert not (ROOT / "src/axiomfig" / obsolete).exists()
    for wrapper in ("build_gallery.py", "render.py", "render_intent.py", "validate.py"):
        assert not (ROOT / "scripts" / wrapper).exists()
