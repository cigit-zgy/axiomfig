# Tectonic rendering and validation

## Formal pipeline

```text
Matplotlib Figure
  -> vector intermediate.pdf
  -> standalone wrapper.tex with includegraphics
  -> tectonic --keep-logs --keep-intermediates
  -> final PDF
  -> pdftoppm preview PNG
```

Matplotlib's PGF backend does not accept `tectonic` as `pgf.texsystem`; setting it directly is not a supported route. AxiomFig therefore uses Matplotlib's vector PDF as the TeX-compatible intermediate, then compiles a zero-border standalone TeX wrapper with Tectonic. Tectonic is always the final PDF producer. The same embedded vector content becomes the PNG by rasterizing that final PDF.

All `.tex`, `.aux`, `.log`, wrapper PDF, source PDF, and preview intermediates stay below `tmp/`. The render manifest records the full Tectonic command, style paths, font paths, intermediate path, physical dimensions, file size, and `pdffonts` rows.

## Commands

```bash
uv run python scripts/render.py line-ci --output output/line \
  --geometry single-column --colors default --plot line
uv run python scripts/validate.py output
uv run python scripts/build_gallery.py
```

## Deterministic checks

Validation fails for a missing/empty/unparseable PDF, more than one page, a missing PNG pair, wrong expected gallery set, absent Tectonic log, missing-font/glyph log diagnostic, non-embedded or non-subset font, Type 3 font, or a missing required multilingual string. Physical dimensions are read from the PDF media box.

Poppler may emit `Mismatch between font type and embedded font file` for Matplotlib 3.11 CFF OpenType subsets. This is not classified as fallback: the run still requires `emb=yes`, `sub=yes`, `uni=yes`, exact font names, successful text extraction, and visual inspection. Record the warning rather than hiding it.

## Visual gate

Render every final PDF to PNG and inspect at normal and enlarged scale. Check text and math baselines, Chinese/Japanese glyphs, tofu, clipping, overlap, panel labels, legend occlusion, marker/line clarity, heatmap/colorbar spacing, and consistent whitespace. Do not convert subjective aesthetics into a fake automated PASS.
