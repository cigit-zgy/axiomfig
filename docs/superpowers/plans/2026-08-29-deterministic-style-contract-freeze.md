# Deterministic Style Contract Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the Round 02 AxiomFig visual, typography, palette, layout, and validation contracts and regenerate ten verified gallery pairs.

**Architecture:** Keep native `.mplstyle` files and Matplotlib templates. Add only small contract, palette, layout, and LaTeX-probe helpers where rcParams cannot express the required behavior; keep the stable vector-PDF-to-Tectonic renderer unless a real TeX-native text experiment proves reliable.

**Tech Stack:** Python 3.11 conda base, Matplotlib, NumPy, fontTools, pypdf, Tectonic, Poppler, pytest, Ruff, LaTeX (`xcolor`, `siunitx`, `mhchem`, `amsmath`, `unicode-math`).

**Spec:** `/Users/wenv/.codex/attachments/7af0cb50-66f5-4e34-a799-136445f74616/pasted-text.txt`

## Global Constraints

- Work directly on `master`; do not create a branch or environment.
- Prefix local Python commands with `PATH=/Users/wenv/miniforge3/bin:$PATH`.
- AxiomFig must not require uv or conda; official commands use plain `python` and `ruff`.
- Preserve the native Matplotlib template architecture and the existing stable renderer unless the TeX-native experiment passes.
- Use one central stroke token: `0.6 pt`.
- Default typography is sans; each figure selects exactly one complete sans or serif family.
- Write temporary outputs only under ignored `tmp/`; gallery contains final PDF/PNG pairs only.
- Use TDD for production behavior and record genuine TeX-native failures without monkey patches.

---

### Task 1: Environment and execution contract

**Files:**
- Modify: `README.md`, `SKILL.md`, `references/rendering-validation.md`, `references/typography.md`
- Delete: `uv.lock`

**Interfaces:**
- Consumes: standard `pyproject.toml` metadata and repo-local scripts.
- Produces: official plain-Python commands independent of the user's environment manager.

- [ ] Verify conda-base Python and external executables; install only missing runtime/test dependencies into the existing base or with Homebrew.
- [ ] Run the current test suite from conda base to establish the baseline.
- [ ] Replace required `uv run` commands with `python`/`ruff`; retain environment-manager neutrality.
- [ ] Verify the documented commands resolve from conda base.

### Task 2: Central stroke, tick, and palette contracts

**Files:**
- Create: `src/axiomfig/contracts.py`, `src/axiomfig/colors.py`, `scripts/generate_colors.py`, `latex/axiomfig-colors.tex`
- Modify: `styles/base/publication.mplstyle`, `styles/colors/*.mplstyle`, `styles/plot/*.mplstyle`, `src/axiomfig/styles.py`
- Test: `tests/test_contracts.py`, `tests/test_colors.py`, `tests/test_styles.py`

**Interfaces:**
- Produces: `STROKE_WIDTH_PT: float = 0.6`, `PALETTES`, `render_mplstyle(name) -> str`, and `render_xcolor() -> str`.

- [ ] Write failing behavior tests for equal stroke rcParams, open/filled tick ownership, and exact Matplotlib/xcolor RGB parity.
- [ ] Run targeted tests and confirm failures are caused by the missing Round 02 contract.
- [ ] Implement the constants and deterministic palette generator; generate committed style/xcolor artifacts from one source.
- [ ] Normalize all default visible stroke widths to 0.6 pt and declare only required style overrides.
- [ ] Run targeted tests to green and refactor without adding abstraction.

### Task 3: Deterministic axes, panels, legends, bars, and scatter

**Files:**
- Modify: `src/axiomfig/template_helpers.py`, `templates/*.py`
- Test: `tests/test_layout_contract.py`, `tests/test_plot_contract.py`, `tests/test_templates.py`

**Interfaces:**
- Produces: `apply_axis_contract(axis, surface='open')`, `add_panel_labels(axes, gap_pt=2.0)`, `place_legend_above(axis, gap_pt=2.0)`, `add_bar_value_labels(axis, containers, decimals=2)`, and `apply_scatter_contract(collection)`.

- [ ] Write failing tests for one linear minor tick per major interval, open/filled directions, uniform physical panel offsets, right-aligned responsive legends, black bar/scatter edges, 0.6 pt edges, and fixed-decimal bar labels.
- [ ] Run the targeted tests and confirm expected RED behavior.
- [ ] Implement the minimal helpers with physical-point transforms and rendered-width legend fallback.
- [ ] Update existing templates to use the helpers; expose `decimals: int = 2` on bar builders.
- [ ] Run the targeted suite to green and check that templates still leave global rcParams unchanged.

