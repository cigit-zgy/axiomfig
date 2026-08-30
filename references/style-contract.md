# Deterministic style contract

## Canonical sources

`src/axiomfig/resources/styles/style.yaml`, `fonts.yaml`, and `colors.yaml` are the only visual
configuration sources. `axiomfig.config.load_contracts()` loads the same package resources from a
source checkout or installed wheel. `build_rcparams()` translates the selected geometry and
typography into a small `rcParams` mapping. Templates consume `axiomfig.style` and must not
duplicate token values.

`colors.yaml` owns qualitative, sequential, diverging, and cyclic colormaps plus the canonical
palette set. Templates request a scientific color semantic through `semantic_colormap()` and do
not hard-code map names. Diverging data requires an explicit meaningful center. `render_xcolor()`
generates the matching LaTeX definitions; RGB lists are not maintained in Python or prose.

The default `axiom_classic` tokens are `AxiomBlue`, `AxiomCyan`, `AxiomGreen`, `AxiomYellow`,
`AxiomOrange`, `AxiomRed`, `AxiomPurple`, and `AxiomGrey`. Paul Tol's exact `tol_bright` and
`tol_muted` schemes are attributed to <https://sronpersonalpages.nl/~pault/>; the `axiom_*`
palettes are project-defined.

## Geometry and physical typography

| Geometry | Width | Default height | Aspect |
|---|---:|---:|---:|
| `single-column` | 90 mm | 67.5 mm | 4:3 |
| `onehalf-column` | 140 mm | 105 mm | 4:3 |
| `double-column` | 190 mm | 142.5 mm | 4:3 |

Font sizes are physical points and do not scale with figure width.

## Strokes and filled artists

`main_stroke = 0.8 pt` applies to spines, normal data lines, major ticks, error bars, and reference lines. `fill_edge = 0.6 pt` applies to black edges of every filled bar, violin body, filled scatter marker, and other filled patch. Fill alpha is encoded only in face RGBA; edge RGBA is always opaque. Artist-wide alpha is forbidden because it also makes the edge translucent.

Use color, alpha, linestyle, or fill for hierarchy. A template may not create a second baseline stroke width.

## Tick surfaces

| Axis kind | Major | Minor | Notes |
|---|---|---|---|
| open continuous | `inout` | `in` | exactly one minor between majors |
| filled surface (`bar`, `heatmap`, `image`) | `out` | `out` | exactly one minor between numeric majors |
| categorical | none | none | labels remain |

Raster measurement confirms that Matplotlib divides an `inout` tick approximately equally across the spine. Round 04 lengthens the previous `1.236 pt` minor by 1.5 to `1.854 pt`. With φ = `0.6180339887`, the required major inward projection is `1.854 / φ`, approximately `3 pt`, so the central Matplotlib `inout` major parameter is `2 × 1.854 / φ = 5.9996700308 pt`. Filled numeric axes reuse that total with outward direction. A colorbar deletes the inward half and therefore derives its outward major as `5.9996700308 / 2 pt`; its minor remains `1.854 pt`. No second colorbar length token exists.

`AutoMinorLocator(2)` yields one minor tick per major interval. Log axes keep their mathematical locators and do not use the deterministic linear-axis rule.

## Nice linear axes

`nice_linear_axis()` targets 5–7 major ticks and chooses only `1`, `2`, `2.5`, or `5 × 10^n`. After choosing major step `Δ`, it sets minor step `Δ/2`. Limits normally snap to integer multiples of `Δ`; when whole-step expansion creates unnecessary blank space beyond the configured threshold, half-step endpoints are allowed. Ordinary linear scientific axes must not retain visually arbitrary start or end values.

## Plot defaults

- Line markers and errorbar markers: `5.2 pt`, black `0.6 pt` edge; errorbar caps are `2.5 pt`.
- Confidence intervals: face alpha `0.22`, opaque black `0.6 pt` edge.
- Scatter: opaque black `0.6 pt` edge, face alpha `0.55`, marker area `36 pt²`.
- Bar: opaque black `0.6 pt` edge, face alpha `0.82`, value labels enabled, two decimals, no category tick marks. Single-series width is exactly `0.60`; grouped total width is exactly `0.76`, divided by series count and independent of category count.
- Box/violin: black `0.6 pt` edges, YAML-owned fill alpha/width, and no category tick marks.
- Histogram: face alpha `0.72` with opaque black `0.6 pt` bin edges.
- Heatmap/image: filled-surface tick directions; colorbar is separate support axes.

## Square matrix geometry

A matrix whose two axes represent the same variables must render with equal physical width and
height. Its cells must therefore have equal physical width and height, not merely equal data
increments. `set_aspect("equal")` is an implementation aid rather than sufficient evidence:
runtime validation measures the final renderer transform and rejects a primary visual square whose
width and height differ by more than `0.5 px` or whose cell dimensions differ by more than
`0.1 px`. Auxiliary axes and outer ornaments must not distort the square.

## Colorbar contract

A Colorbar is the continuous color scale (continuous color legend) for a scalar mapping; it is not
a categorical legend. The global vertical Colorbar contract is stored only in `style.yaml`:

- physical width: `9 pt`;
- gap from its reference visual region: `6 pt`;
- length: `0.72` times the reference square height;
- alignment: vertically centered on the reference square;
- position: outside-right;
- major/minor ticks: the shared filled-axis tick contract;
- tick labels and the concise scalar label: right side.

The layout subsystem owns the Auxiliary Axes dimensions and placement. A template supplies only
the scalar mapping, tick values, label, and the data-space reference square. It must not set a local
box aspect, inset position, width, gap, or length. Categorical keys continue to use ordinary legend
artists rather than a Colorbar.

## Redundant series identity

Multi-series graphics use one ordered central cycle that combines palette color, line style, and marker. The first four styles are solid/circle, dash-dot/square, dotted/triangle, and long-dash/diamond. The custom long-dash pattern is `6 pt on, 2 pt off`. Secondary and reference lines default to dash-dot. Templates call the shared helper by series index and do not replace these channels locally.

## Fixed-page output margins

The default output mode is `tight` with `1.5 pt` physical padding. Ordinary single panels retain the centralized fixed-page margin solver. Registered panel grids reserve the output boundary in advance, perform one measurement/formula solve, and then run anatomy validation; they are never moved by the single-panel solver. `normal` leaves configured single-panel margins unchanged, and `custom` remains a validated configuration value. Templates must not implement crop, `bbox_inches`, or trial-and-error placement.
