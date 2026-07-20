# Experiment Protocol — Formal Design

**Role**: experiment protocol design only. No experiment code was written, no
experiment was run, no adapter/schema/harness file was touched, no other
session's directory was modified. This file and its siblings in
`docs/experiment_design/` are the only files this session wrote.

**Skills used, and how**: `experiment-plan`'s Phase 0–4 methodology
(freeze claims → build experimental storyline → specify blocks → execution
order) was applied directly to produce this document's structure — its
default machinery writes to `refine-logs/EXPERIMENT_PLAN.md` in a
paper-planning-specific template; this task requires a specific file path
and a specific per-block field set (research question / hypothesis / input
/ target / experimental unit / sample construction / baseline / method /
metric / expected evidence / failure interpretation / dependencies / cost /
priority / main-vs-appendix), so the skill's *methodology* was followed and
its output redirected and reshaped into the required structure, rather than
its literal `Write`-to-`refine-logs/` template — disclosed here rather than
silently substituted, consistent with how Session 1 disclosed the same kind
of adaptation for `kill-argument`/`research-refine` against a non-LaTeX,
non-training-recipe target. `ablation-planner`'s Codex-leads-design
methodology was applied to the Cross-Cutting Evaluation ablations (§6)
prospectively — the skill's literal trigger condition ("main results pass
`result-to-claim`") cannot be met because no experiment has run yet; it was
therefore used to design *what* ablations the eventual results will need,
not to plan post-hoc ablations of existing results. Both adaptations are
logged with real Codex MCP thread IDs where a Codex call was made (§6).

---

## 1. Scope and inputs

This protocol is grounded in, and must be read together with:
- `docs/research_positioning/ICAIF_POSITIONING_REPORT.md`,
  `NOVELTY_AUDIT.md`, `CLAIM_CANDIDATES.md`,
  `_working/REFINED_CORE_CLAIM.md` (Session 1) — full synthesis and
  absorption/rejection log in `SESSION1_INTEGRATION_NOTES.md`.
- `PROJECT_SCHEMA_AUDIT.md`, `ADAPTER_CAPABILITY_RECOVERY.md`,
  `NEW_ADAPTER_INTEGRATION.md`, `CONTRACT/schemas.py` (engineering
  substrate — read-only) — precise field names, adapter live-readiness, and
  the `Q4Policy.generation_window` "harness-supplied, adapter must not
  alter it" contract requirement are used verbatim throughout this
  document and its siblings.

---

## 2. Hypothesis formalization

### 2.1 Primary hypothesis (H1)

Session 1's refined core claim (`_working/REFINED_CORE_CLAIM.md`) is
operationalized here into a fully testable form, per this session's remit.

**H1 (falsifiable form)**: Let a *structural contradiction event* be defined
only by the pre-registered ontology in §2.2 (not by mere strength/appetite
disagreement). For a given (adapter-pair-or-adapter, ticker, `as_of`,
horizon) decision point, let `C` be a binary/severity-scored contradiction
indicator computed only from information available at `information_cutoff
<= as_of`, and let `E` be a forward realized-error/degraded-quality measure
computed only from information strictly after `as_of` (§2.3). Controlling
for each system's own self-reported `ConfidenceEstimate.value` (and its
`kind`, per Session 1's confidence-kind-conditioning finding) as a
covariate, **H1 asserts `C` carries non-zero incremental information about
`E`** — i.e., a model of `E` on confidence alone is significantly
outperformed by a model of `E` on confidence + `C`.

**H0 (null, the falsification target)**: the incremental-information
coefficient on `C` is zero (equivalently: confidence-only and
confidence+`C` models are not significantly different) once confidence is
controlled for. H1 is **rejected** if H0 cannot be rejected at the
pre-registered significance/effect-size bar in §2.4 across the
pre-registered robustness strata.

### 2.2 Pre-registered contradiction ontology (written now, before any measurement)

Per Session 1's explicit, unresolved flag ("the contradiction ontology
itself must be pre-registered... before any measurement is run" — this was
out of Session 1's scope and is squarely this session's job), the following
ontology is fixed. **Only these count as `C=1` (structural contradiction).
Everything else — differences in risk appetite, conviction strength,
horizon, or a coherent high-risk/high-conviction trade — is explicitly
`C=0` and must never be counted as contradiction**, per
`CLAUDE.md`'s no-fabrication spirit (do not manufacture a stronger signal
than what is structurally there).

