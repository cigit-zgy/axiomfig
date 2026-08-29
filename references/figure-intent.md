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
`semantics` are optional. A data-bearing intent must provide every required field in the selected
family contract. Scientific semantics that cannot be inferred belong under `semantics`:

```yaml
template: heatmap.correlation
data: {matrix: correlation, labels: variables}
semantics: {center: 0}
```

The validator rejects font sizes, line widths, tick lengths, legend coordinates, panel offsets,
bar width, colorbar width, subplot spacing, and arbitrary fields. It also rejects missing explicit
uncertainty types, centers, significance thresholds, or other required contract fields.

CSV supplies named columns. JSON supplies a mapping of keys to arrays/matrices or a non-empty array
of row objects. The v1 external-data adapters are deliberately explicit:

- `line/single`;
- `scatter/simple`, `scatter/grouped`, `scatter/parity`;
- `bar/vertical`;
- `distribution/violin`;
- `heatmap/correlation`;
- `estimation/forest`;
- `diagnostics/residual`;
- `ordination/pca_scores`;
- `omics/volcano`;
- `survival/kaplan_meier`.

All 55 public templates accept a no-data Figure Intent to render their deterministic canonical
example. A data-bearing intent for another variant fails explicitly rather than silently ignoring
user data or generating arbitrary Matplotlib code.

```bash
axiomfig-intent intent.yaml --data observations.csv --output output/figure
```

The command builds the selected canonical grammar, applies the geometry and typography contracts,
renders PDF through the Tectonic wrapper, creates PNG from that PDF, and runs runtime validation.

