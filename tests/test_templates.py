import matplotlib as mpl
import matplotlib.figure
import matplotlib.pyplot as plt
import pytest

from axiomfig.templates import TEMPLATE_BUILDERS, build_template


@pytest.mark.parametrize(
    "name",
    [
        "line-single",
        "line-multi",
        "line-marker",
        "line-ci",
        "scatter-basic",
        "scatter-grouped",
        "scatter-parity",
        "bar-vertical",
        "bar-grouped",
        "boxplot",
        "violin",
        "heatmap",
        "model-evaluation",
        "residual",
        "layout-2-panel",
        "layout-4-panel",
        "multilingual",
    ],
)
def test_required_template_builders_return_figures(name: str) -> None:
    assert name in TEMPLATE_BUILDERS

    figure = build_template(name)

    assert isinstance(figure, matplotlib.figure.Figure)
    assert figure.axes


@pytest.mark.parametrize("name", sorted(TEMPLATE_BUILDERS))
def test_templates_do_not_mutate_contract_rcparams(name: str) -> None:
    forbidden = {
        "font.size",
        "font.family",
        "figure.figsize",
        "lines.linewidth",
        "axes.linewidth",
        "xtick.major.size",
        "ytick.major.size",
        "axes.prop_cycle",
        "savefig.format",
    }

    before = {key: mpl.rcParams[key] for key in forbidden}

    figure = build_template(name)

    after = {key: mpl.rcParams[key] for key in forbidden}
    assert after == before
    plt.close(figure)


def test_model_evaluation_panels_share_geometry() -> None:
    figure = build_template("model-evaluation")
    figure.canvas.draw()
    left, right = (axis.get_position() for axis in figure.axes)

    assert left.y0 == pytest.approx(right.y0, abs=0.01)
    assert left.height == pytest.approx(right.height, abs=0.01)
    plt.close(figure)
