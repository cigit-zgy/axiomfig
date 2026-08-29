# Round 05 Layout and Ornament Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Subagent delegation is not authorized for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace template-local panel, legend, colorbar, and geometry handling with one deterministic Layout and Ornament Engine and a runtime figure-anatomy validator.

**Architecture:** A small registry in `layout.py` gives every multi-panel figure explicit equal outer footprints and ownership. `ornaments.py` measures and places legends, labels, and colorbars only after axes geometry is solved. `anatomy.py` validates the resulting ownership and output boundary before rendering.

**Tech Stack:** Python 3.11+, Matplotlib GridSpec/transforms, importlib.resources, PyYAML, pytest, Tectonic, Poppler.

**Spec:** `docs/superpowers/specs/2026-08-30-round-05-layout-ornament-engine-design.md`

## Global Constraints

- Work directly on `master`; create no branch and make one final commit only after validation.
- Add no plot templates, template knowledge base, orchestration, routing, or statistical capability.
- Use a one-measurement formula solve; no trial-and-error placement loop.
- Keep exactly three YAML configuration sources.
- Run the full pytest suite only once at final validation.
- Perform one Gallery visual review and at most one repair pass.

---

### Task 1: RED geometry and resource contracts

**Files:**
- Modify: `tests/test_layout_contract.py`
- Modify: `tests/test_plot_contract.py`
- Modify: `tests/test_validation.py`
- Modify: `tests/test_packaged_cli.py`

**Interfaces:**
- Consumes: current `build_template()`, wheel build, and current helper behavior.
- Produces: failing behavioral tests for `get_figure_layout()`, `validate_figure_anatomy()`, package-local fonts, and derived colorbar ticks.

- [ ] Write tests that assert 2x2 and 2x3 footprint equality/alignment, registered primary/auxiliary ownership, panel content containment, label anchor, legend normal/boundary/overflow behavior, colorbar half-major/same-minor lengths, and figure-boundary failure.
- [ ] Extend the clean-wheel test to locate fonts and licenses through `importlib.resources.files("axiomfig")` and assert root `fonts/` and `latex/` are absent from the wheel contract.
- [ ] Run only the changed test modules and confirm failures name missing registry/validator behavior, current 6 pt colorbar major ticks, and current external resource packaging.

### Task 2: Package runtime resource convergence

**Files:**
- Move: `fonts/*` to `src/axiomfig/resources/fonts/*`
- Delete: `latex/`
- Modify: `src/axiomfig/typography.py`
- Modify: `pyproject.toml`
- Modify: `references/latex-contract.md`
- Modify: `references/typography.md`

**Interfaces:**
- Consumes: `styles/fonts.yaml` filenames and `importlib.resources.files("axiomfig")`.
- Produces: `_bundled_font_root() -> Traversable`, clean-wheel font discovery, one LaTeX runtime source.

- [ ] Move binaries and licenses without changing file contents or font contracts; merge valid root LaTeX README guidance into the reference before deleting the duplicate directory.
- [ ] Replace repository/data-file lookup with package resource traversal while preserving optional system search roots.
- [ ] Change setuptools package-data to include `resources/latex/*`, `resources/fonts/*`, and `resources/fonts/licenses/*`; remove font data-files.
- [ ] Run the resource and clean-wheel tests until green.

### Task 3: Deterministic Layout Engine

**Files:**
- Create: `src/axiomfig/layout.py`
- Modify: `src/axiomfig/templates/panels.py`
- Modify: `src/axiomfig/templates/surfaces.py`
- Modify: `src/axiomfig/templates/__init__.py`
- Modify: `styles/style.yaml`
- Modify: `src/axiomfig/config.py`

**Interfaces:**
- Produces:
  - `create_panel_grid(figure: Figure, rows: int, columns: int) -> FigureLayout`
  - `add_panel_axes(layout: FigureLayout, index: int, *, colorbar: bool = False) -> tuple[Axes, Axes | None]`
  - `solve_panel_layout(figure: Figure) -> None`
  - `get_figure_layout(figure: Figure) -> FigureLayout | None`
  - `outer_panel_bbox(axis: Axes) -> Bbox`

- [ ] Implement frozen row/column footprint identity and explicit mutable ownership collections without a class hierarchy.
- [ ] Calculate top-level GridSpec margins and wspace/hspace from figure points, output padding, label gutter, and physical panel-gap tokens.
- [ ] Measure decoration overhangs once, derive common ordinary-panel insets, reserve legend height, and set final primary/auxiliary positions once.
- [ ] Refactor four existing panel templates and surface colorbar creation to register through the engine; do not add builders.
- [ ] Run the layout RED tests until footprint, ownership, and containment tests pass.

### Task 4: Ornament Engine and tick derivation

