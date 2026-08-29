# Canonical color contract

`styles/colors.yaml` is the only maintained palette source. `axiomfig.colors.palettes()` returns its validated mappings, and `render_xcolor()` generates both repository/package LaTeX color files. Do not maintain RGB lists in Python, templates, `.mplstyle`, or prose.

The canonical palette set is:

- `tol_bright` and `tol_muted`: exact qualitative schemes published by Paul Tol;
- `axiom_classic`: AxiomFig's stable default palette;
- `axiom_soft`: a lower-contrast AxiomFig alternative;
- `axiom_deep`: a darker high-contrast alternative;
- `axiom_warm`: a warm-shifted balanced alternative;
- `axiom_cool`: a cool-shifted balanced alternative;
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

Each Axiom palette contains the same eight semantic suffixes: Blue, Cyan, Green, Yellow, Orange, Red, Purple, and Grey. The default keeps short names such as `AxiomBlue`; generated LaTeX also exposes palette-qualified names such as `AxiomClassicBlue`, `AxiomSoftBlue`, `AxiomDeepBlue`, `AxiomWarmBlue`, and `AxiomCoolBlue`.

After changing the source, run:

```bash
python scripts/generate_colors.py
python scripts/generate_colors.py --check
python -m pytest -q tests/test_colors.py
```

A palette change requires Gallery regeneration and visual inspection.
