# Validation

## Rendering trust boundary

```text
Matplotlib Figure
  -> deterministic layout and ornaments
  -> in-memory Figure validation
  -> vector intermediate PDF
  -> Tectonic standalone finalization
  -> final PDF
  -> Poppler PNG preview
  -> artifact validation
```

The PNG is rasterized from the final PDF. TeX sources, logs, intermediates, manifests, and caches
remain under ignored temporary directories; Gallery contains only final PDF/PNG deliverables.

## In-memory validation

`validate_figure_anatomy()` runs after final layout, typography, and ornament placement. It checks:

1. equal panel-footprint width and height;
2. row and column footprint alignment;
3. Primary/Auxiliary Axes and local artist containment;
4. frame-relative panel-label anchors and collisions;
5. legend, annotation, colorbar, and Figure-ornament containment;
6. visible output-boundary overflow.

Checks use display coordinates after `canvas.draw()` and a physical-point tolerance converted by
figure DPI. A failure raises `FigureAnatomyError`; rendering stops instead of emitting a knowingly
invalid artifact.

## PDF and Gallery validation

Artifact validation requires a parseable single-page PDF, expected physical geometry, a non-empty
PNG, embedded and subset fonts, no Type 3 fonts, no text beyond the PDF boundary, and clean Tectonic
font/glyph diagnostics. Gallery validation additionally enforces the exact registry-derived nested
artifact set and rejects missing or orphan files.

The frozen Gallery contains 55 sans pairs, 55 serif pairs, and two Tectonic-native technical pairs:
112 pairs and 224 artifacts.

## Commands

```bash
python scripts/check_fonts.py
python scripts/check_latex.py
python scripts/generate_colors.py --check
axiomfig-gallery gallery
axiomfig-validate gallery
python scripts/evaluate_release.py --output tmp/release-evaluation
```

Automated validation does not replace the final human review of stroke hierarchy, tick direction,
categorical axes, legends, panel symmetry, colorbars, clipping, and sans/serif structural identity.
