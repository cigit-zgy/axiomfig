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
- `PLANNED`: the semantic capability is justified, but no executable public surface exists.
- `NOT_SUPPORTED`: the current architecture intentionally does not offer it.

A `PLANNED` name is a descriptive capability label, not a callable API, Figure Intent field, or
promise of a future spelling. Only an `AVAILABLE` surface may be emitted as an executable public
control.

## Translate implementation wording into semantic intent

Researchers may describe a legitimate visual goal using plotting-library arguments, numeric
coordinates, backend names, or other implementation details. Treat those details as a proposed
implementation, not as the visual or scientific intent itself.

Use this sequence:

1. Identify the intended visual outcome and the element it affects.
2. Preserve the current scientific representation, data mapping, and template grammar unless the
   researcher explicitly asks to change the scientific encoding.
3. Discard low-level implementation details from the public decision surface.
4. Route the semantic goal to the relevant element contract.
5. Use the real `AVAILABLE`, `INTERNAL_ONLY`, `PLANNED`, or `NOT_SUPPORTED` status.
6. Keep deterministic defaults for every unrelated element.

A low-level visual request must not silently change scientific encoding. For example, a request for
smaller scatter markers does not authorize replacing the scatter with hexbin counts; a request to
move a legend does not authorize removing series; a collision request does not authorize dropping
mandatory labels. Change the scientific grammar only when the researcher explicitly requests a
different representation or the existing grammar cannot express the supplied scientific intent.

For non-`AVAILABLE` adjustments, preserve the semantic goal in the response but do not invent a
Figure Intent field, Matplotlib argument, coordinate, physical number, or backend option. Exact
deterministic values remain in packaged YAML/runtime contracts.

The ontology and relation terms used by these topics belong to
[figure anatomy](../figure-anatomy.md); this directory is only the default -> exception -> supported
surface map.
