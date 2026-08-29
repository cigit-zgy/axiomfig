# Canonical color contract

## One source

`axiomfig.colors.PALETTES` is the only maintained color source. The values are Paul Tol qualitative schemes expressed as six-digit uppercase HTML RGB. Do not hand-edit generated `.mplstyle` or xcolor files and do not treat xcolor's built-in names as a validated scientific palette.

The default bright palette is:

| Token | HTML |
|---|---|
| `AxiomBlue` | `4477AA` |
| `AxiomRed` | `EE6677` |
| `AxiomGreen` | `228833` |
| `AxiomYellow` | `CCBB44` |
| `AxiomCyan` | `66CCEE` |
| `AxiomPurple` | `AA3377` |
| `AxiomGrey` | `BBBBBB` |

Matplotlib also exposes the verified Paul Tol `muted` and three-color `colorblind` cycles. Qualitative colors are discrete; do not interpolate them into a continuous map.

## Generated consumers

`python scripts/generate_colors.py` renders all Matplotlib color styles and the default xcolor definitions from the canonical Python mapping:

```text
axiomfig.colors.PALETTES
  -> styles/colors/default.mplstyle
  -> styles/colors/muted.mplstyle
  -> styles/colors/colorblind.mplstyle
  -> src/axiomfig/resources/latex/axiomfig-colors.tex
```

The xcolor artifact contains `\definecolor{AxiomBlue}{HTML}{4477AA}` and corresponding definitions for every default token. Tests compare the complete generated default mapping to `PALETTES["default"]`, so Matplotlib and xcolor cannot drift independently. The standalone package inputs this generated file.

After changing the canonical mapping, regenerate and verify:

```bash
python scripts/generate_colors.py
python scripts/generate_colors.py --check
python -m pytest -q tests/test_colors.py
```

Changing the palette is a contract change: update the source mapping, regenerate both consumers, render the gallery, and inspect categorical distinguishability. Do not maintain a second RGB list in templates or prose.
