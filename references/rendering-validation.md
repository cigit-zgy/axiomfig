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

Both `gallery/sans/` and `gallery/serif/` contain the exact 20 PDF/PNG pairs listed in [template-contract.md](template-contract.md), from `01_single_line` through `20_multi_panel`. This is 40 final files per typography mode and 80 committed Gallery artifacts in total.

The single Gallery E2E reconstructs these canonical cases, verifies physical geometry, PDF/PNG presence, embedded/subset non-Type-3 fonts, and the exact nested artifact set. Cases `01`–`19` use 90 × 67.5 mm pages; `20_multi_panel` uses 190 × 142.5 mm. Unit tests cover deterministic normal, boundary, and overflow/error behavior without generating hundreds of PDFs.

## Visual gate

After automation passes, inspect all 40 PNGs at normal and enlarged scale. Check `0.8 pt` main strokes, `0.6 pt` filled edges, open/filled tick direction, measured minor/major lengths, categorical axes, scatter alpha/size, two-decimal bar labels, panel labels, legends, equal ordinary subplot boxes, independent heatmap colorbars, clipping, and sans/serif structural identity. Automated checks do not certify subjective visual quality.

Read [latex-contract.md](latex-contract.md) for the current TeX-native boundary.
