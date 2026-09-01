# Independent falsification audit: Bar family completion

- Task: `reports/chatgpt/260901_chatgpt_02.md`
- Pinned task source commit: `4f2368aff9181291c78ee8159d8fe0e7dff804ce`
- Candidate audited: `da5c8864064c92bd9ff4235382bc9ff32bc62faa`
- Audit date: 2026-09-01
- Scope: independent read-only inspection and focused probes; this file is the only authorized audit output
- Verdict: **FAIL**

The candidate passes substantial positive runtime, Gallery, registry, compatibility, repeatability, and CI checks, but it does not meet all task-level requirements. In particular, malformed public Bar inputs can still escape as raw `ValueError`, null identifiers are silently stringified, advertised axis-label fields are conditionally discarded, and several explicit documentation/example/test deliverables are incomplete.

## Candidate and task pinning

Checks:

```text
git rev-parse HEAD
git show -s --format='%H%n%P%n%s' HEAD
git diff --exit-code 4f2368aff9181291c78ee8159d8fe0e7dff804ce:reports/chatgpt/260901_chatgpt_02.md HEAD:reports/chatgpt/260901_chatgpt_02.md
git ls-remote --heads origin master
```

Results:

- `HEAD`, local `master`, `origin/master`, and GitHub `master` were all `da5c8864064c92bd9ff4235382bc9ff32bc62faa` during the audit.
- Candidate parent is the pinned task source commit `4f2368aff9181291c78ee8159d8fe0e7dff804ce`.
- The task file is byte-identical to the version at the pinned source commit.
- Worktree was clean before this audit artifact was created.

## Release blockers

### 1. Identifier columns accept null and render it as the literal label `"None"`

The task requires identifier columns to be non-null categorical labels (`260901_chatgpt_02.md:242-255`). Shared `labels_1d` first stringifies every object and only then checks whether the resulting string is empty (`src/axiomfig/templates/_adapter.py:16-22`). Thus `None` becomes the non-empty string `"None"`. Bar applies this helper to category/group/component/side (`src/axiomfig/templates/bar/adapter.py:69-76`), range category (`adapter.py:114-123`), and waterfall step/role (`adapter.py:126-130`).

Public-path probe:

```python
intent = parse_figure_intent(
    {
        "template": "bar.simple",
        "data": {"category": "category", "value": "value"},
    }
)
figure = build_intent_figure(intent, {"category": [None], "value": [1.0]})
```

Observed: the call succeeded and the tick label was `"None"`. Direct adapter probes likewise accepted null category, group, component, range category, mirrored side, waterfall step, and waterfall role.

Smallest fix: reject `None` before string conversion in the shared label validator (and test all Bar identifier roles through the public route).

### 2. Incomplete logical grids escape the public Figure Intent boundary as raw `ValueError`

The guide promises complete multi-series grids (`bar.md:53-55`), and the task requires adapter validation plus bounded `FigureIntentError` (`260901_chatgpt_02.md:319-333`). The adapter validates equal lengths and unique logical keys but not completeness (`bar/adapter.py:69-91`). Completeness is instead checked in builder-only `_pivot` and `_tensor` (`bar/builders.py:96-149`). `build_intent_figure` catches adapter errors only and then calls the builder outside the catch (`src/axiomfig/intent.py:215-231`).

Reproduction using grouped rows `A/G1`, `A/G2`, `B/G1` (missing `B/G2`) returned:

```text
ValueError: bar long-form data must form a complete category by series grid
```

The same raw public exception was reproduced for grouped, stacked, normalized-stacked, diverging-stacked, and mirrored incomplete grids. Grouped-stacked returned raw:

```text
ValueError: grouped-stacked data must form a complete category/group/component grid
```

Smallest fix: move complete-grid validation into `bar/adapter.py` so public input defects are converted by the existing boundary; keep builder assertions only as internal invariant checks.

### 3. Malformed normalized stacks escape as raw `ValueError`, and the tolerance policy is neither clear nor tested

The adapter checks normalization vocabulary and non-negativity only (`bar/adapter.py:95-101`). Positive totals and asserted-proportion sums are checked in `_stacked` after the public adapter boundary (`bar/builders.py:286-297`). Public reproductions returned raw `ValueError` for both:

```text
normalization=proportion, values=[0.8, 0.8]
  ValueError: proportion stacks must sum to one for each category
normalization=normalize, values=[0.0, 0.0]
  ValueError: normalized stacks require positive category totals
```

