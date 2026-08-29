# Scientific LaTeX contract

Use these general-purpose packages and exact macros. Do not invent ad hoc unit, chemistry, math, or color syntax.

## Units: `siunitx`

```latex
\usepackage{siunitx}
\unit{\milli\gram\per\liter}
\qty{10}{\milli\gram\per\liter}
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
\setmathfont{Latin Modern Math}
\symup{Re}
\symbf{x}
```

Use `\setmathfont{...}` to select the OpenType math font, `\symup{...}` for upright mathematical symbols, and `\symbf{...}` for bold mathematical symbols. This package requires a Unicode math engine such as XeTeX or LuaTeX; the repository's standalone probe uses Tectonic where supported.

## Color: `xcolor`

```latex
\usepackage{xcolor}
\definecolor{AxiomBlue}{HTML}{4477AA}
\textcolor{AxiomBlue}{highlighted text}
{\color{AxiomBlue} scoped text}
```

Use `\definecolor{name}{HTML}{RRGGBB}` for a named canonical color, `\textcolor{name}{...}` for an inline span, and scoped `\color{name}` for a group. AxiomFig's generated definitions come from `styles/colors.yaml`.

## Current boundary

The stable figure path renders Matplotlib text into an intermediate PDF before Tectonic wraps that PDF. Therefore Tectonic cannot expand `\qty`, `\unit`, `\ce`, or other TeX macros placed inside Matplotlib labels. TeX-native Matplotlib text remains **DEFERRED**. The syntax above is valid for TeX-native documents; it is not evidence that plot labels support these macros.
