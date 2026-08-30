---
name: axiomfig
description: Create deterministic publication-oriented scientific PDF and PNG figures from compact Figure Intent, canonical templates, and explicit scientific data or precomputed results. Use for scientific plotting, multi-panel composition, Mantel and ordination graphics, Gallery generation, or AxiomFig validation.
---

# AxiomFig

## Normal Agent route

1. Read `src/axiomfig/templates/index.yaml` and select one registered template.
2. Read only `src/axiomfig/templates/<family>/contract.yaml` for accepted data roles and
   `input_mode`.
3. If scientific intent is ambiguous, read `references/template-knowledge/index.yaml`, then only
   its routed topic.
4. Write minimal Figure Intent using `references/figure-intent.md`.
5. Run `axiomfig-intent <intent.yaml> --data <data.csv|json> --output <stem>`.
6. Return the validated PDF and PNG. Report any validation failure instead of bypassing it.

Figure Intent should contain only template choice, data mapping, geometry, typography, and
scientifically meaningful semantics. Use precomputed results when the selected contract declares
`input_mode: precomputed`.

## Progressive disclosure

- Template availability: `src/axiomfig/templates/index.yaml`
- Selected input contract: one family `contract.yaml`
- Recommendation help: one routed file under `references/template-knowledge/`
- Figure Intent syntax: `references/figure-intent.md`
- Runtime changes only: `references/style-contract.md`, `layout-contract.md`, `validation.md`,
  `typography.md`, or `latex-contract.md`

Do not read all builders, contracts, references, or Gallery descriptions for a normal request.

## Non-negotiable boundary

- Use registered templates when one exists; all 55 public templates have executable data paths.
- Never expose deterministic fields such as font size, line width, tick length, legend position,
  bar width, panel offset, margins, or colorbar geometry in Figure Intent.
- Do not infer uncertainty type, diverging center, Mantel statistics, ordination, clustering,
  adjusted p-values, diagnostics, or survival models.
- Do not bypass deterministic layout, ornaments, typography, Tectonic finalization, or validation.
- Do not copy proprietary Arial, Times New Roman, SimSun, or Yu Gothic binaries into the project.
- CJK/Japanese canonical modes and TeX-native Matplotlib labels remain post-v1 work.

## Development route

Visual configuration lives only under `src/axiomfig/resources/styles/`. Builders own plot grammar;
family `adapter.py` files own input normalization; `style.py`, `layout.py`, `ornaments.py`,
`typography.py`, and `validation.py` own deterministic behavior.

Use targeted tests while editing. Before release, run Ruff, full pytest, registry-driven Gallery,
font and Tectonic probes, release Evaluation, isolated wheel installation, and clean-clone E2E.
