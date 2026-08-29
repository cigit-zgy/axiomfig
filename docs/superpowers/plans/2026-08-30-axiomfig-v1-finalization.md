# AxiomFig v1 Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all 55 frozen public templates executable through real external-data Figure Intent,
evaluate that path truthfully, and freeze the verified v1 state on `master`.

**Architecture:** Keep `intent.py` thin by routing resolved roles to explicit family adapters, then
pass normalized kwargs to the existing canonical builders. Use one compact fixture corpus to drive
55 true intent builds and separate routing, canonical, external, validation, repeatability, and
Gallery metrics.

**Tech Stack:** Python 3.11+, NumPy, Matplotlib, PyYAML, pytest, Ruff, Tectonic, Poppler.

**Spec:** `docs/superpowers/specs/2026-08-30-axiomfig-v1-finalization-design.md`

## Global Constraints

- Work directly on `master`; do not create a branch or conda environment.
- Keep exactly 55 public templates and the existing Gallery taxonomy.
- Do not change visual tokens or validation thresholds unless true data exposes a correctness bug.
- Do not compute regression, clustering, ordination, Mantel, adjusted-p, interval, or survival science.
- Use `apply_patch` for source edits and TDD for every behavior change.
- Run targeted tests during work and one full local release gate before completion.

---

### Task 1: Freeze operability contracts

**Files:**
- Modify: `src/axiomfig/templates/*/contract.yaml`
- Test: `tests/test_intent.py`

**Interfaces:**
- Consumes: `public_template_specs()` and `load_family_contract(family)`.
- Produces: 55 explicit contracts matching `references/figure-intent-coverage.md`.

- [ ] Add a parameterized test asserting every public template has an A/B class, required roles,
      and no canonical-only state; verify it fails on the 12/55 baseline.
- [ ] Align only inconsistent role names: multi-series values/labels, precomputed density,
      clustered row/column order, Mantel/network structure, Sankey value, contour grid/z, generic
      omics fields, and survival-ready optional inputs.
- [ ] Re-run the contract test and registry tests until green.

### Task 2: Add explicit family adapters

**Files:**
- Create: `src/axiomfig/data_adapters/__init__.py`
- Create: `src/axiomfig/data_adapters/_shared.py`
- Create: `src/axiomfig/data_adapters/{line,scatter,bar,distribution,heatmap,estimation,diagnostics,ordination,association,flow,field,omics,survival}.py`
- Modify: `src/axiomfig/intent.py`
- Test: `tests/test_intent.py`

**Interfaces:**
- Produces: `adapt_template_data(template_id: str, values: Mapping[str, object]) -> dict[str, object]`,
  `DATA_ADAPTERS`, and `OPERABILITY`.

- [ ] Add failing tests that `DATA_ADAPTERS` exactly equals all 55 public IDs, the class counts are
      A=28/B=27/C=0, malformed equal-length/matrix/structured inputs fail, and extra fields fail.
- [ ] Implement shared finite array, matrix, label, coordinate, interval, and structured-edge checks.
- [ ] Implement 13 explicit family dispatchers and make `build_intent_figure()` resolve, adapt, and
      pass all supplied roles without silently dropping any.
- [ ] Run intent tests and verify both valid and invalid paths are green.

### Task 3: Make the 55 canonical builders data-bearing

**Files:**
- Modify: `src/axiomfig/templates/{line,scatter,bar,distribution,heatmap,estimation,diagnostics,ordination,association,flow,field,omics,survival}/builders.py`
- Test: `tests/test_intent.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: normalized adapter kwargs using exact contract role names.
- Produces: every registered public builder accepts either zero kwargs or one complete external set.

- [ ] Add a 55-case fixture-driven test that calls `build_intent_figure()` and verifies every ID
      reaches a real Figure; confirm failure before builder changes.
- [ ] Extend builders family-by-family while preserving the no-argument canonical paths byte-for-byte
      in visual intent and rejecting partial parameter sets.
- [ ] Run family-targeted tests after each family and registry/template tests after all families.

### Task 4: Replace the illustrative Evaluation with true data execution

**Files:**
- Replace: `evaluation/cases.yaml`
- Create: `evaluation/fixtures.yaml`
- Modify: `src/axiomfig/evaluation.py`
- Modify: `pyproject.toml`
- Test: `tests/test_evaluation.py`

**Interfaces:**
- Produces: 55 `EvaluationCase` objects with `fixture_id` and an `EvaluationResult` containing
  separate routing, canonical, external, validation, repeatability, and Gallery metrics.

- [ ] Add failing tests for 55 unique public IDs, packaged fixtures, separate 55/55 metrics, true
      `build_intent_figure()` execution, seven stable repeatability templates, and Gallery coverage.
- [ ] Add compact shared deterministic fixtures and load them from repo or installed package data.
- [ ] Implement separate metric counters; run anatomy validation on all external figures and optional
      PDF/PNG release rendering without collapsing failures into one pass rate.
- [ ] Run evaluation tests and one full 55-template external canvas evaluation.

### Task 5: Close CLI, package, and CI paths

**Files:**
- Modify: `tests/test_packaged_cli.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `references/figure-intent.md`
- Modify: `references/template-knowledge/index.yaml`

**Interfaces:**
- Consumes: installed fixture resources and the unchanged `axiomfig-intent` CLI.
- Produces: exact public claims and 7-template fast-CI data smoke coverage.

- [ ] Add failing installed-wheel CLI tests for one external flow per family and verify invalid input
      returns a clear nonzero failure.
- [ ] Package `evaluation/fixtures.yaml`, add a fast 7-template external-data smoke command to CI,
      and keep full 55-PDF validation release-only.
- [ ] Expand Knowledge routes to cover all 55 IDs without enlarging the normal Skill path; update
      README/SKILL/contracts to state 55 external paths, 28 direct and 27 precomputed.
- [ ] Run packaged CLI, release-readiness, Skill, and documentation tests.

### Task 6: Freeze and publish the validated master state

**Files:**
- Create: `reports/agent/YYMMDD_agent_NN.md`
- Modify: this plan checklist only after evidence passes.

**Interfaces:**
- Produces: one report, coherent commits, exact-commit CI, and local/origin/GitHub SHA equality.

- [ ] Run all 55 external-data PDF/PNG Evaluation cases and validate every pair.
- [ ] Validate the unchanged canonical Gallery, fonts, Tectonic, styles, Skill, and repository hygiene.
- [ ] Run isolated wheel and GitHub fresh-clone representative E2E across all 13 families.
- [ ] Run exactly one final `python -m pytest -q`, `ruff check .`, and `ruff format --check .`.
- [ ] Determine report date/sequence from the filesystem, write the final report, commit, and push.
- [ ] Wait for CI on the exact report commit, then verify clean tree and local/origin/GitHub SHA equality.
