# Reports

Reports are provenance and evaluation evidence. They are not part of the AxiomFig runtime or Agent
knowledge surface unless a task explicitly links to one.

```text
reports/
├── chatgpt/      # immutable task specifications issued to implementation Agents
├── agent/        # implementation, audit, and verification reports
└── discussion/   # architecture decisions and discussion records
```

Naming is independent by category:

```text
YYMMDD_chatgpt_NN.md
YYMMDD_agent_NN.md
YYMMDD_discussion_NN.md
```

A formal Agent task should record the task source path and pinned task commit SHA. An Agent report
should record task ID, task source SHA, baseline SHA, implementation SHA, and final SHA so the chain
remains traceable:

```text
ChatGPT task specification
→ implementation commits
→ Agent report
→ final repository state
```

## Independent acceptance rule

An Agent/Codex `PASS` or `VERDICT: PASS` is a claim to be audited, not acceptance evidence by itself.
Any reviewer accepting a completed Agent task must independently inspect the repository rather than
summarize the Agent report.

At minimum, independently verify:

1. the current default-branch SHA and task provenance;
2. the baseline-to-implementation diff and the actual production code changed;
3. the relevant tests and whether they exercise the claimed behavior rather than only assert file
   existence or prose;
4. GitHub Actions run/job status and, for important gates, the actual job logs;
5. release artifacts, generated evidence, or executable E2E results when the claim depends on them;
6. consistency between the Agent's reported counts/results and independently observable evidence;
7. whether supposedly independent audits or local-only checks have a separate traceable artifact.

If a claim is supported only by an Agent report or uncommitted/local output that cannot be
independently inspected, label it `REPORTED, NOT INDEPENDENTLY VERIFIED`; do not silently promote it
to verified evidence. Any mismatch between the report and GitHub/CI evidence must be stated
explicitly. The reviewer should actively try to falsify the reported PASS before issuing an
acceptance verdict.

Do not use reports as runtime configuration, public Figure Intent fields, or sources of deterministic
visual defaults.
