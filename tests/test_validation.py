from pathlib import Path

import pytest

from axiomfig.validation import ValidationError, validate_gallery


def test_gallery_validation_rejects_missing_pairs(tmp_path: Path) -> None:
    (tmp_path / "01_line.pdf").write_bytes(b"not a PDF")

    with pytest.raises(ValidationError, match="missing PNG preview"):
        validate_gallery(tmp_path)
