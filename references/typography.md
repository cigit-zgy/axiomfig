# Typography contract

## Complete modes

A figure selects exactly one publication mode. `sans` is the default.

| Role | `sans` | `serif` |
|---|---|---|
| Latin text | Latin Modern Sans (`LMSans10`) | Latin Modern Roman (`LMRoman10`) |
| mathematics | Fira Math | Latin Modern Math |
| Simplified Chinese | Noto Sans CJK SC | Noto Serif CJK SC |
| Japanese | Noto Sans CJK JP | Noto Serif CJK JP |
| code/identifier auxiliary | Maple Mono | Maple Mono |

Titles, axis labels, tick labels, legend text/title, annotations, panel labels, math, Chinese, and Japanese must follow the selected mode. Maple Mono is available through `font_for_language("mono", mode=...)`; it is not a third publication family and must not be mixed into ordinary figure prose.

`discover_fonts(mode="sans" | "serif")` registers and verifies exact files and internal family names. Missing files, missing variants, wrong internal names, or fallback raise `FontContractError`. Discovery does not mutate global `rcParams`.

On macOS, discovery checks `~/Library/Fonts`, `/Library/Fonts`, `/System/Library/Fonts`, and `/opt/homebrew/share/fonts`. It resolves the Latin Modern variants, `FiraMath-Regular.otf`, exact Noto CJK OTF or collection faces, `latinmodern-math.otf`, and `MapleMono[wght].ttf`; it does not substitute a nearby family.

## Exact text variants

Latin text has four supported files per mode:

| Shape | `sans` file | `serif` file |
|---|---|---|
| regular | `lmsans10-regular.otf` | `lmroman10-regular.otf` |
| bold | `lmsans10-bold.otf` | `lmroman10-bold.otf` |
| italic/oblique | `lmsans10-oblique.otf` | `lmroman10-italic.otf` |
| bold italic/oblique | `lmsans10-boldoblique.otf` | `lmroman10-bolditalic.otf` |

Regular weight aliases are `None`, `normal`, `regular`, `book`, and `400`. Bold aliases are `bold`, `semibold`, `demibold`, `demi`, `extrabold`, `ultrabold`, `heavy`, and `black`; spaces and hyphens are ignored during normalization. A finite, integral numeric weight in Matplotlib's `0..1000` range maps only as follows: exactly `400` is regular, and `600..1000` is bold. Booleans, non-integral/non-finite values, out-of-range values, and every remaining numeric or string weight hard-fail because no exact file exists. `italic` and `oblique` select the mode's exact slanted file; combining either with a bold weight selects the exact bold-slanted file.

Chinese and Japanese contracts currently expose regular files only. `font_for_language()` and `add_language_text()` accept only regular weight (`None`, `normal`, `regular`, or numeric `400`) and normal style (`None` or `normal`) for `zh`/`ja`; every other weight or style hard-fails instead of silently using Regular. `add_language_text()` accepts `weight`/`fontweight` and `style`/`fontstyle` aliases, and rejects conflicting duplicate aliases.

```bash
python scripts/check_fonts.py
python -c "from axiomfig.typography import discover_fonts; discover_fonts(mode='serif')"
```

The first command checks the default sans mode; the second explicitly checks serif. The gallery build checks both modes again.

## Ordinary artist pass

`render_figure(..., typography=mode)` calls `apply_figure_typography()` immediately before saving the Matplotlib PDF. It visits figure text, all three axes-title positions, x/y labels, major/minor tick labels, axes annotations, legend titles, and legend labels. Artists without an explicit font file receive the exact Latin, Chinese, or Japanese file for the selected mode while preserving their existing size, weight, style, and stretch. Every such artist, including a pure-math artist with no plain-script run, receives the selected custom math family.

This pass covers ordinary single-script `Text` artists; it is not a general text shaping engine. Latin is `en`, kana marks a string as `ja`, and otherwise Han-only text is treated as `zh`. An artist with an explicitly assigned font file is preserved, so shared Han-only Japanese text must be assigned explicitly.

## CJK and mixed-script segmentation

Shared Han glyphs require an explicit regional choice. Use `font_for_language("zh", mode=...)` or `font_for_language("ja", mode=...)`, or create the run through `add_language_text(axis, x, y, text, language, mode=..., **kwargs)`.

A single ordinary artist may contain one plain-script family plus `$...$` math. Plain Latin and CJK in the same artist are rejected with `FontContractError`; do not depend on fallback order. Segment such content into separate adjacent artists/runs and call `add_language_text` for each `en`, `zh`, or `ja` run using the same mode. The helper assigns one font to one run; it does not parse or expand a mixed string automatically.

`src/axiomfig/resources/templates/multilingual.py` is the verified pattern. It emits separate English, Simplified Chinese, and Japanese artists, plus a math artist, and is rendered in both modes as gallery `07_multilingual` and `09_serif`.

## Verification boundary

Font discovery verifies source files and internal family names before rendering. The generic figure validator parses `pdffonts` rows but enforces only embedded/subset fonts and absence of Type 3; it does not universally enforce `uni=yes` or exact family identity. Targeted gallery E2E tests inspect exact family names for the serif and style-contract acceptance figures and extract required multilingual content. The standalone LaTeX probe separately requires Unicode mappings. Regional CJK glyph shape and unintended visual family mixing remain a human inspection of the rasterized PDF, not a generic `pdffonts` PASS.
