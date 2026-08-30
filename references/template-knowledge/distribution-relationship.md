# Distribution and relationship routing

Use this topic when the scientific question concerns the shape of a distribution, individual
observations, or a relationship between quantitative variables. First decide whether the user
wants a univariate/grouped distribution or a bivariate relationship. Then determine whether raw
observations, a precomputed density, a fitted relationship, or a third quantitative encoding is
actually supplied.

## Choose among distribution templates

- `distribution.histogram` bins raw values and shows empirical count or frequency. Apparent shape
  depends partly on the binning, so do not present it as invariant to bin choice.
- `distribution.density` consumes a precomputed x grid and density values. It visualizes an
  upstream density estimate; AxiomFig does not select a kernel or bandwidth.
- `distribution.ecdf` uses raw observations to show empirical cumulative probability without
  histogram bins or density bandwidth. It is useful for comparing complete distributions and
  reading proportions above or below a value.
- `distribution.box` gives a compact distribution summary. It does not expose multimodality or the
  complete empirical shape.
- `distribution.violin` emphasizes supplied raw-data distribution shape. It does not make each
  observation individually visible.
- `distribution.box_violin` combines compact summary and distribution shape when both matter.
- `distribution.strip` keeps individual observations visible and is especially valuable when the
  observation-level pattern is scientifically important and overplotting remains manageable.
- `distribution.raincloud` combines distribution, summary, and observations when all three layers
  contribute to interpretation.

Small samples often benefit from showing observations because summaries can hide their structure.
As density increases, ECDFs or distribution summaries may communicate structure more clearly than
an unreadable point cloud. These are qualitative routing principles, not universal sample-size
cutoffs. Study design, discreteness, ties, outliers, and the scientific role of individual
observations matter more than a fixed n threshold.

## Choose among relationship templates

- `scatter.simple` shows association between two quantitative variables. Association alone does
  not establish causality.
- `scatter.grouped` adds a scientifically meaningful group identity. Do not create groups from
  arbitrary styling preferences.
- `scatter.regression` consumes supplied x, y, and fitted values. AxiomFig displays an upstream fit;
  it does not select or fit a regression model.
- `scatter.parity` compares the same scientific quantity on both axes, such as observed versus
  predicted values or two measurement methods in compatible units. Its identity line `y = x` is
  meaningful only under that same-quantity contract.
- `scatter.bubble` adds a quantitative third variable encoded by marker area. The scientific
  quantity maps to area, not marker diameter; the size role and its units must be explicit.
- `scatter.hexbin` aggregates dense bivariate observations into spatial counts when point overlap
  makes an ordinary scatter unreadable. Its continuous color scale represents count.

Parity is not a generic scatter aesthetic. Temperature versus ammonia, for example, is an
ordinary relationship because the axes measure different quantities. Method A versus method B may
use parity only when both measure the same underlying quantity in compatible units. A parity view
can reveal deviations from equality, but formal agreement is a different scientific question;
when supplied mean-and-difference results and limits of agreement are the intended evidence, route
to `diagnostics.bland_altman`.

## Scientific distinctions

| Question | Choose | Avoid confusing with |
|---|---|---|
| What values and outliers were observed? | `strip` | mean-only bars |
| What compact summary differs by group? | `box` | complete distribution shape |
| What is the shape of each distribution? | `violin` or precomputed `density` | raw-point visibility |
| What fraction is below a threshold? | `ecdf` | histogram bin counts |
| How are two quantitative variables associated? | `scatter.simple` | parity/agreement |
| Does prediction or method output equal the reference quantity? | `scatter.parity` | unrelated x-y association |
| What fitted relationship was computed upstream? | `scatter.regression` | fitting within AxiomFig |
| Are points too dense to read? | `scatter.hexbin` | arbitrary loss of observation identity |

## Ask when

Ask when:

- the objective could mean comparing raw distributions or comparing supplied summary estimates;
- a precomputed density is requested but the meaning or normalization of its density values is
  unclear;
- two axes in a proposed parity plot may represent different quantities or incompatible units;
- an unspecified "best-fit line" would require choosing a model;
- a bubble-size field has ambiguous scientific meaning or non-comparable units;
- a group column could encode a real experimental group or merely an identifier;
- method comparison could mean equality visualization or formal agreement assessment.

Do not ask the user to pick a marker, histogram color, legend location, bin-edge styling, or figure
size. If the template contract already determines a safe rendering choice, let the runtime apply
it.

## Require upstream computation when

Require upstream computation for a KDE or other density estimate when only raw values are supplied
for `distribution.density`; for fitted regression values when `scatter.regression` is requested;
and for Bland–Altman mean, differences, bias, and agreement limits when only paired raw method
measurements are available. AxiomFig may deterministically form an ECDF from raw observations
because that transformation is part of the existing plot grammar, but it must not silently choose
a statistical estimator or agreement procedure.

## Do not infer

Do not infer a kernel, bandwidth, probability model, regression family, transformation, causal
relationship, group definition, unit conversion, or agreement threshold. Do not infer that a box
plot represents a normal distribution or that a violin exposes raw observations. Do not interpret
marker diameter as the bubble quantity. Do not call high correlation agreement.

## Common misuse

- Replacing eight biological replicates per condition with mean bars without being asked to
  aggregate.
- Reading histogram peaks without considering binning.
- Treating a smooth density as observed point-level evidence.
- Choosing parity for two merely correlated but scientifically different variables.
- Adding a regression line and describing it causally.
- Using an ordinary scatter when overlap destroys the density pattern, or using hexbin when every
  observation must remain identifiable.

## Evidence

- Weissgerber et al., [Beyond Bar and Line Graphs](https://doi.org/10.1371/journal.pbio.1002128), documents how summary-only displays can conceal continuous-data distributions.
- Bland and Altman, [Statistical methods for assessing agreement between two methods of clinical measurement](https://www-users.york.ac.uk/~mb55/meas/ba.htm), explains why correlation does not measure agreement and motivates the mean-difference display.
