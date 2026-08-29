from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from axiomfig.rendering import RenderError, render_figure, standalone_tex


def test_standalone_tex_wraps_vector_intermediate_without_claiming_macro_expansion() -> None:
    source = standalone_tex("intermediate.pdf")

    assert "\\includegraphics{intermediate.pdf}" in source
    assert "Figure text is already embedded" in source


def test_missing_tectonic_fails_before_writing_outputs(tmp_path: Path) -> None:
    figure, axis = plt.subplots()
    axis.plot([0, 1], [0, 1])

    with pytest.raises(RenderError, match="Tectonic executable"):
        render_figure(figure, tmp_path / "figure", tectonic="/missing/tectonic")

    assert not (tmp_path / "figure.pdf").exists()
    assert not (tmp_path / "figure.png").exists()
    plt.close(figure)
