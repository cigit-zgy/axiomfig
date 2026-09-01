# Second independent falsification audit: Bar family completion

- Task: `reports/chatgpt/260901_chatgpt_02.md`
- Pinned task source: `4f2368aff9181291c78ee8159d8fe0e7dff804ce`
- Candidate: `32ad843e560242623086dcf1298d04f2ffd9ea61`
- Candidate parent: `da5c8864064c92bd9ff4235382bc9ff32bc62faa`
- Audit date: 2026-09-01
- Scope: independent read-only falsification; this file is the only authorized audit output
- Verdict: **FAIL**

The remediation closes most of the first audit's seven findings and passes its ordinary focused, Gallery, repeatability, Mypy, and exact-candidate CI checks. It is not task-ready because finite oversized data still cause silent scientific corruption or raw public exceptions, waterfall reconciliation accepts undocumented relative error, and the mandated Bar-guide heading structure remains unmet.

## Candidate pinning

```text
git rev-parse HEAD
git rev-parse master
git rev-parse origin/master
git show -s --format='%H%n%P%n%s' HEAD
git diff --exit-code 4f2368aff9181291c78ee8159d8fe0e7dff804ce:reports/chatgpt/260901_chatgpt_02.md HEAD:reports/chatgpt/260901_chatgpt_02.md
```

Results:

- `HEAD`, local `master`, and `origin/master` were all `32ad843e560242623086dcf1298d04f2ffd9ea61`.
- The candidate's parent is the first audited candidate, and the pinned task file is unchanged from its source commit.
- The worktree was clean before this artifact was created.
- Repository-root `tmp/` was absent.

## Release blockers

### 1. Finite oversized Bar values silently corrupt normalized geometry or leak raw public exceptions

The pinned contract says numeric fields are finite (`260901_chatgpt_02.md:242-255`) and public Figure Intent failures remain bounded `FigureIntentError` (`260901_chatgpt_02.md:319-333`). The adapter validates each supplied scalar as finite but does not validate derived totals, spans, stack accumulations, or plot bounds.

Normalized-stack reproduction through `parse_figure_intent` and `build_intent_figure`:

```python
dataset = {
    "category": ["A", "A"],
    "component": ["C1", "C2"],
    "value": [1e308, 1e308],
}
semantics = {"normalization": "normalize"}
```

Observed: both individually finite values were accepted. `_category_totals` overflowed their sum to `inf` (`src/axiomfig/templates/bar/adapter.py:62-66`); the adapter's positive-total check did not reject it (`adapter.py:140-145`); the builder divided both values by `inf` (`bar/builders.py:318-325`). The resulting two bar heights were `[0.0, 0.0]` instead of proportions summing to one. This is silent scientific corruption.

Simple reproduction:

```python
dataset = {"category": ["A", "B"], "value": [-1e308, 1e308]}
```

Observed public exception:

```text
ValueError: linear-axis bounds must be finite
```

The builder's `_limits` overflows the finite range (`bar/builders.py:31-36`), and `build_intent_figure` catches adapter failures only before calling the builder outside the catch (`src/axiomfig/intent.py:215-231`). Equivalent raw `ValueError` was independently reproduced for grouped, stacked, grouped-stacked, diverging-stacked, range, and mirrored oversized finite data. Stack accumulations and range subtraction emit overflow warnings at `builders.py:352`, `451`, `502`, and `542` before the raw bound failure.

Smallest release-safe fix: reject non-finite derived totals, spans, stack accumulations, and display bounds in `bar/adapter.py` so external failures are bounded, or implement numerically stable normalization where the stated contract intends such finite values to remain valid. Add public-route regressions across the affected grammars, including the zero-height corruption case.

### 2. Waterfall reconciliation accepts undocumented relative mismatch

The guide says intermediate subtotals and the final total “must equal” the cumulative value (`references/template-knowledge/families/bar.md:62-65`). The adapter uses `np.isclose` without explicit tolerances for both comparisons (`bar/adapter.py:184-195`), thereby inheriting NumPy's nonzero default relative tolerance.

Public-path reproductions that were accepted:

```text
delta = [1.0, 0.5, 1.500005]
role  = [subtotal, change, total]

delta = [1.0, 0.5, 1.500005, 1.500005]
role  = [subtotal, change, subtotal, total]
```

In each case the claimed subtotal/total differs from the actual cumulative value `1.5` by `5e-6`. The builder renders the inconsistent supplied total. The task requires deterministic cumulative semantics and rejection of malformed/ambiguous sequences (`260901_chatgpt_02.md:222-240`, `319-330`), but neither guide nor tests define this relative slack.

Smallest fix: define and document an explicit reconciliation rule, use an explicit absolute tolerance with `rtol=0.0` if tolerance is scientifically intended, and add accepted/rejected boundary tests through public Figure Intent.

### 3. The task-mandated Bar-guide heading structure is still not used

The pinned task says “Use this structure” and gives exact headings (`260901_chatgpt_02.md:65-85`), including:

```text
# Bar charts
## Scientific role
## Canonical tabular/DataFrame contracts
## Selection rules
## Modifiers
## Scientific boundaries
## Neighboring / non-Bar charts
```

The candidate instead has `# Bar family knowledge`, `## Scientific question`, `## Canonical DataFrame/tabular contract`, `## Grammar selection rules`, `## Semantic modifiers`, `## Scientific boundaries and upstream boundary`, and `## Neighboring and unsupported Bar requests` (`bar.md:1,3,33,149,171,192,207`). The earlier missing per-grammar tables and incorrect normalized/mirrored schemas are fixed, but the explicit structure portion of that prior documentation blocker is not.

Smallest fix: heading-only alignment; no prose or runtime changes are required.

