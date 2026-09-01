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

The association family contract is the executable owner of required, optional, and legacy link
field names. Its optional `label` and `metadata` fields are preserved; its legacy endpoint aliases
normalize to canonical `source` and `target`.

Mantel r is accepted on `[-1, 1]`. Stroke width encodes `abs(r)` because strength is a magnitude;
the signed value remains attached to the rendered link. The canonical width mode uses the
family-owned executable bin contract. Correlation p values, `lower_ci`, and `upper_ci` must be
supplied as precomputed symmetric matrices matching the correlation matrix.

## Advanced semantics

Canonical defaults are circle glyphs, a lower-left matrix region, a hidden matrix diagonal,
original order, explicit source/target nodes, three p-value categories, and faded
non-significant links. The lower-left matrix owns left and bottom variable labels; its coupling
occupies the complementary upper-right triangle. `upper_right` is the exact geometric mirror and
owns top and right labels. Label edges and the coupling triangle are derived from the matrix region,
not selected independently.

```yaml
template: association.mantel
data:
  correlation_matrix: correlations
  labels: variables
  links: mantel_links
semantics:
  matrix_region: lower_left
  matrix_method: circle
  diagonal: hide
  order: original
  nonsignificant_links: fade
```

Supported high-level semantics are:

| Semantic | Values |
|---|---|
| `matrix_method` | `circle`, `square`, `ellipse`, `number`, `shade`, `color`, `pie` |
| `matrix_region` | `lower_left`, `upper_right`; the two mirrored triangular layouts |
| `matrix_type` | `full`, `upper`, `lower`, `mixed` |
| `diagonal` | `show`, `hide` |
| `lower_method`, `upper_method` | any matrix method; used by `mixed` |
| `order` | `original`, `alphabet`, `AOE`, `FPC`, `hclust` |
| `hclust_method` | `complete`, `ward`, `ward.D`, `ward.D2`, `single`, `average`, `mcquitty`, `median`, `centroid` |
| `clusters` | integer cluster count; requires `order: hclust` |
| `coefficients` | boolean coefficient overlay |
| `coefficient_format` | `decimal`, `percent` |
| `significance_mode` | `none`, `mark`, `p_value`, `blank`, `label_sig` |
| `significance_thresholds` | explicit decreasing thresholds; the family grammar owns the default |
| `ci_mode` | `none`, `square`, `circle`, `rect` |
| `link_width_mode` | `binned`, `continuous` |
| `p_value_mode` | `canonical` (three bins), `detailed` (four bins) |
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
  -> MatrixSpec                 structural mask, ordering, diagonal, label-edge contract
  -> GlyphSpec[]               one reusable cell primitive per structural region
  -> StatisticalOverlay[]      coefficient, significance, CI, cluster outline
  -> NodeLayer                 parallel SourceRail and diagonal TargetRail nodes
  -> CouplingSpec              ordered quadratic source-to-target relationships
  -> OrnamentLayer             Pearson colorbar and Mantel legends
