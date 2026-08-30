# Domain-specialized routing

Use this topic for supplied flow structures, scalar or vector fields, omics results, survival
curves, and canonical multi-panel examples. These grammars carry domain-specific assumptions, so
route only after confirming that the supplied data or results have the required scientific
meaning. AxiomFig visualizes these inputs; it does not run enrichment, differential-expression,
survival, or field-estimation analyses.

## Flow

`flow.sankey` consumes source, target, and non-negative quantitative flow values. Ribbon thickness
encodes the supplied magnitude and direction follows the supplied source-target structure. Use it
for transfer, allocation, or flow between explicit categories.

Do not infer mass conservation. Equal incoming and outgoing totals are a property of the upstream
system, not something a Sankey appearance proves. Do not interpret left-to-right direction as
causal direction unless the scientific process establishes causality. A source and target should
represent comparable stages or entities, and values must share a coherent quantity/unit where
their widths are compared.

Ask when the supplied edges might represent association rather than flow, when values use
incompatible units, or when direction is not defined. Do not ask for node positions, ribbon colors,
curvature, or column spacing.

## Scalar and vector fields

- `field.contour` consumes x/y grids and a scalar z field plus explicit color semantics. Use it for
  a scalar quantity defined over coordinates. Contours imply interpolation across the represented
  domain; do not use them for arbitrary categorical observations or sparse unstructured points
  unless the gridded field was produced upstream.
- `field.quiver` consumes x/y coordinates and vector components u/v. An optional supplied magnitude
  may drive color, but AxiomFig does not infer units, coordinate orientation, or a physical norm.
  Use it when direction and magnitude of a vector field are the scientific message.

Color semantics follow the quantity: sequential for one-sided magnitude, diverging for a signed
quantity with an explicit meaningful center, and cyclic for periodic direction such as angle when
that is the supplied interpretation. Do not select diverging or cyclic treatment as an aesthetic
preference. Ask when coordinate units, orientation, component meaning, or color quantity is
ambiguous. Require upstream interpolation when only irregular observations are supplied for a
requested contour field.

## Omics results

### Volcano

`omics.volcano` consumes precomputed effect values, adjusted p-values, a significance threshold,
and an effect threshold. The current builder displays effect values as log2 fold change and applies
the deterministic display transform `-log10(adjusted p-value)` to the supplied adjusted p-values.
Therefore map `effect_size` only from an already computed log2-fold-change quantity; do not compute
fold change from raw counts or silently map an untransformed ratio. Thresholds must be supplied on
the corresponding input scales.

Never infer raw versus adjusted p-value, log base, effect definition, contrast direction,
significance threshold, or effect threshold. If the user provides raw expression/count data,
request upstream differential analysis. If a result column says only `p` or `effect`, clarify its
meaning before mapping. Applying `-log10` for display to an explicitly supplied adjusted p-value is
not differential analysis; calculating that p-value or log2 fold change is.

### Enrichment dot plot

`omics.enrichment_dot` consumes term, enrichment quantity, significance quantity, and a positive
size quantity. These roles remain distinct: position encodes supplied enrichment, color encodes the
supplied significance quantity through the established plot grammar, and area encodes the supplied
size. The current default significance label describes adjusted p-values, so do not map raw
p-values under that label without an explicit contract-compatible meaning.

Do not infer which enrichment method was used, calculate pathway enrichment, convert a p-value to
an adjusted p-value, or guess whether size means gene count, set size, overlap count, or another
quantity. Ask when any role's scientific definition is missing. Do not interpret enriched terms as
causal mechanisms solely from the visualization.

## Survival

`survival.kaplan_meier` consumes visualization-ready time and non-increasing survival probability,
with optional group, censoring, lower/upper confidence bounds, and censor times. It displays a
precomputed step function; AxiomFig does not fit a Kaplan–Meier estimator.

If only individual time/event records are supplied, require upstream survival estimation. Do not
compute censoring indicators, confidence intervals, hazard ratios, median survival, or log-rank
tests. If confidence bounds are provided, their meaning and coverage must be known upstream.
Censoring markers indicate supplied censoring semantics and must not be guessed from repeated time
values. Group curves should represent comparable time units and event definitions.

Ask when event definition, time unit, group meaning, censoring representation, or interval meaning
is ambiguous. Do not ask for step-line width, censor marker style, legend placement, or panel size.

## Canonical multi-panel layouts

The registered `layouts.grid_2x2`, `layouts.grid_2x3`, and `layouts.grid_3x2` IDs are canonical
no-data Gallery fixtures, not a general nested user-data composition API. Do not claim that an
external request with independent panel datasets is currently executable through Figure Intent.
Report that scope honestly and defer composition design.

Future scientific composition must keep group/color identity consistent only when the group
semantics match; share a colorbar only when quantity, normalization, scale, center, and color
meaning match; and share numerical axes only for compatible quantities, units, and scales. Panel
labels and geometry remain deterministic visual decisions.

## Ask when

Across these templates, ask when:

- flow versus association, direction, conservation, or units are unclear;
- a field is scalar versus vector, gridded versus unstructured, or has unknown coordinate units;
- volcano effect or significance columns lack transformation/adjustment meaning;
- enrichment roles or significance adjustment are unspecified;
- survival event, time, censoring, group, or interval semantics are missing;
- a multi-panel request expects general user-data composition that the current public boundary does
  not support.

## Require upstream computation when

Require upstream computation for gridding/interpolation, differential analysis, multiple-testing
adjustment, enrichment analysis, Kaplan–Meier estimation, confidence bands, hazard ratios,
log-rank tests, or any other missing domain result. Losslessly mapping an already computed result
to canonical CSV/JSON is allowed; deriving the result is not.

## Do not infer

Never infer conservation, causality, field units, coordinate orientation, p-value adjustment,
log2-fold-change status, contrast direction, thresholds, enrichment method, size meaning, survival
estimator, event definition, censoring, or unit conversion. Never imply that a figure establishes a
domain mechanism.

## Common misuse

- Treating association weights as flow values or causal arrows.
- Contouring raw scattered observations without an upstream field estimate.
- Computing log2 fold change or adjusted p-values inside a volcano adapter.
- Mapping raw p-values to a colorbar labeled adjusted p-value.
- Fitting survival curves from time/event rows in the plotting layer.
- Claiming canonical layout fixtures prove general nested composition support.
