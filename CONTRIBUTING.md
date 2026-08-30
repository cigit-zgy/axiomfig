# Contributing

Open an issue before a large taxonomy, Figure Intent, or visual-contract change. Keep scientific
computation separate from visualization, preserve deterministic defaults, and avoid cosmetic-only
templates. `SKILL.md` stays a short router; Agent protocol and recommendation knowledge stay in
`references/`; Figure Intent remains the sole LLM-to-runtime boundary; family contracts own
scientific I/O; deterministic visual decisions stay in the runtime contracts.

Install development dependencies and run focused tests while editing:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
python -m pytest -q -m "not e2e"
python scripts/validate_skill.py
```

## Release readiness

A release candidate must be scope-frozen before version metadata or tags change. Deferred or
partially operable capabilities must remain explicitly documented rather than being completed by a
last-minute public-schema expansion. In particular, canonical `layouts/*` fixtures do not imply a
user-data multi-panel Figure Intent path, and a benchmark specification does not imply measured LLM
routing accuracy.

Before proposing a release-affecting change, require all of the following from one candidate SHA:

- Ruff, full pytest, Skill validation, Agent-protocol structural validation, and release Evaluation
  pass without weakened gates;
- the registry-driven Gallery is rebuilt and validated, affected figures are visually inspected,
  and public-template/Gallery counts change only with an explicit scope decision;
- bundled-font, Tectonic, PDF, isolated-wheel, and clean-clone CLI E2E checks pass on the candidate;
- Python 3.11 and 3.12 CI pass for the same candidate SHA;
- `CHANGELOG.md`, README installation guidance, and package version agree with the release scope;
- immutable historical tags are never moved or recreated.

Only after those gates pass and release authorization is explicit should `pyproject.toml` be changed
from the previous released version, `Unreleased` notes be finalized under the new version, and a new
tag/release be created. Do not use a version bump itself as evidence of readiness.

Do not commit caches, build directories, temporary renders, commercial fonts, private data, or
machine-specific paths.
