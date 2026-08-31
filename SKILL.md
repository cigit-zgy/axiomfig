---
name: axiomfig
description: Create deterministic publication-oriented scientific PDF and PNG figures from compact Figure Intent, canonical templates, and explicit scientific data or precomputed results. Use for scientific plotting, Mantel and ordination graphics, canonical layout fixtures, Gallery generation, or AxiomFig validation.
---

# AxiomFig

## Normal Agent route

1. Inspect the request and available data schema. Follow the decision gates in
   `references/agent-protocol.md`.
2. Resolve scientific intent before final template selection. If it is ambiguous, read
   `references/template-knowledge/index.yaml`, then only its routed topic. Ask only for missing
   scientific meaning that would materially change the result.
3. Read `src/axiomfig/templates/index.yaml`, select exactly one registered template, and read only
   `src/axiomfig/templates/<family>/contract.yaml`.
4. Confirm whether the contract requires direct data or precomputed scientific results. Never
   invent missing analysis or scientific semantics.
5. Normalize supported user files losslessly to CSV or JSON when needed, then write minimal Figure
   Intent using `references/figure-intent.md`.
6. Run `axiomfig-intent <intent.yaml> --data <data.csv|json> --output <stem>`.
7. Return the validated PDF and PNG with minimal provenance. Report validation failure instead of
   bypassing it.

Figure Intent contains only template choice, data mapping, geometry, typography, and scientifically
meaningful semantics. The deterministic runtime owns every reusable visual decision.

## Progressive disclosure

- Execution and clarification gates: `references/agent-protocol.md`
- Recommendation routing: `references/template-knowledge/index.yaml`
- Template discovery: `src/axiomfig/templates/index.yaml`
- Selected input contract: one family `contract.yaml`
- Figure Intent syntax: `references/figure-intent.md`
- Advanced Mantel customization only: `references/mantel.md`
- Non-default visual or positional request only: read `references/element-contracts/index.md`, then
  at most one routed element topic when possible. Use only a real `AVAILABLE` surface; for
  `INTERNAL_ONLY`, `PLANNED`, or `NOT_SUPPORTED`, do not invent Figure Intent fields or low-level
  plotting parameters. Keep deterministic defaults for every unrelated element.
- Runtime changes only: `references/style-contract.md`, `layout-contract.md`, `validation.md`,
  `typography.md`, or `latex-contract.md`

Do not read all builders, contracts, references, or Gallery descriptions for a normal request.

## Non-negotiable boundary

- Use registered templates when one exists; all 55 public templates have executable data paths.
- Never expose font size, line width, tick length, legend position, marker or bar size, panel offset,
  margins, or colorbar geometry in Figure Intent.
- Do not infer uncertainty type, diverging center, Mantel statistics, ordination, clustering,
  adjusted p-values, diagnostics, or survival models.
- Do not ask users for deterministic visual defaults or require them to author Figure Intent.
- Do not bypass deterministic layout, ornaments, typography, Tectonic finalization, or validation.
## Development route

Visual configuration lives only under `src/axiomfig/resources/styles/`. Builders own plot grammar;
family `adapter.py` files own input normalization; `style.py`, `layout.py`, `ornaments.py`,
`typography.py`, and `validation.py` own deterministic behavior.

Use targeted tests while editing. Before release, run Ruff, full pytest, Skill validation, release
Evaluation, registry-driven Gallery checks, isolated wheel installation, and clean-clone E2E.
