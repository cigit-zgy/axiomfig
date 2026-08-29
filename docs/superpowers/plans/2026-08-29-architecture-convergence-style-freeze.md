# AxiomFig Architecture Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user permits exactly one review and at most one repair, so do not substitute a workflow that adds per-task reviewer loops.

**Goal:** Replace the layered `.mplstyle` system with three canonical YAML files and freeze the requested deterministic scientific-figure contract in code, tests, documentation, and a two-family Gallery.

**Architecture:** Root-level YAML is the only maintained configuration source. A thin loader maps validated tokens to Matplotlib, four Python plot-family modules replace dynamic resource templates, and small helpers own geometry that rcParams cannot express.

**Tech Stack:** Python 3.11, PyYAML, Matplotlib, NumPy, fontTools, pypdf, Pillow, Tectonic, Poppler, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-29-architecture-convergence-design.md`

## Global Constraints

- Work in the explicitly approved current `master`; do not reset the unpushed history or the three pre-existing dirty Gallery files.
- Prefix Python commands with `PATH=/Users/wenv/miniforge3/bin:$PATH`.
- The only maintained style sources are `styles/style.yaml`, `styles/fonts.yaml`, and `styles/colors.yaml`.
- Do not add font binaries, new CJK/Japanese work, multilingual Gallery probes, or a TeX-native Matplotlib text pipeline.
- Use `main_stroke = 0.8 pt` and `fill_edge = 0.6 pt` exactly as specified.
- Keep real PDF E2E limited to canonical Gallery cases and the complete test pass near one minute.
- Perform one review and at most one repair pass. Any remaining Important finding blocks push.
- Write temporary artifacts only below ignored `tmp/`.

---

### Task 1: Canonical YAML and loader

**Files:**
- Create: `styles/style.yaml`
- Create: `styles/fonts.yaml`
- Create: `styles/colors.yaml`
- Create: `src/axiomfig/config.py`
- Modify: `pyproject.toml`
- Replace tests: `tests/test_styles.py`, `tests/test_colors.py`
- Delete: `src/axiomfig/resources/styles/**/*.mplstyle`

**Interfaces:**
- Produces: `Contracts`, `load_contracts()`, `build_rcparams()`, `get_token()`.
- Consumes: no project Python configuration source other than the three YAML files.

- [ ] **Step 1: Write failing loader behavior tests**

  Assert that exactly three YAML files exist, all obsolete `.mplstyle` files are absent,
  three geometries resolve to 90/140/190 mm at 4:3, sans/serif fixed point sizes are equal,
  and the default color cycle comes from `colors.yaml`.

- [ ] **Step 2: Verify RED**

  Run `python -m pytest -q tests/test_styles.py tests/test_colors.py`; expect failures from
  missing YAML and old resource ownership.

- [ ] **Step 3: Add minimal YAML and loader**

  Use this fixed schema:

  ```yaml
  version: 1
  geometry: {}
  typography: {}
  stroke: {}
  ticks: {}
  axes: {}
  legend: {}
  panel: {}
  plots: {}
  rendering: {}
  ```

  `config.py` loads with `yaml.safe_load`, freezes nested mappings, rejects missing mappings
  and non-finite/non-positive physical tokens, and returns a plain rcParams dictionary.

- [ ] **Step 4: Remove old style ownership and package root YAML**

  Delete every tracked `.mplstyle`, remove composition/conflict code, add PyYAML, and install
  the three root YAML files to `share/axiomfig/styles` without creating tracked duplicates.

- [ ] **Step 5: Verify GREEN**

  Re-run the targeted tests and build a wheel to prove installed commands locate the YAML.

### Task 2: Font contract and template convergence

**Files:**
- Modify: `src/axiomfig/typography.py`
- Replace: `src/axiomfig/templates.py` with `src/axiomfig/templates/__init__.py`
- Create: `src/axiomfig/templates/curves.py`
- Create: `src/axiomfig/templates/distributions.py`
- Create: `src/axiomfig/templates/surfaces.py`
- Create: `src/axiomfig/templates/panels.py`
- Delete: `src/axiomfig/resources/templates/*.py`
- Modify tests: `tests/test_typography.py`, `tests/test_templates.py`, `tests/test_packaged_cli.py`

**Interfaces:**
- Produces: exact Latin/math/mono discovery from `fonts.yaml` and `TEMPLATE_BUILDERS` backed by four imported modules.
- Consumes: `load_contracts()` and existing Figure return contract.

- [ ] **Step 1: Write failing font and registry tests**

  Assert sans=`Latin Modern Sans`, serif=`Latin Modern Roman`, math=`Latin Modern Math`,
  mono=`Maple Mono`; assert Arial, Times New Roman, SimSun, and Yu Gothic are optional and
  unbundled; assert only four template family modules serve the six canonical names.

- [ ] **Step 2: Verify RED**

  Run targeted typography/template/package tests and confirm failures arise from current
  hard-coded CJK contracts and dynamic resource modules.

- [ ] **Step 3: Implement exact YAML-driven font discovery**

  Preserve internal-family and exact-file checks. Default discovery resolves only Latin,
  math, and mono. Optional system families resolve only when explicitly requested. No
  fallback or binary copying is permitted.

- [ ] **Step 4: Merge templates by family**

  Move line/scatter builders to `curves.py`, bar/violin to `distributions.py`, heatmap to
  `surfaces.py`, and multi-panel to `panels.py`. Replace dynamic file imports with direct
  callable registry entries and remove obsolete archetypes from the public registry.

- [ ] **Step 5: Verify GREEN**

  Re-run targeted tests and an installed-wheel CLI smoke test.

### Task 3: Deterministic axis and artist contracts

**Files:**
- Modify: `src/axiomfig/contracts.py`
- Modify: `src/axiomfig/template_helpers.py`
- Modify tests: `tests/test_contracts.py`, `tests/test_plot_contract.py`

**Interfaces:**
- Produces: `nice_linear_axis()`, `apply_axis_contract()`, `apply_categorical_axis()`, `add_bar_value_labels()`, `apply_violin_contract()`, and `apply_scatter_contract()`.
- Consumes: stroke, tick, axis, and plot tokens from `Contracts`.

- [ ] **Step 1: Write failing numeric-axis and artist tests**

  Use hand-derived limits and steps for ordinary, exact-boundary, narrow, negative, and
  constant ranges. Assert 5--7 target ticks when feasible, allowed step mantissas, half-step
  minors, snapped limits, untouched log locators, black filled edges, 0.55 scatter alpha,
  configured marker size, and two-decimal bar labels.

- [ ] **Step 2: Characterize rendered tick geometry**

  Render a small Agg figure and measure the major `inout` line around the spine. Derive the
  minor `in` token from the observed inward projection and assert the physical ratio is
  `0.618` within raster tolerance.

- [ ] **Step 3: Verify RED**

  Run the targeted tests and retain the expected failure evidence.

- [ ] **Step 4: Implement minimal helpers**

  Candidate major steps are generated from literal mantissas `(1, 2, 2.5, 5)` and decimal
  exponents. Whole-step snapping is preferred; half-step snapping is selected only when
  whole snapping increases span beyond the configured blank-space threshold. Categorical
  helpers set tick length to zero without removing labels.

- [ ] **Step 5: Verify GREEN**

  Re-run the targeted tests, including the rendered tick-ratio characterization.

### Task 4: Legend, panel, and colorbar layout

**Files:**
- Modify: `src/axiomfig/template_helpers.py`
- Modify: `src/axiomfig/templates/panels.py`
- Modify tests: `tests/test_layout_contract.py`

**Interfaces:**
- Produces: `place_legend_above()`, `add_panel_labels()`, and a four-data-axes panel builder with a dedicated colorbar axes.

- [ ] **Step 1: Write failing layout tests**

  Cover single-series legend removal, normal one-row legend, exact axes-width boundary,
  overflow column reduction/error, right-spine alignment, 10 pt bold panel labels with equal
  physical offsets, equal data-axes boxes, and a colorbar that does not resize panel d.

- [ ] **Step 2: Verify RED**

  Run `python -m pytest -q tests/test_layout_contract.py` and confirm the current legend,
  panel x-offset, and colorbar layout fail the new contract.

- [ ] **Step 3: Implement measured deterministic layout**

  Set `legend.handlelength=1.0`, frame off, no top/right labels, right-align at a fixed point
  gap, and measure normal/boundary/overflow only. Use an outer GridSpec with a dedicated
  colorbar column and a nested equal-size data grid; disable layout engines that can shrink a
  single panel.

- [ ] **Step 4: Verify GREEN**

  Re-run layout tests at two DPIs to prove physical-offset and equal-box behavior.

### Task 5: Documentation and skill behavior

**Files:**
- Create: `references/latex-contract.md`
- Modify: `SKILL.md`, `README.md`, `references/style-contract.md`, `references/typography.md`, `references/layout.md`, `references/colors.md`, `references/templates.md`, `references/rendering-validation.md`
- Delete: `references/latex.md`

**Interfaces:**
- Produces: progressive-disclosure instructions matching the YAML contract and exact LaTeX macros.
- Consumes: one pre-edit baseline scenario and one post-edit forward test.

- [ ] **Step 1: Run the skill RED baseline**

  Give a fresh agent the current skill plus a realistic request that pressures it to invent
  rcParams, use a single-series legend, and claim `\qty` works in Matplotlib labels. Record
  the actual choices without giving the intended answer.

- [ ] **Step 2: Update the skill and references**

  Route configuration to the three YAML files, reduce the entrypoint, remove multilingual
  claims, document deferred CJK/Tectonic-native typography, and list exact macros:
  `\qty`, `\unit`, `\ce`, `\begin{align}`, `\symup`/`\symbf`, and `\textcolor`/`\definecolor`.

- [ ] **Step 3: Verify GREEN**

  Re-run an equivalent fresh-agent scenario with the updated skill. Require deterministic
  token lookup, no unsupported LaTeX claim, and no invented visual values.

- [ ] **Step 4: Validate skill structure**

  Run the system `quick_validate.py` and check every linked reference exists.

### Task 6: Canonical Gallery

**Files:**
- Modify: `src/axiomfig/gallery.py`, `src/axiomfig/validation.py`, `scripts/build_gallery.py`
- Modify tests: `tests/test_gallery.py`, `tests/test_validation.py`, `tests/test_rendering.py`
- Replace: `gallery/*` with `gallery/sans/*` and `gallery/serif/*`

**Interfaces:**
- Produces: exactly 24 files, six PDF/PNG pairs per typography directory.
- Consumes: the six canonical template names and fixed 90/140/190 mm geometry.

- [ ] **Step 1: Write failing Gallery registry tests**

  Assert both modes contain exactly `01_line` through `06_multi_panel`, every PDF has a PNG
  partner, and no CJK/multilingual stem remains.

- [ ] **Step 2: Verify RED**

  Run Gallery/validation tests without generating PDFs and confirm the old flat registry fails.

- [ ] **Step 3: Implement and rebuild canonical cases**

  Build all 12 figures through the existing Tectonic wrapper and rasterize PNG from each final
  PDF. Preserve English content and identical scientific data between sans and serif.

- [ ] **Step 4: Run PDF QA and visual inspection**

  Check physical size, embedded/subset non-Type-3 fonts, text/page bounds, strokes, tick
  directions and lengths, categorical axes, scatter alpha/size, bar labels, legends, panels,
  colorbar, symmetry, and sans/serif parity. Record evidence; do not call this automated QA.

### Task 7: Single deterministic pass, review, repair, and release

**Files:**
- Create only after refreshing date and sequence: `reports/agent/YYMMDD_agent_NN.md`

**Interfaces:**
- Produces: one bounded test result, one review result, at most one repair result, final QA evidence, report, and verified remote state.

- [ ] **Step 1: Run the one deterministic test pass**

  Time `python -m pytest -q`, run Ruff checks, font check, LaTeX check, Gallery validation,
  skill validation, and artifact scans. Record wall time and exact failure count.

- [ ] **Step 2: Run exactly one review**

  Review the diff against all 14 task sections and classify findings as Critical, Important,
  or Minor. Do not dispatch another reviewer.

- [ ] **Step 3: Apply at most one repair pass**

  For every Critical/Important finding, first add a failing regression test, then repair and
  run only the affected targeted checks. Do not recurse. Remaining Important blocks push.

- [ ] **Step 4: Run final validation**

  Re-run the complete acceptance commands and inspect the latest rendered PNGs. Scan for
  `tmp`, caches, build outputs, font binaries, obsolete `.mplstyle`, and dirty untracked files.

- [ ] **Step 5: Generate the Agent report**

  Immediately before creation, run `date +%y%m%d` and scan `reports/agent/` for that date's
  maximum two-digit sequence. Report architecture deletion, YAML schema, tokens, Gallery
  before/after, runtime, manual QA, and deferred CJK/Tectonic-native typography.

- [ ] **Step 6: Commit, push, and verify remote**

  Only when all gates pass, commit the complete bounded round, push `master`, fetch/read the
  remote tree, verify both Gallery directories and all pairs/report exist, verify no temporary
  artifacts are tracked, and prove `git rev-parse master == git rev-parse origin/master`.
