# Trend and comparison routing

Use this topic when the request concerns an ordered trajectory or compares categorical magnitudes. Before selecting a template, identify what is ordered, what is categorical, whether continuity is scientifically meaningful, and whether the available values are observations, estimates, or parts of a total. Do not turn repeated observations into summary bars merely because a group label is present.

## Choose among line templates

- `line.single` shows one response over an ordered x variable when progression or trajectory is the scientific message.
- `line.multi` compares several trajectories on the same ordered x domain. Series must represent comparable quantities and units if they share an axis. Its executable contract takes a supplied series-by-shared-x matrix and one label per matrix row; it is not a long-form subject-paired slope grammar.
- `line.marker` is appropriate when sampled locations themselves matter.
- `line.confidence_band` shows a supplied estimate with supplied lower and upper bounds whose interval meaning is explicit.
- `line.errorbar` shows pointwise estimates with supplied uncertainty.
- `line.step` represents an event-driven or piecewise-constant process.
- `line.area` emphasizes magnitude relative to a meaningful supplied baseline.

A line visually connects observations. The connection is warranted when x is ordered and the scientific story concerns change across that order. It does not establish mechanistic continuity, interpolation, or causality. For unordered quantitative x-y relationships, route to scatter. For categorical x, route to bars, dots, or distribution graphics according to whether the values are magnitudes, summaries, or observations.

## Choose among categorical comparison templates

- `bar.simple` encodes one supplied categorical magnitude. Vertical and horizontal are semantic orientations of the same grammar and schema.
- `bar.grouped` compares supplied group magnitudes within categories. Sparse category/group combinations are allowed as absent bars; missing is not zero. Supplied uncertainty requires an explicit uncertainty type.
- `bar.stacked` shows additive part-to-whole magnitudes while preserving total magnitude.
- `bar.normalized_stacked` shows composition after an explicit normalization decision. `normalization=normalize` is the registered deterministic within-category plotting normalization; `normalization=proportion` means supplied values are already proportions. This display normalization does not authorize other statistical/domain normalization.
- `bar.grouped_stacked`, `bar.diverging_stacked`, `bar.range`, `bar.mirrored`, and `bar.waterfall` own distinct hierarchy, sign, endpoint, side, and cumulative semantics. After Bar selection, read `families/bar.md` for exact tabular contracts.

Magnitude bars normally require a meaningful zero baseline because bar length encodes value. A bar with uncertainty still hides the underlying observations/distribution. When replicate-level variation matters, route to `distribution.strip`, `distribution.box`, `distribution.violin`, `distribution.box_violin`, or `distribution.raincloud` instead of silently aggregating.

## Scientific distinctions

| Scientific question | Appropriate grammar |
|---|---|
| How does one quantity change over ordered x? | `line.single` or `line.marker` |
| How do comparable trajectories differ? | `line.multi` |
| What is supplied uncertainty around a trajectory? | `line.confidence_band` |
| What is uncertainty at individual estimates? | `line.errorbar` |
| When does a state change discretely? | `line.step` |
| What magnitude exists relative to a meaningful baseline? | `line.area` |
| Which category has a larger supplied magnitude? | `bar.simple` |
| How do group magnitudes compare within categories? | `bar.grouped` |
| How much does each component contribute to a total? | `bar.stacked` |
| How do compositions compare after explicit plotting normalization? | `bar.normalized_stacked` |
| How do components compare within category-group combinations? | `bar.grouped_stacked` |
| Which signed components accumulate around zero? | `bar.diverging_stacked` |
| What supplied lower-to-upper span belongs to each category? | `bar.range` |
| How do two comparable sides differ around zero? | `bar.mirrored` |
| How do explicit changes reconcile to a final total? | `bar.waterfall` |
| How are replicate values distributed? | distribution topic, not summary bars |

## Ask when

Ask a minimal clarification when:

- x could be ordered time/dose or an unordered quantitative covariate;
- uncertainty fields are supplied without SD, SE, CI, PI, credible-interval, or other explicit meaning;
- connecting measurements would imply a trajectory the design does not support;
- a requested filled area has no scientifically meaningful baseline;
- normalized and unnormalized stacked bars would answer different questions and intent is unclear;
- values on a shared axis may have incompatible quantities/units;
- the user supplies raw replicates but asks for a grouped magnitude comparison without specifying an upstream summary.

Do not ask about line width, marker/bar size, colors, tick direction, legend placement, or figure dimensions. The deterministic runtime owns those decisions.

## Require upstream computation when

Require supplied scientific/statistical results rather than calculating them when the request needs an estimator, SD/SE/CI/PI computation, fitted trajectory, batch/reference correction, domain normalization denominator, or another scientific aggregation/normalization that is not explicitly owned by a registered plotting grammar.

AxiomFig may execute deterministic transformations that are explicitly part of a registered grammar, such as `bar.normalized_stacked` with `normalization=normalize`. That operation changes the display to within-category composition; it does not select a scientific estimator or infer a domain normalization rule.

A lossless column mapping is input normalization. Computing a statistical summary or undeclared scientific transformation is analysis.

## Do not infer

Never infer uncertainty type, interpolation, cumulative meaning, normalization denominator, component conservation, units, or causal direction. Do not equate adjacent measurements with a continuous process. Do not call a confidence band a prediction band, or SD an SE. Do not turn raw replicates into means solely to fit a bar template. For grouped bars, a missing category/group row is absent and must not be invented as zero.

## Common misuse

- Connecting unordered categories and describing the result as a trend.
- Using `line.step` only because its shape looks distinctive.
- Filling an area to zero when zero has no scientific meaning.
- Showing mean bars for small replicate sets while hiding every observation.
- Comparing normalized component shares as if original totals were equal.
- Treating overlap/non-overlap of unspecified uncertainty intervals as a hypothesis test.
- Filling missing grouped combinations with zero merely to obtain a rectangular table.

## Evidence

- Cumming, Fidler, and Vaux, [Error bars in experimental biology](https://doi.org/10.1083/jcb.200611141), distinguishes standard deviation, standard error, and confidence-interval displays.
- Weissgerber et al., [Beyond Bar and Line Graphs](https://doi.org/10.1371/journal.pbio.1002128), demonstrates that identical summaries can conceal materially different continuous-data distributions.
