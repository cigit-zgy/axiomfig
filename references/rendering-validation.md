# Rendering and validation

## Formal pipeline

```text
Matplotlib Figure
  -> vector intermediate.pdf
  -> standalone includegraphics wrapper
  -> Tectonic final PDF
  -> Poppler preview PNG
```

The PNG is rasterized from the formal PDF, not independently rendered. TeX sources, logs, intermediates, manifests, and caches remain under ignored `tmp/`; `gallery/` contains only final deliverables.

## Commands

```bash
python scripts/check_fonts.py
python scripts/generate_colors.py --check
python scripts/build_gallery.py
python scripts/validate.py gallery
python -m pytest -q
ruff check .
ruff format --check .
```

## Gallery acceptance set

Both `gallery/sans/` and `gallery/serif/` contain the exact 36 PDF/PNG pairs listed in [template-contract.md](template-contract.md), from `01_single_line` through `36_complex_multi_panel`. `gallery/latex/` contains `01_scientific_typography` and `02_palettes` as Tectonic-native PDF/PNG pairs. This is 74 pairs and 148 committed Gallery artifacts in total.

The single Gallery E2E reconstructs these canonical cases, verifies physical geometry for Matplotlib pages, PDF/PNG presence, embedded/subset non-Type-3 fonts, Tectonic logs, and the exact nested artifact set. Most individual plots use 90 × 67.5 mm pages, the Mantel-style view uses 140 × 105 mm, and panel compositions use 190 × 142.5 mm. Tectonic-native pages use standalone content geometry. Unit tests cover deterministic normal, boundary, and overflow/error behavior without generating hundreds of PDFs.

## Visual gate

After automation passes, inspect all 74 PNGs at normal and enlarged scale. Check `0.8 pt` main strokes, opaque `0.6 pt` filled edges, face alpha, open/filled tick direction, measured minor/major lengths, categorical axes, scatter alpha/size, exact bar widths, two-decimal labels, redundant series identity, 11 pt panel labels, legends, equal outer footprints, nested heatmap colorbars, statistical semantics, clipping, sans/serif structural identity, and both Tectonic-native references. Automated checks do not certify subjective visual quality.

Read [latex-contract.md](latex-contract.md) for the current TeX-native boundary.
