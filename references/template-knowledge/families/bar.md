# Bar charts

## Scientific role

Use the Bar family for supplied categorical magnitudes, parts of categorical totals, explicit ranges, paired mirrored magnitudes, or a supplied cumulative change sequence. A bar encodes quantity by length from a scientifically meaningful baseline. It is not a default summary of raw replicates, a distribution display, or an instruction to aggregate rows.

The Agent selects a scientific grammar first and then applies semantic modifiers when needed. Vertical and horizontal forms carry the same data meaning and use the same canonical tabular schema.

## Grammar taxonomy

| Grammar | Scientific question | Canonical columns |
|---|---|---|
| `bar.simple` | What supplied magnitude belongs to each category? | `category`, `value` |
| `bar.grouped` | How do supplied group magnitudes compare within categories? | `category`, `group`, `value` |
| `bar.stacked` | How do supplied components contribute to each categorical total? | `category`, `component`, `value` |
| `bar.normalized_stacked` | How do component proportions compare after an explicit normalization decision? | `category`, `component`, `value` |
| `bar.grouped_stacked` | How do component totals compare across groups nested within categories? | `category`, `group`, `component`, `value` |
| `bar.diverging_stacked` | How do signed components accumulate above and below zero? | `category`, `component`, `value` |
| `bar.range` | What supplied lower-to-upper span belongs to each category? | `category`, `lower`, `upper` |
| `bar.mirrored` | How do two non-negative supplied sides compare around a shared zero interface? | `category`, `side`, `value` |
| `bar.waterfall` | How do explicit changes reconcile to a supplied final total? | `step`, `delta`, `role` |

`bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable compatibility IDs released in v1.1. They are not core recommendation grammars. New requests use `bar.simple` plus `orientation`; a categorical dot/lollipop request is a neighboring grammar.

## Canonical tabular/DataFrame contracts

The Agent-facing representation is long/tidy tabular data. CSV and JSON are executable runtime paths; “DataFrame schema” describes the same rows and columns without making pandas a runtime dependency.

Logical keys are:

- simple and range: `category`;
- grouped: `category` + `group`;
- stacked, normalized-stacked, diverging-stacked: `category` + `component`;
- grouped-stacked: `category` + `group` + `component`;
- mirrored: `category` + `side`;
- waterfall: `step`.

Duplicate logical rows fail closed. AxiomFig never resolves duplicates with `mean`, `sum`, `groupby`, or another hidden aggregation. Labels are non-null and non-empty; numeric roles are finite and must produce finite renderable geometry. First-seen ordering is preserved unless a typed grammar explicitly owns another ordering rule.

### Missing combinations

`bar.grouped` may be sparse. A missing `(category, group)` row means no value was supplied for that combination, so the corresponding bar is absent. It is never filled with zero. An explicit numeric `0` remains a supplied zero value. Global group order and bar slots follow first-seen group order so another group does not shift into the missing group's semantic slot.

The cumulative/compositional/paired grammars `bar.stacked`, `bar.normalized_stacked`, `bar.grouped_stacked`, `bar.diverging_stacked`, and `bar.mirrored` require complete logical grids. In these grammars an omitted row would be scientifically ambiguous or visually indistinguishable from a zero contribution. Changing that rule requires a design decision rather than an implementation fallback.

`bar.range` requires `lower <= upper`. Range endpoints are the encoded span itself and are not automatically uncertainty around a point estimate.

For `bar.mirrored`, input magnitudes remain non-negative and exactly two `side` labels are required. `mirror_side` explicitly identifies which supplied side is reflected across zero. The runtime sign change is display grammar, not mutation of the scientific values.

For `bar.waterfall`, `role` is `change`, `subtotal`, or `total`. The sequence starts from an explicit subtotal; changes update the running value; any intermediate subtotal and the final total reconcile to the cumulative value under the executable tolerance contract.

### Minimal examples

`bar.simple`

| category | value |
|---|---:|
| Control | 3.1 |
| Treatment | 4.6 |

`bar.grouped` may be sparse; missing rows are absent bars.

| category | group | value |
|---|---|---:|
| R1 | Control | 2.0 |
| R1 | Treatment | 2.7 |
| R2 | Control | 2.4 |

`bar.stacked`

| category | component | value |
|---|---|---:|
| R1 | Soluble | 2.0 |
| R1 | Particulate | 1.0 |
| R2 | Soluble | 2.5 |
| R2 | Particulate | 1.2 |

`bar.normalized_stacked`

| category | component | value |
|---|---|---:|
| R1 | A | 0.7 |
| R1 | B | 0.3 |
| R2 | A | 0.4 |
| R2 | B | 0.6 |

`bar.grouped_stacked`

| category | group | component | value |
|---|---|---|---:|
| R1 | Control | Soluble | 2.0 |
| R1 | Control | Particulate | 1.0 |
| R1 | Treatment | Soluble | 2.6 |
| R1 | Treatment | Particulate | 1.3 |

`bar.diverging_stacked`

| category | component | value |
|---|---|---:|
| R1 | Gain | 2.0 |
| R1 | Loss | -0.8 |
| R2 | Gain | 1.5 |
| R2 | Loss | -1.1 |

`bar.range`

| category | lower | upper |
|---|---:|---:|
| Reactor A | 1.2 | 2.8 |
| Reactor B | 1.6 | 3.1 |

`bar.mirrored`

| category | side | value |
|---|---|---:|
| 18–29 | Female | 4.2 |
| 18–29 | Male | 3.8 |
| 30–44 | Female | 5.1 |
| 30–44 | Male | 4.7 |

`bar.waterfall`

| step | delta | role |
|---|---:|---|
| Start | 10.0 | subtotal |
| Addition | 2.5 | change |
| Removal | -1.0 | change |
| Final | 11.5 | total |

## Selection rules

Choose `simple` for one supplied magnitude per category; `grouped` for supplied group magnitudes within categories; `stacked` for additive components when absolute totals matter; `normalized_stacked` when composition is intentionally compared after explicit normalization; `grouped_stacked` for a real category → group → component hierarchy; `diverging_stacked` for signed components accumulated independently around zero; `range` for supplied interval endpoints whose span is itself the quantity; `mirrored` for two comparable sides; and `waterfall` for an ordered cumulative reconciliation.

Do not relabel uncertainty around an estimate as a `range` simply because both use lower/upper endpoints.

## Modifiers

- `orientation`: `vertical` or `horizontal`; it never changes required data columns.
- uncertainty for `bar.simple` and `bar.grouped`: the canonical external tabular form is `value`, `lower`, `upper` plus explicit `uncertainty_type`, especially for asymmetric intervals. Require `lower <= value <= upper`. `lower` and `upper` are supplied together.
- compatibility uncertainty: existing `error` input remains executable for symmetric/programmatic deviation forms. `error` is mutually exclusive with `lower`/`upper`. Any uncertainty form requires `uncertainty_type` and must produce finite renderable geometry.
- `value_labels`: requests semantic value annotation; physical placement and typography remain deterministic.
- `normalization`: `normalize` is the registered deterministic within-category plotting normalization owned by `bar.normalized_stacked`; `proportion` asserts supplied values are already proportions and must satisfy the executable sum/tolerance contract. Other scientific/statistical/domain normalization remains upstream analysis.
- `mirror_side`: identifies the supplied mirrored side; it is semantic state, not a coordinate.

Axis-label text may carry supplied quantity/unit information. Bar width, group gap, colors, alpha, edge, legend placement, label padding, margins, and physical dimensions remain deterministic runtime decisions.

## Scientific boundaries

Do not turn replicate observations into category means to fit a bar grammar. When raw variation is the message, route to strip, box, violin, box-violin, raincloud, ECDF, histogram, or density as scientifically appropriate. A bar plus an uncertainty interval still does not reveal a distribution.

Do not infer uncertainty type, an undeclared normalization denominator, component conservation, missing values, units, or causality. Missing grouped combinations remain absent; explicit zero is zero. Stacked/compositional/paired grammars retain their declared completeness requirements. Components sharing a stack must be additive in a coherent quantity/unit.

AxiomFig may execute the explicitly registered plotting normalization of `bar.normalized_stacked`. Estimator choice, baseline/reference correction, batch correction, fitted scaling, and other scientific/domain normalization are upstream computations.

## Neighboring / non-Bar charts

- Raw distributions belong to the Distribution family.
- A histogram bins observations; it is not a categorical Bar grammar.
- Dot/lollipop, Pareto, Gantt, Marimekko/mosaic, and bullet charts are neighboring grammars, not aliases for the nine core Bar grammars.
- Pareto requires ordered magnitude plus cumulative-percentage semantics.
- Gantt encodes intervals on a time axis.
- Marimekko/mosaic uses width as an additional quantitative channel.
- Bullet charts compare performance against explicit targets/ranges.

When no registered grammar matches, report unsupported scope rather than approximating it through low-level Matplotlib instructions.

## Runtime mapping

The Agent selects one registered `bar.*` template, maps canonical columns under `data`, and places typed modifiers such as `orientation`, `uncertainty_type`, `normalization`, or `mirror_side` under `semantics`. `src/axiomfig/templates/bar/contract.yaml` is the executable source of required/optional roles; `adapter.py` validates types, logical keys, missing-grid semantics, ordering, interval semantics, and derived geometry; `builders.py` maps normalized rows to deterministic plot geometry.

```yaml
template: bar.simple
data: {category: treatment, value: estimate, lower: ci_low, upper: ci_high}
semantics: {orientation: horizontal, uncertainty_type: 95% CI}
```

The same scientific columns are used for vertical orientation. The Agent must not add orientation-specific data fields or low-level visual parameters.
