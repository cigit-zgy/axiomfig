# Uncertainty, estimation, and model-evaluation routing

Use this topic when uncertainty, effect estimates, agreement, calibration, classification
performance, model residuals, learning behavior, or feature importance is central. All templates in
this topic visualize supplied statistical results. The Agent must identify the result and its
meaning; AxiomFig does not fit models or compute diagnostic curves.

## Uncertainty terms are not interchangeable

- **Standard deviation (SD)** describes dispersion of observations in a sample or modeled
  population.
- **Standard error (SE)** describes sampling uncertainty of an estimated statistic, commonly a
  mean, under a stated procedure.
- **Confidence interval (CI)** is a frequentist interval produced by a stated repeated-sampling
  procedure for an estimate or parameter.
- **Prediction interval (PI)** describes uncertainty for a future or new observation and is not a
  CI for a mean or parameter.
- **Credible interval** is a Bayesian posterior probability interval under an explicit model and
  prior.

These concepts answer different questions. Never relabel one as another. If a request says only
"error", or supplies `lower` and `upper` without interval meaning, the action is `clarify` before
rendering. The runtime can display supplied limits; it cannot recover their scientific definition
from their numerical values.

## Choose among estimation templates

- `estimation.forest` compares multiple precomputed effects and intervals, often across studies or
  subgroups. Its labels, estimates, interval type, and any null reference must be supplied.
- `estimation.point_interval` is a compact categorical display when estimate precision is the main
  message and a forest-study grammar is unnecessary.
- `estimation.coefficient` compares supplied model terms and coefficient intervals, optionally
  across models. Coefficient meaning depends on the upstream model and scale.

Estimate, interval, and null/reference value are separate concepts. Difference and coefficient
effects often use zero as a null; ratio measures such as odds, risk, or hazard ratios often use one.
That general convention is not permission to guess the effect type, axis transform, or reference.
The current contracts accept an optional `reference` for forest and coefficient graphics. Supply
it when scientifically required; otherwise clarify or record the unsupported semantic gap. Do not
silently put ratio measures on a log axis or transform an estimate merely because forest plots
often do so.

## Choose among diagnostic templates

- `diagnostics.residual` receives fitted values and residuals. Its zero line is the invariant
  no-residual reference; an optional supplied trend is descriptive, not a model AxiomFig fits.
- `diagnostics.bland_altman` receives precomputed means, differences, center, limits, and an
  explicit `agreement_type`. All must come from the upstream agreement analysis. It addresses
  agreement, not correlation.
- `diagnostics.calibration` receives predicted probabilities and observed frequencies. The
  identity relation represents perfect calibration and must not be described as an ordinary
  regression fit.
- `diagnostics.roc` receives false-positive and true-positive rates. AxiomFig does not derive these
  points from labels or scores.
- `diagnostics.precision_recall` receives recall and precision. It may include a supplied baseline;
  AxiomFig does not derive prevalence or curve points.
- `diagnostics.learning_curve` receives iteration, metric, and series. Confirm whether the supplied
  x role represents iteration, epoch, or training size; do not rename one as another.
- `diagnostics.qq` receives theoretical and sample quantiles and an explicit reference
  distribution. It does not choose the reference distribution or compute quantiles.
- `diagnostics.feature_importance` receives feature, importance, and an explicit
  `importance_type`. Importance from coefficients, permutation, impurity, SHAP-like summaries, or
  other methods is not a universal interchangeable quantity.

## Scientific distinctions

Residual and Q-Q graphics diagnose different properties: residual plots expose structure against
fitted values, while a Q-Q plot compares supplied sample quantiles to a named reference
distribution. Calibration concerns whether predicted probabilities match observed frequencies;
discrimination curves concern ranking/class separation. ROC and precision–recall views are not
interchangeable. Under substantial class imbalance, ROC can look optimistic while precision makes
false positive burden more visible, but this does not make PR universally superior. Choose from the
scientific evaluation objective and supplied curve data.

Agreement and association are also distinct. A high correlation can occur despite systematic
method differences. Bland–Altman uses differences against means, with supplied bias and limits when
available, to address whether methods agree sufficiently for the intended use. A parity scatter can
show equality deviations but does not replace an upstream agreement analysis.

## Ask when

Ask a minimal clarification when:

- uncertainty type or coverage is unknown;
- the effect measure, coefficient scale, null reference, or axis transformation materially affects
  interpretation;
- a method-comparison request could mean parity, correlation, or formal agreement;
- a learning-curve x field could be epoch, iteration, or training size;
- a Q-Q reference distribution is unspecified;
- feature importance is supplied without its definition;
- a classifier-evaluation request does not reveal whether the user has ROC/PR points or only raw
  labels and scores;
- quantities or units are incompatible on a shared estimation axis.

Do not ask about error-bar cap width, marker size, line style, legend position, or reference-line
appearance. Those are deterministic visual rules.

## Require upstream computation when

Require upstream analysis for residuals, fitted values, regression trends, agreement means and
differences, bias or limits of agreement, calibration bins/frequencies, ROC points, PR points,
learning metrics, theoretical/sample quantiles, feature importance, estimates, and intervals when
they are absent. Do not calculate a confidence interval from an estimate and SE, or an SE from an
SD and n, merely to make a plot. Such calculations embed statistical assumptions outside the
visualization contract.

## Do not infer

Never infer uncertainty type, confidence level, prediction target, Bayesian interpretation,
reference distribution, feature-importance method, model family, class prevalence, effect scale,
null value, or causal meaning. Do not call a reference line a fitted model. Do not translate
correlation into agreement, discrimination into calibration, or feature importance into causal
effect.

## Common misuse

- Labeling mean ± SD as a confidence interval.
- Reading overlapping unspecified error bars as a formal significance test.
- Using correlation to claim two measurement methods agree.
- Computing ROC or PR inside the plotting layer from labels and scores.
- Comparing coefficient magnitudes from incompatible scales as if they were commensurate.
- Treating a Q-Q reference as implicitly normal.
- Presenting one feature-importance definition as model-independent truth.

## Evidence

- Cumming, Fidler, and Vaux, [Error bars in experimental biology](https://doi.org/10.1083/jcb.200611141), explains why SD, SE, and confidence intervals communicate different quantities.
- Bland and Altman, [Statistical methods for assessing agreement between two methods of clinical measurement](https://www-users.york.ac.uk/~mb55/meas/ba.htm), distinguishes method agreement from correlation.
- Saito and Rehmsmeier, [The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets](https://doi.org/10.1371/journal.pone.0118432), analyzes how imbalance changes ROC and PR interpretation.
