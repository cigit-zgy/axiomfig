# Agent execution protocol

This protocol owns the natural-language-to-Figure-Intent workflow. Figure Intent remains the only
formal boundary between an external Agent and the deterministic AxiomFig runtime.

## State machine

| State | Gate | Action |
|---|---|---|
| A. Inspect | Read the request and inspect the available file schema. | Identify the scientific objective, variables, data shape, and supplied results before asking about columns. |
| B. Resolve intent | Is the intended scientific relationship explicit? | If yes, form a candidate template. If no, read the knowledge index and only the routed topic. |
| C. Check sufficiency | Would missing information change scientific meaning or make the requested result unavailable? | Continue, ask one minimal clarification, or request upstream computation. |
| D. Select | Is there one suitable registered template? | Select exactly one template from `templates/index.yaml`; otherwise report unsupported scope. |
| E. Contract | Does its family contract declare direct or precomputed input? | Read that one contract and verify every required role and semantic field. |
| F. Normalize | Is the source already canonical CSV or JSON? | If not, extract it losslessly to a temporary CSV or JSON file without scientific transformation. |
| G. Specify | Are all required roles mapped? | Construct minimal Figure Intent; never include deterministic visual fields. |
| H. Execute | Does `axiomfig-intent` accept and render it? | Run the command, then runtime and artifact validation. Never bypass a failure. |
| I. Return | Are both artifacts validated? | Return PDF, PNG, template ID, input mode, and stated scientific semantics. |

## Clarification gates

Ask only when the answer materially changes scientific meaning or the executable input contract.
Examples include:

- uncertainty is requested but SD, SE, CI, or PI meaning is unknown;
- an ordination or biplot is requested but precomputed coordinates or loadings are absent;
- Mantel visualization is requested but precomputed Mantel `r` or `p_value` results are absent;
- survival visualization is requested but visualization-ready survival results are absent;
- several dataset fields plausibly map to one required role;
- the objective cannot distinguish a complete distribution from a summary comparison;
- a signed color scale is required but its scientifically meaningful center is unknown.

If the missing item is an analysis rather than a plotting role, request upstream computation. Do
not calculate PCA, PCoA, NMDS, Mantel tests, clustering, adjusted p-values, model diagnostics, or
survival models inside AxiomFig.

Do not ask for font size, line width, tick direction, legend position, marker size, bar width,
colorbar size, margins, registered geometry, or default typography. Do not ask the user to choose a
template when one canonical template follows unambiguously from the scientific intent, and do not
ask the user to write Figure Intent.

## Data inspection and normalization

Inspect headers, keys, shapes, and obvious units before requesting mappings. Names such as
`observed` and `predicted` in an explicit parity request are low-risk mappings; ambiguous names are
not permission to infer scientific roles.

The runtime accepts canonical CSV and JSON only. The Agent or an appropriate file tool may extract
Excel, Parquet, HDF5, NPZ, RDS, or other inputs into temporary CSV/JSON when the extraction is
lossless for the selected contract. Preserve values, labels, missingness, units, and ordering; do
not perform statistical analysis or silently aggregate during normalization.

## Execution result

Return the validated PDF and PNG plus minimal provenance: selected template, direct or precomputed
input mode, source file identity, and explicit scientific semantics. Distinguish user-supplied
results from deterministic visual defaults. If input, runtime, or artifact validation fails, report
the failure and required correction rather than presenting partial output as publication-ready.

## Installation boundary

AxiomFig intentionally has two installable concerns. A Skill checkout owns `SKILL.md`, references,
recommendation knowledge, examples, and Agent routing. The Python wheel owns the deterministic
runtime, CLI, registry, family contracts, builders, adapters, fonts, styles, and LaTeX resources.
Installing the wheel alone does not install the Agent Skill documents; an Agent needs the Skill
checkout as well as an available runtime. Do not duplicate all references into the wheel or make
the runtime depend on a repository root.
