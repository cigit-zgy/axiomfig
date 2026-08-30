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
    "ordination",
    "association",
    "flow",
    "field",
    "omics",
    "survival",
)
EXPECTED_PUBLIC_COUNTS = {
    "line": 7,
    "scatter": 6,
    "bar": 6,
    "distribution": 8,
    "heatmap": 5,
    "estimation": 3,
    "diagnostics": 8,
    "ordination": 4,
    "association": 2,
    "flow": 1,
    "field": 2,
    "omics": 2,
    "survival": 1,
}


def test_registry_has_canonical_taxonomy_and_separate_layouts() -> None:
    specs = load_template_registry()
    public = public_template_specs()

    assert tuple(dict.fromkeys(spec.family for spec in public)) == SCIENTIFIC_FAMILIES
    assert {spec.family for spec in specs if not spec.public} == {"layouts"}
    assert len(public) == 55
    assert len(specs) == 59
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
    assert {
        "correlation_matrix",
        "labels",
        "links",
    } <= set(mantel["required"])
    assert "center" in correlation["required"]
    assert "uncertainty_type" in forest["required"]


def test_v1_core_template_variants_are_real_and_scientifically_explicit() -> None:
    public_ids = {spec.template_id for spec in public_template_specs()}
    expected = {
        "line/step",
        "line/area",
        "scatter/bubble",
        "scatter/hexbin",
        "bar/normalized_stacked",
        "bar/dot",
        "distribution/strip",
        "distribution/raincloud",
        "heatmap/annotated",
    }

    assert expected <= public_ids
    assert "size" in load_family_contract("scatter")["variants"]["bubble"]["required"]
    assert (
        "normalization" in load_family_contract("bar")["variants"]["normalized_stacked"]["required"]
    )
    assert "annotations" in load_family_contract("heatmap")["variants"]["annotated"]["required"]


def test_v1_advanced_families_and_semantics_are_registered() -> None:
    public_ids = {spec.template_id for spec in public_template_specs()}
    expected = {
        "estimation/coefficient",
        "diagnostics/qq",
        "diagnostics/feature_importance",
        "ordination/pca_scores",
        "ordination/pca_biplot",
        "ordination/pcoa",
        "ordination/nmds",
        "association/correlation_network",
        "flow/sankey",
        "field/quiver",
        "omics/volcano",
        "omics/enrichment_dot",
        "survival/kaplan_meier",
    }

    assert expected <= public_ids
    assert "coordinates" in load_family_contract("ordination")["variants"]["pca_scores"]["required"]
    assert "value" in load_family_contract("flow")["variants"]["sankey"]["required"]
    assert "adjusted_p_value" in load_family_contract("omics")["variants"]["volcano"]["required"]
    survival = load_family_contract("survival")["variants"]["kaplan_meier"]
    assert {"time", "survival_probability"} <= set(survival["required"])
    assert {"censoring", "lower_ci", "upper_ci", "censor_time"} <= set(survival["optional"])


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


def test_mantel_legends_use_bundled_ascii_glyphs() -> None:
    from matplotlib.legend import Legend

    figure = build_template("association/mantel")
    labels = [
        text.get_text()
        for axis in figure.axes
        for legend in axis.findobj(Legend)
        for text in legend.get_texts()
    ]

    assert labels == [
        "< 0.25",
        "0.25-0.50",
        ">= 0.50",
        "< 0.001",
        "0.001-0.01",
        "0.01-0.05",
        ">= 0.05",
    ]
    plt.close(figure)


def test_contour_data_domain_covers_the_visible_axes() -> None:
    figure = build_template("field/contour")
    axis = figure.axes[0]

    assert axis.get_xlim() == (axis.dataLim.x0, axis.dataLim.x1)
    assert axis.get_ylim() == (axis.dataLim.y0, axis.dataLim.y1)
    plt.close(figure)
