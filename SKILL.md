---
name: axiomfig
description: Use when creating, revising, or validating publication-quality scientific figures with Matplotlib, especially when deterministic styles, multilingual CJK typography, Tectonic PDF rendering, or journal-width geometry matter.
---

# AxiomFig

## Core contract

AxiomFig is deterministic-first: the agent chooses a tested template and style modules, then maps real data and scientific meaning into them. Do not improvise font families, point sizes, line widths, tick geometry, figure width, palettes, or export settings inside a template.

## Workflow

1. Identify the scientific comparison and figure archetype. Read [references/templates.md](references/templates.md) when choosing among line, scatter/parity, bar, distribution, heatmap, model-evaluation, and layout templates.
2. Select exactly one module per layer in this order: `base + geometry + typography + colors + plot + language + rendering`. Read [references/style-contract.md](references/style-contract.md) before changing or adding a module.
3. Run `python scripts/check_fonts.py`. A missing exact font is a hard failure; do not substitute another family.
4. Copy or adapt the closest native Matplotlib template. Change data, labels, units, legend placement, annotations, and plot-specific content only. Templates must not mutate contract `rcParams`.
5. Render through `python scripts/render.py <template> --output <stem> [style options]`. The formal PDF must pass through Tectonic. PNG is rasterized from that final PDF, not rendered by a separate style path.
6. Run `python scripts/validate.py <output-directory>` and visually inspect the PDF rasterization. Read [references/rendering-validation.md](references/rendering-validation.md) for the evidence required.

For multilingual content, explicitly map Chinese text to `zh` and Japanese text to `ja`; read [references/typography.md](references/typography.md). Never rely on font fallback to choose regional CJK glyphs.

## User preference changes

If the user explicitly changes a visual preference, update the owning `.mplstyle` module, its reference contract, and tests. Do not apply a hidden one-off `rcParams` override. Undeclared cross-layer key conflicts must fail composition.

## Output boundary

Write user deliverables to the requested directory. Reserve `gallery/` for the repository's final PDF/PNG demonstration pairs; put TeX, logs, intermediate PDFs, and caches under `tmp/`.

## Completion gate

Complete only when the source template runs, style modules load without undeclared conflicts, Tectonic exits successfully, the PDF is one parseable page at the intended physical size, fonts are embedded/subset, the PNG exists, required multilingual text is present, logs contain no missing-font/glyph diagnostics, and rendered pages show no tofu, clipping, overlap, or unreadable labels.
