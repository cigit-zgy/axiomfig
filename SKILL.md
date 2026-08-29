---
name: axiomfig
description: Use when creating, revising, or validating deterministic publication-quality scientific figures with Matplotlib, especially when journal-width geometry, physical-point typography, scientific axes, legends, panel labels, or Tectonic PDF wrapping matter.
---

# AxiomFig

## Normal Agent route

1. Turn the user request into scientific intent and data roles. If the graphical form is not
   obvious, read only `references/template-knowledge/index.yaml`, then its one routed topic file.
2. Read `src/axiomfig/templates/index.yaml`, select one `family.variant`, and read only that
   family's `contract.yaml`.
3. Write minimal Figure Intent; see `references/figure-intent.md`. Specify scientific semantics
   such as uncertainty type, diverging center, or significance threshold only when required.
4. Run `axiomfig-intent intent.yaml --data data.csv --output output/figure`. The runtime maps data,
   applies deterministic geometry/style/layout, renders PDF through Tectonic, derives PNG from the
   PDF, and validates the result.
5. Inspect the final page for scientific correctness. Runtime PASS does not replace human review of
   the scientific mapping.

For a canonical no-data example, use `axiomfig-render family/variant --output output/figure`.

## Progressive disclosure

- Registry: what templates exist.
- One family contract: accepted roles and required scientific semantics.
- Knowledge topic: which template suits an unresolved scientific intent.
- `references/style-contract.md`, `references/layout-contract.md`, or
  `references/validation-contract.md`: read only when changing the corresponding runtime layer.
- `styles/style.yaml`, `styles/fonts.yaml`, and `styles/colors.yaml`: read only when changing a
  visual default, font contract, or color semantics.

Do not read all builder source, contracts, knowledge topics, or Gallery files for a normal request.

## Non-negotiable boundary

The Agent may decide scientific intent, template, data mapping, geometry preset, typography mode,
and required scientific semantics. It must not emit figure dimensions, font sizes, line widths,
marker or bar geometry, tick geometry, legend/panel/colorbar coordinates, margins, subplot spacing,
or palette values. Any derivable visual property belongs to the deterministic runtime.

Use only registered templates when one exists. Do not silently ignore user data; Figure Intent
fails explicitly when a public template does not yet have an external-data adapter. Do not infer CI,
SE, SD, PI, a heatmap center, Mantel significance, censoring, or adjusted-p thresholds.

Filled geometry has configured face alpha with an opaque black `fill_edge`. Layouts own equal Outer
Panel Footprints; Primary and Auxiliary Axes remain contained. Panel labels anchor to the Primary
Axes frame upper-left. Legends are measured Figure-level ornaments. Registered layouts must pass
artist anatomy, collision, containment, font, PDF, and page-boundary validation.

## Development route

Keep `templates/index.yaml`, family contracts, explicit `BUILDERS`, and generated Gallery coverage
exactly synchronized. Builders own plot grammar, not visual tokens. Change a visual default only in
its canonical YAML source and thin consumer/helper. Add normal, boundary, and overflow/error tests;
never run combinatorial visual searches.

Rebuild Gallery from the registry with `axiomfig-gallery`. Completion requires 55 matching PDF/PNG
pairs in each of `gallery/sans/` and `gallery/serif/`, two Tectonic-native pairs under
`gallery/technical/latex/`, no orphan, embedded/subset non-Type-3 fonts, and final visual review.

Use only the verified LaTeX syntax in `references/latex-contract.md`. Matplotlib text is embedded
before the Tectonic wrapper; TeX-native Matplotlib labels and CJK/Japanese typography remain v1
limitations and must not be claimed.
