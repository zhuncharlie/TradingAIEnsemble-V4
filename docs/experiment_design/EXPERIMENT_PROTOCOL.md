# EXPERIMENT_PROTOCOL.md

**Status**: formal experiment design document for `trading-ai-ensemble`.
**Author role**: experiment designer only, per this task's brief — this
document and its three companions (`DATA_SPLIT_PROTOCOL.md`,
`BASELINE_DESIGN.md`, `METRIC_DESIGN.md`, all in this directory) do not
modify adapters, `CONTRACT/`, `harness/`, or any Python code. Every
concrete fact cited below (adapter names, Q-coverage, schema fields,
runnability status) was verified against the current repo state during
this design pass, not assumed from memory or from stale documentation.

---

## 1. Research framing (recap, not redefinition)

Per `CLAUDE.md` and the task brief: the object of study is **not** "which
AI trading system predicts best." It is: how to turn a large set of
heterogeneous, independently-authored financial AI systems into a unified,
auditable information source, and whether *reliability- and
consistency-aware* use of that information source improves final decision
quality (risk-adjusted return, drawdown, tail risk) beyond naive ensembling.

Two layers, in a strict producer/consumer relationship:

```
Raw adapters (26, schema v2.0.0, Q1-Q4)
      |
      v
Canonical Q1-Q4 outputs  ---------------------------
      |                                             |
      v                                             |
Layer 1 — reliability / calibration / stability /    |
          contradiction / compression-loss features  |
      |                                             |
      v                                             |
Layer 2 — routing / intervention / selective          <---- (raw Q1-Q4
          prediction / shadow-policy / meta-fusion            also feeds
      |                                                       Layer 2
      v                                                       directly)
Final portfolio decision
```

Layer 2 always consumes **both** Layer 1's derived features and the raw
Q1-Q4 outputs — never Layer 1 features alone — matching the brief's
explicit diagram.

---

## 2. Ground truth used to design this protocol (verified this session)

- **Schema**: `CONTRACT/schemas.py`, `SCHEMA_VERSION = "2.0.0"`. Four
  questions only — **Q5 (Backtest) was removed** in the v1→v2 rewrite
  (`milestones/2026-07-16_schema-v1-milestone.md` is the v1 rollback
  point). This matters: the pilot study below built several mechanisms
  (contradiction rules, fusion validation-multiplier) directly on
  `Q5Backtest` fields that no longer exist.
