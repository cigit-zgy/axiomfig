# Deterministic layout helpers

## Panel labels

`add_panel_labels(axes, gap_pt=2.0)` adds bold `(a)`, `(b)`, and subsequent labels in iterable order. Each label anchors at `(0, 1)` in its axes and adds a y-only `ScaledTranslation` in physical points. The label's left edge therefore aligns with the left spine and its lower edge sits `2 pt` above the top spine, independent of axes size or DPI.

Use the helper only for multi-panel figures. Supply axes in scientific reading order; the helper does not infer a grid or reorder panels. Every axes receives the same physical offset and the current figure typography pass assigns the selected family.

## Legends

`place_legend_above(axis, gap_pt=2.0)` implements the verified external legend contract:

1. Read handles and labels; return `None` when there are none.
2. Try `ncol=len(handles)` first, then decrease one column at a time until the rendered legend width fits the axes.
3. Place a frameless legend above the top spine at a `2 pt` physical gap with its right edge aligned to the right spine.
4. For subplot-managed axes, reserve top space and re-measure if the legend would cross the figure top.
5. Raise `ValueError` if the legend still cannot fit; do not silently clip or move it over the data.

The helper measures rendered geometry, so templates do not guess `ncol`. It only controls legends created from the target axes' handles/labels. A manually created figure-level legend or an axes placed with `add_axes` outside subplot layout is not automatically rearranged; an uncontainable axes legend is rejected.

## Mixed layouts

Apply open/filled tick and artist helpers per axes before adding panel labels. `layout-4-panel` and `style-contract` demonstrate different surface types in one figure without weakening the per-axes contract. The whole figure still selects exactly one typography mode, geometry preset, and palette layer.
