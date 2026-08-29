# Deterministic style contract

## Canonical sources

`styles/style.yaml`, `styles/fonts.yaml`, and `styles/colors.yaml` are the only root visual configuration sources. `axiomfig.config.load_contracts()` loads and freezes their mappings; `build_rcparams()` translates the selected geometry and typography into a small `rcParams` mapping. Templates consume tokens through helpers and must not duplicate token values.

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

Raster measurement confirms that Matplotlib divides an `inout` tick approximately equally across the spine. Round 04 lengthens the previous `1.236 pt` minor by 1.5 to `1.854 pt`. With φ = `0.6180339887`, the required major inward projection is `1.854 / φ`, approximately `3 pt`, so the central Matplotlib `inout` major parameter is `2 × 1.854 / φ = 5.9996700308 pt`. Filled numeric axes and colorbars reuse `5.9996700308 pt` major and `1.854 pt` minor lengths with outward direction. These values are one derived central relationship, not duplicated magic numbers.

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

## Redundant series identity

Multi-series graphics use one ordered central cycle that combines palette color, line style, and marker. The first four styles are solid/circle, dash-dot/square, dotted/triangle, and long-dash/diamond. The custom long-dash pattern is `6 pt on, 2 pt off`. Secondary and reference lines default to dash-dot. Templates call the shared helper by series index and do not replace these channels locally.

## Fixed-page output margins

The default output mode is `tight` with `1.5 pt` physical padding. A centralized post-layout solver measures all visible artists and adjusts subplot margins while preserving the requested page size. `normal` leaves the configured layout margins unchanged; `custom` is reserved as a validated configuration value. Templates must not implement their own crop or `bbox_inches` policy.
