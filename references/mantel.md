# Mantel visualization engine

Read this reference only for advanced `association.mantel` customization. Normal requests need only
the family contract and minimal Figure Intent.

## Scientific input boundary

AxiomFig visualizes precomputed results. It does not calculate correlations, correlation p values,
confidence intervals, Mantel statistics, clustering, or permutations.

Required roles are `correlation_matrix`, `labels`, and `links`. The matrix must be square, symmetric,
bounded by `[-1, 1]`, and have a unit diagonal. Symmetric `NaN` pairs are rendered as missing rather
than converted to zero. Each link contains:

```yaml
source: Water chemistry
target: DO
mantel_r: -0.42
p_value: 0.018
```

Optional `label` and `metadata` fields are preserved. Legacy `source_group` and `target_label` keys
remain accepted and normalize to `source` and `target`.

Mantel r is accepted on `[-1, 1]`. Stroke width encodes `abs(r)` because strength is a magnitude;
the signed value remains attached to the rendered link. The canonical width mode uses bins at 0.25
and 0.50. Correlation p values, `lower_ci`, and `upper_ci` must be supplied as precomputed symmetric
matrices matching the correlation matrix.

## Advanced semantics

Canonical defaults are square glyphs, a lower matrix, hidden diagonal, original order, curved links,
and faded non-significant links.

```yaml
template: association.mantel
data:
  correlation_matrix: correlations
  labels: variables
  links: mantel_links
semantics:
  matrix_method: square
  matrix_type: lower
  diagonal: hide
  order: original
  nonsignificant_links: fade
```

Supported high-level semantics are:

| Semantic | Values |
|---|---|
| `matrix_method` | `circle`, `square`, `ellipse`, `number`, `shade`, `color`, `pie` |
| `matrix_type` | `full`, `upper`, `lower`, `mixed` |
| `diagonal` | `show`, `hide` |
| `lower_method`, `upper_method` | any matrix method; used by `mixed` |
| `order` | `original`, `alphabet`, `AOE`, `FPC`, `hclust` |
| `hclust_method` | `complete`, `ward`, `ward.D`, `ward.D2`, `single`, `average`, `mcquitty`, `median`, `centroid` |
| `clusters` | integer cluster count; requires `order: hclust` |
| `coefficients` | boolean coefficient overlay |
| `coefficient_format` | `decimal`, `percent` |
| `significance_mode` | `none`, `mark`, `p_value`, `blank`, `label_sig` |
| `significance_thresholds` | explicit decreasing thresholds; default `[0.05, 0.01, 0.001]` |
| `ci_mode` | `none`, `square`, `circle`, `rect` |
| `link_width_mode` | `binned`, `continuous` |
| `nonsignificant_links` | `hide`, `fade`, `show` |

Mixed rendering remains one public template:

```yaml
semantics:
  matrix_type: mixed
  lower_method: square
  upper_method: number
```

Physical sizes, line widths, colors, label coordinates, curve control points, legend coordinates,
and colorbar geometry are deterministic runtime decisions and are not Figure Intent fields.

## Composition anatomy

Mantel uses one normalized, immutable composition rather than a collection of finished-picture
branches:

```text
MantelComposition
  -> MatrixSpec                 structural mask, ordering, diagonal, target rail
  -> GlyphSpec[]               one reusable cell primitive per structural region
  -> StatisticalOverlay[]      coefficient, significance, CI, cluster outline
  -> CouplingSpec              source groups and Mantel relationships
  -> OrnamentLayer             Pearson colorbar and Mantel legends
```

The matrix layer selects cells before a glyph is known. Each glyph receives the same cell geometry,
correlation value, Axiom color token, and visibility flag. Mixed mode is therefore two ordinary
glyph layers with lower and upper masks; the 49 method pairs are coverage of the same composition
path, not 49 implementations. Statistical overlays are independent artists and can coexist when
the supplied scientific inputs make the combination valid.

Layout uses a fixed two-pass renderer-aware solve. The first pass creates the Figure, Primary Axes,
Auxiliary colorbar Axes, and the final legend grammar, then measures the selected-font label and
legend extents in physical points. The second pass solves matrix cell size, label gutters, source
strip, target rail, and ornament anchors. Character count is not a layout input and the solver does
not perform iterative visual search.

