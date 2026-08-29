from __future__ import annotations


def test_v1_evaluation_has_one_true_data_case_per_public_template() -> None:
    from axiomfig.evaluation import load_evaluation_cases, load_evaluation_fixtures
    from axiomfig.templates.registry import public_template_specs

    cases = load_evaluation_cases()
    fixtures = load_evaluation_fixtures()
    ids = [case.case_id for case in cases]
    public_ids = {spec.template_id for spec in public_template_specs()}

    assert len(cases) == 55
    assert len(ids) == len(set(ids))
    assert {case.expected_template for case in cases} == public_ids
    assert all(case.fixture_id in fixtures for case in cases)
    assert all(case.expected_validation == "pass" for case in cases)


def test_routing_evaluation_is_reported_separately() -> None:
    from axiomfig.evaluation import run_evaluation

    result = run_evaluation(render=False)

    assert result.case_count == 55
    assert result.routing_passed == 55
    assert result.routing_rate == 1.0
    assert result.canonical_rendered == 0
    assert result.external_rendered == 0
    assert result.runtime_validated == 0
    assert result.discovery.registry_bytes > 0
    assert result.discovery.skill_bytes > 0
    assert result.discovery.representative_intent_bytes > 0


def test_true_data_evaluation_separates_render_validation_and_repeatability() -> None:
    from axiomfig.evaluation import run_evaluation

    result = run_evaluation(render=True)

    assert result.canonical_rendered == 55
    assert result.canonical_passed == 55
    assert result.canonical_render_rate == 1.0
    assert result.external_rendered == 55
    assert result.external_passed == 55
    assert result.external_render_rate == 1.0
    assert result.runtime_validated == 55
    assert result.runtime_validation_passed == 55
    assert result.runtime_validation_rate == 1.0
    assert result.repeatability_cases == 7
    assert result.repeatability_passed == 7
    assert result.repeatable
    assert result.gallery_templates_expected == 55
    assert result.gallery_templates_present == 55
    assert result.gallery_coverage_rate == 1.0
