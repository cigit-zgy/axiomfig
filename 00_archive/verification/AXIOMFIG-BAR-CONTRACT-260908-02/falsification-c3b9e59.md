# Independent falsification — c3b9e59

- Task: `AXIOMFIG-BAR-CONTRACT-260908-02`
- Sole task specification: `d66a5b22406aa5dec1e2f6a3b3bffa0326a94cb2:reports/chatgpt/260908_chatgpt_02.md`
- Candidate: `c3b9e597b7b3533082cec24c066e4374d0ab28e8`
- Branch: `task/260908-bar-contract-hardening`
- Repository: `https://github.com/cigit-zgy/axiomfig.git`
- Reviewer: independent subagent `/root/candidate_reaudit`; auxiliary read-only surface inspection by `/root/candidate_reaudit/surface_inspection`.
- Date: 2026-09-08
- Review verdict: **PASS_WITH_LIMITATIONS for this bounded independent falsification review: no task-level blocker found.** The prior F1 is repaired. One pre-existing, out-of-scope documentation mismatch remains disclosed below. This verdict is execution evidence, not whole-task completion or ChatGPT acceptance.

## Independence, authority, and candidate integrity

The reviewer read the exact committed task completely, root `AGENTS.md`, `design/README.md` and all four current design topics, project `SKILL.md`, Bar family guide, comparison routing, Figure Intent guide, and relevant runtime contracts/adapter/builders/geometry/style, registry/Gallery/package owners and tests. The previous sealed failed-candidate evidence was read. No main implementation report was read; none existed on the candidate during review.

Pinned collaboration content was read directly with `git show` from the read cache `/Users/wenv/Documents/skills/agent-collaboration`, whose origin was verified as `https://github.com/cigit-zgy/agent-collaboration.git`:

```sh
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:SKILL.md
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:references/collaboration/verification.md
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:references/collaboration/shared-coding-skills.md
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:references/skill/development.md
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:references/project/reports.md
git show ad88170b23920ddac0bff9a2fd467aa0c59917cf:references/project/design.md
```

Ponytail `full` was read completely. Its local content was independently aligned to the activated immutable authority:

```sh
gh api 'repos/DietrichGebert/ponytail/contents/skills/ponytail/SKILL.md?ref=2ed6c52c9d7e5e56942508591085fd45dea277d3' --jq .sha
git hash-object /Users/wenv/.codex/skills/ponytail/SKILL.md
```

Both returned `02c0712c86277d49d18a77da3a2b825657bf02d1`. `modern-python` was not activated. The minimalism rule informed review of the repair's numerical owner and reuse of existing validated artifacts/environments; it did not replace the scientific or public-error contract.

Initial and final-before-evidence `git rev-parse HEAD` both returned the candidate above. `git status --short` was empty. This reviewer performed no fetch, commit, push, source/test/example/reference/Gallery edit, dependency installation, or environment creation. The auxiliary reviewer performed no writes. The only durable audit write is this new file; disposable caches are confined to `tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/` for the execution owner's eventual disposition.

The prior FAIL artifact was independently compared byte-for-byte with its candidate Git blob and remains unchanged:

```text
00_archive/verification/AXIOMFIG-BAR-CONTRACT-260908-02/falsification-ca2d158.md
SHA-256 c4ee6c4185ffac1d8776a149429cfc2be6506cd86041b9103b6ea68fb0a73c22
```

## F1 repair replay and numerical boundary challenge

The previous candidate leaked raw `ValueError`/`OverflowError` while generating tick candidates for finite simple/grouped magnitudes `5e307` and `1e308`. The new `linear_limits` guard exercises the existing `nice_linear_axis` numerical grammar inside the adapter's error boundary and converts its `ValueError`/`OverflowError` into an explanatory validation error. It introduces no new visual constants, magnitude cutoff, scientific semantics, sample-specific branch, or blanket builder catch. The same geometry owner has real adapter and builder consumers across Bar grammars.