The task also requires a “clear tested tolerance policy” (`260901_chatgpt_02.md:160-168`). The builder uses `np.allclose(..., atol=1e-8)` without specifying `rtol`, so NumPy's much larger default relative tolerance participates. A public probe accepted category totals `1.000000001`, `1.0000001`, and `1.000005`, but rejected `1.00002`. `bar.md:99-102` says only “within tolerance”, and no Bar regression locks either edge of the policy.

Smallest fix: validate normalize/proportion totals in the adapter, define explicit `atol` and `rtol` centrally, document the semantic policy without duplicating visual defaults, and test accepted/rejected boundary values through Figure Intent.

### 4. Contract-advertised axis-label fields are silently discarded

All nine core contracts advertise both `xlabel` and `ylabel` (`bar/contract.yaml:3-38`), and the guide says supplied quantity/unit axis text is public (`bar.md:106-109`). Builders consume only the value-axis field selected by orientation. For example, simple uses only `ylabel` vertically and only `xlabel` horizontally (`bar/builders.py:180-194`); grouped does the same (`builders.py:257-262`), as do stacked and the remaining Bar builders.

Public-path result when both fields were supplied:

```text
vertical:   xlabel=''              ylabel='Value axis'
horizontal: xlabel='Category axis' ylabel=''
```

No error reports the ignored supplied field. This violates the explicit “no silently ignored supplied fields” requirement (`260901_chatgpt_02.md:319-331`) and makes the contract/docs surface inaccurate.

Smallest fix: either consume both labels on both orientations or narrow/validate the contract so an inapplicable supplied field fails closed. Add public-route regressions for every retained field.

### 5. Required example filenames do not match the pinned deliverable

The task specifies `examples/bar/<grammar>.intent.yaml` for all nine grammars (`260901_chatgpt_02.md:337-361`). The candidate instead tracks `simple.yaml`, `grouped.yaml`, and analogous shortened names. `tests/test_bar_examples.py:20-41` explicitly tests the shortened `f"{grammar}.yaml"` path, so the passing E2E suite does not prove the named deliverable.

The nine examples themselves do execute through the real CSV -> Figure Intent -> adapter -> builder -> render/validate path; the blocker is the exact public example artifact contract.

Smallest fix: rename the nine files to the required `.intent.yaml` names and update the E2E paths.

### 6. `bar.md` omits every required per-grammar small table and misstates two canonical data schemas

The task requires one small table example for every core grammar (`260901_chatgpt_02.md:242-257`). The guide contains one taxonomy table and one Figure Intent YAML snippet, but no small data table for any of the nine grammars (`bar.md:14-26`, `bar.md:151-160`).

The taxonomy also lists `normalization` as a normalized-stacked canonical column and `mirror_side` as a mirrored canonical column (`bar.md:21,25`). The pinned canonical schemas explicitly exclude those semantic modifiers: normalized-stacked has the same `category | component | value` schema as stacked (`260901_chatgpt_02.md:160-168`), and mirrored is `category | side | value` with `mirror_side` semantics (`260901_chatgpt_02.md:210-220`). The shipped CSVs follow the pinned schemas, so the guide contradicts both the task and its own later runtime-mapping statement.

The prescribed section structure (`260901_chatgpt_02.md:73-85`) was also renamed rather than used literally (`bar.md:1,14,33,90,126`); this is secondary to the missing and incorrect data-contract content.

Smallest fix: add nine compact data tables, remove semantic modifiers from the canonical-column cells, and align the requested headings.

### 7. The explicit negative Bar test matrix is largely absent

The task requires focused tests for non-finite input, mismatched lengths, invalid labels, invalid orientation, malformed normalized proportions, invalid mirrored cardinality/mirror side, invalid waterfall role/sequence, and explicit uncertainty-type requirement (`260901_chatgpt_02.md:421-448`). `tests/test_bar_grammars.py` ends at line 313 and contains positive geometry/order tests plus duplicate-key rejection, but no focused tests for those required negative cases. Repository-wide searches found no equivalent Bar-specific negative coverage elsewhere.

Several production cases happen to fail boundedly in independent probes, but null labels, incomplete grids, and normalized-total failures expose the consequences of the missing regressions.

