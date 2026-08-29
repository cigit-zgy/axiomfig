# AxiomFig v1 sprint design

## Outcome

AxiomFig v1 is a deterministic scientific-figure package and Agent Skill with a small LLM-facing
boundary. A normal request reads the routing section of `SKILL.md`, the compact template registry,
and at most one family contract or one knowledge entry. It does not require the model to invent
low-level Matplotlib geometry.

## Baseline and migration map

The verified starting point is `83441bbf1da020c95deb3003848b8191090d5bbd`; local `master`,
`origin/master`, and GitHub `master` agree. The older supplied SHA is historical rather than the
active baseline.

| Current v0.1 architecture | v1 disposition | Target |
|---|---|---|
| deterministic style, layout, ornaments, anatomy, render, validation | keep and strengthen | visual kernel |
| nine public template families, 33 variants | keep validated grammar; extend deliberately | 13 families, about 55 variants |
| compact registry and per-family contracts | keep as discovery source; extend schema minimally | registry + contracts |
| registry-derived sans/serif Gallery | keep invariant; rebuild after registry expansion | generated visual catalogue |
| example-only builders | retain canonical examples; add a real data-facing adapter | Figure Intent execution |
| hard-coded template CLI | preserve compatibility; add intent command | small CLI surface |
| no template-selection knowledge layer | add separately from registry | progressive-disclosure knowledge base |
| no system evaluation corpus | add deterministic request cases and metrics | evaluation suite |
| package version 0.1.0, no CI | audit resources and metadata; add focused CI | release-ready v1 |

## Scientific template scope

The v1 target is 55 public variants. Existing variants remain unless a correctness problem is
found. The additions emphasize recurrent grammar rather than palette- or marker-only differences.

| Family | v1 public variants |
|---|---|
| line | single, multi, marker, confidence_band, errorbar, step, area |
| scatter | simple, grouped, regression, parity, bubble, hexbin |
| bar | vertical, horizontal, grouped, stacked, normalized_stacked, dot |
| distribution | histogram, density, ecdf, box, violin, box_violin, strip, raincloud |
| heatmap | basic, annotated, correlation, clustered, confusion_matrix |
| estimation | point_interval, forest, coefficient |
| diagnostics | residual, bland_altman, calibration, roc, precision_recall, learning_curve, qq, feature_importance |
| ordination | pca_scores, pca_biplot, pcoa, nmds |
| association | mantel, correlation_network |
| flow | sankey |
| field | contour, quiver |
| omics | volcano, enrichment_dot |
| survival | kaplan_meier |

Deferred variants are documented as post-v1 extensions rather than implemented as weak aliases.
`layouts` remains a non-public plot family and composes the deterministic layout engine.

## Figure Intent boundary

`FigureIntent` is a small validated record containing:

- `template`, using the stable `family.variant` spelling at the user boundary;
- `data`, mapping scientific roles to keys or columns;
- optional `geometry` and `typography`;
- optional `semantics` only when scientific meaning cannot be derived, such as interval type,
  diverging center, or significance meaning.

It never accepts font size, line width, tick length, legend coordinates, bar width, panel spacing,
or colorbar geometry. Input data may be tabular CSV or structured JSON. A compact explicit adapter
maps supported roles to deterministic builders; there is no generic plotting DSL. Canonical Gallery
builders remain usable without external data and serve as examples and visual fixtures.

## Registry and knowledge separation

`templates/index.yaml` answers what exists. A family `contract.yaml` answers accepted roles and
required scientific semantics. `references/template-knowledge/index.yaml` answers which family or
variant matches an intent and routes to one short topic page. Recommendation prose never enters the
registry. This keeps discovery cheap and prevents Gallery generation, builder lookup, contracts,
and documentation from becoming competing sources of truth.

## Validation and evaluation

Runtime validation remains responsible for geometry, ownership, fonts, clipping, collisions, PDF
validity, and output containment. Evaluation measures the system: registry/contract consistency,
intent validity, expected routing for 24 representative requests, deterministic byte- or image-level
repeatability where stable, render success, Gallery coverage, discovery size, and a representative
mixed-panel render. Deterministic checks replace LLM judging wherever possible.

## Packaging and release boundary

The wheel must contain styles, fonts and attributions, template registry/contracts, LaTeX resources,
and the knowledge index needed at runtime. CLI commands remain few: render, validate, gallery, and
intent. Focused CI installs the package, runs Ruff and the non-E2E suite, validates the Skill, and
performs a small headless render. Local release validation additionally exercises Tectonic, Poppler,
the full Gallery, a clean wheel install, and a fresh clone/equivalent checkout.

Full CJK/Japanese typography, TeX-native Matplotlib labels, animation, dashboards, a 3D suite,
microscopy, chemical drawing, and GIS remain explicit v1 limitations.

## Rougier-derived implementation rules

AxiomFig independently translates the reviewed book principles into six constraints: explicit
Figure/Axes/Artist ownership; physical-point and millimetre geometry; layout solved before drawing;
ornaments subordinate to data; coherent typography and semantic color; and vector-first validation.
No source prose, images, or implementations are copied.