Ordering is a single data transformation before rendering. It applies the same permutation to the
matrix, labels, p values, CI bounds, cluster membership, and Mantel target mapping. No artist layer
may reorder its own data.

## Visual grammar

- `square` and `circle` use area, not side or radius, to encode `abs(r)`.
- `ellipse` uses orientation for sign and eccentricity for magnitude.
- `number` renders the coefficient with deterministic precision.
- `color` uses a fixed cell area and signed diverging fill.
- `shade` adds sign-directed vector hatching to the signed fill.
- `pie` uses angular fraction for magnitude and sweep direction for sign.
- `mark` and `p_value` identify non-significant cells, `blank` suppresses them, and `label_sig`
  labels significant cells using the explicit thresholds.
- CI modes visualize supplied bounds with vector artists; they never estimate intervals.
- Coupling routes source nodes directly to matrix-owned target anchors. A lower triangle uses a
  measured horizontal source rail at the lower edge of the unused triangle and a
  lower-left-to-upper-right target rail; an upper triangle is its physical mirror at the upper edge.
  Source labels occupy a renderer-measured outward strip, while routes remain on the matrix side.
  Target names are not repeated in a detached link column and target circles are hidden by default.
- Each link is one deterministic rail-normal cubic. Its clearance derives from source order, target
  order, link density, orientation, and lane index; there is no gate column or stochastic graph
  layout.
- Pearson color is constructed from `AxiomRed -> AxiomWhite -> AxiomBlue`. Mantel p-value bins use
  `AxiomOrange`, `AxiomGreen`, `AxiomPurple`, and `AxiomGrey`; all tokens originate in
  `resources/styles/colors.yaml`.
- Mantel p bins (`<0.001`, `0.001-0.01`, `0.01-0.05`, `>=0.05`) and strength bins remain in the
  legends even when a dataset does not use every bin.
- The Pearson key is a true Matplotlib colorbar on a registered Auxiliary Axes. Mantel strength and
  p-value legends are measured before their side-by-side or stacked placement is selected.

## R capability references and differences

The engine is an independent Matplotlib/NumPy implementation informed by the visual capability
surface of [corrplot](https://github.com/taiyun/corrplot),
[linkET](https://github.com/Hy4m/linkET), and [ggcor](https://github.com/hannet91/ggcor).
No R source is copied and no R runtime is required.

The audited mapping is stored in `references/mantel-r-parity.yaml`. It is an R grammar reference,
not a claim of pixel identity. Its generated PDF/PNG evidence lives under
`gallery/parity/mantel/`, with permanent contact sheets under `gallery/parity/mantel/review/`; both
are intentionally outside the public Template Registry. Normal Agents do not read the manifest or
atlas.

| R capability | AxiomFig implementation | Status | Notes |
|---|---|---|---|
| circle, square, ellipse, number, shade, color, pie | vector glyph layer | supported | AxiomFig styling, not an R-default clone |
| full, upper, lower | geometry-derived masks | supported | diagonal independently controlled |
| mixed | independent lower/upper glyph dispatch | supported | all 49 method pairs |
| original, alphabet, AOE, FPC | synchronized NumPy ordering | supported | links remain label-addressed |
| hclust | pure Python Lance-Williams engine | supported | `ward` aliases legacy `ward.D` |
| cluster rectangles | ordered cluster-block outlines | supported | explicit cluster count |
| coefficient annotation | deterministic text overlay | supported | decimal or percent |
| significance modes | precomputed p-value layer | supported | explicit thresholds |
| CI square, circle, rect | vector interval layer | supported | precomputed bounds only |
| `geom_couple` | source-to-target Bézier subsystem | supported | deterministic, no force layout |
| `nice_curvature` | source/order/density-aware lanes | supported | stable routing signature |
| r and p encodings | deterministic width/color mappings | supported | unused bins retained |
| multi-source coupling | physical-space-aware nodes | supported | arbitrary validated groups |

R dendrogram leaf orientation can differ when several merges have identical dissimilarity. AxiomFig
uses a stable original-index tie rule, while preserving the requested Lance-Williams recurrence and
cluster membership. `ward.D2` squares dissimilarities before the update; `ward` is normalized to the
legacy `ward.D` spelling documented by corrplot. Median and centroid linkage can exhibit inversions,
as in the R methods.
