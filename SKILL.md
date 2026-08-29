---
name: axiomfig
description: Use when creating, revising, or validating publication-quality scientific figures with Matplotlib, especially when deterministic styles, multilingual CJK typography, Tectonic PDF wrapping, or journal-width geometry matter.
---

# AxiomFig

## Core contract

AxiomFig is deterministic-first. Choose a tested template and exactly one style module per layer, then map real data and scientific meaning into that contract. Do not improvise fonts, stroke widths, ticks, layout offsets, palettes, figure geometry, or export settings inside a template.

## Workflow

1. Choose the closest native Matplotlib builder in [references/templates.md](references/templates.md).
2. Compose `base -> geometry -> typography -> colors -> plot -> language -> rendering`. Read [references/style-contract.md](references/style-contract.md) for ownership, `0.6 pt` strokes, and open-versus-filled tick rules.
3. Select one complete typography mode: `sans` (default) or `serif`. Run `python scripts/check_fonts.py`; for `serif`, CJK, math, mono, ordinary-artist handling, or mixed-script segmentation, read and follow [references/typography.md](references/typography.md).
4. Use the deterministic helpers for panel labels, legends, bars, and scatter. Read [references/layout.md](references/layout.md) only for layout work and [references/colors.md](references/colors.md) only for palette or xcolor work.
5. Render with `python scripts/render.py <template> --output <stem> [style options]`. The formal PDF passes through Tectonic; the PNG is rasterized from that PDF.
6. Run `python scripts/validate.py <output-directory>` and inspect the rendered page. Use [references/rendering-validation.md](references/rendering-validation.md) for evidence and the `01`-`10` acceptance gallery.

## Scientific LaTeX boundary

The packaged standalone LaTeX layer provides generated xcolor definitions plus `siunitx`, `mhchem`, `amsmath`, and `unicode-math`; read [references/latex.md](references/latex.md) before using it. It is verified for TeX-native documents only. Matplotlib label text is already embedded before the wrapper reaches Tectonic, so native `\qty` or `\ce` expansion inside plot labels is **TECHNICALLY BLOCKED / DEFERRED** and must not be claimed.

## Preference changes

When the user changes a visual preference, update the owning style/helper, its reference contract, and behavioral tests. Do not hide a one-off `rcParams` override. Undeclared cross-layer key conflicts must fail composition.

## Output and completion

Write deliverables to the requested directory. Reserve `gallery/` for final `01`-`10` PDF/PNG pairs and `tmp/` for TeX, logs, intermediates, and caches.

Complete only when the source runs, styles compose, exact fonts resolve, Tectonic succeeds, the one-page PDF has the intended physical size and embedded/subset non-Type-3 fonts, the PNG exists, and visual inspection finds no missing glyphs, tofu, clipping, overlap, or unreadable labels.
