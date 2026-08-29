# Figure Intent operability coverage

## Scope

This matrix freezes the AxiomFig v1 public surface at 55 templates. It classifies the scientific
input shape without changing taxonomy or visual defaults:

- **A — direct data:** observation vectors, categorical records, matrices, grids, or flow records
  can be visualized without an inferential analysis step.
- **B — precomputed result:** the user supplies model, statistical, ordination, association, omics,
  or survival results computed outside AxiomFig.
- **C — canonical only:** no public v1 template is allowed to remain in this class.

The `Current` column records the audited baseline
`01da286a5b1e178976d51986571fe22c56483acb`, before adapter completion. The role column is the
frozen v1 external-data contract; optional presentation text and scientifically meaningful
semantics remain in each family `contract.yaml`.

## Coverage matrix

| Template | Class | Current | v1 required external roles |
|---|:---:|:---:|---|
| `line/single` | A | yes | `x`, `y` |
| `line/multi` | A | no | `x`, `series_values`, `series_labels` |
| `line/marker` | A | no | `x`, `y` |
| `line/confidence_band` | B | no | `x`, `estimate`, `lower`, `upper`, `uncertainty_type` |
| `line/errorbar` | B | no | `x`, `estimate`, `error`, `uncertainty_type` |
| `line/step` | A | no | `x`, `y` |
| `line/area` | A | no | `x`, `y` |
| `scatter/simple` | A | yes | `x`, `y` |
| `scatter/grouped` | A | yes | `x`, `y`, `group` |
| `scatter/regression` | B | no | `x`, `y`, `fitted` |
| `scatter/parity` | A | yes | `observed`, `predicted` |
| `scatter/bubble` | A | no | `x`, `y`, `size` |
| `scatter/hexbin` | A | no | `x`, `y` |
| `bar/vertical` | A | yes | `category`, `value` |
| `bar/horizontal` | A | no | `category`, `value` |
| `bar/grouped` | A | no | `category`, `value`, `group` |
| `bar/stacked` | A | no | `category`, `value`, `component` |
| `bar/normalized_stacked` | A | no | `category`, `value`, `component`, `normalization` |
| `bar/dot` | A | no | `category`, `value` |
| `distribution/histogram` | A | no | `value` |
| `distribution/density` | B | no | `x`, `density` |
| `distribution/ecdf` | A | no | `value` |
| `distribution/box` | A | no | `value`, `category` |
| `distribution/violin` | A | yes | `value`, `category` |
| `distribution/box_violin` | A | no | `value`, `category` |
| `distribution/strip` | A | no | `value`, `category` |
| `distribution/raincloud` | A | no | `value`, `category` |
| `heatmap/basic` | A | no | `matrix`, `row_labels`, `column_labels`, `color_semantics` |
| `heatmap/correlation` | B | yes | `matrix`, `labels`, `center` |
| `heatmap/clustered` | B | no | `matrix`, `row_labels`, `column_labels`, `row_order`, `column_order`, `color_semantics` |
| `heatmap/confusion_matrix` | B | no | `matrix`, `class_labels` |
| `heatmap/annotated` | A | no | `matrix`, `row_labels`, `column_labels`, `annotations`, `color_semantics` |
| `estimation/forest` | B | yes | `label`, `estimate`, `interval`, `uncertainty_type` |
| `estimation/point_interval` | B | no | `label`, `estimate`, `interval`, `uncertainty_type` |
| `estimation/coefficient` | B | no | `term`, `estimate`, `interval`, `uncertainty_type` |
| `diagnostics/residual` | B | yes | `fitted`, `residual` |
| `diagnostics/bland_altman` | B | no | `mean`, `difference`, `agreement_type` |
| `diagnostics/calibration` | B | no | `predicted_probability`, `observed_frequency` |
| `diagnostics/roc` | B | no | `false_positive_rate`, `true_positive_rate` |
| `diagnostics/precision_recall` | B | no | `recall`, `precision` |
| `diagnostics/learning_curve` | B | no | `iteration`, `metric`, `series` |
| `diagnostics/qq` | B | no | `theoretical_quantile`, `sample_quantile`, `reference_distribution` |
| `diagnostics/feature_importance` | B | no | `feature`, `importance`, `importance_type` |
| `ordination/pca_scores` | B | yes | `coordinates`, `explained_variance` |
| `ordination/pca_biplot` | B | no | `coordinates`, `loadings`, `explained_variance` |
| `ordination/pcoa` | B | no | `coordinates`, `explained_variance`, `distance_metric` |
| `ordination/nmds` | B | no | `coordinates`, `stress`, `distance_metric` |
| `association/mantel` | B | no | `correlation_matrix`, `matrix_labels`, `links`, `link_strength`, `significance` |
| `association/correlation_network` | B | no | `nodes`, `edges`, `edge_weight` |
| `flow/sankey` | A | no | `source`, `target`, `value` |
| `field/contour` | A | no | `x_grid`, `y_grid`, `z`, `color_semantics` |
| `field/quiver` | A | no | `x`, `y`, `u`, `v`, `color_semantics` |
| `omics/volcano` | B | yes | `effect_size`, `adjusted_p_value`, `significance_threshold`, `effect_threshold` |
| `omics/enrichment_dot` | B | no | `term`, `enrichment`, `significance`, `size` |
| `survival/kaplan_meier` | B | yes | `time`, `survival_probability` |

## Frozen counts and execution rule

| State | Count |
|---|---:|
| Public templates | 55 |
| Class A direct-data templates | 28 |
| Class B precomputed-result templates | 27 |
| Baseline adapters | 12 |
| Final externally operable | 55 |
| Final direct-data operable | 28 |
| Final precomputed-result operable | 27 |
| Final canonical-only | 0 |

Every data-bearing Figure Intent must resolve all contract roles, pass family-specific shape
validation, reach the registered canonical builder with normalized kwargs, and fail on any
unsupported field. AxiomFig does not fit regressions, clustering, ordination, Mantel statistics,
model diagnostics, adjusted p-values, survival curves, or uncertainty intervals.

The baseline `Current` column is retained for audit provenance. Completion is enforced by the
55-case true external-data Evaluation corpus, not by changing those historical baseline values.
