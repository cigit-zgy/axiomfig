from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import yaml


def _corpus() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    root = Path(__file__).resolve().parents[1]
    cases_document = yaml.safe_load((root / "evaluation/cases.yaml").read_text(encoding="utf-8"))
    fixture_document = yaml.safe_load(
        (root / "evaluation/fixtures.yaml").read_text(encoding="utf-8")
    )
    return cases_document["cases"], fixture_document["fixtures"]


def test_every_public_template_executes_true_external_data_intent() -> None:
    from axiomfig.anatomy import validate_figure_anatomy
    from axiomfig.intent import build_intent_figure, parse_figure_intent
    from axiomfig.templates.registry import public_template_specs

    cases, fixtures = _corpus()
    public_ids = {spec.template_id for spec in public_template_specs()}
    case_ids = {str(case["expected_template"]).replace(".", "/") for case in cases}

    assert len(cases) == 55
    assert case_ids == public_ids

    completed: list[str] = []
    for case in cases:
        template_id = str(case["expected_template"]).replace(".", "/")
        intent = parse_figure_intent(case["figure_intent"])
        dataset = fixtures[str(case["fixture"])]
        figure = build_intent_figure(intent, dataset)
        try:
            figure.canvas.draw()
            validate_figure_anatomy(figure)
            completed.append(template_id)
        finally:
            plt.close(figure)

    assert set(completed) == public_ids
