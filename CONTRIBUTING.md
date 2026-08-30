# Contributing

Open an issue before a large taxonomy or visual-contract change. Keep scientific computation
separate from visualization, preserve deterministic defaults, and avoid cosmetic-only templates.

Install development dependencies and run focused tests while editing:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
python -m pytest -q -m "not e2e"
python scripts/validate_skill.py
```

Before proposing a release-affecting change, run the full suite with Tectonic and Poppler installed,
rebuild Gallery with `axiomfig-gallery gallery`, validate it with `axiomfig-validate gallery`, run
`python scripts/evaluate_release.py --output tmp/release-evaluation`, and visually inspect the
output.
Do not commit caches, build directories, temporary renders, commercial fonts, private data, or
machine-specific paths.
