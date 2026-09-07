---
design_id: family-contracts
title: Scientific family and tabular contracts
status: active
role: design_authority
summary: >
  Defines ownership and invariants for registered figure grammars, family tabular contracts, Bar uncertainty, sparse grouped data, normalization, and compatibility behavior.
operational_projection:
  - references/template-knowledge/
  - src/axiomfig/templates/index.yaml
  - src/axiomfig/templates/bar/contract.yaml
  - src/axiomfig/templates/bar/adapter.py
  - src/axiomfig/templates/bar/builders.py
  - examples/bar/
  - tests/test_bar_grammars.py
---

# Scientific family and tabular contracts

## Family ownership model

Each scientific family has one executable grammar surface. Responsibilities remain separated:

```text
family guide in references/
    Agent-facing scientific selection and canonical tabular guidance

src/axiomfig/templates/index.yaml
    registered public template identity/status/geometry

family contract.yaml
    executable required/optional scientific roles

family adapter.py
    external data validation, fail-closed semantics, deterministic normalization

family builders.py
    deterministic scientific plotting geometry
```

A family guide does not own physical visual numbers. Executable style values remain in runtime resources. Builders do not silently redefine scientific input semantics already owned by the contract/adapter.

## Shared tabular invariants

Canonical external data are explicit tables/CSV/JSON mappings. “DataFrame contract” means the same rows and columns and does not require pandas as a runtime dependency.

- Identifier roles are explicit non-empty labels where the grammar requires them.
- Numeric scientific roles are finite and must produce finite renderable derived geometry.
- Logical duplicate rows fail closed unless a grammar explicitly owns an aggregation operation; Bar owns no hidden statistical aggregation.
- Input ordering is preserved when ordering is semantically relevant and no explicit typed ordering rule exists.
- Missing data and numeric zero are distinct states. A missing logical row is never silently converted to `0`.
- Plotting does not compute mean/median/statistical summaries, infer uncertainty type, or choose scientific aggregation.

## Bar core grammar

The current Agent-recommended Bar grammars are:

```text
bar.simple
bar.grouped
bar.stacked
bar.normalized_stacked
bar.grouped_stacked
bar.diverging_stacked
bar.range
bar.mirrored
bar.waterfall
```

Released `bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable compatibility IDs but are excluded from the current core recommendation taxonomy. Orientation is a semantic modifier where meaningful and does not alter the canonical scientific data schema.

### Bar uncertainty

Point-estimate Bar grammars that support uncertainty (`bar.simple`, `bar.grouped`) use explicit uncertainty meaning and support a canonical endpoint representation for external tabular data:

```text
simple:
category | value | lower | upper

grouped:
category | group | value | lower | upper
```

Invariants:

```text
lower <= value <= upper
```

`uncertainty_type` is mandatory whenever uncertainty is supplied and is never inferred.

The endpoint form is the canonical Agent recommendation for CSV/DataFrame uncertainty, especially asymmetric intervals. Existing `error` input remains executable compatibility for symmetric/programmatic deviation forms. The two representations are mutually exclusive; `lower` and `upper` are supplied together. The adapter may deterministically convert endpoints to backend-required error widths, but that conversion must preserve the supplied interval and reject invalid, negative, non-finite, or overflowing derived geometry.

### Sparse grouped data

`bar.grouped` permits sparse `(category, group)` combinations because an unavailable/not-supplied group measurement can be represented by an absent bar. Its semantics are:

- duplicate `(category, group)` rows fail;
- a missing combination means absent/not supplied;
- explicit `value = 0` means a supplied zero and must remain distinguishable from an absent row;
- first-seen category order and global first-seen group order are deterministic;
- group slots are determined from the global group order, so a missing group does not cause another group to shift into the wrong semantic slot;
- legends use the supplied global group set deterministically;
- vertical/horizontal orientation and supported uncertainty forms preserve the same sparse semantics.

No densification or hidden zero filling is permitted.

### Complete grids for cumulative/compositional/paired grammars

The following Bar grammars retain complete logical-grid requirements because an omitted row would be scientifically ambiguous or visually indistinguishable from zero contribution within their accepted grammar:

```text
bar.stacked
bar.normalized_stacked
bar.grouped_stacked
bar.diverging_stacked
bar.mirrored
```

Changing missing-value semantics for these grammars is a design change and requires User + ChatGPT adjudication before implementation.

### Normalization boundary

`bar.normalized_stacked` may perform registered deterministic within-category plotting normalization when the explicit semantic mode is `normalize`. This operation changes the displayed scale to composition and is part of the accepted grammar.

`normalization = proportion` means supplied values are already proportions and must satisfy the executable sum/tolerance contract; malformed values are not silently renormalized.

Other statistical/scientific/domain normalization—including estimator choice, baseline/reference correction, batch correction, fitted scaling, or an undeclared denominator—remains upstream analysis and is not inferred by plotting.

## Failure classification

When testing exposes behavior not determined by this design or by another current design owner, classify it as `DESIGN_GAP` and stop the affected implementation path. Clear Markdown/runtime mismatch is `PROJECTION_DRIFT`; clear code/runtime violation of the accepted contract is `IMPLEMENTATION_DRIFT`; over-specific tests are `TEST_DEFECT`.

## Design acceptance

The family contract is sufficiently specified when an unfamiliar Agent can select the grammar and construct the canonical table, the adapter can validate the scientific invariants without task-specific branches, and the builder can render deterministic geometry without inventing missing scientific semantics.
