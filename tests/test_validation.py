from pathlib import Path

import pytest

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