All source probes used the following environment values. Commands were invoked through `env` with these values; the export form below makes the reproductions concise:

```sh
cd /Users/wenv/Documents/skills/axiomfig
export PATH=/opt/homebrew/bin:/Users/wenv/miniforge3/bin:/usr/bin:/bin
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/tmp"
export MPLCONFIGDIR="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/mpl"
export HYPOTHESIS_STORAGE_DIRECTORY="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/hypothesis"
```

Exact Python replay and the additional randomized challenge of the final merged uncertainty bounds:

```sh
/Users/wenv/miniforge3/bin/python - <<'PY'
import itertools, warnings
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from axiomfig.intent import parse_figure_intent, build_intent_figure, FigureIntentError
from axiomfig.templates.bar.geometry import error_limits
from axiomfig.style import nice_linear_axis
counts=Counter()
for variant,v,orientation,uncertainty in itertools.product(['simple','grouped'],[5e307,1e308],['vertical','horizontal'],['none','error','endpoints']):
    data={'category':['A'],'value':[v]}
    sem={'orientation':orientation,'value_labels':False}
    if variant=='grouped': data['group']=['G']
    if uncertainty=='error': data['error']=[v*.2]
    if uncertainty=='endpoints': data.update(lower=[v*.5],upper=[v*1.2])
    if uncertainty!='none': sem['uncertainty_type']='CI'
    try:
        build_intent_figure(parse_figure_intent({'template':'bar.'+variant,'data':{r:r for r in data},'semantics':sem}),data)
    except FigureIntentError as exc:
        assert 'finite renderable axis geometry' in str(exc)
        counts['F1_bounded']+=1
    else: raise AssertionError((variant,v,orientation,uncertainty,'accepted'))
    finally: plt.close('all')
print(dict(counts))
rng=np.random.default_rng(91375)
counts=Counter()
with warnings.catch_warnings():
    warnings.simplefilter('ignore',RuntimeWarning)
    for i in range(3000):
        scale=10.**rng.uniform(303,308)
        values=rng.uniform(-1,1,3)*scale
        errors=rng.uniform(0,2,(3,2))*scale
        try: bounds=error_limits(values,errors)
        except ValueError: counts['bounded']+=1; continue
        result=nice_linear_axis(*bounds)
        assert all(np.isfinite([result.lower,result.upper,result.major_step,result.minor_step]))
        counts['validated_actual_bounds']+=1
print(dict(counts))
PY
```

Result: **24/24 prior failing public combinations now bounded as `FigureIntentError`**. Of 3,000 independently seeded finite/high-magnitude uncertainty trials, 509 rejected and 2,491 returned final bounds whose actual downstream axis calculation succeeded with finite limits and steps. This specifically probes the recombined bounds from `error_limits`, rather than assuming that checking a wider padded interval proves the actual bounds safe. The randomized loop is a numerical owner probe, not 3,000 rendered figures.

## Public artist, malformed-input, and scientific-contract probes

All following runtime probes used `parse_figure_intent` → `build_intent_figure`. Successful rendering probes additionally executed Agg `figure.canvas.draw()`. Exceptions were accepted only as `FigureIntentError` for invalid public inputs; unexpected exceptions would terminate the probe.

### Sparse grouped artists

An independent seeded probe used `np.random.default_rng(2098)`, with 12 successive samples. Each sample chose nine distinct keys without replacement from `itertools.product(['Z','A','Q','B'], ['w','b','x','a'])`, preserving sampled row order. Values were `rng.uniform(-7,9,9)` with the first value set to zero. Lower/upper widths were independently sampled from `[0,.7)` and `[0,.9)`, with both first-row widths set to zero. Every sample ran both orientations and none/row-wise asymmetric `error`/endpoint uncertainty: **72 successful public artist/draw probes**.

