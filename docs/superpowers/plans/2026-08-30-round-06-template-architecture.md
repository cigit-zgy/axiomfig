# Round 06 Canonical Template Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan inline. Subagent delegation is not authorized for this task.

**Goal:** Replace the four coarse template modules and flat Gallery with a compact canonical
scientific taxonomy, registry-driven rendering, and a PrimaryAxes-frame panel-label anchor.

**Architecture:** `templates/index.yaml` is the small discovery/Gallery source; each family owns a
plain builder mapping and `contract.yaml`; `templates/registry.py` validates their exact agreement.
Layouts remain registered non-public composition capabilities. Gallery renders only public specs
and derives every path from the template ID.

**Tech Stack:** Python 3.11+, Matplotlib, PyYAML, pytest, Ruff, Tectonic, Poppler.

**Spec:** `docs/superpowers/specs/2026-08-30-round-06-template-architecture-design.md`

## Global constraints

- Work directly on `master`; create no branch or environment.
- Use `/Users/wenv/miniforge3/bin` first in `PATH`.
- Preserve Round 05 layout, ornament, anatomy, colorbar, legend, and PDF-boundary gates.
- Run targeted tests during implementation and the full pytest suite only once at final validation.
- Perform one visual review and at most one repair pass.
- Do not add recommendation knowledge, orchestration, CJK, interactive, animation, or broad 3D work.

### Task 1: RED registry, taxonomy, and Gallery contracts

**Files:**
- Replace: `tests/test_templates.py`
- Replace: `tests/test_gallery.py`
- Modify: `tests/test_packaged_cli.py`
- Modify: `tests/test_layout_contract.py`

**Interfaces:**
- `load_template_registry() -> tuple[TemplateSpec, ...]`
- `public_template_specs() -> tuple[TemplateSpec, ...]`
- `expected_gallery_stems() -> tuple[str, ...]`

- [ ] Assert the nine scientific families and separate layouts section parse from `index.yaml`.
- [ ] Assert globally unique `family/variant` IDs, contracts for all families, resolvable builders,
  exact contract/registry/builder agreement, and no old coarse modules.
- [ ] Assert 33 public templates, first-class `association/mantel`, and real `field/contour`.
- [ ] Assert sans/serif Gallery projections match, technical probes are semantic and isolated, and
  numbered flat artifacts are rejected.
- [ ] Assert the clean wheel contains registry/contracts/new family modules and none of the old four.
- [ ] Replace footprint-anchor checks with PrimaryAxes-frame bbox checks at the central `-1/+1 pt`.
- [ ] Run only these changed tests and record the expected RED failures.

### Task 2: Canonical family packages and registry

**Files:**
- Create: `src/axiomfig/templates/registry.py`
- Create: `src/axiomfig/templates/index.yaml`
- Create: `src/axiomfig/templates/{line,scatter,bar,distribution,heatmap,estimation,diagnostics,association,field,layouts}/`
- Replace: `src/axiomfig/templates/__init__.py`
- Delete: `src/axiomfig/templates/{curves,distributions,surfaces,panels}.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Every package exports `BUILDERS: dict[str, Callable[..., Figure]]`.
- Every contract declares `family` and `variants` with required/optional/explicit semantic fields.
- Registry specs own `template_id`, `family`, `variant`, `geometry`, and `public`.

- [ ] Extract existing builders without changing deterministic example behavior or central styles.
- [ ] Add native-Matplotlib `association/mantel` with explicit precomputed link semantics.
- [ ] Add deterministic 2D `field/contour` with central sequential color semantics and colorbar.
- [ ] Keep the four layout builders registered under non-public `layouts/*` IDs.
- [ ] Add registry parsing and validation with explicit imports and actionable errors.
- [ ] Package all YAML registry/contracts as package data.
- [ ] Run registry/template/package targeted tests until GREEN.
- [ ] Commit and push the architecture checkpoint.

### Task 3: PrimaryAxes-frame panel labels

**Files:**
- Modify: `styles/style.yaml`
- Modify: `src/axiomfig/layout.py`
- Modify: `src/axiomfig/ornaments.py`
- Modify: `src/axiomfig/anatomy.py`
- Modify: `tests/test_layout_contract.py`

**Interfaces:**
- Panel anchor = PrimaryAxes bbox upper-left.
- Bbox/anchor translation = `left_offset_pt=-1`, `top_offset_pt=1`.
- Outer footprint reserves measured label height without label-driven post-placement movement.

- [ ] Change the central physical token once; add no per-template values.
- [ ] Reserve a shared measured label gutter in the layout solve.
- [ ] Create/refresh labels from the final PrimaryAxes position.
- [ ] Validate bbox-to-spine offsets, ownership, containment, and legend collision.
- [ ] Measure 2x2, 2x3, and 3x2 before/after values and run layout/anatomy tests until GREEN.

### Task 4: Registry-driven Gallery and CLI

**Files:**
- Replace: `src/axiomfig/gallery.py`
- Modify: `src/axiomfig/cli.py`
- Modify: `src/axiomfig/latex.py`
- Modify: `tests/test_gallery.py`
- Rebuild: `gallery/`

**Interfaces:**
- `GallerySpec` is derived from each public `TemplateSpec`.
- Output stem = `<mode>/<family>/<variant>`.
- Technical output = `technical/latex/{scientific_typography,palettes}`.

- [ ] Remove the hard-coded flat Gallery list and generate specs from the registry.
- [ ] Make Gallery preparation reject unknown files and recreate only the canonical tree.
- [ ] Rename technical probe stems and paths semantically.
- [ ] Update CLI choices and exact expected-stem validation from the registry API.
- [ ] Run Gallery unit tests, then rebuild all 68 canonical pairs once.
- [ ] Validate exact PDF/PNG sets, dimensions, embedded fonts, logs, boundaries, and no orphans.
- [ ] Commit and push the Gallery checkpoint.

### Task 5: Documentation, one visual review, and one repair gate

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Replace: `references/template-contract.md`
- Create: `references/template-taxonomy.md`

- [ ] Document the registry-first execution path, layout separation, contract semantics, Gallery
  invariant, 33 implemented templates, and deferred variants without recommendation prose.
- [ ] Inspect representative sans/serif line, scatter, bar, distribution, heatmap, estimation,
  diagnostics, Mantel, and field PNGs plus separately rendered 2x2/2x3/3x2 layouts.
- [ ] Compare one old and one new multi-panel image and record label geometry.
- [ ] If one review finds Important defects, perform one repair pass and rebuild affected canonical
  artifacts; otherwise proceed without iterative tuning.

### Task 6: Final validation, report, commits, and remote proof

**Files:**
- Create: `reports/agent/YYMMDD_agent_NN.md` after a fresh date/sequence scan.

- [ ] Read `basic-rule.md` from its actual project-level location before reporting.
- [ ] Run Ruff check and format check, quick skill validation, exact Gallery validation, artifact
  hygiene checks, and the full pytest suite exactly once; record wall time and slowest tests.
- [ ] Re-read system date and report sequence, then write the report with every required Round 06
  field, migrated/planned table, counts, measured label root cause, and remaining limitations.
- [ ] Run `git diff --check`, inspect intended changes, commit final documentation/validation, and
  push `master`.
- [ ] Fetch and verify local `master == origin/master == GitHub master`, remote Gallery trees,
  report presence, and absence of tmp/cache/build artifacts.
- [ ] Print only the exact Round 06 final stdout schema.
