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
semantics: {matrix_method: square, matrix_type: lower, nonsignificant_links: fade}
```

Each Mantel link contains `source`, `target`, `mantel_r`, and `p_value`. The plotting layer validates
and displays these results but never computes Mantel statistics. See `references/mantel.md` only for
advanced matrix, ordering, significance, confidence-interval, or coupling capabilities.

The validator rejects font sizes, line widths, tick lengths, legend coordinates, panel offsets,
bar width, colorbar width, subplot spacing, and arbitrary fields. It also rejects missing explicit
uncertainty types, centers, significance thresholds, or other required contract fields.

CSV supplies named columns. JSON supplies a mapping of keys to arrays/matrices or a non-empty array
of row objects. All 55 public templates have deliberately explicit family-owned adapters. Read only
the selected family's `contract.yaml` to discover its required and optional roles. Twenty-eight
templates consume direct observations, categorical records, matrices, grids, or flow records;
twenty-seven consume precomputed scientific results such as intervals, ordination coordinates,
Mantel links, adjusted p-values, or survival curves. AxiomFig does not compute those analyses.

All public templates also accept a no-data Figure Intent for their deterministic canonical example.
Unknown, missing, or shape-incompatible data roles fail explicitly rather than being dropped or
routed to arbitrary Matplotlib code.

```bash
axiomfig-intent intent.yaml --data observations.csv --output output/figure
```

The command builds the selected canonical grammar, applies the geometry and typography contracts,
renders PDF through the Tectonic wrapper, creates PNG from that PDF, and runs runtime validation.
