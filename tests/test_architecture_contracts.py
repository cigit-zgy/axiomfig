from __future__ import annotations

import ast
import re
from dataclasses import fields
from importlib.util import resolve_name
from pathlib import Path

from axiomfig.intent import FORBIDDEN_VISUAL_FIELDS, FigureIntent
from axiomfig.structured_io import load_yaml
from axiomfig.templates import TEMPLATE_BUILDERS
from axiomfig.templates.registry import public_template_specs, validate_registry

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/axiomfig"
RUNTIME_CORE = tuple(path.name for path in PACKAGE.glob("*.py") if path.name != "__init__.py")
PUBLIC_FAMILIES = {spec.family for spec in public_template_specs()}


def _imports(path: Path, *, package: str | None = None) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                parent = package or ".".join(path.relative_to(ROOT / "src").parts[:-1])
                module = resolve_name("." * node.level + module, parent)
            names.append(module)
            names.extend(f"{module}.{alias.name}" for alias in node.names)
    return tuple(names)


def test_import_audit_resolves_relative_and_from_import_aliases(tmp_path: Path) -> None:
    source = tmp_path / "builders.py"
    source.write_text(
        "from ..scatter import builders\n"
        "from .. import scatter\n"
        "from axiomfig.templates import scatter\n"
        "from . import geometry\n",
        encoding="utf-8",
    )
    imports = _imports(source, package="axiomfig.templates.bar")

    assert imports.count("axiomfig.templates.scatter") == 3
    assert "axiomfig.templates.scatter.builders" in imports
    assert "axiomfig.templates.bar.geometry" in imports


def test_production_does_not_import_evidence_or_repository_layers() -> None:
    """Catch production depending on test, script, Gallery, report, or example code."""
    forbidden = ("tests", "scripts", "gallery", "reports", "examples", "design", "00_archive")
    violations = {
        path.relative_to(ROOT).as_posix(): name
        for path in PACKAGE.rglob("*.py")
        for name in _imports(path)
        if name in forbidden or name.startswith(tuple(f"{item}." for item in forbidden))
    }

    assert violations == {}


def _frontmatter(path: Path) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    assert source.startswith("---\n"), path
    metadata = load_yaml(source[4:].split("\n---\n", maxsplit=1)[0], source=str(path))
    assert isinstance(metadata, dict), path
    return metadata


def test_project_authority_routes_to_current_owners() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for owner in (
        "design/",
        "SKILL.md",
        "references/",
        "src/axiomfig/",
        "tests/",
        "gallery/",
        "reports/chatgpt/",
        "reports/codex/",
        "reports/concept/",
        "reports/handoff/",
        "00_archive/",
    ):
        assert owner in agents
    assert re.search(r"cigit-zgy/agent-collaboration@[0-9a-f]{40}", agents)
    for path in (*PACKAGE.rglob("*.py"), *(ROOT / "scripts").glob("*.py")):
        assert "00_archive" not in path.read_text(encoding="utf-8"), path


def test_living_design_is_one_current_metadata_backed_set() -> None:
    design = ROOT / "design"
    readme = (design / "README.md").read_text(encoding="utf-8")
    mapped = re.findall(r"^\| `([^`]+)` \| `([^`]+\.md)` \|", readme, flags=re.MULTILINE)
    topics = tuple(path for path in design.iterdir() if path.name != "README.md")
    assert mapped and len(mapped) == len(set(mapped))
    assert {name for _, name in mapped} == {path.name for path in topics}
    identities = []
    for path in topics:
        assert path.is_file() and re.fullmatch(r"\d{2}_[a-z][a-z0-9_]*\.md", path.name)
        assert not re.search(r"_(?:old|backup|draft|v\d+|\d{6,})(?:_|\.)", path.name)
        metadata = _frontmatter(path)
        assert metadata["status"] == "active"
        assert metadata["role"] == "design_authority"
        assert set(metadata) <= {
            "design_id",
            "title",
            "status",
            "role",
            "summary",
            "operational_projection",
        }
        assert all(metadata.get(field) for field in ("design_id", "title", "summary"))
        identities.append(metadata["design_id"])
        assert (metadata["design_id"], path.name) in mapped
        for projection in metadata.get("operational_projection", []):
            assert any(ROOT.glob(projection)), (path, projection)
    assert len(identities) == len(set(identities))
    assert not any(re.match(r"design[_-]", path.name) for path in ROOT.iterdir())


def test_active_reports_are_flat_canonical_artifacts() -> None:
    families = {
        "chatgpt": "chatgpt_task",
        "codex": "codex_report",
        "concept": "project_concept",
        "handoff": "conversation_handoff",
    }
    for family in (ROOT / "reports").iterdir():
        assert family.is_dir() and family.name in families, family
        for path in family.iterdir():
            assert path.is_file() and re.fullmatch(
                rf"\d{{6}}_{family.name}_\d{{2}}\.md", path.name
            ), path
            metadata = _frontmatter(path)
            assert metadata["artifact_type"] == families[family.name]
            assert metadata["artifact_id"] == path.stem
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(metadata["date"]))
            assert all(
                metadata.get(key) for key in ("title", "project", "repository", "status", "summary")
            )


def test_generic_runtime_does_not_import_concrete_template_families() -> None:
    """Catch a generic runtime module acquiring scientific-family knowledge."""
    violations = {
        name: imported
        for name in RUNTIME_CORE
        for imported in _imports(PACKAGE / name)
        if any(imported.startswith(f"axiomfig.templates.{family}") for family in PUBLIC_FAMILIES)
    }

    assert violations == {}


def test_generic_runtime_does_not_own_mantel_family_logic() -> None:
    """Keep the concrete Mantel contract and helpers inside its family package."""
    violations = {
        name
        for name in ("config.py", "style.py")
        if "mantel" in (PACKAGE / name).read_text(encoding="utf-8").lower()
    }

    assert violations == set()


def test_public_scientific_families_do_not_import_each_other() -> None:
    """Catch one family reusing another family's private adapter or builder."""
    violations: list[tuple[str, str]] = []
    for family in sorted(PUBLIC_FAMILIES):
        for path in (PACKAGE / "templates" / family).rglob("*.py"):
            for imported in _imports(path):
                for other in PUBLIC_FAMILIES - {family}:
                    if imported.startswith(f"axiomfig.templates.{other}"):
                        violations.append((path.relative_to(ROOT).as_posix(), imported))

    assert violations == []


def test_figure_intent_remains_the_single_compact_public_schema() -> None:
    """Catch a second visual intent schema or low-level fields entering Figure Intent."""
    assert [field.name for field in fields(FigureIntent)] == [
        "template_id",
        "data",
        "geometry",
        "typography",
        "semantics",
    ]
    assert {
        "font_size",
        "linewidth",
        "tick_length",
        "legend_x",
        "bar_width",
        "panel_offset",
        "subplot_wspace",
        "colorbar_width",
    } <= FORBIDDEN_VISUAL_FIELDS

    forbidden_schema_names = {"ElementIntent", "RenderIntent", "VisualIntent", "PlotSpec"}
    defined = {
        node.name
        for path in PACKAGE.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert defined.isdisjoint(forbidden_schema_names)


def test_registry_contract_and_builder_binding_remain_consistent() -> None:
    """Catch duplicated identity drifting away from the executable binding."""
    specs = validate_registry(TEMPLATE_BUILDERS)

    assert len([spec for spec in specs if spec.public]) == len(public_template_specs())
    assert len(TEMPLATE_BUILDERS) == len(specs)
