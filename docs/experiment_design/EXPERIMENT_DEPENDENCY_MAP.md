# Experiment Dependency Map

All experiment-group IDs (L1.x/L2.x/X.x) and hypothesis IDs (H1–H7) are
defined in `EXPERIMENT_PROTOCOL.md` §2–§7; this file sequences them and
does not redefine them.

## 1. Dependency chain

```
Field mapping and data validity (L1.1)
        |
        v
Layer 1 basic diagnostics  ---------------------------------------------
        |                                                              |
        +--> L1.2 Calibration & Stability                              |
        +--> L1.3 Structural Contradiction & Cross-Q Coherence (H1) <--+ (needs L1.2's
        +--> L1.4 Regime-Conditioned Reliability (needs L1.2, L1.3)      confidence-kind
        +--> L1.5 Q4 Performance & Risk Audit (independent of L1.2-4)    labels)
                 |
                 v
        [[ HUMAN CHECKPOINT 1 — see §3 ]]  (H1 result reviewed before any L2 spend)
                 |
                 v
Layer 1 feature freeze  (L1.1-L1.5 outputs frozen; no further tuning against
                          validation once L2 experiments begin, per
                          DATA_SPLIT_PROTOCOL.md §1's interval-fitting rule)
                 |
                 v
Layer 2 simple baselines  (naive aggregation baselines inside L2.1;
                            fixed-system/equal-weight baselines inside L2.2;
                            no-intervention baseline inside L2.4)
                 |
                 v
Layer 2 primary methods — PARALLEL after Layer 1 freeze:
        +--> L2.1 Fusion (needs L1.1, L1.2, L1.3, L1.5)
        +--> L2.2 Routing (needs L1.4, L1.5)                    [also depends on
        +--> L2.3 Shadow Q4 (needs L1.5)                         Q4_EXPERIMENT_
        +--> L2.4 Intervention/Abstention (needs L1.2, L1.3;     REQUIREMENTS.md
        |         shares L2.1's signal — run after L2.1 starts)  being satisfied]
        +--> L2.5 Validation-Conditioned Selection (needs L1.5;
        |         also required AS a baseline inside L2.2 — see note below)
                 |
                 v
        [[ HUMAN CHECKPOINT 2 — see §3 ]]  (L2.1/L2.2 primary results reviewed)
                 |
                 v
L2.6 Lightweight Multi-View Meta-Fusion  (strictly after L2.1 exists —
                                           L2.1 is its required baseline)
                 |
                 v
Cross-cutting ablation and robustness (X.1, X.2, X.3, X.4)
                 |
                 v
        [[ HUMAN CHECKPOINT 3 — see §3 ]]  (explicit approval to touch final test)
                 |
                 v
Frozen final test  (single evaluation pass, no re-tuning afterward —
                    DATA_SPLIT_PROTOCOL.md §1's "Untouched final test" row)
```

**Note on L2.5**: it is listed both as its own optional group and as a
required baseline *inside* L2.2's baseline ladder (`EXPERIMENT_PROTOCOL.md`
§6, L2.2's Baseline list includes "recent-performance router," which is
L2.5's mechanism). Concretely this means L2.5's machinery must exist
*before* L2.2 can be considered complete, even though L2.5's own
standalone write-up is NICE-TO-HAVE.

## 2. What can run in parallel

- **L1.2, L1.4's regime-labeling machinery, and L1.5 can start
  simultaneously once L1.1 completes** — L1.4 formally depends on L1.2/L1.3
  for its *reliability metrics*, but the regime-label construction itself
  (`DATA_SPLIT_PROTOCOL.md` §6) has no dependency on L1.2/L1.3 and can be
  built in parallel, then applied once L1.2/L1.3 land.
- **L1.3 needs L1.2's confidence-kind labels validated first** (its nested
  model's covariate must be trustworthy) — not fully parallel with L1.2,
  but can begin ontology-application (§2.2 of `EXPERIMENT_PROTOCOL.md`) on
  a pilot slice while L1.2 finishes.
