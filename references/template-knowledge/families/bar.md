# Bar charts

## Scientific role

Use the Bar family for supplied categorical magnitudes, parts of categorical totals, explicit
ranges, paired mirrored magnitudes, or a supplied cumulative change sequence. A bar encodes a
quantity by length from a scientifically meaningful baseline. It is not a default summary of raw
replicates, a distribution display, or an instruction to aggregate rows.

The Agent selects a scientific grammar first and then, when useful, applies the semantic
`orientation` modifier. Vertical and horizontal forms carry the same data meaning and use the same
canonical tabular schema. Orientation is not a separate data grammar.

## Grammar taxonomy

| Grammar | Scientific question | Canonical columns |
|---|---|---|
| `bar.simple` | What supplied magnitude belongs to each category? | `category`, `value` |
| `bar.grouped` | How do supplied group magnitudes compare within categories? | `category`, `group`, `value` |
| `bar.stacked` | How do supplied components contribute to each categorical total? | `category`, `component`, `value` |
| `bar.normalized_stacked` | How do component proportions compare after an explicit normalization decision? | `category`, `component`, `value` |
| `bar.grouped_stacked` | How do component totals compare across groups nested within categories? | `category`, `group`, `component`, `value` |
| `bar.diverging_stacked` | How do signed components accumulate above and below a zero reference? | `category`, `component`, `value` |
| `bar.range` | What supplied lower-to-upper span belongs to each category? | `category`, `lower`, `upper` |
| `bar.mirrored` | How do two non-negative supplied sides compare around a shared zero interface? | `category`, `side`, `value` |
| `bar.waterfall` | How do explicit changes lead from a supplied subtotal to a supplied final total? | `step`, `delta`, `role` |

`bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable compatibility IDs released in
v1.1. They are not core recommendation grammars. New requests use `bar.simple` plus `orientation`;
a categorical dot/lollipop request is a neighboring grammar rather than a reason to extend Bar
internals.

## Canonical tabular/DataFrame contracts

The canonical Agent-facing representation is a long/tidy table. CSV and JSON are the executable
runtime paths; “DataFrame schema” describes the same rows and columns without making pandas a
runtime dependency.

Every logical key must identify exactly one row:

- simple and range: `category`;
- grouped: `category` + `group`;
- stacked, normalized-stacked, and diverging-stacked: `category` + `component`;
- grouped-stacked: `category` + `group` + `component`;
- mirrored: `category` + `side`;
- waterfall: `step`.

Duplicate logical rows fail closed. AxiomFig never resolves duplicates with `mean`, `sum`,
`groupby`, or any other aggregation. If the researcher needs a summary, total, normalization, or
uncertainty estimate, that scientific computation happens upstream and its meaning remains
explicit.

Labels must be non-null and non-empty, numeric columns must be finite, and row order is preserved by first
appearance. Multi-series grammars require a complete logical grid so that a missing combination is
not silently interpreted as zero. `bar.range` requires `lower <= upper`. Range endpoints are
supplied spans; they are not automatically interpreted as confidence intervals or uncertainty.

For `bar.mirrored`, input magnitudes remain non-negative and exactly two `side` labels are required.
`mirror_side` explicitly identifies which supplied side the runtime reflects across zero. The
runtime sign change is display grammar, not a mutation of the scientific values.

For `bar.waterfall`, `role` is one of `change`, `subtotal`, or `total`. The sequence starts from an
explicit subtotal, change rows update the running value, an intermediate subtotal must equal the
current cumulative value, and exactly one final total must equal the final cumulative value. The
runtime does not infer missing totals, insert reconciliation rows, or repair an inconsistent
sequence.

### Minimal tabular examples

`bar.simple` — one supplied magnitude per category.

| category | value |
|---|---:|
| Control | 3.1 |
| Treatment | 4.6 |

`bar.grouped` — every category/group combination is present exactly once.

| category | group | value |
|---|---|---:|
| R1 | Control | 2.0 |
| R1 | Treatment | 2.7 |
| R2 | Control | 2.4 |
| R2 | Treatment | 3.0 |

`bar.stacked` — additive components form categorical totals.

| category | component | value |
|---|---|---:|
| R1 | Soluble | 2.0 |
| R1 | Particulate | 1.0 |
| R2 | Soluble | 2.5 |
| R2 | Particulate | 1.2 |

`bar.normalized_stacked` — the same data schema is used whether values are normalized by the
runtime or asserted to be supplied proportions.

| category | component | value |
|---|---|---:|
| R1 | A | 0.7 |
| R1 | B | 0.3 |
| R2 | A | 0.4 |
| R2 | B | 0.6 |

`bar.grouped_stacked` — category, group, and component form a complete hierarchy.

| category | group | component | value |
|---|---|---|---:|
| R1 | Control | Soluble | 2.0 |
| R1 | Control | Particulate | 1.0 |
| R1 | Treatment | Soluble | 2.6 |
| R1 | Treatment | Particulate | 1.3 |

`bar.diverging_stacked` — supplied signed components accumulate independently around zero.

| category | component | value |
|---|---|---:|
| R1 | Gain | 2.0 |
| R1 | Loss | -0.8 |
| R2 | Gain | 1.5 |
| R2 | Loss | -1.1 |

`bar.range` — lower and upper are the encoded endpoints.

| category | lower | upper |
|---|---:|---:|
| Reactor A | 1.2 | 2.8 |
| Reactor B | 1.6 | 3.1 |

`bar.mirrored` — two non-negative sides use the same canonical schema; `mirror_side` is a semantic
modifier rather than a data column.

| category | side | value |
|---|---|---:|
| 18–29 | Female | 4.2 |
| 18–29 | Male | 3.8 |
| 30–44 | Female | 5.1 |
| 30–44 | Male | 4.7 |

`bar.waterfall` — the ordered rows explicitly distinguish changes, subtotals, and the final total.

| step | delta | role |
|---|---:|---|
| Start | 10.0 | subtotal |
| Addition | 2.5 | change |
| Removal | -1.0 | change |
| Final | 11.5 | total |

Waterfall subtotal and total reconciliation uses an absolute tolerance of `1e-8` with no relative
slack. Values outside that tolerance fail closed rather than changing the supplied cumulative
story.

## Selection rules

Choose `simple` when each category already has one supplied magnitude. Choose `grouped` when group
identity matters within each category and side-by-side comparison is the message. Choose `stacked`
when components share a coherent quantity and their absolute total matters. Choose
`normalized_stacked` only when composition matters and removing total magnitude is intentional.

Choose `grouped_stacked` when both the group comparison and the component composition must remain
visible. Do not use it merely to place many series in one panel; the category → group → component
hierarchy must be scientifically real. Choose `diverging_stacked` when signed contributions around
zero are meaningful. Positive and negative values accumulate independently, so ordinary stacking
is not equivalent.

Choose `range` for an explicitly supplied interval whose two endpoints are themselves the encoded
quantity, such as an operating span. If the endpoints mean SD, SE, confidence, prediction, or
credible uncertainty around an estimate, use a grammar whose scientific uncertainty semantics are
explicit instead of relabeling a range bar.

Choose `mirrored` only for two comparable sides with a meaningful shared zero interface. Choose
`waterfall` only for an ordered reconciliation in which the supplied changes and totals have an
explicit cumulative meaning.

## Modifiers

- `orientation`: `vertical` or `horizontal`; defaults are runtime-owned. It never changes required
  columns. Use horizontal orientation when category-label readability or the communication goal
  warrants it, not as a different scientific template.
- `error` with `uncertainty_type`: available only for supplied simple or grouped estimates. The
  uncertainty type is mandatory and is never inferred.
- `value_labels`: requests semantic value annotation. Font size, placement, padding, and formatting
  remain deterministic.
- `normalization`: `normalize` asks the runtime to convert supplied non-negative components to
  within-category proportions; `proportion` asserts values are already proportions and requires
  them to sum to one within an absolute tolerance of `1e-8` with no relative slack. This is an
  explicit display normalization, not an inferred scientific analysis.
- `mirror_side`: identifies the supplied mirrored side; it is scientific/display semantics, not a
  coordinate.

Axis labels may carry supplied quantity and unit text. Orientation, label text, and these typed
semantics are the entire public adjustment surface. Bar width, group gap, colors, alpha, edge,
legend placement, label padding, margins, and physical dimensions remain deterministic runtime
decisions.

## Scientific boundaries

Do not turn replicate observations into category means to fit a bar grammar. When raw variation is
the message, route to strip, box, violin, box-violin, raincloud, ECDF, histogram, or density as
scientifically appropriate. A bar plus an error bar still does not reveal a distribution.

Do not infer uncertainty type, a normalization denominator, component conservation, missing
combinations, a zero baseline, units, or causality. Stacked parts must be additive in the supplied
quantity and unit. Normalized stacks compare composition, not original total magnitude.
Grouped-stacked components must mean the same thing across groups. Diverging components require a
scientifically meaningful sign. Mirrored sides require comparable quantities and compatible units.

Bar order follows the supplied first-seen order. AxiomFig does not sort by magnitude or derive an
order unless a future typed grammar explicitly owns that scientific rule.

## Neighboring / non-Bar charts

- Raw distributions belong to the Distribution family.
- A histogram bins observations; it is not a categorical bar grammar.
- Dot/lollipop, Pareto, Gantt, Marimekko/mosaic, and bullet charts are neighboring grammars, not
  aliases for the nine core Bar grammars. Do not hallucinate a Bar API for them.
- Pareto requires an ordered magnitude plus cumulative-percentage grammar that is not supplied by
  `bar.simple`.
- Gantt encodes intervals on a time axis rather than categorical magnitudes.
- Marimekko/mosaic uses width as an additional quantitative channel.
- Bullet charts compare performance against explicit targets and qualitative ranges.

When no registered grammar matches, report the unsupported scope or use an explicitly released
compatibility ID only for replaying an existing intent. Do not approximate a missing grammar by
low-level Matplotlib instructions.

## Runtime mapping

The Agent selects one registered `bar.*` template, maps canonical columns under `data`, and places
typed modifiers such as `orientation`, `normalization`, or `mirror_side` under `semantics`.
`src/axiomfig/templates/bar/contract.yaml` is the executable source of required and optional roles;
`adapter.py` validates types, shapes, logical-key uniqueness, ordering, and scientific invariants;
`builders.py` maps the normalized rows to the nine plot grammars. Shared style, layout, ornament,
typography, rendering, and validation modules own all physical appearance.

Example:

```yaml
template: bar.simple
data: {category: treatment, value: response}
semantics: {orientation: horizontal}
```

The same `category` and `value` columns are used for vertical orientation. The Agent must not add
orientation-specific data fields or low-level visual parameters.
