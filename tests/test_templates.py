import matplotlib as mpl
import matplotlib.figure
import matplotlib.pyplot as plt
import pytest

from axiomfig.templates import TEMPLATE_BUILDERS, build_template

CANONICAL_TEMPLATES = {
    "single-line",
    "multi-line",
    "line-marker",
    "line-ci",
    "scatter",
    "grouped-scatter",
    "parity",
    "regression-scatter",
    "vertical-bar",
    "grouped-bar",
    "horizontal-bar",
    "stacked-bar",
    "boxplot",
    "violin",
    "box-violin",
    "histogram",
    "density",
    "ecdf",
    "heatmap",
    "errorbar",
    "forest-plot",
    "point-interval",
    "bland-altman",
    "correlation-heatmap",
    "clustered-heatmap",
    "confusion-matrix",
    "roc-curve",
    "pr-curve",
    "calibration-curve",
    "residual-diagnostics",
    "mantel-test",
    "model-evaluation",
    "two-panel",
    "four-panel",
    "six-panel",
    "complex-multi-panel",
}


def test_registry_contains_only_thirty_six_canonical_templates_from_four_families() -> None:
    assert set(TEMPLATE_BUILDERS) == CANONICAL_TEMPLATES
    assert {
        builder.__module__.rsplit(".", maxsplit=1)[-1] for builder in TEMPLATE_BUILDERS.values()
    } == {"curves", "distributions", "surfaces", "panels"}


@pytest.mark.parametrize("name", sorted(CANONICAL_TEMPLATES))
def test_canonical_template_builders_return_figures(name: str) -> None:
    figure = build_template(name)

    assert isinstance(figure, matplotlib.figure.Figure)
    assert figure.axes
    plt.close(figure)


@pytest.mark.parametrize("name", sorted(CANONICAL_TEMPLATES))
def test_templates_do_not_mutate_contract_rcparams(name: str) -> None:
    keys = ("font.size", "font.family", "figure.figsize", "lines.linewidth", "axes.linewidth")
    before = {key: mpl.rcParams[key] for key in keys}

    figure = build_template(name)

    assert {key: mpl.rcParams[key] for key in keys} == before
    plt.close(figure)


def test_mantel_significance_legend_uses_bundled_ascii_glyphs() -> None:
    figure = build_template("mantel-test")
    labels = [
        text.get_text()
        for axis in figure.axes
        if axis.get_legend() is not None
        for text in axis.get_legend().get_texts()
    ]

    assert labels == ["p < 0.05", "not significant"]
    plt.close(figure)
