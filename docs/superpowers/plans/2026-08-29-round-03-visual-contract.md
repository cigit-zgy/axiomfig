# AxiomFig Round 03 Visual Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the Round 03 visual contract, bundle licensed Latin/math fonts, and publish matching twenty-figure sans and serif galleries.

**Architecture:** Preserve the three YAML files as the only visual roots, extend the existing thin consumers and four template-family modules, and centralize final layout/export behavior. Matplotlib produces vector content, Tectonic finalizes the PDF container, and Poppler derives every PNG from that PDF.

**Tech Stack:** Python 3.11+, Matplotlib, NumPy, PyYAML, fontTools, pypdf, Tectonic, Poppler, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-29-round-03-visual-contract-design.md`

## Global Constraints

- Work directly on the clean current `master`; do not create a branch or environment.
- Use `/Users/wenv/miniforge3/bin` first on `PATH`.
- Do not add CJK/Japanese work, TeX-native Matplotlib text, brute-force probes, or a large configuration framework.
- Keep `styles/style.yaml`, `styles/fonts.yaml`, and `styles/colors.yaml` as the only visual configuration sources.
- Run one implementation/build pass, one review, at most one repair, and one final validation.
- Do not push until tests, Gallery inspection, report generation, and repository hygiene checks pass.

---

### Task 1: Freeze configuration and asset contracts

**Files:**
- Modify: `styles/style.yaml`
- Modify: `styles/fonts.yaml`
- Modify: `styles/colors.yaml`
- Create: `fonts/` open-font assets and `fonts/licenses/` attribution
- Modify: `src/axiomfig/config.py`
- Modify: `src/axiomfig/typography.py`
- Modify: `src/axiomfig/colors.py`
- Test: `tests/test_styles.py`, `tests/test_typography.py`, `tests/test_colors.py`

**Interfaces:**
- Produces: bundled-first font resolution, validated output margin tokens, five named palettes, and deterministic `render_xcolor()`.

- [ ] Add failing behavioral tests for the new serif family, bundled asset resolution, output modes, required palettes, token names, and xcolor output.
- [ ] Run the targeted tests and confirm failures identify missing Round 03 behavior.
- [ ] Add verified open assets/licenses and update the three YAML contracts.
- [ ] Implement only the loader/resolver changes required by the tests.
- [ ] Run the targeted tests and confirm they pass.

### Task 2: Correct layout and plot-family behavior

**Files:**
- Modify: `src/axiomfig/template_helpers.py`
- Modify: `src/axiomfig/templates/curves.py`
- Modify: `src/axiomfig/templates/distributions.py`
- Modify: `src/axiomfig/templates/surfaces.py`
- Modify: `src/axiomfig/templates/panels.py`
- Modify: `src/axiomfig/templates/__init__.py`
- Test: `tests/test_layout_contract.py`, `tests/test_plot_contract.py`, `tests/test_templates.py`

**Interfaces:**
- Produces: plot-type tick application, centralized margin fitting, twenty builder names, and a 2x2 multi-panel with a panel-(d)-only colorbar.

- [ ] Add failing tests for bar/violin numeric tick direction, heatmap outward ticks, legend gap, panel offsets, twenty registry names, equal panel boxes, and colorbar bounds.
- [ ] Run targeted tests and verify the expected contract failures.
- [ ] Implement minimal helper and family changes, keeping constants in YAML.
- [ ] Run targeted tests, then refactor duplication while staying green.

### Task 3: Publish generic LaTeX infrastructure

**Files:**
- Create: `latex/axiomfig.sty`
- Create: `latex/axiomfig-colors.tex`
- Create: `latex/README.md`
- Modify: `src/axiomfig/resources/latex/axiomfig.sty`
- Modify: `src/axiomfig/resources/latex/axiomfig-colors.tex`
- Modify: `src/axiomfig/latex.py`
- Modify: `references/latex-contract.md`
- Test: `tests/test_latex.py`

**Interfaces:**
- Produces: matching source/package LaTeX resources and a verified Tectonic probe using generic macros only.

- [ ] Add a failing test that compares repository and packaged resources and checks XCharter Math in the serif probe.
- [ ] Run it and confirm the root infrastructure is missing.
- [ ] Generate/copy the generic package resources and update the probe contract.
- [ ] Run the test and the real Tectonic probe.

### Task 4: Expand and render the canonical Gallery

**Files:**
- Modify: `src/axiomfig/gallery.py`
- Modify: `scripts/build_gallery.py`
- Modify: `tests/test_gallery.py`, `tests/test_rendering.py`, `tests/test_validation.py`
- Replace: `gallery/sans/*`, `gallery/serif/*`

**Interfaces:**
- Produces: exactly twenty matching PDF/PNG pairs per typography mode and representative Tectonic evidence.

- [ ] Add failing Gallery-set and representative-render tests.
- [ ] Run them and confirm the old six-case suite fails.
- [ ] Expand `GALLERY_SPECS`, rebuild all final PDFs and PDF-derived PNGs, and validate the exact set.
- [ ] Render contact sheets and inspect every image, with enlarged checks of `20_multi_panel` and representative tick/legend/panel cases.

### Task 5: Update skill documentation and validate behavior

**Files:**
- Modify: `SKILL.md`, `README.md`
- Modify/Create: `references/style-contract.md`, `references/template-contract.md`, `references/typography.md`, `references/colors.md`, `references/rendering-validation.md`, `references/layout.md`
- Test: isolated skill baseline/forward scenarios and `quick_validate.py`

**Interfaces:**
- Produces: concise discoverable instructions that route future agents to the exact maintained contracts.

- [ ] Record an isolated baseline scenario without the skill and its observable failure.
- [ ] Update instructions and references from the implemented behavior, including the four README previews.
- [ ] Run the same isolated scenario with the skill and verify it follows the canonical builder/config path.
- [ ] Run the skill validator and fix only demonstrated issues.

### Task 6: One review, report, and release validation

**Files:**
- Create: `reports/agent/YYMMDD_agent_NN.md` after refreshing date and scanning numbers.
- Modify: only files required by the single repair pass, if review finds Critical/Important defects.

**Interfaces:**
- Produces: reviewed commit on `master`, pushed and verified against `origin/master`.

- [ ] Run pytest, Ruff check/format, color generation check, font checks, Gallery validation, representative Tectonic probes, PDF font/bbox checks, and hygiene scans.
- [ ] Perform exactly one deterministic code/visual review; if required, make one bounded repair and rebuild Gallery once.
- [ ] Inspect the final Gallery again, refresh the system date, scan report numbering, and write the required report.
- [ ] Re-run the complete final verification, commit, push `master`, fetch/read remote state, and verify local `master == origin/master` plus all remote artifact paths.