- **Adapters**: 26 real production adapters under `adapters/*.py`
  (`example_stub_adapter.py` excluded as the non-deliverable reference
  stub, per `analysis/icaif_data_loader.py`'s own exclusion convention).
  Verified Q-coverage by scanning for real (non-stub) `q1_action`/
  `q2_state`/`q3_signal`/`q4_policy`/`q4_initialize`/`q4_step` overrides:

  | Q | Adapters (count) |
  |---|---|
  | Q1 Action | `ai_hedge_fund, deepalpha, finagent, finmem, finrobot, tradingagents` (6) |
  | Q2 State | `finbert, fingpt, finrl_x, finrobot, prediction_arena, quantmuse, tradingagents` (7) |
  | Q3 Signal | `alphaforge, alphagen, atlas, deepalpha, finclaw, finrl_x, qlib, quantmuse, rdagent, vibe_trading` (10) |
  | Q4 Policy | `agentictrading, deepdow, earnmore, finagent, finclaw, finrl, finrl_x, pgportfolio, qlib, skfolio, trademaster, universal_portfolios, vibe_trading` (13) |

  Coverage is uneven (Q4 has more than 2× Q1/Q2's density) — echoes, but
  does not simply repeat, the pilot's "Q3 is 2.7× Q1/Q4" finding under the
  old 15-adapter/Q1-Q5 set; **D1 below must re-measure this from scratch**,
  not assume the old ratio transfers.
- **Runnability** (`results/unified_harness/unified_harness_summary.json`,
  run `2026-07-18`, `as_of=2024-01-15`, universe `AAPL/MSFT/NVDA`): 21/26
  `PASSED`, 3 `FAILED` (`fingpt` — env error; `tradingagents`, `finagent` —
  280s timeout, both LLM-latency-bound), 2 `BLOCKED` (`finmem` — needs an
  OpenAI-compatible credential for embeddings; `pgportfolio` — live
  `yfinance` rate limit on crypto pair, transient/external). Any experiment
  requiring all 26 adapters online simultaneously will hit this ceiling —
  design experiments to degrade gracefully to the 21 currently-passing
  adapters and report the gap, not silently drop failing adapters from the
  denominator.
- **Q4 execution taxonomy** (`q4_stepwise_support.csv`): 10 adapters are
  true `STEPWISE` (causal per-step trajectory), 2 are `STATIC_ONLY`
  (`agentictrading`, `finclaw` — one-shot, no trajectory to evaluate),
  `vibe_trading` is `STEPWISE_UNSUPPORTED` served via `LEGACY_INTERNAL_LOOP`
  replay. This taxonomy gates which portfolio metrics are even computable
  per adapter — detailed in `METRIC_DESIGN.md` §2.2, must not be ignored
  when comparing Q4 adapters head-to-head.
- **Data**: `yfinance` (already the project's price provider) confirmed
  capable of 10 years of daily history for the existing liquid-ticker
  universe (2016-07-18 → 2026-07-17, verified live this session). The
  configured `massive.com` MCP (`mcp__massive__*`) was also probed live:
  its current plan returns real daily aggregates only back to ~2024-07-19
  and gives `HTTP 403 NOT_AUTHORIZED — "Your plan doesn't include this
  data timeframe"` for anything earlier. **10 years of price data is
  achievable now via `yfinance`; the massive.com plan upgrade the user
  offered to configure is not required for this purpose** — it would still
  be useful for data `yfinance` doesn't have (options, point-in-time news,
  fundamentals), which is a separate, real gap documented in
  `DATA_SPLIT_PROTOCOL.md` §1 (it's exactly what would let Class-L/
  news-dependent adapters be replayed historically, which they currently
  cannot be). Full detail and the adapter replay-class split this drives:
  `DATA_SPLIT_PROTOCOL.md` §§1–3.

---

## 3. Relationship to the pilot study (`reports/icaif_experiments/`)

An informal 5-experiment pilot already ran, against the **v1 schema
(Q1-Q5) and 15 adapters**, producing real findings this protocol treats as
informative precedent, not as reusable ground truth or as pre-existing TEST
results:

- Confirmed structurally: all systems fit the Q-taxonomy; coverage is
  uneven; most secondary fields are well-filled except `bull_case`/
  `bear_case`; self-reported confidence is 7 mutually incompatible
  measurement mechanisms, none calibrated; 129 real cross-adapter
  contradictions were detected and were invisible to headline-only
  comparison; naive confidence-weighted fusion *underperformed* plain
  majority vote (57.1% vs 60.7% hit rate), traced to one miscalibrated
  high-confidence adapter (`deepalpha`) dominating the weighted average.
- Self-reported limitations this protocol is explicitly designed to close:
  no significance testing (`METRIC_DESIGN.md` §4), small samples (`DATA_
  SPLIT_PROTOCOL.md`'s regime/shared-window design exists partly to grow
  this), `Q4`/`Q5` alignment done via best-effort `task_id` join for 37% of
  contradiction cases (moot for `Q5`-based rules since `Q5` no longer
  exists; `D4` below must redesign around this rather than inherit it),
  and calibration reliability not yet folded into the fusion weight (this
  is literally what `M2` below exists to fix).
- **Not reusable as-is**: the pilot's contradiction rulebook (8 rules) and
  fusion module (`analysis/icaif_fusion.py`) reference `Q5Backtest` fields
  that were removed in schema v2.0.0. `D4` and `M1`–`M4` below must
  redesign, not port, these mechanisms. Flagged in detail in
  `BASELINE_DESIGN.md` §6.

---

## 4. Experiment taxonomy

Sixteen candidate experiments were supplied in the task brief (Exp1–Exp16).
Per the brief's own instruction not to leave these as 16 disjoint items,
they are consolidated into four families below. Every experiment specifies:
**Hypothesis / Method / Baseline / Data window / Metric / Expected result /
Failure interpretation**. "Baseline" and "Metric" reference
`BASELINE_DESIGN.md` and `METRIC_DESIGN.md` by section rather than
redefining them here.

### Family D — Diagnostic (Layer 1: what is actually true about the data/adapters)

#### D1. Coverage, Declaration Integrity & Compression Audit
- **Hypothesis**: (a) is a **sanity check, not a real finding** — every
  file under `adapters/*.py` was written specifically to implement
  `BaseAdapter`'s Q1-Q4 methods, so "the taxonomy covers all 26 adapters"
  is close to true by construction; D1 reports it but does not treat a
  positive result as evidence of anything beyond "the contract was
  followed." The actual testable hypotheses are: (b) declared
  (`questions_answered`) vs. statically-implemented vs. actually-observed
  capability disagree in practice (this can genuinely fail either way);
  (c) headline-field-only comparison discards recoverable, non-trivial
  information (also genuinely falsifiable).
- **Method**: reuse-and-extend `analysis/icaif_data_loader.py`'s AST-scan
  + result-JSON cross-check methodology (schema-introspective, not
  Q5-dependent, so it survives the v1→v2 migration largely intact) against
  all 26 adapters. Compute field fill-rate (`METRIC_DESIGN.md` §1.8) and
  evidence-atom unlock count per Q.
- **Baseline**: `BASELINE_DESIGN.md` §4 (headline-only vs. interwoven;
  declared vs. observed) — methodological contrasts, not scored baselines.
- **Data window**: all available Plane-B decisions to date across both
  adapter classes (`DATA_SPLIT_PROTOCOL.md` §2.2) — this is inventory, not
  a held-out evaluation, so CAL/VAL/TEST boundaries don't apply.
- **Metric**: `METRIC_DESIGN.md` §1.8.
- **Expected result**: 100% structural coverage (every adapter maps onto
  ≥1 Q) holds again, per the pilot's finding and the pattern of schema
  design; coverage density ratio across Q1-Q4 is *not* assumed to match
  the pilot's 2.7× and must be re-measured fresh (Q4 is now the largest
  category by adapter count, unlike the pilot's Q3-heavy 15-adapter set —
  a genuinely different distribution is plausible and would itself be a
  finding).
- **Failure interpretation**: if declared/implemented/observed disagree
  for a nontrivial fraction of adapters, that is not a failed experiment —
  it is the primary intended finding (as it was in the pilot, which found
  0 mismatches only after tightening its own scan logic); report exact
  mismatch list per `coverage_audit_findings.csv`-equivalent output, do not
  suppress it because it's inconvenient.

#### D2. Confidence Semantics & Calibration Audit
- **Hypothesis**: (a) `ConfidenceEstimate.kind` is populated meaningfully
  and distinguishes genuinely different measurement mechanisms (as it was
  designed to, post-pilot); (b) regardless of `kind`, self-reported
  confidence/strength values do not reliably predict forward-return hit
  rate; (c) at least one adapter is measurably overconfident.
- **Method**: two sub-steps, both mandatory and in order: **D2a** — audit
  whether `kind` is populated and whether its value is defensible given
  each adapter's actual computation (source-level check, as the pilot did
  by hand for 9 adapters — extend to all confidence/strength-bearing
  adapters across all 26). **D2b** — bucketed calibration
  (`METRIC_DESIGN.md` §1.2), ECE/Brier only where `kind=PROBABILITY`
  (§1.3), overconfidence flagging (§1.4).
