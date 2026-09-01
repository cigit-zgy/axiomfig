from __future__ import annotations

from pathlib import Path

import pytest

CORE_BAR_GRAMMARS = (
    "simple",
    "grouped",
    "stacked",
    "normalized_stacked",
    "grouped_stacked",
    "diverging_stacked",
    "range",
    "mirrored",
    "waterfall",
)


@pytest.mark.e2e
@pytest.mark.parametrize("grammar", CORE_BAR_GRAMMARS)
def test_bar_csv_figure_intent_examples_execute_real_cli(grammar: str, tmp_path: Path) -> None:
    from axiomfig.cli import intent_main
    from axiomfig.validation import validate_pair

    root = Path(__file__).resolve().parents[1]
    stem = tmp_path / grammar
    result = intent_main(
        [
            str(root / "examples" / "bar" / f"{grammar}.yaml"),
            "--data",
            str(root / "examples" / "bar" / f"{grammar}.csv"),
            "--output",
            str(stem),
            "--work-root",
            str(tmp_path / "work" / grammar),
        ]
    )

    assert result == 0
    validate_pair(stem.with_suffix(".pdf"), stem.with_suffix(".png"))


@pytest.mark.e2e
def test_grouped_uncertainty_uses_external_csv_and_explicit_semantics(tmp_path: Path) -> None:
    from axiomfig.cli import intent_main
    from axiomfig.validation import validate_pair

    root = Path(__file__).resolve().parents[1]
    stem = tmp_path / "grouped_uncertainty"
    result = intent_main(
        [
            str(root / "examples/bar/grouped_uncertainty.yaml"),
            "--data",
            str(root / "examples/bar/grouped_uncertainty.csv"),
            "--output",
            str(stem),
            "--work-root",
            str(tmp_path / "work"),
        ]
    )

    assert result == 0
    validate_pair(stem.with_suffix(".pdf"), stem.with_suffix(".png"))
