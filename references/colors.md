# Canonical color contract

`styles/colors.yaml` is the only maintained palette source. `axiomfig.colors.palettes()` returns its validated mappings, and `render_xcolor()` generates `src/axiomfig/resources/latex/axiomfig-colors.tex` from the default palette. Do not maintain RGB lists in Python, templates, `.mplstyle`, or prose.

The default qualitative palette is:

| Token | HTML |
|---|---|
| `AxiomBlue` | `4477AA` |
| `AxiomRed` | `EE6677` |
| `AxiomGreen` | `228833` |
| `AxiomYellow` | `CCBB44` |
| `AxiomCyan` | `66CCEE` |
| `AxiomPurple` | `AA3377` |
| `AxiomGrey` | `BBBBBB` |

`muted` and `colorblind` are explicit alternatives. Qualitative colors are discrete and must not be interpolated into a continuous map.

After changing the source, run:

```bash
python scripts/generate_colors.py
python scripts/generate_colors.py --check
python -m pytest -q tests/test_colors.py
```

A palette change requires Gallery regeneration and visual inspection.