- **Baseline**: `BASELINE_DESIGN.md` §4 row 3 (raw value vs. kind-gated
  value).
- **Data window**: CAL window per adapter class (`DATA_SPLIT_PROTOCOL.md`
  §3.1/§3.2) — this experiment's output (the reliability profile,
  `METRIC_DESIGN.md` §1.9) is exactly what CAL is for.
- **Metric**: `METRIC_DESIGN.md` §§1.2–1.4, §0.
- **Expected result**: `kind` diversity persists (multiple mechanisms
  remain genuinely different even when labeled); calibration error
  remains material for most non-`PROBABILITY` adapters, consistent with
  pilot direction; at least the pilot's flagged case (`deepalpha` Q1,
  high-confidence/low-hit-rate) either replicates or is shown to have been
  fixed by the recovered `confidence_interval` field noted in
  `ADAPTER_CAPABILITY_RECOVERY.md`.
- **Failure interpretation**: if `kind=PROBABILITY` is never populated
  honestly by any adapter, that is a valid, reportable finding (schema
  provides the mechanism, adapters don't yet use it) — not a reason to
  compute ECE on non-probability values anyway.

#### D3. Stability & Determinism Audit
- **Hypothesis**: at least one adapter exhibits materially non-deterministic
  output on repeated calls at identical `(ticker, as_of)`, and this is
  traceable to a specific, reportable root cause (as the pilot found for
  `deepalpha`'s uncached, unseeded ensemble retraining).
- **Method**: N≥5 repeat calls per `(adapter, ticker, as_of)` for a
  sampled subset of Class-R adapters (repeat calls are cheap and honest
  only for Class R — Class L repeat calls against "today" are not
  repeats of the same information state, so D3 is Class-R-scoped by
  construction).
- **Baseline**: `BASELINE_DESIGN.md` §4 row 4.
- **Data window**: any single CAL-window date per adapter, repeated.
- **Metric**: `METRIC_DESIGN.md` §1.5.
- **Expected result**: most Class-R adapters are near-deterministic (fixed
  seeds / no retraining per call, per `q4_stepwise_support.csv`'s
  "frozen"/"no retraining" annotations for `deepdow`, `earnmore`, `qlib`,
  `trademaster`, `finrl`, `finrl_x`); any adapter that retrains per-call
  without a fixed seed is flagged by name with root cause, matching the
  `deepalpha` precedent.
- **Failure interpretation**: universal determinism (0 instability found)
  would be a genuine, reportable, mildly surprising result given the
  pilot's finding — verify the repeat-call harness itself is actually
  invoking a fresh process/state before trusting a "stable" result over an
  artifact of accidental caching.

#### D4. Cross-Field & Cross-Q Contradiction Detection (rulebook redesign required)
- **Hypothesis**: real, detectable contradictions exist across and within
  adapters under the v2 (Q1-Q4-only) schema; contradiction flags carry
  predictive power (flagged decisions underperform unflagged ones at the
  same horizon).
- **Method**: redesign the pilot's 8-rule rulebook to remove all `Q5`
  dependencies. Concrete mapping: rules keyed on Q1/Q2/Q3 pairs (`BUY_WITH_
  HIGH_RISK`, `ACTION_ALPHA_DIRECTION_CONFLICT`, `POSITIVE_SENTIMENT_BEAR_
  REGIME`, `HIGH_CONFIDENCE_POOR_CALIBRATION` fed by D2's output) port
  directly; rules keyed on `Q5Backtest.validation`/`max_drawdown`
  (`LONG_WITH_WEAK_VALIDATION`, `HIGH_WEIGHT_HIGH_DRAWDOWN`) need a
  replacement signal — candidates: `Q4Policy.constraints`/
  `constraint_violations` (native v2 field, `METRIC_DESIGN.md` §2.3) for a
  drawdown-adjacent risk signal, and D2's own calibration-flag output as
  the "weak validation" replacement (an adapter's own poor calibration
  standing in for the missing backtest-validation status). This
  substitution must be stated explicitly wherever used, not silently
  presented as equivalent to the original rule.
- **Baseline**: `BASELINE_DESIGN.md` §4 row 5 (adapter-reported regime vs.
  independent SPY-derived regime tag) feeds the redesigned
  `POSITIVE_SENTIMENT_BEAR_REGIME`-equivalent rule.
- **Data window**: shared recent window (`DATA_SPLIT_PROTOCOL.md` §3.3)
  for exact-join rules; full per-class CAL/VAL windows for best-effort
  `task_id`-joined rules.
- **Metric**: `METRIC_DESIGN.md` §1.6–1.7, significance test per §4.
- **Expected result**: contradictions continue to concentrate on adapters
  answering multiple Qs (structurally more opportunities to self-conflict)
  — re-verify rather than assume `deepalpha` remains the top offender,
  since the adapter set and its instrumentation have both changed since
  the pilot.
- **Failure interpretation**: `0` cases for a given rule is not evidence
  the rule is broken (the pilot already saw this for
  `POSITIVE_SENTIMENT_BEAR_REGIME`, because no `BEAR` regime ever appeared
  in that sample) — report `0`-count rules with the reason (no
  triggering state observed vs. rule genuinely never fires) rather than
  dropping them silently.

#### D5. Regime & Market-State Reliability Profiling
- **Hypothesis**: adapter reliability (hit rate, calibration, contradiction
  rate) is regime-dependent — some adapters are reliable in trending
  markets and not in choppy ones, or vice versa. D5 tests only this
  descriptive claim; it does not test whether the pattern is exploitable —
  that is `M2`'s hypothesis, kept separate here so the two experiments'
  falsifiability boundaries don't blur (a positive D5 result motivates
  running `M2`, it does not substitute for it). Directly answers the
  brief's explicit ask: "测试不同市场（或市场情绪）下，哪些adapters表现较好".
- **Method**: slice D1–D4's outputs by the independent regime tag
  (`DATA_SPLIT_PROTOCOL.md` §4.1), build the `(adapter, regime)`
  reliability-profile table (`METRIC_DESIGN.md` §1.9).
- **Baseline**: none — this is a measurement, ranked against itself across
  regimes, not against an external baseline.
- **Data window**: full CAL+VAL history per class, sliced by regime;
  small-`n` regime cells reported honestly (§4 FDR correction applies when
  ranking across many regime×adapter cells at once).
- **Metric**: `METRIC_DESIGN.md` §1.9, FDR-corrected ranking per §4.
- **Expected result**: at least a partial regime-dependent ranking shift
  (i.e., not the same top-3 adapters in every regime) — this is the
  minimum finding needed to justify `M2` (reliability-aware routing) as
  more than a re-statement of "just use the globally best adapter."
- **Failure interpretation**: if reliability ranking is regime-invariant
  (same ordering everywhere), that is a real, negative, reportable result
  for `M2`'s premise — `M2` would then reduce to `BASELINE_DESIGN.md` §2.3
  (single best adapter) and should be reported as such, not forced to look
  more sophisticated than it is.

#### D6. Risk, Exposure & Native Policy Validation Audit
- **Hypothesis**: (a) Q4 adapters differ materially in realized gross/net
  exposure, concentration, and turnover even when nominally similar in
  stated `PortfolioConstraints`; (b) Q4 adapters differ materially in
  native (un-fused) risk-adjusted performance — this half directly answers
  the brief's **Exp4 Policy Validation** ask (total/annualized return,
  Sharpe, Sortino, max drawdown, Calmar, alpha, per adapter, on its own,
  independent of any fusion or baseline-selection purpose). Folded into D6
  rather than kept as a separate experiment per the brief's own
  instruction not to leave 16 disjoint items — but given its own explicit
  hypothesis/output here so it isn't only a silent byproduct of `M1`'s
  baseline-selection step.
- **Method**: compute `METRIC_DESIGN.md` §2.1 (return-based) **and**
  §2.2–2.3 (risk/turnover/constraint-compliance) directly from
  `Q4Policy`/`PolicyDecisionStep` native fields (no derivation needed
  beyond what the schema already carries) across all 13 Q4-answering
  adapters, gated by execution class (§2 above). Report as a per-adapter
  leaderboard, not only as an intermediate input to `BASELINE_DESIGN.md`
  §3.4's single-best selection.
- **Baseline**: `BASELINE_DESIGN.md` §3 (buy-and-hold, vol-target, cash,
  single-best) for context, not as something D6 itself must "beat" — D6 is
  descriptive.
- **Data window**: full CAL+VAL per adapter's reachable window.
- **Metric**: `METRIC_DESIGN.md` §2.1–2.3.
- **Expected result**: `STATIC_ONLY` adapters show trivially-zero turnover
  by construction (not a finding, a definitional fact — must be labeled as
  such, not reported as "low turnover = good").
- **Failure interpretation**: any adapter with recorded
  `constraint_violations` invalidates its other metrics for that run until
  investigated — treat as a data-quality gate, not a performance data
  point to average in.

#### D7. Abstention / Low-Reliability Behavior Audit
- **Hypothesis**: adapters do not currently exhibit systematic abstention
  behavior (HOLD-heavy or cash-heavy output correlating with genuinely
  lower-confidence or lower-reliability states) — i.e., there is headroom
  for `M3`/explicit intervention to add value beyond what adapters already
  do on their own.
- **Method**: correlate D2's per-decision calibration standing with
  HOLD/NEUTRAL/cash-weight frequency, per adapter.
- **Baseline**: `BASELINE_DESIGN.md` §2.1/§3.3 (majority vote, cash) as
  reference points for "what abstention would look like if applied."
- **Data window**: CAL+VAL.
- **Metric**: correlation coefficient (with CI, per §4) between D2's
  calibration flag and abstention-like output frequency.
- **Expected result**: weak-to-no existing correlation (adapters don't
  self-modulate based on reliability) — this is what justifies building
  `M3` at all.
- **Failure interpretation**: a strong existing correlation would mean
  some adapters already self-abstain effectively — reportable as a
  positive finding about that specific adapter, and grounds to scope `M3`
  down to the adapters that don't already do this, rather than applying it
  uniformly.

### Family M — Method (Layer 2: does using Layer 1 improve decisions)

#### M1. Baseline Fusion Bench
- **Hypothesis**: none (this experiment exists to produce numbers, not test
  one) — establishes what every M2–M4 method must beat.
- **Method**: run all of `BASELINE_DESIGN.md` §2–3 under identical
  causality/window/cost rules.
- **Baseline**: is the baseline bank itself.
- **Data window**: VAL (iteration) then TEST (final report), per
  `DATA_SPLIT_PROTOCOL.md` §3.
- **Metric**: `METRIC_DESIGN.md` §§1.1, 2.1–2.3, §4.
- **Expected result**: replicates the pilot's direction (naive majority
  vote competitive with or better than naive confidence-weighting) as a
  sanity check that the harness is behaving consistently pre/post schema
  migration — a large unexplained deviation from pilot direction here
  would be a signal to debug the harness before trusting M2–M4.
