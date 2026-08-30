# Matrix, ordination, and association routing

Use this topic for matrix-valued quantities, ordination results, Mantel results, and precomputed
association networks. Before routing, identify whether matrix cells are magnitudes, signed
deviations, correlations, categorical states, counts, or annotations. For multivariate methods,
identify which analysis was performed upstream and which result objects are available. Similar
two-dimensional displays do not make PCA, PCoA, and NMDS scientifically interchangeable.

## Choose among heatmap templates

- `heatmap.basic` displays a supplied matrix with row labels, column labels, and explicit
  `color_semantics`. Use sequential semantics for ordered one-sided magnitude; diverging semantics
  only when a scientifically meaningful center is supplied; qualitative semantics for genuinely
  categorical cells; and cyclic semantics only for periodic quantities.
- `heatmap.annotated` adds supplied cell annotations to the same explicit matrix color semantics.
  Annotations identify or quantify cells; AxiomFig does not derive new statistics for them.
- `heatmap.correlation` displays a supplied square correlation matrix with a signed diverging scale.
  Correlation has a meaningful neutral center at zero; the contract requires the center rather
  than relying on an unspoken default in user data.
- `heatmap.clustered` displays a supplied matrix using supplied complete row and column orders.
  AxiomFig does not choose a distance metric, linkage, cluster count, or ordering.
- `heatmap.confusion_matrix` displays a supplied square class-by-class matrix. It does not create
  predictions, choose a threshold, or calculate the confusion matrix from labels.

Never center every heatmap at zero. A non-negative abundance matrix generally uses sequential
semantics; zero may be a minimum rather than a neutral midpoint. Conversely, a signed deviation or
effect matrix may need a center whose meaning must be stated. Color semantics are scientific
semantics, not palette preferences. The runtime selects the actual colors and colorbar geometry.

## Choose among ordination templates

- `ordination.pca_scores` displays supplied PCA coordinates and explained variance. PCA is a linear
  projection based on variance structure of a numeric representation; AxiomFig does not center,
  scale, decompose, or fit it.
- `ordination.pca_biplot` requires supplied sample coordinates, feature loadings, and explained
  variance. Scores and loadings represent different entities. Never infer loadings from scores or
  treat vector direction as a group trajectory.
- `ordination.pcoa` requires supplied coordinates, explained variance, and the upstream distance
  metric. PCoA operates from a dissimilarity/distance representation and is not PCA with a different
  label.
- `ordination.nmds` requires supplied coordinates, stress, and distance metric. NMDS represents
  rank-order relationships in dissimilarities; do not invent stress, attach variance-explained
  meaning to axes, or calculate an ordination.

Ordination orientation, reflection, and rotation can be arbitrary without changing the fitted
relationships. Interpret relative configuration under the supplied method and metric, not compass
direction. Group coloring is allowed only when the group is scientifically supplied. Proximity in
an ordination is not automatically evidence of causality or a formal hypothesis test.

## Choose among association templates

- `association.mantel` consumes a supplied Pearson correlation matrix and supplied Mantel links.
  Every link contains source, target, `mantel_r`, and `p_value`; AxiomFig neither calculates the
  correlation matrix nor performs the Mantel tests. Advanced visual composition remains documented
  in `references/mantel.md` rather than duplicated here.
- `association.correlation_network` consumes supplied nodes, edges, and edge weights, with optional
  group and significance information. It visualizes a precomputed association structure; layout or
  edge presence must not be described as causal direction unless direction was scientifically
  supplied upstream.

Pearson and Mantel encode different questions. Pearson asks whether measured variable values
co-vary. A Mantel link asks whether two sample-to-sample dissimilarity patterns correspond. Neither
establishes causality. Do not derive Mantel significance from the matrix, or describe a correlation
network as a mechanistic network solely because it has edges.

## Scientific distinctions

| Available result and question | Route |
|---|---|
| General labeled matrix with known color meaning | `heatmap.basic` |
| Same matrix with supplied cell labels/values | `heatmap.annotated` |
| Signed correlation coefficients | `heatmap.correlation` |
| Matrix plus upstream row/column ordering | `heatmap.clustered` |
| Supplied class-confusion counts or rates | `heatmap.confusion_matrix` |
| PCA sample coordinates | `ordination.pca_scores` |
| PCA scores plus feature loadings | `ordination.pca_biplot` |
| Coordinates from a named distance metric via PCoA | `ordination.pcoa` |
| NMDS coordinates plus stress and distance metric | `ordination.nmds` |
| Pearson matrix plus Mantel r and p links | `association.mantel` |
| Precomputed node-edge association structure | `association.correlation_network` |

## Ask when

Ask when:

- a matrix's color meaning or diverging center is unspecified;
- values could be raw magnitudes, signed changes, proportions, or categories;
- a requested clustered heatmap lacks an explicit upstream ordering decision;
- an ordination method, distance metric, explained variance, stress, or score/loading identity is
  missing;
- a generic "PCA plot" could mean scores only or a biplot;
- network edge direction, sign, weight, or significance meaning is ambiguous;
- units or normalization differ across matrix rows/columns in a way that changes interpretation.

Do not ask for colormap names, cell size, colorbar width, label rotation, node size, or network edge
width. Those visual decisions are deterministic.

## Require upstream computation when

Require upstream analysis when the user provides raw features but requests PCA, PCoA, NMDS, a
Mantel test, correlation significance, clustering, or a confusion matrix derived from labels and
predictions. Require scores and explained variance for PCA; scores and loadings for a biplot;
coordinates, metric, and explained variance for PCoA; coordinates, metric, and stress for NMDS;
orders for clustered heatmaps; and complete Mantel or network relationships for association
templates. Do not add an analysis dependency to make the plot render.

## Do not infer

Never infer color center, normalization, clustering order, distance metric, ordination coordinates,
loadings, stress, explained variance, Mantel statistics, edge significance, causal direction, or
unit conversion. Do not equate correlation with causation, PCA with PCoA, or either with NMDS. Do
not describe axis orientation as intrinsically meaningful when the method does not support that
claim.

## Common misuse

- Applying a diverging scale centered at zero to an unsigned abundance matrix.
- Calling a reordered matrix "clustered" without an upstream clustering result.
- Computing PCA or Mantel statistics in the plotting adapter.
- Reading PCA loading vectors as sample trajectories.
- Reporting variance explained for NMDS axes.
- Treating a dense association network as a causal mechanism.

## Evidence

- The scikit-learn [PCA documentation](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html) defines PCA as a linear dimensionality-reduction projection of centered data.
- The scikit-bio [PCoA documentation](https://scikit.bio/docs/latest/generated/skbio.stats.ordination.pcoa.html) specifies a distance matrix as the method input and returns eigenvalue-based ordination results.
- The vegan [NMDS documentation](https://vegandevs.github.io/vegan/reference/metaMDS.html) documents non-metric multidimensional scaling, supplied dissimilarity choices, and stress.
