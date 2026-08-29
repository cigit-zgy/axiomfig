# Scientific visualization principles for AxiomFig

## 1. Source and attribution

This contract derives project decisions from Nicolas P. Rougier's *Scientific Visualization: Python + Matplotlib*, reviewed in both the [upstream repository](https://github.com/rougier/scientific-visualization-book) and the [cigit-zgy fork](https://github.com/cigit-zgy/scientific-visualization-book) at commit `62fa569f30333c817c13e4dc757877c1192fd15a`.

The book material is licensed under CC BY-NC-SA 4.0; repository code carries the BSD-style terms in `LICENSE.txt`. AxiomFig copies neither text, figures, nor source implementations. It records only attributed design implications and implements them independently.

## 2. Concrete implications

### 2.1 Explicit anatomy and ownership

A Figure is the output container. Each regular top-level GridSpec slot is an Outer Panel Footprint that owns one Primary Axes, optional Auxiliary Axes, and local artists. Legends are Figure-level Ornaments; colorbars are Auxiliary Axes. Explicit ownership replaces reliance on Matplotlib's current-axes state or inferred artist location.

### 2.2 Physical and deterministic layout

Publication geometry is calculated in millimetres and points before conversion to Matplotlib fractions. Figure width, panel gaps, label offsets, legend gap, colorbar gap/width, padding, fonts, and strokes do not vary with DPI or Agent preference. Constraint conflicts fail validation instead of being resolved through visual trial and error.

### 2.3 GridSpec as a constraint boundary

Top-level GridSpec cells define equal panel footprints. Complex panels subdivide their own slot. A heatmap may use a narrower Primary Axes because its fixed colorbar is inside the same footprint, but it cannot append an axes beyond the slot or change a peer footprint.

### 2.4 Ornaments remain subordinate to data

Legends, labels, annotations, direct labels, value labels, reference lines, and insets exist only to clarify scientific meaning. They receive explicit ownership, z-order, color, alpha, face, edge, and collision behavior. Unnecessary ornament is rejected as chartjunk rather than treated as decoration.

### 2.5 Typography and color semantics

Text roles use one complete sans or serif family contract at physical point sizes. Qualitative palettes encode categories, sequential maps encode ordered magnitude, and diverging maps require a scientifically meaningful center. Transparency belongs to the face when an opaque boundary carries structure.

### 2.6 Vector-first validation

The formal publication output is PDF. Raster PNG is a preview rendered from that PDF. A successful plotting call is insufficient: page geometry, font embedding, text boundary, panel containment, collision, and visual hierarchy must also pass.
