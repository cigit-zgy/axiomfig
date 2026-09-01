# Deterministic style contract

Agent-facing non-default requests route through `references/element-contracts/index.md`; this file
remains the deterministic implementation contract and numeric source-of-truth guide.

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

The named geometry presets and all of their physical dimensions and aspect ratios are defined only
in `style.yaml`. Font sizes use physical units and do not scale with figure width.

## Strokes and filled artists

The shared `main_stroke` token applies to spines, normal data lines, major ticks, error bars, and
reference lines. The `fill_edge` token applies to black edges of every filled bar, violin body,
filled scatter marker, and other filled patch. Fill alpha is encoded only in face RGBA; edge RGBA is
always opaque. Artist-wide alpha is forbidden because it also makes the edge translucent.

Use color, alpha, linestyle, or fill for hierarchy. A template may not create a second baseline stroke width.

## Tick surfaces

| Axis kind | Major | Minor | Notes |
|---|---|---|---|
| open continuous | `inout` | `in` | exactly one minor between majors |
| filled surface (`bar`, `heatmap`, `image`) | `out` | `out` | exactly one minor between numeric majors |
| categorical | none | none | labels remain |

The runtime derives open, filled, and Colorbar tick lengths from the shared tick tokens in
`style.yaml`. A Colorbar converts the central `inout` major contract to its outward-only equivalent;
it does not own a second independent length token.

The configured linear minor-tick divisor yields deterministic subdivisions between major ticks. Log axes keep their mathematical locators and do not use the linear-axis rule.

## Nice linear axes

`nice_linear_axis()` uses the YAML-owned bounded tick target and approved step sequence. After
choosing major step `Δ`, it derives the minor step and snaps limits according to the configured
endpoint policy. Ordinary linear scientific axes must not retain visually arbitrary endpoints.

## Plot defaults

- Line markers and errorbar markers use their shared marker, edge, and cap tokens.
- Confidence intervals use the shared translucent-face and opaque-edge contract.
- Scatter uses the shared opaque-edge, face-alpha, and marker-area tokens.
- Dense raw distribution observations reuse the scatter face/edge contract with their dedicated
  marker-area token. ECDF sampling is bounded deterministically so the empirical step remains the
  dominant artist.
- Hexbin count is a continuous quantitative color encoding and therefore uses
  the global vertical Colorbar contract rather than an unlabelled palette.
- Bar uses the YAML-owned opaque-edge, face-alpha, value-label, and categorical-width contracts.
- Box/violin use the shared edge contract and YAML-owned fill and width tokens.
- Histogram uses its YAML-owned face alpha with the shared opaque bin-edge contract.
- Heatmap/image: filled-surface tick directions; colorbar is separate support axes.

## Square matrix geometry

A matrix whose two axes represent the same variables must render with equal physical width and
height. Its cells must therefore have equal physical width and height, not merely equal data
increments. `set_aspect("equal")` is an implementation aid rather than sufficient evidence:
runtime validation measures the final renderer transform against the YAML-owned square and cell
tolerances. Auxiliary axes and outer ornaments must not distort the square.

## Colorbar contract

A Colorbar is the continuous color scale (continuous color legend) for a scalar mapping; it is not
a categorical legend. The global vertical Colorbar contract is stored only in `style.yaml`:

- physical width: the vertical Colorbar width token;
- gap from its reference visual region: the vertical Colorbar gap token;
- length: the vertical Colorbar length-fraction token applied to the reference square height;
- alignment: vertically centered on the reference square;
- position: outside-right;
- major/minor ticks: the shared filled-axis tick contract;
- tick labels and the concise scalar label: right side.

The vertical Colorbar occupies a measured right Ornament Strip. Its reservation is the configured
gap and width, actual renderer-measured right tick/label overhang, and containment padding. Its compact
height does not reserve top or bottom space. The layout subsystem owns the Auxiliary Axes dimensions
and placement and maximizes the remaining Primary Visual Area. A template supplies only the scalar
mapping, tick values, label, and an optional data-space reference square. It must not set a local box
aspect, inset position, width, gap, or length. Categorical keys continue to use ordinary legend
artists rather than a Colorbar. Horizontal Colorbar geometry remains intentionally unspecified
until a real production consumer requires it.

## Redundant series identity

Multi-series graphics use one ordered central cycle that combines palette color, line style, and
marker. The exact sequence and custom dash pattern live only in `style.yaml`. Secondary and
reference lines use the shared reference-line style. Templates call the shared helper by series
index and do not replace these channels locally.

## Fixed-page output margins

The default output mode and physical padding live only in `style.yaml`. Ordinary single panels retain
the centralized fixed-page margin solver. Registered panel grids reserve the output boundary in
advance, perform one measurement/formula solve, and then run anatomy validation; they are never moved
by the single-panel solver. `normal` leaves configured single-panel margins unchanged, and `custom`
remains a validated configuration value. Templates must not implement crop, `bbox_inches`, or
trial-and-error placement.
