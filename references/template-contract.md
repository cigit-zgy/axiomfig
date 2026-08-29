# Canonical template contract

Thirty-six public templates are grouped into four Python family modules. Select the smallest builder that expresses the scientific comparison. Templates own deterministic example data, scientific labels, units, justified annotations, and arrangement; all reusable visual defaults remain in YAML and shared helpers.

| Gallery stem | Builder | Module | Scientific intent |
|---|---|---|---|
| `01_single_line` | `single-line` | `curves.py` | one ordered response |
| `02_multi_line` | `multi-line` | `curves.py` | redundant multi-series response |
| `03_line_marker` | `line-marker` | `curves.py` | sampled ordered response |
| `04_line_ci` | `line-ci` | `curves.py` | response with confidence interval |
| `05_scatter` | `scatter` | `curves.py` | ungrouped association |
| `06_grouped_scatter` | `grouped-scatter` | `curves.py` | grouped association |
| `07_parity` | `parity` | `curves.py` | observed-predicted parity |
| `08_regression_scatter` | `regression-scatter` | `curves.py` | association with fitted line and math |
| `09_vertical_bar` | `vertical-bar` | `distributions.py` | vertical categorical magnitude |
| `10_grouped_bar` | `grouped-bar` | `distributions.py` | grouped categorical magnitude |
| `11_horizontal_bar` | `horizontal-bar` | `distributions.py` | horizontal categorical magnitude |
| `12_stacked_bar` | `stacked-bar` | `distributions.py` | compositional categorical magnitude |
| `13_boxplot` | `boxplot` | `distributions.py` | distribution summaries |
| `14_violin` | `violin` | `distributions.py` | distribution density |
| `15_box_violin` | `box-violin` | `distributions.py` | density plus summary |
| `16_histogram` | `histogram` | `distributions.py` | one-dimensional frequency |
| `17_density` | `density` | `distributions.py` | deterministic kernel density |
| `18_ecdf` | `ecdf` | `distributions.py` | empirical cumulative distribution |
| `19_errorbar` | `errorbar` | `curves.py` | estimates with uncertainty |
| `20_forest_plot` | `forest-plot` | `curves.py` | categorical effects and intervals |
| `21_point_interval` | `point-interval` | `curves.py` | grouped point estimates and intervals |
| `22_bland_altman` | `bland-altman` | `curves.py` | method agreement and limits |
| `23_heatmap` | `heatmap` | `surfaces.py` | matrix-valued surface |
| `24_correlation_heatmap` | `correlation-heatmap` | `surfaces.py` | signed correlation matrix |
| `25_clustered_heatmap` | `clustered-heatmap` | `surfaces.py` | explicitly preordered similarity matrix |
| `26_confusion_matrix` | `confusion-matrix` | `surfaces.py` | classification counts |
| `27_roc_curve` | `roc-curve` | `curves.py` | receiver operating characteristic |
| `28_pr_curve` | `pr-curve` | `curves.py` | precision-recall behavior |
| `29_calibration_curve` | `calibration-curve` | `curves.py` | predicted-observed calibration |
| `30_residual_diagnostics` | `residual-diagnostics` | `curves.py` | residual structure and trend |
| `31_mantel_test` | `mantel-test` | `surfaces.py` | sparse Mantel-style matrix relationships |
| `32_model_evaluation` | `model-evaluation` | `curves.py` | training and validation evolution |
| `33_two_panel` | `two-panel` | `panels.py` | canonical 1 × 2 composition |
| `34_four_panel` | `four-panel` | `panels.py` | canonical 2 × 2 composition |
| `35_six_panel` | `six-panel` | `panels.py` | canonical 2 × 3 composition |
| `36_complex_multi_panel` | `complex-multi-panel` | `panels.py` | 3 × 2 composition with nested colorbar |

The clustered heatmap uses a deterministic declared order and does not claim runtime hierarchical clustering. The Mantel-style figure uses a compact correlation matrix plus four relationship links; width and color encode correlation while line style and labels encode significance, avoiding a dense network.

Required consumers include deterministic nice-axis, open/filled/categorical tick, face-alpha/opaque-edge, exact bar-width, redundant-series, legend, outer-footprint, panel-label, output-margin, and colorbar-layout helpers. Do not add per-template font sizes, stroke widths, edge colors, fill alpha, marker sizes, bar widths, line-cycle overrides, tick geometry, or export crop policies.
