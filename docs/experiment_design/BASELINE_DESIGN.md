# Baseline Design

Baselines for every Layer 2 experiment group defined in
`EXPERIMENT_PROTOCOL.md` (§6, groups L2.1–L2.6). All baselines run on the
**Controlled Scientific Track** (`EXPERIMENT_PROTOCOL.md` §4) — the same
`as_of`/`data_cutoff` sequence, universe mapping, calendar, transaction-cost
model, benchmark, execution-delay assumption, risk-free rate, rebalancing/
missing-output/failure-handling/cash-treatment policy, exposure audit, and
result-aggregation method as the proposed methods. A baseline evaluated
under looser conditions than the proposed method is not a fair baseline —
this is enforced by construction, not by a note.

Every baseline entry below reports: **Deployable** (could this run live,
unmodified, tomorrow?), **Uses validation** (does it require a validation-
window fit?), **Uses future information** (a leakage flag — any "Yes" here
is disqualifying for anything but an explicitly-labeled upper bound),
**Complexity**, **Parameter count**, **Compute cost**, and a **Fairness
note** relative to the proposed method it competes against.

---

## 1. Prediction / Action baselines (compete against L2.1 fusion)

| Baseline | Deployable | Uses validation | Uses future info | Complexity | Params | Cost | Fairness note |
|---|---|---|---|---|---|---|---|
| Random | Yes | No | No | Trivial | 0 | Free | Floor sanity check only |
| Always HOLD | Yes | No | No | Trivial | 0 | Free | Floor sanity check; also the honest baseline for adapters whose only observed action across a window is HOLD |
| Single adapter (each TIER-1 adapter alone) | Yes | No | No | Trivial | 0 | Adapter's own real per-call cost | Establishes what L2.1 must beat *individually*, not just in aggregate |
| Best single adapter, selected on validation | Yes | Yes | No | Low | 1 selection | Adapter's own cost + selection overhead | Selection itself must not touch final test — see `DATA_SPLIT_PROTOCOL.md` §5 |
| Majority vote | Yes | No | No | Low | 0 | Sum of adapter costs | — |
| Equal-weight vote | Yes | No | No | Low | 0 | Sum of adapter costs | — |
| Raw self-reported-confidence weighting | Yes | No | No | Low | 0 (weights = raw confidence) | Sum of adapter costs | The naive baseline L2.1 is explicitly designed to improve on (Session 1 Candidate 1's central contrast) |
| Calibrated-confidence weighting | Yes | Yes | No | Low-Medium | ~1 per `ConfidenceKind` bucket | Sum of adapter costs + calibration fit | Uses L1.2's calibration curves but *not* L1.3's contradiction penalty — isolates the calibration-only contribution from the contradiction contribution inside L2.1 |
| Regime-blind weighting | Yes | Yes | No | Low | ~1 per adapter | Sum of adapter costs | Same weighting scheme as calibrated-confidence but without L1.4's regime stratification — isolates the regime-conditioning contribution |
| Simple linear/logistic model on raw Q1/Q3 outputs | Yes | Yes | No | Low | O(#adapters) | Sum of adapter costs + fit | A generic ML baseline, distinct from any reliability-aware weighting — tests whether *any* learned combination beats the reliability-specific design |
| **TrustTrade-style cross-agent agreement weighting** (arXiv 2603.22567) | Yes (reimplementable from the published mechanism: cross-agent semantic+numerical agreement discounts divergent signals) | Yes (same fit discipline as L2.1) | No | Medium | comparable to L2.1's own weight count | Sum of adapter costs + agreement computation | **Non-negotiable per Session 1's novelty audit** — omitting this baseline is the single most-cited risk in `NOVELTY_AUDIT.md`/`CLAIM_CANDIDATES.md` Candidate 1. Fairness: implemented against the *same* 26-adapter/6+-paradigm pool as L2.1, not against a smaller LLM-only subset, so the comparison isolates the calibration-vs-agreement mechanism delta, not a scope difference |
| **ContestTrade-style outcome-utility weighting** (arXiv 2508.00554) | Yes (reimplementable: score by delayed market outcomes, allocate toward positive-predicted-utility sources) | Yes | No | Medium | comparable to L2.1's own weight count | Sum of adapter costs + utility-scoring computation | **Non-negotiable per Session 1's novelty audit** — the closest competitor on the *outcome-weighting* axis specifically, per `NOVELTY_AUDIT.md`. Same fairness note as TrustTrade above |

**Correct lone dissenter case-study** (not a baseline table row, but a
required companion analysis for L2.1 per `EXPERIMENT_PROTOCOL.md` §6): a
deliberately-constructed or mined slice of the validation/test set where
one adapter is directionally correct while the majority is wrong, used to
show concretely (not just in aggregate metrics) that calibration-weighting
does not structurally penalize the correct dissenter the way agreement-
weighting does by construction. This slice must be identified using
validation-window data only, before the final test evaluation.

---

## 2. Portfolio baselines (compete against L1.5's audit and every Q4-facing L2 group)

| Baseline | Deployable | Uses validation | Uses future info | Complexity | Params | Cost | Fairness note |
|---|---|---|---|---|---|---|---|
| CASH (100% cash, 0% return before rates) | Yes | No | No | Trivial | 0 | Free | Absolute floor |
| Equal-weight buy-and-hold | Yes | No | No | Trivial | 0 | Free | Standard passive floor |
| Market benchmark (index matched to the Controlled Scientific Track's universe) | Yes | No | No | Trivial | 0 | Free | Must use the *same* universe mapping as the proposed methods, not a generic broad-market index, or the comparison is not apples-to-apples |
| Inverse volatility | Yes | No | No | Low | 0 | Free (uses only historical vol) | — |
| Minimum variance | Yes | No | No | Low-Medium | O(N²) covariance | Free | — |
| Risk parity | Yes | No | No | Medium | O(N²) covariance + iterative solve | Free | — |
| One representative native Q4 policy (fixed, e.g. the highest-live-readiness TIER-1 Q4 adapter) | Yes | No | No | Depends on adapter | Adapter's own | Adapter's own real cost | Chosen for live-readiness, not for favorable historical performance — selection criterion fixed before any performance is observed |
| Best Q4 policy selected on validation | Yes | Yes | No | Low (selection only) | 1 selection | Sum of all Q4 adapters' costs during selection | Same validation-only discipline as "best single adapter" above; this **is** L2.5 (Validation-Conditioned Policy Selection), promoted from a baseline to its own experiment group per `EXPERIMENT_PROTOCOL.md` §6 |
| Equal mixture of Q4 policies | Yes | No | No | Low | 0 | Sum of all Q4 adapters' costs | — |

---

## 3. Routing baselines (compete against L2.2)

| Baseline | Deployable | Uses validation | Uses future info | Complexity | Params | Cost | Fairness note |
|---|---|---|---|---|---|---|---|
| Random router | Yes | No | No | Trivial | 0 | Sum of routed adapters' costs | Floor |
| Static global-best adapter | Yes | Yes | No | Trivial | 1 selection | Selected adapter's cost | Same as "best single adapter" above |
| Round-robin | Yes | No | No | Trivial | 0 | Sum of routed adapters' costs | — |
| Regime-blind learned router | Yes | Yes | No | Low-Medium | O(#adapters) | Fit + routed adapters' costs | Isolates the value of L1.4's regime conditioning specifically |
| Recent-performance router (rolling Sharpe/return-based) | Yes | Yes (rolling, causal — see `DATA_SPLIT_PROTOCOL.md` §6) | No, provided the rolling window is strictly causal | Low | 0 (rule-based) | Sum of routed adapters' costs | This **is** L2.5 reused as a routing baseline — same machinery, different consumer |
| **FineFT-style within-framework VAE-routing baseline, retrained on this project's own harness data** (arXiv 2512.23773) | Partially — requires retraining a VAE on this project's own market-state features, a real implementation effort, not a reference to the paper | Yes | No | Medium-High | VAE parameter count (project-specific) | Retraining cost (see `RISK_AND_FAILURE_PLAN.md` compute budget) | **Non-negotiable per Session 1's novelty audit** — this is the single named condition for L2.2's "not obviously preempted" verdict to hold empirically rather than just argumentatively. Fairness: trained on the *same* harness data and evaluated under the *same* Controlled Scientific Track as L2.2, not compared to FineFT's own published numbers (which used a different universe/harness and are not comparable) |
| Oracle upper bound (perfect hindsight routing to the best-performing system at each step) | **No — explicitly non-deployable** | N/A | **Yes, by design** | N/A | N/A | N/A | Reported only as an upper bound / ceiling reference, never as a competing "result" — mislabeling this as a deployable baseline is exactly the kind of leakage `RISK_AND_FAILURE_PLAN.md` flags |

---

## 4. Contradiction / intervention baselines (compete against L2.4)

| Baseline | Deployable | Uses validation | Uses future info | Complexity | Params | Cost | Fairness note |
|---|---|---|---|---|---|---|---|
| No intervention (always fuse, L2.1's output as-is) | Yes | No | No | — | — | — | The reference point for measuring intervention's marginal risk reduction |
| Random intervention (abstain at random, matched base rate) | Yes | No | No | Trivial | 1 (base rate) | Free | Rules out "any abstention helps by construction" |
| Fixed cash buffer (constant, regardless of signal) | Yes | No | No | Trivial | 1 | Free | Rules out "any de-risking helps regardless of trigger quality" |
| Binary disagreement count | Yes | Yes (threshold fit) | No | Low | 1 threshold | Low | A generic ensemble-disagreement baseline, **not** structural-contradiction-aware — this is the specific comparison that isolates whether §2.2's ontology adds value over raw disagreement counting |
| Entropy/dispersion rule | Yes | Yes (threshold fit) | No | Low | 1 threshold | Low | Same purpose as binary disagreement, continuous variant — per Session 1 Codex Phase C, this is the exact comparison needed to show "structural contradiction is special," not just "disagreement of any kind" |
| Contradiction-aware rule (§2.2's `C` alone) | Yes | Yes (threshold fit) | No | Low | 1 threshold | Low | — |
| Contradiction + reliability rule (`C` + L1.2 calibration score, L2.4's actual method) | Yes | Yes (threshold fit) | No | Low-Medium | 2 thresholds | Low | — |

---

## 5. Meta-fusion baselines (compete against L2.6)

| Baseline | Deployable | Uses validation | Uses future info | Complexity | Params | Cost | Fairness note |
|---|---|---|---|---|---|---|---|
| Raw majority | Yes | No | No | Trivial | 0 | Sum of adapter costs | Same as §1's majority vote, reused |
| Equal average | Yes | No | No | Trivial | 0 | Sum of adapter costs | — |
| Weighted average (L2.1's own mechanism) | Yes | Yes | No | Low | O(#adapters) | Sum of adapter costs | **This is the baseline L2.6 exists to beat** — per `EXPERIMENT_PROTOCOL.md` §6, L2.6 is only worth reporting in the main paper if it materially beats L2.1, not merely differs from it |
| Linear model | Yes | Yes | No | Low | O(#features) | Fit + adapter costs | — |
| Shallow tree / boosting | Yes | Yes | No | Medium | O(trees × depth) | Fit + adapter costs | Preferred over a deep/opaque model per the task brief's explicit interpretability-first instruction; only escalate complexity if shallow classes demonstrably fail |
| Proposed lightweight meta-layer (L2.6) | Yes | Yes | No | Medium (bounded — see `EXPERIMENT_PROTOCOL.md` §6) | Bounded, to be fixed at pilot stage | Fit + adapter costs | Complexity-adjusted comparison required (`RISK_AND_FAILURE_PLAN.md` overfitting section) — a marginal metric win must exceed what added parameters would predict by chance before being reported as a real gain |

---

## 6. Cross-cutting baseline notes

- **No baseline in this document may be fit or selected on the final test
  set.** Every "uses validation" = Yes baseline is fit strictly on the
  Controlled Scientific Track's validation window; see
  `DATA_SPLIT_PROTOCOL.md` for the exact split boundaries and embargo
  rules.
- **The oracle upper bound (§3) is the only intentionally non-deployable
  baseline in this document.** Every other baseline must be realistically
  runnable under the same operational constraints as the proposed methods
  — if a baseline requires information or compute the proposed method
  does not also have access to, it is not a fair baseline and must be
  flagged, not silently included.
- **Real cost matters.** `RunMetadata.cost_usd`/`latency_sec`
  (`CONTRACT/schemas.py`) already exists on every adapter call; baselines
  that call every TIER-1 adapter (majority vote, equal-weight vote, etc.)
  incur the *sum* of real per-adapter costs already observed in
  `ADAPTER_CAPABILITY_RECOVERY.md` (e.g. `tradingagents`'s ~9-10 real LLM
  calls per run) — this is a real budget line item, not a free
  computation, and must be accounted for in
  `EXPERIMENT_DEPENDENCY_MAP.md`'s compute budget gates.
