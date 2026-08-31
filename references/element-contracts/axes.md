# Axes element contracts

## Figure, canvas, and panel regions

**Scientific role.** Publication geometry establishes the physical evidence boundary; Primary and
Auxiliary Axes separate scientific content from support regions.

**Default behavior.** Use the registered template geometry and the deterministic panel solve.
**Default source.** `src/axiomfig/templates/index.yaml` -> template `geometry`;
`src/axiomfig/resources/styles/style.yaml` -> `geometry` and `layout`;
`src/axiomfig/layout.py`.

**When to modify.** Choose another registered publication preset when the intended journal column
footprint changes. A panel, inset, marginal, or support region changes only when a registered
scientific grammar requires it.

**Recommended adjustment surface.** Figure Intent `geometry` with a key from `style.yaml ->
geometry`. **Adjustment status:** `AVAILABLE`. User-data panel, inset, marginal, twin, or secondary
Axes creation has no public surface. **Adjustment status:** `NOT_SUPPORTED`. Canonical layout
fixtures and template-owned Auxiliary Axes remain **Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Exact dimensions, margins, region rectangles, gaps, aspect, reservations,
and renderer corrections.

**Interaction / layout relations.** `containment`, `equal_size`, `shared_edge`, `aspect`,
`minimum_gap`, and `ownership` follow `references/figure-anatomy.md`.

**Validation.** Fail on page overflow, ornament intrusion, unequal registered panel footprints, or
an infeasible Primary Visual Area. **Implementation note.** GridSpec and explicit Axes are runtime
mechanisms, never Agent controls. **Avoid / anti-patterns.** Do not emit figure dimensions,
subplot spacing, or manual Axes rectangles.

## Spine, scale, limits, ticks, and grid

**Scientific role.** Scale and limits define the quantitative reading; spines, ticks, labels, and
grid expose that mapping without adding scientific data.

**Default behavior.** Builders select a scientifically valid scale; the runtime applies the
canonical open, filled, categorical, or log-axis contract and nice linear limits.
**Default source.** `style.yaml` -> `axes`, `ticks`, and `stroke`; `src/axiomfig/style.py` ->
`apply_axis_contract()`, `apply_nice_linear_axis()`, and template builders.

**When to modify.** A log or symmetric-log scale must be scientifically requested; limits may be
fixed only when a template exposes a semantic domain such as parity identity bounds. Tick values
may need scientific thresholds, not decorative tuning.

**Recommended adjustment surface.** `scatter.parity semantics.identity_limits` is
**Adjustment status:** `AVAILABLE`. A `semantic axis-scale request` is **Adjustment status:**
`PLANNED`. The `deterministic categorical tick contract` and `deterministic tick contract`,
including generic limits, locations, direction, physical geometry, spines, and grid, are
**Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Exact locators, limits after snapping, tick count, tick geometry, stroke,
spines, and grid appearance.

**Interaction / layout relations.** `shared_axis`, `alignment`, `aspect`, `containment`,
`allowed_overlap`, and `z_order`.

**Validation.** Fail when a requested scientific scale cannot represent supplied values, parity
limits do not bound both quantities, or labels/ticks clip. **Implementation note.** Matplotlib scale
objects and locators are implementation details. **Avoid / anti-patterns.** Do not translate a
request into `set_xscale`, fixed tick lengths, custom spine widths, or arbitrary limits outside an
exact family contract.

## Axis labels, tick labels, and title

**Scientific role.** Labels identify quantities and units; tick labels map positions to values;
titles provide context only when the scientific grammar owns one.

**Default behavior.** Builders provide canonical labels, and renderer measurement reserves their
space. **Default source.** Family `contract.yaml` and builder; `style.yaml -> typography`;
`src/axiomfig/typography.py` and `layout.py`.

**When to modify.** Supply explicit quantity/unit labels when canonical labels are not correct.
Long labels justify measured reservation, not smaller arbitrary typography.

**Recommended adjustment surface.** `family semantics.xlabel and semantics.ylabel`, where listed
in that family contract, are **Adjustment status:** `AVAILABLE`. Generic title text,
rotation, padding, line wrapping, and physical tick-label treatment are **Adjustment status:**
`INTERNAL_ONLY`; a generic user title is **Adjustment status:** `NOT_SUPPORTED`.

**Runtime ownership.** Font, size, weight, rotation, padding, wrapping policy, bbox measurement,
and final placement.

**Interaction / layout relations.** `anchor`, `alignment`, `containment`, `minimum_gap`, and
`non_overlap`.

**Validation.** Fail on missing scientific identity/units, fallback fonts, clipped labels, or
decorated-Axes overflow. **Implementation note.** Text extents require a drawn renderer.
**Avoid / anti-patterns.** Do not ask for a font size, label coordinates, or manual rotation.

## Shared, twin, secondary, inset, and marginal axes

**Scientific role.** These topologies coordinate multiple scientific coordinate systems or
summaries.

**Default behavior.** They exist only inside a registered builder/layout whose scientific meaning
defines them. **Default source.** `src/axiomfig/layout.py`, the selected builder, and
`references/layout-contract.md`.

**When to modify.** Only a scientifically explicit composition, marginal distribution, or support
axis justifies another region.

**Recommended adjustment surface.** Canonical layout fixtures and current template-owned support
axes are **Adjustment status:** `INTERNAL_ONLY`. General user-data shared/twin/secondary/inset or
marginal composition is **Adjustment status:** `PLANNED` only where the future composition contract
can preserve units and scales; otherwise it is **Adjustment status:** `NOT_SUPPORTED`.

**Runtime ownership.** Region topology, axis sharing, transforms, physical alignment, z-order, and
ornament reservation. **Interaction / layout relations.** `shared_axis`, `shared_edge`,
`equal_size`, `alignment`, `containment`, and `ownership`.

**Validation.** Fail when unlike quantities share a scale, aligned regions drift, or decorations
collide. **Implementation note.** Existing complex-figure evidence proves Matplotlib feasibility,
not a public composition API. **Avoid / anti-patterns.** Do not create a twin axis or inset from a
user-supplied coordinate rectangle.
