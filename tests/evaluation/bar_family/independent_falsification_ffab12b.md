# Final independent falsification audit: Bar family completion

- Task: `reports/chatgpt/260901_chatgpt_02.md`
- Pinned task source: `4f2368aff9181291c78ee8159d8fe0e7dff804ce`
- Candidate: `ffab12b9ef7064703a6df2a730b0841d4f14cc2d`
- Candidate parent: `32ad843e560242623086dcf1298d04f2ffd9ea61`
- Prior independent evidence: `independent_falsification_da5c886.md`, `independent_falsification_32ad843.md`
- Audit date: 2026-09-01
- Scope: independent read-only falsification; this file is the only authorized audit output
- Verdict: **FAIL**

All ten findings recorded by the two prior audits now close under their original reproductions. The candidate also passes focused tests, full runtime Gallery rebuild, Bar artifact drift comparison, 61-template repeatability, Mypy, exact-SHA CI, registry, compatibility, and Git/tag checks. One new task-level blocker remains: valid finite uncertainty intervals are drawn but then clipped because their extents are discarded when Bar axis limits are set.

## Candidate pinning

```text
git rev-parse HEAD
git rev-parse master
git rev-parse origin/master
git show -s --format='%H%n%P%n%s' HEAD
git diff --exit-code 4f2368aff9181291c78ee8159d8fe0e7dff804ce:reports/chatgpt/260901_chatgpt_02.md HEAD:reports/chatgpt/260901_chatgpt_02.md
```

Results:

- `HEAD`, local `master`, and `origin/master` were all `ffab12b9ef7064703a6df2a730b0841d4f14cc2d`.
- The pinned task file is unchanged from its task-source commit.
- Worktree was clean before this artifact was written.
- Repository-root `tmp/` was absent.

## Release blocker

### Finite uncertainty extents are validated but discarded from rendered axis bounds

The pinned task makes supplied uncertainty an explicit scientific modifier and requires uncertainty bounds/shape/type validation plus testable scientific geometry (`260901_chatgpt_02.md:271-277`, `319-335`, `421-446`). The adapter correctly computes symmetric or asymmetric error endpoints and verifies that they are finite (`src/axiomfig/templates/bar/adapter.py:40-48`, `118-137`). Those endpoints are not returned or otherwise consumed by the builders.

Both relevant builders set value-axis limits from bar magnitudes alone:

- simple: `linear_limits(values)` at `src/axiomfig/templates/bar/builders.py:213`;
- grouped: `linear_limits(values)` at `builders.py:285`.

Matplotlib creates the error artists before those limits are imposed (`builders.py:195-203`, `261-274`), so valid intervals outside the magnitude-only range are silently clipped.

Public Figure Intent reproduction for simple bars:

```python
intent = parse_figure_intent({
    "template": "bar.simple",
    "data": {"category": "category", "value": "value", "error": "error"},
    "semantics": {"orientation": "vertical", "uncertainty_type": "SE"},
})
figure = build_intent_figure(
    intent,
    {"category": ["A"], "value": [1.0], "error": [100.0]},
)
```

Observed artist and axis geometry:

```text
vertical error segment: y = -99 .. 101
vertical ylim:          -0.25 .. 1.25

horizontal error segment: x = -99 .. 101
horizontal xlim:          -0.25 .. 1.25
```

The public call succeeds without warning or error, but almost the entire uncertainty interval is invisible.

A grouped asymmetric-error probe also reproduced the defect in both orientations:

```text
values = [1, 2]
errors = [[20, 30], [40, 50]]
rendered error extent = -38 .. 52
vertical ylim = -0.5 .. 2.5
horizontal xlim = -0.5 .. 2.5
```

This is not a request for a public visual adjustment. The existing deterministic axis-bound calculation must include the already supplied scientific uncertainty endpoints.

Smallest fix: centralize symmetric/asymmetric error-endpoint derivation, use those endpoints in `linear_limits` for simple and grouped builders, and add artist-containment regressions for both orientations and both error shapes. Preserve the current bounded overflow checks.

## Replay of all ten prior blockers