Smallest fix: add the enumerated focused tests, preferring the real public Figure Intent route for externally supplied malformed input.

## Positive falsification results

### Contract, registry, recommendation, and compatibility

- Exactly nine recommended core Bar grammars are routed: simple, grouped, stacked, normalized-stacked, grouped-stacked, diverging-stacked, range, mirrored, waterfall.
- The registry exposes 61 public templates: 58 recommended plus compatibility-only `bar/vertical`, `bar/horizontal`, and `bar/dot`.
- The three legacy IDs existed in v1.1.0, remain executable, are excluded from the canonical recommendation taxonomy, and are absent from the formal Bar Gallery.
- Orientation is a semantic modifier over invariant data roles for the nine core contracts; focused schema-invariance tests passed.
- Duplicate logical rows failed closed for all nine grammars; no aggregation path (`mean`, `sum`, `groupby`, or implicit deduplication) was found.
- Figure Intent, template registry, and family-contract YAML duplicate-key regressions passed (`3 passed`).

### Geometry and real external-data execution

Focused command:

```text
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_bar_grammars.py tests/test_data_adapters.py \
  tests/test_bar_examples.py tests/test_gallery.py \
  -k 'not gallery_builds_only_curated_pdf_png_pairs'
```

Result: `61 passed, 1 deselected in 5.99s`.

This covered positive Matplotlib-artist geometry for simple orientation equivalence, grouped offsets, stacked cumulative baselines, normalized totals, grouped-stacked hierarchy, independent positive/negative diverging baselines, range start/span, mirrored sign application, waterfall starts/ends/connectors, and first-seen order. Independent horizontal probes confirmed the corresponding geometry. All nine CSV+Intent examples and the grouped-uncertainty external-file example rendered and validated through the real CLI.

### Formal Gallery

- Current formal Gallery contains only `README.md` and 13 direct family directories; retired `sans`, `serif`, `technical`, `capability_audit`, and `archive` directories are absent.
- Inventory is 68 paired PDFs and PNGs, including exactly 16 required Bar pairs. No non-PDF/PNG artifact exists under family directories.
- `validate_gallery(..., expected_gallery_stems())` passed with 68/68 stems and 16 Bar stems.
- All 16 tracked Bar PDFs identify XCharter serif text in `pdffonts`.
- An independent temporary rebuild of all 16 Bar `GALLERY_SPECS` through `build_template`, `render_figure`, and `validate_pair` produced 16 valid pairs whose 32 hashes exactly matched the tracked Gallery (`32/32`, no drift).
- No production/evaluation path that recreates the retired Gallery hierarchy was found. Development benchmark/probe artifacts route outside formal Gallery.

### Dynamic counts, repeatability, typing, CI, and Git state

- Registry-derived counts: 61 public, 58 recommended, 65 builders, 61 adapters; Gallery expected stems derive dynamically to 68.
- `python -m tests.evaluation.structural_repeatability --repeats 3 --fresh-processes 2` passed all 61 public templates with no mismatches (3 in-process + 2 fresh-process runs).
- Non-render release evaluation reported 61/61 cases, 61/61 routing, and Gallery 68 expected/68 present with no failures.
- `/Users/wenv/miniforge3/bin/python -m mypy src/axiomfig` returned `Success: no issues found in 75 source files`.
- Exact-candidate GitHub Actions run `33488485865` completed successfully for Python 3.12 job `99794090594` and Python 3.11 job `99794090976`.
- Local and remote tag objects/peeled commits are unchanged: `v1.0.0` = `8a6b862...` / `8c70caba...`; `v1.1.0` = `f92d9b5...` / `45ec3dd...`. No new release tag was present.
- Repository-root `tmp/` was absent at audit time.

## Final criterion assessment

The candidate satisfies the Gallery consolidation, flat serif-only artifacts, old-directory removal, dynamic-count, nine-grammar runtime existence, duplicate-key fail-closed behavior, orientation-schema invariance, uncertainty explicitness in valid examples, geometry, legacy compatibility, tags, master alignment, and exact-candidate CI checks.

It does **not** satisfy the full Bar data contract, bounded public failure behavior, no-silently-ignored-fields rule, required example naming, per-grammar guide examples/canonical schema documentation, required negative regression matrix, or the requirement that the independent audit itself pass. Per `260901_chatgpt_02.md:553-578`, any unmet criterion precludes PASS.

**VERDICT: FAIL**
