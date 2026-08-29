# Template selection

Use the smallest archetype that expresses the scientific comparison. Every entry is a real native Matplotlib builder under `templates/`.

| Intent | Template names |
|---|---|
| trajectory or response over an ordered axis | `line-single`, `line-multi`, `line-marker`, `line-ci` |
| association, groups, or agreement | `scatter-basic`, `scatter-grouped`, `scatter-parity` |
| discrete magnitude comparison | `bar-vertical`, `bar-grouped` |
| distribution comparison | `boxplot`, `violin` |
| matrix magnitude and structure | `heatmap` |
| predictive performance and error | `model-evaluation`, `residual` |
| related panels | `layout-2-panel`, `layout-4-panel` |
| CJK/math pipeline check | `multilingual` |

Choose parity only when both axes represent comparable observed and predicted quantities, and include the 1:1 reference. Use residual plots to expose magnitude-dependent error. Use a heatmap for an actual matrix; do not turn unrelated categorical values into a pseudo-matrix.

Keep source data and statistical meaning intact. Confidence intervals come from supplied or computed uncertainty, not a decorative band. Axis labels include units. High-density scatter or heatmap image artists may be rasterized locally while axes and text remain vector.

Legend location and annotations depend on the data and therefore remain template decisions. Font size, linewidth, marker size, palette, tick geometry, figure width, and export settings remain style decisions.
