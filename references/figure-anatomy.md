# Scientific Figure Anatomy

This reference is a developer/runtime vocabulary for diagnosing layout ownership. It is not Figure
Intent, an Agent output, a user-authored schema, a runtime object, or a public API.

## Hierarchy

A scientific figure contains five levels.

1. **Figure / canvas** — physical width and height, outer padding, background.
2. **Region topology** — panel footprint, Primary Axes, Auxiliary Axes, marginal Axes, inset Axes,
   table region, annotation strip, and shared, twin, or secondary Axes.
3. **Axis system** — spines, scales, limits, major and minor ticks and labels, axis labels, title,
   and grid.
4. **Scientific artists** — lines, markers, bars and patches, error bars, intervals and confidence
   bands, matrices and images, contours, densities, reference lines and bands, and statistical
   glyphs.
5. **Ornaments and annotations** — legends, colorbars, panel labels, data labels, free annotations,
   connectors and leaders, statistical text, significance brackets, dendrograms, marginal
   distributions, risk tables, and summary or statistics tables.

An element is described by the following properties:

| Property | Meaning |
|---|---|
| Owner | The layer responsible for its semantics and placement. |
| Coordinate system | Figure, physical point, Axes, data, blended transform, or renderer display coordinates. |
| Position basis | Data anchor, structural region, measured bounding box, or another named element. |
| Renderer measurement | Whether final placement or validation requires a drawn renderer and measured bounding box. |
| Can move? | Whether placement may change without changing scientific meaning. |
| Movement limits | The allowed direction, distance, region, and preserved anchor when movement is permitted. |
| Containment rule | The footprint or page region that must contain the element and its decoration. |
| Overlap rule | Elements it may overlap, must avoid, or may cover only under an explicit contract. |
| Z-order ownership | The layer that fixes stacking relative to scientific artists and ornaments. |

## Position ownership

### A — Data-bound

Lines, markers, bars, matrix cells, contours, reference lines, and similar scientific marks receive
their positions from data coordinates. Layout must not move them to improve appearance. Their
builder owns data transforms and z-order; Axes limits or clipping own containment. Overlap is data,
not a layout defect, unless the scientific grammar specifies aggregation or another encoding.

### B — Structurally constrained

Panels, Primary and Auxiliary Axes, marginal Axes, risk-table regions, legend regions, and colorbar
regions are placed by deterministic layout contracts in figure or physical coordinates. They may
move only while preserving declared alignment, adjacency, shared-axis, equal-size, aspect, and
minimum-gap relations. Final renderer measurement validates decorated containment and non-overlap.

### C — Renderer-measured fixed ornaments

Tick labels, axis labels, titles, panel labels, and fixed statistical text are anchored by their
owning Axes or panel. The renderer measures their actual text bounds so layout can reserve space.
They are not arbitrarily displaced; typography and semantic alignment remain fixed. They must stay
inside the declared figure or panel footprint and avoid unrelated ornaments.

### D — Movable annotations

Selected volcano labels, influential-observation labels, Manhattan labels, and biplot loading labels
retain a data-bound scientific anchor while their text may move within an explicit displacement
region. The annotation owner fixes permitted directions, maximum displacement, connectors,
containment, non-overlap targets, and z-order. Movement must not alter the anchor or imply a
different datum.

## Element ownership table

| Element | Owner | Coordinates / position basis | Renderer | Movement | Containment and overlap | Z-order |
|---|---|---|---|---|---|---|
| Canvas | rendering/layout | physical figure points | validates page | fixed after geometry selection | contains every decorated region | background |
| Panel footprint | layout | figure/physical; canvas allocation | measured | class B constraints only | inside canvas; disjoint unless declared | layout |
| Primary Axes | layout | panel-relative physical bounds | measured | class B | decorated bbox inside panel | layout |
| Auxiliary/marginal/inset/table Axes | layout/ornament | relation to Primary Axes or panel | measured | class B | declared region; no unplanned overlap | layout |
| Spine, scale, limits, ticks, grid | builder plus style | Axes/data transforms | tick text measured | fixed | Axes contract; grids may overlap data by design | style/builder |
| Axis label and title | typography/ornament | Axes anchor plus physical padding | required | class C | decorated Axes/panel | ornament |
| Scientific artist | builder | data coordinates | only for validation | class A | Axes clip or scientific exception | builder |
| Legend | ornament/layout | measured handles/text in reserved region | required | class B/C | panel ornament zone; no data collision unless explicit | ornament |
| Colorbar | ornament/layout | Auxiliary Axes related to Primary Visual Area | required | class B | panel ornament zone; no primary-area intrusion | ornament |
| Panel label | ornament | panel anchor plus physical padding | required | class C | panel footprint | ornament |
| Fixed data/statistical label | builder/ornament | data or Axes anchor | required | class C | declared Axes/panel | ornament |
| Movable label and connector | annotation layer | data anchor plus bounded display-space displacement | required | class D only | declared region; non-overlap targets explicit | annotation |
| Dendrogram | builder/layout | dedicated Axes aligned to matrix ordering | measured | class A/B split | its region; leaves align with matrix | builder |
| Risk/summary table | builder/layout | dedicated table region aligned to scientific axis | measured | class B/C | reserved footprint; rows/columns align | builder/layout |

## Relation vocabulary

- **containment** — one decorated element must remain within a named region.
- **alignment** — named edges, centers, baselines, or data positions coincide within tolerance.
- **anchor** — the scientific or structural point from which placement is derived.
- **minimum_gap** — minimum physical edge-to-edge separation.
- **equal_size** — named regions have equal rendered physical dimensions.
- **shared_edge** — adjacent regions use the same physical boundary.
- **shared_axis** — Axes share scale, limits, and coordinate mapping for a named dimension.
- **aspect** — rendered physical width-to-height or data-unit ratio.
- **ordering** — a stable scientific ordering shared by all dependent elements.
- **non_overlap** — measured decorated bounding boxes must not intersect.
- **allowed_overlap** — a named, intentional intersection such as grid beneath data.
- **allowed_displacement** — the bounded movement available to a class-D annotation.
- **z_order** — deterministic stacking relationship.
- **ownership** — the single layer responsible for defining and validating a relation.

Relations are expressed in code or validation only when an executable consumer exists. This
vocabulary does not authorize a generic constraint DSL or a second public figure schema.
