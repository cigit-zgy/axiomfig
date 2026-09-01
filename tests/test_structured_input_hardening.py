from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from axiomfig import config
from axiomfig.config import load_contracts
from axiomfig.intent import (
    FigureIntentError,
    build_intent_figure,
    load_dataset,
    load_figure_intent,
    parse_figure_intent,
)
from axiomfig.structured_io import load_yaml
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


@pytest.mark.parametrize(
    "mutate",
    (
        lambda style: style["output"].__setitem__("allowed_margin_modes", None),
        lambda style: style["geometry"].__setitem__("single-column", None),
        lambda style: style["typography"].__setitem__("sizes_pt", None),
        lambda style: style["ticks"]["open"].__setitem__("major", None),
        lambda style: style["colorbar"].__setitem__("vertical", None),
        lambda style: style["layout"].__setitem__("multi_panel", None),
        lambda style: style["plots"].__setitem__("scatter", None),
    ),
)
def test_style_contract_bounds_malformed_nested_containers(
    mutate: Callable[[dict[str, object]], None],
) -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    mutate(style)

    with pytest.raises(ValueError, match="must be a mapping|must be a sequence"):
        config._validate_style(style)


def test_mantel_style_contract_contains_only_executable_defaults() -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    mantel = style["plots"]["mantel"]

    assert "minimum_cell_side" not in mantel["matrix"]
    assert "nonsignificant_mode" not in mantel["links"]


def test_packaged_contracts_contain_no_known_dead_visual_defaults() -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    fonts = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/fonts.yaml").read_text(encoding="utf-8"),
        source="fonts.yaml",
    )

    assert "default" not in style["typography"]
    assert "panel" not in style["typography"]["sizes_pt"]
    assert "top_tick_labels" not in style["axes"]
    assert "right_tick_labels" not in style["axes"]
    assert "single_series" not in style["legend"]
    assert "location" not in style["legend"]
    assert "prefer_single_row" not in style["legend"]
    assert "default" not in fonts
    assert "minor_to_major_inward_ratio" not in style["ticks"]["geometry"]
    assert all("length_token" not in policy for policy in style["ticks"]["open"].values())
    assert all("length_token" not in policy for policy in style["ticks"]["filled"].values())
    assert "alignment" not in style["colorbar"]["vertical"]
    assert "line" not in style["plots"]
    assert "value_labels" not in style["plots"]["bar"]


@pytest.mark.parametrize(
    ("filename", "mutate"),
    (
        ("fonts.yaml", lambda document: document.__setitem__("modes", None)),
        ("fonts.yaml", lambda document: document.__setitem__("families", None)),
        ("colors.yaml", lambda document: document.__setitem__("palettes", None)),
        ("colors.yaml", lambda document: document.__setitem__("constructed_colormaps", None)),
        ("style.yaml", lambda document: document.__setitem__("series", None)),
        ("style.yaml", lambda document: document["axes"].__setitem__("nice_linear", None)),
        ("style.yaml", lambda document: document["layout"].__setitem__("single_panel", None)),
        ("style.yaml", lambda document: document["plots"].__setitem__("heatmap", None)),
        ("style.yaml", lambda document: document["typography"]["sizes_pt"].pop("base")),
        ("style.yaml", lambda document: document["rendering"].__setitem__("pdf_fonttype", None)),
        ("fonts.yaml", lambda document: document["modes"]["sans"].__setitem__("extra", "x")),
        (
            "fonts.yaml",
            lambda document: document["families"]["latin-modern-sans"]["filenames"].pop("bold"),
        ),
    ),
)
def test_all_executable_resource_containers_fail_closed(
    tmp_path: Path,
    filename: str,
    mutate: Callable[[dict[str, object]], None],
) -> None:
    source = ROOT / "src/axiomfig/resources/styles"
    target = tmp_path / "styles"
    shutil.copytree(source, target)
    path = target / filename
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    load_contracts.cache_clear()
    try:
        with pytest.raises(ValueError):
            load_contracts(target)
    finally:
        load_contracts.cache_clear()


@pytest.mark.parametrize(
    ("required", "optional"),
    (
        (1, []),
        (["x", "x"], []),
        (["x"], None),
        ([""], []),
    ),
)
def test_family_contract_role_sequences_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required: object,
    optional: object,
) -> None:
    family = tmp_path / "line"
    family.mkdir()
    document = {
        "family": "line",
        "variants": {
            "single": {
                "input_mode": "direct",
                "required": required,
                "optional": optional,
            }
        },
    }
    (family / "contract.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)

    with pytest.raises(ValueError, match="required|optional"):
        registry.load_family_contract("line")


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


@pytest.mark.parametrize(
    "mutate",
    (
        lambda contract: contract["matrix"].__setitem__("source_label_max_width_pt", 10**10000),
        lambda contract: contract["matrix"].__setitem__("target_rail_offset", 10**10000),
        lambda contract: contract["links"]["strength_breaks"].__setitem__(0, 10**10000),
        lambda contract: contract["links"]["p_value_modes"]["canonical"]["breaks"].__setitem__(
            0, 10**10000
        ),
    ),
)
def test_complete_mantel_contract_bounds_oversized_numeric_values(
    mutate: Callable[[dict[str, object]], None],
) -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    contract = style["plots"]["mantel"]
    mutate(contract)

    with pytest.raises(ValueError, match="must be finite"):
        mantel_styling._validate_mantel_contract(contract)


def test_mantel_contract_rejects_unowned_ornament_configuration() -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    contract = style["plots"]["mantel"]
    contract["ornaments"]["obsolete_anchor"] = {"x": 0.5}

    with pytest.raises(ValueError, match="ornaments must contain only legend"):
        mantel_styling._validate_mantel_contract(contract)


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda contract: contract["links"].__setitem__("widths_pt", None), "must be a sequence"),
        (
            lambda contract: contract["links"]["p_value_modes"]["canonical"].__setitem__(
                "colors", 1
            ),
            "must be a sequence",
        ),
        (
            lambda contract: contract["links"]["p_value_modes"]["canonical"]["colors"].__setitem__(
                0, ["only-one-token"]
            ),
            "palette reference",
        ),
    ),
)
def test_mantel_contract_bounds_malformed_sequence_containers(
    mutate: Callable[[dict[str, object]], None], message: str
) -> None:
    style = load_yaml(
        (ROOT / "src/axiomfig/resources/styles/style.yaml").read_text(encoding="utf-8"),
        source="style.yaml",
    )
    contract = style["plots"]["mantel"]
    mutate(contract)

    with pytest.raises(ValueError, match=message):
        mantel_styling._validate_mantel_contract(contract)
