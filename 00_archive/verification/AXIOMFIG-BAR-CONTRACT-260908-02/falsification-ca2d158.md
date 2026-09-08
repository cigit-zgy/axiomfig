# Independent falsification — ca2d158

- Task: `AXIOMFIG-BAR-CONTRACT-260908-02`
- Sole task specification: `d66a5b22406aa5dec1e2f6a3b3bffa0326a94cb2:reports/chatgpt/260908_chatgpt_02.md`
- Candidate: `ca2d158db870721db08a0ab2ecafcef506b8a240`
- Branch: `task/260908-bar-contract-hardening`
- Reviewer: independent subagent `/root/final_falsification`, fresh audit context; not the implementation author or earlier architecture-probe/test-author agent.
- Verdict: **FAIL**. One high-severity task blocker is independently reproduced. This is execution evidence, not ChatGPT acceptance.
- Date: 2026-09-08

## Independence and authority

The reviewer read the exact committed task completely, current `AGENTS.md`, all four current design topics and their index, project `SKILL.md`, Bar family guide, comparison routing, Figure Intent guide, relevant contracts/adapters/builders/geometry/registry/style, package configuration, and affected architecture/example/package tests. No implementation report was read.

Collaboration authority was read with `git show` at `ad88170b23920ddac0bff9a2fd467aa0c59917cf` in the local cache whose origin is `https://github.com/cigit-zgy/agent-collaboration.git`. Relevant owners read were verification, maintained Skill development, shared coding-Skill alignment, project reports, and living design. The read cache's pinned commit exists. Ponytail `full` was read completely and independently aligned by:

```sh
gh api 'repos/DietrichGebert/ponytail/contents/skills/ponytail/SKILL.md?ref=2ed6c52c9d7e5e56942508591085fd45dea277d3' --jq .sha
git hash-object /Users/wenv/.codex/skills/ponytail/SKILL.md
```

Both returned `02c0712c86277d49d18a77da3a2b825657bf02d1`. `modern-python` was not activated. The first API invocation had an unquoted `?ref` and was rejected by zsh glob expansion; quoting the immutable URL resolved that audit-command error.

`git remote -v` confirmed `https://github.com/cigit-zgy/axiomfig.git`. Initial and final-before-evidence `git rev-parse HEAD` both returned the candidate above; `git status --short` was empty. The audit performed no fetch, commit, push, production/test/example/document/Gallery edit, dependency install, or environment creation. Only this new retained evidence file is a durable audit write. Audit caches remain under the task's `audit/` directory until the execution owner disposes of them.

## F1 — High: finite Bar values escape the public numeric error boundary

Classification: `IMPLEMENTATION_DRIFT`.

Finite, ordered endpoint inputs pass the adapter's geometry checks but fail in deterministic axis candidate generation. The public `build_intent_figure` raises raw `ValueError` or `OverflowError`, rather than `FigureIntentError`.

| Value | Lower | Upper | Actual public result |
|---:|---:|---:|---|
| `5e307` | `2.5e307` | `6e307` | `ValueError: cannot convert float NaN to integer` |
| `1e308` | `5e307` | `1.2e308` | `OverflowError: cannot convert float infinity to integer` |

All input endpoints and endpoint-to-width differences in these two cases are finite. The failure occurs during `build_intent_figure` itself; calling `canvas.draw()` is unnecessary.

Reproduction environment (all source-based Python probes used these settings):

```sh
cd /Users/wenv/Documents/skills/axiomfig
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/audit/tmp"
export MPLCONFIGDIR="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/audit/mpl"
export HYPOTHESIS_STORAGE_DIRECTORY="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/audit/hypothesis"
/Users/wenv/miniforge3/bin/python - <<'PY'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from axiomfig.intent import parse_figure_intent, build_intent_figure, FigureIntentError
from axiomfig.templates import adapt_template_data
for variant in ['simple', 'grouped']:
    for value in [5e307, 1e308]:
        for orientation in ['vertical', 'horizontal']:
            for uncertainty in ['endpoints', 'error', 'none']:
                data = {'category': ['A'], 'value': [value]}
                sem = {'orientation': orientation, 'value_labels': False}
                if variant == 'grouped':
                    data['group'] = ['G']
                if uncertainty == 'endpoints':
                    data.update(lower=[value*.5], upper=[value*1.2])
                if uncertainty == 'error':
                    data['error'] = [value*.2]
                if uncertainty != 'none':
                    sem['uncertainty_type'] = 'CI'
                intent = parse_figure_intent({
                    'template': 'bar.'+variant,
                    'data': {r:r for r in data}, 'semantics': sem})
                try:
                    adapt_template_data('bar/'+variant, {**data, **sem})
                    build_intent_figure(intent, data)
                    print(variant, value, orientation, uncertainty, 'BUILD_OK')
                except FigureIntentError as exc:
                    print(variant, value, orientation, uncertainty, 'BOUNDED', str(exc))
                except Exception as exc:
                    print(variant, value, orientation, uncertainty,
                          'LEAK', type(exc).__name__, str(exc))
                finally:
                    plt.close('all')
PY
```

