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
python scripts/render.py line-ci --output "$PWD/tmp/demo/line" \
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

## Validation tiers

The checks are deliberately split; do not report the generic validator as the full build-time/E2E gate.

| Tier | Verified behavior |
|---|---|
| `validate_pair()` | PDF exists, parses as one page, has a non-empty PNG partner, keeps text within the page, embeds/subsets every font, and has no Type 3 fonts; optional caller-supplied width/height and Tectonic log checks |
| `validate_gallery()` / `python scripts/validate.py` | runs the generic pair checks over existing PDFs; an API caller may supply `expected_stems`, but the CLI does not reconstruct artifacts or supply the frozen set, dimensions, render logs, or multilingual strings |
| `build_gallery.py` plus gallery E2E tests | reconstructs `01`-`10`, supplies each spec's dimensions and fresh render log, checks required multilingual text, enforces the exact set after building, and automatically tests reproducible PDF/PNG hashes and expected font families |
| `check_latex.py` | separately verifies TeX-native `siunitx`/`mhchem`/math extraction and requires embedded, subset, Unicode-mapped, non-Type-3 Latin Modern text/math fonts |

The gallery builder uses `SOURCE_DATE_EPOCH=0` for deterministic PDF metadata and records hashes, style paths, commands, dimensions, and font rows in the ignored manifest. The xcolor/Matplotlib RGB equality belongs to `generate_colors.py --check` and `tests/test_colors.py`, not to the standalone typesetting probe.

Poppler can report `Mismatch between font type and embedded font file` for Matplotlib CFF OpenType subsets. This warning is recorded rather than hidden. Generic figure validation still requires `emb=yes`, `sub=yes`, and no Type 3 fonts; automated gallery E2E adds expected-family and extracted-content checks. The standalone probe separately requires `uni=yes`.

## Visual gate

After the automated build/E2E tier passes, a human must open every final rasterization at normal and enlarged scale. Check family uniformity, math/text baselines, Chinese/Japanese glyph shapes, tofu, clipping, overlap, panel-label distance/alignment, legend containment/right alignment, open-versus-filled tick direction, marker/bar edges, heatmap/colorbar spacing, and whitespace. This visual gate is required but is not executed or certified by pytest, `validate_gallery()`, or `pdffonts`; subjective aesthetics must never be reported as an automated PASS.
