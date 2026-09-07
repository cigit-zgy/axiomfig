# AxiomFig context

## Identity

AxiomFig is a deterministic-first scientific-figure Skill and Python runtime. It owns Agent-facing scientific figure routing, executable plotting contracts, deterministic rendering, validation, and curated publication-reference artifacts.

## Authority

```text
explicit User instruction
→ design/                                   current accepted project design
→ SKILL.md + references/                    operational Agent projection
→ src/axiomfig/templates/*/contract.yaml    executable family input contracts
→ src/axiomfig/resources/                   deterministic visual defaults
→ src/axiomfig/                             implementation
→ tests/                                    conformance and design-probing evidence
→ gallery/                                  curated validated reference output
```

`reports/concept/` is chronological design exploration/history only. `reports/handoff/` is conversation context only. Neither overrides current `design/` or an active committed task.

Global collaboration authority is `cigit-zgy/agent-collaboration`. For repository tasks, resolve the current/pinned revision through its `SKILL.md`; delegated Codex tasks pin the exact collaboration commit.

## Ownership

```text
design/                one current living design set
SKILL.md                shortest normal Agent route
references/             scientific/routing/element contracts for progressive disclosure
src/axiomfig/templates/ family registry, contracts, adapters, builders, Gallery case definitions
src/axiomfig/resources/ executable typography/style/color/LaTeX resources
gallery/                serif-only curated publication-reference PDF/PNG pairs
examples/               executable external-data examples
reports/chatgpt/        durable LOCAL-QUICK and FORMAL Codex task specifications
reports/codex/          FORMAL Codex execution reports only
reports/concept/        chronological design history/input
reports/handoff/        conversation migration snapshots
tests/                  verification, falsification, architecture and release evidence
00_archive/             historical retained material only
tmp/                    project-local Agent ephemeral state; never authority
```

## Workflow

Normal figure execution:

```text
AGENTS.md
→ SKILL.md
→ routed scientific/reference owner
→ one registered template + one family contract
→ Figure Intent
→ deterministic runtime
→ validated PDF/PNG
```

Maintained Skill behavior changes follow:

```text
User + ChatGPT adjudication
→ design/ current authority
→ SKILL.md / references projection
→ implementation
→ design-probing tests
```

A discovered design gap returns upstream for adjudication; code and tests do not silently invent new project semantics.

## Runtime and tooling

The supported Python/tooling contract is declared by `pyproject.toml`, repository CI, and the executable tests. Common release verification includes Ruff, Mypy, pytest, Skill validation, registry/release evaluation, structural repeatability, isolated wheel installation, clean-checkout E2E, Gallery validation, and project-scoped dependency audit when the active task requires them.

Project-specific shared coding-Skill additions: none. Use the collaboration-pinned shared coding profile for activated cross-Agent coding Skills.

## Human / trust checkpoints

The User + ChatGPT own scientific/product/design semantics and final acceptance. Codex supplies local implementation and evidence and never self-accepts. Release/tag/publication authorization remains a User checkpoint unless explicitly delegated.

## Hard invariants

- `design/` contains one current accepted design set only.
- Figure Intent is the single formal Agent-to-runtime boundary; reusable physical visual decisions remain deterministic runtime-owned values.
- Plotting never silently invents scientific analysis, uncertainty meaning, aggregation, normalization semantics, or missing data.
- Every Codex repository task is durably specified under `reports/chatgpt/`; chat carries only the immutable locator.
- LOCAL-QUICK creates no `reports/codex/` artifact; FORMAL does.
- Repository-changing Codex work uses the collaboration remote-synchronization handshake and preserves pre-existing User state.
