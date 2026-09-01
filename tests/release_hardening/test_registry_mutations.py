from __future__ import annotations

from pathlib import Path

import pytest

from axiomfig.templates import TEMPLATE_BUILDERS, registry


def test_duplicate_template_ids_in_test_local_registry_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "index.yaml").write_text(
        """\
version: 1
families:
  duplicate:
    variants:
      example: {geometry: single-column}
layouts:
  duplicate:
    variants:
      example: {geometry: double-column}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)
    with pytest.raises(ValueError, match="duplicate template ID"):
        registry.load_template_registry()


def test_invalid_contract_input_mode_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    family = tmp_path / "line"
    family.mkdir()
    (family / "contract.yaml").write_text(
        "family: line\nvariants: {single: {input_mode: inferred}}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)
    with pytest.raises(ValueError, match="invalid input_mode"):
        registry.load_family_contract("line")


def test_missing_family_contract_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "files", lambda _package: tmp_path)
    with pytest.raises(ValueError, match="missing contract"):
        registry.load_family_contract("line")


def test_registry_builder_mismatch_fails() -> None:
    incomplete = dict(TEMPLATE_BUILDERS)
    incomplete.pop("scatter/parity")
    with pytest.raises(ValueError, match="registry/builder mismatch"):
        registry.validate_registry(incomplete)


def test_registry_contract_variant_mismatch_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual_loader = registry.load_family_contract

    def altered_contract(family: str) -> dict[str, object]:
        contract = actual_loader(family)
        if family == "scatter":
            contract = dict(contract)
            variants = dict(contract["variants"])
            variants.pop("parity")
            contract["variants"] = variants
        return contract

    monkeypatch.setattr(registry, "load_family_contract", altered_contract)
    with pytest.raises(ValueError, match="registry/contract mismatch"):
        registry.validate_registry(TEMPLATE_BUILDERS)
