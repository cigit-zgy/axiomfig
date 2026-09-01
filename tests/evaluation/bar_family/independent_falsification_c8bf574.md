# Independent falsification audit: final Bar candidate

- Task: `reports/chatgpt/260901_chatgpt_02.md`
- Pinned task source: `4f2368aff9181291c78ee8159d8fe0e7dff804ce`
- Candidate: `c8bf57497531abe5f77f8f0e436fb3077e04a647`
- Prior audit artifacts: `independent_falsification_da5c886.md`, `independent_falsification_32ad843.md`, `independent_falsification_ffab12b.md`
- Audit date: 2026-09-01
- Scope: independent read-only falsification; this file is the only authorized audit output
- Verdict: **FAIL**

All earlier blockers, including ordinary uncertainty containment, close under their original reproductions. The formal Gallery remains compact and unchanged, and the candidate passes focused tests, 61-template repeatability, Mypy, registry, Gallery, exact-SHA CI, tags, and master-alignment checks. One adversarial derived-geometry case still leaks a raw public `OverflowError`: an uncertainty interval whose endpoints are individually finite but whose total span overflows.

## Candidate pinning

```text
git rev-parse HEAD
git rev-parse master
git rev-parse origin/master
git show -s --format='%H%n%P%n%s' HEAD
git diff --exit-code 4f2368aff9181291c78ee8159d8fe0e7dff804ce:reports/chatgpt/260901_chatgpt_02.md HEAD:reports/chatgpt/260901_chatgpt_02.md
```

Results:

- `HEAD`, local `master`, `origin/master`, and remote GitHub `master` were all `c8bf57497531abe5f77f8f0e436fb3077e04a647`.
- The pinned task file is unchanged from its source commit.
- The worktree was clean before this artifact was created.
- Repository-root `tmp/` was absent.

## Release blocker

### Individually finite extreme uncertainty endpoints still leak raw `OverflowError`

The pinned task requires finite numeric data, validated uncertainty bounds, and bounded public `FigureIntentError` failures (`260901_chatgpt_02.md:242-255`, `271-277`, `319-335`). The new shared `error_limits` validates only that each lower/upper endpoint is finite, then calculates padded limits from magnitudes alone before replacing them with endpoint extrema (`src/axiomfig/templates/bar/geometry.py:22-29`). It does not validate that the combined endpoint span is finite and usable by the tick engine.

Public Figure Intent reproduction:

```python
intent = parse_figure_intent(
    {
        "template": "bar.simple",
        "data": {"category": "category", "value": "value", "error": "error"},
        "semantics": {"uncertainty_type": "CI"},
    }
)
build_intent_figure(
    intent,
    {"category": ["A"], "value": [0.0], "error": [1e308]},
)
```

The supplied value and symmetric endpoints `-1e308` and `1e308` are individually finite, so adapter validation succeeds. Their difference overflows. Both vertical and horizontal public routes emit a Matplotlib overflow warning and leak:

```text
OverflowError: cannot convert float infinity to integer
```

Traceback path:

```text
intent.py:231 build_intent_figure
templates/bar/builders.py:218 build_simple
templates/bar/builders.py:44 _categorical_axes
style.py:251 apply_nice_linear_axis
style.py:185 nice_linear_axis
style.py:137 _candidate_steps -> math.log10(inf)
```

This is a malformed/unrenderable public numeric extent and must fail bounded at the adapter boundary. It also regresses the previous implementation's `_require_finite_derived(magnitude, lower, upper)`, which passed all endpoints through `linear_limits` and rejected the non-finite combined span.

Smallest fix: make `error_limits` derive and validate limits from the combined magnitudes and lower/upper endpoints through `linear_limits` (while preserving ordinary containment), or explicitly reject a non-finite endpoint span before returning. Add symmetric and asymmetric public regressions for both simple and grouped routes.

## Replay of prior blockers

All prior findings close except for the narrower extreme-error regression above:

- Null/blank/non-finite identifier roles fail bounded.
- Duplicate logical keys fail closed; no hidden aggregation occurs.
- Incomplete grouped, stacked, normalized, grouped-stacked, diverging, and mirrored grids fail bounded in the adapter.
- Invalid normalized totals fail bounded under documented absolute `1e-8`, `rtol=0`; the prior `[1e308, 1e308]` zero-height corruption no longer returns a figure.
- Every prior oversized simple/grouped/stacked/normalized/grouped-stacked/diverging/range/mirrored/waterfall reproduction fails bounded.
- Non-finite error endpoints such as value `1e308` plus error `1e308` fail bounded.
- Waterfall cumulative overflow fails bounded; reconciliation uses documented absolute `1e-8`, `rtol=0` and passes/fails the expected boundary cases.
- Both explicit axis labels are consumed in both orientations for all nine grammars.
- All exact prescribed Bar-guide headings, nine small tables, and canonical normalized/mirrored schemas are present.
- All nine exact `.intent.yaml` + CSV examples exist and execute; the old core `*.yaml` names are absent.
- The required focused negative-input test matrix is present.

