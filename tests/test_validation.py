from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from axiomfig.templates import build_template
from axiomfig.validation import ValidationError, validate_gallery


def test_nested_gallery_validation_rejects_missing_pairs(tmp_path: Path) -> None:
    mode = tmp_path / "sans"
    mode.mkdir()
    (mode / "01_line.pdf").write_bytes(b"not a PDF")

    with pytest.raises(ValidationError, match="missing PNG preview"):
        validate_gallery(tmp_path)


def test_nested_gallery_validation_checks_relative_expected_stems(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="gallery PDF set mismatch"):
        validate_gallery(tmp_path, expected_stems={"sans/01_line", "serif/01_line"})


def test_figure_anatomy_rejects_auxiliary_axes_outside_its_footprint() -> None:
    from axiomfig.anatomy import FigureAnatomyError, validate_figure_anatomy
    from axiomfig.layout import get_figure_layout

    figure = build_template("layouts/grid_2x2")
    layout = get_figure_layout(figure)
    assert layout is not None
    heatmap = layout.panels[-1]
    assert len(heatmap.auxiliary_axes) == 1
    auxiliary = heatmap.auxiliary_axes[0]
    position = auxiliary.get_position()
    auxiliary.set_position((1.01, position.y0, position.width, position.height))

    with pytest.raises(FigureAnatomyError, match="auxiliary axes.*outside panel footprint"):
        validate_figure_anatomy(figure)
    plt.close(figure)


def test_figure_anatomy_rejects_figure_level_ornament_overflow() -> None:
    from axiomfig.anatomy import FigureAnatomyError, validate_figure_anatomy
    from axiomfig.layout import register_figure_ornament

    figure = build_template("layouts/horizontal_2")
    overflow = figure.text(1.25, 1.25, "overflow", transform=figure.transFigure)
    register_figure_ornament(figure, overflow)

    with pytest.raises(FigureAnatomyError, match="figure-level ornament.*outside output boundary"):
        validate_figure_anatomy(figure)
    plt.close(figure)
