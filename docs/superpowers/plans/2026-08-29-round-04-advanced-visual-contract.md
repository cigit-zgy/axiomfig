# AxiomFig Round 04 Implementation Plan

**Goal:** Freeze the advanced visual contract, expand the canonical statistical Gallery, add Tectonic-native reference figures, and publish one verified master commit.

**Architecture:** Extend the three YAML configuration sources and keep Python helpers thin. Implement artist styling and outer-footprint layout in shared helpers, build deterministic examples inside the four existing template-family modules, and keep artifact orchestration in Gallery/LaTeX modules.

**Tech stack:** Python 3.11+, Matplotlib, NumPy, PyYAML, pytest, Tectonic, Poppler.

---

## Task 1: Add failing visual-contract tests

**Files:**
- Modify: `tests/test_styles.py`
- Modify: `tests/test_plot_contract.py`
- Modify: `tests/test_layout_contract.py`
- Modify: `tests/test_colors.py`
- Modify: `tests/test_latex.py`
- Modify: `tests/test_gallery.py`

1. Add tests for phi-derived tick geometry and shared filled/colorbar lengths.
2. Add face-alpha/opaque-edge tests for scatter, bars, confidence intervals, boxplots, violins, and filled patches.
3. Add exact single and grouped bar-width tests for 3, 5, and 10 categories and 2/4 series.
4. Add ordered redundant series-cycle and dash-dot reference-line tests.
5. Add legend normal, exact-boundary, and overflow tests using the figure boundary and panel-label collision.
6. Add outer-footprint equality and panel-label anchoring tests for 2x2, 2x3, and 3x2 layouts with a nested heatmap colorbar.
7. Add sans mathematical typography and five-palette schema/xcolor tests.
8. Update Gallery expectations to 36 pairs per typography plus two LaTeX pairs.
9. Run only the new targeted tests and confirm they fail for the intended missing behavior.

## Task 2: Implement the central contract

**Files:**
- Modify: `styles/style.yaml`
- Modify: `styles/fonts.yaml`
- Modify: `styles/colors.yaml`
- Modify: `src/axiomfig/config.py`
- Modify: `src/axiomfig/contracts.py`
- Modify: `src/axiomfig/colors.py`

1. Add central tick, panel, legend, bar-width, series-cycle, and reference-line tokens.
2. Map sans math to Latin Modern Sans and retain XCharter Math for serif mode.
3. Add Axiom Deep, Warm, and Cool so all five Axiom palettes contain eight canonical colors.
4. Add deterministic helpers for tick geometry, bar width, series identity, and reference-line kwargs.
5. Run contract/color/style tests until green.

## Task 3: Implement artist and layout helpers

**Files:**
- Modify: `src/axiomfig/template_helpers.py`
- Modify: `tests/test_plot_contract.py`
- Modify: `tests/test_layout_contract.py`

1. Replace artist-wide alpha with face RGBA transformation while preserving opaque black edges.
2. Apply central geometry to ordinary axes and colorbars.
3. Make legend fitting figure-aware and retain the first fitting column count.
4. Anchor panel labels to top-level outer footprints.
5. Add a nested GridSpec helper that places data axes and colorbars inside one footprint.
6. Verify the errorbar tick defect with a minimal sans/serif reproduction and encode its root-cause regression test.
7. Run targeted plot and layout tests until green.

## Task 4: Expand deterministic templates

**Files:**
- Modify: `src/axiomfig/templates/curves.py`
- Modify: `src/axiomfig/templates/distributions.py`
- Modify: `src/axiomfig/templates/surfaces.py`
- Modify: `src/axiomfig/templates/panels.py`
- Modify: `src/axiomfig/templates/__init__.py`
- Modify: `src/axiomfig/gallery.py`

1. Apply the redundant visual cycle to multi-series line, scatter, and interval plots.
2. Apply exact central widths to vertical, horizontal, grouped, and stacked bars.
3. Add density, ECDF, forest, point-interval, Bland-Altman, heatmap variants, ROC, precision-recall, calibration, residual, and Mantel-style templates.
4. Add two-, four-, and six-panel layouts; put every colorbar inside its panel footprint.
5. Register exactly 36 canonical Matplotlib Gallery cases for both sans and serif modes.
6. Run template and Gallery schema tests.

## Task 5: Add Tectonic-native Gallery figures

**Files:**
- Modify: `src/axiomfig/latex.py`
- Modify: `latex/axiomfig-colors.tex`
- Modify: `tests/test_latex.py`
- Modify: `src/axiomfig/gallery.py`

1. Generate canonical and palette-qualified xcolor definitions from `colors.yaml`.
2. Factor a deterministic Tectonic compile helper from the existing probe.
3. Build the scientific-typography and five-palette LaTeX sources.
4. Compile real PDFs and rasterize PNGs under `gallery/latex`.
5. Validate all four artifacts and retain logs only in the temporary work root.

## Task 6: Update skill instructions and references

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `references/style-contract.md`
- Modify: `references/layout.md`
- Modify: `references/colors.md`
- Modify: `references/typography.md`
- Modify: `references/template-contract.md`
- Modify: `references/latex-contract.md`

1. Document the central-only token policy and ban template-local visual overrides.
2. Document face-only alpha, redundant series identity, exact bar widths, and figure-aware legends.
3. Define outer panel footprint and nested colorbar ownership.
4. Distinguish Matplotlib typography from Tectonic-native output.
5. Document all Gallery families and palette names.
6. Run a fresh forward behavioral skill test and confirm it uses the frozen contract without inventing tokens.

## Task 7: Rebuild and review the Gallery

**Files:**
- Rebuild: `gallery/sans/*`
- Rebuild: `gallery/serif/*`
- Rebuild: `gallery/latex/*`

1. Run the canonical Gallery builder once.
2. Verify artifact counts, PDF page dimensions, embedded fonts, PNG dimensions, and absence of out-of-page content.
3. Create contact sheets and perform one review of alpha/edges, ticks, legends, math typography, bar widths, panel symmetry, colorbar ownership, series identity, statistical semantics, and sans/serif consistency.
4. If required, perform one bounded repair pass and rebuild only once more.
5. Run final artifact validation after any repair.

## Task 8: Test, report, commit, push, and verify remote

**Files:**
- Create: `reports/agent/260829_agent_05.md` or the next free number discovered at runtime.

1. Re-read the current date and scan report numbering.
2. Run formatting/lint checks and the complete pytest suite, recording wall time and any slow point beyond one minute.
3. Run skill structure validation and inspect `git diff --check` plus repository status.
4. Write the report with architecture, schema, tokens, Gallery changes, review result, runtime, Tectonic result, and remaining limitations.
5. Re-run the final validation commands required to support completion claims.
6. Commit on `master` and push only if all acceptance checks pass and no Important issue remains.
7. Fetch/re-read `origin/master`, verify local and remote SHA equality, inspect remote tree paths for Gallery/report, and confirm no tmp/cache/build artifacts are tracked.
