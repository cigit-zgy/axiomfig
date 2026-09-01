# Annotation element contracts

## Fixed data labels and fixed statistical text

**Scientific role.** A fixed label identifies a supplied datum, feature, category, threshold, or
statistic without changing its anchor.

**Default behavior.** Add labels only when the selected family contract supplies or requires their
scientific content. **Default source.** Ordination, omics, heatmap, flow, diagnostics, association,
and bar family contracts/builders; typography/layout runtime.

**When to modify.** Labels are warranted when identity or supplied result text is necessary for
interpretation, not merely to decorate every point.

**Recommended adjustment surface.** Contract-listed `sample_labels`, `feature_labels`,
`feature_label`, `annotations`, `flow_labels`, `value_labels`, and fixed statistic/threshold fields
are **Adjustment status:** `AVAILABLE`. Generic label coordinates, font properties, and offsets are
**Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Anchor transform, typography, formatting, z-order, bbox reservation, and
containment.
**Interaction / layout relations.** `anchor`, `alignment`, `containment`, `minimum_gap`,
`non_overlap`, and `z_order`.

**Validation.** Fail when labels mismatch data length, attach to the wrong datum, clip, or obscure
required scientific content. **Implementation note.** Renderer text bboxes are used for validation.
**Avoid / anti-patterns.** Do not emit text coordinates, font sizes, or per-label pixel offsets.

## Movable and selected-point annotations

**Scientific role.** The immutable scientific anchor identifies the selected datum; only the text
box may move to remain readable.

**Default behavior.** Keep fixed labels when they do not collide. Collision-aware displacement is
not a current general production service. **Default source.** Selected builder plus
`references/figure-anatomy.md` class D; prior evidence in
`tests/evaluation/figure_capability/artifacts/`.

**When to modify.** Mandatory selected labels, dense volcano/Manhattan/biplot labels, or influential
observations may require bounded displacement.

**Recommended adjustment surface.** Existing template label data roles are **Adjustment status:**
`AVAILABLE` for identity/content, not placement. A `semantic mandatory-selected-label policy`,
`semantic collision-aware selected-label policy`, or `semantic bounded-direction annotation
policy` is **Adjustment status:** `PLANNED`. Case-local runtime placements are **Adjustment
status:** `INTERNAL_ONLY`.

**Runtime ownership.** Backend choice, permitted displacement region, text bbox, candidate/solver
policy, exact position, connector activation, and z-order. The scientific anchor never moves.
**Interaction / layout relations.** `anchor`, `allowed_displacement`, `containment`,
`non_overlap`, `minimum_gap`, and `z_order`.

**Validation.** Fail when the anchor changes, label identity becomes ambiguous, text leaves its
region, or required labels remain unreadable. **Implementation note.** External allocation
libraries were benchmark probes only and are not public switches. **Avoid / anti-patterns.** Do not
expose backend names, force values, candidate counts, or arbitrary label coordinates.

## Leaders, connectors, and crossing control

**Scientific role.** A connector preserves the relationship between displaced text and its fixed
scientific anchor.

**Default behavior.** Omit connectors when direct association is unambiguous; a template-specific
builder may draw a deterministic connector. **Default source.** Template builder and class-D
ownership in `references/figure-anatomy.md`.

**When to modify.** Use a leader only when text displacement would otherwise make identity
ambiguous.

**Recommended adjustment surface.** A `semantic connector requirement` tied to mandatory selected
labels is **Adjustment status:** `PLANNED`. Existing benchmark-local or template-local connector
geometry is **Adjustment status:** `INTERNAL_ONLY`. User-provided control points or routing solver
parameters are **Adjustment status:** `NOT_SUPPORTED`.

**Runtime ownership.** Activation threshold, path primitive, endpoint attachment, crossing policy,
stroke, clipping, and z-order.
**Interaction / layout relations.** `anchor`, `containment`, `non_overlap`, `allowed_overlap`,
`allowed_displacement`, and `z_order`.

**Validation.** Fail when a connector starts/ends in empty space, crosses required labels/data
without permission, or points to the wrong anchor. **Implementation note.** Connector crossing was
the retained fragile class in the complex-figure audit. **Avoid / anti-patterns.** Do not emit
control points, curvature numbers, or backend tuning.

## Threshold labels, significance text, and brackets

**Scientific role.** These annotations explain a supplied scientific threshold, significance
decision, or comparison.

**Default behavior.** Render only results and thresholds explicitly supplied by a supported family
contract. **Default source.** Omics/association/heatmap contracts and builders; selected scientific
knowledge topic.

**When to modify.** A threshold label or significance annotation changes only when the upstream
scientific result and its meaning are explicit.

**Recommended adjustment surface.** Volcano `significance_threshold`/`effect_threshold`, Mantel
significance fields, and heatmap supplied `annotations` are **Adjustment status:** `AVAILABLE`.
Generic arbitrary significance brackets/text are **Adjustment status:** `NOT_SUPPORTED`; their
visual placement remains **Adjustment status:** `INTERNAL_ONLY` where a builder owns it.

**Runtime ownership.** Formatting, line/text style, physical gap, collision handling, and z-order.
**Interaction / layout relations.** `anchor`, `alignment`, `minimum_gap`, `containment`, and
`non_overlap`.

**Validation.** Fail when p-value meaning or threshold is inferred, a bracket targets the wrong
groups, or text clips/collides. **Implementation note.** AxiomFig displays supplied inferential
results; it does not calculate them. **Avoid / anti-patterns.** Do not invent thresholds, corrected
p-values, stars, bracket heights, or label offsets.

## Annotation priority and collision policy

**Scientific role.** Priority determines which scientifically required labels must remain visible
when all text cannot coexist.

**Default behavior.** Current registered builders use local deterministic selection; there is no
general priority surface. **Default source.** Selected builder and runtime validation.

**When to modify.** Only an explicit scientific selection or declared priority may decide which
labels are mandatory.

**Recommended adjustment surface.** `semantic annotation priority`, bounded direction, text-text
avoidance, and text-data avoidance are **Adjustment status:** `PLANNED`. Current placements and
collision checks are **Adjustment status:** `INTERNAL_ONLY`.

**Runtime ownership.** Priority resolution, obstacles, displacement bounds, exact packing,
connector policy, and deterministic failure behavior.
**Interaction / layout relations.** `ordering`, `non_overlap`, `allowed_overlap`,
`allowed_displacement`, `containment`, and `ownership`.

**Validation.** Fail when a lower-priority label hides mandatory evidence, collisions remain
ambiguous, or repeated runs differ. **Implementation note.** The next evidence round should compare
one deterministic allocator across multiple real templates. **Avoid / anti-patterns.** Do not ask
the Agent to choose force strengths, iteration counts, or low-level obstacle coordinates.
