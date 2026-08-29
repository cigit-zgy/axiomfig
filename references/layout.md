# Deterministic layout

## Legends

Single-series figures omit the legend. Multi-series legends are frameless, use `handlelength=1.0`, and sit outside the axes at top-right with their right edge aligned to the right spine. The helper first tries one row, measures the rendered boundary, and reduces column count only for true overflow. Tests cover only normal, exact-boundary, and overflow/error cases.

Top and right tick labels remain off by default. A legend may not cross the figure boundary or cover the data area.

## Panel labels

Multi-panel labels are `(a)`, `(b)`, `(c)`, … at `10 pt` bold. Each is positioned from its own axes using fixed physical offsets: `2 pt` left of the left spine and `2 pt` above the top spine. The offset is independent of DPI, figure width, and subplot size.

All ordinary data axes in a panel grid must have identical boxes. A heatmap colorbar is created through a dedicated layout slot/support axes; it does not compress the heatmap panel or any peer panel.

## Layout acceptance

The `multi-panel` Gallery figure is the canonical symmetry check. Validate ordinary axes box equality, panel-label containment, legend containment/right alignment, and colorbar independence after rendering the final PDF-derived PNG.
