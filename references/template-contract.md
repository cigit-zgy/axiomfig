# Canonical template contract

`src/axiomfig/templates/index.yaml` is the compact discovery and Gallery registry. It exposes 33
public scientific templates across nine families. The `layouts` package contains four registered
composition capabilities but is not a scientific plot family and does not create public Gallery
entries.

| Family | Implemented variants |
|---|---|
| `line` | `single`, `multi`, `marker`, `confidence_band`, `errorbar` |
| `scatter` | `simple`, `grouped`, `regression`, `parity` |
| `bar` | `vertical`, `horizontal`, `grouped`, `stacked` |
| `distribution` | `histogram`, `density`, `ecdf`, `box`, `violin`, `box_violin` |
| `heatmap` | `basic`, `correlation`, `clustered`, `confusion_matrix` |
| `estimation` | `forest`, `point_interval` |
| `diagnostics` | `residual`, `bland_altman`, `calibration`, `roc`, `precision_recall`, `learning_curve` |
| `association` | `mantel` |
| `field` | `contour` |
| `layouts` | `horizontal_2`, `grid_2x2`, `grid_2x3`, `grid_3x2` (non-public composition) |

A template ID is `<family>/<variant>`, for example `scatter/parity` or
`association/mantel`. After selecting an ID from `index.yaml`, read only that family's
`contract.yaml`. The contract declares accepted required/optional data fields and scientific
semantics that must be explicit. It contains no recommendation knowledge.

Uncertainty type is explicit for interval templates. A diverging correlation heatmap requires a
meaningful center. Mantel receives precomputed correlation, relationship strength, and
significance values; the visualization builder does not compute the Mantel test. Clustered
heatmaps receive an explicit order and do not claim runtime hierarchical clustering.

Builders own plot grammar and deterministic example data. They must consume shared nice-axis,
tick, edge, bar-width, series, legend, layout, panel-label, anatomy, margin, and colorbar helpers.
They must not hard-code fonts, font sizes, strokes, tick lengths, palette values, legend/panel
coordinates, figure margins, or colorbar geometry.