Assertions checked nine patches exactly; legend/global group and category tick order equal to first-seen input order; every supplied key present exactly once; all absent keys absent; supplied zero retained; each patch magnitude equal to its original row; and each group center at `category_index + (global_group_index - (group_count - 1)/2) * observed_bar_width`. This expected relation uses input order and observed width, not the production position implementation.

For each uncertainty container, its `LineCollection` endpoints matched the original lower/upper values in the group's supplied row order at `rtol=atol=1e-14`, and remained inside the value-axis limits. This covers groups absent from some categories without slot reassignment, implicit sorting, aggregation, or densification.

The decisive runnable artist assertions used:

```python
bars=[c for c in ax.containers if isinstance(c,BarContainer)]
assert len(ax.patches)==9
assert ax.get_legend_handles_labels()[1]==group_order
ticks=ax.get_xticklabels() if orientation=='vertical' else ax.get_yticklabels()
assert [x.get_text() for x in ticks]==cats_order
actual={}
for group,c in zip(group_order,bars,strict=True):
    indices=[i for i,g in enumerate(groups) if g==group]
    assert len(c.patches)==len(indices)
    for i,p in zip(indices,c.patches,strict=True):
        width=p.get_width() if orientation=='vertical' else p.get_height()
        center=(p.get_x() if orientation=='vertical' else p.get_y())+width/2
        expected=cats_order.index(cats[i])+(group_order.index(group)-(len(group_order)-1)/2)*width
        np.testing.assert_allclose(center,expected,rtol=0,atol=1e-14)
        actual[(cats[i],group)]=p.get_height() if orientation=='vertical' else p.get_width()
    if mode!='none':
        segments=c.errorbar.lines[2][0].get_segments()
        coord=1 if orientation=='vertical' else 0
        limits=ax.get_ylim() if orientation=='vertical' else ax.get_xlim()
        for i,seg in zip(indices,segments,strict=True):
            np.testing.assert_allclose(seg[:,coord],[vals[i]-low_width[i],vals[i]+high_width[i]],rtol=1e-14,atol=1e-14)
            assert limits[0]<=seg[:,coord].min()<=seg[:,coord].max()<=limits[1]
assert set(actual)==set(zip(cats,groups))
assert actual[(cats[0],groups[0])]==0
for key,val in zip(zip(cats,groups),vals,strict=True): assert actual[key]==val
```

### Endpoint extremes and malformed inputs

Simple/grouped × both orientations × values `[0.,5e-324,1e-320,1e-200,1.,1e250,1e300,1e307,-1e307,-5e307,5e307]` used ordered endpoints `min(.8*v,1.2*v)`/`max(.8*v,1.2*v)`, explicit `CI`, and value labels enabled. Result: **36 successful builds/draws and eight bounded rejections**, with no raw exception. Zero-width and subnormal intervals therefore retained a successful public execution path.

For both simple/grouped and both orientations, the valid one-row base was `value=2, lower=1, upper=3`. Each numeric role (`value`, `lower`, `upper`) was independently replaced with `None`, `{}`, `[None]`, `[{}]`, `[[1.]]`, `[10**1000]`, `[NaN]`, `[Inf]`, `['']`, `[complex(1,2)]`, or `[]`. Additional cases removed either endpoint; set lower to `2.1` or upper to `1.9`; added `error=[.5]`; omitted uncertainty meaning; or used `lower=-1e308, upper=1e308`. Result: **160/160 bounded**. Duplicate grouped `(A,g)` rows, `group=None`, and a whitespace-only group label were also bounded: **3/3**.

### Complete-grid preservation and normalization

For each of stacked, normalized-stacked, diverging-stacked, and mirrored, every individual cell was removed in turn from a three-category/two-series grid, in each orientation. Grouped-stacked used three categories × two groups × two components, likewise removing every individual cell. Categories were `['Z','A','Q']`, component/side labels `['d','b']`, and grouped-stacked groups `['k','s']`. Supplied values were sequential positive integers; normalized-stacked explicitly used `normalize`, and mirrored used `mirror_side='d'`. Result: **72/72 rejected with `complete logical grid`**.

