# Template selection and helper contract

Use the smallest archetype that expresses the scientific comparison. Every entry is a native Matplotlib builder under `src/axiomfig/resources/templates/` and is included in the wheel.

| Intent | Template names | Surface |
|---|---|---|
| trajectory or ordered response | `line-single`, `line-multi`, `line-marker`, `line-ci` | open |
| association, groups, agreement | `scatter-basic`, `scatter-grouped`, `scatter-parity` | open |
| discrete magnitude comparison | `bar-vertical`, `bar-grouped` | filled |
| distribution comparison | `boxplot`, `violin` | filled |
| matrix magnitude and structure | `heatmap` | filled |
| predictive performance and error | `model-evaluation`, `residual` | mixed by axes |
| related panels | `layout-2-panel`, `layout-4-panel` | per axes |
| multilingual family probe | `multilingual` | open |
| deterministic acceptance panel | `style-contract` | per axes |

Choose parity only when both axes represent comparable observed and predicted quantities and include the 1:1 reference. Use residual plots to expose magnitude-dependent error. Use a heatmap for an actual matrix. Confidence bands represent supplied or computed uncertainty, not decoration; labels include units.

## Exact mixed 2 x 2 recipe

For one figure containing line, grouped bar, scatter, and heatmap panels, select the `style-contract` template. Do not start from `layout-4-panel`: its fourth panel is a violin plot, so adapting it would re-open plot/module decisions already frozen in `style-contract`.

Use these seven modules exactly:

| Layer | Selection | File |
|---|---|---|
| base | `publication` (fixed default) | `src/axiomfig/resources/styles/base/publication.mplstyle` |
| geometry | `double-column` | `src/axiomfig/resources/styles/geometry/double-column.mplstyle` |
| typography | `sans` | `src/axiomfig/resources/styles/typography/sans.mplstyle` |
| colors | `default` | `src/axiomfig/resources/styles/colors/default.mplstyle` |
| plot | `line` (neutral mixed-figure layer) | `src/axiomfig/resources/styles/plot/line.mplstyle` |
| language | `multilingual` | `src/axiomfig/resources/styles/language/multilingual.mplstyle` |
| rendering | `vector` | `src/axiomfig/resources/styles/rendering/vector.mplstyle` |

```bash
python scripts/render.py style-contract \
  --output "$PWD/tmp/style-contract/style-contract" \
  --geometry double-column --typography sans --colors default \
  --plot line --language multilingual --rendering vector
```

One figure can compose only one plot layer, so `line` is the neutral selection here; it does not pretend that every panel is open-surface. The template deterministically calls `apply_axis_contract(..., surface="open")` for line/scatter and `surface="filled"` for bar/heatmap, applies bar/scatter artist helpers, places measured legends, adds uniform panel labels, and leaves the colorbar support axes outside the data-axes tick contract. There is no per-panel `.mplstyle` guessing.

## Required thin helpers

```python
from axiomfig.template_helpers import (
    add_bar_value_labels,
    add_panel_labels,
    apply_axis_contract,
    apply_scatter_contract,
    place_legend_above,
)
```

- Every data-bearing axes calls `apply_axis_contract(axis, surface="open" | "filled")`. Linear data axes get one minor tick per major interval; log locators are preserved. Do not apply the helper to Matplotlib-generated support axes such as a colorbar.
- Every scatter collection passes through `apply_scatter_contract(collection)` for black `0.6 pt` edges.
- Every bar container passes through `add_bar_value_labels(axis, containers, decimals=2)`. It applies black `0.6 pt` edges, `2 pt` label padding, fixed trailing-zero precision, and reserves headroom for vertical or horizontal bars. `decimals` must be non-negative.
- Multi-panel templates call `add_panel_labels(axes)` once; single-panel templates omit panel labels.
- Legends that have labels call `place_legend_above(axis)`. The helper measures width, prefers one row, reduces columns only when needed, aligns to the right spine, and fails if it cannot remain inside the figure.

Read [layout.md](layout.md) for physical offsets and containment limits. High-density scatter or image artists may be rasterized locally, but axes and text remain vector-first.

Templates may change data, labels, units, annotations, data-justified limits, and scientific content. They do not set contract fonts, sizes, stroke widths, palettes, tick geometry, panel offsets, physical figure size, or export settings.
