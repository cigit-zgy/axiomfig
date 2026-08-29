# AxiomFig Round 04 Advanced Visual Contract Design

## Scope

Round 04 extends the existing deterministic YAML-driven figure system without replacing the standard `src/axiomfig` package layout. The implementation keeps configuration in `styles/style.yaml`, `styles/fonts.yaml`, and `styles/colors.yaml`; Python remains a thin contract, layout, template, rendering, and validation layer.

The deliverable is a 36-case Matplotlib Gallery for both sans and serif modes, plus two Tectonic-native LaTeX figures. Every Gallery item is emitted as PDF and PNG. The round also updates the skill instructions, references, behavioral tests, and agent report.

## Architecture boundary

The existing modules retain distinct responsibilities:

- `config.py`: YAML loading and rcParams translation.
- `contracts.py`: deterministic numeric token calculations.
- `template_helpers.py`: artist and layout application helpers.
- `templates/`: four figure-family modules and their registry.
- `gallery.py`: canonical Gallery orchestration.
- `latex.py`: generated xcolor output and Tectonic-native rendering.
- `typography.py`, `rendering.py`, and `validation.py`: font discovery, artifact rendering, and artifact QA.

No module is merged solely to reduce file count. A module is removed only if repository evidence shows that it is a pure forwarding layer with no independent responsibility.

## Central visual tokens

`style.yaml` is the single source for the following new or revised values:

- Tick geometry uses `phi = 0.6180339887`, `minor_length_pt = 1.854`, and derives the open-axis `inout` major parameter as `2 * minor / phi`, approximately `6.0 pt`. Filled axes and colorbars reuse the same total major and minor lengths with outward direction.
- Panel labels use 11 pt bold text and fixed physical point offsets from the outer panel footprint.
- Legend top gap is `0.4667 pt`; legend fitting tests column counts from `N` down to `1` and accepts the first candidate fitting the figure boundary without panel-label collision.
- Bar widths use `single_width = 0.60` and `group_width = 0.76`; grouped series width is `group_width / series_count`.
- The redundant series cycle combines palette color, line pattern, and marker. The first four line patterns are solid, dash-dot, dotted, and long-dash. Reference and secondary lines default to dash-dot.
- Fill opacity is a face-only token. Filled faces receive RGBA alpha while black outlines remain fully opaque at the central `fill_edge` width.

## Typography

Sans mode uses Latin Modern Sans for ordinary text and Matplotlib math glyphs, including Greek letters, subscripts, superscripts, and expressions such as R squared. Serif mode continues to use XCharter and XCharter Math. Tectonic-native typography remains a separate output path and is not described as Matplotlib TeX-native text.

## Layout model

An outer panel footprint is the rectangular slot assigned by the top-level GridSpec. Ordinary data axes occupy the full slot. A heatmap panel with a colorbar subdivides its own outer slot into data, gap, and colorbar columns. The colorbar therefore never changes the size or placement of peer outer panels.

Panel labels are figure-level text positioned from the top-left of each outer footprint with physical point offsets. A nested data axis resolves its topmost SubplotSpec so the label anchor is independent of the inner colorbar subdivision. The Gallery exercises 2x2, 2x3, and 3x2 layouts.

## Statistical Gallery

The Matplotlib Gallery contains 36 deterministic examples per typography mode:

1. single line
2. multi-line
3. line with markers
4. line with confidence interval
5. scatter
6. grouped scatter
7. parity
8. regression scatter
9. vertical bar
10. grouped bar
11. horizontal bar
12. stacked bar
13. boxplot
14. violin
15. combined box and violin
16. histogram
17. density
18. ECDF
19. errorbar
20. forest plot
21. point interval
22. Bland-Altman
23. heatmap
24. correlation heatmap
25. deterministically preordered clustered heatmap
26. confusion matrix
27. ROC curve
28. precision-recall curve
29. calibration curve
30. residual diagnostics
31. Mantel-style relationship view
32. model evaluation
33. two-panel layout
34. four-panel layout
35. six-panel 2x3 layout
36. complex six-panel 3x2 layout with an internally allocated colorbar

The Mantel-style view combines a compact correlation matrix with a small number of relationship links. Link width and color encode correlation, while line style and annotation encode significance. It intentionally avoids a dense network.

## Palette contract

`colors.yaml` contains five eight-color Axiom palettes: Classic, Soft, Deep, Warm, and Cool. Tol palettes and grayscale remain available. Generated LaTeX colors include stable canonical default names and palette-qualified names, all derived from YAML rather than duplicated by hand.

## Tectonic-native output

`gallery/latex/01_scientific_typography` demonstrates `amsmath`, `unicode-math`, `siunitx`, `mhchem`, and `xcolor` through the bundled `axiomfig.sty`. `gallery/latex/02_palettes` compares the five Axiom palettes. Both are compiled by the real `tectonic` executable and converted to PNG for inspection.

## Verification strategy

Tests are divided into normal, boundary, and overflow/error behavior. Unit tests cover token derivation, alpha separation, exact bar widths, series ordering, legend column reduction, typography selection, and outer footprint geometry. Real PDF E2E remains limited to canonical Gallery generation. One deterministic visual review may produce one bounded repair pass, followed by final validation. If an Important issue remains after that repair, the round stops without recursive review.
