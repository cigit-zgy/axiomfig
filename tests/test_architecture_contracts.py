from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from axiomfig.intent import FORBIDDEN_VISUAL_FIELDS, FigureIntent
from axiomfig.templates import TEMPLATE_BUILDERS
from axiomfig.templates.registry import public_template_specs, validate_registry

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/axiomfig"
RUNTIME_CORE = (
    "config.py",
    "style.py",
    "layout.py",
    "ornaments.py",
    "typography.py",
    "rendering.py",
    "validation.py",
    "latex.py",
)
PUBLIC_FAMILIES = {spec.family for spec in public_template_specs()}


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


def test_production_does_not_import_evidence_or_repository_layers() -> None:
    """Catch production depending on test, script, Gallery, report, or example code."""
    forbidden = ("tests", "scripts", "gallery", "reports", "examples")
    violations = {
        path.relative_to(ROOT).as_posix(): name
        for path in PACKAGE.rglob("*.py")
        for name in _imports(path)
        if name in forbidden or name.startswith(tuple(f"{item}." for item in forbidden))
    }

    assert violations == {}


def test_generic_runtime_does_not_import_concrete_template_families() -> None:
    """Catch a generic runtime module acquiring scientific-family knowledge."""
    violations = {
        name: imported
        for name in RUNTIME_CORE
        for imported in _imports(PACKAGE / name)
        if any(imported.startswith(f"axiomfig.templates.{family}") for family in PUBLIC_FAMILIES)
    }

    assert violations == {}


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

    assert len([spec for spec in specs if spec.public]) == 55
    assert len(TEMPLATE_BUILDERS) == len(specs) == 59
