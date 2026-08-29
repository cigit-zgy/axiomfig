# Canonical color contract

`styles/colors.yaml` is the only maintained palette source. `axiomfig.colors.palettes()` returns its validated mappings, and `render_xcolor()` generates `src/axiomfig/resources/latex/axiomfig-colors.tex` from the default palette. Do not maintain RGB lists in Python, templates, `.mplstyle`, or prose.

The canonical palette set is:

- `tol_bright` and `tol_muted`: exact qualitative schemes published by Paul Tol;
- `axiom_classic`: AxiomFig's stable default palette;
- `axiom_soft`: a lower-contrast AxiomFig alternative;
- `grayscale`: deterministic monochrome mapping.

The default `axiom_classic` palette is:

| Token | HTML |
|---|---|
| `AxiomBlue` | `315A7D` |
| `AxiomCyan` | `5596A6` |
| `AxiomGreen` | `4B7F52` |
| `AxiomYellow` | `C2A23A` |
| `AxiomOrange` | `C46D3B` |
| `AxiomRed` | `A94E59` |
| `AxiomPurple` | `735C8E` |
| `AxiomGrey` | `7F858B` |

Paul Tol's canonical reference is <https://sronpersonalpages.nl/~pault/>. The `axiom_*` palettes are project-defined rather than attributed to Tol. Qualitative colors are discrete and must not be interpolated into a continuous map.

After changing the source, run:

```bash
python scripts/generate_colors.py
python scripts/generate_colors.py --check
python -m pytest -q tests/test_colors.py
```

A palette change requires Gallery regeneration and visual inspection.