- **Failure interpretation**: if this bench cannot be run to completion
  (e.g. too many Class-L adapters unavailable per the 5/26 currently
  failing/blocked), report the achieved coverage (e.g. "bench run on 21/26
  adapters, `fingpt`/`finmem`/`tradingagents`/`finagent`/`pgportfolio`
  excluded, reasons stated") rather than blocking the whole protocol on
  100% adapter availability.

#### M2. Reliability-Aware Routing & Weighting
- **Hypothesis**: weighting/selecting adapters by D5's regime-conditioned
  reliability profile (rather than global confidence-weighting) beats both
  M1's confidence-weighted baseline and majority vote — this is the
  specific fix the pilot identified as its "missing fifth dimension."
- **Method**: fold D2's calibration reliability and D5's regime-conditioned
  hit rate into the fusion weight (formalized replacement for the pilot's
  `interwoven_calibrated_fusion`, which had risk/validation/contradiction/
  evidence multipliers but no calibration-reliability term).
- **Baseline**: `BASELINE_DESIGN.md` §2.1–§2.4 + M1's numbers.
- **Data window**: fit on CAL, threshold/weight selection on VAL, single
  evaluation on TEST.
- **Metric**: `METRIC_DESIGN.md` §§1.1, 2.1, §4 (must beat M1's best
  baseline with a statistically defensible margin, not just a point
  estimate).
- **Expected result**: hit rate and/or Sharpe improvement over M1's best
  baseline, driven specifically by down-weighting the regime-and-
  calibration-flagged adapter(s) that dominated the pilot's negative
  result (`deepalpha`-equivalent case, re-verified not assumed).
- **Failure interpretation**: if M2 does not beat M1, the mechanism must be
  diagnosed (which specific weight/adapter drove the shortfall — same
  case-study depth the pilot applied to its own negative result on
  `interwoven_calibrated_fusion`, e.g. `EXPERIMENT_REPORT.md` §8's
  GLD/2026-06-08 trace) — a negative M2 result reported without a
  mechanism trace does not meet this protocol's bar.

#### M3. Contradiction-Aware Intervention
- **Hypothesis**: applying D4's contradiction flags as an intervention
  trigger (abstain / reduce position / hold cash / down-weight the
  flagged adapter) improves risk-adjusted return (lower drawdown/CVaR,
  even if raw return is flat or slightly lower) versus M1/M2 without
  intervention.
- **Method**: wrap M2 (or M1's best baseline if M2 underperforms) with a
  D4-triggered intervention rule; report both with- and without-
  intervention variants side by side.
- **Baseline**: M1, M2 (this is explicitly an ablation-style A/B against
  the method it's layered on, not a from-scratch comparison).
- **Data window**: VAL for the intervention rule's threshold, TEST once.
- **Metric**: `METRIC_DESIGN.md` §2.1 (Sortino/Calmar/CVaR weighted more
  heavily than raw Sharpe here, since the hypothesis is about risk
  reduction specifically), §4.
- **Expected result**: measurable CVaR/max-drawdown improvement, plausibly
  at some raw-return cost (an intervention that abstains sometimes gives
  up some upside) — report the trade-off explicitly, don't cherry-pick
  whichever metric looks better.
- **Failure interpretation**: intervention that reduces both risk and
  return with no favorable trade-off anywhere is a valid negative result —
  report the threshold sensitivity (was it too aggressive?) before
  discarding the mechanism outright.

#### M4. Multi-View Meta-Fusion / Shadow Q4 Construction
- **Hypothesis**: a learned combination of raw Q1-Q4 outputs plus D1–D7
  Layer 1 features outperforms any hand-specified rule from M1–M3.
- **Method**: construct a shadow Q4 policy per the brief's explicit
  decomposition (Q1 → selection, Q3 → ranking, Q2 → risk adjustment),
  fit a meta-fusion mapping `[Q1..Q4, D1..D7 features] → decision` on
  CAL, select architecture/hyperparameters on VAL, evaluate once on TEST.
  This is the most ambitious experiment in the protocol and the most
  exposed to overfitting given the sample sizes documented in `DATA_SPLIT_
  PROTOCOL.md` — keep the model class simple (linear/logistic combination
  or shallow tree over engineered features) unless VAL-window sample size
  genuinely supports more capacity.
- **Baseline**: M1, M2, M3, all evaluated identically.
- **Data window**: strict CAL/VAL/TEST separation, single TEST evaluation
  — this is the experiment most at risk of test-tuning if run casually;
  `DATA_SPLIT_PROTOCOL.md` §5's embargo rule is non-negotiable here.
- **Metric**: full `METRIC_DESIGN.md` §2 suite, §4 significance testing
  mandatory (this is the headline result candidate for any eventual paper
  claim, so it is exactly what `result-to-claim` (§6 below) must gate).
- **Expected result**: modest but real improvement over M2/M3 if the
  Layer 1 features genuinely carry incremental information beyond what
  M2's simpler reliability weighting already captures; a *lack* of
  improvement over M2/M3 alone is scientifically interesting (Layer 1
  richer features may be redundant with the simpler reliability signal).
- **Failure interpretation**: if M4 outperforms only on VAL and not on
  TEST, that is overfitting, reported as such, not laundered into "M4
  needs more tuning" (which would just be test-tuning by another name).

### Family A — Ablation

#### A1. Information Pathway Ablation
- **Hypothesis**: performance degrades monotonically (or near-monotonically)
  as informational pathways are removed from the winning M-method, i.e.
  the richer Q2/Q4/evidence/confidence information genuinely earns its
  keep rather than being decorative.
- **Method**: re-run the winning method from M1–M4 (whichever passes
  `result-to-claim`, §6) restricted to: Q1-only, Q3-only, Q1+Q3,
  Q1+Q2+Q3, Q4-only, all-Q; each with/without confidence, with/without
  evidence fields. Use the `ablation-planner` skill (§6) to structure the
  run matrix once the base method is fixed — do not hand-run this ad hoc.
- **Baseline**: the full-information arm of the *same* method
  (`BASELINE_DESIGN.md` §5 — explicitly not compared against §2–3's
  baseline bank).
- **Data window**: TEST, reusing the exact split the winning method was
  frozen on (no new tuning).
- **Metric**: same metric(s) the winning method was selected on, §4
  significance applied to each pairwise pathway comparison with FDR
  correction (many comparisons at once).
- **Expected result**: `all-Q` ≥ `Q1+Q2+Q3` ≥ `{Q1+Q3, Q1-only, Q3-only}`,
  with `Q4-only` incomparable (different task) rather than ranked in the
  same list.
- **Failure interpretation**: non-monotonic results (e.g. `Q1+Q3` beating
  `all-Q`) are informative, not a bug — would indicate some included
  pathway is net-harmful (adding noise) rather than merely
  low-information, worth its own follow-up rather than being averaged away.

#### A2. Layer 1 Feature Ablation
- **Hypothesis**: M2–M4's improvement over M1 is attributable to specific
  Layer 1 features (calibration reliability, contradiction flags,
  stability score), not all equally — directly answers the brief's "哪些字段
  真正有价值" question at the Layer-1-feature level rather than the raw-field
  level (that's A1's job).
- **Method**: leave-one-feature-out re-runs of the winning M2–M4 method,
  removing calibration-reliability, contradiction-flags, or
  stability-score one at a time.
- **Baseline**: the full-feature arm of the same method.
- **Data window**: TEST, same frozen split as A1.
- **Metric**: same as A1, per-feature attribution via performance delta.
- **Expected result**: calibration-reliability is load-bearing (it's the
  specific gap the pilot identified and M2 was built to close) —
  contradiction-flags and stability-score's marginal contribution is
  genuinely open.
- **Failure interpretation**: if removing a feature *improves* performance,
  that feature is actively harmful in its current form — report and route
  back to D2/D3/D4 for re-diagnosis rather than just dropping it silently
  from M2-M4.

### Family Ro — Robustness

#### Ro1. Regime Robustness
- **Hypothesis**: M2–M4's edge over M1 (if any, established in Family M)
  holds within each individual regime slice from D5, not just on average
  across a sample dominated by one regime.
- **Method**: re-score Family M's TEST-window results split by D5's regime
  tags.
- **Baseline**: Family M's own aggregate result.
- **Data window**: TEST, split post-hoc by regime (no new decisions
  generated, purely a re-slicing of already-frozen TEST results — this
  does not violate the single-TEST-touch rule since it's the same
  evaluation, sliced).
- **Metric**: same as the Family M experiment being checked, per regime
  slice, small-n caveat per `METRIC_DESIGN.md` §4.
- **Expected result**: edge holds directionally in most regimes, may be
  statistically insignificant in low-n regimes (report as such, not as
  disconfirming).
- **Failure interpretation**: an edge driven entirely by one regime (e.g.
  only `BULL_LOWVOL`) that reverses in others is a materially important
  caveat for any claim from Family M — must be stated in any downstream
  paper claim, not buried.

#### Ro2. Adapter Dropout / Leave-One-Out Robustness
- **Hypothesis**: Family M's results are not driven by a single dominant
  adapter (the pilot's `deepalpha` pattern — one adapter involved in 83/129
  contradiction cases and dominating the negative confidence-weighting
  result).
- **Method**: leave-one-adapter-out re-runs of the winning M-method on
  TEST (post-hoc re-scoring where possible, matching Ro1's non-violating
  re-slicing approach; a true LOO re-fit would require touching CAL/VAL
  again and must be scoped as a VAL-window-only exercise if so, to avoid a
  second TEST touch).
- **Baseline**: the full-adapter-set result.
- **Data window**: VAL (if refitting) or a post-hoc TEST re-slice (if not).
- **Metric**: performance delta per dropped adapter, ranked.
- **Expected result**: some concentration is likely (echoing the pilot),
  but the method should not collapse entirely when any single adapter is
  removed — if it does, that's a real fragility finding.
- **Failure interpretation**: high sensitivity to one adapter is not
  disqualifying by itself but must be reported prominently — it means the
  "ensemble" claim is weaker than it appears and any paper claim should be
  scoped accordingly (`result-to-claim`, §6, should specifically check
  this before green-lighting an "ensemble improves robustness" claim).

#### Ro3. Historical Event Stress Test
- **Hypothesis**: exploratory only — no confirmatory hypothesis is claimed
  given small event counts; the goal is to characterize behavior during
  acute stress, not to confirm a pre-registered effect size.
- **Method**: run available Class-R adapters against the declared event
  windows in `DATA_SPLIT_PROTOCOL.md` §4.2, verifying reachability per
  adapter before inclusion (do not assume reachability).
- **Baseline**: `BASELINE_DESIGN.md` §3.1/§3.3 (buy-and-hold, cash) for the
  same event window.
- **Data window**: the declared event windows only, out-of-sample relative
  to any CAL/VAL/TEST split (these dates may fall inside TRAIN for some
  adapters — report this explicitly per adapter rather than treating it as
  a clean out-of-sample test where it isn't).
- **Metric**: drawdown, CVaR, and qualitative behavior description
  (`METRIC_DESIGN.md` §2.1).
- **Expected result**: no specific expected direction — report what
  happened.
- **Failure interpretation**: explicitly not falsifiable at this sample
  size (typically N=1 event per adapter) — any claim drawn from Ro3 alone
  must be labeled illustrative/case-study, never statistically supported,
  and `result-to-claim` (§6) must reject any attempt to promote a Ro3
  finding to a confirmed claim.

---

## 5. Data/Baseline/Metric cross-reference summary

| Family | Primary data window | Primary baseline source | Primary metric source |
|---|---|---|---|
| D1–D7 | `DATA_SPLIT_PROTOCOL.md` §2 (inventory) / §3 CAL | `BASELINE_DESIGN.md` §4 | `METRIC_DESIGN.md` §1 |
| M1–M4 | `DATA_SPLIT_PROTOCOL.md` §3 (CAL→VAL→TEST) | `BASELINE_DESIGN.md` §2–3 | `METRIC_DESIGN.md` §2–4 |
| A1–A2 | `DATA_SPLIT_PROTOCOL.md` §3 TEST (frozen, reused) | `BASELINE_DESIGN.md` §5 | `METRIC_DESIGN.md` §4 |
| Ro1–Ro3 | `DATA_SPLIT_PROTOCOL.md` §3 TEST / §4.2 events | Family M's own results | `METRIC_DESIGN.md` §2, §4 |

---

## 6. ARIS skill usage plan

- **`research-refine`** — used during this design pass itself (see §7) as
  a critical-review gate on this document before treating it as final.
- **`experiment-plan`** — this document *is* the deliverable that skill
  would normally produce; not separately re-invoked, since the roadmap
  already exists here in the brief's required format.
- **`ablation-planner`** — to be invoked once a Family M experiment passes
  `result-to-claim` (i.e. once there's a real result worth ablating),
  structuring A1/A2's run matrix rather than hand-building it.
- **`experiment-audit`** — to be invoked before any results from this
  protocol are written up as claims, checking for the integrity failure
  modes it's built to catch (fake ground truth, phantom results,
  insufficient scope) — particularly relevant given how much of D1–D7
  depends on honestly reporting `insufficient_data`/small-n rather than
  padding samples.
- **`result-to-claim`** — the gate between any Family M/A/Ro result and a
  written claim; explicitly required before M4 or Ro3 findings are
  promoted to paper-level claims, per their failure-interpretation notes
  above.

---

## 7. Design-pass verification note

Per the task's explicit instruction to fan out subagents to save time, this
design pass used a research fork to independently synthesize the pilot
study's methodology/limitations (cross-checked against this document's own
direct reading of the same source files) and made two live, non-simulated
checks against real systems: (1) `mcp__massive__call_api` against
`/v2/aggs/ticker/AAPL/range/1/day/...` to determine actual historical data
availability, and (2) a live `yfinance` pull to confirm the 10-year
alternative actually works, rather than asserting either from memory. Both
findings are load-bearing for `DATA_SPLIT_PROTOCOL.md` §2.1 and are why
this protocol does not block on a massive.com plan upgrade for the
core 10-year backtest requirement.

A separate critique pass was attempted via direct Codex MCP call
(`mcp__codex__codex`, since the `research-refine` skill's Problem-Anchor/
Method-Thesis scaffold is built for refining a vague research idea into a
paper proposal, not for critiquing an already-finished experiment-design
document, and would have produced a mismatched artifact). The Codex MCP
call failed 3/3 attempts with a network-layer error (`stream disconnected
... error sending request for url https://chatgpt.com/backend-api/codex/
responses`), not a prompt or scope issue. A self-critique was run in its
place — see `docs/research_reports/2026-07-19_experiment_protocol_self_
review.md` for the full findings (2 CRITICAL, 5 IMPORTANT, 2 MINOR) and
which were fixed directly in these four documents vs. left open. This
document should be treated as **self-reviewed, not externally reviewed by
a second model** — re-running the Codex critique once connectivity is
restored is recommended before treating this protocol as final.

A second, independently-launched session working the same brief also
converged on this document (see `docs/research_reports/
coordinator2_review_of_experiment_protocol.md`) — its independent research
(separate forks, separate live `massive.com`/`yfinance` checks) reached the
same adapter roster, Q-coverage counts, unreliable-adapter list, and
`atlas` ticker-mislabeling finding, and it deferred to this document rather
than overwriting it, per the standing multi-agent rule. Its one flagged gap
(no standalone native-Q4-policy return diagnostic) is incorporated into D6
above.

---

## 8. Multi-agent governance for future work on this protocol

Per this session's standing instruction: parallel subagents must not edit
the same final document directly. Going forward, any subagent asked to
extend, validate, or run this protocol writes its independent findings to
`docs/research_reports/` (one file per agent/topic, never a shared file
two agents write concurrently); only the coordinator (whichever session is
acting in that role) merges accepted findings into
`docs/research_positioning/` and/or updates the four documents in this
`docs/experiment_design/` directory. Before editing any of these four
files, check `docs/research_reports/` and recent git history for
in-flight work from another agent on the same file.

---

## 9. Explicit non-goals / out of scope for this document

- No adapter, `CONTRACT/`, `harness/`, or other Python code was written or
  modified to produce this protocol.
- This document does not itself run any experiment — it specifies what to
  run, on what data, against what baseline, measured how, and how to
  interpret both success and failure.
- Calendar boundaries in `DATA_SPLIT_PROTOCOL.md` §3.1 and the T0 date in
  §3.2 are left as open scheduling decisions for whoever executes this
  protocol, not fixed here.
