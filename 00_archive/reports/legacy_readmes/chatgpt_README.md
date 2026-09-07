# ChatGPT task specifications

This directory stores formal task specifications issued by ChatGPT for Agent/Codex execution.

## Naming

Use:

```text
YYMMDD_chatgpt_NN.md
```

Rules:

- Use the actual issue date.
- `NN` is a two-digit daily sequence starting at `01`.
- Before creating a task, scan `reports/chatgpt/` and increment the highest sequence for that date.
- `chatgpt`, `agent`, and `discussion` sequences are independent.
- Do not use suffixes such as `_final`, `_v2`, `_new`, or similar.

## Task lifecycle

1. A complete task specification is written here.
2. The task file is committed and pushed before execution begins.
3. Agent/Codex should read the task through a commit-pinned GitHub URL whenever possible.
4. The committed task version is immutable as an issued specification.
5. A material revision creates a new `YYMMDD_chatgpt_NN.md` file and declares `Supersedes: <task-id>` in metadata; do not silently overwrite an issued task.
6. The resulting Agent report is written independently under `reports/agent/YYMMDD_agent_NN.md`.

## Required task metadata

Each formal task should record at least:

- Task ID
- Issued date
- Repository
- Branch
- Expected baseline SHA or baseline policy
- Status
- `Supersedes` when applicable

## Traceability

Agent reports should record:

- Task ID
- Task source path
- Task source commit SHA
- Baseline SHA
- Implementation SHA
- Final SHA

The intended provenance chain is:

```text
ChatGPT task specification
        ↓
implementation / evaluation commits
        ↓
Agent report
        ↓
final repository state
```

## Scope

Use this directory for independently executable development work such as repository implementation, refactoring, systematic audits, benchmarks, release work, or substantial test plans. Ordinary short discussion does not require a task file.
