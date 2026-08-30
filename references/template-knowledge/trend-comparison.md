# Trend and comparison routing

Use this topic when the request concerns an ordered trajectory or compares categorical magnitudes.
Before selecting a template, identify what is ordered, what is categorical, whether continuity is
scientifically meaningful, and whether the available values are observations, estimates, or
parts of a total. Do not turn repeated observations into summary bars merely because a group label
is present.

## Choose among line templates

- `line.single` shows one response over an ordered x variable when progression or trajectory is
  the scientific message.
- `line.multi` compares several trajectories on the same ordered x domain. Series must represent
  comparable quantities and units if they share an axis.
- `line.marker` is appropriate when the sampled locations themselves matter. Markers identify
  observations; they are not decorative additions to an otherwise continuous curve.
- `line.confidence_band` shows a supplied estimate with supplied lower and upper bounds. The
  interval meaning must be explicit, for example confidence, prediction, or credible interval.
- `line.errorbar` shows pointwise estimates with supplied uncertainty. Use it when uncertainty is
  attached to distinct observations or estimates rather than forming a continuous envelope.
- `line.step` represents an event-driven or piecewise-constant process. Do not choose it as a
  stylistic alternative to a smooth or linearly connected trajectory.
- `line.area` emphasizes magnitude relative to a meaningful supplied baseline. Filling can suggest
  accumulated quantity or contribution, so do not use it when that implication is unsupported.

A line visually connects observations. The connection is warranted when x is ordered and the
scientific story concerns change across that order. It does not establish mechanistic continuity,
interpolation, or causality. For unordered quantitative x-y relationships, route to the scatter
templates instead. For categorical x, route to bars, dots, or distribution graphics according to
whether the available values are magnitudes, summaries, or observations.

## Choose among categorical comparison templates

- `bar.vertical` and `bar.horizontal` encode one categorical magnitude per category. Horizontal
  bars are often the clearer contract for long category labels; this is a routing decision about
  label legibility, not a new scientific meaning.
- `bar.grouped` compares magnitudes for combinations of category and group. Supplied error values
  require an explicit uncertainty type; their presence does not make the bars a distribution plot.
- `bar.stacked` shows part-to-whole magnitudes while preserving the total. Components and totals
  must share a coherent quantity and unit.
- `bar.normalized_stacked` shows composition after an explicit normalization. It removes total
  magnitude from the message and therefore must not substitute for ordinary stacking when totals
  matter.
- `bar.dot` compares categorical magnitudes with less visual mass than bars. Prefer it when precise
  positions matter and filled rectangles add no scientific information.

Magnitude bars normally require a meaningful zero baseline because bar length encodes value.
Never choose a truncated magnitude bar merely to magnify small differences. A bar with an error
bar still hides the underlying observations and distribution: several very different distributions
can share the same mean and uncertainty summary. When replicate-level values are available and
their variation matters, route to `distribution.strip`, `distribution.box`,
`distribution.violin`, `distribution.box_violin`, or `distribution.raincloud` instead of silently
aggregating.

## Scientific distinctions

Separate these questions before routing:

| Scientific question | Appropriate grammar |
|---|---|
| How does one quantity change over ordered x? | `line.single` or `line.marker` |
| How do comparable trajectories differ? | `line.multi` |
| What is the supplied uncertainty around a trajectory? | `line.confidence_band` |
| What is the uncertainty at individual estimates? | `line.errorbar` |
| When does a state change discretely? | `line.step` |
| What magnitude exists relative to a meaningful baseline? | `line.area` |
| Which category has a larger supplied magnitude? | bar or `bar.dot` |
| How do group magnitudes compare within categories? | `bar.grouped` |
| How much does each component contribute to a total? | `bar.stacked` |
| How do compositions compare after normalization? | `bar.normalized_stacked` |
| How are replicate values distributed? | distribution topic, not summary bars |

## Ask when

Ask a minimal clarification when:

- x could be ordered time/dose or merely an unordered quantitative covariate;
- an `error`, `lower`, or `upper` field is supplied without SD, SE, CI, PI, credible-interval, or
  other explicit meaning;
- connecting measurements would imply a trajectory that the design does not support;
- a requested filled area has no scientifically meaningful baseline;
- normalized and unnormalized stacked bars would answer different questions and the intended one
  is unclear;
- values on a shared axis may have incompatible quantities or units;
- the user asks which group is "higher" but supplies replicates and does not say whether the goal
  is distribution comparison or a precomputed summary comparison.

Do not ask about line width, marker size, bar width, colors, tick direction, legend placement, or
figure dimensions. The deterministic runtime owns those decisions.

## Require upstream computation when

Require supplied results rather than calculating them when the request needs estimates,
uncertainty limits, normalization, aggregation, or a fitted trajectory not already present in the
data. AxiomFig can display supplied mean and interval values; it does not decide the estimator,
calculate SD/SE/CI/PI, fit a smoother, or choose a scientifically meaningful aggregation. A
lossless column mapping is normalization; computing a statistical summary is analysis.

## Do not infer

Never infer uncertainty type, interpolation, cumulative meaning, normalization denominator,
component conservation, units, or causal direction. Do not equate adjacent measurements with a
continuous process. Do not call a confidence band a prediction band, or a standard-deviation bar a
standard-error bar. Do not turn raw replicates into means solely to fit a bar template.

## Common misuse

- Connecting unordered categories and describing the result as a trend.
- Using `line.step` only because its shape looks distinctive.
- Filling an area to zero when zero has no scientific meaning.
- Showing mean bars for small replicate sets while hiding every observation.
- Comparing normalized component shares as if their original totals were equal.
- Treating overlap or non-overlap of unspecified error bars as a hypothesis test.

## Evidence

- Cumming, Fidler, and Vaux, [Error bars in experimental biology](https://doi.org/10.1083/jcb.200611141), distinguishes standard deviation, standard error, and confidence-interval displays.
- Weissgerber et al., [Beyond Bar and Line Graphs](https://doi.org/10.1371/journal.pbio.1002128), demonstrates that identical summaries can conceal materially different continuous-data distributions.
