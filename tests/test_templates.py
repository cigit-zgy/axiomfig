from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.figure
import matplotlib.pyplot as plt

from axiomfig.templates import TEMPLATE_BUILDERS, build_template
from axiomfig.templates.registry import (
    load_family_contract,
    load_template_registry,
    public_template_specs,
)

ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC_FAMILIES = (
    "line",
    "scatter",
    "bar",
    "distribution",
    "heatmap",
    "estimation",
    "diagnostics",
    "association",
    "field",
)
EXPECTED_PUBLIC_COUNTS = {
    "line": 5,
    "scatter": 4,
    "bar": 4,
    "distribution": 6,
    "heatmap": 4,
    "estimation": 2,
    "diagnostics": 6,
    "association": 1,
    "field": 1,
}


def test_registry_has_canonical_taxonomy_and_separate_layouts() -> None:
    specs = load_template_registry()
    public = public_template_specs()

    assert tuple(dict.fromkeys(spec.family for spec in public)) == SCIENTIFIC_FAMILIES
    assert {spec.family for spec in specs if not spec.public} == {"layouts"}
    assert len(public) == 33
    assert len(specs) == 37
    assert {
        family: sum(spec.family == family for spec in public) for family in SCIENTIFIC_FAMILIES
    } == EXPECTED_PUBLIC_COUNTS


def test_registry_ids_contracts_and_builders_agree_exactly() -> None:
    specs = load_template_registry()
    ids = [spec.template_id for spec in specs]

    assert len(ids) == len(set(ids))
    assert set(ids) == set(TEMPLATE_BUILDERS)
    for family in (*SCIENTIFIC_FAMILIES, "layouts"):
        contract = load_family_contract(family)
        variants = set(contract["variants"])
        registered = {spec.variant for spec in specs if spec.family == family}
        built = {
            template_id.split("/", maxsplit=1)[1]
            for template_id in TEMPLATE_BUILDERS
            if template_id.startswith(f"{family}/")
        }
        assert contract["family"] == family
        assert variants == registered == built


def test_mandatory_mantel_field_and_explicit_scientific_semantics() -> None:
    public_ids = {spec.template_id for spec in public_template_specs()}
    mantel = load_family_contract("association")["variants"]["mantel"]
    correlation = load_family_contract("heatmap")["variants"]["correlation"]
    forest = load_family_contract("estimation")["variants"]["forest"]

    assert {"association/mantel", "field/contour"} <= public_ids
    assert {"correlation_matrix", "mantel_links", "significance"} <= set(mantel["required"])
    assert "center" in correlation["required"]
    assert "uncertainty_type" in forest["required"]


def test_old_coarse_template_modules_are_removed() -> None:
    template_root = ROOT / "src/axiomfig/templates"
    assert not {
        template_root / "curves.py",
        template_root / "distributions.py",
        template_root / "surfaces.py",
        template_root / "panels.py",
    } & set(template_root.glob("*.py"))


def test_registered_template_builders_return_figures() -> None:
    for name in sorted(TEMPLATE_BUILDERS):
        figure = build_template(name)
        assert isinstance(figure, matplotlib.figure.Figure), name
        assert figure.axes, name
        plt.close(figure)


def test_templates_do_not_mutate_contract_rcparams() -> None:
    keys = ("font.size", "font.family", "figure.figsize", "lines.linewidth", "axes.linewidth")
    for name in sorted(TEMPLATE_BUILDERS):
        before = {key: mpl.rcParams[key] for key in keys}
        figure = build_template(name)
        assert {key: mpl.rcParams[key] for key in keys} == before, name
        plt.close(figure)


def test_mantel_significance_legend_uses_bundled_ascii_glyphs() -> None:
    figure = build_template("association/mantel")
    labels = [
        text.get_text()
        for axis in figure.axes
        if axis.get_legend() is not None
        for text in axis.get_legend().get_texts()
    ]

    assert labels == ["p < 0.05", "not significant"]
    plt.close(figure)