Normalization used categories `['Z','Z','A','A']`, components `['b','a','b','a']`, both orientations, both modes, and both `[2,6,3,1]` and `[.25,.75,.75,.25]`. Six valid builds/draws produced component magnitudes `[[.25,.75],[.75,.25]]` at `rtol=0, atol=1e-14`. The two `proportion` runs with `[2,6,3,1]` rejected instead of renormalizing. `normalization=normalize` was rejected as an unsupported role for simple, grouped, stacked, diverging-stacked, grouped-stacked, and mirrored: **6/6**.

### Figure Intent visual boundary

The following fields were separately injected at the root, `semantics`, and data-role level of an otherwise valid endpoint intent: `font_size`, `fontsize`, `lw`, `linewidth`, `bar_width`, `legend`, `kwargs`, `style`, `markersize`, `margins`, `subplot_kw`, and `rcParams`. Result: **36/36 bounded**. Supplying `{'linewidth':1}` as each of `orientation`, `value_labels`, `xlabel`, and `uncertainty_type` was also bounded: **4/4**. No tested alias/nesting route exposed low-level Matplotlib fields.

## Architecture, archive, inventory, examples, and Gallery

Exact focused test command, using the source environment above:

```sh
/Users/wenv/miniforge3/bin/python -m pytest -q \
  tests/test_architecture_contracts.py tests/test_knowledge.py \
  tests/test_repository_hygiene.py tests/test_bar_examples.py \
  -k 'not execute and not uses_external' \
  -o cache_dir=tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/pytest-cache \
  --basetemp=tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/pytest
```

Result: **26 passed, 14 deselected in 0.84s**. These existing tests supplement the independent probes and static inspection; they are not treated as self-sufficient architecture proof.

The auxiliary reviewer independently checked identity, current authority/projection, registry/inventory, and archive/tool/package exclusions without writing files. Active intended repository identity uses `cigit-zgy/axiomfig`; no active `55`/`61` public-template magic count was found. Archived identities/provenance were preserved. Root `AGENTS.md` routes the one indexed active design set, and current Bar guide/routing/contract consistently describe endpoints, sparse grouped data, retained complete grids, and normalization. Active reports contained only the bound task under `reports/chatgpt/`; no fifth family, nested report, or active report README was present. Runtime and maintenance scripts do not load `00_archive` as authority.

The actual Ruff selection was inspected, not just its configuration:

```sh
RUFF_CACHE_DIR="$PWD/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/ruff" \
  /Users/wenv/miniforge3/bin/ruff check --show-files .
```

Its 148 selected paths contained **zero `00_archive` paths**. Pytest discovery is rooted at `tests`, Mypy at `src/axiomfig`, and package discovery/resources at `src`. One audit-only environment-command typo returned exit 127 before running any check; the corrected Ruff selection command succeeded. This is an audit-command defect, not a product failure.

Independent runtime inventory checked exact ID-set equality, not only counts:

```text
65 registered specs == 65 builders
61 public specs == 61 adapters
58 recommended specs
compatibility-only public IDs = bar/vertical, bar/horizontal, bar/dot
recommended Bar set = the nine accepted core grammars
```

Both new external examples were independently loaded with `load_figure_intent` and `load_dataset`, built through `build_intent_figure`, and drawn: `simple_interval` retained three supplied patches; `grouped_sparse_interval` retained five. This is real external CSV/mapping execution, not inline replacement of example data. Full Tectonic CSV/JSON rendering was left to the already completed ordinary gates.

