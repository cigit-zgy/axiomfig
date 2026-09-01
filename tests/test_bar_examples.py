from __future__ import annotations

from pathlib import Path

import pytest
import yaml

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
            str(root / "examples" / "bar" / f"{grammar}.intent.yaml"),
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
            str(root / "examples/bar/grouped_uncertainty.intent.yaml"),
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


def test_core_bar_examples_use_explicit_intent_suffix_and_canonical_data_roles() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "bar"
    expected = {f"{grammar}.intent.yaml" for grammar in CORE_BAR_GRAMMARS}

    assert expected <= {path.name for path in root.glob("*.intent.yaml")}
    assert not any((root / f"{grammar}.yaml").exists() for grammar in CORE_BAR_GRAMMARS)

    normalized = yaml.safe_load((root / "normalized_stacked.intent.yaml").read_text())
    mirrored = yaml.safe_load((root / "mirrored.intent.yaml").read_text())
    assert set(normalized["data"]) == {"category", "component", "value"}
    assert normalized["semantics"]["normalization"] in {"normalize", "proportion"}
    assert set(mirrored["data"]) == {"category", "side", "value"}
    assert mirrored["semantics"]["mirror_side"] == "Female"
