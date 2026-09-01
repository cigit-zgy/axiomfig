# Template system

## Public surface

`src/axiomfig/templates/index.yaml` is the compact discovery and Gallery registry. Public-template
counts are derived from it across 13 scientific families. `layouts` provides four registered composition
capabilities but is not a plot family and does not produce public Gallery entries.

| Family | Variants |
|---|---|
| `line` | `single`, `multi`, `marker`, `confidence_band`, `errorbar`, `step`, `area` |
| `scatter` | `simple`, `grouped`, `regression`, `parity`, `bubble`, `hexbin` |
| `bar` | core: `simple`, `grouped`, `stacked`, `normalized_stacked`, `grouped_stacked`, `diverging_stacked`, `range`, `mirrored`, `waterfall`; compatibility: `vertical`, `horizontal`, `dot` |
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

The registered layout builders currently provide validated canonical composition fixtures. They
are not external-data adapters and do not make nested panel Figure Intent user-operable. See the
explicit PARTIAL status in `references/figure-intent.md`.

## Discovery and execution

```text
templates/index.yaml
  -> selected family/contract.yaml
  -> family/adapter.py
  -> family/builders.py
  -> deterministic runtime and validation
```

The registry contains only family, variant, geometry, public/layout classification, and a minimal
core/compatibility status for released IDs. Each family
contract declares required and optional roles plus `input_mode: direct|precomputed`. Operability
counts are derived from contracts rather than duplicated as constants. No public template is
canonical-only.

An adapter validates role ownership and shape compatibility without silently dropping fields.
Builders own plot grammar and deterministic canonical examples. They do not own fonts, strokes,
ticks, margins, legend coordinates, panel geometry, palette values, or colorbar placement.

Scientific analysis remains outside plotting. Regression lines, intervals, ordinations, clustering
orders, Mantel results, adjusted p-values, model diagnostics, and survival curves are supplied as
explicit precomputed results where the contract requires them.

## Invariants

- Registry IDs are unique and match builder and contract variants exactly.
- Every public ID has one adapter and one direct/precomputed input mode.
- Every public ID has an executable data path; the formal serif-only Gallery is curated and may
  exclude compatibility-only IDs or include multiple representative cases for one core grammar.
- Technical Tectonic probes are not templates.
- Recommendation knowledge remains under `references/template-knowledge/`, outside the registry.
- Explicit imports are used instead of plugin discovery, metaclasses, a DSL, or dynamic import magic.

Formal Gallery artifacts use one family-first layer:

```text
gallery/<family>/<case>.pdf
gallery/<family>/<case>.png
```
