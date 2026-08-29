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

The wrapper deliberately does not load the packaged
`src/axiomfig/resources/latex/axiomfig.sty`. Figure text has already been shaped and
embedded in `intermediate.pdf`, so loading scientific packages in the outer document
could not expand macros inside labels. The shared package is for TeX-native documents
and the standalone probe described below.

All `.tex`, `.aux`, `.log`, wrapper PDF, source PDF, and preview intermediates stay below `tmp/`. The render manifest records the full Tectonic command, style paths, font paths, intermediate path, physical dimensions, file size, and `pdffonts` rows.

## Commands

```bash
python scripts/render.py line-ci --output output/line \
  --geometry single-column --colors default --plot line
python scripts/validate.py output
python scripts/build_gallery.py
python scripts/check_latex.py
```

`check_latex.py` copies the wheel-packaged `axiomfig.sty` and the single canonical,
generated `axiomfig-colors.tex` into a fresh work directory, then compiles real
standalone examples through Tectonic. Only after semantic and font checks pass are the
verified artifacts atomically published to ignored `tmp/latex-probe/`. The probe
exercises `\qty{10}{\milli\gram\per\litre}`,
`\ce{NH4+}`, `\ce{NO3-}`, `\ce{PO4^3-}`, and
`\mu_{\max}, \alpha, \beta`. Success requires extracted semantic text plus non-Type-3,
embedded, subset Latin Modern text and math fonts with Unicode mappings.
`axiomfig.sty` provides only generic infrastructure: generated xcolor definitions,
`xcolor`, `siunitx`, `mhchem`, `amsmath`, and `unicode-math`; it defines no
wastewater- or model-specific macros.

## Tectonic-native Matplotlib text investigation

The following experiment was run with Python 3.11.16, Matplotlib 3.10.9, and
Tectonic 0.17.0. It uses Matplotlib's real PGF backend configuration, no alternate TeX
engine, and no monkeypatch:

```python
import matplotlib as mpl

mpl.use("pgf")
mpl.rcParams["pgf.texsystem"] = "tectonic"

import matplotlib.pyplot as plt

figure, axis = plt.subplots()
axis.set_xlabel(r"$\qty{10}{\milli\gram\per\litre}$")
figure.savefig("pgf-tectonic.pdf")
```

Configuration fails before the figure can be saved, with the exact diagnostic:

```text
ValueError: Key pgf.texsystem: 'tectonic' is not a valid value for pgf.texsystem; supported values are ['xelatex', 'lualatex', 'pdflatex']
```

The current vector wrapper was also exercised with the same `siunitx` label. Outside
math mode Matplotlib draws the backslash command and braces literally; Tectonic sees
only those already embedded glyphs. Inside math mode Matplotlib fails before the
wrapper stage:

```text
\qty{10}{\milli\gram\per\litre}
^
ParseFatalException: Unknown symbol: \qty, found '\'  (at char 0), (line:1, col:1)
```

**Verdict: TECHNICALLY BLOCKED / DEFERRED.** Matplotlib 3.10.9 exposes no supported
PGF route to Tectonic, so AxiomFig keeps the stable vector-PDF wrapper unchanged and
does not claim `siunitx` or `mhchem` support for plot labels. A future route must first
prove a TeX-native text layer with Tectonic in an isolated end-to-end prototype,
including macro expansion, font inspection, text extraction, geometry, and failure
handling; only then may it replace the stable renderer.

## Deterministic checks

Validation fails for a missing/empty/unparseable PDF, more than one page, a missing PNG pair, wrong expected gallery set, absent Tectonic log, missing-font/glyph log diagnostic, non-embedded or non-subset font, Type 3 font, or a missing required multilingual string. Physical dimensions are read from the PDF media box.

Poppler may emit `Mismatch between font type and embedded font file` for Matplotlib 3.11 CFF OpenType subsets. This is not classified as fallback: the run still requires `emb=yes`, `sub=yes`, `uni=yes`, exact font names, successful text extraction, and visual inspection. Record the warning rather than hiding it.

## Visual gate

Render every final PDF to PNG and inspect at normal and enlarged scale. Check text and math baselines, Chinese/Japanese glyphs, tofu, clipping, overlap, panel labels, legend occlusion, marker/line clarity, heatmap/colorbar spacing, and consistent whitespace. Do not convert subjective aesthetics into a fake automated PASS.
