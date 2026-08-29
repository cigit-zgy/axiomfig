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

Both `gallery/sans/` and `gallery/serif/` contain exactly these PDF/PNG pairs:

1. `01_line`
2. `02_scatter`
3. `03_bar`
4. `04_violin`
5. `05_heatmap`
6. `06_multi_panel`

The single Gallery E2E reconstructs these canonical cases, verifies physical geometry, PDF/PNG presence, embedded/subset non-Type-3 fonts, and the exact nested artifact set. Unit tests cover deterministic normal, boundary, and overflow/error behavior without generating hundreds of PDFs.

## Visual gate

After automation passes, inspect all twelve PNGs at normal and enlarged scale. Check `0.8 pt` main strokes, `0.6 pt` filled edges, open/filled tick direction, measured minor/major lengths, categorical axes, scatter alpha/size, two-decimal bar labels, panel labels, legends, equal ordinary subplot boxes, independent heatmap colorbars, and sans/serif structural identity. Automated checks do not certify subjective visual quality.

Read [latex-contract.md](latex-contract.md) for the current TeX-native boundary.
