# Typography contract

## Complete modes

`sans` is the default. Both modes use exact installed font files; missing files or internal-family mismatches raise `FontContractError` instead of silently falling back.

| Role | `sans` | `serif` |
|---|---|---|
| Latin text | Latin Modern Sans | XCharter |
| Matplotlib mathematics | Latin Modern Sans | XCharter Math |
| monospace auxiliary | Maple Mono | Maple Mono |

Font provenance, filenames, licenses, license URLs, copyright attribution, redistribution status, attribution files, and full license files live only in `styles/fonts.yaml`. The selected open Latin/math/mono binaries and their notices are bundled under `fonts/` and installed under `share/axiomfig/fonts/`.

Arial, Times New Roman, SimSun, and Yu Gothic are optional system-font records with `bundled: false`. They are not copied, redistributed, or selected by a canonical mode.

## Exact text variants

Latin Modern Sans and XCharter each resolve regular, bold, italic/oblique, and bold-italic files. Maple Mono and XCharter Math resolve the configured regular/variable file. Sans mode maps Matplotlib MathText regular, italic, and bold roles to Latin Modern Sans so `R^2`, Greek letters, subscripts, and superscripts remain visually sans. `discover_fonts(mode)` searches the repository/installed bundle before optional system roots, registers exact matches, and returns the resolved `text`, `math`, and `mono` roles without mutating global `rcParams`.

`apply_figure_typography()` assigns the selected Latin family and MathText mapping to ordinary Matplotlib text artists while preserving size, weight, and style. An artist with an explicit font file is preserved. This is distinct from the XCharter/XCharter Math Tectonic-native reference figures under `gallery/latex/`.

## Deferred scripts

Chinese and Japanese font work, multilingual segmentation, and heavy multilingual probes are intentionally deferred. The current canonical Gallery is English-only. If CJK text is requested, stop and report the unsupported boundary; do not guess a fallback family or claim the optional SimSun/Yu Gothic metadata as a validated typography path.

## License attribution

Latin Modern text/math use the GUST Font License. XCharter carries the Bitstream Charter free-font notice, while XCharter Math and Maple Mono use the SIL Open Font License 1.1. The repository retains the required attribution and full license text named by each bundled family. Arial and Times New Roman remain proprietary optional system fonts: their metadata is recorded with `bundled: false`, and their binaries are never copied or redistributed. SimSun and Yu Gothic are likewise metadata-only optional system fonts while CJK work is deferred.
