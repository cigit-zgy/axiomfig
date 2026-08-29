# Deterministic layout

## Legends

Single-series figures omit the legend. Multi-series legends are frameless, use `handlelength=1.0`, and sit outside the axes at top-right with their right edge aligned to the right spine. The top gap is `0.4666666667 pt`. The helper tries `N`, `N-1`, … columns and accepts the first candidate inside the figure boundary without panel-label collision. It does not reduce columns merely because a legend is wider than the data axis. Tests cover only normal, exact-boundary, and overflow/error cases.

Top and right tick labels remain off by default. A legend may not cross the figure boundary or cover the data area.

## Panel labels

Multi-panel labels are `(a)`, `(b)`, `(c)`, … at `11 pt` bold. Each is positioned from its outer panel footprint using fixed physical offsets: `2 pt` left and `2 pt` above. The offset is independent of DPI, figure width, subplot size, and any nested data/colorbar subdivision.

An **outer panel footprint** is the top-level GridSpec slot assigned to a panel. All outer footprints in a regular grid have identical width and height. An ordinary data axis fills the slot. A heatmap panel subdivides its own footprint into data, fixed gap, and colorbar columns with a nested GridSpec. The narrower heatmap data axis is intentional; the outer footprint remains equal to every peer and the colorbar cannot extend beyond or compress another panel.

## Layout acceptance

Gallery cases `33_two_panel`, `34_four_panel`, `35_six_panel`, and `36_complex_multi_panel` cover 1 × 2, 2 × 2, 2 × 3, and 3 × 2 layouts. Validate outer-footprint equality, panel-label containment, legend containment/right alignment, nested colorbar ownership, and row/column alignment after rendering the final PDF-derived PNG. The centralized fixed-page solver must also preserve the requested page dimensions and `1.5 pt` visible-artist padding.
