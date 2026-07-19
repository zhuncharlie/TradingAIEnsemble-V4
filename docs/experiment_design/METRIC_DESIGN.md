# METRIC_DESIGN.md

Status: design document. Defines what to compute and how, and the
conditions under which a metric is *not* computable and must be reported as
`insufficient_data`/`not_applicable` rather than approximated. No adapter,
schema, harness, or Python code is modified here.

Companion documents: `DATA_SPLIT_PROTOCOL.md` (windows/purge rules these
metrics are computed within), `BASELINE_DESIGN.md` (what gets compared),
`EXPERIMENT_PROTOCOL.md` (which experiment uses which metric).

---

## 0. The confidence-comparability problem (governs §1.2–1.4)

`CONTRACT/schemas.py` v2.0.0 already contains the fix the pilot study
identified it needed: `ConfidenceEstimate.kind` (`PROBABILITY`,
`SELF_REPORTED`, `MODEL_MARGIN`, `SCORE_NORMALIZED`, `ENTROPY_DERIVED`,
`HEURISTIC`). This is a hard constraint on every calibration-style metric
below:

- **Brier score and ECE are only mathematically meaningful for
  `kind=PROBABILITY`** (a value claiming to already be a well-formed
  probability of a binary/categorical outcome). Computing Brier/ECE on a
  `SELF_REPORTED` LLM conviction score or a `SCORE_NORMALIZED`
  cross-sectional percentile (as the pilot did, treating all nine
  confidence-bearing adapters' values as interchangeable 0–1 numbers) is
  exactly the error D2 exists to catch — this document does not repeat it.
- For non-`PROBABILITY` kinds, use **hit-rate-by-bucket reliability
  diagrams** (bucketed avg-value vs. realized hit rate, no probabilistic
  interpretation implied) — this is what the pilot actually computed and
  correctly labeled as calibration error, just not as Brier/ECE.
- Every calibration table row must carry the `kind` it was computed under.
  A table that mixes kinds in one column without labeling them repeats the
  pilot's exact finding (seven incompatible mechanisms) instead of fixing
  it.

---

## 1. Layer 1 / prediction-level metrics

### 1.1 Directional accuracy / hit rate

`compute_hit`-style rule (reused from the pilot,
`analysis/icaif_metrics.py`): BUY/LONG hits if forward return over horizon
`h` exceeds `+threshold_bps`; SELL/SHORT hits if below `-threshold_bps`;
HOLD/NEUTRAL hits if `|forward return| <= threshold_bps`. Default
`threshold_bps = 20.0`, horizons `{1, 5, 20}` trading days — kept identical
to the pilot for comparability, but must be re-justified (or swept as a
sensitivity check) rather than assumed correct, since 20bp was originally
a pilot default, not a validated choice.

### 1.2 Calibration error (bucketed, all kinds)

`|avg(confidence.value) - hit_rate|` within `[0.0-0.5, 0.5-0.6, ...,
0.9-1.0]` buckets, per (adapter, question, horizon). Report bucket `n`
alongside every cell — the pilot found 28/39 buckets with `n<10`; treat
any cell below a minimum sample threshold (recommend `n>=10`, matching the
pilot's own overconfidence-flag threshold) as directional-only, not a
point estimate to be reported without a wide uncertainty caveat.

### 1.3 ECE / Brier — `kind=PROBABILITY` only

Standard definitions, computed only on the `PROBABILITY`-kind subset. If
zero adapters populate `kind=PROBABILITY` honestly (plausible — the pilot's
9 confidence-bearing adapters were all `SELF_REPORTED`/`MODEL_MARGIN`/
`SCORE_NORMALIZED`-equivalent under the old schema), report this as an
explicit finding ("0 adapters expose a true probability estimate under v2
schema either") rather than silently falling back to computing ECE on
non-probability values.

### 1.4 Overconfidence flag

Bucketed rule from the pilot, unchanged: flag `(adapter, question,
horizon)` if `avg_confidence >= 0.75` and `hit_rate <= 0.55` and `n >= 10`.
Kept identical because it is a threshold rule, not a comparability claim —
unlike Brier/ECE it doesn't assume `value` is a probability, just that
higher stated confidence should correlate with higher hit rate regardless
of `kind`.

### 1.5 Stability (repeat-run variance)

For N independent repeat calls at the same `(adapter, ticker, as_of)`:
- Q1: proportion of repeats agreeing with the modal `action`.
- Q3: variance of `values`/`direction` sign-flip rate.
- Q4: mean pairwise L1 distance between `target_weights`/`initial_weights`
  vectors across repeats (weight drift).
Report N explicitly; N=1 (only one run exists) means stability is
`not_measured`, not `stable`.

### 1.6 Cross-Q / cross-field coherence score

Per adapter, per (ticker, date): count of internal contradictions between
its own Q1/Q2/Q3/Q4 outputs (e.g. Q2 negative sentiment state co-occurring
with Q1 BUY from the *same* adapter) divided by the count of adapters
answering ≥2 Qs for that (ticker, date) — only defined where an adapter
answers multiple Qs itself (per the Q-coverage matrix in
`EXPERIMENT_PROTOCOL.md` §2, that's `deepalpha, finrl_x, finrobot,
tradingagents, quantmuse, finagent, finclaw, qlib, vibe_trading`).

### 1.7 Contradiction severity and predictive power

Extends the pilot's binary rule-hit count (`contradiction_summary.csv`)
with two additions the pilot flagged as future work:
- **Severity**: a documented, non-fabricated weight per rule (e.g. rule
  magnitude scaled by how far the triggering field is from its threshold —
  `risk_level=EXTREME` scores higher severity than `HIGH` for the
  `BUY_WITH_HIGH_RISK`-equivalent rule), not a single flat "1 contradiction
  = 1 point" count. **Not yet fully specified** (self-review finding I4,
  `docs/research_reports/2026-07-19_experiment_protocol_self_review.md`):
  this document gives the one worked example above but does not fix a
  general formula for every rule — that is deliberately left to whoever
  implements D4's rulebook redesign (`EXPERIMENT_PROTOCOL.md` D4), since
  the concrete severity function depends on what replacement signal ends
  up standing in for each removed-Q5 rule. Do not implement D4 without
  first fixing this formula explicitly; do not silently default to a flat
  count in its absence.
- **Predictive power**: forward-return comparison between flagged and
  unflagged decisions at the same horizon (the pilot's own
  `fig_10_flagged_vs_unflagged_forward_returns.png` precedent) — with a
  significance test (§4), not just a visual comparison.
- **Rule redesign required**: the pilot's 8 rules reference `Q5Backtest`
  fields (`validation status`, `max_drawdown`) that no longer exist post
  schema v2.0.0. `EXPERIMENT_PROTOCOL.md` D4 owns the redesign; this
  document only fixes how severity/predictive-power are scored once rules
  are redefined.

### 1.8 Field coverage / compression loss

Fill-rate per field per Q (pilot's `field_coverage.csv` methodology,
reusable as-is since it's schema-introspective, not Q5-dependent), plus
evidence-atom unlock count (pilot's 12-category keyword tagging on
`explanation`/`evidence`/`bull_case`/`bear_case` — an explicitly coarse,
deterministic heuristic, not an NLU claim, same caveat the pilot already
stated in `PAPER_FINDINGS.md`).

### 1.9 Reliability profile (Layer 1's headline deliverable)

Not a new computation — a structured aggregation of 1.1–1.8 per
`(adapter, regime_label)` cell using `DATA_SPLIT_PROTOCOL.md` §4.1's
independent regime tags. This is the object Layer 2 (M2 routing) consumes;
define its schema here so M1–M4 have a stable interface:
`{adapter, regime, hit_rate, calibration_error, stability_score,
contradiction_rate, n}`. `n` must always be carried — a routing decision
based on a 3-sample regime cell is not the same claim as one based on 300.

---

## 2. Layer 2 / portfolio-level metrics

### 2.1 Return-based

Total return, annualized return (geometric, trading-day convention: 252),
Sharpe (annualized, using a documented, non-zero risk-free rate source —
not hardcoded to 0; recommend the same 3-month T-bill series used for any
`CASH` baseline in `BASELINE_DESIGN.md` §3.3, not fabricated), Sortino
(downside deviation only), max drawdown, Calmar (annualized return / |max
drawdown|), alpha vs. benchmark (`SPY`, OLS or simple excess-return alpha —
document which), CVaR at 95% and 99% (historical, not parametric, given
small-sample non-normality risk already evident in the pilot's 40-sample
fusion-ablation set).

**CVaR@99% sample-size caveat**: a ~12-month TEST window (`DATA_SPLIT_
PROTOCOL.md` §3.1) has on the order of ~230 trading days, and fewer
independent rebalance points for lower-frequency STEPWISE Q4 adapters — a
historical 99% CVaR from that many points is estimating a tail with only
~2-3 expected exceedances. Report CVaR@99% as directional-only (same
treatment as an n<10 calibration bucket in §1.2), never as a precise point
estimate driving a pass/fail claim on its own.

### 2.2 Risk/turnover/exposure

Gross exposure (`sum(|w_i|)`), net exposure (`sum(w_i)`), cash ratio,
concentration (Herfindahl-Hirschman index over `|w_i|`), turnover (`sum(|
Δw_i|)` per rebalance), transaction-cost-adjusted return (fixed bps-per-
turnover assumption, stated explicitly — recommend starting at 10bps
round-trip as a documented placeholder, swept as a sensitivity range, not
asserted as realistic for every asset class in the universe).

**Execution-class caveat (ties to `BASELINE_DESIGN.md` §3.4)**: turnover
and per-step drawdown are only computable for **STEPWISE** Q4 adapters that
produce a real per-step `PolicyDecisionStep` trajectory. For
**STATIC_ONLY** adapters (`agentictrading`, `finclaw`) there is one
allocation, so turnover after initialization is `0` by construction, not
`not_applicable` — but *trajectory-level* metrics (drawdown path, rolling
Sharpe) are `not_applicable`, only point-in-time metrics exist. For
`vibe_trading`'s `LEGACY_INTERNAL_LOOP` replay, trajectory metrics are
computable but must be labeled as replayed-not-regenerated, per
`DATA_SPLIT_PROTOCOL.md` §1.

### 2.3 Constraint compliance

`constraint_violations` count from `PolicyDecisionStep`/`Q4Policy` (already
a native schema field — read it, don't recompute it) — reported as a
pass/fail gate before trusting any other Q4 metric from that adapter/run,
since a policy violating its own declared constraints has a data-quality
problem upstream of performance measurement.

---

## 3. Cost model (shared across §2)

State once, reused everywhere a portfolio metric needs a cost assumption:
- Round-trip transaction cost: 10bps placeholder (sensitivity-swept at 5/10
  /25bps in Ro-family robustness checks).
- No slippage/market-impact model — flagged as a known simplification, not
  silently assumed away.
- No borrowing cost modeled for short positions even where
  `PortfolioConstraints.long_only=False` permits shorting — same
  simplification, flagged.

---

## 4. Statistical rigor (fixes the pilot's explicitly stated gap)

`EXPERIMENT_REPORT.md` §10 (pilot limitations) states plainly: "无统计显著性检验"
(no significance testing). This protocol does not repeat that gap:

- **Sharpe-ratio differences** between any method and any baseline: report
  via stationary/block bootstrap confidence intervals (block length ≥ the
  longest horizon used, 20 trading days) rather than a point-estimate
  difference alone. A Jobson-Korkie-style test (or its Ledoit-Wolf-corrected
  variant) is the preferred parametric alternative where sample size
  permits; state which was used.
- **Hit-rate differences** (majority vote vs. confidence-weighted vs.
  method-under-test): two-proportion test or bootstrap CI on the
  difference, not a bare percentage-point gap — the pilot's headline
  "60.7% vs 57.1%" comparison (`EXPERIMENT_REPORT.md` §8) is exactly the
  kind of claim that needs a CI before being called a real effect rather
  than 30-sample noise.
- **Multiple-comparison correction**: 26 adapters × several metrics ×
  several regime slices produces many simultaneous comparisons. Apply
  Benjamini-Hochberg FDR control (recommended over Bonferroni given the
  exploratory, hypothesis-generating nature of D1–D8) whenever ranking
  adapters or flagging "significant" findings across more than a handful of
  cells at once — most acutely in D5's regime-reliability ranking.
- **Report point estimate + CI + N together, always.** A metric without N
  is not trustworthy given how small several of the pilot's cells already
  were (n<10 in 28/39 calibration buckets) — this document treats that as
  a standing risk to guard against by convention, not a one-time note.

---

## 5. What NOT to compute (explicit non-goals)

- No metric may be computed by substituting a plausible-looking value when
  data is missing (CLAUDE.md §2). `insufficient_data` is a valid, expected
  metric value, not a failure of this design.
- No cross-adapter metric comparison may silently mix Class R and Class L
  adapters' differently-scoped windows (`DATA_SPLIT_PROTOCOL.md` §1) without
  stating the mismatch.
- No `kind`-unaware Brier/ECE (§0).
