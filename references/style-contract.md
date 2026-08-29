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

`main_stroke = 0.8 pt` applies to spines, normal data lines, major ticks, error bars, and reference lines. `fill_edge = 0.6 pt` applies to black edges of every filled bar, violin body, filled scatter marker, and other filled patch.

Use color, alpha, linestyle, or fill for hierarchy. A template may not create a second baseline stroke width.

## Tick surfaces

| Axis kind | Major | Minor | Notes |
|---|---|---|---|
| open continuous | `inout` | `in` | exactly one minor between majors |
| filled surface (`bar`, `heatmap`, `image`) | `out` | `out` | exactly one minor between numeric majors |
| categorical | none | none | labels remain |

For open axes, the configured major length is `4 pt`. Raster measurement confirms that Matplotlib divides an `inout` tick approximately equally across the spine, so its inward projection is `2 pt`. The minor length is therefore `0.618 × 2 pt = 1.236 pt`. This is a measured geometry contract, not an inference from the parameter name.

`AutoMinorLocator(2)` yields one minor tick per major interval. Log axes keep their mathematical locators and do not use the deterministic linear-axis rule.

## Nice linear axes

`nice_linear_axis()` targets 5–7 major ticks and chooses only `1`, `2`, `2.5`, or `5 × 10^n`. After choosing major step `Δ`, it sets minor step `Δ/2`. Limits normally snap to integer multiples of `Δ`; when whole-step expansion creates unnecessary blank space beyond the configured threshold, half-step endpoints are allowed. Ordinary linear scientific axes must not retain visually arbitrary start or end values.

## Plot defaults

- Line markers and errorbar markers: `5.2 pt`, black `0.6 pt` edge; errorbar caps are `2.5 pt`.
- Confidence intervals: alpha `0.22`, black `0.6 pt` edge.
- Scatter: black `0.6 pt` edge, alpha `0.55`, marker area `36 pt²`.
- Bar: black `0.6 pt` edge, value labels enabled, two decimals, no category tick marks.
- Box/violin: black `0.6 pt` edges, YAML-owned fill alpha/width, and no category tick marks.
- Histogram: black `0.6 pt` bin edges.
- Heatmap/image: filled-surface tick directions; colorbar is separate support axes.

## Fixed-page output margins

The default output mode is `tight` with `1.5 pt` physical padding. A centralized post-layout solver measures all visible artists and adjusts subplot margins while preserving the requested page size. `normal` leaves the configured layout margins unchanged; `custom` is reserved as a validated configuration value. Templates must not implement their own crop or `bbox_inches` policy.
