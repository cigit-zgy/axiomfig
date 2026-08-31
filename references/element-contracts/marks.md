# Scientific mark element contracts

## Lines, steps, reference lines, and reference bands

**Scientific role.** Data lines encode ordered trajectories; steps encode piecewise-constant
processes; reference marks encode supplied or template-invariant scientific baselines.

**Default behavior.** Use the template grammar and canonical stroke hierarchy.
**Default source.** `style.yaml` -> `series`, `stroke`, and `plots.line`; selected family contract
and builder.

**When to modify.** Change step alignment or a baseline only when the scientific process defines
it. A supplied null, target, agreement bound, or prediction band may replace the template default.

**Recommended adjustment surface.** `line.step semantics.where`, `line.area semantics.baseline`,
`estimation.forest semantics.reference`, and diagnostics template-specific `center`, `limits`,
`baseline`, or `target` are **Adjustment status:** `AVAILABLE` only in the contracts that list
them. Generic line style, width, dash, or arbitrary reference geometry is **Adjustment status:**
`INTERNAL_ONLY`.

**Runtime ownership.** Exact stroke, dash pattern, z-order, and clipping.
**Interaction / layout relations.** `anchor`, `ordering`, `allowed_overlap`, `containment`, and
`z_order`.

**Validation.** Fail when a reference changes scientific meaning, step order is invalid, or the
mark leaves its Axes. **Implementation note.** Matplotlib line methods are builder details.
**Avoid / anti-patterns.** Do not emit linewidths, dash tuples, or raw reference coordinates unless
an exact public scientific field owns them.

## Markers, scatter points, highlights, and size encoding

**Scientific role.** Position encodes observations; group or supplied quantity may encode identity,
color, or marker area. Highlighting must preserve which datum is emphasized.

**Default behavior.** Use canonical marker geometry and edge treatment. **Default source.**
`style.yaml` -> `plots.scatter`, `plots.line_marker`, `plots.errorbar`, and `series.markers`;
`src/axiomfig/style.py`.

**When to modify.** Supplied quantitative size, explicit scientific grouping, dense bivariate
counts, or mandatory selected observations justify a semantic exception.

**Recommended adjustment surface.** `scatter.bubble data.size and semantics.size_label`,
group-capable template data role `group`, and `scatter.hexbin template with semantics.gridsize and
semantics.count_label` are **Adjustment status:** `AVAILABLE`. A `semantic selected-point policy`
is **Adjustment status:** `PLANNED`. The `deterministic marker-size contract`, including physical
marker area, glyph, alpha, and edge, is **Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Area mapping, physical size range, glyph sequence, edge, alpha, color,
overplotting policy, and legend handles.
**Interaction / layout relations.** `anchor`, `ordering`, `allowed_overlap`, `z_order`, and
`ownership`.

**Validation.** Fail when diameter rather than area is interpreted as magnitude, mappings are
length-incompatible, or highlights lose their data anchors. **Implementation note.** Scatter
collection kwargs are not Figure Intent. **Avoid / anti-patterns.** Do not emit marker `s` values,
alpha values, glyph codes, or ad hoc highlight colors.

## Bars, patches, areas, and filled geometry

**Scientific role.** Filled marks encode categorical magnitude, composition, range, or area from a
scientifically meaningful baseline.

**Default behavior.** Width, fill, edge, and labels follow the template and shared filled-artist
contract. **Default source.** `style.yaml` -> `plots.bar`, `plots.boxplot`, `plots.violin`,
`plots.histogram`, and `plots.confidence_interval`; selected builder.

**When to modify.** Toggle bar value labels, choose scientifically meaningful histogram bins, or
provide an explicit area baseline. Category width and fill appearance are not semantic controls.

**Recommended adjustment surface.** Bar optional `value_labels`, histogram optional `bins`, and
the area `baseline` are **Adjustment status:** `AVAILABLE`. Strip/raincloud optional `jitter` and
raincloud `summary` are **Adjustment status:** `AVAILABLE` in their exact family contracts.
Physical width, face alpha, edge stroke, hatch, and arbitrary patch geometry are
**Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Physical width, category packing, fill/edge hierarchy, jitter realization,
and value-label placement. **Interaction / layout relations.** `ordering`, `alignment`,
`minimum_gap`, `allowed_overlap`, and `z_order`.

**Validation.** Fail on misleading nonzero baselines, category overlap, invisible edges, or labels
outside the footprint. **Implementation note.** Histogram bins remain a scientific summarization
choice; runtime styling remains fixed. **Avoid / anti-patterns.** Do not emit bar width, patch
alpha, edge width, or jitter coordinates.

## Error bars, point intervals, and uncertainty bands

**Scientific role.** These marks display supplied uncertainty whose meaning must remain explicit.

**Default behavior.** Draw the supplied estimate and interval using the canonical uncertainty
grammar. **Default source.** Line/estimation family contracts and builders; `style.yaml` ->
`plots.errorbar` and `plots.confidence_interval`.

**When to modify.** Use the template whose topology matches pointwise error, interval estimates, or
a continuous band; never substitute SD, SE, CI, PI, or credible interval.

**Recommended adjustment surface.** Required supplied uncertainty values plus
`uncertainty_type` in `line.errorbar` and estimation contracts, and `line.confidence_band supplied
bounds and semantics.uncertainty_type`, are **Adjustment status:** `AVAILABLE`. Computing
uncertainty or tuning cap/edge/band opacity is **Adjustment status:** `NOT_SUPPORTED` as a public
plotting adjustment.

**Runtime ownership.** Cap geometry, stroke, band fill/edge, ordering, and clipping.
**Interaction / layout relations.** `anchor`, `containment`, `allowed_overlap`, and `z_order`.

**Validation.** Fail on missing/unknown uncertainty meaning, inverted bounds, shape mismatch, or
clipping. **Implementation note.** The runtime visualizes; it does not estimate intervals.
**Avoid / anti-patterns.** Do not infer interval type or invent cap size and band alpha.

## Matrix cells, contours, vectors, and statistical glyphs

**Scientific role.** Matrix/image color, contour levels, vector components, and domain glyphs encode
supplied scientific quantities.

**Default behavior.** Select a semantic colormap and template-owned glyph grammar. **Default
source.** Heatmap/field/association contracts and builders; `colors.yaml -> colormaps`;
`style.yaml -> plots.heatmap` and `plots.mantel`.

**When to modify.** Declare sequential versus diverging meaning, an explicit neutral center,
scientifically fixed contour levels, supplied vector magnitude, or advanced Mantel semantics.

**Recommended adjustment surface.** Heatmap/field `color_semantics`, their contract-listed
`center`, field `levels`/`magnitude`, and exact optional Mantel fields in
`association/contract.yaml` are **Adjustment status:** `AVAILABLE`. Generic cell interpolation,
colormap RGB values, contour stroke, quiver scale, and statistical-glyph geometry are
**Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Palette resolution, normalization, cell aspect, contour/vector appearance,
physical glyph geometry, and ornaments. **Interaction / layout relations.** `aspect`, `ordering`,
`alignment`, `allowed_overlap`, and `z_order`.

**Validation.** Fail when diverging semantics lack a center, vectors/matrices are shape-invalid, or
glyphs distort scientific encoding. **Implementation note.** Advanced Mantel options route to
`references/mantel.md`; its physical geometry remains deterministic. **Avoid / anti-patterns.** Do
not emit colormap names, RGB values, cell sizes, contour linewidths, or quiver scaling parameters.
