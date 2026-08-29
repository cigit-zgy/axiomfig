# AxiomFig v1 sprint implementation plan

> Execute directly on `master` as explicitly authorized. Use targeted red/green tests during
> development, one full test run at final validation, coherent checkpoint pushes, and at most one
> visual repair pass.

## H1 — Freeze architecture and evidence

- [x] Verify local, origin, and GitHub baseline SHA and clean worktree.
- [x] Inventory package, template, Gallery, runtime, CLI, documentation, tests, and release files.
- [x] Review Rougier upstream/fork provenance and record implementation consequences only.
- [x] Record a 25-paper public caption-level journal census.
- [x] Freeze the 13-family, approximately 55-variant v1 target and migration map.
- [x] Run focused documentation checks; commit and push the H1 checkpoint.

## H2 — Extend core canonical templates

- [x] Add failing registry/contract/builder tests for the selected core variants.
- [x] Implement line `step` and `area`.
- [x] Implement scatter `bubble` and `hexbin`.
- [x] Implement bar `normalized_stacked` and `dot`.
- [x] Implement distribution `strip` and `raincloud`.
- [x] Implement heatmap `annotated`.
- [x] Run targeted registry/render tests and push a coherent core checkpoint.

## H3 — Add advanced scientific families

- [x] Add failing tests for advanced family presence, contracts, builders, and explicit semantics.
- [x] Extend estimation and diagnostics with coefficient, QQ, and feature importance.
- [x] Add ordination with four precomputed-coordinate templates.
- [x] Add correlation network while preserving Mantel as first-class.
- [x] Add one dependency-free Sankey, one quiver field, volcano/enrichment-dot, and Kaplan–Meier.
- [x] Rebuild the registry-derived sans/serif Gallery and validate exact coverage.
- [x] Perform the single visual review; no repair pass was required.
- [x] Commit and push the advanced-template/Gallery checkpoint.

## H4 — Implement the LLM-efficient boundary

- [ ] Add failing Figure Intent schema, role mapping, and invalid-input tests.
- [ ] Implement a frozen `FigureIntent`, YAML/JSON loader, compact data adapters, and intent CLI.
- [ ] Add explicit semantics for uncertainty, diverging centers, and significance where required.
- [ ] Create the progressive-disclosure knowledge index and concise topic references.
- [ ] Rewrite `SKILL.md` as a routing document and keep Registry, Contract, and Knowledge roles clear.
- [ ] Measure routing, registry, selected-contract, and representative-intent bytes/lines/tokens.
- [ ] Commit and push the Figure Intent/knowledge checkpoint.

## H5 — Evaluate, package, and automate

- [ ] Add 24 deterministic scientific request cases with expected routing and validity.
- [ ] Implement evaluation metrics for pass rate, render success, repeatability, and token cost.
- [ ] Audit wheel contents and add package-resource tests for registry, contracts, styles, fonts,
      attributions, LaTeX, and knowledge resources.
- [ ] Update v1 metadata and minimal CLI entry points; add contributor/security metadata.
- [ ] Add least-privilege, SHA-pinned CI for install, Ruff, tests, Skill validation, and render smoke.
- [ ] Perform an isolated wheel install from a clean temporary directory.
- [ ] Commit and push the packaging/evaluation/CI checkpoint.

## H6 — Validate the whole v1 product

- [ ] Exercise line, grouped scatter, bar, violin, correlation heatmap, parity, Mantel, ordination,
      forest, volcano, and mixed-panel flows from a fresh clone/equivalent checkout.
- [ ] Run Gallery validation, font validation, Tectonic probe, and PDF geometry checks.
- [ ] Run exactly one final `python -m pytest -q`, `ruff check .`, and `ruff format --check .`.
- [ ] Audit tracked files, generated junk, absolute local paths, secrets patterns, and remote contents.
- [ ] Reconcile README, SKILL, taxonomy, contracts, CLI, and documented limitations.
- [ ] Write the date/sequence-correct final agent report.
- [ ] Commit, push `master`, then verify local, origin, and GitHub SHA equality.
