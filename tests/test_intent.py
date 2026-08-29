from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
import yaml


def test_minimal_figure_intent_normalizes_template_and_defaults(tmp_path: Path) -> None:
    from axiomfig.intent import load_figure_intent

    path = tmp_path / "intent.yaml"
    path.write_text(
        "template: scatter.parity\ndata:\n  observed: obs\n  predicted: pred\n",
        encoding="utf-8",
    )

    intent = load_figure_intent(path)

    assert intent.template_id == "scatter/parity"
    assert dict(intent.data) == {"observed": "obs", "predicted": "pred"}
    assert intent.geometry == "single-column"
    assert intent.typography == "sans"
    assert not intent.semantics


@pytest.mark.parametrize(
    "field",
    [
        "font_size",
        "linewidth",
        "tick_length",
        "legend_x",
        "panel_offset",
        "bar_width",
        "colorbar_width",
        "subplot_wspace",
    ],
)
def test_figure_intent_rejects_low_level_visual_decisions(field: str) -> None:
    from axiomfig.intent import FigureIntentError, parse_figure_intent

    with pytest.raises(FigureIntentError, match="deterministic visual field"):
        parse_figure_intent(
            {
                "template": "line.single",
                "data": {"x": "time", "y": "value"},
                field: 2,
            }
        )


def test_figure_intent_requires_explicit_scientific_semantics() -> None:
    from axiomfig.intent import FigureIntentError, parse_figure_intent

    with pytest.raises(FigureIntentError, match="uncertainty_type"):
        parse_figure_intent(
            {
                "template": "estimation.forest",
                "data": {"label": "term", "estimate": "estimate", "interval": "half_width"},
            }
        )


def test_json_dataset_and_parity_intent_reach_canonical_builder(tmp_path: Path) -> None:
    from axiomfig.intent import build_intent_figure, load_dataset, parse_figure_intent

    dataset_path = tmp_path / "data.json"
    dataset_path.write_text(
        json.dumps({"obs": [1.0, 2.0, 3.0], "pred": [1.1, 1.9, 3.2]}),
        encoding="utf-8",
    )
    intent = parse_figure_intent(
        {
            "template": "scatter.parity",
            "data": {"observed": "obs", "predicted": "pred"},
        }
    )

    figure = build_intent_figure(intent, load_dataset(dataset_path))
    offsets = figure.axes[0].collections[0].get_offsets()

    np.testing.assert_allclose(
        np.asarray(offsets),
        [[1.0, 1.1], [2.0, 1.9], [3.0, 3.2]],
    )
    plt.close(figure)


def test_csv_dataset_supports_grouped_scatter(tmp_path: Path) -> None:
    from axiomfig.intent import build_intent_figure, load_dataset, parse_figure_intent

    dataset_path = tmp_path / "data.csv"
    dataset_path.write_text(
        "observed,predicted,split\n1,1.2,train\n2,1.8,test\n3,3.1,train\n4,3.8,test\n",
        encoding="utf-8",
    )
    intent = parse_figure_intent(
        {
            "template": "scatter.grouped",
            "data": {"x": "observed", "y": "predicted", "group": "split"},
        }
    )

    figure = build_intent_figure(intent, load_dataset(dataset_path))

    assert len(figure.axes[0].collections) == 2
    assert {text.get_text() for text in figure.axes[0].get_legend().get_texts()} == {
        "train",
        "test",
    }
    plt.close(figure)


def test_intent_without_data_uses_deterministic_canonical_example() -> None:
    from axiomfig.intent import build_intent_figure, parse_figure_intent

    intent = parse_figure_intent({"template": "association.mantel"})
    figure = build_intent_figure(intent)

    assert intent.geometry == "onehalf-column"
    assert len(figure.axes) == 2
    plt.close(figure)


def test_multi_line_intent_reaches_data_bearing_canonical_builder() -> None:
    from axiomfig.intent import build_intent_figure, parse_figure_intent

    intent = parse_figure_intent(
        {
            "template": "line.multi",
            "data": {
                "x": "time",
                "series_values": "responses",
                "series_labels": "models",
            },
        }
    )

    figure = build_intent_figure(
        intent,
        {
            "time": [0.0, 1.0, 2.0],
            "responses": [[0.1, 0.4, 0.8], [0.2, 0.5, 0.7]],
            "models": ["Mechanistic", "Hybrid"],
        },
    )

    assert [line.get_label() for line in figure.axes[0].lines] == ["Mechanistic", "Hybrid"]
    plt.close(figure)


