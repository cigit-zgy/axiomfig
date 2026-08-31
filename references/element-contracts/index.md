# Scientific Figure Element Contracts

Use this index only when the user asks for a non-default visual or positional treatment. If the
request does not require one, stop here and retain every deterministic default.

| Requested change | Read |
|---|---|
| publication geometry, axis scale or limits, tick policy, long tick labels, axis labels, grid | [axes.md](axes.md) |
| line, marker, bar, fill, interval, reference mark, matrix cell, contour, vector glyph | [marks.md](marks.md) |
| legend, colorbar, panel label, marginal/risk-table/dendrogram region | [ornaments.md](ornaments.md) |
| selected labels, collision handling, connectors, significance text/brackets | [annotations.md](annotations.md) |
| panel or Auxiliary Axes physical geometry | [layout contract](../layout-contract.md) |
| font family or typography mode | [typography contract](../typography.md) |
| color meaning or palette provenance | [style contract](../style-contract.md) |

Read one topic whenever possible. A topic reports each adjustment as `AVAILABLE`, `INTERNAL_ONLY`,
`PLANNED`, or `NOT_SUPPORTED`:

- `AVAILABLE`: an exact current public AxiomFig surface can execute it.
- `INTERNAL_ONLY`: runtime code can own it, but Figure Intent does not expose it.
- `PLANNED`: a semantic need is justified, but no executable public surface exists.
- `NOT_SUPPORTED`: the current architecture intentionally does not offer it.

Use only `AVAILABLE` surfaces. For every other status, preserve the semantic goal in the response
but do not invent a Figure Intent field, Matplotlib argument, coordinate, physical number, or
backend option. Exact deterministic values remain in packaged YAML/runtime contracts.

The ontology and relation terms used by these topics belong to
[figure anatomy](../figure-anatomy.md); this directory is only the default -> exception -> supported
surface map.