| Prior blocker | Final-candidate result |
|---|---|
| Null identifier roles were stringified to `"None"` | **Closed.** Null, blank, and non-finite labels fail bounded through Figure Intent. |
| Incomplete logical grids leaked builder `ValueError` | **Closed.** All six multi-series grid forms fail in the adapter as `FigureIntentError`. |
| Malformed normalized stacks leaked raw errors | **Closed.** Zero totals and invalid proportions fail bounded. |
| Normalized tolerance was implicit/default-relative | **Closed.** Documented and tested absolute `1e-8`, `rtol=0`. |
| `xlabel`/`ylabel` fields were conditionally ignored | **Closed.** Both labels are preserved for all nine grammars and both orientations. |
| Required example names omitted `.intent.yaml` | **Closed.** All nine exact pairs exist; obsolete names are absent. |
| Guide lacked nine tables and misclassified semantic modifiers as columns | **Closed.** Nine tables exist; normalized and mirrored schemas match the task. |
| Required negative Bar regression matrix was absent | **Closed.** Focused public and adapter regressions now cover the enumerated cases. |
| Oversized finite values caused normalized zero-height corruption/raw errors | **Closed.** Simple, grouped, stacked, normalized, grouped-stacked, diverging, range, mirrored, and waterfall oversized probes all fail bounded with `FigureIntentError`; no zero-height figure is returned. Non-finite error endpoints also fail bounded. |
| Waterfall used undocumented relative reconciliation tolerance and guide headings differed | **Closed.** Subtotal/total reconciliation uses absolute `1e-8`, `rtol=0`; cumulative overflow fails bounded; every prescribed guide heading is exact. |

The oversized replay used the same `1e308` counterexamples from the previous audit. Accepted waterfall difference `5e-9` and rejected difference `2e-8` confirmed the absolute-only boundary.

## Positive independent evidence

### Focused tests and malformed public inputs

```text
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_bar_grammars.py tests/test_bar_examples.py tests/test_knowledge.py \
  tests/test_gallery.py tests/test_structured_input_hardening.py \
  -k 'bar or figure_intent_yaml_rejects_duplicate_keys or template_registry_rejects_duplicate_keys or family_contract_rejects_duplicate_keys'
```

Result: `94 passed, 90 deselected in 6.15s`.

Independent public-route probes confirmed bounded errors for null/blank labels, nonfinite values, mismatched lengths, invalid orientation, missing uncertainty type, duplicate/incomplete grids, normalized totals, mirrored cardinality/side/sign, waterfall role/sequence/reconciliation, every oversized grammar, waterfall cumulative overflow, and non-finite error endpoints. Duplicate logical rows fail before any display summation; no hidden statistical aggregation was found.

### Bar architecture and examples

- Registry contains exactly nine recommended Bar grammars: simple, grouped, stacked, normalized-stacked, grouped-stacked, diverging-stacked, range, mirrored, waterfall.
- For each grammar, contract required+optional fields exactly equal its builder signature and a family adapter route exists.
- Orientation remains an optional semantic field over invariant canonical data roles.
- All nine exact CSV + `.intent.yaml` example pairs and the grouped-uncertainty external-file example execute through the real CLI and validate.
- Focused artist tests pass for grouped offsets, cumulative and normalized stacks, grouped-stacked hierarchy, diverging positive/negative baselines, range start/span, mirrored declared sign, waterfall cumulative geometry/connectors, both orientations, and first-seen order.
- `bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable v1.1 compatibility IDs but are excluded from current recommendations and formal Gallery cases.

### Gallery

```text
/Users/wenv/miniforge3/bin/python -m pytest -q tests/test_gallery.py
```

Result: `7 passed in 35.51s`, including a real temporary rebuild and validation of the complete formal Gallery.

- Formal Gallery contains 68 PDF/PNG pairs, including 16 Bar pairs; tracked stems exactly equal dynamic expected stems.
- It is serif-only and flat by family. Retired `sans`, `serif`, `technical`, `capability_audit`, and `archive` directories are absent; no nested/development directories exist.
- A separate temporary runtime rebuild of all 16 Bar cases validated all pairs and matched all 32 tracked PDF/PNG hashes (`32/32`).

### Dynamic counts, repeatability, typing, evaluation, CI, and Git

- Dynamic inventory: 61 public templates, 58 recommended, 65 builders, 61 adapters, 68 curated Gallery specs.
- Structural repeatability: 61/61 public templates, 3 in-process plus 2 fresh-process runs, no mismatch.
- Mypy: `Success: no issues found in 76 source files`.
- Non-render release evaluation: 61 cases, 61 routing passes, Gallery 68 expected/68 present, no failures.
- Exact-SHA GitHub Actions run `33493812673` succeeded: Python 3.12 job `99811244977`, Python 3.11 job `99811245318`.
- Remote `master` matched `ffab12b9ef7064703a6df2a730b0841d4f14cc2d`.
- Historical tags are unchanged locally and remotely:
  - `v1.0.0`: tag `8a6b862...`, peeled commit `8c70caba...`;
  - `v1.1.0`: tag `f92d9b5...`, peeled commit `45ec3dd...`.

## Verdict

All historical blockers are closed, but the newly demonstrated uncertainty-geometry loss means supplied scientific data are not faithfully visible. The pinned task states that any unmet PASS criterion prevents PASS (`260901_chatgpt_02.md:553-578`).

**VERDICT: FAIL**
