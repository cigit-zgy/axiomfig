# Figure anatomy validation contract

## 1. Runtime gate

Registered layouts run `validate_figure_anatomy()` after final typography and ornament placement and before the Matplotlib PDF is saved. A failure raises `FigureAnatomyError`; rendering stops rather than emitting a knowingly invalid artifact.

## 2. Deterministic checks

The validator checks:

1. equal footprint width and height;
2. same-column x0/x1 alignment and same-row y0/y1 alignment;
3. Primary/Auxiliary/local panel content containment;
4. exact footprint-based panel-label anchor;
5. panel-label collision and output boundary;
6. legend collision and output boundary;
7. colorbar/Auxiliary Axes containment;
8. local annotation containment;
9. visible output clipping represented by bbox overflow;
10. registered Figure-level Ornament overflow.

Checks run in display coordinates after `canvas.draw()`. The tolerance is a physical point value converted by the figure DPI. Equal-layout assertions use the registered logical footprints, not inferred Primary Axes widths.

## 3. Ownership behavior

Panel content is validated against only its own footprint. A panel label is anchored to the Primary Axes frame and uses the explicitly reserved label gutter inside that footprint. A legend is validated against the Figure boundary and all data axes/labels because it is Figure-owned. Moving an Auxiliary Axes beyond its panel or registering an out-of-page Figure ornament produces an issue-specific runtime failure.

## 4. Test boundary

Geometry tests use a small deterministic set: 2x2, 2x3, heatmap/colorbar containment, label anchor, legend normal/boundary/overflow, colorbar tick derivation, and deliberate boundary errors. They do not generate random combinations or hundreds of PDFs. The canonical Gallery remains the only full real-PDF E2E set, followed by one human visual review.
