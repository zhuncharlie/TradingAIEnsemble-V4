# Candidate Paper Directions — trading-ai-ensemble → ICAIF

Generated 2026-07-19. Grounded in: (1) the actual current repo state (26 adapters,
CONTRACT/schemas.py v2.0.0, harness/q4_protocol.py + execution_engine.py causal
Q4 stepwise engine, 167 tests, all finished 2026-07-17→19); (2) the **stale but
real** v1-schema diagnostic results in
`reports/icaif_experiments_backup_20260710T110429_pre_exp4_expansion/` (15
adapters, 292 observations, 5 experiments — coverage, secondary-field value,
calibration, 19-rule contradiction detection, 3-method fusion ablation); (3) the
literature landscape in `LITERATURE_MAP.md`. See `NOVELTY_AUDIT.md` for the
prior-art verdict on each direction and `ICAIF_POSITIONING.md` for the
recommended sequencing.

**Read this first**: none of the four directions below can be submitted as-is
today. Every one requires rebuilding `analysis/icaif_*.py` against schema
v2.0.0 and the 26-adapter roster (the existing pipeline still imports
`Q1Decision`/`Q4Portfolio`/`Q5Backtest`, which no longer exist), plus real new
experiment runs. What differs between directions is *how much* new
infrastructure work is required beyond that rebuild, and how much of the
underlying empirical finding is already known (from the v1 run) versus still
untested. This is stated per-direction below, not glossed over.

---

## A. Reliability- and Contradiction-Aware Multi-View Fusion of Financial AI Agents

### Research Question
Does explicitly modeling (i) per-adapter calibration reliability and (ii)
detected cross-agent contradictions in a fusion weight improve decision
quality over naive majority-vote or confidence-weighted fusion, across
financial AI systems that compute "confidence" via mutually incompatible
mechanisms?

