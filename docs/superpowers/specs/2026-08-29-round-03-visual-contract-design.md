# AxiomFig Round 03 Visual Contract Design

## Status

This design records the user-approved Round 03 contract. It is intentionally limited to deterministic visual defaults, English-only canonical templates, open Latin/math typography, generic scientific LaTeX infrastructure, and one bounded review cycle.

## Architecture

The three YAML files remain the only visual configuration roots. `style.yaml` owns physical geometry, margins, strokes, ticks, legends, panel labels, and plot defaults; `fonts.yaml` owns exact font assets and redistribution metadata; `colors.yaml` owns all palette values. Python remains a thin validator/translator plus reusable artist helpers. Template modules own scientific data and semantic composition but never duplicate visual constants.

The public template registry expands from six to twenty canonical names while staying grouped into four family modules: curves and model comparison, distributions and bars, surfaces, and multi-panel composition. Export applies one centralized output-margin policy, writes a Matplotlib vector PDF, finalizes it with Tectonic, and rasterizes the final PDF through Poppler.

## Typography and licensing

Sans remains Latin Modern Sans with Latin Modern Math. Serif changes to XCharter text plus XCharter Math. Maple Mono remains the monospace role. These open fonts are bundled under `fonts/` with exact upstream license and attribution files. XCharter text uses the Bitstream free-font grant reproduced by the upstream package; XCharter Math and Maple Mono use SIL OFL 1.1; Latin Modern uses the GUST Font License.

Arial and Times New Roman remain optional system-only proprietary records. Microsoft explicitly disallows general redistribution of Windows fonts outside permitted document embedding, so no commercial font file enters the repository. SimSun and Yu Gothic remain optional system metadata; CJK/Japanese behavior is deferred.

## Visual contracts

Bar and violin use no categorical tick marks while their numeric axes use the open policy: major `inout`, minor `in`. Heatmap/image and colorbars use outward ticks. The `0.8 pt` main stroke and `0.6 pt` filled edge stay central. Scatter remains alpha `0.55` with black `0.6 pt` edges and a YAML-owned marker area.

Legends remain frameless, right-spine aligned, outside top-right, single-row first, and absent for one series. The vertical gap becomes `0.7 pt`. Multi-panel labels stay `(a)` through `(d)`, bold `10 pt`, at `x=-2 pt`, `y=+2 pt` relative to each axes box.

Output margins are centralized under `style.output`. `tight` is the default and targets `1.5 pt` visible padding without cropping artists or changing the requested physical page geometry. `normal` preserves configured base subplot margins. `custom` uses an explicit point padding value. Templates do not call per-figure output-cropping APIs.

## Multi-panel layout

The canonical `20_multi_panel` is a 2x2 grid with line-plus-CI, grouped bar, scatter, and heatmap panels. The four ordinary axes boxes are exactly equal. The colorbar is a dedicated axes placed immediately to the right of panel (d), with the same vertical bounds and without changing panel (d). Consequently panels (b) and (d) share the same left edge and all four ordinary panels retain symmetry.

## Color and LaTeX

`colors.yaml` defines `tol_bright`, `tol_muted`, `axiom_classic`, `axiom_soft`, and `grayscale`. Paul Tol values are copied from his current official scheme page. The Axiom palettes provide stable `AxiomBlue`, `AxiomCyan`, `AxiomGreen`, `AxiomYellow`, `AxiomOrange`, `AxiomRed`, `AxiomPurple`, and `AxiomGrey` tokens. Generated xcolor definitions always come from the selected canonical Axiom palette.

The repository-level `latex/axiomfig.sty` loads only `xcolor`, `siunitx`, `mhchem`, `amsmath`, and `unicode-math`; it defines no domain macros. Documentation calls the wrapper stage “Tectonic finalization” and states that plot text is already embedded by Matplotlib.

## Validation and stopping rule

Behavioral tests use only normal, boundary, and overflow/error cases. Real PDF E2E is limited to the canonical Gallery. Both typography directories must contain the same twenty PDF/PNG pairs. Representative Tectonic checks cover sans/serif single-panel and multi-panel outputs. After one implementation/build pass, one review is allowed; one repair pass follows only when required. Any remaining Important issue stops release and is reported without recursive reviewer/fixer loops.
