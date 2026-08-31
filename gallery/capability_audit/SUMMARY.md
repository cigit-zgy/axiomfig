# Figure capability audit summary

This audit asks two separate questions: what the current public AxiomFig Skill can reach, and what
Matplotlib core can express with benchmark-local, deterministic figure code. It does not add public
templates or production solvers.

## Results by case

Agent tokens are the measured tokens reported by the isolated `gpt-5.6-sol` progressive-disclosure
run. Each case used a fresh context with only the AxiomFig Skill surface.

| ID | Figure | Skill action | Skill output | Agent tokens | Native result | Difficulty | Architecture class | Fragile / missing anatomy |
|---|---|---|---|---:|---|---|---|---|
| 01 | Complex clustermap | unsupported | — | 4,356 | success | HARD | IV | Manual seven-Axes topology; ornament/alignment constraints are case-local. |
| 02 | Dense PairGrid | unsupported | — | 3,245 | success | MODERATE | II | Shared-axis grid is supported; no missing anatomy. |
| 03 | Joint + marginals | unsupported | — | 3,408 | success | MODERATE | II | Shared marginal axes are supported; selected-label placement is local. |
| 04 | Extended forest | unsupported | — | 4,269 | success | MODERATE | II | Long external statistics column requires explicit page reservation. |
| 05 | KM + risk table | unsupported | — | 4,204 | success | EASY | II | Risk-table auxiliary axes are supported. |
| 06 | Calibration dashboard | unsupported | — | 4,692 | success | MODERATE | II | Heterogeneous shared-x dashboard is supported. |
| 07 | PDP / ICE dashboard | unsupported | — | 4,244 | success | MODERATE | II | 1-D/2-D mixed grid and colorbar are supported. |
| 08 | Influence labels | unsupported | — | 4,145 | success, fragile | FRAGILE | IV | Movable annotations/connectors require case-specific edge lanes. |
| 09 | Dense volcano | clarify | — | 4,278 | success, fragile | FRAGILE | IV | Thirty labels are readable; connector crossing remains FRAGILE. |
| 10 | Dotplot + dendrogram | unsupported | — | 3,562 | success | EASY | II | Dendrogram/matrix alignment and two ornaments are supported. |
| 11 | UpSet | unsupported | — | 3,245 | success | EASY | II | Set/intersection axes and connectors are supported. |
| 12 | OncoPrint | unsupported | — | 3,245 | success | EASY | II | Multi-glyph cells and marginal summaries are supported. |
| 13 | Ridge density | unsupported | — | 3,245 | success | HARD | IV | Overlapping-Axes label z-order required a figure-level repair. |
| 14 | Distribution composite | unsupported | — | 3,442 | success | EASY | II | Layered categorical artists and supplied brackets are supported. |
| 15 | PCA biplot | unsupported | — | 4,298 | success, minor debt | HARD | IV | Dense loading-label/connector placement remains case-specific. |
| 16 | Mantel + correlation | render `association/mantel` | validated PDF | 7,501 | success | EASY | I | Current registered complex control is adequate. |
| 17 | Classifier dashboard | unsupported | — | 4,244 | success | MODERATE | II | Mixed diagnostic panels and matrix colorbar are supported. |
| 18 | Regression diagnostics | unsupported | — | 4,495 | success, fragile | FRAGILE | IV | Influential-observation labels require case-specific lanes. |
| 19 | Learning / scalability | clarify | — | 3,581 | success | MODERATE | II | Six coordinated panels are supported; public composition is absent. |
| 20 | Manhattan + Q-Q | unsupported | — | 3,245 | success | EASY | II | Grouped genomic x geometry and adjacent Q-Q axes are supported. |

Skill totals: **1 render, 2 clarify, 0 require_precomputed, 17 unsupported**. The sole render was
executed through `axiomfig-intent` and validated; it is committed as
`skill/16_mantel_correlation.pdf`.

## Engineering-complexity proxies

The literal count is an AST count of benchmark-local numeric constants, not a quality score. It is
reported because a high count together with manual `add_axes` calls and fragile review evidence is
a useful sign of case-specific geometry. No builder performs a post-draw correction pass; the audit
therefore does not hide iterative layout work behind its render time.

