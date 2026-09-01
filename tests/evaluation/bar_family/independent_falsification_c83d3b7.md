# Independent falsification audit: Bar family release candidate

- Task: `reports/chatgpt/260901_chatgpt_02.md`
- Pinned task source: `4f2368aff9181291c78ee8159d8fe0e7dff804ce`
- Candidate: `c83d3b75d96946e95adafddb5f0bccf6e6b3f70f`
- Prior FAIL artifacts: `independent_falsification_da5c886.md`, `independent_falsification_32ad843.md`, `independent_falsification_ffab12b.md`, `independent_falsification_c8bf574.md`
- Audit date: 2026-09-01
- Scope: independent read-only falsification; this file is the only authorized audit output
- Verdict: **PASS**

No task-level release blocker remained after replaying every prior failure and independently checking the complete Bar contract, public failure boundary, Gallery, dynamic registry, repeatability, exact-SHA CI, historical refs, and root cleanliness. The prior uncertainty-span leak is closed for simple/grouped, symmetric/asymmetric errors, and both orientations without changing the compact formal Gallery.

## Candidate pinning

```text
git rev-parse HEAD
git rev-parse master
git rev-parse origin/master
git show -s --format='%H%n%P%n%s' HEAD
git diff --exit-code 4f2368aff9181291c78ee8159d8fe0e7dff804ce:reports/chatgpt/260901_chatgpt_02.md HEAD:reports/chatgpt/260901_chatgpt_02.md
```

Results:

- `HEAD`, local `master`, `origin/master`, and remote GitHub `master` were all `c83d3b75d96946e95adafddb5f0bccf6e6b3f70f`.
- The pinned task file is unchanged from the task-source commit.
- Worktree was clean before this artifact was created.
- Repository-root `tmp/` was absent.

## Replay of all prior blockers

### Identifier, schema, aggregation, and public-boundary failures

- Null, blank, and non-finite identifier labels fail bounded through public Figure Intent.
- Duplicate logical rows fail closed for all nine grammars. No mean/median/groupby or hidden statistical aggregation path exists.
- Incomplete grouped, stacked, normalized-stacked, grouped-stacked, diverging-stacked, and mirrored logical grids fail in the adapter as bounded `FigureIntentError`; missing combinations are not treated as zero.
- Invalid lengths, non-finite numeric inputs, invalid orientation, malformed mirrored roles/signs, invalid waterfall roles/sequences, and absent uncertainty type all fail bounded.
- Both `xlabel` and `ylabel` are retained in both orientations for all nine core grammars.

### Normalization, cumulative geometry, and oversized values

The previous `1e308` reproductions were replayed through `parse_figure_intent` and `build_intent_figure`:

```text
simple                 BOUNDED finite derived geometry
grouped                BOUNDED finite derived geometry
stacked                BOUNDED finite derived geometry
normalized_stacked     BOUNDED finite derived geometry
grouped_stacked        BOUNDED finite derived geometry
diverging_stacked      BOUNDED finite derived geometry
range                  BOUNDED finite derived geometry
mirrored               BOUNDED finite derived geometry
waterfall cumulative   BOUNDED finite derived geometry
```

The normalized-stack overflow no longer returns zero-height bars. Ordinary invalid proportion/zero-total cases remain bounded. Proportion validation uses the documented absolute tolerance `1e-8` with `rtol=0`.

Waterfall subtotal/total reconciliation uses documented absolute tolerance `1e-8` with no relative slack. A difference of `5e-9` was accepted, `2e-8` was rejected, and cumulative overflow failed bounded.

### Uncertainty artist containment and overflowing spans

Independent public-path probes covered all combinations required by the final audit:

| Route | Error shape | Orientation | Ordinary endpoints contained | Endpoints `±1e308` |
|---|---|---|---:|---|
| simple | symmetric | vertical | yes | bounded `FigureIntentError` |
| simple | asymmetric | vertical | yes | bounded `FigureIntentError` |
| grouped | symmetric | vertical | yes | bounded `FigureIntentError` |
| grouped | asymmetric | vertical | yes | bounded `FigureIntentError` |
| simple | symmetric | horizontal | yes | bounded `FigureIntentError` |
| simple | asymmetric | horizontal | yes | bounded `FigureIntentError` |
| grouped | symmetric | horizontal | yes | bounded `FigureIntentError` |
| grouped | asymmetric | horizontal | yes | bounded `FigureIntentError` |

Ordinary measured results:

