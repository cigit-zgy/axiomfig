from pathlib import Path

import matplotlib as mpl
import pytest

from axiomfig.styles import StyleConflictError, StyleSelection, compose_styles

ROOT = Path(__file__).resolve().parents[1]
STYLE_ROOT = ROOT / "src/axiomfig/resources/styles"


def test_style_selection_uses_fixed_layer_order() -> None:
    selection = StyleSelection(
        geometry="double-column",
        typography="sans",
        colors="muted",
        plot="line",
        language="multilingual",
        rendering="vector",
    )

    paths = selection.paths()

    assert [path.relative_to(STYLE_ROOT).as_posix() for path in paths] == [
        "base/publication.mplstyle",
        "geometry/double-column.mplstyle",
        "typography/sans.mplstyle",
        "colors/muted.mplstyle",
        "plot/line.mplstyle",
        "language/multilingual.mplstyle",
        "rendering/vector.mplstyle",
    ]


def test_composition_rejects_undeclared_key_conflicts(tmp_path: Path) -> None:
    first = tmp_path / "first.mplstyle"
    second = tmp_path / "second.mplstyle"
    first.write_text("lines.linewidth: 1.0\n", encoding="utf-8")
    second.write_text("lines.linewidth: 1.2\n", encoding="utf-8")

    with pytest.raises(StyleConflictError, match="lines.linewidth"):
        compose_styles([first, second])


def test_every_committed_style_is_loadable() -> None:
    style_paths = sorted(STYLE_ROOT.rglob("*.mplstyle"))

    assert style_paths
    for path in style_paths:
        params = mpl.rc_params_from_file(path, fail_on_error=True, use_default_template=False)
        assert params


def test_plot_style_overrides_are_limited_to_declared_contract_exceptions() -> None:
    expected_overrides = {
        "bar": {"patch.edgecolor", "xtick.direction", "ytick.direction"},
        "distribution": {"boxplot.flierprops.markersize", "xtick.direction", "ytick.direction"},
        "heatmap": {"image.cmap", "image.interpolation", "xtick.direction", "ytick.direction"},
        "line": {"lines.markersize"},
        "scatter": {"lines.markersize"},
    }

    for name, expected_keys in expected_overrides.items():
        params = mpl.rc_params_from_file(
            STYLE_ROOT / "plot" / f"{name}.mplstyle",
            fail_on_error=True,
            use_default_template=False,
        )
        assert set(params) == expected_keys
