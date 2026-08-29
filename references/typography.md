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

`templates/multilingual.py` is the verified pattern. It emits separate English, Simplified Chinese, and Japanese artists, plus a math artist, and is rendered in both modes as gallery `07_multilingual` and `09_serif`.

## Verification boundary

Text extraction checks required content, `pdffonts` checks embedded/subset non-Type-3 fonts and Unicode mappings, and rendering rejects missing-glyph warnings. Regional glyph shape and unintended family mixing still require visual inspection of the PDF rasterization.
