# Agent decision evaluation

`agent_protocol_cases.yaml` is a gold specification for observable scientific-routing decisions.
Its structural validator checks registry/contract consistency, action coverage, language coverage,
and forbidden visual fields. It does not execute an LLM and does not measure model accuracy.

Future isolated Agent runs may emit one JSON object per line:

```json
{"id":"R11-scatter-parity","action":"render","template":"scatter.parity","input_mode":"direct","mapped_roles":["observed","predicted"],"scientific_inferences":[]}
```

Only observable decisions belong in this file. Do not include chain-of-thought or private model
reasoning. Depending on the action, a record may also provide `scientific_semantics`,
`clarification_reason`, `upstream_requirement`, or a minimal `figure_intent`.

Score predictions without a model call:

```bash
python -m tests.evaluation.agent_scoring predictions.jsonl
```

The scorer reports action, render-template, family, input-mode, clarification,
require-precomputed, unsupported-scope, valid-Figure-Intent, and scientific-boundary-safety metrics
separately. Rendering when upstream analysis or clarification is required, or asserting a gold
forbidden scientific inference, fails the safety metric even if the selected template looks
plausible.

Run selected cases through an externally supplied, one-shot Agent command:

```bash
python -m tests.evaluation.blind_agent \
  --case-id S03-zh-parity-compatible \
  --output tmp/agent-benchmark/predictions.jsonl \
  --workspace tmp/agent-benchmark/run \
  -- <isolated-agent-command>
```

The runner copies only the normal Agent-facing Skill surface, strips gold metadata and case IDs
from prompts, launches one fresh process per case, and stores only observable JSON decisions. The
external command remains responsible for disabling repository, network, memory, and prior-session
access. Do not call a benchmark blind unless those controls have been verified independently.
