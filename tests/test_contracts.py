from pathlib import Path

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.ticker import AutoMinorLocator, LogLocator

from axiomfig.contracts import FILLED_TICK_PARAMS, OPEN_TICK_PARAMS, STROKE_WIDTH_PT
from axiomfig.styles import apply_tick_contract

ROOT = Path(__file__).resolve().parents[1]


def test_publication_style_uses_the_central_stroke_for_every_default_visible_stroke() -> None:
    params = mpl.rc_params_from_file(
        ROOT / "styles/base/publication.mplstyle", fail_on_error=True, use_default_template=False
    )

    assert STROKE_WIDTH_PT == 0.6
    assert {
        params[key]
        for key in (
            "axes.linewidth",
            "xtick.major.width",
            "ytick.major.width",
            "xtick.minor.width",
            "ytick.minor.width",
            "lines.linewidth",
            "lines.markeredgewidth",
            "patch.linewidth",
            "boxplot.boxprops.linewidth",
            "boxplot.capprops.linewidth",
            "boxplot.medianprops.linewidth",
            "boxplot.whiskerprops.linewidth",
        )
    } == {STROKE_WIDTH_PT}


def test_open_plot_style_owns_open_tick_directions() -> None:
    figure, axes = plt.subplots()
    apply_tick_contract(axes, filled=False)

    assert OPEN_TICK_PARAMS == {"major": "inout", "minor": "in"}
    assert axes.xaxis._major_tick_kw["tickdir"] == OPEN_TICK_PARAMS["major"]
    assert axes.xaxis._minor_tick_kw["tickdir"] == OPEN_TICK_PARAMS["minor"]
    plt.close(figure)


def test_filled_plot_style_owns_outward_ticks() -> None:
    figure, axes = plt.subplots()
    apply_tick_contract(axes, filled=True)

    assert FILLED_TICK_PARAMS == {"major": "out", "minor": "out"}
    assert axes.xaxis._major_tick_kw["tickdir"] == FILLED_TICK_PARAMS["major"]
    assert axes.xaxis._minor_tick_kw["tickdir"] == FILLED_TICK_PARAMS["minor"]
    plt.close(figure)


def test_open_tick_contract_sets_one_linear_minor_locator_per_major_interval() -> None:
    figure, axes = plt.subplots()
    apply_tick_contract(axes, filled=False)

    assert isinstance(axes.xaxis.get_minor_locator(), AutoMinorLocator)
    assert isinstance(axes.yaxis.get_minor_locator(), AutoMinorLocator)
    plt.close(figure)


def test_tick_contract_preserves_log_minor_locator() -> None:
    figure, axes = plt.subplots()
    axes.set_xscale("log")
    expected_locator = axes.xaxis.get_minor_locator()
    assert isinstance(expected_locator, LogLocator)

    apply_tick_contract(axes, filled=True)

    assert axes.xaxis.get_minor_locator() is expected_locator
    assert axes.xaxis._major_tick_kw["tickdir"] == FILLED_TICK_PARAMS["major"]
    assert axes.xaxis._minor_tick_kw["tickdir"] == FILLED_TICK_PARAMS["minor"]
    plt.close(figure)
