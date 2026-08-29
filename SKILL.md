---
name: axiomfig
description: Use when creating, revising, or validating deterministic publication-quality scientific figures with Matplotlib, especially when journal-width geometry, physical-point typography, scientific axes, legends, panel labels, or Tectonic PDF wrapping matter.
---

# AxiomFig

## Core contract

AxiomFig is deterministic-first. Read the three canonical sources before changing a visual default:

- `styles/style.yaml`: geometry, sizes, strokes, ticks, axes, legends, panels, plot defaults, and rendering;
- `styles/fonts.yaml`: sans/serif/mono/math families, exact files, provenance, license attribution, and optional system fonts;
- `styles/colors.yaml`: canonical scientific palettes.

Do not introduce `.mplstyle` files or one-off `rcParams` overrides. Python is a thin YAML-to-`rcParams`/token consumer; template builders own data and scientific meaning, not visual defaults.

## Workflow

1. Choose one of the 20 builders in [references/template-contract.md](references/template-contract.md). They cover line, scatter/evaluation, bar/distribution, surface, and multi-panel figure intents while remaining grouped in four Python family modules.
2. Choose geometry `single-column` (90 mm), `onehalf-column` (140 mm), or `double-column` (190 mm). Font sizes remain physical points and never scale with width.
3. Choose a complete Latin/math typography mode: `sans` (default) or `serif`. Run `python scripts/check_fonts.py`; read [references/typography.md](references/typography.md) before changing font metadata.
4. Use the deterministic helpers for nice linear axes, open/filled/categorical ticks, filled-artist edges, legends, and panel labels. Read [references/style-contract.md](references/style-contract.md) and [references/layout.md](references/layout.md).
5. Render with `python scripts/render.py <template> --output <stem> [--geometry ...] [--typography sans|serif]`. The formal PDF passes through Tectonic; the PNG is rasterized from that PDF.
6. Validate with `python scripts/validate.py <output-directory>` and inspect the rendered page. For a repository change, rebuild both `gallery/sans/` and `gallery/serif/`, then inspect all 40 PNGs.

## Scientific LaTeX boundary

Use only the verified general scientific syntax recorded in [references/latex-contract.md](references/latex-contract.md). Do not invent unit, chemistry, math, or color macros. The current Matplotlib path embeds text before the Tectonic wrapper; TeX-native macro expansion inside plot labels remains **DEFERRED** and must not be claimed.

## Preference changes

Update the owning YAML token, the thin consumer/helper, the relevant reference contract, and a behavioral test. Use only `normal`, `boundary`, and `overflow/error` cases; never launch combinatorial visual searches.

## Completion

Complete only when deterministic tests pass, each Gallery font mode contains all 20 canonical PDF/PNG pairs (40 files per mode), PDFs have the intended physical size and embedded/subset non-Type-3 fonts, and visual inspection finds no clipping, overlap, asymmetric ordinary panels, malformed legends, or missing glyphs.
