# AxiomFig LaTeX infrastructure

`axiomfig.sty` is a generic scientific package for Tectonic/XeTeX-compatible documents. It loads `xcolor`, `siunitx`, `mhchem`, `amsmath`, and `unicode-math`, selects XCharter text with XCharter Math, and imports canonical plus palette-qualified color definitions generated from `styles/colors.yaml`.

```latex
\documentclass{article}
\usepackage{axiomfig}
\begin{document}
\qty{10}{\milli\gram\per\litre}, \ce{NH4+}, $\mu_{\max}$,
\textcolor{AxiomBlue}{validated text}.
\end{document}
```

This package directly builds the two Tectonic-native references under `gallery/latex/`. It is not loaded into Matplotlib labels: AxiomFig first embeds plot text in the Matplotlib PDF and then uses Tectonic only to finalize that PDF container.