```

The matrix layer selects cells before a glyph is known. Each glyph receives the same cell geometry,
correlation value, Axiom color token, and visibility flag. Mixed mode is therefore two ordinary
glyph layers with lower and upper masks; the 49 method pairs are coverage of the same composition
path, not 49 implementations. Statistical overlays are independent artists and can coexist when
the supplied scientific inputs make the combination valid.

Layout uses a fixed two-pass renderer-aware solve. The first pass creates the Figure, Primary Axes,
Auxiliary colorbar Axes, and the final legend grammar, then measures the selected-font variable
labels, source labels, and legends in physical points. The second pass solves matrix cell size,
matrix-edge label gutters, source positions, the diagonal interface, and ornament anchors. Source
labels may wrap once at a measured word boundary. Character count is not a layout input and the
solver does not perform iterative visual search. The matrix plus complementary coupling triangle is
the Primary Visual Square. Runtime validation measures its final renderer transform and enforces
equal physical width and height as well as equal cell dimensions.

Ordering is a single data transformation before rendering. It applies the same permutation to the
matrix, labels, p values, CI bounds, cluster membership, and Mantel target mapping. No artist layer
may reorder its own data.

## Visual grammar

- `circle` is the canonical Mantel glyph. `square` and `circle` use area, not side or radius, to
  encode `abs(r)`.
- `ellipse` uses orientation for sign and eccentricity for magnitude.
- `number` renders the coefficient with deterministic precision.
- `color` uses a fixed cell area and signed diverging fill.
- `shade` adds sign-directed vector hatching to the signed fill.
- `pie` uses angular fraction for magnitude and sweep direction for sign.
- `mark` and `p_value` identify non-significant cells, `blank` suppresses them, and `label_sig`
  labels significant cells using the explicit thresholds.
- CI modes visualize supplied bounds with vector artists; they never estimate intervals.
- A lower-left matrix places labels on its left and bottom edges and coupling in the upper-right
  triangle. An upper-right matrix places labels on its top and right edges and coupling in the
  lower-left triangle. These are the only two triangular orientations and are exact mirrors.
- The shared diagonal is an interface, not a label rail. Each variable owns one small visible
  target node on that interface; variable names are not repeated there. Each source group owns a
  larger node on one SourceRail parallel to the target diagonal. Source order maps monotonically
  along that rail, and all source labels use one measured normal-side placement rule. Every link
  begins and ends at those explicit node coordinates.
- Each route is one quadratic Bezier from SourceNode centre to TargetNode centre. All links share
  one contract-owned curvature magnitude. Targets before the ordered rail midpoint use negative
  curvature and targets at or after it use positive curvature; for odd target counts the centre is
  assigned to the second half. Geometry never depends on previously rendered routes, candidate
  lanes, crossing scores, or stochastic layout.
- Source and target nodes reuse the shared scatter marker contract: the source marker uses the
  family-owned area ratio, the target marker uses the base area, faces use scatter alpha, and edges
  use the shared black fill-edge stroke. Source fills follow deterministic series colors; target
  fills use one neutral Axiom color.
- Pearson color uses the Axiom diverging palette. Canonical and detailed Mantel p-value modes use
  their family-owned ordered threshold/color mappings. All tokens originate in
  `resources/styles/colors.yaml`, and every active mode shows every executable bin in the legend.
- The Pearson key is a true Matplotlib colorbar on a registered Auxiliary Axes. Mantel strength and
  p-value legends are measured before their side-by-side or stacked placement is selected. Pearson
  r uses the global Primary Visual Area and vertical Colorbar contracts in
  `references/layout-contract.md` and `references/style-contract.md`. Mantel supplies the scalar
  mapping, ticks, `Pearson r` label, and scientific reference square but owns no generic Colorbar
  dimensions or reservation logic.

## SourceRail packing contract

`TargetRail` is the matrix diagonal and `SourceRail` is one parallel line in the complementary
coupling triangle. SourceNodes remain collinear and preserve deterministic scientific source order.
Every source label is placed on the same outward normal side of SourceRail. Its visual gap is the
physical distance from the circular marker edge to the nearest visible text edge, using the
family-owned `source_label_gap_pt` token; it is not a node-centre offset.

Each SourceNode and its renderer-measured label bbox form one `SourceGroupFootprint`. The solver
projects those footprints onto the SourceRail tangent and packs adjacent groups with the
family-owned `source_group_gap_pt` visible
clearance. The resulting rail uses the shortest feasible content-derived span: short labels reduce
the span and longer labels expand it only as required. The complete packed rail is then translated
along the coupling-region outward normal until a source footprint activates the family-owned
`source_boundary_padding_pt` of the Primary Visual Square. This maximizes distance from TargetRail and gives the shared
quadratic curves their usable physical length without a link-length option.

All measurements use the selected font renderer, physical marker area, and point-space conversion.
The solve is deterministic, uses at most two fixed passes, and never reorders sources based on text
width. Figure Intent may select scientific Mantel semantics but never supplies SourceRail, label,
marker, Colorbar, or curve coordinates.

## R capability references and differences

The engine is an independent Matplotlib/NumPy implementation informed by the visual capability
surface of [corrplot](https://github.com/taiyun/corrplot),
[linkET](https://github.com/Hy4m/linkET), and [ggcor](https://github.com/hannet91/ggcor).
No R source is copied and no R runtime is required.

The formal Gallery deliberately keeps only four publication-oriented Mantel figures under each
typography tree: `mantel_canonical`, `mantel_dense`, `mantel_long_labels`, and
`mantel_multigroup`. Combinatorial capability coverage remains in tests rather than a separate
user-facing atlas.

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
| `geom_couple` | source-to-target Bezier subsystem | supported | one quadratic curve family |
| `nice_curvature` principle | target-half curvature sign | supported | no route optimizer or prior-route state |
| r and p encodings | deterministic width/color mappings | supported | unused bins retained |
| multi-source coupling | parallel physical SourceRail | supported | arbitrary validated groups |

R dendrogram leaf orientation can differ when several merges have identical dissimilarity. AxiomFig
uses a stable original-index tie rule, while preserving the requested Lance-Williams recurrence and
cluster membership. `ward.D2` squares dissimilarities before the update; `ward` is normalized to the
legacy `ward.D` spelling documented by corrplot. Median and centroid linkage can exhibit inversions,
as in the R methods.
