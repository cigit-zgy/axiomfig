# Typography contract

## Complete modes

`sans` is the default. Both modes use exact installed font files; missing files or internal-family mismatches raise `FontContractError` instead of silently falling back.

| Role | `sans` | `serif` |
|---|---|---|
| Latin text | Latin Modern Sans | Latin Modern Roman |
| mathematics | Latin Modern Math | Latin Modern Math |
| monospace auxiliary | Maple Mono | Maple Mono |

Font provenance, filenames, licenses, license URLs, copyright attribution, and redistribution status live only in `styles/fonts.yaml`. No font binary is bundled in this repository.

Arial, Times New Roman, SimSun, and Yu Gothic are optional system-font records with `bundled: false`. They are not copied, redistributed, or selected by a canonical mode.

## Exact text variants

Latin Modern Sans and Roman each resolve regular, bold, italic/oblique, and bold-italic files. Maple Mono and Latin Modern Math resolve the configured regular/variable file. `discover_fonts(mode)` searches the roots declared in `fonts.yaml`, registers exact matches, and returns the resolved `text`, `math`, and `mono` roles without mutating global `rcParams`.

`apply_figure_typography()` assigns the selected Latin family and math font to ordinary Matplotlib text artists while preserving size, weight, and style. An artist with an explicit font file is preserved.

## Deferred scripts

Chinese and Japanese font work, multilingual segmentation, and heavy multilingual probes are intentionally deferred. The current canonical Gallery is English-only. If CJK text is requested, stop and report the unsupported boundary; do not guess a fallback family or claim the optional SimSun/Yu Gothic metadata as a validated typography path.

## License attribution

Latin Modern text and math use the GUST Font License. Maple Mono uses the SIL Open Font License 1.1. The exact primary source and license links are stored alongside each family in `styles/fonts.yaml`; because `bundled: false`, the repository records attribution without redistributing binaries.
