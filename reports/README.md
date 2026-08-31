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

Do not use reports as runtime configuration, public Figure Intent fields, or sources of deterministic
visual defaults.