def test_v1_data_adapters_cover_all_public_templates() -> None:
    from axiomfig.intent import DATA_ADAPTERS
    from axiomfig.templates.registry import public_template_specs

    assert {spec.template_id for spec in public_template_specs()} == DATA_ADAPTERS


def test_matrix_intent_passes_explicit_center_to_heatmap() -> None:
    from axiomfig.intent import build_intent_figure, parse_figure_intent

    intent = parse_figure_intent(
        {
            "template": "heatmap.correlation",
            "data": {"matrix": "correlation", "labels": "variables"},
            "semantics": {"center": 0.0},
        }
    )
    figure = build_intent_figure(
        intent,
        {
            "correlation": [[1.0, -0.4], [-0.4, 1.0]],
            "variables": ["A", "B"],
        },
    )

    assert figure.axes[0].images[0].norm.vcenter == 0.0
    plt.close(figure)


def test_intent_cli_loads_data_and_uses_intent_geometry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    import axiomfig.cli as cli

    intent_path = tmp_path / "intent.yaml"
    data_path = tmp_path / "data.json"
    intent_path.write_text(
        "template: line.single\ndata: {x: time, y: value}\ngeometry: onehalf-column\n",
        encoding="utf-8",
    )
    data_path.write_text('{"time": [0, 1, 2], "value": [0.1, 0.4, 0.8]}', encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_render(figure: object, output: Path, **kwargs: object) -> object:
        captured["size"] = tuple(figure.get_size_inches())  # type: ignore[attr-defined]
        captured["output"] = output
        captured.update(kwargs)
        return SimpleNamespace(
            pdf=output.with_suffix(".pdf"),
            png=output.with_suffix(".png"),
            log=tmp_path / "render.log",
        )

    monkeypatch.setattr(cli, "discover_fonts", lambda mode: {})
    monkeypatch.setattr(cli, "render_figure", fake_render)
    monkeypatch.setattr(cli, "validate_pair", lambda *args, **kwargs: None)

    exit_code = cli.intent_main(
        [
            str(intent_path),
            "--data",
            str(data_path),
            "--output",
            str(tmp_path / "figure"),
        ]
    )

    assert exit_code == 0
    assert captured["geometry"] == "onehalf-column"
    assert captured["typography"] == "sans"
    assert captured["size"] == pytest.approx((140.0 / 25.4, 105.0 / 25.4))


def test_intent_cli_executes_one_real_data_contract_per_family(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    import axiomfig.cli as cli
    from axiomfig.anatomy import validate_figure_anatomy
    from axiomfig.evaluation import load_evaluation_cases, load_evaluation_fixtures

    selected = {
        "line/single",
        "scatter/parity",
        "bar/grouped",
        "distribution/violin",
        "heatmap/correlation",
        "estimation/forest",
        "diagnostics/roc",
        "ordination/pca_scores",
        "association/mantel",
        "flow/sankey",
        "field/contour",
        "omics/volcano",
        "survival/kaplan_meier",
    }
    cases = [case for case in load_evaluation_cases() if case.expected_template in selected]
    fixtures = load_evaluation_fixtures()
    rendered: list[str] = []

    def fake_render(figure: object, output: Path, **kwargs: object) -> object:
        figure.canvas.draw()  # type: ignore[attr-defined]
        validate_figure_anatomy(figure)  # type: ignore[arg-type]
        rendered.append(output.name)
        return SimpleNamespace(
            pdf=output.with_suffix(".pdf"),
            png=output.with_suffix(".png"),
            log=tmp_path / "render.log",
        )

    monkeypatch.setattr(cli, "discover_fonts", lambda mode: {})
    monkeypatch.setattr(cli, "render_figure", fake_render)
    monkeypatch.setattr(cli, "validate_pair", lambda *args, **kwargs: None)

    for case in cases:
        intent_path = tmp_path / f"{case.case_id}.yaml"
        data_path = tmp_path / f"{case.case_id}.json"
        intent_path.write_text(
            yaml.safe_dump(dict(case.figure_intent), sort_keys=False),
            encoding="utf-8",
        )
        data_path.write_text(
            json.dumps(dict(fixtures[case.fixture_id])),
            encoding="utf-8",
        )
        assert (
            cli.intent_main(
                [
                    str(intent_path),
                    "--data",
                    str(data_path),
                    "--output",
                    str(tmp_path / case.case_id),
                ]
            )
            == 0
        )

    assert len(cases) == 13
    assert len(rendered) == 13
