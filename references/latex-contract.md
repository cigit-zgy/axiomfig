# Scientific LaTeX contract

Use these general-purpose packages and exact macros. Do not invent ad hoc unit, chemistry, math, or color syntax.

## Units: `siunitx`

```latex
\usepackage{siunitx}
\unit{\milli\gram\per\litre}
\qty{10}{\milli\gram\per\litre}
\num{1.25}
```

Use `\unit{...}` for a unit alone, `\qty{number}{unit}` for a quantity, and `\num{...}` for a formatted number. Use semantic unit macros inside the unit argument.

## Chemistry: `mhchem`

```latex
\usepackage[version=4]{mhchem}
\ce{NH4+}
\ce{NO3-}
\ce{2 NH4+ + 3 O2 -> 2 NO2- + 4 H+ + 2 H2O}
```

Use `\ce{...}` for chemical formulae and reactions, including stoichiometry, charges, states, and arrows.

## Mathematics: `amsmath`

```latex
\usepackage{amsmath}
\begin{equation}
  \mu = \mu_{\max}\frac{S}{K_S + S}
\end{equation}
\begin{align}
  \frac{dS}{dt} &= -r_S, \\
  \frac{dX}{dt} &= \operatorname{growth}(S, X).
\end{align}
```

Use `equation` for one displayed equation, `align` for aligned multi-line equations, `\text{...}` for ordinary words in math, and `\operatorname{...}` for named mathematical operators.

## Unicode mathematics: `unicode-math`

```latex
\usepackage{unicode-math}
\setmathfont{XCharter Math}
\symup{Re}
\symbf{x}
```

Use `\setmathfont{...}` to select the OpenType math font, `\symup{...}` for upright mathematical symbols, and `\symbf{...}` for bold mathematical symbols. This package requires a Unicode math engine such as XeTeX or LuaTeX; the repository's standalone probe uses Tectonic where supported.

## Color: `xcolor`

```latex
\usepackage{xcolor}
\definecolor{AxiomBlue}{HTML}{315A7D}
\textcolor{AxiomBlue}{highlighted text}
{\color{AxiomBlue} scoped text}
```

Use `\definecolor{name}{HTML}{RRGGBB}` for a named canonical color, `\textcolor{name}{...}` for an
inline span, and scoped `\color{name}` for a group. AxiomFig's generated definitions come from
`src/axiomfig/resources/styles/colors.yaml`.

## Current boundary

The only runtime LaTeX source is `src/axiomfig/resources/latex/`. Its `axiomfig.sty` loads `xcolor`, `siunitx`, `mhchem`, `amsmath`, and `unicode-math`, selects XCharter text with XCharter Math, and imports the generated canonical and palette-qualified colors. Installed callers locate both `.sty`/`.tex` resources with `importlib.resources`.

```latex
\documentclass{article}
\usepackage{axiomfig}
\begin{document}
\qty{10}{\milli\gram\per\litre}, \ce{NH4+}, $\mu_{\max}$,
\textcolor{AxiomBlue}{validated text}.
\end{document}
```

The Tectonic-native typography and palette probes in the evaluation suite are built through that
packaged resource; macros and palette-qualified colors are expanded by TeX there. They are not
formal Gallery entries.

The Matplotlib Gallery path renders plot text into an intermediate PDF before Tectonic wraps that PDF. Therefore Tectonic cannot expand `\qty`, `\unit`, `\ce`, or other TeX macros placed inside Matplotlib labels. TeX-native Matplotlib text remains **DEFERRED**. The syntax above is valid for TeX-native documents; it is not evidence that Matplotlib labels support these macros.
