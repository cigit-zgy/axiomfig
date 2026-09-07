---
design_id: axiomfig-overview
title: AxiomFig system overview
status: active
role: design_authority
summary: >
  Defines the current whole-system architecture for deterministic scientific-figure routing, executable contracts, rendering, and evidence.
operational_projection:
  - AGENTS.md
  - SKILL.md
  - references/
  - src/axiomfig/
  - tests/
  - gallery/
---

# AxiomFig system overview

AxiomFig provides a deterministic-first scientific-figure layer for Agents and researchers. Scientific intent is resolved into a small registered grammar and explicit data roles; reusable visual decisions are owned by deterministic contracts/runtime rather than generated ad hoc by an LLM.

The current system has four architectural layers:

```text
Agent knowledge and routing
→ executable family/data contracts
→ deterministic rendering/validation runtime
→ Gallery and verification evidence
```

The Agent layer owns scientific meaning: figure family/grammar selection, scientific data roles, uncertainty meaning, thresholds, supplied precomputed results, and explicit semantic modifiers. The runtime owns reusable physical visual decisions such as typography, dimensions, bar/marker/stroke geometry, tick behavior, legend/colorbar placement, panel spacing, renderer measurement, and artifact validation.

Figure Intent is the sole formal Agent-to-runtime specification. It remains compact and contains only template identity, data mapping, geometry, typography, and scientifically meaningful semantics. Low-level backend parameters are outside this public boundary.

Current responsibility map:

```text
01_agent_runtime_boundary.md
    scientific/Agent responsibility vs deterministic runtime ownership

02_family_contracts.md
    registered figure grammars, tabular roles, family-specific semantics, compatibility

03_gallery_evidence.md
    formal Gallery and verification/evidence ownership
```

Global invariants:

- A scientific representation is selected before low-level appearance.
- Reusable visual decisions that can be deterministic are runtime-owned.
- Plotting does not invent statistical/scientific analysis, aggregate raw replicates, infer uncertainty type, or silently repair missing scientific values.
- One semantic rule has one durable owner; Markdown guides, executable contracts, implementation, and tests project the same accepted design without parallel truth.
- Compatibility identifiers may remain executable without being promoted as current Agent-recommended grammars.
- Verification may expose `DESIGN_GAP`, `PROJECTION_DRIFT`, `IMPLEMENTATION_DRIFT`, `TEST_DEFECT`, or environment/tool defects; only User + ChatGPT adjudication changes accepted design semantics.