## Ordinary uncertainty containment and Gallery stability

Independent artist probes covered all required combinations:

| Grammar/error shape | Expected endpoints | Vertical contained | Horizontal contained |
|---|---:|---:|---:|
| simple symmetric, value `1`, error `100` | `-99 .. 101` | yes | yes |
| simple asymmetric, value `1`, error `[20,30]` | `-19 .. 31` | yes | yes |
| grouped symmetric, values `[1,2]`, errors `[20,40]` | `-38 .. 42` | yes | yes |
| grouped asymmetric, values `[1,2]`, errors `[[10,20],[40,50]]` | `-38 .. 52` | yes | yes |

The actual value-axis limits were expanded beyond those endpoints in every ordinary case. Thus the `ffab12b` clipping defect is closed for renderable finite spans.

The formal `bar/grouped_uncertainty` output remains compact and byte-identical. A temporary real-runtime rebuild of all 16 Bar cases validated each pair and matched every tracked PDF/PNG hash (`32/32`).

## Positive full-task evidence

### Focused tests

```text
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_bar_grammars.py tests/test_bar_examples.py tests/test_knowledge.py \
  tests/test_gallery.py tests/test_structured_input_hardening.py \
  -k 'bar or figure_intent_yaml_rejects_duplicate_keys or template_registry_rejects_duplicate_keys or family_contract_rejects_duplicate_keys'
```

Result: `98 passed, 90 deselected in 6.42s`.

The positive geometry tests cover grouped offsets, cumulative/normalized stacks, grouped-stacked nesting, independent diverging baselines, range start/span, mirrored declared sign, waterfall cumulative geometry, both orientations, uncertainty containment, and first-seen ordering.

### Registry, contract, examples, and compatibility

- Exactly nine recommended Bar grammars are present: simple, grouped, stacked, normalized-stacked, grouped-stacked, diverging, range, mirrored, waterfall.
- For every core grammar, contract required+optional fields equal its builder signature and an adapter route exists.
- Public inventory is dynamic: 61 public templates, 58 recommended, 65 builders, 61 adapters.
- The nine CSV + `.intent.yaml` examples and grouped-uncertainty external-file example pass the real CLI/render/validation path.
- Released `bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable compatibility IDs, excluded from current recommendations and formal Gallery cases.

### Gallery

- Tracked formal Gallery validation passed for all 68 PDF/PNG pairs; 16 pairs are Bar cases.
- Gallery is serif-only and flat by direct family. Retired `sans`, `serif`, `technical`, `capability_audit`, and `archive` directories and nested development directories are absent.
- All 16 current Bar cases rebuilt through `build_template`, `render_figure`, and `validate_pair`; all 32 hashes matched tracked artifacts, including unchanged `grouped_uncertainty`.
- Non-Bar Gallery generation code and artifacts are unchanged from the immediately prior candidate whose full 68-case temporary runtime rebuild passed; current tracked validation independently passed 68/68.

### Repeatability, evaluation, typing, CI, and refs

- Structural repeatability: 61/61 templates, 3 in-process plus 2 fresh processes, no mismatch.
- Mypy: `Success: no issues found in 76 source files`.
- Non-render release evaluation: 61 cases, 61 routing passes, Gallery 68 expected/68 present, no failures.
- Exact-SHA CI run `33495842217` succeeded: Python 3.11 job `99817720432`, Python 3.12 job `99817720663`.
- Remote master matched the candidate.
- Historical tags are unchanged locally and remotely:
  - `v1.0.0`: tag `8a6b862...`, peeled commit `8c70caba...`;
  - `v1.1.0`: tag `f92d9b5...`, peeled commit `45ec3dd...`.

## Verdict

The ordinary Bar contract and Gallery evidence are strong, but the remaining raw public exception violates the task's bounded-failure requirement. The pinned task states that any unmet PASS criterion prevents PASS (`260901_chatgpt_02.md:553-578`).

**VERDICT: FAIL**
