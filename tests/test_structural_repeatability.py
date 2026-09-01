from __future__ import annotations

import matplotlib.pyplot as plt

from tests.evaluation.structural_repeatability import figure_signature


def test_structural_signature_is_stable_and_sensitive_to_line_data() -> None:
    figure, axis = plt.subplots()
    axis.plot([0.0, 1.0], [0.0, 1.0], label="Series")
    axis.legend()
    try:
        initial = figure_signature(figure)
        assert figure_signature(figure) == initial
        axis.lines[0].set_ydata([0.0, 2.0])
        assert figure_signature(figure) != initial
    finally:
        plt.close(figure)
