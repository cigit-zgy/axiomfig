# Ornament element contracts

## Legend and shared figure legend

**Scientific role.** A legend explains scientifically meaningful series/group identity; it does not
create grouping semantics.

**Default behavior.** Omit single-series legends and renderer-pack multi-series legends in the
measured ornament region. **Default source.** `style.yaml -> legend`;
`src/axiomfig/ornaments.py`; group/series roles in family contracts.

**When to modify.** A shared legend, orientation, or side is meaningful only for a real composition
whose panels share the same grouping semantics.

**Recommended adjustment surface.** Supplying a contract-listed `group` or series-label role is
**Adjustment status:** `AVAILABLE` for legend content. Placement, rows, columns, gaps, and handles
are **Adjustment status:** `INTERNAL_ONLY`. A `semantic shared-legend scope` or `semantic legend
side and orientation` is **Adjustment status:** `PLANNED`; canonical layout fixture flags are not a
general user surface.

**Runtime ownership.** Bbox measurement, location, packing, row/column choice, handles, spacing,
and reservation.
**Interaction / layout relations.** `containment`, `minimum_gap`, `non_overlap`, `alignment`, and
`ownership`.

**Validation.** Fail on data/legend collision, page overflow, duplicate identity, or a shared legend
for unlike group semantics. **Implementation note.** Legend anchors are runtime details.
**Avoid / anti-patterns.** Do not emit `bbox_to_anchor`, column counts, handle lengths, or numeric
coordinates.

## Colorbar and shared colorbar

**Scientific role.** A colorbar explains a continuous quantitative color mapping and its units.

**Default behavior.** A template requiring continuous color receives the global measured vertical
Colorbar contract. **Default source.** `style.yaml -> colorbar.vertical`; `colors.yaml ->
colormaps`; `src/axiomfig/layout.py` and `ornaments.py`.

**When to modify.** Change the semantic label or scientific color meaning when supplied data demand
it. Horizontal/shared topology is valid only when quantity, normalization, scale, center, and color
semantics agree.

**Recommended adjustment surface.** Exact contract-listed `colorbar_label`, `count_label`,
`color_semantics`, and `center` fields are **Adjustment status:** `AVAILABLE`. Physical vertical
placement is **Adjustment status:** `INTERNAL_ONLY`. `semantic colorbar orientation` and `semantic
shared-colorbar scope` are **Adjustment status:** `PLANNED`.

**Runtime ownership.** Colormap resolution, normalization after semantics, physical width/length,
gap, side, tick geometry, label placement, and decorated containment.
**Interaction / layout relations.** `alignment`, `minimum_gap`, `containment`, `aspect`, and
`ownership`.

**Validation.** Fail on missing continuous quantity/units, wrong center, mismatch across a proposed
shared scale, or Primary Visual Area intrusion. **Implementation note.** Auxiliary Axes allocation
is not a public coordinate surface. **Avoid / anti-patterns.** Do not emit `add_axes` rectangles,
aspect hacks, raw colormap names, or physical Colorbar dimensions.

## Panel label and fixed title-like ornament

**Scientific role.** Panel labels establish manuscript reference order; fixed statistical/title-like
text communicates template-owned context.

**Default behavior.** Registered layouts add deterministic panel labels; builders own fixed
scientific text such as metric names when contracts supply it. **Default source.** `style.yaml ->
panel`; `src/axiomfig/ornaments.py`; selected family contract/builder.

**When to modify.** Only panel story/order or supplied scientific text can change meaning. Physical
offsets and typography do not.

**Recommended adjustment surface.** Contract-listed `fit_label`, `metric_name`, `auc`,
`size_label`, `strength_label`, and similar supplied text roles are **Adjustment status:**
`AVAILABLE`. The `deterministic panel-label contract` and template-owned fixed text placement are
**Adjustment status:** `INTERNAL_ONLY`. Arbitrary figure-title ornaments are **Adjustment status:**
`NOT_SUPPORTED`.

**Runtime ownership.** Format, typography, anchor, offset, measured reservation, and z-order.
**Interaction / layout relations.** `anchor`, `alignment`, `containment`, `minimum_gap`, and
`z_order`.

**Validation.** Fail on missing/duplicate panel identity, collision, clipping, or a statistical
label detached from its supplied result. **Implementation note.** Figure-level text coordinates are
runtime-owned. **Avoid / anti-patterns.** Do not supply panel offsets or title coordinates.

## Annotation strips, marginals, risk/summary tables, and dendrogram regions

**Scientific role.** These regions provide aligned supporting evidence outside or alongside the
Primary Axes.

**Default behavior.** They exist only in a template or canonical layout that owns their data and
alignment. **Default source.** Selected builder; `src/axiomfig/layout.py`;
`references/layout-contract.md`.

**When to modify.** A supplied risk table, marginal distribution, annotation strip, summary table,
or clustering geometry must be scientifically part of the requested figure.

**Recommended adjustment surface.** Current production template-specific examples are
**Adjustment status:** `INTERNAL_ONLY` unless an exact family contract lists their input role.
General user-data auxiliary-region composition is **Adjustment status:** `PLANNED`. Automatic
clustering or risk/survival computation is **Adjustment status:** `NOT_SUPPORTED`.

**Runtime ownership.** Region topology, physical reservation, shared ordering/axis alignment,
z-order, and renderer measurement.
**Interaction / layout relations.** `shared_axis`, `shared_edge`, `ordering`, `alignment`,
`equal_size`, `containment`, and `ownership`.

**Validation.** Fail when rows/leaves do not align, support content steals unreserved primary area,
or a computed result is invented. **Implementation note.** Prior capability figures demonstrate
Matplotlib feasibility only. **Avoid / anti-patterns.** Do not hand-place support Axes or imply a
canonical fixture is a general composition API.
