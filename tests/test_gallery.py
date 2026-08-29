from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_STEMS = (
    "01_single_line",
    "02_multi_line",
    "03_line_marker",
    "04_line_ci",
    "05_scatter",
    "06_grouped_scatter",
    "07_parity",
    "08_regression_scatter",
    "09_vertical_bar",
    "10_grouped_bar",
    "11_horizontal_bar",
    "12_stacked_bar",
    "13_boxplot",
    "14_violin",
    "15_box_violin",
    "16_histogram",
    "17_density",
    "18_ecdf",
    "19_errorbar",
    "20_forest_plot",
    "21_point_interval",
    "22_bland_altman",
    "23_heatmap",
    "24_correlation_heatmap",
    "25_clustered_heatmap",
    "26_confusion_matrix",
    "27_roc_curve",
    "28_pr_curve",
    "29_calibration_curve",
    "30_residual_diagnostics",
    "31_mantel_test",
    "32_model_evaluation",
    "33_two_panel",
    "34_four_panel",
    "35_six_panel",
    "36_complex_multi_panel",
)


def test_gallery_registry_is_two_matching_thirty_six_case_families() -> None:
    from axiomfig.gallery import GALLERY_MODES, GALLERY_SPECS

    assert GALLERY_MODES == ("sans", "serif")
    assert tuple(spec.stem for spec in GALLERY_SPECS) == EXPECTED_STEMS
    assert tuple(spec.template for spec in GALLERY_SPECS) == tuple(
        stem.split("_", maxsplit=1)[1].replace("_", "-") for stem in EXPECTED_STEMS
    )


def test_gallery_declares_two_tectonic_native_cases() -> None:
    from axiomfig.gallery import LATEX_GALLERY_STEMS

    assert LATEX_GALLERY_STEMS == ("01_scientific_typography", "02_palettes")


def test_gallery_cli_validates_matplotlib_and_latex_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from axiomfig import cli

    captured: dict[str, set[str]] = {}
    monkeypatch.setattr(cli, "build_gallery", lambda *args, **kwargs: [])

    def capture(_gallery: Path, *, expected_stems: object) -> list[object]:
        captured["expected"] = set(expected_stems)  # type: ignore[arg-type]
        return []

    monkeypatch.setattr(cli, "validate_gallery", capture)

    assert cli.gallery_main(["--gallery", str(tmp_path / "gallery")]) == 0
    assert captured["expected"] == {
        *(f"{mode}/{stem}" for mode in ("sans", "serif") for stem in EXPECTED_STEMS),
        "latex/01_scientific_typography",
        "latex/02_palettes",
    }


@pytest.mark.e2e
def test_gallery_builds_only_canonical_pdf_png_pairs(tmp_path: Path) -> None:
    from axiomfig.gallery import GALLERY_MODES, build_gallery
    from axiomfig.validation import validate_gallery

    gallery = tmp_path / "gallery"
    results = build_gallery(gallery, work_root=tmp_path / "work")
    expected_paths = {f"{mode}/{stem}" for mode in GALLERY_MODES for stem in EXPECTED_STEMS}
    expected_paths.update({"latex/01_scientific_typography", "latex/02_palettes"})
    entries = validate_gallery(gallery, expected_stems=expected_paths)

    assert len(results) == 74
    assert len(entries) == 74
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.pdf")
    } == expected_paths
    assert {
        path.relative_to(gallery).with_suffix("").as_posix() for path in gallery.rglob("*.png")
    } == expected_paths
