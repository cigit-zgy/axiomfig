# Capability-audit sources

`original/` records authoritative topology evidence, not a style target. Exact official examples
were preferred; otherwise a documented first-party API was executed with frozen substitute data,
or an official published raster was wrapped without claiming vector reconstruction. Optional
packages were used only from `tmp/layout-benchmark-venv` and are not AxiomFig dependencies.

| ID | Figure | Authoritative source | Exact URL | Version | Acquisition mode | Differences | License / provenance notes |
|---|---|---|---|---|---|---|---|
| 01 | Complex clustermap | Seaborn `clustermap` | https://seaborn.pydata.org/generated/seaborn.clustermap.html | 0.13.2 | Documented API; direct PDF | Frozen 18 x 12 matrix, supplied linkages and annotations replace Iris. | Seaborn BSD-3-Clause. |
| 02 | Dense PairGrid | Seaborn `PairGrid` | https://seaborn.pydata.org/generated/seaborn.PairGrid.html | 0.13.2 | Documented API; direct PDF | Frozen grouped measurements replace Penguins; the original has four rather than the audit's five variables. | Seaborn BSD-3-Clause. |
| 03 | Joint distribution | Seaborn `JointGrid` | https://seaborn.pydata.org/generated/seaborn.JointGrid.html | 0.13.2 | Documented API; direct PDF | Frozen grouped measurements replace documentation data; joint and marginal topology is retained. | Seaborn BSD-3-Clause. |
| 04 | Extended forest | statsmodels `dot_plot` | https://www.statsmodels.org/stable/generated/statsmodels.graphics.dotplots.dot_plot.html | 0.14.6 | Documented API; direct PDF | Frozen estimates and intervals replace example values; original has 14 rather than 24 rows. | statsmodels BSD-3-Clause. |
| 05 | KM + risk table | lifelines `add_at_risk_counts` | https://lifelines.readthedocs.io/en/stable/lifelines.plotting.html#lifelines.plotting.add_at_risk_counts | 0.30.3 | Documented API; direct PDF | Deterministic simulated durations replace unspecified data; three rather than four groups. | lifelines MIT. |
| 06 | Calibration dashboard | scikit-learn calibration example | https://scikit-learn.org/1.9/auto_examples/calibration/plot_calibration_curve.html | 1.9.0 | Official example; direct PDF | Export to PDF replaces `show`; official four-model topology retained. | scikit-learn BSD-3-Clause. |
| 07 | PDP / ICE dashboard | scikit-learn `PartialDependenceDisplay` | https://scikit-learn.org/1.9/auto_examples/inspection/plot_partial_dependence.html | 1.9.0 | Documented API; direct PDF | Frozen Friedman data replace network data; reference uses six 1-D panels while the audit includes a 2-D panel. | scikit-learn BSD-3-Clause. |
| 08 | Influence labels | statsmodels `influence_plot` | https://www.statsmodels.org/stable/generated/statsmodels.graphics.regressionplots.influence_plot.html | 0.14.6 | Documented API; direct PDF | Deterministic OLS fixture replaces State Crime data. | statsmodels BSD-3-Clause. |
| 09 | Dense volcano | EnhancedVolcano connector example | https://bioconductor.org/packages/release/bioc/vignettes/EnhancedVolcano/inst/doc/EnhancedVolcano.html#fit-more-labels-by-adding-connectors | 1.30.0 | Official published PNG wrapped losslessly | Exact reviewed 1920 x 1632 raster; no crop or retouch. | EnhancedVolcano GPL-3; image retained only as reference evidence. |
| 10 | Dotplot + dendrogram | Scanpy dotplot tutorial | https://scanpy.readthedocs.io/en/latest/tutorials/plotting/core.html#dotplot | 1.14.0.dev docs | Official published PNG wrapped losslessly | Exact reviewed documentation raster; no vector claim. | Scanpy BSD-3-Clause. |
| 11 | UpSet | UpSetPlot examples / API | https://upsetplot.readthedocs.io/en/stable/auto_examples/index.html | 0.9.0 | Documented API; direct PDF | Frozen memberships and counts replace example data. | UpSetPlot BSD-3-Clause. |
| 12 | OncoPrint | ComplexHeatmap OncoPrint book | https://jokergoo.github.io/ComplexHeatmap-reference/book/oncoprint.html | First-party book accessed 2026-08-31 | Official published PNG wrapped in one-page PDF | Introductory three-gene example is topology evidence; the audit expands samples and alteration types. | ComplexHeatmap MIT; documentation image retained as reference evidence. |
| 13 | Ridge density | Seaborn ridgeplot example | https://seaborn.pydata.org/examples/kde_ridgeplot.html | 0.13.2 | Documented first-party API; direct PDF | Frozen twelve-condition data replace the example dataset; figure-level labels preserve the documented stacked-facet topology. | Seaborn BSD-3-Clause. |
| 14 | Distribution composite | Seaborn `violinplot` and `stripplot` | https://seaborn.pydata.org/generated/seaborn.violinplot.html | 0.13.2 | Documented APIs; direct PDF | Frozen ten-treatment data; the reference omits the audit's precomputed brackets. | Seaborn BSD-3-Clause. |
| 15 | PCA biplot | AxiomFig registered PCA biplot control | https://github.com/cigit-zgy/axiomfig-skill/blob/master/gallery/sans/ordination/pca_biplot.pdf | Repository baseline `ea078fe` | Existing validated PDF copied | Current public grammar is used as a topology control; audit fixture adds three groups, ellipses and 12 labels. | AxiomFig repository license; no external authorship claim. |
| 16 | Mantel + correlation | AxiomFig canonical Mantel contract | https://github.com/cigit-zgy/axiomfig-skill/blob/master/references/mantel.md | Repository baseline `ea078fe` | Existing validated canonical PDF copied | Same registered grammar; audit native implementation is independently reconstructed with frozen values. | AxiomFig repository license; known-control evidence. |
| 17 | Classifier dashboard | scikit-learn display-object example | https://scikit-learn.org/stable/auto_examples/miscellaneous/plot_display_object_visualization.html | 1.9.0 | Documented display APIs; direct PDF | Frozen breast-cancer data and one fitted model; the audit freezes two models' visualization-ready metrics. | scikit-learn BSD-3-Clause. |
| 18 | Regression diagnostics | statsmodels regression plots | https://www.statsmodels.org/stable/generated/statsmodels.graphics.regressionplots.plot_regress_exog.html | 0.14.6 | Documented API; direct PDF | Deterministic OLS fixture; statsmodels' four regression-exog panels are topology evidence for the audit's diagnostic quartet. | statsmodels BSD-3-Clause. |
| 19 | Learning / scalability | scikit-learn learning-curve example | https://scikit-learn.org/stable/auto_examples/model_selection/plot_learning_curve.html | 1.9.0 | Documented API; direct PDF | Frozen digits/GaussianNB data; reference keeps learning and fit-time panels while the audit expands to six panels and two models. | scikit-learn BSD-3-Clause. |
| 20 | Manhattan + Q-Q | qqman first-party demo | https://github.com/stephenturner/qqman/blob/master/tools/qqman.gif | 0.1.9 repository | Two official animation frames cropped to their plot panes and wrapped side by side | RStudio chrome is excluded; no plot reconstruction or GWAS computation. | qqman GPL-3; official raster evidence only. |

## External probe provenance

The frozen native pass exposed repeated class-D movable-annotation work in cases 08 and 09. The
four PDFs under `external_probe/` therefore test only label allocation, using the previous frozen
fixture and otherwise identical Matplotlib/AxiomFig geometry:

- [adjustText 1.4.0](https://adjusttext.readthedocs.io/) — iterative text repulsion with connector
  support; inspected for both influence and volcano topologies.
- [textalloc 1.2.4](https://github.com/ckjellson/textalloc) — candidate-based allocation with
  obstacle and connector support; inspected for the same two topologies.

Both packages remained isolated in `tmp/layout-benchmark-venv`; neither is recommended as a
production dependency by this audit alone.
