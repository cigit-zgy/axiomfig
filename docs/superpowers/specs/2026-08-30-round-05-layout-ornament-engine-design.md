# Round 05 Deterministic Layout and Ornament Engine Design

## 1. Scope and authority

This design implements the approved Round 05 brief. Work stays on `master`, adds no plot templates, no template knowledge base, no agent orchestration, and no new statistical behavior. The only architectural change is to make layout, ornaments, ownership, and geometry validation deterministic runtime services.

The implementation adopts principles from Nicolas P. Rougier's *Scientific Visualization: Python + Matplotlib*, reviewed at upstream/fork commit `62fa569f30333c817c13e4dc757877c1192fd15a`. The book text is CC BY-NC-SA 4.0 and its code uses a BSD-style license. AxiomFig will record attribution and derived design implications, but will copy neither prose, figures, nor source implementations.

## 2. Root cause

Round 04 computes a panel label from `outer_panel_bbox(axis)`, but the surrounding lifecycle is unstable:

1. panel builders place legends before the outer grid is finalized;
2. panel labels do not exist while legend collision checks run;
3. `place_legend_above()` may call `figure.subplots_adjust(top=...)`, mutating every panel after legend measurement;
4. family layout and label refresh run later, without re-solving legend collisions;
5. `outer_panel_bbox()` infers a top-level `SubplotSpec`, but no explicit object owns primary axes, auxiliary axes, local artists, or figure-level ornaments;
6. the inferred slot equals the data-axes rectangle, so tick labels, axis labels, value labels, and heatmap labels lie outside it by construction.

The failure is therefore lifecycle and ownership ambiguity, not an incorrect `left_offset_pt` or `top_offset_pt`.

## 3. Architecture

`src/axiomfig/layout.py` will own a small explicit model:

- `PanelFootprint`: immutable row/column identity and top-level `SubplotSpec`, plus registered primary axes, auxiliary axes, and panel-owned artists;
- `FigureLayout`: regular grid dimensions, ordered footprints, legend requests, and figure-level ornaments;
- `create_panel_grid()`: construct equal top-level GridSpec slots from physical page padding and physical panel gaps;
- `add_panel_axes()`: create ordinary or heatmap axes within one footprint;
- `solve_panel_layout()`: draw once, measure decoration overhangs, calculate common ordinary-panel insets and heatmap auxiliary allocation in points, then set all axes positions once;
- `outer_panel_bbox()` and registry accessors: expose stable ownership without rediscovering topology from arbitrary axes.

The solver is measure-once and formula-driven. It does not repeatedly move axes until they look right. Ordinary panels in a regular grid receive identical primary-axes geometry. A heatmap receives a panel-specific primary width because its fixed-gap, fixed-width colorbar is contained inside the same equal outer footprint.

`src/axiomfig/ornaments.py` will own reusable ornament behavior:

- legend request, measurement, deterministic `N..1` column selection, and placement;
- panel-label creation and refresh from the footprint upper-left plus physical ScaledTranslation;
- colorbar tick styling derived from central tick geometry;
- registration of figure-level and panel-level ornaments.

Templates declare the need for an ornament through these functions; they do not emit coordinates. Existing non-layout artist helpers remain in `template_helpers.py`.

`src/axiomfig/anatomy.py` will validate the runtime figure anatomy and raise one `FigureAnatomyError` containing deterministic issues. It will check footprint equality and alignment, panel-owned containment, label anchors and collisions, legend collision/boundary, auxiliary/colorbar containment, annotation boundary, and figure overflow. Rendering a registered layout will run this validator before PDF export.

## 4. Physical contracts

All layout calculations use `72 pt = 1 inch` and `25.4 mm = 1 inch`. Figure size remains 90/140/190 mm with physical font sizes unchanged.

The YAML owns only central visual tokens. Round 05 adds physical horizontal/vertical panel gaps, local containment padding, colorbar width/gap, and legend spacing. Derived values are not duplicated:

- colorbar major length = normal inout major total length / 2;
- colorbar minor length = normal minor length;
- legend lower bbox to top spine = `legend.top_gap_pt`;
- legend interior padding = `borderpad: 0`;
- legend axes padding = `borderaxespad: 0`;
- main inter-entry gap = `columnspacing: 1.0`, measured as half the prior default contribution.

Panel labels stay 11 pt bold at footprint upper-left with the same fixed physical offset. The label gutter is reserved in the figure boundary calculation, so no output solver moves the labels after placement.

## 5. Resource convergence

Runtime resources become package-local sources of truth:

```plain
src/axiomfig/resources/
├── fonts/
│   ├── licenses/
│   └── font binaries
└── latex/
    ├── axiomfig-colors.tex
    └── axiomfig.sty
```

Root `latex/` is deleted after its valid usage notes are merged into `references/latex-contract.md`. Root `fonts/` is moved into package resources with licenses intact. `typography.py` resolves bundled fonts through `importlib.resources`; `pyproject.toml` includes fonts and licenses as package data. A clean-wheel test proves both resource families remain discoverable without repository-relative paths.

## 6. Validation and Gallery

New deterministic tests cover exactly the requested geometry cases: equal 2x2 and 2x3 footprints, heatmap/colorbar containment, footprint-based panel-label anchor, legend normal/boundary/overflow, colorbar tick derivation, and output boundary failure. Resource tests cover absence of root duplicates and clean-wheel importlib lookup.

The complete Gallery retains the same 36 sans, 36 serif, and 2 Tectonic-native cases. After rebuilding, one visual review focuses on `02_multi_line`, `34_four_panel`, `35_six_panel`, and `36_complex_multi_panel` in both typography modes. At most one repair pass follows that review.

## 7. Documentation and completion

`SKILL.md` states the deterministic-first boundary and routes detailed layout/validation decisions to references. New references document Rougier-derived implications, layout terminology, runtime validator behavior, and the consolidated LaTeX resource path. The final report follows `basic-rule.md`, records measured root cause and test runtime, then the validated state is committed once, pushed to `master`, and verified from the fetched remote tree.
