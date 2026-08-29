# Task 1 report: environment and execution contract

## Completed scope

- Replaced every required `uv run` invocation in `README.md`, `SKILL.md`, `references/rendering-validation.md`, and `references/typography.md` with direct `python` commands. The test and lint commands in `README.md` now use `python -m pytest` and `ruff`.
- Replaced the `uv sync --dev` setup instruction with `python -m pip install -e ".[dev]"`, retaining standard `pyproject.toml` metadata and avoiding any dependency on a particular environment manager.
- Deleted `uv.lock` as required. No package metadata or package architecture was changed.

## Environment verification

All commands below used `PATH=/Users/wenv/miniforge3/bin:$PATH` and the existing conda base Python 3.11.16. The pre-existing base lacked `pypdf` and `ruff`; installed only `pypdf 6.16.2` and `ruff 0.16.5` into that base. Tectonic and Poppler (`pdftoppm`, `pdffonts`) were already available from Homebrew.

The initial suite found five failures caused by the required `Noto Sans CJK SC` font being absent. Installed the missing Homebrew cask `font-noto-sans-cjk-sc`, refreshed fontconfig, and forced a Matplotlib font-cache rebuild by fresh discovery. The exact font contract then resolved for Latin, math, Chinese, and Japanese roles.

## Verification evidence

| Command or check | Result |
| --- | --- |
| `python scripts/check_fonts.py` | PASS: all four exact font roles resolved |
| `python scripts/compose_style.py ...` | PASS: composed deterministic style written to isolated `tmp/task1-contract/` |
| `python scripts/render.py line-ci ...` | PASS: Tectonic PDF and PNG created at 90.00 x 67.50 mm |
| `python scripts/validate.py ...` | PASS: single render and isolated eight-pair gallery validated |
| `python scripts/build_gallery.py --gallery ... --work-root ...` | PASS: all eight PDF/PNG pairs rebuilt in isolated `tmp/task1-contract/` |
| `python -m pytest` | PASS: 47 passed |
| `ruff check .` | PASS: all checks passed |
| `ruff format --check .` | PASS: 37 files already formatted |
| documentation scan | PASS: no `uv run` or `uv sync` remains in the four task documentation files |
| `git diff --check` | PASS: no whitespace errors |

The initial baseline after adding missing Python dependencies was 42 passed and 5 failed, all due to the missing required Chinese font. The final baseline is 47 passed.

## Self-review and boundaries

Reviewed the staged scope against the task brief: only the four specified documentation files and `uv.lock` are product changes. The repository's pre-existing untracked `docs/` directory was not inspected, modified, staged, or committed. Verification artifacts are confined to ignored `tmp/task1-contract/`.

## Concern

The Homebrew aggregate `font-noto-sans-cjk` cask was already installed but exposed only the Japanese TTC face to the fresh Matplotlib cache in this environment; the separate `font-noto-sans-cjk-sc` cask was needed for exact Chinese-family discovery. No source-code workaround was added.