| Class | Rule | Not contradiction (explicitly excluded) |
|---|---|---|
| **Cross-adapter directional conflict** | Two adapters' `Q1Action.action` (mapped BUY→+1/SELL→-1/HOLD→0) or `Q3Signal.direction` (LONG/SHORT/NEUTRAL) are literally opposite (+1 vs -1, LONG vs SHORT) on the *same* `(ticker, as_of, horizon)` | Two adapters both BUY but with different `action_strength`/`confidence`; one BUY one HOLD (HOLD is not an opposite of BUY) |
| **Cross-adapter risk-flag conflict** | One adapter's `Q1Action.action=BUY` (or `Q3Signal.direction=LONG`) on ticker X at time `t` co-occurs with another adapter's `Q2State` for the same ticker/market at the same `t` reporting a state on the `dimension="risk"` (or equivalent open-vocabulary risk/volatility dimension) at or above a pre-registered extreme threshold (top decile of that adapter's own historical `value_numeric`/`value_category` distribution — adapter-relative, not an arbitrary absolute cutoff) | A single adapter's own BUY co-occurring with its own or another adapter's *moderate* risk state; risk flags on a *different* ticker/market than the action targets |
| **Intra-adapter Q1/Q3 direction mismatch** | The *same* adapter's `Q1Action.action` and `Q3Signal.direction` disagree in sign for the *same* `(ticker, as_of, horizon)` in the *same* result envelope (e.g. `action=BUY` but `direction=SHORT`) | Q1 present without a corresponding Q3 for that ticker/horizon (not comparable, not contradiction) |
| **Intra-adapter Q2→Q4 self-referential violation** | The *same* adapter's own `Q2State` risk/volatility dimension is at the adapter-relative extreme threshold (as above) at step `t`, and that same adapter's next `PolicyDecisionStep` (t' > t, same policy) *increases* gross exposure (`sum(abs(target_weights))`) or reduces `cash`/`CASH` weight relative to step `t`, with no offsetting `explanation` referencing the risk state | `Action=BUY` co-occurring with `Risk=HIGH` in a single static snapshot (Session 1's own explicit non-example); a policy that reduces risk after flagging it |
| **Intra-adapter action/logic inconsistency** | The adapter's own stated `decision_policy.decision_rule` (if present) is directly contradicted by the realized `action`/`target_weights` under that adapter's own documented rule (e.g. a stated "sell when signal < 0" rule with a positive signal but a SELL action) — evaluated only where a machine-checkable rule exists; not evaluated from free-text `explanation` | Any case requiring semantic judgment of free-text `explanation`/`bull_case`/`bear_case` — deliberately excluded to avoid fabricating a contradiction from prose interpretation |

**Deterministic operationalization of three table cells the fresh blind
review (thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`, question 2/8) found
left implementer discretion — fixed now, not left to judgment at
implementation time**:
1. *"or equivalent open-vocabulary risk/volatility dimension"* (row 2): the
   fixed, closed whitelist of `StateEstimate.dimension` string values that
   count as the risk/volatility dimension for this rule is: `"risk"`,
   `"volatility"`, `"downside_risk"`, `"tail_risk"`, `"uncertainty"` —
   exact, case-insensitive string match only, no fuzzy/semantic matching.
   Any other dimension string (e.g. `"sentiment"`, `"liquidity"`,
   `"market_regime"`) does **not** count for this rule, even if it might
   plausibly correlate with risk. This whitelist may be extended only
   during the pilot stage, recorded once in `EXPERIMENT_DEPENDENCY_MAP.md`'s
   pilot record, and frozen before validation — never extended after seeing
   a validation or test result.
2. *"with no offsetting `explanation` referencing the risk state"* (row 4):
   **removed as a criterion.** The fresh review is right that "offsetting
   explanation" requires semantic judgment of free text, which the
   project's own next table row (row 5) explicitly excludes as a
   contradiction-detection input to avoid fabricating a contradiction from
   prose interpretation — row 4 cannot consistently use the criterion row 5
   forbids. **Fix**: row 4's rule is now purely structural — the
   exposure-increase/cash-reduction condition alone (with no
   free-text-based override or exception) determines `C=1` for this class.
   An adapter's own free-text justification for the increase may be
   surfaced as `explanation`/evidence in a case-study write-up, but it never
   changes the binary `C` label.
3. *"evaluated only where a machine-checkable rule exists"* (row 5): a
   `decision_policy.decision_rule` string counts as machine-checkable only
   if it matches one of a fixed set of parseable templates, fixed at the
   pilot stage before validation (e.g. `"{action} when {signal_field}
   {comparator} {threshold}"` patterns with a numeric threshold and a
   comparator in `{<, <=, >, >=, ==}`) — recorded in the pilot-stage record
   as an explicit regex/parser spec, not decided ad hoc per adapter at
   evaluation time. An adapter whose `decision_rule` does not match any
   registered template contributes `C=0` for this class always (not
   evaluated as "no rule" vs. "unparseable rule" — both mean the class
   cannot fire for that adapter, a conservative default that never inflates
   `C`).

**Primary vs. secondary exposure (tightened after adversarial review, §8)**:
a hostile review correctly flagged that leaving severity scoring
"optionally scaled" reads as registered flexibility. Fix: **H1's primary
exposure is the binary `C` (did any of the five classes above fire, yes or
no) — full stop, no scaling, no optionality.** The severity score below is
retained only as a **secondary, explicitly-labeled-exploratory** measure
(used for L2.1/L2.4's weighting/intervention thresholds, where a graded
signal is operationally useful) and must never be substituted for binary
`C` in H1's own primary test. Severity score definition (secondary use
only): count of distinct classes triggered simultaneously for the same
decision point, scaled by the magnitude of the directional conflict (e.g.
LONG vs SHORT scores higher than LONG vs NEUTRAL-adjacent-to-SHORT) using
a fixed linear scale fixed at the pilot stage (not "optional" — a single
concrete scaling function must be written down in the pilot-stage record
before any validation-stage data is touched, per `EXPERIMENT_DEPENDENCY_
MAP.md` §6's freeze rule). The cross-adapter risk-flag conflict class's
"adapter-relative extreme threshold" (top decile of the adapter's own
historical distribution) is likewise frozen as a fixed numeric percentile
(90th) at the pilot stage using pilot-window data only, then locked for
validation and test — "adapter-relative" describes *what the threshold is
computed from* (each adapter's own distribution), not license to
re-compute or adjust it after the pilot stage.

### 2.3 Operational "degraded forecast/policy quality" (`E`)

**Primary outcome family, fixed now (added after the Session 3 fresh
blind review, thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`, which found
`E` "mixes Q1/Q3 directional error and Q4 policy degradation under one
H1 without a clearly locked primary outcome family")**: H1's pooled
headline test (§2.3.2) uses **only the Q1/Q3 prediction-quality variant**
below as its primary `E`, because it is computable for every TIER-1
adapter regardless of Q4 capability, keeping the pooled sample
homogeneous. The Q4 policy-quality variant is a **separate, secondary
robustness check**, run only on the Q4-capable subset, reported alongside
but never pooled into the same headline model as the Q1/Q3 variant — mixing
outcome types with different units and different eligible samples into one
pooled coefficient would itself be a design flaw, not a strength.

- **Q1/Q3 (prediction quality, primary)**: sign mismatch between the
  decision's directional call (`action`/`direction`) and the realized sign
  of forward return at the stated `context.horizon` (1d/5d/20d, per
  Session 1's candidate horizons), computed strictly from data with
  timestamp > `as_of`. Continuous variant: realized forward return times
  the decision's directional sign (negative = wrong-way), for
  magnitude-sensitive tests. **HOLD/NEUTRAL handling (fixed now, per the
  fresh review's question 8)**: a decision with `action=HOLD` (and no
  `Q3Signal.direction`, or `direction=NEUTRAL`) makes no directional call
  and is therefore **excluded from the Q1/Q3 `E` computation entirely**
  (not scored as correct, not scored as incorrect, not imputed) — only
  decisions with a genuine directional call (`BUY`/`SELL` or
  `LONG`/`SHORT`) enter the sign-mismatch test. This is symmetric with
  §2.2's directional-conflict ontology class, which already excludes
  HOLD from counting as a contradiction with BUY/SELL for the same reason.
- **Q4 (policy quality, secondary robustness check only)**: forward realized
  return of the `PolicyDecisionStep.target_weights` (or `initial_weights`
  for single-point policies) over the step's implied holding period, net of
  a transaction-cost model (§ BASELINE_DESIGN.md / METRIC_DESIGN.md),
  compared against a matched same-universe equal-weight baseline over the
  identical window (a relative, not absolute, degradation measure, to
  control for market-wide moves).
- Both variants require the **information-cutoff-to-outcome time ordering**
  to be strictly enforced: `E` is computed only from timestamps after the
  `as_of`/`information_cutoff` that produced `C`. This reuses the
  `PolicyDecisionStep` causality invariant (`information_cutoff <=
  timestamp`) already enforced by `CONTRACT/schemas.py` and already
  live-verified with 0 violations across 344 real decisions in
  `ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md` — this
  protocol extends the same invariant to the *evaluation* layer, not just
  the decision layer.

### 2.3.1 H1-specific negative controls (added after adversarial review, §8)

A hostile-review pass (§8) found H1's original design — confidence-only vs.
confidence+`C` — insufficient to distinguish "structural contradiction (§2.2)
is special" from "any disagreement predicts errors, unsurprisingly." A
second, fresh blind review (thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`,
Task A of the Session 3 pre-pilot readiness pass) confirmed the risk
persists specifically because §2.2's first ontology class ("cross-adapter
directional conflict") is itself *a form of* disagreement, so the burden is
on `C` to add information beyond a *precisely defined* disagreement score,
not merely to be labeled differently. **H1's own nested-model test (§2.4)
must therefore include these controls as required covariates/comparators,
not optional extras**:
- a **generic cross-adapter disagreement magnitude** term, precisely
  defined (fixed now, per the fresh review's finding that "e.g.
  entropy/dispersion" was underspecified): at each `(ticker, as_of,
  horizon)` tuple, map every eligible adapter's directional call to
  {-1, 0, +1} (SELL/SHORT=-1, HOLD/NEUTRAL=0, BUY/LONG=+1), form the
  empirical distribution of these values across the eligible adapters
  present at that tuple, and compute its **Shannon entropy in bits,
  normalized by log2(3)** (the maximum possible entropy over a 3-outcome
  distribution) to a fixed [0,1] scale. This is the one, sole, precisely-
  specified disagreement-magnitude covariate for H1's own model — the
  same construction is reused (not redefined) as L2.4's entropy baseline
  in `BASELINE_DESIGN.md` §4, so the two are guaranteed identical by
  construction, not merely "computed identically" by convention;
- a **missingness/coverage indicator** (does the decision tuple have fewer
  eligible adapters present than the modal count — a low-coverage tuple can
  spuriously correlate with both `C` and `E`);
- an **adapter-pair effect term** — the *same single term* used in §2.3.2's
  pooled model (not a second, separately-specified term here; §2.3.1's
  controls and §2.3.2's pooled-model structure are one model specification,
  not two stacked ones) — defaulting to a **random effect / partial
  pooling**, not a fixed effect, unless pilot-stage diagnostics show sparse
  per-pair sample sizes make a fixed effect clearly preferable (fixed
  effects on sparse categories can cost more power than they buy in
  rigor — this default is a direct fix from the research-refine-adapted
  pass in §8);
- a **pre-specified per-class breakdown** of §2.2's five ontology classes
  (report each class's own incremental contribution, not only the pooled
  `C` score) so a reviewer can see the effect is not concentrated in one
  narrow class standing in for the whole ontology.
H1 is only reported as supported if `C`'s incremental-information
coefficient remains significant **after** controlling for generic
disagreement magnitude and the other controls above — this is a strictly
harder bar than the original design and is the direct fix for the
"structural contradiction is not shown to be different from ordinary
disagreement" critique.

**Unit of analysis, fixed now (added after the fresh blind review's
finding #9, thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`: "cross-adapter
pairs can create many correlated rows from the same ticker/time/outcome,
raising pseudo-replication risk")**: H1's primary pooled test (§2.3.2)
uses **one row per `(ticker, as_of, horizon)` tuple**, not one row per
adapter-pair. At each tuple, `C` is aggregated across every eligible
adapter/adapter-pair present (`C=1` if **any** of §2.2's five classes
fires for **any** eligible adapter or adapter-pair at that tuple; the
generic-disagreement-magnitude covariate above is likewise computed once
per tuple, across all eligible adapters' votes jointly, not per pair).
This is the deliberate fix for pseudo-replication: multiple adapter pairs
sharing the same underlying market outcome at the same tuple would
otherwise inflate the effective sample size and understate variance if
each pair contributed its own row. The **per-class breakdown** and any
pair-level exploratory analysis (e.g. "which specific adapter pairs drive
the tuple-level `C=1` flag most often") are explicitly secondary,
tuple-conditional detail — never a second, competing unit of analysis for
the headline pooled test.

### 2.3.2 Primary estimand: pooled, not stratum-cherry-picked (added after adversarial review, §8)

The original design's H1 acceptance criterion ("significant in **at least
one** horizon × regime stratum") is **demoted to a secondary, exploratory,
hypothesis-generating result.** **H1's primary, paper-headline acceptance
criterion is now a single pooled test**: one nested model fit across all
eligible (adapter-pair-or-adapter × regime × horizon) strata jointly, with
the single adapter-pair effect term specified in §2.3.1 (default random
effect/partial pooling, fixed-effect only if pilot-stage sparsity
diagnostics justify it — the same term, not a second one; corrected here
for consistency with §2.3.1) and regime/horizon as fixed or random effects
(that specific choice, for regime/horizon only, is left to the pilot
stage, recorded before validation), testing the *pooled*
incremental-information coefficient on `C` (plus §2.3.1's controls). The
per-stratum breakdown (with BH-FDR correction, §2.4) is reported
*alongside* the pooled result as color/robustness detail, never
substituted for it. This directly closes the "a corrected positive result
in one surviving stratum gets called 'H1 supported'" attack — the
headline claim now requires the pooled, whole-deployment effect, and
stratum-level results can only *qualify* (regime-conditional framing,
§2.4/Fallback (c)) an already-pooled-significant result, not manufacture
support on their own.

### 2.4 Statistical test and robustness requirements

- **Primary test**: nested-model incremental-information test — a model of
  `E` on confidence alone vs. confidence + `C` (logistic regression for
  binary `E`, OLS/quantile regression for continuous `E`); likelihood-ratio
  or F-test for the added-variable significance of `C`.
- **Autocorrelation correction**: financial time series are not i.i.d. —
  use **block bootstrap** (block length ≥ the longest horizon tested, i.e.
  ≥ 20 trading days for the 20d-horizon test) for confidence intervals on
  the incremental-information coefficient, not a naive i.i.d. bootstrap.
- **Multiple-comparison correction**: tests are run per (adapter-pair-or-
  adapter class × regime × horizon) stratum; apply Benjamini-Hochberg FDR
  correction across the full stratum grid before declaring any individual
  stratum significant.
- **Effect size, not just p-value**: report the incremental-information
  coefficient's magnitude and a practical-significance threshold. A hostile
  review (§8) correctly noted that deferring this to "an exact numeric
  threshold fixed at pilot stage" without specifying *how* is itself a
  form of registered flexibility. **Fix — the procedure, not just a bare
  deferral, is pre-registered now**: at the pilot stage, compute a power
  analysis using the pilot slice's own observed variance in `E` and
  observed `C` incidence rate, targeting **80% power to detect the
  smallest incremental-AUC/pseudo-R² gain considered practically meaningful
  a priori (a placeholder judgment call, not a data-driven one: 0.02
  incremental AUC / pseudo-R², a conventional small-to-medium effect
  threshold in comparable applied-ML calibration literature) at
  alpha=0.05 after BH-FDR correction**; the resulting minimum sample size
  (minimum number of eligible decision tuples with computed `E`) is then
  checked against the actual TIER-1-eligible sample from
  `ADAPTER_REGISTRY_REQUIREMENTS.md`/`DATA_SPLIT_PROTOCOL.md` §5 **before**
  the validation stage begins. If the eligible sample is under-powered for
  the 0.02 threshold, the threshold (not the sample) is what may be
  revised — and only once, with the revision and its justification
  recorded in `EXPERIMENT_DEPENDENCY_MAP.md`'s pilot-stage record before
  any validation-stage result is seen. This procedure is the pre-registered
  artifact; the resulting number is a pilot-stage output, not a
  post-hoc-adjustable free parameter.
- **Single, non-contradictory acceptance rule (rewritten after the fresh
  blind review, thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`, which found
  this bullet's original wording — "survive FDR correction in at least one
  horizon and one regime stratum" — directly contradicted §2.3.2's pooled-
  test-is-primary rule, an exploitable inconsistency, not a stylistic
  one)**: **H1 is supported if, and only if, the pooled test (§2.3.2,
  §2.3.1's controls included) is significant and clears the pilot-computed
  practical-significance threshold below.** No per-stratum result, however
  significant individually, can support H1 on its own — this sentence is
  now the single, unqualified acceptance rule and supersedes any other
  phrasing anywhere in this deliverable set (see `CLAIM_TO_EXPERIMENT_
  MATRIX.md`'s matching H1 row and Fallback-table entry, kept in sync).
  Once, and only once, the pooled test is significant, the following are
  required **robustness checks on that already-significant pooled result**
  (not alternative paths to significance): (a) not attributable to a single
  adapter pair or single ticker (leave-one-adapter-out, leave-one-ticker-out
  sensitivity checks on the pooled coefficient); (b) directionally
  consistent (no sign flip) in the majority of individual (regime ×
  horizon) strata large enough to be individually informative, even though
  those strata are not BH-FDR-significance-tested for acceptance purposes;
  (c) the secondary per-stratum breakdown (BH-FDR corrected, reported for
  color/interpretability) may show the pooled effect is *stronger in some
  regimes than others* — this is reported as regime-conditional nuance on
  top of an already-supported H1, per Fallback Claims below, never as a
  substitute for pooled significance.

### 2.4.1 Minimum coverage for H1 to remain claim-bearing (added after adversarial review, §8; simplified after a second research-refine-adapted pass, thread `019f7c8c-bf7c-7b23-b596-02cf2bba2264`)

A hostile review flagged that adapter/universe/horizon eligibility and
per-stratum failure attrition could narrow scope after the fact without a
floor. A follow-up research-refine-adapted pass then flagged the *first*
draft of this fix as over-prescriptive for a pre-registration document —
"feels more like a pilot-stage scope-calibration rule than something
strongly justified now" — and recommended pre-registering the *principle
and downgrade path* now, finalizing the *exact numeric tiers* at the pilot
stage rather than hand-picking specific numbers (4 paradigms, 8 adapters,
etc.) before any pilot data exists to justify them. **Simplified fix,
adopted**: the principle is fixed now — **H1 may only be reported as the
paper's primary, full-scope claim if the eligible pooled-test sample
(§2.3.2) spans a majority of Session 1's catalogued 6+ paradigms and a
sample size adequate for the §2.4 power-analysis procedure at the
regime/horizon-stratification level the pooled model actually uses** — and
the exact minimum counts (how many paradigms/adapters/horizons/regime
strata specifically) are computed *as part of* the same pilot-stage power
analysis in §2.4 (one combined pilot-stage calculation, not two separate
gates), then recorded in `EXPERIMENT_DEPENDENCY_MAP.md`'s pilot-stage
record before validation begins. If the TIER-1-eligible roster cannot meet
the pilot-computed floor, H1 must be reported with an explicitly narrowed
scope claim (per `RISK_AND_FAILURE_PLAN.md` §12's scope-language
discipline) rather than as the originally-intended cross-paradigm,
26-adapter-scale claim — a pre-registered downgrade path, not a silent
one, now computed once rather than asserted twice.

### 2.5 Secondary hypotheses

| ID | Statement | Primary experiment group(s) |
|---|---|---|
| H2 | Reliability-/contradiction-weighted fusion (measured calibration + `C`-penalty) improves risk-adjusted decision quality over naive-aggregation baselines (majority vote, equal-weight, self-reported-confidence-weight) | L2.1 |
| H3 | Contradiction-aware intervention (abstain/reduce-position) lowers downside risk (drawdown/tail risk) relative to always-fuse and random-intervention baselines, even without improving raw return | L2.4 |
| H4 | Reliability (calibration error, hit-rate, `C` rate) is regime- and horizon-dependent | L1.4 |
| H5 | Layer 1 diagnostic features add incremental decision value beyond raw Q1–Q4 outputs alone | Cross-cutting X.2 (pathway ablation), feeding L2.1/L2.2 |
| H6 | Shadow Q4 policies (recombining one system's Q1/Q3 with another's Q2/Q4 risk adjustment) convert otherwise Q4-weak systems' Q1/Q3 information into competitive portfolio value | L2.3 |
| H7 | Reliability-aware routing outperforms one-size-fits-all fusion under regime/horizon conditioning | L2.2 vs. L2.1 head-to-head |

### 2.6 Fallback claims (pre-registered now, per §8's explicit instruction not to invent these after seeing final-test results)

| If this happens... | ...the pre-registered acceptable conclusion is |
|---|---|
| L2.1/L2.2 (fusion/routing) fail to beat baselines on raw return | H1 alone, if it holds, remains a complete, independent contribution per Session 1's `REFINED_CORE_CLAIM.md` design — report fusion/routing as negative/null decision-layer results, not as invalidating H1 |
| Only downside-risk reduction holds (H3), not return improvement | Reframe the paper's decision-layer contribution as "a risk-management tool, not an alpha source" — an explicitly legitimate, pre-registered fallback framing, not a downgrade to be hidden |
| The pooled test (§2.3.2, the sole acceptance path per §2.4) is significant, but the secondary per-stratum breakdown shows the effect is markedly stronger in some regimes/horizons than others | H1 is supported (the pooled test passed); report the per-stratum heterogeneity as regime-conditional nuance layered on top of an already-supported claim — **not** as a substitute for pooled significance. This row does **not** apply if the pooled test itself is not significant — see the next row |
| The pooled test is **not** significant, but one or more individual strata are significant before/without FDR correction | **This is not a fallback path — H1 is not supported.** Per §2.4's single acceptance rule (rewritten after the Session 3 fresh blind review), an uncorrected or cherry-picked stratum-level result may never be reported as "H1 supported" under any framing, regime-conditional or otherwise; report the pooled null result honestly under the next row |
| Calibration (Q2 diagnostic group L1.2) is poor project-wide, but `C`/coherence (L1.3) is still diagnostic | Supports Session 1's Candidate-2 framing that calibration and contradiction are different diagnostic axes — report both findings, do not let poor calibration be read as invalidating the contradiction result |
| The eligible (TIER-1, see `DATA_SPLIT_PROTOCOL.md`) adapter subset is smaller than the full 26 | Scope every claim explicitly to "N adapters, M paradigms actually used in the historical main experiment" — never claim the full 26-adapter, 6+-paradigm scope if the eligible subset is smaller; see `ADAPTER_REGISTRY_REQUIREMENTS.md` for the eligibility gate |
| Q4 projects are not fully comparable under one protocol | This is exactly why the Controlled Scientific Track (§4) exists; if even that track cannot produce a clean comparison for a given adapter pair, exclude that pair from the controlled comparison and report it only on the Native Capability Track with an explicit non-comparability caveat — never force an unfair comparison to hit a paper deadline |

---

## 3. Original Exp2–Exp18 → new experiment-group mapping

Every original item is accounted for exactly once as a *primary* home,
with cross-references where an item legitimately feeds more than one group.
Two items (Exp1, Exp7) do not appear in the user's own numbered list and
are not invented here.

| Original | New home | Disposition |
|---|---|---|
| Exp2 (Field Value / Compression Loss) | **L1.1** | Kept as a dedicated diagnostic group — directly answers CLAUDE.md §4's provenance-separation requirement |
| Exp3 (Confidence Calibration) | **L1.2** | Merged with Exp8 — kept together because Session 1's Claim 2 dossier found the calibration-by-mechanism-kind and stability/determinism diagnostics only become non-obvious *jointly* |
| Exp4 (Cross-Adapter Contradiction) | **L1.3** (primary hypothesis carrier) | Merged with Exp10 — cross-adapter and intra-adapter contradiction are measured by one shared severity-scored `C` (§2.2), not two disconnected diagnostics |
| Exp5 (Q4 Policy Validation) | **L1.5** | Merged with Exp6 — kept as one "Q4 Audit" group per the task brief's explicit instruction to merge but report performance/risk separately |
| Exp6 (Q4 Risk/Exposure Audit) | **L1.5** | (see Exp5) |
| Exp8 (Stability/Repeatability) | **L1.2** | (see Exp3); also feeds Cross-Cutting X.3 (seed/repeated-run analysis reuses this group's machinery) |
| Exp9 (Regime-Stratified Reliability) | **L1.4** | Kept standalone — Session 1 Candidate 3 explicitly scoped this as a supporting ablation feeding L2.1/L2.2, not a silo |
| Exp10 (Cross-Q Coherence) | **L1.3** | (see Exp4) — deliberately **not** conflated with cross-adapter contradiction as one flat count; §2.2's ontology keeps the five classes distinct even though they feed one severity score |
| Exp11 (Source/Field Ablation) | **Cross-cutting X.1** | Kept cross-cutting, not folded into L1.1, because it cuts across every Layer 1 *and* Layer 2 group's inputs |
| Exp12 (Selective Prediction/Abstention) | **L2.4** | Merged with Exp15 — per Session 1 Candidate 5's finding that these are the same mechanism (threshold-triggered abstention) described from a general-reliability angle (Exp12) and a contradiction-specific angle (Exp15); kept as one group evaluated on both triggers |
| Exp13 (Reliability-Aware Routing) | **L2.2** | Kept standalone — deliberately **not** merged with L2.1 (fusion) despite the task brief's own suggested outline listing "Fusion / Routing" as one group, because Session 1's positioning treats fusion (vs. TrustTrade/ContestTrade) and routing (vs. FineFT) as two separately-scored, separately-competed decision-layer contributions (6/10 and 7/10 respectively) that must be benchmarked against *different* baselines — collapsing them would blur two distinct novelty claims into one experiment group. See `SESSION1_INTEGRATION_NOTES.md` |
| Exp14 (Shadow Q4 Policy Construction) | **L2.3** | Kept standalone — Session 1's Codex Phase C called this "the stronger, more defensible half" of the routing claim; it deserves its own group, not a sub-bullet of L2.2 |
| Exp15 (Contradiction-Aware Intervention) | **L2.4** | (see Exp12) |
| Exp16 (Validation-Conditioned Policy Selection) | **L2.5** | Kept as a supporting/optional group — not directly required by H1 or the two lead decision-layer claims, but required as a baseline family (rolling-performance selector) for L2.2's baseline ladder per Session 1's non-negotiable-experiment list |
| Exp17 (Multi-View Meta-Fusion) | **L2.1** (simplified instance) + **L2.6** (general form) | Split deliberately: L2.1 uses a *simple, interpretable, weighted-vote* instance of this mechanism as the main-paper primary fusion method (smallest adequate mechanism, per `research-refine`'s governing principle); the full learned meta-layer is kept as L2.6, an optional-enhancement/appendix-only comparison against L2.1, explicitly to test whether the added complexity of a learned meta-model earns its keep over the simple weighted-vote version |
| Exp18 (Information Pathway Ablation) | **Cross-cutting X.2** | Kept distinct from Exp11/X.1 per the task brief's own instruction — X.1 is field/source-level, X.2 is end-to-end-pathway-level |

---

## 4. Shared Evaluation Protocol — three tracks

Directly answers Session 1 adversarial review's structural gap (fusion,
routing, and abstention did not yet share one evaluation protocol). Full
field-by-field specification is in `DATA_SPLIT_PROTOCOL.md` §4; summarized
here because every experiment group below is tagged with the track it runs
on.

1. **Compatibility Track** — adapter-specific minimal runnable config
   (per-adapter universe/generation-window substitutions, as already used
   ad hoc in `NEW_ADAPTER_INTEGRATION.md`'s unified-harness run). Used
   *only* for engineering coverage/smoke verification. **Never used to
   support a claim.**
2. **Controlled Scientific Track** — one shared `as_of`/`data_cutoff`
   sequence, one shared universe mapping, one shared trading calendar, one
   shared transaction-cost model, one shared benchmark, one shared
   execution-delay assumption, one shared risk-free rate, one shared
   rebalancing/missing-output/failure-handling/cash-treatment policy, one
   shared leverage/exposure audit, one shared result-aggregation method.
   **This is the only track any Layer 2 comparison (L2.1–L2.6) or H1–H7
   claim may be evaluated on.**
3. **Native Capability Track** — each adapter's closest-to-native
   configuration (e.g. skfolio's `WalkForward` cross-validation loop run
   exactly as its own paper intends, TradeMaster's native DJ30-only
   universe). Used *only* for L1.1's compression-loss analysis (native
   capability vs. unified-schema capability) — **never used for a
   cross-system claim**, since native configs are not mutually comparable
   by construction.

---

## 5. Layer 1 diagnostic groups

### L1.1 — Representation and Field Value

- **Research question**: does the unified schema lose decision-relevant
  information present in native upstream output?
- **Hypothesis**: some canonical fields carry near-zero incremental
  predictive/decision value while some native fields excluded from the
  canonical schema (per `PROJECT_SCHEMA_AUDIT.md` §9's three
  `OPTIONAL_EXTENSION` candidates and §10's excluded-capability list) would
  add value if surfaced.
- **Input**: native upstream output (Native Capability Track) vs. canonical
  `AdapterResult` (Controlled Scientific Track), for the TIER-1 eligible
  adapter set (`ADAPTER_REGISTRY_REQUIREMENTS.md`).
- **Target**: information-retention score (already partially estimated in
  `PROJECT_SCHEMA_AUDIT.md` §7 per-project, 45–95% range) recomputed on a
  decision-relevance basis, not just field-coverage basis.
- **Experimental unit**: one (adapter, canonical field) pair.
- **Sample construction**: all `FieldMapping` records already produced by
  every TIER-1 adapter's own `field_mappings` output (schema-native
  provenance, no new instrumentation needed) plus the 474-row
  `PROJECT_SCHEMA_AUDIT.csv` as the native-side reference.
- **Baseline**: raw native fields (no mapping loss) vs. canonical-core-only
  vs. canonical-core+optional.
- **Method**: field-coverage ratio (already computed) + a *predictive-value*
  regression of forward `E` (§2.3) on each field's presence/value,
  controlling for the rest — an incremental-value test structurally
  identical to H1's, applied per field instead of per contradiction event.
- **Metric**: field coverage, native retention %, extraction loss,
  missingness, incremental predictive value (§METRIC_DESIGN.md §Layer1
  Representation).
- **Expected evidence**: a ranked list of which canonical fields are
  load-bearing vs. decorative, and whether any `OPTIONAL_EXTENSION`
  candidate (`iteration_history`, `sub_opinions`, `EvidenceItem.relevance_
  score`) shows enough incremental value to justify a future schema
  version bump (a recommendation, not a decision this protocol can make —
  `CONTRACT/` stays protected per CLAUDE.md §3).
- **Failure interpretation**: if canonical fields show no measurable
  information loss relative to native, the "unified schema as audit
  substrate" framing is *strengthened*, not weakened — a null result here
  is good news for Session 1's positioning, and should be reported as such.
- **Dependencies**: none upstream (can start immediately — field mappings
  already exist for every TIER-1 adapter).
- **Estimated cost**: low — no new adapter calls, pure post-hoc analysis of
  already-produced `field_mappings`/`native_output`.
- **Priority**: MUST-RUN (feeds L1.2/L1.3 as a sanity precondition — see
  `EXPERIMENT_DEPENDENCY_MAP.md`).
- **Main paper or appendix**: main paper (short section), full field-level
  table in appendix.

### L1.2 — Calibration and Stability

- **Research question**: does confidence/strength predict forward outcome
  quality, and is it reproducible under repeated identical queries?
- **Hypothesis**: naive per-adapter calibration hides a structural pattern
  visible only when conditioned on `ConfidenceKind` and on
  determinism-vs-non-determinism (Session 1 Candidate 2's finding).
- **Input**: `Q1Action.confidence`/`Q3Signal.confidence`/`strength`, keyed
  by `ConfidenceKind` (6 kinds in `CONTRACT/schemas.py`); K repeated calls
  per frozen `(adapter, ticker/universe, as_of, data_cutoff, horizon)`.
- **Target**: forward 1d/5d/20d realized return sign/magnitude (same `E`
  construction as §2.3); output variance across the K repeats.
- **Experimental unit**: one (adapter, ticker, `as_of`, horizon) decision,
  observed K times for the stability half.
- **Sample construction**: draw from the Controlled Scientific Track's
  validation-window decision set; K to be fixed at the pilot stage (§7),
  budgeted separately per adapter class (deterministic adapters need K=1
  sanity-only; stochastic ML/RL and LLM adapters need K≥3, cost-gated by
  `RunMetadata.cost_usd`/`latency_sec` — real historical costs already
  observed in `ADAPTER_CAPABILITY_RECOVERY.md`, e.g. `tradingagents`
  ~9-10 real LLM calls per single run, inform this budget).
- **Baseline**: none needed for calibration (it's a diagnostic, not a
  competition); for stability, compare against a "perfectly stable" ideal
  (zero variance) and report the empirically observed distribution.
- **Method**: reliability diagrams / ECE / Brier score per `ConfidenceKind`
  bucket; action-flip rate, score variance, weight-vector distance across
  K repeats, split by adapter determinism class (deterministic / stochastic
  ML-RL / LLM).
- **Metric**: see `METRIC_DESIGN.md` §Layer1 Calibration and §Layer1
  Stability.
- **Expected evidence**: calibration quality ranked by confidence-kind (not
  by adapter identity alone); a documented, already-known real defect
  (unseeded per-call retraining in one adapter, per Session 1's Candidate 2
  dossier) should reproduce as a stability outlier — a useful sanity check
  that the diagnostic actually detects a known-real issue.
- **Failure interpretation**: uniformly poor calibration across all kinds
  is itself a reportable finding (motivates L2.1's move away from
  self-reported confidence) — not a failed experiment; see Fallback Claims
  §2.6.
- **Dependencies**: L1.1 (field mappings must be validated first so
  confidence-kind labels are trustworthy).
- **Estimated cost**: medium — K-repeat calls to stochastic/LLM adapters
  incur real API cost; budget gate required (see
  `RISK_AND_FAILURE_PLAN.md`).
- **Priority**: MUST-RUN.
- **Main paper or appendix**: main paper (motivates L2.1's design), full
  per-adapter tables in appendix.

### L1.3 — Structural Contradiction and Cross-Q Coherence (primary hypothesis carrier)

- **Research question**: H1 (§2.1) directly.
- **Hypothesis**: H1.
- **Input**: the pre-registered contradiction ontology (§2.2) applied to
  every eligible decision pair/tuple in the Controlled Scientific Track.
- **Target**: `E` (§2.3), at the pre-registered horizons.
- **Experimental unit**: one contradiction *event* (a specific ontology
  class firing on a specific tuple at a specific `as_of`).
- **Sample construction**: all TIER-1-eligible adapter pairs (cross-adapter
  classes) and all TIER-1 adapters individually (intra-adapter classes),
  one row per `(ticker, as_of, horizon)` tuple per §2.3.1's unit-of-
  analysis fix, over the Calibration/Validation intervals (never the final
  test set for ontology tuning — the ontology's definition is frozen before
  any data is touched at all, per §2.2/§2.4, and its one adjustable
  numeric threshold, if any, is fixed at the pilot stage on Calibration-
  interval data, per `DATA_SPLIT_PROTOCOL.md` §1.1; corrected here — a
  prior version of this bullet cited a nonexistent "§9").
- **Baseline**: confidence-only model of `E` (§2.4's nested-model design
  *is* the baseline, not a separate system).
- **Method**: §2.4's nested-model incremental-information test, block
  bootstrap, FDR-corrected across strata.
- **Metric**: contradiction incidence, severity, breadth, persistence,
  contradiction-conditioned error, contradiction-conditioned drawdown,
  coherence-violation rate (see `METRIC_DESIGN.md`).
- **Expected evidence**: H1 supported (possibly regime-conditionally, per
  §2.4's explicit tolerance).
- **Failure interpretation**: H0 not rejected → this is the single most
  consequential possible failure in the whole protocol (per Session 1's
  `REFINED_CORE_CLAIM.md`: "a more basic and more informative failure than
  either decision-layer mechanism underperforming... a signal to rethink
  the whole submission"). If this happens, escalate to a human checkpoint
  before continuing to L2.1–L2.6 (see `EXPERIMENT_DEPENDENCY_MAP.md`'s kill
  criteria).
- **Dependencies**: L1.1, L1.2 (confidence-kind labels must be validated so
  the confidence covariate in §2.4's nested model is trustworthy).
- **Estimated cost**: low-medium — reuses decisions already generated for
  L1.2; ontology evaluation itself is pure post-hoc computation.
- **Priority**: MUST-RUN, highest priority of all groups.
- **Main paper or appendix**: main paper, the headline result.

### L1.4 — Regime-Conditioned Reliability

- **Research question**: H4.
- **Hypothesis**: H4 (regime/horizon-dependence of reliability, tolerating
  a null result per Session 1 Candidate 3).
- **Input**: L1.2/L1.3 outputs, stratified by a pre-registered regime
  label.
- **Target**: same reliability metrics as L1.2/L1.3, computed per regime
  stratum.
- **Experimental unit**: one (adapter-or-pair, regime, horizon) stratum.
- **Sample construction**: regime labels must be defined **using only
  information available up to each stratum's own decision points** — a
  regime classifier trained/fit on the full historical span including
  future-relative-to-decision data would leak; see `DATA_SPLIT_PROTOCOL.md`
  §6 for the exact regime-labeling causality rule.
- **Baseline**: pooled (non-regime-stratified) reliability as the
  reference.
- **Method**: stratified re-computation of L1.2/L1.3's metrics; a
  regime-by-metric interaction test.
- **Metric**: conditional hit rate, conditional calibration, conditional
  policy performance, adapter/pair rank stability across regimes.
- **Expected evidence**: an adapter×regime×horizon reliability table,
  feeding L2.2's routing signal directly.
- **Failure interpretation**: a null result (regime-invariant reliability)
  is explicitly pre-registered as informative, not thin — per Fallback
  Claims §2.6 and Session 1 Candidate 3's positioning.
- **Dependencies**: L1.2, L1.3.
- **Estimated cost**: low — post-hoc stratification of already-computed
  metrics.
- **Priority**: MUST-RUN (feeds L2.2 directly), but its *standalone*
  narrative weight is secondary — see `CLAIM_TO_EXPERIMENT_MATRIX.md`.
- **Main paper or appendix**: main paper as a supporting section/ablation
  for L2.1/L2.2, not a standalone claim (per Session 1 Candidate 3).

### L1.5 — Q4 Performance and Risk Audit

- **Research question**: how do native Q4 policies actually perform and
  what risk do they carry, under one common evaluation engine?
- **Hypothesis**: none (this is a descriptive audit, not a claim test) —
  it is a **required precondition** for L2.2/L2.3/L2.5/L2.6's baselines.
- **Input**: `Q4Policy`/`PolicyDecisionStep` output from every TIER-1 Q4
  adapter (7 confirmed Q4-causal adapters with 0 violations across 344 real
  decisions per `ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.
  md`, plus the newly-integrated Q4 adapters).
- **Target**: forward realized performance and risk profile of each
  policy's decision trajectory.
- **Experimental unit**: one adapter's Q4 policy trajectory over the
  Controlled Scientific Track's validation/test window.
- **Sample construction**: only adapters whose `PolicyType` genuinely
  produces a causal trajectory (`decisions` populated via repeated
  per-step calls) or an honestly single-point `STATIC_ALLOCATION` — reuse
  `finrl_adapter.py`'s already-documented, already-correct exclusion of its
  own in-sample trajectory (a causality-correct precedent this protocol
  extends system-wide, not a new rule).
- **Baseline**: CASH, equal-weight buy-and-hold, market benchmark (see
  `BASELINE_DESIGN.md`).
- **Method**: standard portfolio performance/risk computation under the
  Controlled Scientific Track's shared transaction-cost/benchmark/
  rebalancing assumptions.
- **Metric**: performance metrics and risk metrics, reported **separately**
  per the task brief's explicit instruction (see `METRIC_DESIGN.md`).
- **Expected evidence**: a per-adapter Q4 performance+risk table under one
  fair protocol — this table itself is the direct answer to Session 1
  adversarial review's "financial-evaluation hygiene" risk-table entry.
- **Failure interpretation**: wide native-vs-controlled performance
  divergence for a given adapter is expected and informative (quantifies
  the cost of unification) — report, do not suppress.
- **Dependencies**: none upstream; depends on `Q4_EXPERIMENT_REQUIREMENTS.md`
  being satisfied by Session 4's rolling protocol before this group can run
  on more than a pilot slice.
- **Estimated cost**: medium-high — full rolling execution over a real
  validation window for every Q4 adapter.
- **Priority**: MUST-RUN (feeds every L2 group as the fixed-system
  baseline).
- **Main paper or appendix**: main paper (performance table), full risk
  breakdown in appendix.

---

## 6. Layer 2 method groups

Every group below runs **only** on the Controlled Scientific Track (§4) and
consumes **both** raw canonical Q1–Q4 outputs and Layer 1 diagnostic
features, per the task brief's explicit two-layer wiring requirement — see
the ablation in Cross-Cutting X.2 for the "raw-only / Layer1-only / both"
decomposition that makes this wiring's necessity falsifiable rather than
assumed.

### L2.1 — Reliability-/Contradiction-Weighted Fusion

- **Research question**: H2 (does calibration+contradiction-weighted
  fusion beat naive aggregation and, non-negotiably per Session 1, a
  TrustTrade-style agreement-weighting baseline and a ContestTrade-style
  outcome-utility-weighting baseline?).
- **Input**: Q1/Q3 votes from TIER-1 adapters + L1.2 calibration weights +
  L1.3 contradiction penalty.
- **Target**: fused directional decision; evaluated on `E` (prediction
  accuracy) and, where a Q4 wrapper is added, on portfolio performance/risk
  (reusing L1.5's engine).
- **Experimental unit**: one fused decision per `(ticker, as_of, horizon)`.
- **Sample construction**: L1.2's calibration curves are already fixed
  (fit on the Calibration interval, per `DATA_SPLIT_PROTOCOL.md` §1) before
  this group runs. L2.1's own fusion weights (which *combine* those
  already-fixed calibration scores with §2.2's contradiction penalty into a
  weighting formula) are the Layer 2 parameter being fit here, on the
  Controlled Scientific Track's Validation interval only, never on test
  (corrected — a prior version of this bullet's wording, "calibration
  weights are fit only on validation," conflated L1.2's calibration fit
  with L2.1's own fusion-weight fit and cited a nonexistent "§9"; see
  `DATA_SPLIT_PROTOCOL.md` §1/§1.1 for the single corrected rule); final
  test set for the one-shot evaluation.
- **Baseline**: majority vote, equal-weight vote, raw-self-reported-
  confidence weighting, **TrustTrade-style cross-agent agreement weighting
  (non-negotiable per Session 1)**, **ContestTrade-style outcome-utility
  weighting (non-negotiable per Session 1)** — see `BASELINE_DESIGN.md`.
- **Method**: L2.1's own mechanism is the *simplified* Exp17 instance — a
  linear/weighted-vote combination (not a trained black-box meta-model;
  that is reserved for L2.6) weighted by (a) measured out-of-sample
  calibration and (b) a penalty when §2.2's `C` fires.
- **Metric**: directional accuracy, Brier, selective risk; portfolio-level
  metrics where wrapped into a Q4 decision (`METRIC_DESIGN.md`).
- **Expected evidence**: L2.1 beats naive baselines AND the TrustTrade-
  /ContestTrade-style baselines, **with the "correct lone dissenter"
  ablation** (a case-study slice where calibration-weighting and
  agreement-weighting provably diverge, per Session 1's non-negotiable
  condition) showing calibration-weighting's structural advantage
  concretely, not just in the aggregate metric.
- **Failure interpretation**: if L2.1 does not beat the TrustTrade-style
  baseline, Session 1's own Codex reviewers already predicted this is the
  single most likely failure mode ("danger zone") — report honestly; H1
  (§2.1) is unaffected by this outcome (Fallback Claims §2.6).
- **Dependencies**: L1.1, L1.2, L1.3 (feature freeze), L1.5 (baseline
  engine).
- **Estimated cost**: medium — mostly post-hoc recombination of already-
  computed decisions plus the two competitor-baseline implementations.
- **Priority**: MUST-RUN, primary decision-layer claim.
- **Main paper or appendix**: main paper.

### L2.2 — Reliability-Aware Routing

- **Research question**: H7; is routing across independently-authored real
  systems, under one causal harness, better than a FineFT-style
  within-framework VAE-routing baseline retrained on this project's data?
- **Input**: L1.4's adapter×regime×horizon reliability table; L1.5's fixed
  Q4 policies as the routable candidate set.
- **Target**: routed decision trajectory, evaluated via L1.5's engine.
- **Experimental unit**: one routing decision per legal rebalance point.
- **Sample construction**: router fit on the Validation interval only
  (`DATA_SPLIT_PROTOCOL.md` §1); final test is a single held-out
  evaluation (corrected — a prior version cited a nonexistent "§9"; the
  final-test-touched-once rule lives in `DATA_SPLIT_PROTOCOL.md` §1's
  "Untouched final test" row).
- **Baseline**: random router, static global-best adapter, round-robin,
  regime-blind learned router, recent-performance router,
  **FineFT-style within-framework VAE-routing baseline retrained on this
  harness's data (non-negotiable per Session 1)**, oracle upper bound
  (**deployability flag = non-deployable**, upper-bound-only, per
  `BASELINE_DESIGN.md`).
- **Method**: rule-based or lightweight learned router conditioned on
  regime/horizon/L1.4's measured reliability; must never see future
  performance (see `RISK_AND_FAILURE_PLAN.md`'s leakage section).
- **Metric**: L1.5's performance+risk metrics, plus routing-specific
  metrics (regret vs. oracle, router stability).
- **Expected evidence**: routing beats the full baseline ladder including
  FineFT-style routing — the single most demanding bar in this protocol,
  Session 1 flagged this as the least-implemented, highest-risk claim.
- **Failure interpretation**: a result no better than the best fixed system
  or naive blending is the specific failure mode Session 1's Codex reviewer
  named ("standard dynamic ensemble selection") — report as a negative
  result for the *routing* sub-claim without automatically invalidating
  L2.3 (shadow policy), which Session 1 rates as the stronger half.
- **Dependencies**: L1.4, L1.5.
- **Estimated cost**: high — full multi-baseline ladder under rolling
  execution.
- **Priority**: MUST-RUN, second primary decision-layer claim.
- **Main paper or appendix**: main paper.

### L2.3 — Shadow Q4 Policy Construction

- **Research question**: H6.
- **Input**: one system's Q1/Q3 selection+ranking output + another
  system's Q2/Q4 risk-adjustment output, recombined causally.
- **Target**: synthetic shadow policy trajectory, evaluated via L1.5's
  engine.
- **Experimental unit**: one shadow-policy decision trajectory per
  (selection-source, risk-source) pair tested.
- **Sample construction**: pairs chosen to maximize paradigm diversity
  (e.g. an alpha-factor-mining adapter's Q3 ranking + a portfolio-RL
  adapter's Q2/Q4 risk adjustment) — a small, deliberately-scoped pair set,
  not a combinatorial sweep across all adapter pairs (cost control, see
  `RISK_AND_FAILURE_PLAN.md`).
- **Baseline / attribution controls (synced from `CLAIM_TO_EXPERIMENT_
  MATRIX.md`'s H6 row into this main protocol section — Task B4, Session
  3)**: each source system's own native Q4 policy (fixed), equal-weight
  blend, **plus four required attribution controls**, not optional:
  `donor-Q1/Q3-only` (the donor's selection/ranking alone, no borrowed risk
  module), `recipient-native-policy-only` (the recipient's own unmodified
  policy), `shuffled-Q1/Q3 placebo` (the donor's Q1/Q3 output randomly
  permuted across tickers/dates before recombination, breaking any real
  signal while preserving its marginal distribution), and
  `risk-module-only with neutral selection` (the recipient's Q2/Q4 risk
  adjustment applied to a neutral/equal-weight selection instead of the
  donor's real Q1/Q3 ranking). **"Q4-weak" status for candidate donor
  systems must be defined ex ante** (e.g. via L1.5's audit) before pairs
  are chosen, not post-hoc.
- **Method**: causal recombination under the shared execution harness
  (`Q4_EXPERIMENT_REQUIREMENTS.md`); the Q1/Q3/Q4 decomposition must be
  well-defined and causal, not post-hoc signal stacking (Session 1's
  explicit condition for this to read as principled).
- **Metric**: L1.5's performance+risk metrics.
- **Expected evidence**: shadow policies outperform at least one of their
  two source systems' native policies on a risk-adjusted basis, **and**
  outperform the `risk-module-only` control — **if the shadow policy beats
  the native baselines but does not beat `risk-module-only`, the paper may
  not claim the donor's Q1/Q3 information contributed incremental value**
  (the gain would be indistinguishable from the risk module alone); this is
  a hard, non-optional attribution requirement, not a nice-to-have
  ablation.
- **Failure interpretation**: if shadow recombination looks arbitrary/
  underprincipled, this is a framing failure Session 1's Codex reviewer
  explicitly warned about — the decomposition rule must be published
  before results, not adjusted after.
- **Dependencies**: L1.5.
- **Estimated cost**: medium.
- **Priority**: MUST-RUN — per Session 1, this is "the stronger, more
  defensible half" of the routing/shadow-Q4 claim.
- **Main paper or appendix**: main paper.

### L2.4 — Contradiction-/Reliability-Aware Intervention (Abstention)

- **Research question**: H3; is structural contradiction (§2.2) a useful
  risk-reduction trigger in its own right, distinct from ordinary
  uncertainty/confidence/dispersion baselines (per Session 1 Codex Phase C)?
- **Input**: L1.3's `C` signal (and severity score) + L1.2's calibration/
  stability signal.
- **Target**: abstain/reduce-position/increase-cash decision, evaluated on
  drawdown/tail-risk primarily, return secondarily.
- **Experimental unit**: one intervention decision per legal rebalance
  point.
- **Sample construction**: same validation/test split as L2.1 (they share
  the same diagnostic signal by design, per Session 1's fuse-vs-abstain
  framing).
- **Baseline**: no intervention, random intervention, fixed cash buffer,
  binary-disagreement-count rule, entropy/dispersion rule (see
  `BASELINE_DESIGN.md`).
- **Method**: threshold-triggered abstain/reduce/increase-cash policy keyed
  to `C` and L1.2's reliability score; thresholds fit on validation only.
- **Metric**: coverage-risk curve, selective accuracy, drawdown reduction,
  turnover reduction, portfolio opportunity cost (`METRIC_DESIGN.md`).
- **Expected evidence**: intervention beats the dispersion/entropy baseline
  specifically on drawdown/tail-risk, demonstrating that *structural*
  contradiction (not mere disagreement magnitude) is the useful signal —
  this is the exact ablation Session 1's Codex reviewer said the paper
  needs.
- **Failure interpretation**: if intervention performs no better than a
  generic dispersion rule, this specifically weakens the "structural
  contradiction is special" framing (not H1 itself, which only requires
  incremental *predictive* information, not intervention *value*) —
  report as a distinct, separable finding.
- **Dependencies**: L1.2, L1.3.
- **Estimated cost**: low-medium — reuses L2.1's signal computation.
- **Priority**: MUST-RUN as an ablation arm of L2.1 (per Session 1's fold-
  in recommendation), not a standalone claim.
- **Main paper or appendix**: main paper (as an ablation subsection inside
  L2.1's results), not a separate headline section.

### L2.5 — Validation-Conditioned Policy Selection

- **Research question**: can rolling validation performance alone (Sharpe,
  drawdown, turnover, stability, regime-conditioned performance,
  contradiction with Q1–Q3) dynamically select the active Q4 policy?
- **Input**: L1.5's rolling performance/risk history.
- **Target**: dynamically-selected policy trajectory.
- **Baseline/Method/Metric**: reuses L1.5's engine and L2.2's baseline
  ladder machinery (this group *is* one of L2.2's required baselines —
  "rolling-performance selector" — promoted to its own experiment group
  because the task brief lists it as Exp16 in its own right).
- **Dependencies**: L1.5.
- **Estimated cost**: low (shares machinery with L2.2).
- **Priority**: NICE-TO-HAVE / supporting — required as an L2.2 baseline,
  optional as a standalone result.
- **Main paper or appendix**: appendix (as a baseline ladder entry inside
  L2.2); not a headline result on its own.

### L2.6 — Lightweight Multi-View Meta-Fusion

- **Research question**: does a trained (but still lightweight,
  interpretable-first per the task brief's explicit instruction) meta-layer
  over Q1–Q4 + Layer 1 features beat L2.1's simple weighted-vote fusion
  enough to justify its added complexity?
- **Input**: full Q1–Q4 + all Layer 1 diagnostic features.
- **Target**: final action/ranking/weight-adjustment/policy-selection/risk-
  budget decision (task brief's candidate output list).
- **Baseline**: **L2.1 itself is the primary baseline this group must
  beat** — per `research-refine`'s "smallest adequate mechanism" principle,
  this group exists specifically to prove complexity is earning its keep,
  not to add a second unmotivated fusion method.
- **Method**: shallow/interpretable model class first (linear, shallow
  tree/boosting); explicitly avoid an opaque deep meta-model unless the
  simpler classes demonstrably fail (task brief's explicit instruction to
  prefer lightweight/interpretable).
- **Metric**: same as L2.1, plus a complexity-adjusted comparison (does the
  gain, if any, exceed what added parameters/opacity would predict by
  chance — see `RISK_AND_FAILURE_PLAN.md`'s overfitting section).
- **Failure interpretation**: no material gain over L2.1 is a **positive**
  finding for the paper's parsimony argument, not a failed experiment —
  explicitly framed this way in advance.
- **Dependencies**: L2.1 (must exist first as the baseline to beat).
- **Estimated cost**: medium.
- **Priority**: NICE-TO-HAVE / optional enhancement.
- **Main paper or appendix**: appendix only, unless it meaningfully beats
  L2.1 (in which case it is a candidate to *replace* L2.1 as the main
  fusion result — a decision left to the human checkpoint after results
  exist, per `EXPERIMENT_DEPENDENCY_MAP.md`).

---

## 7. Cross-cutting evaluation

### X.1 — Field and Source Ablation

Ladder (not combinatorial): Q1-only → Q1+confidence → Q1 without
explanation → Q2 state-only → Q2 without drivers → Q3 values-only → Q3
without evidence → Q4 without trajectory → Q4 without policy metadata →
native-fields-only → derived-fields-only → remove provenance → remove
Layer 1 reliability features. A **primary rung + a small supplementary set**
(per the task brief's explicit instruction to avoid combination explosion)
— the primary rung is "raw Q1–Q4 only" vs. "raw + Layer 1 features," since
that is the one ablation every Layer 2 claim structurally depends on
(§5 intro; H5).

### X.2 — Information Pathway Ablation

Q1-only / Q2-only / Q3-only / Q4-only / Q1+Q3 / Q1+Q2+Q3 / Q4+validation-
history / raw-Q1–Q4-only / Layer1-features-only / raw+Layer1 / all — run
against L2.1's fusion output and L2.2's routing output as the two
consuming methods. This is the ablation that makes the two-layer wiring
requirement (raw *and* Layer 1 features must both feed Layer 2) falsifiable
rather than assumed, directly answering §5's "not two disconnected
experiment sets" instruction.

### X.3 — Robustness, Transaction-Cost Sensitivity, Seed/Repeated-Run, Cost & Latency

- Transaction-cost sensitivity: re-run L1.5/L2.1–L2.3's headline results
  under 2–3 cost regimes (zero cost as an upper bound, a realistic
  cost, a stressed/high cost) to check claim stability.
- Seed/repeated-run: reuses L1.2's stability machinery, applied to any
  stochastic component *this protocol itself* introduces (e.g. L2.6's
  trained meta-model, if pursued) — distinct from L1.2's *adapter-level*
  stability audit.
- Cost and latency: aggregate `RunMetadata.cost_usd`/`latency_sec` (already
  a schema-native field, populated by every adapter) across the full
  experiment set — required for the compute-budget gates in
  `EXPERIMENT_DEPENDENCY_MAP.md` and for honest disclosure per the
  Session-1-cited "benchmark disclosure" literature finding (arXiv
  2605.21404 — financial/agent benchmarks under-disclose cost/methodology
  relative to classical benchmarks).

### X.4 — Failure Case Analysis

Qualitative review of the largest-error/largest-contradiction-severity
cases in L1.3/L2.1/L2.4's output, cross-referenced against
`ADAPTER_CAPABILITY_RECOVERY.md`'s already-documented real defects (e.g.
the FinRL in-sample-trajectory exclusion, the FinBERT non-point-in-time
news source) to check whether known engineering limitations, rather than
the phenomena under test, explain outlier cases.

## 8. Adversarial review (`kill-argument`-adapted)

`kill-argument`'s literal trigger targets LaTeX theorem-papers; its
attack→adjudicate methodology was applied directly to this markdown
protocol instead (disclosed, matching the pattern Session 1 used for the
same adaptation). Two real, fresh `mcp__codex__codex` calls, never
`codex-reply` (per the skill's fresh-thread requirement): attack thread
`019f7c86-3730-7823-bb0a-5a8a2a367376`, adjudication thread
`019f7c88-0e7b-7f40-809b-2b7a92753ce4`, both `model_reasoning_effort:
high`, `sandbox: read-only`. Full transcript in
`_working/ADVERSARIAL_REVIEW.md`.

**Attack (verbatim summary)**: H1's acceptance surface is not fully
frozen — contradiction severity is "optionally scaled," the practical-
significance threshold is deferred without a specified procedure, H1 can
be declared supported from a single significant stratum (inviting
post-hoc stratum selection), and adapter/universe/horizon eligibility can
narrow scope after the fact — collectively enough registered flexibility
that a positive result could reflect validation-stage selection rather
than a genuine model-agnostic signal.

**Adjudication**: 5 atomic points, **0 answered_by_current_text, 4
partially_answered (major), 1 still_unresolved (critical — H1 was not
shown to be distinguishable from generic cross-adapter disagreement,
independent of the structural-contradiction ontology specifically)**.
Per the skill's verdict-mapping convention (any `still_unresolved` at
critical severity → **FAIL**, `reason_code: unresolved_critical`), this
protocol's H1 design **failed** this adversarial pass as originally
written.

**Fixes applied in direct response** (§2.3.1, §2.3.2, §2.4, §2.4.1, §2.2):
H1-specific negative controls (generic disagreement, missingness, adapter-
pair fixed effects, per-ontology-class breakdown) added as required
covariates, not optional; the primary acceptance criterion changed from
"significant in ≥1 stratum" to a pooled whole-deployment test (stratum
results demoted to secondary/exploratory); a concrete power-analysis
*procedure* (not a bare deferral) pre-registered for the practical-
significance threshold; severity scoring demoted from H1's primary
exposure to a secondary, fixed-formula-only measure, with binary `C` as
the sole primary exposure; a minimum-coverage floor (paradigms/adapters/
horizons/regimes) added for H1 to remain the paper's primary claim.

**Second pass — `research-refine`-adapted check for over-correction**: per
that skill's governing "smallest adequate mechanism" principle, a real
Codex call (thread `019f7c8c-bf7c-7b23-b596-02cf2bba2264`,
`model_reasoning_effort: high`) checked whether the five fixes above
over-corrected into unnecessary complexity. Verdict: **REVISE** (not
READY, not RETHINK) — two concrete simplifications, both adopted:
(a) §2.3.1's adapter-pair control and §2.3.2's pooled-model adapter-pair
effect are now written as **one model specification**, not two stacked
terms, defaulting to a random effect/partial pooling rather than a fixed
effect (sparse fixed effects can cost more power than they buy in rigor);
(b) §2.4.1's minimum-coverage floor was rewritten from hand-picked numeric
counts (which the reviewer judged over-prescriptive for a pre-registration
document with no pilot data yet) to a principle-plus-downgrade-path now,
with the exact numeric tiers computed *as part of* §2.4's power-analysis
procedure at the pilot stage — one combined calculation, not two separate
gates.

**What this session does not claim**: these fixes were made by the same
session that received the critique, not independently re-adjudicated by a
fresh reviewer thread — per `kill-argument`'s own rule that "the verdict
is computed by the skill, not by the adjudicator" (i.e. self-grading after
a fix is not equivalent to a real pass), **this protocol's H1 design
should be treated as FAIL-with-fixes-applied-but-not-re-verified**, not as
a confirmed PASS, even after the second (research-refine-adapted, REVISE-
verdict) pass — that pass checked for over-correction, it did not
re-run the original kill-argument adjudication against the revised text.
A genuine re-adjudication (a fresh Codex thread, reading only the
post-fix files, blind to this history) is the correct next step before
this protocol is treated as fully hardened — flagged here explicitly
rather than silently upgrading the verdict, and listed as an open item in
the final terminal summary.

### Ablation-design cross-check (genuine `ablation-planner`-adapted Codex call)

`ablation-planner`'s literal trigger ("after `result-to-claim` passes") is
unmet — no experiment has run. Its Codex-leads-design methodology was
applied prospectively instead: a real `mcp__codex__codex` call
(thread `019f7c7c-b95d-7361-a190-3a7f89e9ef74`, `model_reasoning_effort:
high`, `sandbox: read-only`) reviewed X.1/X.2 above and returned three
concrete findings, all incorporated:

1. **The single primary rung needs one more sibling to stay diagnostic of
   H1 specifically, not just "Layer 1 helps."** Verbatim: *"reviewers may
   ask whether the gain comes specifically from contradiction or from any
   Layer-1 metadata bundle... the main table should include at least
   `raw + Layer1-minus-contradiction` or `raw + contradiction-only`.
   Otherwise H1 is diluted."* **Incorporated**: X.1's main-paper-load-
   bearing rung is now a 3-point comparison, not 2: `raw Q1–Q4 only` vs.
   `raw + Layer1-minus-contradiction` (calibration/stability/regime
   features, no `C`) vs. `raw + full Layer1 (incl. contradiction)` — this
   isolates §2.2's `C` signal specifically from the rest of the Layer 1
   bundle, which the flat "raw vs. raw+Layer1" framing in the original
   draft could not do.
   2. **Confirmed, not new**: the leave-one-adapter/leave-one-ticker
   robustness check already specified in §2.4's H1 robustness requirement
   is independently the reviewer's top-priority missing ablation
   ("more important than finer Q-field ablations... If only one pair or
   ticker carries the effect, H1 is not model-agnostic"). No draft change
   needed here — this is a genuine independent confirmation that §2.4 was
   already right to require it, not a new addition.
3. **Cuts/demotions to appendix-only**, all accepted: `Q3 values-only`
   (underspecified without a fixed economic meaning), `Q4 without policy
   metadata` (narrow, relevant only if policy metadata proves central to
   L2.2 routing — re-promote only if L2.2 results show it matters),
   `native-fields-only`/`derived-fields-only` (appendix-only — an
   adapter-engineering diagnostic, closer to L1.1 than to a Layer-2
   hypothesis test), and one of `Q2 without drivers`/`Q3 without evidence`
   (redundant — keep one, drop the other; keep `Q3 without evidence` as
   more directly load-bearing for the calibration story, drop `Q2 without
   drivers`).