- **L2.1, L2.2, L2.3 are mutually parallel** once the Layer 1 feature
  freeze happens — they consume disjoint-enough inputs (L2.1 needs L1.2/
  L1.3, L2.2 needs L1.4, L2.3 needs only L1.5) that a compute-budget-
  permitting team could run all three concurrently.
- **L2.4 should start only after L2.1 has a working signal computation**,
  since it reuses L2.1's diagnostic pipeline (not a hard blocking
  dependency, but a practical one to avoid duplicated engineering).
- **X.1/X.2/X.3/X.4 are mutually parallel** and can each start as soon as
  their specific consuming experiment (L1.1 for X.1; L2.1+L2.2 for X.2;
  L1.5/L2.1-3 for X.3; L1.3/L2.1/L2.4 for X.4) has a first-pass result —
  they do not need to wait for every other cross-cutting item.

## 3. Human-approval checkpoints (non-optional, per the task brief)

**Checkpoint 1 — after L1.3 (H1) first-pass result, before any Layer 2
spend.** `EXPERIMENT_PROTOCOL.md` §5's L1.3 entry is explicit that a null
H1 result must escalate to a human checkpoint before continuing to L2.1–
L2.6 — this is carried forward here as a hard gate, not softened. At this
checkpoint a human reviews: (a) H1's nested-model test result and
robustness checks, (b) whether to proceed to full Layer 2 experimentation,
proceed to Layer 2 as a pure decision-layer question independent of H1
(Fallback (a)), or pause the project pending a redesign of the contradiction
ontology.

**Checkpoint 2 — after L2.1/L2.2's primary results, before L2.6 and before
finalizing which claims are "main paper" vs. "appendix."**
`EXPERIMENT_PROTOCOL.md` §6's L2.6 entry explicitly defers the "does L2.6
replace L2.1 as the main fusion result" decision to a human, and §3 of
`ICAIF_POSITIONING_REPORT.md` (Session 1) already flagged that whether to
run Candidate 1 (fusion) and Candidate 4 (routing) as one combined paper or
two separate submissions is a genuine open decision this protocol does not
resolve unilaterally — this checkpoint is where that decision gets made,
informed by real L2.1/L2.2 results rather than argued in the abstract.

**Checkpoint 3 — before touching the final (untouched) test set at all.**
No experiment in this protocol may access final test data until every
Layer 1 group, every MUST-RUN Layer 2 group, and the cross-cutting ablation
plan have completed on validation and been reviewed by a human. This is the
single hardest gate in the whole protocol — see `DATA_SPLIT_PROTOCOL.md`
§8 for the exact access-control statement.

## 4. Kill criteria and stopping rules

| Condition | Action |
|---|---|
| H1 fails robustly (H0 not rejected after FDR correction in **any** stratum, or effect is not leave-one-out-robust) at Checkpoint 1 | **Do not silently proceed.** Per Fallback (a)'s own logic, if H1 also fails there is no fallback narrative left for the diagnostic substrate — escalate to a human decision on whether to (i) revise the contradiction ontology (§2.2) and re-run on a *fresh* validation slice (never on data already used to test the failed ontology, to avoid ontology p-hacking), or (ii) stop the diagnostic-substrate line of the paper entirely and pivot to a narrower engineering/benchmark-artifact contribution (Session 1's Alt C fallback, `ICAIF_POSITIONING_REPORT.md` §3) |
| L2.2 does not clear the FineFT-style baseline after the full baseline ladder | Per `EXPERIMENT_PROTOCOL.md` §6's L2.2 failure interpretation: stop investing further compute in the *routing* sub-claim specifically; L2.3 (shadow policy) is not automatically invalidated and may continue independently |
| L2.1 does not beat the TrustTrade-/ContestTrade-style baselines | Do not iterate on L2.1's weighting formula against the **validation** set indefinitely trying to beat these baselines — more than 2 tuning rounds against the same validation slice risks p-hacking (see `RISK_AND_FAILURE_PLAN.md`); after 2 rounds, report the honest result and move to Checkpoint 2 |
| Compute/cost budget gate exceeded (§5 below) before a MUST-RUN group completes | Escalate to a human budget decision — do not silently downgrade the group's sample size/K-repeat count without recording the change and its effect on statistical power |
| A TIER-1 adapter that a MUST-RUN group depends on becomes newly BLOCKED (credential expiry, upstream API change) mid-experiment | Re-run the eligibility check (`ADAPTER_REGISTRY_REQUIREMENTS.md`); if the group's minimum-diversity requirement (≥2 paradigms per H1's cross-adapter classes) can no longer be met, escalate rather than silently narrowing scope |

