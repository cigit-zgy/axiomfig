# Standalone scientific LaTeX contract

## Packaged resources

The wheel resources are installed as:

- `axiomfig/resources/latex/axiomfig.sty`
- `axiomfig/resources/latex/axiomfig-colors.tex`

Their checkout sources live under `src/axiomfig/resources/latex/`.

`axiomfig.sty` inputs the generated color definitions and loads `xcolor`, `siunitx`, `mhchem` version 4, `amsmath`, and `unicode-math`. It provides generic scientific typesetting infrastructure only; it defines no wastewater-, ASM-, ADM-, COD-, or BOD-specific macros.

`compile_latex_probe(output_dir)` copies the packaged resources into a fresh temporary directory, compiles real `\qty`, `\ce`, and math examples with Tectonic, checks extracted semantics and embedded/subset Unicode-mapped non-Type-3 Latin Modern fonts, then atomically publishes the verified files. The command interface is:

```bash
python scripts/check_latex.py
python scripts/check_latex.py --output-dir tmp/latex-probe
```

This PASS applies to TeX-native documents that explicitly load `axiomfig.sty`.

## Export for a TeX-native document

After installing AxiomFig, copy both package resources into the TeX document directory with the standard `importlib.resources` API:

```bash
python - /absolute/path/to/tex-project <<'PY'
from importlib.resources import files
from pathlib import Path
import sys

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
resources = files("axiomfig").joinpath("resources", "latex")
for name in ("axiomfig.sty", "axiomfig-colors.tex"):
    (destination / name).write_bytes(resources.joinpath(name).read_bytes())
PY
```

Keep the two files together, then use `\usepackage{axiomfig}` in a Tectonic document. Regenerate and test canonical colors in the AxiomFig checkout; do not edit the exported color file as an independent palette source.

## Matplotlib-to-Tectonic boundary

The production figure path is different:

```text
Matplotlib shapes labels -> intermediate.pdf
                           -> standalone \includegraphics wrapper
                           -> Tectonic final PDF
```

The wrapper intentionally loads only `graphicx`. By the time Tectonic sees it, label glyphs and any literal backslashes are already embedded in the included PDF. Tectonic cannot retroactively expand `\qty`, `\unit`, or `\ce` inside that graphic.

The verified native experiment with Matplotlib 3.10.9 and Tectonic 0.17.0 fails at configuration:

```text
ValueError: Key pgf.texsystem: 'tectonic' is not a valid value for pgf.texsystem; supported values are ['xelatex', 'lualatex', 'pdflatex']
```

Putting `\qty` in MathText fails before the wrapper stage with `ParseFatalException: Unknown symbol: \qty`; placing it outside math draws literal command text. Therefore native `siunitx`/`mhchem` expansion in Matplotlib labels is **TECHNICALLY BLOCKED / DEFERRED**. Do not report the standalone package probe as evidence of plot-label macro support.

The stable vector wrapper remains the production path. A future TeX-native route must first prove Tectonic macro expansion, fonts, text extraction, physical geometry, error handling, and the complete PDF/PNG pipeline in an isolated end-to-end prototype; do not introduce a backend monkeypatch.
