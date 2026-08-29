# Round 06 Canonical Template Architecture and Gallery Rebuild Design

## 1. Scope and authority

This design implements the approved Round 06 brief directly on `master`. It formalizes the
scientific plot taxonomy, adds a compact registry and per-family input contracts, migrates the
existing builders, rebuilds Gallery exclusively from registered public templates, and corrects
the remaining panel-label semantic anchor. It does not add template recommendation knowledge,
agent orchestration, CJK work, TeX-native Matplotlib labels, animation, interactivity, or a broad
3D suite.

The verified starting point is commit
`32852bfd7d4e5e19362d9a41d31bd7f3416788c3` on local `master`, `origin/master`, and the GitHub
remote. The starting worktree is clean.

## 2. Baseline audit and migration map

Round 05 exposes 36 builders through one Python dictionary and duplicates the same order,
template names, output stems, and geometry in `gallery.py`. The implementation is split by
coarse code shape rather than scientific plot grammar:

```plain
curves.py          17 builders
distributions.py   10 builders
surfaces.py         5 builders
panels.py           4 layout builders
```

The authoritative registry and Gallery each expose 36 total entries: 32 scientific templates and
four composition layouts.

The canonical migration is:

| Old template | New template ID |
|---|---|
| `single-line` | `line/single` |
| `multi-line` | `line/multi` |
| `line-marker` | `line/marker` |
| `line-ci` | `line/confidence_band` |
| `errorbar` | `line/errorbar` |
| `scatter` | `scatter/simple` |
| `grouped-scatter` | `scatter/grouped` |
| `regression-scatter` | `scatter/regression` |
| `parity` | `scatter/parity` |
| `vertical-bar` | `bar/vertical` |
| `horizontal-bar` | `bar/horizontal` |
| `grouped-bar` | `bar/grouped` |
| `stacked-bar` | `bar/stacked` |
| `histogram` | `distribution/histogram` |
| `density` | `distribution/density` |
| `ecdf` | `distribution/ecdf` |
| `boxplot` | `distribution/box` |
| `violin` | `distribution/violin` |
| `box-violin` | `distribution/box_violin` |
| `heatmap` | `heatmap/basic` |
| `correlation-heatmap` | `heatmap/correlation` |
| `clustered-heatmap` | `heatmap/clustered` |
| `confusion-matrix` | `heatmap/confusion_matrix` |
| `forest-plot` | `estimation/forest` |
| `point-interval` | `estimation/point_interval` |
| `bland-altman` | `diagnostics/bland_altman` |
| `roc-curve` | `diagnostics/roc` |
| `pr-curve` | `diagnostics/precision_recall` |
| `calibration-curve` | `diagnostics/calibration` |
| `residual-diagnostics` | `diagnostics/residual` |
| `model-evaluation` | `diagnostics/learning_curve` |
| `mantel-test` | `association/mantel` |
| new canonical builder | `field/contour` |
| `two-panel` | `layouts/horizontal_2` |
| `four-panel` | `layouts/grid_2x2` |
| `six-panel` | `layouts/grid_2x3` |
| `complex-multi-panel` | `layouts/grid_3x2` |

The four layouts remain registered runtime capabilities but are not public scientific plot
templates and therefore do not create sans/serif taxonomy artifacts. Their purpose is layout
composition and geometry verification. This keeps Gallery's plot taxonomy exact while retaining
the required 2x2, 2x3, and 3x2 verification cases in tests.

## 3. Canonical package architecture

Each major family is a compact package with `builders.py`, `contract.yaml`, and a small
`__init__.py` export. `layouts/` has the same compact form but is classified separately.

```plain
src/axiomfig/templates/
├── __init__.py
├── registry.py
├── index.yaml
├── line/
├── scatter/
├── bar/
├── distribution/
├── heatmap/
├── estimation/
├── diagnostics/
├── association/
├── field/
└── layouts/
```