```text
simple symmetric:  endpoints -99..101, limits -100..150
simple asymmetric: endpoints -19..31,  limits -20..40
grouped symmetric: endpoints -38..42,  limits -40..60
grouped asymmetric:endpoints -38..52,  limits -40..60
```

The same containment held horizontally on the x axis. The fix validates combined magnitude and endpoint bounds through `linear_limits`, so individually finite but jointly overflowing uncertainty spans fail at the adapter boundary instead of reaching the tick engine.

### Guide, examples, compatibility, and tests

- `bar.md` uses every prescribed heading exactly, documents all nine scientific grammars, contains one small canonical table for each, and keeps `normalization`/`mirror_side` as semantics rather than data columns.
- All exact required `examples/bar/<grammar>.intent.yaml` and CSV pairs exist. The old shortened core YAML names are absent.
- All nine examples plus grouped uncertainty execute through the real Figure Intent -> external dataset -> adapter -> builder -> render -> validation path.
- The required negative-input and geometry test matrix is present.
- Released `bar.vertical`, `bar.horizontal`, and `bar.dot` remain executable compatibility IDs but are absent from current Agent recommendations and formal Gallery cases.

## Architecture and geometry evidence

- Exactly nine Agent-recommended core Bar templates exist: simple, grouped, stacked, normalized-stacked, grouped-stacked, diverging-stacked, range, mirrored, waterfall.
- For each core grammar, the contract required+optional field set exactly equals its builder signature and a family adapter route exists.
- Orientation remains a semantic modifier over the same canonical data roles.
- Artist tests and independent probes confirm grouped offsets, stacked cumulative bottoms, normalized totals, grouped-stacked hierarchy, separate diverging positive/negative accumulation, range start/span, mirrored declared sign, waterfall cumulative start/end/connectors, both orientations, first-seen order, and uncertainty containment.
- Adapter owns external scientific/data validation; builders consume normalized data and existing deterministic style/layout/ornament contracts. The shared Bar geometry helper has current adapter and builder consumers.

## Focused tests, repeatability, and typing

```text
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_bar_grammars.py tests/test_bar_examples.py tests/test_knowledge.py \
  tests/test_gallery.py tests/test_structured_input_hardening.py \
  -k 'bar or figure_intent_yaml_rejects_duplicate_keys or template_registry_rejects_duplicate_keys or family_contract_rejects_duplicate_keys'
```

Result: `102 passed, 90 deselected in 5.55s`.

```text
python -m tests.evaluation.structural_repeatability --repeats 3 --fresh-processes 2
```

Result: 61/61 public templates; 3 in-process and 2 fresh-process runs; no mismatch.

```text
/Users/wenv/miniforge3/bin/python -m mypy src/axiomfig
```

Result: `Success: no issues found in 76 source files`.

Non-render release evaluation independently reported 61 cases, 61 routing passes, Gallery 68 expected/68 present, and no failures.

## Formal Gallery

```text
/Users/wenv/miniforge3/bin/python -m pytest -q tests/test_gallery.py
```

Result: `7 passed in 37.03s`, including a complete exact-candidate temporary runtime rebuild and validation of all 68 curated pairs.

- Formal Gallery has exactly 68 paired PDF/PNG stems, including 16 Bar cases.
- A separate exact-candidate runtime rebuild of all 16 Bar cases validated every pair and matched all 32 tracked PDF/PNG hashes (`32/32`). The compact `grouped_uncertainty` artifact therefore remains unchanged.
- Formal typography is serif. All files are directly under family directories.
- Retired `gallery/sans`, `gallery/serif`, `gallery/technical`, `gallery/capability_audit`, and `gallery/archive` directories are absent; no nested/development directories exist.
- Gallery and public-template counts derive from registry/curated specifications. Historical `55` evidence is not used as an operational count.

## CI, tags, and repository state

- Exact-candidate CI run `33497067746` succeeded:
  - Python 3.11 job `99821587581`;
  - Python 3.12 job `99821587736`.
- Dynamic inventory: 61 public templates, 58 recommended, 65 builders, 61 adapters, 68 Gallery specs.
- Remote master matched the candidate.
- Historical tags are unchanged locally and remotely:
  - `v1.0.0`: tag object `8a6b862...`, peeled commit `8c70caba...`;
  - `v1.1.0`: tag object `f92d9b5...`, peeled commit `45ec3dd...`.
- Repository-root `tmp/` remained absent.

## Verdict

The independent audit found no remaining task-level blocker. All pinned PASS criteria checked in this audit are satisfied on the exact candidate.

**VERDICT: PASS**