## Replay of the first audit's seven findings

| Prior finding | Current result | Evidence |
|---|---|---|
| Null identifiers stringify to `"None"` | **Closed for the public CSV/JSON/Python-mapping route** | `None`, blank labels, and non-finite float labels now fail as bounded `FigureIntentError`; `_bar_labels` is used for all Bar identifier roles. |
| Incomplete grids leak builder `ValueError` | **Closed for ordinary grids** | grouped, stacked, normalized, grouped-stacked, diverging, and mirrored incomplete grids fail in the adapter as bounded `FigureIntentError`. |
| Malformed normalized stacks leak; tolerance unclear | **Closed for ordinary magnitudes, but superseded by blocker 1** | zero-total normalize and out-of-tolerance proportion fail bounded; totals `1.000000009` and `1.000000011` respectively pass/fail under documented absolute `1e-8`, `rtol=0`. |
| One axis-label field is ignored | **Closed** | public vertical and horizontal probes preserved both explicit labels; all nine builders share `_set_axis_labels`. |
| Example filenames lack `.intent.yaml` | **Closed** | all nine required CSV plus `.intent.yaml` pairs exist; obsolete core `*.yaml` names are absent. |
| Guide lacks nine tables and misstates two schemas | **Content closed; exact-heading part remains blocker 3** | nine compact tables exist; `normalization` and `mirror_side` are correctly semantic rather than CSV columns. |
| Required negative Bar matrix absent | **Closed for enumerated ordinary cases** | focused tests now cover nonfinite, length, labels, orientation, normalized totals, mirrored rules, waterfall role/sequence, uncertainty, duplicate/incomplete grids, and public bounding. |

## Positive independent evidence

### Focused Bar, guide, structured-input, and Gallery tests

```text
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_bar_grammars.py tests/test_bar_examples.py tests/test_knowledge.py \
  tests/test_gallery.py tests/test_structured_input_hardening.py \
  -k 'bar or figure_intent_yaml_rejects_duplicate_keys or template_registry_rejects_duplicate_keys or family_contract_rejects_duplicate_keys'
```

Result: `83 passed, 90 deselected in 17.46s`.

`python -m pytest -q tests/test_gallery.py` independently completed `7 passed in 35.20s`, including a real temporary rebuild and validation of the complete curated Gallery.

Independent public-route probes additionally confirmed bounded errors for nonfinite values, length mismatch, blank labels, invalid orientation, missing uncertainty type, mirrored cardinality/mirror-side/negative-value errors, and grossly invalid waterfall roles/sequences.

### Contract, registry, examples, and compatibility

- Registry: 61 public templates, 58 Agent-recommended, and compatibility-only `bar/vertical`, `bar/horizontal`, `bar/dot`.
- Exactly nine recommended Bar IDs are present. Each contract's required+optional field set exactly equals its builder signature, and each has an adapter entry.
- Duplicate logical rows fail closed for all nine grammars; complete-grid validation plus unique keys prevents hidden aggregation or zero filling.
- Orientation is optional rather than data-schema-defining for every core grammar.
- All nine exact CSV + `.intent.yaml` example pairs and the grouped-uncertainty external-file example executed through the real CLI and validated.
- v1.1.0 evidence confirms all three compatibility IDs were released. They remain executable but are excluded from current recommendations and formal Gallery cases.

### Geometry

Focused Matplotlib-artist tests passed for simple vertical/horizontal equivalence, grouped offsets, stacked cumulative bottoms, normalized totals, grouped-stacked group/component nesting, diverging independent positive/negative baselines, range start/span, mirrored declared sign, waterfall start/end/connectors, and first-seen category/group/component order. No silent mean/median/groupby path was found.

### Gallery and dynamic counts

- `GALLERY_TYPOGRAPHY == "serif"`.
- Formal inventory is exactly 68 PDF/PNG pairs, including 16 Bar pairs, matching all dynamically derived expected stems.
- Only direct family directories are present. Retired `sans`, `serif`, `technical`, `capability_audit`, and `archive` directories are absent, and no nested directories or development artifacts occur in formal Gallery.
- All 68 PDFs embed XCharter Roman; the one math-bearing PDF additionally embeds XCharter Math.
- A separate temporary rebuild of all 16 Bar cases through `build_template`, `render_figure`, and `validate_pair` produced 16 valid pairs and matched all 32 tracked PDF/PNG hashes (`32/32`).
- No stale operational hard-coded public-template or two-typography Gallery count was found; historical `55` references remain only as historical changelog/evidence content.

### Repeatability, evaluation, typing, CI, refs

```text
python -m tests.evaluation.structural_repeatability --repeats 3 --fresh-processes 2
```

Result: 61/61 public templates, 3 in-process and 2 fresh-process runs, no mismatches.

Non-render release evaluation: 61 cases, 61 routing passes, Gallery 68 expected/68 present, no failures.

```text
/Users/wenv/miniforge3/bin/python -m mypy src/axiomfig
```

Result: `Success: no issues found in 75 source files`.

Exact-candidate GitHub Actions run `33491240467` succeeded for Python 3.11 job `99802980133` and Python 3.12 job `99802980319`.

Local and remote historical tags are unchanged:

- `v1.0.0`: tag object `8a6b862...`, peeled commit `8c70caba...`
- `v1.1.0`: tag object `f92d9b5...`, peeled commit `45ec3dd...`

Remote `master` matched the exact candidate during the audit.

## Verdict

The positive architecture, geometry, examples, Gallery, compatibility, dynamic-count, repeatability, and CI evidence does not override the three unresolved task-level findings. The pinned task states that any unmet PASS criterion precludes PASS (`260901_chatgpt_02.md:553-578`).

**VERDICT: FAIL**
