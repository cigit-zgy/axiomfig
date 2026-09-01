# Figure Intent contract

Figure Intent is the minimal LLM-to-AxiomFig boundary. It selects scientific grammar and maps
scientific roles to a CSV column or JSON key; the runtime owns every reusable visual decision.

```yaml
template: scatter.parity
data:
  observed: observed
  predicted: predicted
geometry: single-column
typography: sans
```

Only `template` is required for a canonical example. `data`, `geometry`, `typography`, and
`semantics` are optional. When geometry is omitted, the selected template's Registry geometry is
used. A data-bearing intent must provide every required field in the selected family contract.
Scientific semantics that cannot be inferred belong under `semantics`:

```yaml
template: heatmap.correlation
data: {matrix: correlation, labels: variables}
semantics: {center: 0}
```

Precomputed association results use structured JSON/YAML data rather than parallel ad hoc arrays:

```yaml
template: association.mantel
data: {correlation_matrix: correlation_matrix, labels: labels, links: mantel_links}
semantics: {matrix_region: lower_left, matrix_method: circle, nonsignificant_links: fade}
```

Each Mantel link contains `source`, `target`, `mantel_r`, and `p_value`. The plotting layer validates
and displays these results but never computes Mantel statistics. See `references/mantel.md` only for
advanced matrix, ordering, significance, confidence-interval, or coupling capabilities.

The validator rejects font sizes, line widths, tick lengths, legend coordinates, panel offsets,
bar width, colorbar width, subplot spacing, and arbitrary fields. It also rejects missing explicit
uncertainty types, centers, significance thresholds, or other required contract fields.

CSV supplies named columns. JSON supplies a mapping of keys to arrays/matrices or a non-empty array
of row objects. Every registered public template has a deliberately explicit family-owned adapter.
Read only the selected family's `contract.yaml` to discover its required and optional roles. Some
templates consume direct observations, categorical records, matrices, grids, or flow records;
others consume precomputed scientific results such as intervals, ordination coordinates,
Mantel links, adjusted p-values, or survival curves. AxiomFig does not compute those analyses.

All public templates also accept a no-data Figure Intent for their deterministic canonical example.
Unknown, missing, or shape-incompatible data roles fail explicitly rather than being dropped or
routed to arbitrary Matplotlib code.

```bash
axiomfig-intent intent.yaml --data observations.csv --output output/figure
```

The command builds the selected canonical grammar, applies the geometry and typography contracts,
renders PDF through the Tectonic wrapper, creates PNG from that PDF, and runs runtime validation.

## Multi-panel composition status

**Verdict: PARTIAL.** The four `layouts/*` IDs are reachable through a no-data Figure Intent and
render deterministic canonical composition examples. They are not currently a user-data
composition interface:

- layout contracts declare `panels`, but layouts have no family data adapter;
- `Figure Intent.data` maps roles to scalar CSV columns or JSON keys, not nested panel intents;
- `axiomfig-intent` therefore cannot compose independent external datasets into user-specified
  panels.

A future composition design may add `panels` containing ordinary Figure Intents, but it must retain
one public boundary, reuse the same panel schema, expose no visual coordinates, and preserve the
deterministic layout engine. That public-schema change is deferred rather than implied by the
current canonical layout builders.