## 5. Compute budget gates

Tied to `RunMetadata.cost_usd`/`latency_sec` — schema-native fields already
populated by every adapter, not new instrumentation.

- **Real historical cost anchor**: `ADAPTER_CAPABILITY_RECOVERY.md`
  documents `tradingagents` making ~9–10 real LLM calls per single run
  (multi-agent debate architecture), and `finrl_adapter.py`'s smoke test
  alone exceeding a 250-second timeout budget once (real DRL training +
  yfinance fetch). These are not hypothetical costs — they are observed.
- **L1.2's K-repeat stability testing is the single largest cost
  multiplier in this protocol**: K repeated calls × every stochastic/LLM
  TIER-1 adapter × every sampled `(ticker, as_of, horizon)` tuple. Before
  running L1.2 at full validation-set scale, a **pilot-stage cost estimate
  must be computed and reviewed** (pilot K on a small tuple sample,
  extrapolated to the full validation set) — this is a hard gate, not a
  suggestion, given the real per-run LLM costs already observed.
- **L2.2's full baseline ladder** (7 baselines × rolling execution over a
  real validation window) is the second largest cost driver — budget this
  explicitly before Checkpoint 2, using L1.5's already-observed per-adapter
  rolling-execution latency as the per-baseline cost anchor.
- **Gate rule**: no MUST-RUN group may proceed past its pilot slice (§6)
  without an explicit, recorded cost estimate reviewed against available
  budget. This is separate from, and in addition to, the three human
  checkpoints in §3.

## 6. Stage structure — entry/exit criteria

| Stage | Entry criteria | Exit criteria |
|---|---|---|
| **Pilot** | L1.1 complete; TIER-1 adapter roster finalized (`ADAPTER_REGISTRY_REQUIREMENTS.md`) | A small (single-digit-ticker, short-window) slice of every MUST-RUN Layer 1 group runs end-to-end without a schema/causality violation; K (L1.2), the practical-significance threshold (§2.4 of `EXPERIMENT_PROTOCOL.md`), and per-group cost estimates are all fixed and recorded **before** the screening stage begins — none of these may be adjusted after seeing screening-stage results |
| **Screening** | Pilot exit criteria met | Every Layer 1 group (L1.1–L1.5) completes on the full validation-window decision set; Checkpoint 1 passed |
| **Full validation** | Screening exit criteria met; Layer 1 feature freeze declared | Every MUST-RUN Layer 2 group (L2.1–L2.4) and the required NICE-TO-HAVE baseline machinery (L2.5) complete on validation; cross-cutting ablations (X.1–X.4) complete on validation; Checkpoint 2 passed |
| **Final test** | Full validation exit criteria met; Checkpoint 3 explicitly granted by a human | A single, one-shot evaluation of the frozen (post-freeze) fusion/routing/intervention configurations on the untouched final test set — **no further tuning after this point, regardless of result** (`DATA_SPLIT_PROTOCOL.md` §1's causality/no-peeking rule; corrected here — a prior version cited a nonexistent "§9" of this file) |

## 7. What this map deliberately does not decide

Whether Session 1's Candidate 1 (fusion) and Candidate 4 (routing) end up
as one combined paper or two separate submissions is explicitly left to
Checkpoint 2, informed by real results — this map sequences the
*experiments*, not the eventual paper-structure decision, which remains
open per `ICAIF_POSITIONING_REPORT.md` §3.
