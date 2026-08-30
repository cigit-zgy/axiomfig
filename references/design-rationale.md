# Design rationale

## Scientific visualization principles

AxiomFig translates principles from Nicolas P. Rougier's *Scientific Visualization: Python +
Matplotlib* into independent deterministic behavior. The project reviewed the
[upstream repository](https://github.com/rougier/scientific-visualization-book) and the
[cigit-zgy fork](https://github.com/cigit-zgy/scientific-visualization-book) at commit
`62fa569f30333c817c13e4dc757877c1192fd15a`.

The book material is CC BY-NC-SA 4.0 and its repository code carries BSD-style terms. AxiomFig
copies neither prose, figures, nor implementations. The concrete consequences are:

- Figure, Panel, Primary/Auxiliary Axes, Artist, and Ornament ownership is explicit.
- Publication geometry is solved in millimetres and points before conversion to figure fractions.
- Top-level GridSpec cells define equal outer footprints; complex panels subdivide their own cell.
- Ornaments clarify data and must pass containment and collision checks.
- Typography is coherent and color follows qualitative, sequential, diverging, or cyclic semantics.
- PDF is the formal output; successful plotting alone is not publication acceptance.

## Journal-informed taxonomy

The v1 taxonomy was checked against graphical forms visible in public pages or captions from 25
papers published in 2024–2025 across Nature, Nature Communications, Science Advances,
Environmental Science & Technology, and Water Research. This was an architecture census, not a
bibliometric study; no figures were copied.

Approximate paper-level lower bounds were: line/time-series 15/25, image or schematic 15/25,
scatter/regression 13/25, distribution 12/25, ordination 7/25, heatmap/matrix 6/25, omics 6/25,
bar/dot 3/25, association/network 3/25, estimation 2/25, survival 2/25, and field/map 1/25.

This evidence supports the bounded 13-family surface:

- core: `line`, `scatter`, `bar`, `distribution`, `heatmap`;
- statistical interpretation: `estimation`, `diagnostics`, `survival`;
- multivariate and domain science: `ordination`, `association`, `omics`;
- continuous and transport structure: `field`, `flow`;
- composition only: `layouts`.

Images, microscopy, chemical structures, GIS, general diagrams, animation, dashboards, and a large
3D suite remain outside AxiomFig v1.
