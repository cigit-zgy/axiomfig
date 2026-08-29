from __future__ import annotations


def test_v1_evaluation_has_24_unique_representative_cases() -> None:
    from axiomfig.evaluation import load_evaluation_cases

    cases = load_evaluation_cases()
    ids = [case.case_id for case in cases]
    expected_intents = {
        "trend",
        "comparison",
        "distribution",
        "relationship",
        "uncertainty",
        "model_evaluation",
        "matrix",
        "ordination",
        "association",
        "flow",
        "field",
        "omics",
        "survival",
        "composition",
    }

    assert len(cases) == 24
    assert len(ids) == len(set(ids))
    assert {case.scientific_intent for case in cases} == expected_intents
    assert all(case.request.strip() for case in cases)


def test_evaluation_cases_agree_with_knowledge_registry_and_intent_contract() -> None:
    from axiomfig.evaluation import run_evaluation

    result = run_evaluation(render=False)

    assert result.case_count == 24
    assert result.passed == 24
    assert result.pass_rate == 1.0
    assert result.discovery.registry_bytes > 0
    assert result.discovery.skill_bytes > 0
    assert result.discovery.representative_intent_bytes > 0


def test_render_evaluation_is_repeatable_and_includes_mixed_layout() -> None:
    from axiomfig.evaluation import run_evaluation

    result = run_evaluation(render=True)

    assert result.rendered_templates >= 20
    assert result.render_success_rate == 1.0
    assert result.repeatable
    assert result.mixed_layout_passed