**Files:**
- Create: `src/axiomfig/ornaments.py`
- Modify: `src/axiomfig/template_helpers.py`
- Modify: `src/axiomfig/templates/curves.py`
- Modify: `src/axiomfig/templates/distributions.py`
- Modify: `src/axiomfig/templates/panels.py`
- Modify: `styles/style.yaml`

**Interfaces:**
- Produces:
  - `request_legend(axis: Axes) -> Legend | None`
  - `finalize_ornaments(figure: Figure) -> None`
  - `add_panel_labels(figure: Figure) -> None`
  - `apply_colorbar_contract(colorbar: Colorbar) -> None`

- [ ] Set central legend `columnspacing=1.0`, `borderpad=0`, `borderaxespad=0`, preserve `top_gap_pt`, and pass every spacing token explicitly to Matplotlib.
- [ ] For registered layouts, record legend intent during template construction and place candidates only after the layout solve; keep direct standalone helper behavior for single-axis consumers.
- [ ] Choose legend columns deterministically from `N` down to 1 and accept the first candidate inside the figure boundary without label/data collision.
- [ ] Create 11 pt bold labels from each registered footprint upper-left using fixed-point translation after layout solve.
- [ ] Derive colorbar major ticks as `major_total / 2` and minor ticks as the central minor length.
- [ ] Run legend, label, and colorbar tests until green.

### Task 5: Runtime figure-anatomy validation

**Files:**
- Create: `src/axiomfig/anatomy.py`
- Modify: `src/axiomfig/rendering.py`
- Modify: `tests/test_validation.py`

**Interfaces:**
- Produces: `validate_figure_anatomy(figure: Figure, *, tolerance_pt: float = 0.25) -> None` and `FigureAnatomyError`.

- [ ] Draw once and compare every registered footprint in display coordinates for equal size and row/column alignment.
- [ ] Union primary/auxiliary tight bboxes and registered local artist bboxes, excluding registered figure-level ornaments, then enforce containment.
- [ ] Check panel-label anchors/collisions, legend boundary/collision, auxiliary axes, annotations, and full output boundary with issue-specific messages.
- [ ] Invoke validation before Matplotlib PDF save for figures with a registered layout.
- [ ] Run validator tests including deliberate auxiliary overflow and figure-level ornament overflow until green.

### Task 6: Skill and reference contracts

**Files:**
- Modify: `SKILL.md`
- Create: `references/scientific-visualization-principles.md`
- Create: `references/layout-contract.md`
- Create: `references/validation-contract.md`
- Modify: `references/latex-contract.md`
- Modify: `references/style-contract.md`
- Modify: `references/rendering-validation.md`
- Remove or redirect: `references/layout.md`

**Interfaces:**
- Consumes: observable runtime contracts from Tasks 2-5.
- Produces: concise skill routing and maintained project references, not copied book content.

- [ ] Record the deterministic-first hard rule and the exact boundary of future agent inputs in SKILL and design references.
- [ ] Document Figure/Panel/Primary/Auxiliary/Figure-level Ornament terminology, physical units, ownership, containment, and validator failures.
- [ ] Add Rougier/book attribution, source commit, license distinction, and only AxiomFig-specific implications.
- [ ] Run `quick_validate.py` and the relevant documentation/resource tests.

### Task 7: Gallery, final verification, report, and remote state

**Files:**
- Rebuild: `gallery/sans/*`, `gallery/serif/*`, `gallery/latex/*`
- Create: `reports/agent/YYMMDD_agent_NN.md` after a fresh date/sequence scan

**Interfaces:**
- Consumes: all completed runtime and documentation contracts.
- Produces: 74 canonical PDF/PNG pairs, one report, one validated master commit.

- [ ] Rebuild the complete Gallery once and validate exact artifact counts, page dimensions, fonts, Tectonic logs, and no overflow.
- [ ] Visually inspect both typography modes for `02_multi_line`, `34_four_panel`, `35_six_panel`, and `36_complex_multi_panel`, plus colorbar tick geometry; record findings.
- [ ] If the single review finds Important defects, perform one repair pass and rebuild affected/all canonical artifacts once; otherwise proceed directly.
- [ ] Run Ruff, format check, color/font/LaTeX checks, exact Gallery validation, clean-wheel test, and the full pytest suite exactly once; record total runtime and slow tests.
- [ ] Re-read the system date and report directory immediately before creating the report; follow `basic-rule.md` and include root cause, before/after geometry, and remaining limitations.
- [ ] Run `git diff --check`, review all intended changes, commit once, push `master`, fetch/ls-remote, verify Gallery/resources/report in the remote tree, confirm no tmp/cache/build artifacts, and confirm local `master == origin/master` with a clean worktree.