### Task 4: Complete sans, serif, math, CJK, and mono typography

**Files:**
- Modify: `src/axiomfig/typography.py`, `styles/typography/sans.mplstyle`, `styles/language/multilingual.mplstyle`
- Create: `styles/typography/serif.mplstyle`
- Test: `tests/test_typography.py`

**Interfaces:**
- Produces: `discover_fonts(mode='sans')`, `font_for_language(language, mode='sans')`, and exact role mappings for Latin, math, Chinese, Japanese, and mono.

- [ ] Write failing tests for Fira Math sans mode, Latin Modern Math serif mode, Latin Modern Roman/Noto Serif CJK serif mode, Maple Mono, and hard failure on cross-family fallback.
- [ ] Run tests to verify RED.
- [ ] Register and validate exact font files/families and make typography mode explicit through rendering/gallery/template helpers.
- [ ] Run typography and template tests to green; inspect actual PDF font names for both modes.

### Task 5: LaTeX scientific infrastructure and hard investigation

**Files:**
- Create: `latex/axiomfig.sty`, `scripts/check_latex.py`, `src/axiomfig/latex.py`, `tests/test_latex.py`
- Modify: `src/axiomfig/rendering.py`, `references/rendering-validation.md`

**Interfaces:**
- Produces: a generic package loading `xcolor`, `siunitx`, `mhchem`, `amsmath`, and `unicode-math`, plus `compile_latex_probe(output_dir) -> LatexProbeResult`.

- [ ] Write a failing E2E test that compiles units, chemistry, and math through Tectonic and extracts expected PDF text.
- [ ] Verify the current wrapper cannot interpret Matplotlib label macros and record the exact failure or literal-text behavior.
- [ ] Implement the minimal standalone LaTeX probe and compile the shared `.sty` with Tectonic.
- [ ] Experiment with a genuine Matplotlib-text-to-Tectonic route without alternate engines or monkey patches.
- [ ] Keep the stable renderer if the experiment is unreliable; encode the semantic boundary in tests and references.

### Task 6: Serif and style-contract gallery cases

**Files:**
- Create: `templates/style_contract.py`
- Modify: `templates/multilingual.py`, `src/axiomfig/templates.py`, `src/axiomfig/gallery.py`, `tests/test_gallery.py`

**Interfaces:**
- Produces: gallery stems `09_serif` and `10_style_contract` and typography-aware `GallerySpec`.

- [ ] Write failing gallery-registry and serif/style-contract E2E assertions.
- [ ] Implement the serif sample and 2x2 contract sample without adding unrelated templates.
- [ ] Rebuild all ten PDF/PNG pairs through Tectonic and run deterministic validation.
- [ ] Inspect PDF dimensions, fonts, text, Type 3 absence, bbox, and gallery-only file set.
- [ ] Visually inspect all regenerated PDFs, with emphasis on 08-10, and fix only evidenced defects through new regression tests.

### Task 7: Skill pressure tests and documentation

**Files:**
- Modify: `SKILL.md`, `README.md`, `references/style-contract.md`, `references/typography.md`, `references/templates.md`, `references/rendering-validation.md`
- Create only if needed: `references/colors.md`, `references/layout.md`, `references/latex.md`

**Interfaces:**
- Consumes: baseline pressure-test failures from the pre-edit skill.
- Produces: concise progressive-disclosure routing for the frozen contracts.

- [ ] Record three baseline scenarios without the Round 02 skill changes.
- [ ] Update the skill and linked references to address the observed ambiguity while keeping `SKILL.md` concise.
- [ ] Re-run equivalent fresh-context scenarios and confirm deterministic choices and honest LaTeX boundary reporting.
- [ ] Run `quick_validate.py` and check documentation contains no required uv workflow.

### Task 8: Full verification, report, and Git delivery

**Files:**
- Create: `reports/agent/260829_agent_02.md` only after re-reading the date and scanning the report directory.

**Interfaces:**
- Produces: fresh test/QA evidence, the Round 02 report, a pushed `master`, and final local/remote SHA equality.

- [ ] Run font, LaTeX, gallery, validation, pytest, Ruff, formatter, Skill validation, and repository-cleanliness checks from conda base.
- [ ] Re-read the system date and report directory; generate the next strictly named report with commands, failures, repairs, visual QA, and limitations.
- [ ] Audit staged files and ensure no tmp/cache/build/lock artifacts are committed.
- [ ] Commit and push `master`, re-read the remote tree, append post-push evidence to the report, push the report update, and verify local/remote equality.
