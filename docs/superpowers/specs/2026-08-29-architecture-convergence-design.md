# AxiomFig Architecture Convergence Design

## 1. Scope

This design replaces the unpushed layered `.mplstyle` architecture with a frozen,
deterministic contract. It does not change the Matplotlib-to-vector-PDF-to-Tectonic
rendering boundary, add CJK/Japanese typography, or introduce a general plotting wrapper.

The current checkout is deliberately preserved as the migration source: local `master`
is ahead of `origin/master`, and three old gallery artifacts are modified. No pre-migration
reset, push, or recursive review cycle is allowed.

## 2. Canonical configuration

The repository root contains the only maintained visual configuration sources:

```plain
styles/
├── style.yaml
├── fonts.yaml
└── colors.yaml
```

`style.yaml` owns physical geometry, point sizes, strokes, tick geometry, legend placement,
panel labels, axis snapping, and plot-family defaults. `fonts.yaml` owns family roles,
default modes, source filenames, installation sources, redistribution status, and optional
system-font declarations. `colors.yaml` owns every canonical palette token.

The wheel installs these three files as data files. The source checkout remains the only
tracked copy; installed wheel data is a build artifact, not a second maintained source.

## 3. Thin loader

`src/axiomfig/config.py` provides only four responsibilities:

1. locate the three YAML files in a source checkout or installed wheel;
2. parse them with `yaml.safe_load`;
3. validate required top-level mappings and finite positive numeric tokens;
4. return immutable mappings and a Matplotlib `rcParams` dictionary.

The public interface is:

```python
load_contracts(config_root: Path | None = None) -> Contracts
build_rcparams(contracts: Contracts, *, geometry: str, typography: str) -> dict[str, object]
get_token(contracts: Contracts, dotted_path: str) -> object
```

`Contracts` is a frozen three-field dataclass containing read-only mappings. There is no
inheritance tree, plugin registry, schema compiler, generated `.mplstyle`, or arbitrary
configuration merge layer.

## 4. Font boundary

The default text families are Latin Modern Sans, Latin Modern Roman, and Maple Mono.
Mathematics uses Latin Modern Math. Font discovery checks exact files and internal family
names and fails instead of silently falling back.

No font binary is added in this round. `fonts.yaml` records the verified upstream license,
source URL, expected filenames, and `bundled: false` status for each open family. Arial,
Times New Roman, SimSun, and Yu Gothic are optional system families with `bundled: false`
and no redistribution claim. CJK/Japanese defaults and multilingual gallery probes are
removed from the active contract and documented as deferred.

## 5. Template convergence

The dynamic resource loader and nine resource modules are replaced by a normal Python
package with four plot-family files:

```plain
src/axiomfig/templates/
├── __init__.py
├── curves.py
├── distributions.py
├── surfaces.py
└── panels.py
```

`curves.py` owns line and scatter builders. `distributions.py` owns bar and violin.
`surfaces.py` owns heatmap. `panels.py` owns the deterministic multi-panel figure. The
registry retains only the canonical names needed by the skill and Gallery.

## 6. Visual contract

Geometry presets are 90, 140, and 190 mm wide at a 4:3 aspect. Font sizes remain physical
points and never scale with width.

`main_stroke = 0.8 pt` controls spines, normal lines, major ticks, error bars, reference
lines, and annotation strokes. `fill_edge = 0.6 pt` controls black edges on bars, violins,
filled scatter markers, and other filled patches.

Open linear axes use major `inout`, minor `in`, and exactly one minor tick between majors.
The minor tick's inward projection is `0.618` times the rendered inward projection of the
major tick. A rendered geometry characterization determines Matplotlib's actual `inout`
projection before the token is frozen. Filled surfaces use major/minor `out`. Categorical
axes preserve labels and remove tick lines.

The linear nice-axis helper chooses 5--7 major ticks using only
`1, 2, 2.5, 5 × 10^n`; the minor step is half the major step. Limits prefer whole-major
multiples, falling back to half-major multiples only when whole snapping adds visibly
unnecessary blank space. Log axes are unchanged.

Single-series axes have no legend. Multi-series legends are frameless, use handle length
`1.0`, begin as one row, align their right edge with the right spine, and reduce columns
only after a measured overflow. Tests cover normal, exact-boundary, and overflow/error.

Panel labels use bold 10 pt text with fixed physical x/y offsets from the upper-left spine.
Multi-panel data axes have equal rendered boxes. The heatmap colorbar occupies a dedicated
outer layout slot and cannot shrink one data panel.

## 7. Gallery and validation

The acceptance Gallery is exactly two typography directories. Each contains English-only
PDF/PNG pairs named `01_line` through `06_multi_panel`. The PNG is rasterized from the final
Tectonic PDF.

Unit tests exercise configuration, geometry, numeric axes, artist defaults, layout, and
the three legend cases without mass rendering. Real PDF E2E is limited to the canonical
Gallery. The complete deterministic test pass targets approximately one minute.

Every final PNG is inspected at normal and enlarged scale. PDF QA checks physical size,
font embedding/subsetting, Type 3 absence, page bounds, and paired artifacts.

## 8. Documentation and release gate

`references/latex-contract.md` records exact `siunitx`, `mhchem`, `amsmath`,
`unicode-math`, and `xcolor` macros. It explicitly states that the current Matplotlib text
pipeline is not TeX-native.

The lifecycle is fixed:

```plain
implementation
→ one deterministic test pass
→ one review
→ at most one repair pass
→ final validation
```

An Important finding after the repair pass blocks push. Otherwise the Agent report is
created only after refreshing the system date and scanning `reports/agent/`. Push is
followed by a remote-tree check for both Gallery directories, all PDF/PNG pairs, the report,
temporary-artifact absence, and exact `master == origin/master` equality.