`index.yaml` is the canonical discovery and Gallery manifest. It contains only registry version,
family, variant, geometry, and public status. Explicit family `BUILDERS` mappings resolve the
listed IDs without dynamic imports. `registry.py` parses the YAML into a small immutable
`TemplateSpec` and validates exact agreement among the registry, contracts, and builders.
Gallery reads only the public specs returned by this registry. Tests and CLI derive their
expected sets from the same API instead of maintaining separate ordered lists.

Family contracts state required inputs, optional inputs, and scientific semantics that must be
explicit. They contain no advice about when a researcher should select a plot.

## 4. Panel-label semantic correction

The baseline rendered measurement separates the old gap into two terms:

| Layout | Footprint to PrimaryAxes left | Footprint to PrimaryAxes top | Old visible label-to-frame gap |
|---|---:|---:|---:|
| 2x2 ordinary panels | 30.84 pt | 11.63 pt | x 14.84-16.28 pt; y 13.63 pt |
| 2x2 heatmap panel | 44.96 pt | 11.63 pt | x 28.96 pt; y 13.63 pt |
| 2x3 ordinary panels | 30.84 pt | 11.63 pt | x 14.84-18.08 pt; y 13.63 pt |
| 3x2 heatmap panel | 44.96 pt | 11.63 pt | x 32.20 pt; y 13.63 pt |

The configured `-2/+2 pt` translation is therefore not the main cause. Tick labels, axis labels,
and colorbar allocation create the footprint-to-frame inset.

The new semantic anchor is the Primary Axes spine rectangle upper-left, with one central
`-1/+1 pt` translation. The label stays a panel-owned figure artist, independent of legend
geometry. The layout solver reserves a measured top label gutter inside each equal Outer Panel
Footprint; placing or refreshing the label never changes PrimaryAxes geometry. Geometry tests
measure the label bounding box against the PrimaryAxes frame, not the YAML token in isolation.

## 5. Public template set and Gallery invariant

Round 06 exposes 33 public scientific templates:

```plain
line          5
scatter       4
bar           4
distribution  6
heatmap       4
estimation    2
diagnostics   6
association   1
field         1
```

Gallery is a pure projection of these public registry entries. Every entry produces exactly one
PDF and one PNG for each of `sans` and `serif`, at a path derived from
`<typography>/<family>/<variant>`. No public registry entry may lack artifacts and no artifact may
lack a public registry entry. The expected Matplotlib result is therefore 66 pairs / 132 files.

The two Tectonic-native probes move to semantic paths under `gallery/technical/latex/`:

```plain
scientific_typography.pdf/.png
palettes.pdf/.png
```

They are technical probes, not templates. The complete expected Gallery is 68 pairs / 136 files.
The previous 74 flat pairs / 148 files are deleted by the registry-driven rebuild, not renamed.

## 6. Scientific behavior

Existing deterministic example arrays and fixed seeds are retained where they expose the visual
grammar. `association/mantel` remains visualization-only: precomputed correlation, Mantel
strength, and significance values are explicit inputs in its contract; the builder does not
compute the statistical test. The new `field/contour` uses a fixed analytic 2D scalar field and a
deterministic sequential color scale. Correlation heatmaps keep an explicit zero center and a
deterministic diverging scale.

Templates own plot grammar only. Fonts, sizes, strokes, ticks, legend geometry, panel-label
coordinates, palettes, margins, and colorbar geometry remain central runtime/YAML concerns.

## 7. Verification and delivery

Tests first establish RED behavior for registry parsing, unique IDs, contract/builder agreement,
Gallery projection, Mantel, the field family, package resources, layout separation, and the new
frame-relative label anchor. Targeted modules run during implementation. Ruff and the full pytest
suite run once at final validation.

The Gallery is rebuilt once from the new registry and reviewed once using representative sans and
serif plot families plus 2x2, 2x3, and 3x2 layout renders. At most one repair pass follows. The
report records measured geometry, counts, runtime, migrated/planned variants, and current CJK and
TeX-native limitations. Coherent commits are pushed to `master`, then local, fetched origin, and
GitHub remote SHAs and remote tree contents are verified.
