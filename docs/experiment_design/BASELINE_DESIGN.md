# BASELINE_DESIGN.md

Status: design document. Defines reference comparators only — no adapter,
schema, harness, or Python code is modified by this document. Baseline
*implementations* are future engineering work; where an implementation
already exists informally (`analysis/icaif_fusion.py` from the pilot), this
document says so and flags what must change for schema v2.0.0.

Companion documents: `DATA_SPLIT_PROTOCOL.md` (defines the windows every
baseline below must be evaluated on), `METRIC_DESIGN.md` (defines how
baseline outputs are scored), `EXPERIMENT_PROTOCOL.md` (says which
experiment uses which baseline).

---

## 0. Fairness rules that apply to every baseline

A baseline that gets special treatment isn't a baseline, it's a straw man.
Every baseline below must:

1. **Obey the same causality constraints** as any method under test — only
   information at or before `data_cutoff`/`information_cutoff`, same
   CAL/VAL/TEST windows from `DATA_SPLIT_PROTOCOL.md`, same purge gaps.
2. **Use the same universe and cost model** as the method(s) it's compared
   against within one experiment (transaction-cost assumptions live in
   `METRIC_DESIGN.md` §3).
3. **Be selected/tuned only on CAL/VAL, never on TEST.** "Single best
   adapter" (§2.3) in particular is a trap here: the *identity* of the best
   adapter is itself a hyperparameter and must be chosen on VAL, then
   frozen before TEST — picking it in hindsight on TEST results would make
   this baseline look artificially strong.
4. **Report N and coverage honestly.** If a baseline can only be scored on
   a subset of the same (ticker, date) pairs a method under test uses
   (common for Class-L-dependent methods, per `DATA_SPLIT_PROTOCOL.md`
   §3.2), state the subset size — do not silently compare on mismatched
   samples.

---

## 1. Why "baseline" means two different things here

Layer 1 (diagnostic) experiments don't have baselines in the ML sense —
D1–D7 in `EXPERIMENT_PROTOCOL.md` are measurements, not predictions being
scored against a null model. Layer 1's only "baseline" is a **methodological
contrast**, listed in §4. Layer 2 (method) experiments are genuinely
predictive/allocation methods and need real baselines, listed in §2–3. Do
not force Layer 1 diagnostics through the §2–3 baseline machinery — that
was one of the framing risks flagged during self-review of this design (see
`EXPERIMENT_PROTOCOL.md` §7 for the review note).

---

## 2. Decision-fusion baselines (Q1/Q3 action/signal level)

Applies where multiple adapters answer the same (ticker, date) at Q1 and/or
Q3 and must be reduced to one tradable decision.

### 2.1 Majority vote

Map each adapter's `Q1Action.action` / `Q3Signal.direction` to
{-1, 0, +1}, sum, take the sign; ties → HOLD. No confidence, no risk, no
history used. This is deliberately the "dumbest fair" baseline — the pilot
found it *outperforming* the more elaborate confidence-weighted method
(60.7% vs 57.1% hit rate, `EXPERIMENT_REPORT.md` §8), which is exactly the
kind of counter-intuitive result this baseline exists to catch. Re-verify
under v2 schema/26 adapters rather than assuming the pilot's ranking still
holds.

### 2.2 Equal-weight fusion

Q4-analogue of 2.1 for portfolio weights: average `target_weights`/
`initial_weights` across all Q4-answering adapters with a valid decision at
that date, renormalized. Distinct from 3.3's 1/N-over-tickers baseline —
this is 1/N *over adapters*, not over assets.

### 2.3 Single best adapter (per-Q)

For each of Q1/Q2/Q3/Q4 separately: the one adapter with the best VAL-window
performance on that Q's primary metric (hit rate for Q1/Q3, calibration
error for confidence-bearing Qs, Sharpe for Q4), frozen before TEST. Must
report *which* adapter was selected and why, every time it's re-run — the
identity is expected to be unstable across CAL/VAL refreshes and that
instability is itself informative (ties to D3 stability findings).

**Winner's-curse caveat**: with 6-13 candidate adapters per Q and VAL
samples already known to be small in places (pilot precedent: 28/39
calibration buckets had n<10), the adapter selected as "best on VAL" is
expected, by construction, to score somewhat worse on TEST than its own
VAL number — a standard selection-on-noisy-data regression-to-the-mean
effect, not evidence of degradation or of the TEST-window method being
unusually strong by comparison. Report both the VAL score that earned the
selection and the TEST score achieved, side by side, so the gap is visible
rather than implicitly treated as surprising.

### 2.4 Confidence-weighted vote

