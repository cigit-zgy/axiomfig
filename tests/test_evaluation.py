from __future__ import annotations


def test_v1_evaluation_has_one_true_data_case_per_public_template() -> None:
    from axiomfig.templates.registry import public_template_specs
    from tests.evaluation.run import load_evaluation_cases, load_evaluation_fixtures

    cases = load_evaluation_cases()
    fixtures = load_evaluation_fixtures()
    ids = [case.case_id for case in cases]
    public_ids = {spec.template_id for spec in public_template_specs()}

    assert len(cases) == len(public_ids)
    assert len(ids) == len(set(ids))
    assert {case.expected_template for case in cases} == public_ids
    assert all(case.fixture_id in fixtures for case in cases)
    assert all(case.expected_validation == "pass" for case in cases)


def test_routing_evaluation_is_reported_separately() -> None:
    from tests.evaluation.run import run_evaluation

    result = run_evaluation(render=False)
    from axiomfig.templates.registry import public_template_specs

    expected = len(public_template_specs())

    assert result.case_count == expected
    assert result.routing_passed == expected
    assert result.routing_rate == 1.0
    assert result.canonical_rendered == 0
    assert result.external_rendered == 0
    assert result.runtime_validated == 0
    assert result.discovery.registry_bytes > 0
    assert result.discovery.skill_bytes > 0
    assert result.discovery.representative_intent_bytes > 0


def test_true_data_evaluation_separates_render_validation_and_repeatability() -> None:
    from axiomfig.gallery import GALLERY_SPECS
    from axiomfig.templates.registry import public_template_specs
    from tests.evaluation.run import run_evaluation

    result = run_evaluation(render=True)
    expected = len(public_template_specs())

    assert result.canonical_rendered == expected
    assert result.canonical_passed == expected
    assert result.canonical_render_rate == 1.0
    assert result.external_rendered == expected
    assert result.external_passed == expected
    assert result.external_render_rate == 1.0
    assert result.runtime_validated == expected
    assert result.runtime_validation_passed == expected
    assert result.runtime_validation_rate == 1.0
    assert result.repeatability_cases == 7
    assert result.repeatability_passed == 7
    assert result.repeatable
    assert result.gallery_templates_expected == len(GALLERY_SPECS)
    assert result.gallery_templates_present == len(GALLERY_SPECS)
    assert result.gallery_coverage_rate == 1.0
