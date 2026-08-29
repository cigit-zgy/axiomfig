# Template families

The six public builders are grouped into four small Python family modules under `src/axiomfig/templates/`:

| Intent | Builder | Module | Surface |
|---|---|---|---|
| ordered response | `line` | `curves.py` | open |
| association | `scatter` | `curves.py` | open |
| discrete magnitude | `bar` | `distributions.py` | categorical + filled |
| distribution | `violin` | `distributions.py` | categorical + filled |
| matrix magnitude | `heatmap` | `surfaces.py` | filled |
| related panels | `multi-panel` | `panels.py` | per axes |

Select the smallest builder that expresses the scientific comparison. Templates own data, labels, units, justified annotations, and subplot arrangement. They do not own fonts, sizes, stroke widths, palettes, tick geometry, panel offsets, physical size, or export settings.

Required helpers include `apply_nice_linear_axis`, `apply_axis_contract`, `apply_categorical_axis`, `apply_scatter_contract`, `apply_violin_contract`, `add_bar_value_labels`, `place_legend_above`, and `add_panel_labels`. Multi-panel colorbars must occupy independent support axes and must not shrink one ordinary panel.
