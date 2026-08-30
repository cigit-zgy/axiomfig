# Deterministic layout and ornament contract

## 1. Anatomy

| Term | Contract |
|---|---|
| Figure | Fixed physical output boundary |
| Outer Panel Footprint | Equal top-level GridSpec slot in a regular grid |
| Primary Visual Area | Scientific data region; it has first claim on panel area |
| Primary Axes | Axes that owns the Primary Visual Area and intrinsic data decorations |
| Auxiliary Axes | Panel-owned support axes such as a Colorbar |
| Ornament Strip | Measured right, bottom, top, or left reservation outside the Primary Visual Area |
| Panel-owned Artist | Local annotation, value/direct label, or other artist assigned to one panel |
| Figure-level Ornament | Legend or other content owned by the Figure rather than one panel |

Every registered panel has one Primary Axes. A heatmap adds its Colorbar as Auxiliary Axes. The
complete primary, auxiliary, and local content bbox plus the panel-label gutter must remain inside
the footprint. Primary scientific content has first claim on panel area: ornaments receive only
their measured strip plus contract-owned physical gaps and containment padding.

## 2. Physical solve and Primary Visual Area protection

The engine converts the fixed page size to points using `72 pt = 1 inch` and `25.4 mm = 1 inch`.
It creates equal GridSpec cells using YAML-owned physical horizontal and vertical gaps. Output
padding bounds the equal footprints; the measured panel-label gutter is reserved inside each
footprint during the solve.

After templates add data and request ornaments, the engine performs one measurement pass. It
measures axis-decoration overhangs, panel-label height, the first collision-free `N..1` legend
candidate, and Colorbar text/tick overhang at its final physical width and compact length. It then
solves the maximum feasible Primary Visual Area. One bounded renderer correction is allowed when
the compact Colorbar selects different tick text from its initial probe; there is no open-ended
position search or visual trial-and-error loop.

All ordinary panels in a regular grid receive the same Primary Axes width and height. A vertical
Colorbar receives a right Ornament Strip equal to its physical gap, width, actual right tick/label
overhang, and containment padding. It consumes width only: unused space above and below the compact
Colorbar cannot reduce primary height. A narrower Primary Axes in that panel is intentional and
cannot alter the equal Outer Panel Footprint.

For a registered square scientific region, the solver maximizes its side under the measured
reservations. The renderer-derived diagnostic compares achieved and maximum area under identical
constraints and requires at least `0.98` efficiency. It also reports the hypothetical maximum with
the right auxiliary strip removed, so every Colorbar penalty is attributable to a real width
constraint rather than hidden subplot whitespace.

## 3. Panel labels

Labels are `(a)`, `(b)`, `(c)`, …, 11 pt bold. The semantic anchor is the Primary Axes spine
rectangle upper-left, followed by the single `panel.left_offset_pt=-1 pt` and
`panel.top_offset_pt=+1 pt` translation. The label remains panel-owned and occupies the reserved
footprint gutter; it does not determine or move Primary Axes geometry after placement.

## 4. Legends

Single-series plots omit legends. A multi-series request tries `N`, `N-1`, … columns and accepts
the first candidate that fits the output boundary without axes or panel-label collision. If one row
fits, a multi-row candidate is forbidden.

Every spacing term is explicit in `style.yaml`: `handlelength=1.0`, `columnspacing=1.0`,
`handletextpad=0.8`, `labelspacing=0.5`, `borderpad=0`, and `borderaxespad=0`. A requested top legend
reserves only its measured bbox height plus `legend.top_gap_pt`. Mantel's bottom legends likewise
reserve their measured bboxes and deterministic gap rather than an arbitrary full-width region.

## 5. Colorbars

A Colorbar is Auxiliary Axes in the right Ornament Strip, not an equal-width sibling plot. The
layout solver is its only geometry owner; no preliminary fixed-ratio subgrid exists. Its width and
gap use physical point tokens and its complete decorated bbox must remain inside the owning
footprint. The vertical Colorbar is centered on its reference Primary Visual Area and reserves no
top or bottom strip.

For normal numeric axes, Matplotlib's `inout` major parameter is the total tick length. The
Colorbar uses outward ticks only, so its major length is derived as half that total. Its outward
minor length is the unchanged central minor token. Stroke width remains `main_stroke`.

Horizontal Colorbar geometry is not standardized in v1 and no current production template depends
on it.

## 6. Failure behavior

All layout quantities are physical points, millimetres, or renderer pixels converted to points.
If primary data, intrinsic labels, required legends, and the measured Colorbar strip cannot fit,
the solver raises `LayoutConstraintError` and identifies the infeasible physical constraint. It
does not shrink typography or markers, shorten a Colorbar, distort a square, overlap ornaments, or
cross the page boundary.

## 7. Deterministic-first boundary

The Agent selects scientific intent, an existing template, data mapping, typography mode, geometry
preset, palette, and limited scientific semantic parameters. The engine derives physical size,
footprints, spacing, ornament position, legend rows, Colorbar geometry, bar width, ticks, margins,
fonts, strokes, and palette values. Agent-generated coordinates or replacement token values are
invalid inputs.
