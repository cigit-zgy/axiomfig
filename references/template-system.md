# Template system

## Public surface

`src/axiomfig/templates/index.yaml` is the compact discovery and Gallery registry. It exposes 55
public templates across 13 scientific families. `layouts` provides four registered composition
capabilities but is not a plot family and does not produce public Gallery entries.

| Family | Variants |
|---|---|
| `line` | `single`, `multi`, `marker`, `confidence_band`, `errorbar`, `step`, `area` |
| `scatter` | `simple`, `grouped`, `regression`, `parity`, `bubble`, `hexbin` |
| `bar` | `vertical`, `horizontal`, `grouped`, `stacked`, `normalized_stacked`, `dot` |
| `distribution` | `histogram`, `density`, `ecdf`, `box`, `violin`, `box_violin`, `strip`, `raincloud` |
| `heatmap` | `basic`, `correlation`, `clustered`, `confusion_matrix`, `annotated` |
| `estimation` | `forest`, `point_interval`, `coefficient` |
| `diagnostics` | `residual`, `bland_altman`, `calibration`, `roc`, `precision_recall`, `learning_curve`, `qq`, `feature_importance` |
| `ordination` | `pca_scores`, `pca_biplot`, `pcoa`, `nmds` |
| `association` | `mantel`, `correlation_network` |
| `flow` | `sankey` |
| `field` | `contour`, `quiver` |
| `omics` | `volcano`, `enrichment_dot` |
| `survival` | `kaplan_meier` |

A template ID is `<family>/<variant>`, such as `scatter/parity`. Palette, marker, typography, and
figure width changes do not create variants. Multi-panel composition changes layout, not plot
identity.

## Discovery and execution

```text
templates/index.yaml
  -> selected family/contract.yaml
  -> family/adapter.py
  -> family/builders.py
  -> deterministic runtime and validation
```

The registry contains only family, variant, geometry, and public/layout classification. Each family
contract declares required and optional roles plus `input_mode: direct|precomputed`. Operability
counts are derived from contracts: 28 direct-data templates and 27 precomputed-result templates.
No public template is canonical-only.

An adapter validates role ownership and shape compatibility without silently dropping fields.
Builders own plot grammar and deterministic canonical examples. They do not own fonts, strokes,
ticks, margins, legend coordinates, panel geometry, palette values, or colorbar placement.

Scientific analysis remains outside plotting. Regression lines, intervals, ordinations, clustering
orders, Mantel results, adjusted p-values, model diagnostics, and survival curves are supplied as
explicit precomputed results where the contract requires them.

## Invariants

- Registry IDs are unique and match builder and contract variants exactly.
- Every public ID has one adapter and one direct/precomputed input mode.
- Every public ID has sans and serif PDF/PNG Gallery artifacts.
- Technical Tectonic probes are not templates.
- Recommendation knowledge remains under `references/template-knowledge/`, outside the registry.
- Explicit imports are used instead of plugin discovery, metaclasses, a DSL, or dynamic import magic.

For each public ID, Gallery contains:

```text
gallery/sans/<family>/<variant>.pdf
gallery/sans/<family>/<variant>.png
gallery/serif/<family>/<variant>.pdf
gallery/serif/<family>/<variant>.png
```