Gallery PDF and PNG stem sets both exactly matched the dynamically curated 68 expected stems. All paths are flat `family/case` paths, retired subtrees are absent, compatibility-only IDs are excluded, and `GALLERY_TYPOGRAPHY='serif'` is actually used by the rendering owner. Every one of the **16 committed Bar PDF/PNG pairs passed `validate_pair`**. No Gallery artifact was regenerated or edited by this reviewer. The current curated Bar Gallery retains its existing supported cases; new endpoint/sparse public representations are explicitly covered by external examples and runtime probes.

## Candidate wheel and installed execution

The ordinary gate's already built wheel was reused at:

```text
tmp/AXIOMFIG-BAR-CONTRACT-260908-02/run/c3b9-full/test_clean_wheel_installs_reso0/wheelhouse/axiomfig-1.1.0-py3-none-any.whl
SHA-256 860ce3430d82a0e8c2909187d8ee3ecfad8f50c7553d9c4eafa6bbd7ac2d81f6
```

All **113 runtime members** were independently compared byte-for-byte against `git show c3b9e597b7b3533082cec24c066e4374d0ab28e8:src/<wheel-member>`: zero mismatches. Font, LaTeX, registry, and Bar contract resources were present. No wheel path contained reports, design, root archive, tests, examples, or evaluation payload.

The existing non-editable interpreter was then used from the audit scratch directory, separate from the importable source tree. The invocation removed both Python path overrides, disabled user-site imports and bytecode writes, and used audit-local caches:

```sh
cd /Users/wenv/Documents/skills/axiomfig/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit
env -u PYTHONPATH -u PYTHONHOME \
  PATH=/opt/homebrew/bin:/Users/wenv/miniforge3/bin:/usr/bin:/bin \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  TMPDIR="$PWD/tmp" MPLCONFIGDIR="$PWD/mpl" \
  /Users/wenv/Documents/skills/axiomfig/tmp/AXIOMFIG-BAR-CONTRACT-260908-02/run/c3b9-full/test_clean_wheel_installs_reso0/environment/bin/python - <<'PY'
import sys,os,itertools
from pathlib import Path
from zipfile import ZipFile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import axiomfig
from axiomfig.intent import parse_figure_intent,build_intent_figure,FigureIntentError
installed=Path(axiomfig.__file__).parent
assert installed.is_relative_to(Path(sys.prefix))
assert 'PYTHONPATH' not in os.environ and 'PYTHONHOME' not in os.environ
assert not any(Path(p or '.').resolve()==Path('/Users/wenv/Documents/skills/axiomfig/src') for p in sys.path)
wheel=Path(sys.prefix).parent/'wheelhouse/axiomfig-1.1.0-py3-none-any.whl'
with ZipFile(wheel) as z:
    names=[n for n in z.namelist() if n.startswith('axiomfig/') and not n.endswith('/')]
    for n in names: assert (installed.parent/n).read_bytes()==z.read(n),n
print('INSTALLED_RUNTIME_WHEEL_BYTE_EQUAL',len(names))
for orientation in ['vertical','horizontal']:
    data={'category':['C','B','C','A'],'group':['q','r','r','p'],'value':[0.,2.,-1.,3.],'lower':[0.,1.,-1.5,2.75],'upper':[0.,2.1,-.75,3.5]}
    doc={'template':'bar.grouped','data':{r:r for r in data},'semantics':{'orientation':orientation,'uncertainty_type':'CI','value_labels':False}}
    fig=build_intent_figure(parse_figure_intent(doc),data); ax=fig.axes[0]
    assert len(ax.patches)==4 and ax.get_legend_handles_labels()[1]==['q','r','p']
    values=[p.get_height() if orientation=='vertical' else p.get_width() for p in ax.patches]
    assert values==[0.,2.,-1.,3.]
    fig.canvas.draw(); plt.close(fig)
print('INSTALLED_SPARSE_ENDPOINT_DRAW',2)
count=0
for variant,v,orientation in itertools.product(['simple','grouped'],[5e307,1e308],['vertical','horizontal']):
    data={'category':['A'],'value':[v],'lower':[.5*v],'upper':[1.2*v]}
    if variant=='grouped': data['group']=['G']
    doc={'template':'bar.'+variant,'data':{r:r for r in data},'semantics':{'orientation':orientation,'uncertainty_type':'CI'}}
    try: build_intent_figure(parse_figure_intent(doc),data)
    except FigureIntentError as exc: assert 'finite renderable axis geometry' in str(exc); count+=1
    else: raise AssertionError('F1 returned')
print('INSTALLED_F1_ENDPOINT_BOUNDED',count)
PY
```