Result: **24/24 combinations leaked**. Both simple/grouped and both orientations fail with endpoint, retained symmetric `error`, and no uncertainty. Every call to `adapt_template_data` succeeded before the builder failed.

Exact traceback owner chain from the endpoint reproductions:

```text
intent.py:231 build_intent_figure
  → templates/__init__.py:137 build_template
  → templates/bar/builders.py:218 build_simple
  → templates/bar/builders.py:44 _categorical_axes
  → style.py:251 apply_nice_linear_axis
  → style.py:183-186 nice_linear_axis
  → style.py:152 _snapped_candidates
  → style.py:133 _major_count
      math.floor(upper / step + 1e-10)
```

`style.py` candidate steps/snapped bounds can overflow even when the adapter's padded extrema are individually finite. The adapter's current `linear_limits`/`error_limits` check does not establish that downstream candidate evaluation is numerically valid. The builder runs outside the public adapter error conversion in `intent.py`.

The accepted design explicitly requires finite/renderable derived geometry and bounded malformed public-input errors. Correct rejection of geometry outside supported rendering arithmetic is already authorized by that design; no scientific semantics need to be invented. Repair belongs at the numerical validation owner. A blanket builder exception catch would conceal programmer defects and would not establish valid geometry. This review does not prescribe new visual defaults or an arbitrary scientific magnitude cutoff.

## Other independently completed probes

All probes below used public `parse_figure_intent` → `build_intent_figure`, except explicitly named inventory/resource inspections. They do not neutralize F1.

### Endpoint and malformed-input probes

For `bar.simple`, `value=v`, `lower=.5*v`, `upper=1.2*v`, `uncertainty_type=CI`, and `value_labels=False`, build plus Agg canvas draw succeeded at `v` in `[1e-320, 1e-250, 1e250, 1e300, 1e306, 1e307]`. The two larger values are F1.

The following were bounded as `FigureIntentError`:

- `value=0, lower=-1e308, upper=1e308` (combined span overflow).
- `value=1e308, lower=-1e308, upper=1e308` (derived width overflow).
- all of value/lower/upper equal to maximum finite float (padded geometry overflow).
- lower-only, upper-only, endpoint plus `error`, missing uncertainty meaning.
- Each numeric role independently replaced with `None`, `{}`, `[None]`, `[{}]`, `[[1.0]]`, `[10**1000]`, `[NaN]`, `['']`, or `[complex(1,2)]`.

Exact zero-width uncertainty and subnormal endpoints around zero built successfully. A cancellation-scale interval (`value=1e16, lower=1, upper=1e16+2`) built successfully; no exact arithmetic guarantee beyond floating-point/renderable geometry was inferred. Boolean inputs follow the existing numeric conversion; this audit did not invent a new Boolean policy.

### Sparse grouped artist probe

Exact independently chosen rows:

```python
data = {
    'category': ['Z', 'A', 'Z', 'C', 'A'],
    'group': ['q', 'p', 'r', 'r', 'q'],
    'value': [-2., 0., 4., 1., 3.],
}
lower = value - [.25, 0, .5, .2, .75]
upper = value + [.5, 0, .75, .3, 1.]
```

Six runs covered vertical/horizontal × none/row-wise asymmetric `error`/endpoints. All passed assertions for exactly five patches, container sizes `[2,1,2]`, global groups/legend `['q','p','r']`, category ticks `['Z','A','C']`, supplied zero retained, absent logical cells having no patch, and positions `category_index + (group_index - 1) * observed_width`. Patch magnitudes equaled supplied values. Uncertainty `LineCollection` endpoints equaled supplied lower/upper in grouped row order `[0,4,1,2,3]` at `atol=rtol=1e-14`, and lay within value-axis limits.

### Complete grids and normalization

Ten missing-grid probes (five grammars × two orientations) rejected with `FigureIntentError` containing `complete logical grid`:

- category `['A','A','B']`, value `[1,2,3]`, component `['c','d','c']` for stacked, normalized-stacked (`normalization=normalize`), and diverging-stacked.
- Same categories/values, group `['g','h','g']`, component `['c','c','c']` for grouped-stacked.
- Same categories/values, side `['L','R','L']`, `mirror_side=L` for mirrored.

Normalization used category `['Z','Z','A','A']`, component `['b','a','b','a']`. `normalize` with `[2,6,3,1]` and `proportion` with `[.25,.75,.75,.25]` both produced component heights `[[.25,.75],[.75,.25]]`. `proportion` with `[2,6,3,1]` rejected instead of renormalizing. `normalization=normalize` rejected on simple, grouped, and stacked.

