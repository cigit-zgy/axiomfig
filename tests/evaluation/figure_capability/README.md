# Complex figure capability audit

This evaluation surface asks what the current AxiomFig Skill and Matplotlib core can express for
twenty deliberately complex, visualization-ready scientific figures. It is not a public template
registry or a source of plotting behavior.

`cases.yaml` freezes the researcher request, supplied schema, authoritative source, expected figure
anatomy, structural relations, physical geometry, and reference PDF for each case. It intentionally
does not encode an expected Skill action. Each Skill decision is obtained through a fresh
progressive-disclosure Agent context and recorded as evidence rather than treated as gold.

The manifest's `source_fixture` identifiers name deterministic, visualization-ready inputs built by
`scripts/build_figure_capability_audit.py` and the preserved round-one fixture module. Upstream
analyses (clustering, survival estimation, model diagnostics, ordination, Mantel tests, enrichment,
and association statistics) are represented only by frozen results. The native renderer uses
Matplotlib plotting and layout primitives; numerical libraries may prepare deterministic fixture
geometry but do not own plotting or placement.

Canonical audit evidence is under `tests/evaluation/figure_capability/artifacts/`. Temporary PNG previews, raw Agent
logs, metrics, repeatability signatures, and the live attempt ledger remain under
`tmp/figure-capability-audit/`.