| ID | Case LOC | Shared-helper LOC | Numeric literals | `add_axes` calls | Renderer measurements | Final render (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01 | 55 | 0 | 47 | 7 | 0 | 0.2979 |
| 02 | 62 | 0 | 58 | 0 | 0 | 0.4016 |
| 03 | 69 | 0 | 68 | 0 | 0 | 0.0974 |
| 04 | 41 | 0 | 32 | 1 | 0 | 0.1188 |
| 05 | 55 | 0 | 40 | 2 | 0 | 0.0589 |
| 06 | 43 | 0 | 46 | 0 | 0 | 0.1086 |
| 07 | 43 | 0 | 56 | 0 | 0 | 0.2796 |
| 08 | 21 | 26 | 15 | 0 | 0 | 0.0929 |
| 09 | 47 | 26 | 36 | 0 | 0 | 0.1383 |
| 10 | 53 | 0 | 50 | 0 | 0 | 0.2155 |
| 11 | 60 | 0 | 89 | 0 | 0 | 0.0735 |
| 12 | 60 | 0 | 62 | 0 | 0 | 0.1637 |
| 13 | 34 | 0 | 42 | 0 | 0 | 0.2499 |
| 14 | 63 | 0 | 52 | 0 | 0 | 0.0865 |
| 15 | 50 | 0 | 52 | 0 | 0 | 0.0794 |
| 16 | 75 | 0 | 81 | 2 | 0 | 0.1754 |
| 17 | 50 | 0 | 75 | 0 | 0 | 0.2969 |
| 18 | 49 | 26 | 71 | 0 | 0 | 0.1462 |
| 19 | 55 | 0 | 76 | 0 | 0 | 0.1834 |
| 20 | 69 | 0 | 58 | 0 | 0 | 0.1543 |

## Anatomy-level capability matrix

`SUPPORTED` means the accepted native output demonstrated the relation. `FRAGILE` means it worked
only through case-local geometry or retained a meaningful defect. No relevant element was MISSING.

| ID | Primary / auxiliary Axes | Shared axes / alignment | Legend / colorbar / table | Dense labels / connectors | Main owner |
|---|---|---|---|---|---|
| 01 | SUPPORTED | FRAGILE | SUPPORTED | N/A | Matplotlib native; future Axiom layout contract |
| 02 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 03 | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | Matplotlib native; public-template coverage |
| 04 | SUPPORTED | SUPPORTED | N/A | FRAGILE | Family builder / renderer measurement |
| 05 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 06 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 07 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 08 | SUPPORTED | N/A | N/A | FRAGILE | Movable-annotation layer |
| 09 | SUPPORTED | N/A | SUPPORTED | FRAGILE | Movable-annotation layer |
| 10 | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | Matplotlib native; public-template coverage |
| 11 | SUPPORTED | SUPPORTED | N/A | SUPPORTED | Matplotlib native; public-template coverage |
| 12 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 13 | SUPPORTED | SUPPORTED | N/A | FRAGILE | Axes z-order / fixed row-label layer |
| 14 | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | Matplotlib native; public-template coverage |
| 15 | SUPPORTED | N/A | SUPPORTED | FRAGILE | Movable-annotation layer |
| 16 | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | Existing AxiomFig Mantel runtime |
| 17 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 18 | SUPPORTED | SUPPORTED | N/A | FRAGILE | Movable-annotation layer |
| 19 | SUPPORTED | SUPPORTED | SUPPORTED | N/A | Matplotlib native; public-template coverage |
| 20 | SUPPORTED | SUPPORTED | N/A | SUPPORTED | Matplotlib native; public-template coverage |

## Recurring failure classes

1. **Class-D annotations (`T01/T02/T05/E02`)** — cases 08, 09, 15 and 18 required
   label/connector decisions outside ordinary data grammar. Case 09 retained connector crossings.
2. **Composite topology and shared geometry (`G03/G04`)** — Matplotlib expressed every requested
   grid, marginal, table and auxiliary axis, but cases 01, 04 and 13 required explicit physical
   reservation or z-order handling rather than a reusable AxiomFig contract.
3. **Public grammar coverage (`S03`)** — 19/20 complex requests did not produce a Skill render even
   though the native audit produced all 20. This is predominantly a public template/composition
   abstraction gap, not a Matplotlib capability gap.

## External-tool trigger

The trigger was met because the same movable-annotation class required case-specific handling in at
least four cases. `external_probe/` therefore contains adjustText and textalloc evidence for the
influence and volcano topologies. Both reduce manual text collisions, but neither result justifies a
production dependency yet: connector topology and deterministic contract ownership still need a
focused follow-up benchmark.

## Architecture recommendation

### KEEP

- Figure Intent as the only Agent/runtime boundary.
- Existing deterministic style, typography, primary-area and ornament ownership.
- Matplotlib core as the default renderer; it reached 20/20 with five-run repeatability.

### OPTIMIZE

- Add reusable composite-Axes topology descriptions only when a future public template consumes
  them; the audit shows shared alignment and auxiliary-Axes geometry are not missing in Matplotlib.
- Replace case-local dense-label lanes with a renderer-measured annotation contract when product
  scope includes at least two real templates that need it.

### ADD

- In a separately scoped round, benchmark one deterministic class-D annotation allocator contract
  against cases 08, 09, 15 and 18. Backend/tool choice and force parameters must remain runtime
  implementation details, never Figure Intent fields.

### DEFER

- New public templates, nested user-data composition, an OncoPrint/UpSet domain package, and any
  external production dependency. Capability evidence alone is not product authorization.

## Reproducibility

- Archived round-one evidence: 50 PDFs, byte-identical after move.
- Authoritative originals: 20 PDFs; native: 20 PDFs; Skill: 1 PDF; external probe: 4 PDFs.
- Native repeatability: 20/20 cases produced one identical geometry signature across five runs.
- Native font probe: all 20 embed XCharter/Charter and none use Type 3 fonts.
- The formal registry-driven Gallery remains a separate 118-pair release surface.