### Figure Intent aliases/nesting

Nine fields (`font_size`, `fontsize`, `lw`, `linewidth`, `bar_width`, `legend`, `kwargs`, `style`, `markersize`) were independently injected at root, semantics, and data-role level: **27/27 rejected**. A `{'linewidth': 1}` object supplied as each of `orientation`, `value_labels`, `xlabel`, and `uncertainty_type`, with otherwise valid endpoint data and explicit CI meaning, was rejected: **4/4**. Unknown visual fields did not reach Matplotlib through these routes.

### Architecture, knowledge, hygiene

Exact test command with the environment above:

```sh
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_architecture_contracts.py tests/test_knowledge.py \
  tests/test_repository_hygiene.py tests/test_bar_examples.py \
  -k 'not execute and not uses_external' \
  -o cache_dir=tmp/AXIOMFIG-BAR-CONTRACT-260908-02/audit/pytest-cache \
  --basetemp=tmp/AXIOMFIG-BAR-CONTRACT-260908-02/audit/pytest
```

Result: **26 passed, 14 deselected in 0.68s**.

Current active reports contain only the task at `reports/chatgpt/260908_chatgpt_02.md`; no implementation report existed during the review. Current design files are the single indexed set with active authority metadata. The root constitution routes ownership without making archived reports runtime authority. Source/operational searches found no old repository identity in current intended identity references and no stale operational public-template count. Numeric `55`/`61` matches in sample data and historical evidence were not misclassified as inventory constants. Existing broad catches inspected in PDF/font inspection enclose external parsers and convert their errors to explicit domain errors; no task-local blanket builder catch was added.

### Package isolation and Gallery

The reviewer inspected the wheel already produced by the ordinary gate at:

```text
tmp/AXIOMFIG-BAR-CONTRACT-260908-02/run/final-full/test_clean_wheel_installs_reso0/wheelhouse/axiomfig-1.1.0-py3-none-any.whl
```

Using stdlib `ZipFile`, all **113 `axiomfig/` runtime members were compared byte-for-byte with candidate `src/` files: zero mismatches**. Required font, LaTeX, template index, and Bar contract resources exist. No wheel path contains reports, design, archive, tests, examples, or evaluation payload. This is independent package-content inspection, not a new wheel build.

The existing gate's non-editable environment was then invoked from `tmp/.../audit`, outside the source checkout, with `PYTHONPATH`/`PYTHONHOME` removed, `PYTHONNOUSERSITE=1`, and audit-local cache variables. Its Python executable was:

```text
tmp/AXIOMFIG-BAR-CONTRACT-260908-02/run/final-full/test_clean_wheel_installs_reso0/environment/bin/python
```

`axiomfig.__file__` was asserted to lie under `sys.prefix`. A public grouped endpoint figure using category `['B','A']`, group `['q','p']`, value `[0,2]`, lower `[0,1]`, upper `[0,3]` retained exactly two patches with magnitudes `[0,2]`: **PASS**. No environment or dependency was created or changed by this reviewer.

Registry-derived inspection produced **61 public specs / 61 adapters / 65 registered specs / 65 builders**, with exact ID-set equality. Gallery PDF and PNG stem sets both equal the dynamically curated **68** expected stems; all are flat family/case paths and retired subtrees are absent. `GALLERY_TYPOGRAPHY == 'serif'` and its use in rendering were inspected. Every one of the **16 actual committed Bar PDF/PNG pairs passed `validate_pair`**. An initial audit script incorrectly assumed typography was a `GallerySpec` field; it raised `AttributeError`, was corrected after reading the actual owner, and the corrected checks passed. This was an audit-script defect, not a product finding.

## Limitations and disposition

- The independent review stops with the confirmed F1 blocker. It does not certify complete task acceptance, final report lifecycle, post-push equality, or temporary-state cleanup.
- Full pytest, release evaluation, all-template repeatability, Ruff/Mypy/Skill validation, dependency audit, clean checkout, fresh wheel construction, and exact-candidate hosted CI were not rerun by this reviewer. The execution owner's raw final-full log was observed to report 817 passed and two optional benchmark skips; that assertion was not used to override F1.
- This review independently validated existing Bar pairs and exercised public artists plus installed-wheel behavior; it did not regenerate the entire Gallery or rerun the external CSV/JSON rendering matrix.
- Broader non-Bar numeric extremes were not exhaustively audited. No separate non-Bar guarantee is asserted from the shared-axis source alone.
- No `DESIGN_GAP` was established. The known failure has a clear existing finite/renderable geometry and bounded-error requirement.
- This file must remain unchanged as failed-candidate evidence after repair. A repaired candidate requires a separately pinned subsequent review and affected-gate reruns.

The implementation owner was notified immediately after F1 reproduction and again after the 24-case confirmation. No candidate mutation occurred before this evidence was written.
