# Deterministic style contract

## Composition

The fixed order is:

```text
base -> geometry -> typography -> colors -> plot -> language -> rendering
```

Later layers may override earlier layers only when `src/axiomfig/styles.py` declares the exact key and layer pair. Version 0.1 permits one override: `language` changes `font.family` after `typography` so the explicit multilingual family list is active. Every other duplicate rcParam is an error.

| Layer | Owns |
|---|---|
| base | point sizes, axes/tick/legend geometry, face colors, layout |
| geometry | `figure.figsize` only |
| typography | Latin/math family and MathText mapping |
| colors | `axes.prop_cycle` only |
| plot | line/marker/patch/image properties specific to an archetype |
| language | ordered multilingual family list |
| rendering | PDF font type, preview DPI, output format and transparency |

Templates own data transforms, plot calls, labels, units, legend placement, annotations, axis limits justified by data, and multi-panel arrangement. They must not set contract rcParams or physical figure width.

## Geometry

The presets keep base typography in physical points rather than scaling it with figure width.

| Preset | Width | Default height | Inches |
|---|---:|---:|---:|
| single-column | 90 mm | 67.5 mm | 3.543307 x 2.657480 |
| onehalf-column | 140 mm | 105 mm | 5.511811 x 4.133858 |
| double-column | 190 mm | 142.5 mm | 7.480315 x 5.610236 |

## Axes, ticks, lines, and panels

Publication base text is 8.5 pt; tick and legend text is 7.5 pt. Axes are 0.55 pt. Major ticks are 3.2 pt and point `inout`; minor ticks are 1.6 pt and remain visible. Plot styles own restrained data-line and marker-edge widths. Legends have no frame unless a future explicit module says otherwise.

Single-panel templates do not add `(a)`. Multi-panel helpers add bold `(a)`, `(b)`, and subsequent labels with one anchor and offset.

## Color

`default` is Paul Tol bright, `muted` is Paul Tol muted, and `colorblind` is Paul Tol high-contrast. The high-contrast scheme is preferred when monochrome separation matters. The hexadecimal values follow [Paul Tol's current official scheme definitions](https://sronpersonalpages.nl/~pault/). Do not interpolate qualitative palettes.
