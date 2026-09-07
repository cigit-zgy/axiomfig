---
design_id: gallery-evidence
title: Gallery and verification evidence
status: active
role: design_authority
summary: >
  Defines the formal Gallery as curated serif publication-reference output and separates it from verification, benchmarks, temporary artifacts, and historical evidence.
operational_projection:
  - gallery/
  - src/axiomfig/gallery.py
  - src/axiomfig/templates/*/gallery_cases.py
  - tests/test_gallery.py
  - tests/evaluation/
  - scripts/evaluate_release.py
---

# Gallery and verification evidence

## Formal Gallery

`gallery/` is the user-facing publication-reference surface. It is curated rather than a one-to-one dump of every executable identifier.

Current shape is family-first:

```text
gallery/<family>/<case>.pdf
gallery/<family>/<case>.png
```

Each formal case is generated through the real AxiomFig runtime and validated as a PDF/PNG pair. Formal Gallery typography is serif-only. Sans runtime support may remain available without duplicating the formal Gallery tree.

Compatibility-only template IDs need not appear in the formal Gallery. A core grammar may have several representative Gallery cases when orientation, uncertainty, sign, or another accepted semantic modifier materially changes what users need to inspect.

## Evidence separation

```text
gallery/
    curated current reference output

tests/ and tests/evaluation/
    executable conformance, falsification, repeatability and architecture evidence

tmp/<work-id>/
    disposable local renders, E2E output, worktrees and scratch state

reports/codex/
    FORMAL execution evidence only

00_archive/
    retained historical evidence only
```

Development benchmarks, capability audits, experimental alternative layouts, historical Gallery versions, and temporary contact sheets are not formal Gallery authority.

## Dynamic inventories

Public-template, recommended-template, builder/adapter and Gallery counts are derived from their current registries/specifications whenever feasible. Historical counts such as `55` or `61` are evidence from earlier states and must not become operational magic constants.

Structural repeatability gates cover the current public registry dynamically. Gallery verification covers the current curated Gallery specification dynamically. A change in one inventory does not imply the other has the same count.

## Verification purpose

Verification challenges the accepted design and implementation. It may demonstrate conformance or expose design/projection/implementation/test/environment defects, but tests and reports do not become a parallel design authority.

Release-grade evidence may include, when required by the active task:

- family/contract/registry parity and architecture constraints;
- bounded malformed-input behavior;
- scientific artist geometry and ordering invariants;
- external CSV/JSON Figure Intent paths;
- deterministic structural repeatability;
- formal Gallery rebuild and validation;
- clean wheel and clean checkout execution;
- Ruff, Mypy, pytest and dependency audit;
- exact-candidate GitHub CI;
- an independent falsification review for Level 2/3 risk.

## Design acceptance

The evidence architecture is coherent when the Gallery remains a small current reference surface, historical/development artifacts live outside it, inventories are not stale hard-coded truth, and a reviewer can distinguish accepted design, executable implementation, current reference output, temporary evidence, and historical evidence without ambiguity.