### Hypothesis
A fusion rule that down-weights adapters in proportion to their *measured,
out-of-sample* calibration error (not their self-reported confidence) — on
top of the existing risk/validation/contradiction/evidence-agreement
multipliers — will (a) suppress the specific known failure mode already found
in the v1 run (a poorly-calibrated adapter's full-weight vote overpowering a
better-calibrated adapter's correct call) and (b) produce a statistically
distinguishable improvement over majority vote and confidence-weighted vote,
where the v1 attempt at this (`interwoven_calibrated_fusion`) did not, because
it never actually included a calibration-reliability term.

### Method
1. Port `analysis/icaif_data_loader.py` / `icaif_metrics.py` /
   `icaif_contradictions.py` / `icaif_fusion.py` to schema v2.0.0
   (`Q1Action`/`Q2State`/`Q3Signal`/`Q4Policy`, `ConfidenceEstimate.kind`,
   open-vocabulary `StateEstimate.dimension`) and the 26-adapter roster.
2. Add a **calibration-reliability score**: a rolling, out-of-sample hit-rate
   vs. self-reported-confidence residual per (adapter, question, regime),
   updated causally (only using observations strictly before the decision
   being scored — mirrors the causality discipline already enforced by
   `harness/execution_engine.py::enforce_causality`).
3. Insert it as a 5th multiplier into `interwoven_calibrated_fusion`
   (`analysis/icaif_fusion.py`), alongside the existing risk / validation /
   contradiction / evidence-agreement multipliers.
4. Use `harness/q4_protocol.py`'s causal stepwise engine to generate a much
   larger, causally clean sample for the 10 STEPWISE-capable Q4 adapters
   (cheap — no LLM cost) and combine it with a cost-budgeted number of fresh
   Q1–Q3 LLM/GP/ensemble-adapter snapshots for breadth.

### Experiments
- **A1 — Replicate-and-fix**: re-run the v1 fusion ablation (majority vs.
  confidence-weighted vs. interwoven) on v2/26-adapter data, with bootstrap
  confidence intervals on hit rate and mean return (the v1 result, 60.7% vs.
  57.1% vs. 57.1% on n=30, carries no reported significance test and should
  not be treated as established).
- **A2 — Multiplier ablation**: turn each of the 5 multipliers on/off
  independently to identify which one(s) actually move the outcome — directly
  answers the v1 report's own open question ("the interwoven formula never
  incorporated calibration reliability, which is why B and C were identical").
- **A3 — Regime-stratified comparison**: split by Q2 `market_regime`
  `StateEstimate` and re-run A1 per regime, to test the project's own stated
  hypothesis #5 ("reliability changes across regimes") — **currently
  completely untested**, not just under-tested (see `NOVELTY_AUDIT.md`).

### Baselines
Majority vote; confidence-weighted vote; the current (calibration-blind)
interwoven fusion, kept in as an ablation baseline rather than discarded;
single-best-adapter-in-hindsight as a disclosed, explicitly-unfair upper
bound (never presented as achievable).

### Expected Contribution
1. An empirical demonstration, on 26 real independently-verified systems
   spanning 6+ methodological paradigms, that naively combining
   "confidence-like" fields that were never designed to be comparable
   (`ConfidenceKind.SELF_REPORTED` vs. `MODEL_MARGIN` vs. `HEURISTIC`, etc.)
   is unsafe, with a specific, previously root-caused failure case as a
   worked example.
2. A concrete, implemented fix (the calibration-reliability multiplier) that
   closes a gap the project's own prior report explicitly diagnosed but did
   not implement — a defensible, falsifiable claim rather than a vague
   "our fusion is better" pitch.
3. A reusable schema + harness (already built, already open) other groups
   could apply to their own heterogeneous agent rosters.

### Risk
- **Small-N**: the v1 fusion ablation had only 30 scoreable (ticker, date)
  groups. Causal Q4 data helps for the 10 STEPWISE adapters but Q1–Q3
  (LLM/GP/ensemble) breadth is bounded by real API/compute cost — this may
  force a narrower, more honestly-scoped claim (e.g. Q4-only, or a disclosed
  small-N diagnostic study rather than a large-scale benchmark claim).
- **The core result could replicate as null** (reliability-aware fusion
  doesn't beat majority vote even after the fix) — this is a legitimate,
  publishable negative/nuanced result if honestly reported, but the framing
  must not force a positive result that the data doesn't support.
- **Statistical testing is currently absent everywhere in this project** —
  must be added before any comparative claim, not optional polish.

### ICAIF Fit
Strong. Matches the "ensembling/robustness" cluster (see `LITERATURE_MAP.md`
— e.g. "Online Ensemble Learning for Sector Rotation: A Gradient-Free
Framework", ICAIF'25). Differentiate explicitly from "FactorMAD"
(LLM-only multi-agent debate for factor mining) by covering non-LLM
paradigms and by being about *reliability-weighted fusion*, not
debate-based rank aggregation.

---

## B. Calibration and Stability Evaluation of Heterogeneous Financial Agents

### Research Question
When 26 independent systems each compute something called "confidence" or
"strength" via mutually incompatible mechanisms (the v1 audit already found 7
distinct formulas across 9 adapters), what does that value actually measure,
is any of it calibrated, and is it even *stable* under repeated identical
queries?

### Hypothesis
(i) Calibration quality correlates with `ConfidenceKind` category — i.e., the
open taxonomy already present in `CONTRACT/schemas.py` (`PROBABILITY`,
`SELF_REPORTED`, `MODEL_MARGIN`, `SCORE_NORMALIZED`, `ENTROPY_DERIVED`,
`HEURISTIC`) predicts calibration behavior better than adapter identity alone.
(ii) Some adapters are not merely miscalibrated but **non-deterministic** —
the v1 report already root-caused one case (`deepalpha`'s unseeded
per-call retraining) — and this is a distinct, cheaply-detectable defect
class that a naive single-query calibration study would misattribute to
"miscalibration."

### Method
1. Rebuild the v1 calibration pipeline (`icaif_metrics.build_calibration_table`
   + `YFinanceFutureReturnProvider`) against v2 schema / 26 adapters, using
   `ConfidenceEstimate.kind` as a first-class grouping variable instead of
   inferring the mechanism from source-reading alone (the v1 approach was
   manual code audit — this promotes it to a structural, schema-driven
   comparison the schema itself was designed to support).
2. **New**: a repeated-query stability experiment — call each adapter K times
   (K≈5–10) on frozen identical inputs, measure output variance
   (action-flip rate for Q1, weight-vector distance for Q4, value spread for
   Q2/Q3). This did not exist in the v1 suite; it was discovered ad hoc via
   code reading for one adapter (deepalpha) and never systematized.
3. Regime-conditioned calibration: repeat the calibration table split by Q2
   `market_regime`.

### Experiments
- **B1**: reliability diagrams grouped by `ConfidenceKind`, not by adapter —
  tests whether the taxonomy itself is doing analytic work.
- **B2**: stability variance test across all 26 adapters — systematizes and
  generalizes the deepalpha finding; flags every adapter whose variance
  exceeds a disclosed threshold, the same honest-flagging discipline the v1
  `overconfidence_flags.csv` already used.
- **B3**: regime-conditioned calibration-error comparison, same untested-
  hypothesis caveat as direction A's A3.

### Baselines
Perfect-calibration reference line (standard reliability-diagram baseline); a
post-hoc isotonic/Platt recalibration fit as an "achievable calibration"
reference, not a deployed component.

### Expected Contribution
A taxonomy-grounded empirical map of what "confidence" means across a real,
large (26-system), multi-paradigm deployment, directly useful to anyone
building a fusion layer on top (i.e., this is a natural prerequisite study
for direction A). The stability-variance diagnostic is a genuinely new,
cheap, automatable defect-detection method not present in the v1 suite.

### Risk
The core danger is that this reads as "we measured stuff" without a sharp
analytic contribution — calibration measurement alone is well-trodden (see
`LITERATURE_MAP.md`'s UQ cluster). The `ConfidenceKind`-conditioned analysis
and the stability-variance method are the parts that must carry the paper;
if those don't show a clean structural signal, this direction weakens to a
workshop-note-level contribution, not a full ICAIF paper. Recommend treating
B as a strong **complementary section inside direction A** rather than a
fully separate submission unless the stability-variance result is unusually
sharp (see `ICAIF_POSITIONING.md`).

### ICAIF Fit
Moderate-strong; must differentiate clearly from single-model UQ papers at
ICAIF'25 ("Predictive Uncertainty Quantification for Financial DNN Using
Regular Vine Copula", "Scaling Conditional Autoencoders for Portfolio
Optimization via Uncertainty-Aware Factor Selection") by being explicitly
cross-system and semantics-first (what does the number *mean*) rather than
distributional (what is the number's uncertainty).

---

## C. Risk-Aware Routing and Policy Selection for Financial AI Systems

### Research Question
Given the just-finished causal Q4 stepwise harness (10 real `STEPWISE`
adapters spanning 4 policy lifecycle categories — online-adaptive, rolling-
optimizer, frozen-learned ×6, static — all driven through one shared
causality- and constraint-enforcing execution engine with 0 violations across
every real run to date), can a regime- or reliability-aware router that
switches which underlying adapter's decision to execute at each step
outperform any single fixed policy type, under identical constraints and
identical causally-disclosed information?

### Hypothesis
No single `PolicyType` dominates across market regimes (a direct instance of
the project's stated hypothesis #5); a router conditioned on Q2 regime state
and/or each adapter's trailing realized reliability improves risk-adjusted
outcomes — or at minimum reduces worst-case drawdown-proxy / turnover
exposure — relative to any fixed adapter, while inheriting the harness's
existing zero-causality-violation, zero-constraint-violation guarantee (the
router must not be allowed to erode that guarantee — this is a hard
correctness requirement, not just a performance one).

### Method
This is the direction requiring the **most net-new experimental work**,
because the enabling infrastructure (`harness/q4_protocol.py`,
`execution_engine.py`, `portfolio_state.py`) was finished 2026-07-18 and has
only been exercised at smoke-test scale (20–70 steps per adapter; see
`HARNESS_INFRASTRUCTURE_FINAL.md` §4/§4b) — **zero large-scale, multi-regime
experiments have been run through it yet**.
1. Extend `tools/run_large_scale_experiment.py`'s manifest-driven dispatch to
   run all 10 STEPWISE adapters over a shared, multi-year, multi-regime
   window (scaling up the existing 4-category coordinated mini-experiment in
   `Q4_STEPWISE_MIGRATION.md` §4b from 20 steps to a real backtest-length
   run).
2. Build the router as an **evaluation-layer** function — not a new adapter,
   not a `CONTRACT/` change — that reads each step's `ExecutionResult`
   history (already logged by the engine) plus the Q2 regime signal, and
   selects which adapter's `PolicyDecisionStep.target_weights` to execute
   next. This keeps the router outside the protected contract, consistent
   with CLAUDE.md §3.
3. Score exclusively via harness-native bookkeeping already computed by
   `PortfolioLedger`/`apply_constraints` (turnover, constraint-violation
   counts, weight trajectories) plus real yfinance forward prices computed at
   the *evaluation* layer — never as a fabricated `Q4Policy` field (per
   CLAUDE.md §4, Sharpe/return/drawdown must never live on an adapter's
   output; here they live only in `analysis/`).

### Experiments
- **C1**: the first real large-scale exercise of the causal Q4 harness —
  proves the "ready for large-scale experiments" claim in
  `HARNESS_INFRASTRUCTURE_FINAL.md` §6 with an actual experiment, not just
  acceptance smoke checks.
- **C2**: regime-conditioned performance-per-`PolicyType` breakdown.
- **C3**: router vs. fixed-adapter vs. naive equal-weight-blend comparison,
  with constraint-violation/turnover accounting throughout.

### Baselines
Each of the 10 fixed STEPWISE adapters run individually over the same
window/universe; a naive equal-weight blend of all 10 adapters' weights at
each step (a static ensemble, not a router) as the non-adaptive baseline.

### Expected Contribution
The first genuinely large-scale, causally-audited, cross-paradigm comparison
of Q4 policy types under one shared execution semantics — this is a
systems+empirical hybrid contribution not really attempted yet anywhere in
this repo's own history (the v1 report's Q4/Q5 experiments were single-shot
weight-vector comparisons, not causal trajectories).

### Risk
This is the **least mature** direction relative to what currently exists —
most of the actual experiment is still to be built, not just rerun on new
schema. Multi-year real backtests are compute/time-costly even for
non-LLM adapters (several retrain per session — FinRL/DeepDow/EarnMore/etc.);
PGPortfolio is currently `BLOCKED` live (transient yfinance rate limit); and
a genuinely multi-regime window is required for the core hypothesis to be
testable at all, which raises both wall-clock cost and the chance of hitting
new, currently-undiscovered upstream bugs (as every prior large real run in
this project's history has — see `DECISIONS.md`/`ADAPTER_CAPABILITY_RECOVERY.md`
for the base rate of real bugs found per real large run).

### ICAIF Fit
Strong for the RL-portfolio / decision-focused-learning / regime-aware
cluster at ICAIF'25 (e.g. "Adaptive Sample Weighting with Regime-Aware
Meta-Learning Framework for Financial Forecasting", "Continuous-Time
Reinforcement Learning for Asset–Liability Management", "Long-Term Financial
Forecasting and Trading via Multi-Agent Reinforcement Learning") — must
differentiate by being explicitly a **system-of-systems** router across
independent real upstream projects (not one model trained with regime
features), which none of those papers are.

---

## D. A Causally-Correct Harness for Evaluating Heterogeneous Financial Policy Adapters (resource/systems framing)

### Research Question
How should a research harness enforce point-in-time causality and portfolio
constraints when driving *externally-authored, mechanistically incompatible*
policy systems (online learners, rolling re-optimizers, frozen-then-inferred
networks, static allocators) through one shared sequential-decision protocol,
without modifying any of their internal logic?

### Hypothesis
A structural (duck-typed, `typing.Protocol`-based) stepwise interface defined
*entirely outside* the shared output schema — so that adding causal
step-by-step execution to an adapter requires zero changes to its existing
one-shot `q4_policy()` method — can be layered onto real, independently
maintained open-source systems with zero causality violations and zero
silent constraint violations, across every policy lifecycle shape found in
practice.

### Method
This direction does not require new adapters or new fusion logic — it is
**already built and already evidenced**: `harness/q4_protocol.py` (the
`Q4StepAdapter` protocol, `MarketObservation`, `PortfolioState`),
`harness/execution_engine.py` (`enforce_causality`, `audit_trajectory`),
`harness/portfolio_state.py` (`apply_constraints`, clip-vs-reject
projection), and the `LEGACY_INTERNAL_LOOP` no-fabrication compatibility path
for adapters that haven't been migrated. The paper's job is to (1) write up
the design rationale and constraints already documented in
`Q4_STEPWISE_MIGRATION.md`/`HARNESS_INFRASTRUCTURE_FINAL.md`, (2) run it at
the C1-scale large experiment from direction C (shared infrastructure), and
(3) release the harness + schema + result corpus as the paper's actual
contribution artifact.

### Experiments
Reuses C1 (the scaled multi-regime run) as its primary evidence; adds an
explicit audit table of every causality/constraint check the engine performs
(already itemized in `HARNESS_INFRASTRUCTURE_FINAL.md` §2) with pass/fail
counts across the full run, plus a "what happens to a non-migrated adapter"
demonstration of the `LEGACY_INTERNAL_LOOP` honest-refusal behavior (already
unit-tested in `tests/test_q4_adapter_sessions.py`).

### Baselines
Not really applicable in the usual sense — the comparison is against the
*absence* of this layer, i.e., the project's own prior state (each adapter's
internal batch `q4_policy()` loop, uninspectable from outside, no external
causality check) is the "baseline" being improved on. Could additionally
compare against how well-known systems (e.g. Qlib's own `backtest_loop`)
handle this internally, to argue for the value of an adapter-external layer
when composing *multiple* independently-authored systems (which no single
upstream project's own harness is designed to do).

### Expected Contribution
A resource/systems contribution: a reusable, adapter-external causal
execution + constraint-enforcement harness for heterogeneous policy systems,
plus the released result corpus. Lower research risk than A/B/C since the
core artifact already exists and works; the main remaining work is running
it at genuine scale (shared with C1) and writing it up rigorously.

### Risk
Reads as "infrastructure paper" rather than a novel empirical finding —
ICAIF does have a resource/dataset-adjacent appetite (see `LITERATURE_MAP.md`,
e.g. FinDER, FinAgentBench, FinMR, PortBench, StockBench are all
benchmark/infrastructure contributions), but reviewers will ask "what did you
learn," not just "what did you build" — this direction is strongest paired
with C's actual experiment as evidence, not standing alone on architecture
description.

### ICAIF Fit
Good fit for a resource/benchmark-track-style submission or as the
infrastructure section of direction C rather than a fully separate paper —
see `ICAIF_POSITIONING.md` for the recommended sequencing (D's artifact as
the enabling layer C's experiment runs on top of).

---

## Recommended sequencing (summary — full reasoning in `ICAIF_POSITIONING.md`)

1. **Rebuild the v1 pipeline against v2/26 adapters first** — this blocks all
   four directions equally and is pure engineering, not research risk.
2. **A is the strongest standalone empirical candidate** — it has the richest
   already-diagnosed-but-unfixed real finding (the missing calibration term)
   to build on, and the smallest amount of *new* infrastructure required.
3. **B is best folded into A** as a diagnostic/related-work section unless
   its stability-variance result turns out unusually sharp on its own.
4. **C is the highest-ceiling but highest-risk/most-work direction** — worth
   pursuing only with a real multi-week experiment budget; D is its
   low-risk infrastructure-paper twin and can be written largely in
   parallel once C1's large run exists.
