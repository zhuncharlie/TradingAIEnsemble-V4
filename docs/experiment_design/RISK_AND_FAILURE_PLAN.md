# Risk and Failure Plan

**Role**: experiment protocol design only (Session 2). No experiment code
was written, no experiment was run, no adapter/schema/harness file was
touched. This document identifies risks and pre-registers mitigations; it
does not resolve them by running anything.

**Skill used, and how**: the ARIS `experiment-audit` skill's methodology
was applied *prospectively* — its literal trigger ("audit experiment
integrity... after experiments complete") cannot be met since nothing has
run. Instead of auditing existing results, its six-category adversarial
checklist (Ground Truth Provenance / Score Normalization / Result File
Existence / Dead Code Detection / Scope Assessment / Evaluation Type
Classification — `.claude/skills/experiment-audit/SKILL.md`) was pointed at
the **design itself**: for each category, "does the current protocol design
create an opportunity for this failure mode once experiments run, and does
the design already have a safeguard, or is one missing?" A real
`mcp__codex__codex` call was made with this adapted framing (thread
`019f7c81-5957-74e0-86df-8425c9945a36`, `model_reasoning_effort: high`,
`sandbox: read-only`) — full findings incorporated in §1 below, matching
the disclosure pattern already used for `ablation-planner` in
`EXPERIMENT_PROTOCOL.md` §6 (thread `019f7c7c-b95d-7361-a190-3a7f89e9ef74`).

All experiment-group IDs (L1.1–L1.5, L2.1–L2.6, X.1–X.4) and hypotheses
(H1–H7) below refer to `EXPERIMENT_PROTOCOL.md`.

---

## 1. Forward-looking integrity design audit (real Codex findings, incorporated)

| Category | Codex finding | Incorporated mitigation |
|---|---|---|
| **A. Ground Truth Provenance** | `E` (forward realized error) must never be defined or modified by any component prediction, ensemble output, confidence score, or contradiction label — only by ex-post market data | **Hard rule, added here**: `E`'s construction (`EXPERIMENT_PROTOCOL.md` §2.3) must cite an immutable, timestamped market-data source (vendor, snapshot time, corporate-action handling) independent of any adapter's own output. No adapter output may ever appear on both sides of the `C → E` test. |
| **B. Score Normalization** | Risk if confidence/error/contradiction-severity/routing-reliability are z-scored within a model's own output distribution — flatters weak/unstable systems | **Hard rule**: all normalization must use an externally fixed scale (e.g. `ConfidenceEstimate`'s already-schema-fixed [0,1] range, or a scale fit on validation data only and frozen before test), never a per-adapter self-referential normalization computed at evaluation time |
| **C. Result File Existence / Phantom Results** | Biggest risk: claiming "significant across strata" while some (adapter-pair × regime × horizon) cells were never computed, failed eligibility, or were silently dropped | **New requirement, added here**: before any final-test run, produce a **results manifest** listing every pre-registered stratum with status ∈ {`computed`, `ineligible`, `failed`, `excluded_by_predefined_rule`}, sample count, and result-file hash. Every claim in the eventual paper must trace to a `computed` manifest row — this is the deterministic, mechanical check `result-to-claim`'s own evidence pre-check (`shared-references/evidence-precheck.md`) performs, applied here at design time as a requirement rather than left implicit. |
| **D. Dead Code / Unused Safeguards** | FDR correction is the single easiest safeguard to skip in practice ("uncorrected per-stratum findings will look tempting and numerous") | **Hard gate, not a suggestion**: no H1 stratum may be reported as significant without Benjamini-Hochberg correction applied over the *complete* pre-registered stratum family (not a subset chosen after seeing results); block bootstrap is likewise mandatory, not optional, for any CI on financial time series |
| **E. Scope Assessment** | Main risk: "26 systems" language outrunning the actually-evaluated, live/point-in-time-eligible subset | **Hard rule** (already partially stated in `EXPERIMENT_PROTOCOL.md` §2.6's fallback table, reinforced here): every headline claim must use the evaluated `N` (TIER-1 count from `ADAPTER_REGISTRY_REQUIREMENTS.md`), never the aspirational catalog size of 26. "26 adapters implemented" and "N adapters in the claim-bearing evaluation" must never be conflated in one sentence. |
| **F. Evaluation Type** | H1 is `real_gt` only if `E` comes from realized market outcomes under the fixed Controlled Scientific Track rules; weakens toward `synthetic_proxy` if any label is backfilled, simulated, or inferred from model agreement | **Explicit classification requirement**: the eventual results write-up must state H1's evaluation type as `real_gt` and justify it against this checklist; the Native Capability and Compatibility Tracks must never be described as claim-bearing evaluations (already true per `EXPERIMENT_PROTOCOL.md` §4, restated here as a hard boundary) |

---

## 2. Leakage

| Risk | Concrete mechanism | Mitigation |
|---|---|---|
| Label leakage across generation/validation/test windows | A 20d-horizon label computed at day T uses information through T+20; if a later window starts immediately after the earlier one ends, the last ~20 days of the earlier window's labels overlap into the next window | **Embargo/purge gap ≥ max tested horizon (20 trading days)** between generation, validation, and final-test windows — specified fully in `DATA_SPLIT_PROTOCOL.md` §3 |
| `generation_window` misuse | `CONTRACT/schemas.py`'s own docstring: `Q4Policy.generation_window` is harness-supplied; "the adapter records this interval but must not choose, expand, shorten, or otherwise alter it" | This protocol never asks an adapter to choose its own window — validation/test window boundaries are defined exclusively in `DATA_SPLIT_PROTOCOL.md`/`Q4_EXPERIMENT_REQUIREMENTS.md`, never left to adapter discretion |
| In-sample trajectory exposure re-introduced at the Layer 2 level | `finrl_adapter.py` was **already found and correctly fixed** to withhold its full daily action-memory trajectory, because `env_gym` for prediction is the same environment the policy trained on — exposing every day as an independent causal decision would be a real, already-diagnosed leakage bug (`ADAPTER_CAPABILITY_RECOVERY.md` item 15) | **Regression-prevention rule**: any Layer 2 group (L2.2 routing, L2.3 shadow-policy, L2.5) that consumes a per-adapter trajectory must re-verify, per adapter, whether `decisions` reflects genuine causal per-step calls or an in-sample replay before using it — do not assume every adapter's exposed trajectory is causally safe just because `finrl`'s specific case was already fixed; this is a systemic check, not a one-adapter fix |
| Regime-label leakage | A regime classifier fit on the full historical span (including data after a given decision's `as_of`) would leak future information into that decision's regime label | Regime labels must be computed causally — see `DATA_SPLIT_PROTOCOL.md` §6; this is the same causality rule already flagged in `EXPERIMENT_PROTOCOL.md` L1.4 |
| Fitting on test data | Any calibration weight, contradiction-ontology threshold, router parameter, or meta-model parameter fit using final-test data | **Absolute rule, reiterated project-wide (corrected — Session 3 protocol consistency audit, Task B1)**: fitting never happens on test. Calibration weights and contradiction-ontology thresholds fit on the **Calibration interval**; router/meta-model/fusion parameters fit on the **Validation interval** — these are two different intervals, not both "validation" (a prior version of this row said "on validation only," which was imprecise/wrong; see `DATA_SPLIT_PROTOCOL.md` §1/§1.1 for the corrected, single source of truth). The final test set is touched exactly once, for a single evaluation pass, per adapter/method (see §5 below and `DATA_SPLIT_PROTOCOL.md` §5) |

## 3. Survivorship bias

- **Adapter survivorship**: only adapters that currently PASS live/offline
  tests (per `ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md`)
  are eligible for TIER-1 — this is a form of survivorship by construction
  (adapters that were tried and abandoned, e.g. real NoFx, are excluded).
  Mitigation: report the full attempted roster (26 integrated + Alpha-GFN
  deferred + real NoFx blocked) alongside the TIER-1 evaluated subset, so a
  reader can see what was excluded and why, not just the survivors.
- **Asset/universe survivorship**: if the shared universe (Controlled
  Scientific Track) is built from currently-listed tickers, delisted/
  failed companies are silently absent from the historical window,
  inflating realized performance. Mitigation: `DATA_SPLIT_PROTOCOL.md` §7
  must specify how the universe is frozen (point-in-time index membership
  where obtainable, or an explicit, disclosed survivorship caveat where
  not).
- **Adapter-internal survivorship**: several adapters already documented as
  applying their own internal filtering (e.g. EarnMore's masked
  sub-universe, TradeMaster's DJ30-only scope) — these are native scope
  choices, not this protocol's survivorship bias, but must be disclosed
  per-adapter in `ADAPTER_REGISTRY_REQUIREMENTS.md` so a reader does not
  mistake a native scope restriction for this protocol's methodology.

## 4. Point-in-time failure

- **Confirmed, not hypothetical**: FinBERT's live data source (yfinance)
  "exposes only current headlines, not historical as-of data"
  (`NEW_ADAPTER_INTEGRATION.md`) — a real PIT failure mode already found in
  this project's own adapter roster, not a generic textbook risk.
  Mitigation: FinBERT is TIER-2 (current-context/diagnostic only, not
  eligible for the historical main experiment) per
  `ADAPTER_REGISTRY_REQUIREMENTS.md`'s eligibility gate.
- **LLM current-knowledge vs. historical as-of mismatch**: any LLM-backed
  adapter's underlying model has a training-data cutoff that may postdate
  or otherwise not track a historical `as_of` used in the experiment — the
  model may "know" things that would not have been knowable at the
  simulated decision time. Mitigation: `DATA_SPLIT_PROTOCOL.md` §8 must
  document each LLM adapter's underlying model's known training cutoff, and
  the historical validation/test windows should be chosen to minimize (not
  eliminate — this is a known, disclosed limitation of LLM-backed adapters
  project-wide, not something this protocol can fully solve) overlap risk.
- **Unavailable historical API outputs**: several adapters depend on live
  third-party APIs with no historical replay mode (real, already-documented
  cases: PGPortfolio's original Poloniex source is permanently dead — HTTP
  410 — worked around via yfinance substitution; yfinance itself has been
  observed transiently rate-limited). Mitigation: TIER classification in
  `ADAPTER_REGISTRY_REQUIREMENTS.md` must record each adapter's live data
  dependency and whether it has been verified to support the specific
  historical window this protocol needs, not just "worked once."

## 5. Test-set tuning and best-seed selection (hard rule)

**The pre-registered contradiction ontology (`EXPERIMENT_PROTOCOL.md` §2.2)
and the practical-significance threshold (§2.4) must be frozen during the
pilot/validation stage and never adjusted after seeing final-test
results.** This is a hard rule, not a suggestion: if a result on the final
test set is disappointing, the correct response is to report it honestly
under the pre-registered Fallback Claims (§2.6), not to redefine the
ontology, re-tune a threshold, or re-run with a different K/seed count
until a better number appears. Best-seed selection (running K stochastic
repeats and reporting only the best) is explicitly prohibited for any
claim-bearing number — K-repeat variance (L1.2) is itself a *reported
diagnostic*, not a selection mechanism to cherry-pick a favorable run. Any
seed/repeat aggregation for a claim-bearing metric must use a
pre-registered aggregation rule (e.g. median across K, or mean ± CI),
fixed before the final test run, never "best of K."

## 6. Incompatible horizons and universes

- **Confirmed, not hypothetical**: TradeMaster is scoped to DJ30 tickers
  only, while other adapters have different native universes
  (`NEW_ADAPTER_INTEGRATION.md`) — a real cross-adapter incompatibility, not
  a hypothetical one. Mitigation: the Controlled Scientific Track's shared
  universe mapping (`DATA_SPLIT_PROTOCOL.md` §4) must define an explicit
  ticker-level intersection or mapping rule; any adapter/comparison that
  cannot be honestly mapped onto the shared universe is excluded from the
  controlled comparison (reported only on the Native Capability Track, per
  `EXPERIMENT_PROTOCOL.md` §2.6's fallback table) rather than force-fit.
- **Horizon mismatch**: not every adapter natively supports every
  pre-registered horizon (1d/5d/20d); a horizon a given adapter does not
  natively support must be marked `ineligible` in the results manifest
  (§1's Category-C mitigation), not silently interpolated or imputed.

## 7. Adapter failures and missing outputs

- **Real precedent**: a genuine `IndexError` (calendar-boundary bug) was
  found and fixed in unmodified upstream Qlib code during capability
  recovery, in an adapter that had otherwise fully PASSED
  (`ADAPTER_CAPABILITY_RECOVERY.md`) — evidence that upstream bugs surface
  even in adapters already marked PASSED, and can resurface under a
  different date range or universe than the one already tested. Mitigation:
  every TIER-1 adapter must be smoke-tested against the *specific*
  validation/test date range and universe this protocol actually uses, not
  assumed safe because it passed under a different prior configuration.
- **Real precedent**: FinMem is live-BLOCKED on a missing OpenAI-compatible
  embeddings credential; PGPortfolio is live-BLOCKED on a dead upstream API
  plus a transient rate limit (`NEW_ADAPTER_INTEGRATION.md`). Mitigation:
  both are TIER-2/TIER-3 per `ADAPTER_REGISTRY_REQUIREMENTS.md` — not
  eligible for the historical main experiment until/unless their blocking
  condition is independently resolved (out of this protocol's scope to
  resolve; a Session-3/engineering task).
- **Missing-output policy**: when an eligible TIER-1 adapter fails or times
  out on a specific decision point during the actual experiment run (not
  pre-known-blocked, but a fresh runtime failure), the Controlled Scientific
  Track's shared missing-output-handling rule (`DATA_SPLIT_PROTOCOL.md`
  §4) applies uniformly — do not silently drop the point from one method's
  evaluation while keeping it in another's, which would bias any
  head-to-head comparison.

## 8. LLM nondeterminism and API cost

- Real, already-observed costs: `tradingagents` makes ~9-10 real LLM calls
  per single run (its own debate architecture); real metered DeepSeek calls
  were also made for `rdagent`, `prediction_arena`, and (indirectly, via
  model training) `deepalpha` (`ADAPTER_CAPABILITY_RECOVERY.md`). K-repeat
  stability testing (L1.2) multiplies this cost by K for every
  stochastic/LLM adapter.
- **Mitigation, compute-budget gate**: aggregate `RunMetadata.cost_usd`/
  `latency_sec` (already schema-native, already populated by every
  adapter) before scaling any K-repeat or multi-baseline experiment beyond
  the pilot stage; a hard per-stage cost ceiling and a stop/go gate belong
  in `EXPERIMENT_DEPENDENCY_MAP.md`, informed by these real historical
  per-adapter costs, not an assumed/generic budget.
- Nondeterminism itself is not purely a risk — it is L1.2's own object of
  study (stability diagnostic) — but it becomes a risk if a claim-bearing
  number for a *different* group (e.g. L2.1's fusion accuracy) is computed
  from a single, unrepeated LLM-adapter call without acknowledging the
  variance L1.2 itself will have already quantified.

## 9. Multiple testing, insignificant and negative results

- **Multiple testing**: already addressed as a hard gate in §1 Category D
  and `EXPERIMENT_PROTOCOL.md` §2.4 (BH-FDR across the full pre-registered
  stratum family). Restated here: an individually-significant, uncorrected
  stratum-level p-value must never be reported as if it were the corrected
  result.
- **Insignificant/negative results**: every experiment group in
  `EXPERIMENT_PROTOCOL.md` §5–§6 has an explicit "Failure interpretation"
  field precisely so that a null or negative result has a pre-written,
  honest home in the eventual write-up rather than being either suppressed
  or forced into a post-hoc positive spin. The Fallback Claims table
  (§2.6) is the single source of truth for what an acceptable "the paper
  still stands" conclusion looks like under each specific negative-result
  scenario — no other fallback framing may be invented after seeing
  results.

## 10. Fusion/routing underperformance (specific, load-bearing case)

L2.1 (fusion) and L2.2 (routing) underperforming their respective
non-negotiable baselines (TrustTrade/ContestTrade-style for fusion,
FineFT-style for routing) is Session 1's own explicitly-predicted most
likely failure mode ("danger zone" for fusion; "least-implemented,
highest-risk" for routing). **This must not be allowed to trigger inventing
a new post-hoc claim.** The only acceptable responses to underperformance
are the pre-registered rows of `EXPERIMENT_PROTOCOL.md` §2.6's Fallback
Claims table — most importantly: **H1, if it holds, is a complete,
independent contribution regardless of L2.1/L2.2's outcome**, and downside-
risk reduction alone (H3, via L2.4) is an explicitly legitimate fallback
framing, not a downgrade to be hidden or reframed as something it isn't.

## 11. Unfair baselines (specific, load-bearing case)

The TrustTrade-style, ContestTrade-style, and FineFT-style baselines
required by `EXPERIMENT_PROTOCOL.md` §6 (L2.1, L2.2) are the single
highest-leverage way this protocol could accidentally (or through resource
pressure) produce a misleading positive result: an under-implemented,
under-tuned competitor baseline would make the proposed method look better
than it is, and Session 1's own novelty audit is explicit that these
baselines are non-negotiable precisely because they are the closest prior
art. **Mitigation, hard rule**: each competitor-style baseline must be
implemented with comparable engineering effort and a comparable
hyperparameter-tuning budget (fit on the same validation window, using a
tuning budget of the same order of magnitude — number of configurations
tried, compute spent) as the proposed L2.1/L2.2 method itself. A baseline
implemented as a quick strawman (e.g. untuned defaults, a single
hyperparameter setting) must be explicitly flagged as such in any results
write-up and must not be used to support a novelty claim — if a
resource-constrained, honestly-labeled "weak-effort baseline" is all that
is achievable within budget, the paper must say so rather than imply a
fair fight occurred.

## 12. Scope-language discipline (project-wide restatement)

Reiterating §1 Category E as a project-wide rule that applies to every
deliverable, not just H1: **"26 adapters" and "the adapters actually used
in the claim-bearing (Controlled Scientific Track) experiment" are not
interchangeable phrases.** Every results write-up, abstract sentence, and
table caption must use the evaluated count, sourced from
`ADAPTER_REGISTRY_REQUIREMENTS.md`'s TIER-1 list at the time of the final
test run — this is the single most likely place for scope-language drift to
occur silently between this protocol's design and an eventual paper draft.
