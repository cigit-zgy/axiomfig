# Canonical template contract

Twenty public templates are grouped into four small Python family modules. Select the smallest template that expresses the scientific comparison; templates own data, labels, units, justified annotations, and arrangement, while visual defaults remain in YAML and thin helpers.

| Gallery stem | Builder | Module | Scientific intent |
|---|---|---|---|
| `01_single_line` | `single-line` | `curves.py` | one ordered response |
| `02_multi_line` | `multi-line` | `curves.py` | multiple ordered responses |
| `03_line_marker` | `line-marker` | `curves.py` | sampled ordered response |
| `04_line_ci` | `line-ci` | `curves.py` | response with confidence interval |
| `05_scatter` | `scatter` | `curves.py` | ungrouped association |
| `06_grouped_scatter` | `grouped-scatter` | `curves.py` | grouped association |
| `07_parity` | `parity` | `curves.py` | observed-predicted parity |
| `08_regression_scatter` | `regression-scatter` | `curves.py` | association with fitted line |
| `09_vertical_bar` | `vertical-bar` | `distributions.py` | vertical categorical magnitude |
| `10_grouped_bar` | `grouped-bar` | `distributions.py` | grouped categorical magnitude |
| `11_horizontal_bar` | `horizontal-bar` | `distributions.py` | horizontal categorical magnitude |
| `12_stacked_bar` | `stacked-bar` | `distributions.py` | compositional categorical magnitude |
| `13_boxplot` | `boxplot` | `distributions.py` | distribution summaries |
| `14_violin` | `violin` | `distributions.py` | distribution density |
| `15_box_violin` | `box-violin` | `distributions.py` | density plus summary |
| `16_histogram` | `histogram` | `distributions.py` | one-dimensional frequency |
| `17_heatmap` | `heatmap` | `surfaces.py` | matrix-valued surface |
| `18_errorbar` | `errorbar` | `curves.py` | estimates with uncertainty |
| `19_model_evaluation` | `model-evaluation` | `curves.py` | training/validation metric evolution |
| `20_multi_panel` | `multi-panel` | `panels.py` | canonical symmetric 2 × 2 composition |

Required consumers include deterministic nice-axis, open/filled/categorical tick, filled-artist, legend, panel-label, output-margin, and colorbar-layout helpers. Do not add per-template font sizes, stroke widths, edge colors, fill alpha, marker sizes, or export crop policies.
