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

1. Choose one of the 36 builders in [references/template-contract.md](references/template-contract.md). They cover line, statistical evaluation, bar/distribution, surface, and multi-panel intents while remaining grouped in four Python family modules.
2. Choose geometry `single-column` (90 mm), `onehalf-column` (140 mm), or `double-column` (190 mm). Font sizes remain physical points and never scale with width.
3. Choose a complete Latin/math typography mode: `sans` (default) or `serif`. Run `python scripts/check_fonts.py`; read [references/typography.md](references/typography.md) before changing font metadata.
4. Use the deterministic helpers for nice linear axes, open/filled/categorical ticks, filled artists, bars, redundant series identity, legends, outer panel footprints, and panel labels. Read [references/style-contract.md](references/style-contract.md) and [references/layout.md](references/layout.md).
5. Render with `python scripts/render.py <template> --output <stem> [--geometry ...] [--typography sans|serif]`. The formal PDF passes through Tectonic; the PNG is rasterized from that PDF.
6. Validate with `python scripts/validate.py <output-directory>` and inspect the rendered page. For a repository change, rebuild `gallery/sans/`, `gallery/serif/`, and `gallery/latex/`, then inspect all 74 PDF/PNG pairs.

## Non-negotiable visual behavior

- Never set an artist-wide alpha on filled geometry. Put configured alpha in face RGBA and keep the black edge RGBA fully opaque at `fill_edge`.
- Never invent template-local alpha, marker size, bar width, stroke width, tick length, legend gap, or panel-label coordinates. Change the owning YAML token and its shared helper when the contract itself changes.
- Use `bar_width(1)` for ordinary bars and `bar_width(series_count)` for grouped bars. Category count does not alter width.
- Use `series_style(index)` for multi-series identity. The ordered line cycle begins solid, dash-dot, dotted, long-dash and is redundantly paired with color and marker. Use `reference_line_kwargs()` for secondary/reference lines; its default is dash-dot.
- Treat an outer panel footprint as the top-level GridSpec slot. A panel colorbar must subdivide that slot; it must not be appended outside a data axis or allowed to compress a peer panel. Anchor 11 pt bold panel labels to the outer footprint with physical-point offsets.
- Fit a multi-series legend with `N`, `N-1`, … columns and accept the first candidate inside the figure boundary without panel-label collision. Do not reduce columns merely because it is wider than the data axis.

## Scientific LaTeX boundary

Use only the verified general scientific syntax recorded in [references/latex-contract.md](references/latex-contract.md). Do not invent unit, chemistry, math, or color macros. `gallery/latex/` is genuinely Tectonic-native. The Matplotlib Gallery embeds text before a separate Tectonic wrapper; TeX-native macro expansion inside Matplotlib labels remains **DEFERRED** and must not be claimed.

## Preference changes

Update the owning YAML token, the thin consumer/helper, the relevant reference contract, and a behavioral test. Use only `normal`, `boundary`, and `overflow/error` cases; never launch combinatorial visual searches.

## Completion

Complete only when deterministic tests pass, each Matplotlib typography mode contains all 36 canonical PDF/PNG pairs, `gallery/latex/` contains both Tectonic-native PDF/PNG pairs, PDFs have the intended geometry and embedded/subset non-Type-3 fonts, and visual inspection finds no translucent edges, clipping, overlap, asymmetric outer panels, malformed legends, or missing glyphs.