Weight each adapter's {-1,0,+1} vote by its `ConfidenceEstimate.value`
(missing → 0.5), average, threshold at ±0.25 (reuses the pilot's threshold
convention, `icaif_fusion.py`). **Explicit caveat inherited from the
pilot's D2 finding**: this baseline is only a legitimate weighting if the
raw `value` field means the same thing across adapters — it usually doesn't
(seven mutually incompatible mechanisms found in the pilot, see
`EXPERIMENT_QA_NOTES.md`). Schema v2 gives this baseline a genuinely new
option the pilot didn't have: gate the weighting by `ConfidenceEstimate.
kind` (§0 of `METRIC_DESIGN.md` explains why) — report both the naive
raw-value-weighted variant (kept for continuity with the pilot) and a
kind-aware variant (weight only `PROBABILITY`/`MODEL_MARGIN` kinds at face
value; treat `SELF_REPORTED`/`HEURISTIC`/`SCORE_NORMALIZED` as needing D2's
calibration correction before use). This split is itself informative for
D2/M2, not just a baseline nicety.

### 2.5 Reliability-aware fusion — NOT a baseline

`M2` (reliability-aware routing/weighting) in `EXPERIMENT_PROTOCOL.md` is
the method under test, built on top of 2.4 by adding D2's calibration
correction — do not list it here as a baseline for itself.

---

## 3. Portfolio-level baselines (Q4 / final allocation)

### 3.1 Buy-and-hold

Two variants, both must be reported:
- **Per-ticker buy-and-hold**: hold each universe ticker alone from the
  window's start, unrebalanced. Used for per-asset context, not a
  portfolio comparator by itself.
- **Equal-weight-at-start buy-and-hold**: invest 1/N across the full
  universe (`DATA_SPLIT_PROTOCOL.md` §2.1's 10+2 set) at window start, no
  rebalancing thereafter. This is the actual Q4 comparator.

### 3.2 Volatility-target / naive risk baseline

Scale a fixed reference portfolio (e.g. equal-weight universe) so trailing
20-day realized volatility matches a fixed annualized target (e.g. 10%),
rebalanced on the same cadence as the Q4 methods under test. This is
"risk-aware but not reliability-aware" — it exists to separate "does the
method just manage volatility well" from "does the method use Layer 1
reliability information well," which is the actual research question.

### 3.3 Cash / risk-free baseline

100% CASH held for the window. Establishes the floor — any method or other
baseline that can't beat this after transaction costs on a risk-adjusted
basis is not adding value, full stop.

### 3.4 Single best Q4 policy baseline

Analogue of §2.3 restricted to the 13 Q4-answering adapters
(`agentictrading, deepdow, earnmore, finagent, finclaw, finrl, finrl_x,
pgportfolio, qlib, skfolio, trademaster, universal_portfolios,
vibe_trading`), selected on VAL by Sharpe, frozen before TEST. Must record
which adapter's **execution class** it used (STEPWISE/STATIC_ONLY/
LEGACY_INTERNAL_LOOP per `q4_stepwise_support.csv`) since that changes what
trajectory-level metrics (turnover, per-step drawdown) are even computable
— see `METRIC_DESIGN.md` §2.2 caveat. Same winner's-curse caveat as §2.3
applies (13 candidates, VAL-selected, expect TEST regression toward the
mean — report VAL and TEST scores side by side).

### 3.5 1/N naive diversification

Equal-weight across whatever Q4 adapters are online-adaptive at each
rebalance point (distinguishes from 3.1's static equal-weight-at-start: this
one *rebalances* to 1/N over adapters' current outputs each step, so it's
the Q4-trajectory analogue of §2.2).

---

## 4. Layer 1 methodological contrasts (not scored baselines)

These exist only inside diagnostic experiments (`EXPERIMENT_PROTOCOL.md`
D1–D7), to falsify a specific naive assumption, not to be beaten on a
leaderboard:

| Contrast | Falsifies the assumption that... | Used in |
|---|---|---|
| Headline-only fields vs. full interwoven fields | ...action/sentiment_score/direction alone carries all decision-relevant information | D1, D4 |
| Declared `questions_answered` vs. statically-implemented vs. actually-observed capability | ...an adapter's self-declared capability is trustworthy without verification | D1 |
| Raw self-reported `confidence.value` vs. `kind`-gated / calibration-corrected value | ...all `ConfidenceEstimate.value` fields are comparable at face value | D2, feeds 2.4 |
| Single-run output vs. N-repeat distribution | ...an adapter's output on a given (ticker, date) is deterministic | D3 |
| Per-adapter Q2/Q4 regime label vs. the independent SPY-derived regime tag (`DATA_SPLIT_PROTOCOL.md` §4.1) | ...an adapter's self-reported market-state estimate is ground truth | D5, D8-equivalent in D4 |

---

## 5. Ablation arms (not baselines, but defined here for cross-reference)

The information-pathway ablation (A1 in `EXPERIMENT_PROTOCOL.md`) runs the
*same* fusion method (whichever M-method passed `result-to-claim`) with
restricted input: Q1-only, Q3-only, Q1+Q3, Q1+Q2+Q3, Q4-only, all-Q, each
with/without confidence and with/without evidence fields. These are
experimental arms of a single method, not independent baselines — do not
double-count them against the §2–3 baseline bank when reporting effect
sizes; the comparator for an ablation arm is the full-information arm of
the *same* method, not majority-vote.

---

## 6. Existing implementation status (informational, not a task list)

`analysis/icaif_fusion.py` already implements §2.1/§2.4 and an
"interwoven_calibrated_fusion" variant for the v1/Q5 schema and 15-adapter
set. It cannot be reused as-is for v2: it reads `Q5Backtest.validation`
fields (`validation_multiplier`) that no longer exist post schema v2.0.0
(Q5 removed). Rebuilding a v2-compatible fusion module is future
engineering work, out of scope for this design document (CLAUDE.md
forbids Python changes under this task) — flagged here so whoever picks up
M1–M4 implementation knows the pilot code is precedent, not a drop-in
dependency.
