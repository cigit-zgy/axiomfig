from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tests" / "evaluation" / "layout_benchmark" / "round01"
BACKENDS = ("original", "default", "kiwi", "adjusttext", "textalloc")
EXPERIMENTAL_BACKENDS = BACKENDS[1:]
FILENAMES = (
    "01_clustered_heatmap.pdf",
    "02_pairgrid.pdf",
    "03_joint_marginal.pdf",
    "04_forest_plot.pdf",
    "05_km_risk_table.pdf",
    "06_calibration_histogram.pdf",
    "07_pdp_ice_grid.pdf",
    "08_influence_labels.pdf",
    "09_volcano_labels.pdf",
    "10_dotplot_dendrogram.pdf",
)


def _load_builder_module():
    path = ROOT / "scripts" / "build_layout_benchmark.py"
    spec = importlib.util.spec_from_file_location("build_layout_benchmark", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_layout_benchmark_fixture_risk_table_shape_matches_time_columns() -> None:
    module = _load_builder_module()
    fixture = module.FIXTURES["05"]

    assert fixture["at_risk"].shape == (3, len(fixture["risk_times"]))


def test_layout_benchmark_rejects_drifted_official_image_payload(tmp_path: Path) -> None:
    module = _load_builder_module()
    cache = tmp_path / "source.png"
    cache.write_bytes(b"not-the-reviewed-official-image")

    with pytest.raises(RuntimeError, match="official image checksum mismatch"):
        module._official_image_to_pdf(
            "https://example.invalid/source.png",
            tmp_path / "source.pdf",
            cache_path=cache,
            expected_sha256="0" * 64,
            expected_dimensions=(1, 1),
        )


def test_layout_benchmark_registers_bundled_serif_font() -> None:
    from matplotlib import font_manager

    module = _load_builder_module()
    module._register_benchmark_fonts()
    family = module._rcparams()["font.serif"][0]
    path = font_manager.findfont(
        font_manager.FontProperties(family=[family]), fallback_to_default=False
    )

    assert "XCharter" in Path(path).name


def test_layout_benchmark_metrics_are_json_serializable() -> None:
    module = _load_builder_module()
    module._register_benchmark_fonts()
    with module.mpl.rc_context(rc=module._rcparams()):
        rendered = module._build_08("default")
        metrics = module._measure(rendered, 0.1)
        module.plt.close(rendered.figure)

    json.dumps(metrics)


def test_layout_benchmark_metrics_distinguish_missing_checks_from_zero() -> None:
    module = _load_builder_module()
    module._register_benchmark_fonts()
    with module.mpl.rc_context(rc=module._rcparams()):
        rendered = module._build_04("default")
        metrics = module._measure(rendered, 0.1)
        module.plt.close(rendered.figure)

    assert metrics["text_data_check_count"] == 0
    assert metrics["text_data_overlap_count"] is None
    assert metrics["ornament_check_count"] == 0
    assert metrics["ornament_overlap_count"] is None
    assert metrics["minimum_gap_check_count"] == 0
    assert metrics["minimum_gap_violation_count"] is None


def test_layout_benchmark_shared_axis_metric_detects_limit_mismatch() -> None:
    module = _load_builder_module()
    figure = module.plt.figure(figsize=(4, 3))
    first = figure.add_axes((0.1, 0.1, 0.35, 0.8))
    second = figure.add_axes((0.1, 0.1, 0.35, 0.8))
    first.set_xlim(0, 1)
    second.set_xlim(0, 2)
    rendered = module.RenderedCase(figure, shared_x_groups=((first, second),))

    metrics = module._measure(rendered, 0.1)
    assert metrics["shared_x_alignment_error_pt"] > 0
    module.plt.close(figure)


def test_layout_benchmark_edge_metric_detects_shifted_equal_width_axes() -> None:
    module = _load_builder_module()
    figure = module.plt.figure(figsize=(4, 3))
    first = figure.add_axes((0.1, 0.1, 0.35, 0.8))
    second = figure.add_axes((0.2, 0.1, 0.35, 0.8))
    rendered = module.RenderedCase(figure, x_edge_groups=((first, second),))

    metrics = module._measure(rendered, 0.1)
    assert metrics["x_edge_alignment_error_pt"] > 0
    module.plt.close(figure)


def test_layout_benchmark_repeatability_signature_includes_artist_paths() -> None:
    module = _load_builder_module()
    figure, axis = module.plt.subplots(figsize=(4, 3))
    (line,) = axis.plot([0, 1], [0, 1])
    rendered = module.RenderedCase(figure)
    initial = module._measure(rendered, 0.1)["geometry_signature"]

    line.set_ydata([1, 0])
    changed = module._measure(rendered, 0.1)["geometry_signature"]

    assert changed != initial
    module.plt.close(figure)


@pytest.mark.parametrize("backend", ("default", "kiwi"))
def test_layout_benchmark_grid_height_ratios_are_top_to_bottom(backend: str) -> None:
    module = _load_builder_module()
    rects = module._grid_rects(
        backend,
        2,
        1,
        margins=(0.1, 0.9, 0.1, 0.9),
        height_ratios=(0.2, 0.8),
        vgap=0.0,
    )

    assert rects[0, 0][3] / rects[1, 0][3] == pytest.approx(0.25)
    assert rects[0, 0][1] > rects[1, 0][1]


def test_layout_benchmark_joint_marginals_share_joint_limits() -> None:
    module = _load_builder_module()
    rendered = module._build_03("default")
    top, right, joint = rendered.figure.axes

    assert top.get_shared_x_axes().joined(top, joint)
    assert right.get_shared_y_axes().joined(right, joint)
    assert top.get_xlim() == pytest.approx(joint.get_xlim())
    assert right.get_ylim() == pytest.approx(joint.get_ylim())
    module.plt.close(rendered.figure)


def test_layout_benchmark_pairgrid_harmonizes_each_variable_axis() -> None:
    module = _load_builder_module()
    rendered = module._build_02("default")
    axes = rendered.figure.axes[:16]

    for column in range(4):
        x_limits = [axes[row * 4 + column].get_xlim() for row in range(4)]
        assert all(limits == pytest.approx(x_limits[0]) for limits in x_limits[1:])
    for row in range(4):
        off_diagonal = [axes[row * 4 + column].get_ylim() for column in range(4) if column != row]
        assert all(limits == pytest.approx(off_diagonal[0]) for limits in off_diagonal[1:])
    module.plt.close(rendered.figure)


def test_layout_benchmark_pairgrid_diagonal_groups_share_bin_edges() -> None:
    module = _load_builder_module()
    rendered = module._build_02("default")
    diagonal = rendered.figure.axes[0]
    x_coordinates = [tuple(patch.get_xy()[:, 0]) for patch in diagonal.patches]

    assert len(x_coordinates) == 3
    assert x_coordinates[1:] == [x_coordinates[0], x_coordinates[0]]
    module.plt.close(rendered.figure)


def test_layout_benchmark_dotplot_dendrogram_aligns_with_matrix_rows() -> None:
    module = _load_builder_module()
    rendered = module._build_10("default")
    dendrogram_axis, matrix_axis = rendered.figure.axes[:2]
    dendrogram_box = dendrogram_axis.get_position()
    matrix_box = matrix_axis.get_position()

    assert dendrogram_box.height == pytest.approx(matrix_box.height)
    assert dendrogram_box.y0 == pytest.approx(matrix_box.y0)
    assert dendrogram_box.x1 < matrix_box.x0
    renderer = rendered.figure.canvas.get_renderer()
    del renderer
    for index in range(7):
        dendrogram_y = dendrogram_axis.transData.transform((0, 5 + 10 * index))[1]
        matrix_y = matrix_axis.transData.transform((0, index))[1]
        assert dendrogram_y == pytest.approx(matrix_y, abs=0.1)
    module.plt.close(rendered.figure)


def test_layout_benchmark_clustered_heatmap_includes_annotation_strips() -> None:
    module = _load_builder_module()
    rendered = module._build_01("default")
    image_shapes = [
        image.get_array().shape for axis in rendered.figure.axes for image in axis.images
    ]

    assert (1, 12) in image_shapes
    assert (18, 1) in image_shapes
    module.plt.close(rendered.figure)


def test_layout_benchmark_stacked_axes_are_formally_shared() -> None:
    module = _load_builder_module()
    for builder in (module._build_05, module._build_06):
        rendered = builder("default")
        upper, lower = rendered.figure.axes[:2]
        assert upper.get_shared_x_axes().joined(upper, lower)
        module.plt.close(rendered.figure)


def test_layout_benchmark_calibration_histogram_contains_models_only() -> None:
    module = _load_builder_module()
    rendered = module._build_06("default")
    calibration, histogram = rendered.figure.axes[:2]

    assert len(calibration.lines) == 3
    assert len(histogram.lines) == 2
    module.plt.close(rendered.figure)


@pytest.mark.parametrize(
    ("backend", "dependency"),
    (
        ("default", None),
        ("kiwi", "kiwisolver"),
        ("adjusttext", "adjustText"),
        ("textalloc", "textalloc"),
    ),
)
def test_layout_benchmark_text_cases_are_repeatable(backend: str, dependency: str | None) -> None:
    if dependency is not None and importlib.util.find_spec(dependency) is None:
        pytest.skip(f"optional benchmark dependency not installed: {dependency}")
    module = _load_builder_module()
    module._register_benchmark_fonts()
    with module.mpl.rc_context(rc=module._rcparams()):
        for case_id in ("08", "09"):
            signatures = []
            for _ in range(2):
                module.np.random.seed(0)
                rendered = module.BUILDERS[case_id](backend)
                signatures.append(module._measure(rendered, 0.1)["geometry_signature"])
                module.plt.close(rendered.figure)
            assert signatures[0] == signatures[1]


def _page_size(path: Path) -> tuple[float, float]:
    page = PdfReader(path).pages[0]
    return float(page.mediabox.width), float(page.mediabox.height)


def test_layout_benchmark_has_exact_pdf_only_projection() -> None:
    assert (BENCHMARK / "SOURCES.md").is_file()
    assert {path.name for path in BENCHMARK.iterdir() if path.is_file()} == {"SOURCES.md"}
    assert {path.name for path in BENCHMARK.iterdir() if path.is_dir()} == set(BACKENDS)
    for backend in BACKENDS:
        directory = BENCHMARK / backend
        assert tuple(sorted(path.name for path in directory.iterdir())) == FILENAMES
        assert all(path.stat().st_size > 1_000 for path in directory.iterdir())


def test_layout_benchmark_experimental_page_sizes_match_by_case() -> None:
    for filename in FILENAMES:
        sizes = [_page_size(BENCHMARK / backend / filename) for backend in EXPERIMENTAL_BACKENDS]
        assert max(width for width, _ in sizes) - min(width for width, _ in sizes) <= 0.01
        assert max(height for _, height in sizes) - min(height for _, height in sizes) <= 0.01


@pytest.mark.skipif(shutil.which("pdffonts") is None, reason="pdffonts is required")
def test_layout_benchmark_pdfs_avoid_type3_and_experiments_use_serif() -> None:
    for backend in BACKENDS:
        for filename in FILENAMES:
            completed = subprocess.run(
                ["pdffonts", str(BENCHMARK / backend / filename)],
                check=True,
                text=True,
                capture_output=True,
            )
            assert "Type 3" not in completed.stdout
            if backend in EXPERIMENTAL_BACKENDS:
                assert "XCharter" in completed.stdout


def test_layout_benchmark_pdfs_are_single_page_with_content() -> None:
    for backend in BACKENDS:
        for filename in FILENAMES:
            reader = PdfReader(BENCHMARK / backend / filename)
            assert len(reader.pages) == 1
            contents = reader.pages[0].get_contents()
            assert contents is not None
            assert contents.get_data().strip()
