# Metric Design

Metrics for every experiment group in `EXPERIMENT_PROTOCOL.md`. Statistical
requirements (§5 below) apply uniformly across all groups and must not be
weakened per group. **Do not only compare max Sharpe** — every portfolio
comparison in this project reports the full metric panel in §3, not a
single headline number, per the task brief's explicit instruction.

---

## 1. Layer 1 metrics

### 1.1 Representation (feeds L1.1)

| Metric | Definition | Computed from |
|---|---|---|
| Field coverage | fraction of canonical fields populated (not `MISSING`) per adapter | `FieldMapping.source_type` (`CONTRACT/schemas.py`'s `FieldSourceType`: NATIVE/DERIVED/HARNESS_SUPPLIED/MISSING) |
| Native retention % | already computed per-project in `PROJECT_SCHEMA_AUDIT.md` §7 (45–95% range) — reused, not recomputed from scratch |
| Representation loss | 1 − native retention |
| Extraction loss | fraction of native fields with real decision-relevant content that map to `MISSING` (not just any native field — see `PROJECT_SCHEMA_AUDIT.md`'s "information actively discarded" findings, e.g. finclaw's 74-field `StrategyDNA`) |
| Missingness | per-field `MISSING` rate across the eligible adapter/decision sample |
| Incremental predictive value | coefficient/effect size of a field's presence/value on forward `E` (`EXPERIMENT_PROTOCOL.md` §2.3), controlling for the rest of the field set — same nested-model logic as H1, applied per field |

### 1.2 Calibration (feeds L1.2)

Computed **per `ConfidenceKind` bucket** (`CONTRACT/schemas.py`:
`PROBABILITY`, `SELF_REPORTED`, `MODEL_MARGIN`, `SCORE_NORMALIZED`,
`ENTROPY_DERIVED`, `HEURISTIC`) — never pooled across kinds, per Session 1
Candidate 2's explicit finding that pooling hides the calibration pattern.

| Metric | Definition |
|---|---|
| Brier score | mean squared error between `ConfidenceEstimate.value` (mapped to [0,1]) and the realized binary outcome (`E`'s binary variant) |
| ECE (expected calibration error) | binned gap between mean predicted confidence and empirical hit rate, per confidence-kind bucket |
| Calibration slope / intercept | linear fit of empirical hit rate on predicted confidence, per bucket |
| Reliability curve | full binned predicted-vs-empirical plot, per bucket |
| Overconfidence rate | fraction of high-confidence (top decile within-bucket) decisions that are wrong |
| Confidence-conditioned return | forward return of the decision, stratified by confidence bucket and kind |

### 1.3 Stability (feeds L1.2)

Computed per adapter determinism class (deterministic / stochastic ML-RL /
LLM), across K repeated calls on a frozen `(adapter, ticker/universe,
as_of, data_cutoff, horizon)` tuple.

| Metric | Definition |
|---|---|
| Action agreement | fraction of the K repeats agreeing with the modal `Q1Action.action` |
| Flip rate | fraction of repeat pairs with disagreeing `action`/`Q3Signal.direction` |
| Score variance | variance of `action_strength`/`Q3Signal.strength`/`values` across repeats |
| Weight distance | L1/L2 distance between `Q4Policy.initial_weights` (or matched `PolicyDecisionStep.target_weights`) across repeats |
| Selected-universe overlap | Jaccard overlap of `PolicyDecisionStep.selected_universe` across repeats, where applicable |
| Policy drift | cumulative weight distance across a rolling trajectory (distinct from single-point weight distance — measures drift over time, not just call-to-call noise) |

### 1.4 Contradiction and Coherence (feeds L1.3 — the primary hypothesis carrier)

Directly tied to the pre-registered ontology in `EXPERIMENT_PROTOCOL.md`
§2.2 — **do not redefine "contradiction" here**; these metrics are computed
*from* that fixed ontology's binary/severity output `C`, not from an
independent definition.

| Metric | Definition |
|---|---|
| Contradiction incidence | rate of `C=1` events per (adapter-pair-or-adapter, stratum) |
| Severity | §2.2's severity score distribution (count of simultaneously-triggered ontology classes, scaled by directional-conflict magnitude) |
| Breadth | fraction of the eligible adapter pool involved in a given contradiction event (relevant for cross-adapter classes) |
| Persistence | how many consecutive `as_of` points a given contradiction (same tuple, same class) recurs before resolving |
| Contradiction-conditioned error | `E` (§2.3) computed separately for `C=1` vs. `C=0` decision points — the core H1 evidence table |
| Contradiction-conditioned drawdown | forward drawdown of the affected position(s), conditioned on `C` — feeds L2.4's evaluation directly |
| Coherence-violation rate | rate of the intra-adapter ontology classes specifically (Q1/Q3 mismatch, Q2→Q4 self-referential violation, action/logic inconsistency) — reported separately from cross-adapter incidence, since the two are structurally distinct per `EXPERIMENT_PROTOCOL.md` §2.2 |

### 1.5 Regime Reliability (feeds L1.4)

| Metric | Definition |
|---|---|
| Conditional hit rate | §1.2/1.3-style hit rate, stratified by regime label |
| Conditional calibration | ECE/Brier, stratified by regime |
| Conditional policy performance | §3's portfolio metrics, stratified by regime |
| Adapter/pair rank stability | Spearman correlation of adapter reliability ranking across regime strata — high correlation = regime-invariant reliability (a valid, pre-registered null result per `EXPERIMENT_PROTOCOL.md` §2.6) |

---

## 2. Layer 2 prediction metrics (feeds L2.1, L2.4's selective-prediction half)

| Metric | Definition |
|---|---|
| Directional accuracy | fraction of decisions whose directional call matches realized forward sign |
| Balanced accuracy | accuracy adjusted for class imbalance across BUY/SELL/HOLD or LONG/SHORT/NEUTRAL |
| Precision / recall | per-class, for the directional call |
| AUC | where a continuous score is available (e.g. `Q3Signal.values`) and the target is binarizable — not forced where meaningless (e.g. not computed for HOLD-heavy adapters with near-degenerate class balance) |
| Brier | same construction as §1.2, applied to the fused/routed/intervened decision rather than a single adapter |
| Selective risk | error rate restricted to the subset of decisions *not* abstained on — the core L2.4 metric |
| Coverage-risk curve | selective risk as a function of abstention rate (coverage), swept across the intervention threshold — required, not just a single-threshold number, per the task brief's explicit instruction that abstention evaluation "cannot only look at accuracy" |

---

## 3. Layer 2 portfolio metrics (feeds L1.5, L2.1–L2.6's Q4-facing evaluation)

Reported as a **full panel**, always together, never Sharpe alone:

| Metric | Definition |
|---|---|
| Cumulative / annualized return | standard, net of the Controlled Scientific Track's shared transaction-cost model |
| Volatility | annualized standard deviation of returns |
| Sharpe | (return − risk-free rate) / volatility, using the Controlled Scientific Track's shared risk-free rate |
| Sortino | downside-deviation-adjusted variant of Sharpe |
| Max drawdown | peak-to-trough decline over the evaluation window |
| Calmar | annualized return / max drawdown |
| CVaR (conditional value at risk) | expected loss beyond a pre-registered tail quantile (e.g. 95th percentile — exact quantile fixed at pilot stage, not chosen post-hoc) |
| Downside deviation | standard deviation computed only over negative-return periods |
| Turnover | per the Controlled Scientific Track's shared rebalancing/turnover definition, consistent across all compared systems |
| Transaction-cost-adjusted return | return net of the shared transaction-cost model — the *only* return figure ever reported as a headline number, never a gross-of-cost figure standing alone |
| Concentration | Herfindahl index or max single-asset weight, per the task brief's risk-audit requirement |
| Cash usage | average/terminal cash weight |
| Exposure | gross and net exposure, per `PortfolioConstraints` (`CONTRACT/schemas.py`) |
| Constraint violations | count/rate of `PolicyDecisionStep.constraint_violations`, and any `PortfolioConstraints` check failures caught by the schema's own `_check_weights_against_constraints` validator |

Per `EXPERIMENT_PROTOCOL.md` L1.5's explicit instruction: **performance
metrics and risk metrics are always reported as two visually/structurally
separate blocks**, not interleaved into one ranked table, so a
high-Sharpe/high-risk system cannot be presented as unambiguously "better"
than a lower-Sharpe/lower-risk one without the reader seeing both facts
side by side.

---

## 4. Routing-specific metrics (feeds L2.2)

| Metric | Definition |
|---|---|
| Regret vs. oracle | performance gap between the router's realized choice and the (non-deployable) oracle upper bound from `BASELINE_DESIGN.md` §3 — a ceiling-reference metric, not a claim of achievability |
| Router stability | how often the router's selected system changes between consecutive rebalance points (excessive churn is itself a cost, tracked via turnover above) |

---

## 5. Statistical requirements (uniform across every group above)

- **Bootstrap confidence intervals**: reported for every headline number in
  every table above, not just point estimates.
- **Block bootstrap for time series**: block length ≥ the longest horizon
  under test (≥ 20 trading days when the 20d horizon is included) — a
  naive i.i.d. bootstrap understates variance for autocorrelated financial
  time series and must not be used anywhere in this protocol. This is the
  same discipline `EXPERIMENT_PROTOCOL.md` §2.4 already fixes for H1's
  test; every other metric in this document reuses it, not a separate,
  weaker standard.
- **Paired tests**: baseline-vs-proposed comparisons use paired
  (same-decision-point) tests wherever the two systems are evaluated on
  the identical decision stream, which is the default under the Controlled
  Scientific Track.
- **Multiple-comparison correction**: Benjamini-Hochberg FDR across the
  full (system × regime × horizon) comparison grid — same rule as
  `EXPERIMENT_PROTOCOL.md` §2.4, reused here, not redefined.
- **Effect size, not just significance**: every reported comparison
  includes an effect-size figure (e.g. standardized mean difference for
  return comparisons, incremental AUC/pseudo-R² for prediction
  comparisons) alongside its p-value/confidence interval.
- **Practical significance threshold**: fixed at the pilot stage
  (`EXPERIMENT_DEPENDENCY_MAP.md`), before the validation stage begins —
  not chosen after seeing results, per `EXPERIMENT_PROTOCOL.md` §2.4 and
  §2.6's explicit anti-post-hoc-fallback discipline.
- **Seeds / repeated runs**: for any stochastic component this protocol
  itself introduces (e.g. L2.6's trained meta-model, a learned router in
  L2.2), report across ≥3 seeds (aligned with the general ARIS
  `experiment-plan` default of `DEFAULT_SEEDS = 3` where budget allows);
  for adapter-level stochasticity, reuse L1.2's K-repeat stability
  machinery instead of introducing a second, redundant repeated-run
  protocol.
- **Aggregation across assets, regimes, and horizons**: never a flat
  average across strata with very different sample sizes or variances —
  aggregate via a weighted or stratum-explicit summary (e.g. random-effects
  meta-analytic pooling across regime strata, or explicit per-stratum
  reporting with a clearly labeled pooled figure), and always report the
  per-stratum breakdown alongside any pooled number so a reader can see
  whether the pooled figure is driven by one stratum.
