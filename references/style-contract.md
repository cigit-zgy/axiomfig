# Deterministic style contract

## Composition and ownership

The fixed order is:

```text
base -> geometry -> typography -> colors -> plot -> language -> rendering
```

`StyleSelection.paths()` resolves one file per layer; `compose_styles()` fails on duplicate rcParams unless `src/axiomfig/styles.py` declares the exact layer pair and key. `ALLOWED_OVERRIDES` permits base-to-plot `xtick.direction`/`ytick.direction` changes and a typography-to-language `font.family` change; the current multilingual module preserves the selected family and sets only `font.stretch`. Templates own data transforms, labels, units, annotations, justified limits, and panel arrangement; they do not set contract rcParams or physical width.

| Layer | Owns |
|---|---|
| base | point sizes, central strokes, axes/tick/legend geometry, faces, layout |
| geometry | `figure.figsize` |
| typography | one complete Latin/math/CJK/mono mode |
| colors | `axes.prop_cycle` |
| plot | archetype-specific marker, patch, image, and filled-surface tick properties |
| language | multilingual metadata; templates still segment language runs explicitly |
| rendering | PDF font type, preview DPI, output format, transparency |

## Geometry

Typography remains in physical points rather than scaling with width.

| Preset | Width | Default height | Inches |
|---|---:|---:|---:|
| `single-column` | 90 mm | 67.5 mm | 3.543307 x 2.657480 |
| `onehalf-column` | 140 mm | 105 mm | 5.511811 x 4.133858 |
| `double-column` | 190 mm | 142.5 mm | 7.480315 x 5.610236 |

## Tick contract

Call `apply_axis_contract(axis, surface="open")` for line and scatter data axes and `surface="filled"` for bar, distribution, heatmap, image, or matrix data axes. Apply it once per data-bearing axes, not to Matplotlib-generated support axes such as a colorbar; the colorbar keeps the locator and tick geometry created by Matplotlib.

| Surface | Major | Minor | Linear minor locator |
|---|---|---|---|
| open | `inout` | `in` | `AutoMinorLocator(2)` |
| filled | `out` | `out` | `AutoMinorLocator(2)` |

`AutoMinorLocator(2)` yields exactly one minor tick between adjacent major ticks. The helper does not replace a logarithmic axis locator; log axes retain mathematical minor-tick semantics while adopting the selected direction.

## Unified strokes

`axiomfig.contracts.STROKE_WIDTH_PT` is `0.6`. The publication style applies it to spines, data lines, major/minor ticks, marker edges, patch/bar edges, boxplot boxes/caps/medians/whiskers, and the defaults inherited by error bars, cap lines, reference lines, and annotation strokes. Bar and scatter helpers reassert the same token at artist level.

Use color, alpha, linestyle, or fill for hierarchy. Override the width only when the user explicitly requests it; do not create a second hidden baseline inside a template.

## Related contracts

- Read [layout.md](layout.md) for panel-label and legend geometry.
- Read [colors.md](colors.md) for Paul Tol tokens and xcolor generation.
- Read [typography.md](typography.md) before selecting or applying a font family.
- Read [templates.md](templates.md) for helper ownership by archetype.
