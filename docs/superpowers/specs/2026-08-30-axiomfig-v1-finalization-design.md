# AxiomFig v1 finalization design

## 1. Scope and invariant

This finalization changes operability and evaluation only. The 55-template taxonomy, canonical
Gallery, physical visual tokens, font stacks, color semantics, layout engine, and validation
thresholds are frozen. A public template remains valid only when both paths are executable:

```plain
canonical example → registered builder → deterministic runtime
external data → Figure Intent → family adapter → same builder → deterministic runtime
```

The complete audited input classification lives in `references/figure-intent-coverage.md`.

## 2. Adapter boundary

`intent.py` retains parsing, dataset loading, role resolution, and orchestration. A focused
`data_adapters/` package owns family-specific input normalization. Each family module exposes one
plain `adapt(variant, values)` function; `_shared.py` contains only repeated shape primitives such
as equal-length one-dimensional arrays, rectangular matrices, labels, coordinates, and finite
scalar validation. `data_adapters/__init__.py` explicitly maps 13 family names to these functions
and records the A/B operability classification.

The adapter returns kwargs using the selected family contract. The canonical builder remains the
single plot-grammar implementation and accepts either no kwargs for its fixed Gallery example or a
complete external-data set. Unknown, missing, malformed, unequal, non-finite, or silently unused
fields fail with `FigureIntentError` or a specific `ValueError`.

## 3. Scientific computation boundary

Direct templates accept observations, category records, matrices, grids, vectors, or flow records.
Precomputed templates accept visualization-ready estimates, intervals, regression fits, density,
diagnostic curves, ordination coordinates/loadings, association edges, adjusted p-values, or
survival curves. AxiomFig performs only deterministic graphical transforms such as sorting an ECDF,
normalizing an explicitly requested normalized stack, category pivoting, and stable Sankey node
placement. It does not fit or infer statistical models.

## 4. Evaluation corpus

`evaluation/cases.yaml` contains one case for every public template and references compact shared
datasets in `evaluation/fixtures.yaml`. Each case records ID, scientific intent route, expected
template, Figure Intent, fixture ID, and expected validation outcome. Fixtures are packaged so an
installed wheel can run the same evaluation without the repository root.

Evaluation reports routing, canonical rendering, external-data rendering, runtime validation,
repeatability, and Gallery coverage separately. All 55 cases parse Figure Intent, load the named
fixture, call `build_intent_figure()`, draw, and run anatomy validation. Release mode additionally
renders and validates PDF/PNG pairs. Seven complex templates use a stable RGBA render signature for
repeatability; PDF metadata bytes are not compared.

## 5. CLI, CI, and release gates

The existing `axiomfig-intent` command remains the only data-rendering CLI. Tests exercise YAML and
JSON intent plus CSV and JSON datasets across all 13 families. Fast CI keeps its current gates and
adds a 7-template external-data smoke subset. Full local release validation runs all 55 external
Figure Intent cases, full pytest once, Ruff, Gallery/font/LaTeX checks, isolated wheel installation,
fresh-clone representative E2E, hygiene scans, final report, push, exact-commit CI, and three-way SHA
verification.

No tag or GitHub Release is created because this task authorizes a release freeze on `master`, not
publication of an immutable release object.
