# Rendering and validation

## Formal figure pipeline

```text
Matplotlib Figure
  -> vector intermediate.pdf
  -> standalone wrapper.tex with includegraphics
  -> tectonic --keep-logs --keep-intermediates
  -> final PDF
  -> pdftoppm preview PNG
```

Tectonic is the final PDF producer. PNG is rasterized from that exact PDF, not rendered through a second Matplotlib style path. TeX, logs, wrapper/source PDFs, previews, manifests, and caches remain under ignored `tmp/`; `gallery/` contains only final PDF/PNG pairs.

The wrapper deliberately does not load the packaged `axiomfig.sty`: plot text has already been shaped and embedded in `intermediate.pdf`, so an outer package cannot expand macros inside labels. Read [latex.md](latex.md) for the verified standalone package and the **TECHNICALLY BLOCKED / DEFERRED** native-label boundary.

## Commands

```bash
python scripts/render.py line-ci --output tmp/demo/line \
  --geometry single-column --typography sans --colors default --plot line
python scripts/validate.py tmp/demo
python scripts/generate_colors.py --check
python scripts/check_fonts.py
python scripts/check_latex.py
python scripts/build_gallery.py
python scripts/validate.py
python -m pytest -q
ruff check .
ruff format --check .
```

AxiomFig uses ordinary Python commands and standard package metadata; no environment manager is a runtime or validation requirement.

## Gallery acceptance set

The gallery contract is exactly twenty final files:

1. `01_line.pdf/png`
2. `02_scatter.pdf/png`
3. `03_bar.pdf/png`
4. `04_violin.pdf/png`
5. `05_heatmap.pdf/png`
6. `06_model_evaluation.pdf/png`
7. `07_multilingual.pdf/png`
8. `08_multi_panel.pdf/png`
9. `09_serif.pdf/png`
10. `10_style_contract.pdf/png`

`09_serif` checks the complete serif text/math/CJK family. `10_style_contract` checks open/filled ticks, `0.6 pt` strokes, bar labels/edges, scatter edges, panel offsets, responsive legends, palette consistency, and multi-panel symmetry.

## Deterministic checks

`validate_pair()` always rejects missing, empty, or unparseable artifacts; more than one PDF page; a missing PNG; out-of-page text; non-embedded or non-subset fonts; and Type 3 fonts. It checks physical dimensions and a Tectonic log when the caller supplies those expectations. `validate_gallery(..., expected_stems=...)` also rejects a missing or unexpected PDF set; `build_gallery.py` supplies the frozen `01`-`10` set, expected dimensions, and per-render logs, and separately checks multilingual content. The standalone LaTeX probe adds the stricter Unicode-map and semantic checks described in [latex.md](latex.md).

The gallery builder uses `SOURCE_DATE_EPOCH=0` for deterministic PDF metadata and records hashes, style paths, commands, dimensions, and font rows in the ignored manifest.

Poppler can report `Mismatch between font type and embedded font file` for Matplotlib CFF OpenType subsets. This warning is recorded rather than hidden; acceptance still requires `emb=yes`, `sub=yes`, `uni=yes`, exact font names, extraction, and visual inspection.

## Visual gate

Open every final rasterization at normal and enlarged scale. Check family uniformity, math/text baselines, Chinese/Japanese glyph shapes, tofu, clipping, overlap, panel-label distance/alignment, legend containment/right alignment, open-versus-filled tick direction, marker/bar edges, heatmap/colorbar spacing, and whitespace. Subjective aesthetics are a human gate, not an automated PASS.
