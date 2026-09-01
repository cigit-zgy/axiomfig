from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from axiomfig import config
from axiomfig.config import load_contracts
from axiomfig.intent import (
    FigureIntentError,
    build_intent_figure,
    load_dataset,
    load_figure_intent,
    parse_figure_intent,
)
from axiomfig.templates import registry
from axiomfig.templates.association.mantel import styling as mantel_styling

ROOT = Path(__file__).resolve().parents[1]


def test_figure_intent_yaml_rejects_duplicate_keys(tmp_path: Path) -> None:
    intent = tmp_path / "intent.yaml"
    intent.write_text(
        "template: scatter.parity\ntemplate: scatter.simple\n",
        encoding="utf-8",
    )

    with pytest.raises(FigureIntentError, match="duplicate YAML key.*template"):
        load_figure_intent(intent)


def test_packaged_style_contract_rejects_duplicate_keys(tmp_path: Path) -> None:
    source = ROOT / "src/axiomfig/resources/styles"
    target = tmp_path / "styles"
    shutil.copytree(source, target)
    style = target / "style.yaml"
    style.write_text("version: 1\n" + style.read_text(encoding="utf-8"), encoding="utf-8")
    load_contracts.cache_clear()
    try:
        with pytest.raises(ValueError, match="duplicate YAML key.*version"):
            load_contracts(target)
    finally:
        load_contracts.cache_clear()


def test_template_registry_rejects_duplicate_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "index.yaml").write_text(
        "version: 1\nversion: 1\nfamilies: {}\nlayouts: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)

    with pytest.raises(ValueError, match="duplicate YAML key.*version"):
        registry.load_template_registry()


def test_family_contract_rejects_duplicate_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    family = tmp_path / "line"
    family.mkdir()
    (family / "contract.yaml").write_text(
        "family: line\nfamily: line\nvariants: {single: {input_mode: direct}}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)

    with pytest.raises(ValueError, match="duplicate YAML key.*family"):
        registry.load_family_contract("line")


@pytest.mark.parametrize(
    ("name", "content"),
    (
        ("malformed.json", "{"),
        ("empty.json", ""),
        ("malformed.yaml", "template: ["),
    ),
)
def test_malformed_figure_intent_is_a_bounded_domain_error(
    tmp_path: Path, name: str, content: str
) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")

    with pytest.raises(FigureIntentError, match="cannot parse Figure Intent"):
        load_figure_intent(path)


def test_missing_figure_intent_path_is_a_bounded_domain_error(tmp_path: Path) -> None:
    with pytest.raises(FigureIntentError, match="cannot read Figure Intent"):
        load_figure_intent(tmp_path / "missing.yaml")


def test_json_rows_must_have_one_consistent_schema(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('[{"x": 1, "y": 2}, {"x": 3}]', encoding="utf-8")

    with pytest.raises(FigureIntentError, match="same string keys"):
        load_dataset(path)


def test_csv_rejects_duplicate_headers(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("x,x\n1,2\n", encoding="utf-8")

    with pytest.raises(FigureIntentError, match="duplicate CSV column"):
        load_dataset(path)


def test_csv_rejects_rows_with_missing_fields_as_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("x,y\n1\n", encoding="utf-8")

    with pytest.raises(FigureIntentError, match="same number of fields"):
        load_dataset(path)


def test_invalid_dataset_unicode_is_a_bounded_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_bytes(b"x\n\xff\n")

    with pytest.raises(FigureIntentError, match="cannot read dataset"):
        load_dataset(path)


def test_json_representable_huge_numbers_are_bounded_domain_errors() -> None:
    intent = parse_figure_intent(
        {
            "template": "line.single",
            "data": {"x": "time", "y": "value"},
        }
    )

    with pytest.raises(FigureIntentError):
        build_intent_figure(
            intent,
            {"time": [0, 1], "value": [1, 10**10000]},
        )


def test_builder_programmer_assertions_are_not_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only public-input normalization errors belong to the bounded wrapper."""
    intent = parse_figure_intent(
        {
            "template": "line.single",
            "data": {"x": "x", "y": "y"},
        }
    )

    def broken_builder(_template_id: str, **_values: object) -> object:
        raise AssertionError("internal builder invariant")

    monkeypatch.setattr("axiomfig.intent.build_template", broken_builder)
    with pytest.raises(AssertionError, match="internal builder invariant"):
        build_intent_figure(intent, {"x": [1, 2], "y": [3, 4]})


@pytest.mark.parametrize(
    "validator",
    (config._finite_number, mantel_styling._finite_number),
)
def test_oversized_executable_yaml_numbers_are_bounded_value_errors(validator) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        validator(10**10000, "style.token")
