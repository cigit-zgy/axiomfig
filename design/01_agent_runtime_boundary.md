---
design_id: agent-runtime-boundary
title: Agent and deterministic runtime boundary
status: active
role: design_authority
summary: >
  Defines what scientific decisions the Agent may make, what Figure Intent may carry, and which visual decisions remain deterministic runtime-owned.
operational_projection:
  - SKILL.md
  - references/agent-protocol.md
  - references/figure-intent.md
  - references/element-contracts/
  - src/axiomfig/intent.py
---

# Agent and deterministic runtime boundary

## Purpose

AxiomFig externalizes scientific figure intent while removing routine visual micro-decisions from the Agent. The boundary must preserve scientific meaning without turning Figure Intent into a backend plotting API.

## Accepted design

The Agent may decide only information whose meaning depends on the scientific request or supplied data, including:

- registered figure grammar/template;
- mapping from supplied data fields to scientific roles;
- uncertainty meaning when explicitly supplied;
- scientifically meaningful thresholds, references, normalization modes, category/component/group roles, or other typed semantics owned by a registered grammar;
- supported geometry/typography choices already exposed by the project contract;
- supplied precomputed scientific results when the selected grammar requires them.

Figure Intent is the sole formal Agent-to-runtime boundary and remains limited to:

```text
template
data
geometry
typography
semantics
```

Reusable physical visual details are deterministic runtime concerns. Figure Intent must not expose backend-specific or low-level settings such as font size, line width, tick length, marker/bar size, physical gaps, legend coordinates, panel offsets, margins, colorbar dimensions, or arbitrary Matplotlib kwargs.

A low-level user request is translated to its semantic visual goal when a real supported semantic surface exists. The scientific representation/data mapping must remain unchanged unless the User explicitly requests a different scientific encoding.

## Trust and failure boundary

The Agent and runtime do not infer missing scientific meaning. In particular, they do not infer uncertainty type, statistical estimator, aggregation, domain normalization denominator, fitted analysis, or causal interpretation.

Malformed user input should fail through bounded AxiomFig domain errors at the public boundary where such a domain contract exists. Programmer defects must remain visible; broad exception swallowing is not accepted.

## Ownership

```text
SKILL.md / references
    Agent route and semantic guidance

Figure Intent parser
    public structured boundary and mapping validation

family contract + adapter
    grammar-specific scientific/data validation and deterministic normalization

builder + shared runtime
    deterministic scientific geometry and physical rendering
```

## Design acceptance

An unfamiliar Agent should be able to select a registered grammar and map data without inventing low-level visual values, while an unfamiliar runtime implementation should be able to reject malformed scientific input and render the accepted grammar deterministically from the same contract.