Result: **113 installed runtime files equal wheel bytes; two isolated sparse endpoint builds/draws passed; eight installed endpoint F1 reproductions were bounded**. The package-content comparison separately ties those same wheel bytes to the candidate commit, so a stale gate environment cannot explain the result.

## L1 — Existing association data-format wording drift

Classification: **low-severity, pre-existing out-of-scope `PROJECTION_DRIFT`**, not a Bar implementation blocker or an unresolved scientific design gap.

`references/figure-intent.md:26` describes association results as structured “JSON/YAML data”. The accepted external dataset implementation in `src/axiomfig/intent.py:161-205` supports CSV/JSON only; `references/agent-protocol.md:48` and the same Figure Intent guide elsewhere agree with CSV/JSON. Figure Intent YAML is supported, but YAML dataset files are a separate matter.

The guide blob was verified unchanged from handoff:

```sh
git rev-parse \
  d66a5b22406aa5dec1e2f6a3b3bffa0326a94cb2:references/figure-intent.md \
  c3b9e597b7b3533082cec24c066e4374d0ab28e8:references/figure-intent.md
```

Both return `10bfaa8b05cac4886971bb8ceac7a95a928306e5`. Calling `load_dataset(Path('tmp/AXIOMFIG-BAR-CONTRACT-260908-02/reaudit/unsupported.yaml'))` returns bounded `FigureIntentError: dataset must use .csv or .json` before any file read. Concrete consequence: a user following that isolated YAML-dataset wording is rejected rather than obtaining a plot. No unsupported data are silently accepted.

This was reported to the execution owner, who independently confirmed the pre-existing mismatch. Under the task's downstream ownership boundary the reference remains unchanged; its wording returns to ChatGPT's projection owner. Accepted Bar CSV/JSON and endpoint/sparse semantics are unaffected.

## Limitations and disposition

- This review challenges the pinned candidate and leaves no known task-level falsification blocker; it is neither final acceptance nor proof of task/report/push/cleanup completion.
- Full pytest, release evaluation, all-template structural repeatability, clean checkout, a fresh wheel build/install, full Ruff/Mypy/Skill validation, dependency audit, and hosted CI were not rerun by this reviewer. The execution owner reported completed ordinary gates and exact-candidate CI; this review does not independently attest those claims or substitute for their bound evidence.
- The package check reuses an existing wheel/environment, independently proving candidate-byte and installed-byte identity plus isolated public execution. It does not establish a new dependency resolution or a different supported Python platform.
- Agg artists and committed Bar PDF/PNG pairs were checked; the entire Gallery was not regenerated, the external JSON/Tectonic matrix was not rerun, and no visual redesign was assessed.
- Numeric/property samples are bounded probes, not exhaustive floating-point or all-family guarantees. No new non-Bar numerical claim follows solely from this Bar review.
- The existing L1 association YAML wording drift remains at its owner. No `DESIGN_GAP` was established, and no implementation/report/acceptance rule was silently broadened to remove it.
- Audit scratch remains under the exact task path for the execution owner to clean or retain deliberately. Candidate HEAD and all tracked candidate bytes remained unchanged until this new evidence file was added. Prior FAIL evidence remains verbatim.

The implementation owner may proceed only after this separately pinned evidence is sealed; subsequent production changes would require affected-gate and independent-review reconsideration rather than treating this candidate's result as transferable.
