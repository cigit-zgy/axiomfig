# Deterministic layout and ornament contract

## 1. Anatomy

| Term | Contract |
|---|---|
| Figure | Fixed physical output boundary |
| Outer Panel Footprint | Equal top-level GridSpec slot in a regular grid |
| Primary Axes | Panel's scientific data axes |
| Auxiliary Axes | Panel-owned support axes such as a colorbar |
| Panel-owned Artist | Local annotation, value/direct label, or other artist assigned to one panel |
| Figure-level Ornament | Legend or other content owned by the Figure rather than one panel |

Every registered panel has one Primary Axes. A heatmap adds its colorbar as Auxiliary Axes. The complete primary/auxiliary/local content bbox must remain inside the footprint; only the documented panel-label gutter may lie just outside it.

## 2. Physical solve

The engine converts the fixed page size to points using `72 pt = 1 inch` and `25.4 mm = 1 inch`. It creates equal GridSpec cells using YAML-owned physical horizontal and vertical gaps. The panel-label gutter and output padding are reserved before cells are created.

After templates add data and request ornaments, the engine performs one measurement pass. It measures axis-decoration overhangs and requested one-row legend height, calculates common ordinary-panel insets, and sets final axes bboxes once. It does not iterate positions until a rendered image looks acceptable.

All ordinary panels in a regular grid receive the same Primary Axes width and height. A heatmap uses its measured label inset plus fixed colorbar gap/width inside the same equal footprint. Its narrower Primary Axes is intentional and cannot alter the footprint.

## 3. Panel labels

Labels are `(a)`, `(b)`, `(c)`, …, 11 pt bold. The anchor is the Outer Panel Footprint upper-left corner, followed by the single `panel.left_offset_pt`/`panel.top_offset_pt` ScaledTranslation. It never uses `ax.transAxes`, the Primary Axes bbox, colorbar geometry, or a legend bbox.

The Round 04 instability was lifecycle-related: legends were measured before labels existed, a legend could mutate global subplot top, and family layout moved panels later. Round 05 finalizes footprint geometry first, then creates labels and legends, and forbids ornament code from changing global subplot geometry.

## 4. Legends

Single-series plots omit legends. A multi-series request tries `N`, `N-1`, … columns and accepts the first candidate that fits the output boundary without axes or panel-label collision. If one row fits, a multi-row candidate is forbidden.

Every spacing term is explicit in `style.yaml`: `handlelength=1.0`, `columnspacing=1.0`, `handletextpad=0.8`, `labelspacing=0.5`, `borderpad=0`, and `borderaxespad=0`. The measured `columnspacing=1.0` halves the prior default inter-column contribution. The lower legend bbox sits exactly `legend.top_gap_pt` above the top spine. A registered-layout legend is a Figure-level Ornament and cannot move panel geometry.

## 5. Colorbars

A colorbar is Auxiliary Axes. Its width and gap use physical point tokens and its complete decorated bbox must remain inside the owning footprint. It cannot be created outside a full-width Primary Axes.

For normal numeric axes, Matplotlib's inout major parameter is the total tick length. The colorbar uses outward ticks only, so its major length is derived as half that total. Its outward minor length is the unchanged central minor token. Stroke width remains `main_stroke`.

## 6. Deterministic-first boundary

The Agent selects scientific intent, an existing template, data mapping, typography mode, geometry preset, palette, and limited scientific semantic parameters. The engine derives physical size, footprints, spacing, ornament position, legend rows, colorbar geometry, bar width, ticks, margins, fonts, strokes, and palette values. Agent-generated coordinates or replacement token values are invalid inputs.
