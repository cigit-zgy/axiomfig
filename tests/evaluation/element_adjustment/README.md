# Element-adjustment A/B benchmark

This evaluation measures whether the progressively disclosed Scientific Figure Element Contracts
improve observable Agent decisions without exposing low-level plotting implementation.

- Baseline source: product commit `b55f1abe0dcc77edb86823a36c844a6a27ca1f10`.
- Treatment source: the frozen implementation commit produced by task `260831_chatgpt_01`.
- Corpus: 32 cases in `cases.yaml`, balanced across default preservation, axes/marks, ornaments,
  annotations, and adversarial low-level requests.
- Design: three fresh logical sessions per case and condition.
- Agent visibility: top-level `SKILL.md` initially; a fail-closed broker discloses one allowlisted
  normal Skill file per turn. Gold, scorer, tests, reports, Git metadata, and other-condition files
  are never copied.
- Output: one observable JSON decision; no chain-of-thought.

`runner.py` is provider-independent. It accepts an external Agent command, records reads and actual
Codex token totals when present, and writes raw evidence under `tmp/`. `scoring.py` validates and
scores decisions after the Agent context terminates. Live model calls are never part of CI.
