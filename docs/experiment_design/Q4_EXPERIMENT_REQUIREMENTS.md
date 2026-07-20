# Q4 Experiment Requirements — Handoff to Session 4

**This is a read-only requirements list, not a design or implementation.**
Session 2 does not modify Session 4's Q4 rolling execution protocol, does
not touch `harness/q4_protocol.py`, `harness/execution_engine.py`, or any
other file in Session 4's scope. This document exists so Session 4's
causal rolling protocol can be built to satisfy exactly what
`EXPERIMENT_PROTOCOL.md`'s L1.5/L2.2/L2.3/L2.5 groups need.

---

## 1. Why this handoff exists

`CONTRACT/schemas.py`'s `Q4Policy.generation_window` docstring is explicit
and load-bearing for this handoff: *"Harness-supplied strategy generation
interval. The adapter records this interval but must not choose, expand,
shorten, or otherwise alter it. Validation/test windows are not part of
this contract — they belong to the harness/experiment execution layer, not
to the adapter's policy output."* Session 2's `DATA_SPLIT_PROTOCOL.md`
defines exactly what those validation/test windows must be
(train/calibration/validation/untouched-final-test, with an embargo gap
≥ the longest horizon tested). This document translates that into concrete
execution-semantics requirements for Session 4's rolling protocol —
**Session 2 does not build the rolling protocol itself**, since that is
explicitly reserved to Session 4 and out of this session's file scope.

## 2. Required execution semantics

| Requirement | Why `EXPERIMENT_PROTOCOL.md` needs it | Grounding |
|---|---|---|
| **Initialization** must accept an explicit `generation_window` (start/end) supplied by the calling experiment code, and the adapter must never expand it | Directly required by `CONTRACT/schemas.py`'s own docstring — Session 4's rolling protocol is the concrete "harness/experiment execution layer" that docstring defers to | `Q4Policy.generation_window: TimeWindow` field |
| **Training/generation window** must be distinct from, and never overlap into, the calibration/validation/test windows defined in `DATA_SPLIT_PROTOCOL.md` §1, respecting the §3 embargo gap (≥ 20 trading days, the longest candidate horizon) | Without this, any Q4 adapter's rolling refit could leak future information into a decision it is later asked to make during validation/test | `DATA_SPLIT_PROTOCOL.md` §1/§3 |
| **Sequential step execution**: for `ROLLING_OPTIMIZER`/`ONLINE_ADAPTIVE_POLICY` policies, the rolling protocol must call the adapter once per legal rebalance point during sequential execution and accumulate one `PolicyDecisionStep` per call — not ask the adapter to predict/fill in a future trajectory upfront | `Q4Policy`'s own docstring: *"`decisions` is optional and does not need to be populated upfront for a rolling or online policy: on each legal rebalance point during sequential execution the harness calls the adapter again and accumulates one `PolicyDecisionStep` per call."* This is already the contract's stated design; Session 4's protocol is the concrete implementation of "the harness" referenced there. |
| **Observation cutoff enforcement**: every step's `information_cutoff` must be `<= timestamp`, and the rolling protocol must supply the adapter with data truncated at that cutoff — not the full historical series with a "please don't look ahead" instruction | Schema already validates `information_cutoff <= timestamp` at the object level, but cannot verify the adapter was *actually* given truncated data — that enforcement must happen at the data-feed layer, which is Session 4's responsibility, not the schema's | `PolicyDecisionStep`'s causality field pair; already verified with 0 violations across 344 real decisions in the *existing* (non-rolling, single-shot) test harness per `ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md` — Session 4's rolling protocol must preserve this invariant under true sequential, multi-step execution, which is a materially harder guarantee than the single-shot case already verified |
| **Rebalance delay / execution delay** must be configurable and match `DATA_SPLIT_PROTOCOL.md` §4's shared "execution delay" field across every adapter compared on the Controlled Scientific Track | A per-adapter-inconsistent execution-delay assumption would silently make one Q4 policy's returns not comparable to another's | `DATA_SPLIT_PROTOCOL.md` §4 |
| **Transaction costs** applied at the evaluation layer, using the shared cost model from `DATA_SPLIT_PROTOCOL.md` §4 — not each adapter's own (if any) internal cost assumption, and not omitted | `PolicyDecisionStep` carries no return/cost field by design ("Carries no return/NAV/Sharpe/drawdown/benchmark information — those belong to the evaluation layer," per its own docstring) — Session 4's rolling protocol is the natural place this evaluation-layer cost application happens, immediately after producing each step | `PolicyDecisionStep`'s docstring; `METRIC_DESIGN.md`'s transaction-cost-adjusted return metric |
| **State persistence** across sequential calls for `ONLINE_ADAPTIVE_POLICY`/`UpdateMode.ONLINE_LEARNING`/`STATE_UPDATE` adapters — the rolling protocol must maintain and pass forward whatever state object a stateful adapter needs between steps, and must not silently reset it | Without this, a genuinely online-adaptive adapter (per its own declared `UpdatePolicy.mode`) would be forced to behave as if `UpdateMode.NONE`, misrepresenting its real capability | `UpdatePolicy`/`UpdateMode` enum in `CONTRACT/schemas.py` |
| **Online updates** (`ROLLING_REFIT`/`ONLINE_LEARNING`) must themselves respect the same information-cutoff discipline as decisions — a refit at step `t` may only use data with timestamp `<= information_cutoff(t)` | Same causality principle as above, applied to the *update* step, not just the *decision* step — a common, easy-to-miss leakage channel (refitting "quietly" on slightly-too-recent data between decision calls) | Extension of `PolicyDecisionStep`'s causality invariant; `RISK_AND_FAILURE_PLAN.md` §leakage |
| **Dynamic universe** support (assets entering/leaving the tradable set mid-rollout) must be handled without silently dropping or fabricating weights for delisted/newly-listed assets | `DATA_SPLIT_PROTOCOL.md` §4's universe-mapping table and `RISK_AND_FAILURE_PLAN.md`'s survivorship-bias section both depend on this being handled explicitly, not assumed away by using only currently-listed tickers throughout a historical window | `UniversePolicy.mode` already supports `"dynamic"` in schema; needs a concrete rolling-execution semantics from Session 4 |
| **Failed-decision handling**: if an adapter call fails or times out at one rebalance point mid-rollout, the protocol must apply `DATA_SPLIT_PROTOCOL.md` §4's shared missing-output policy (hold prior position) and log the failure as a first-class event, not silently skip the step or halt the entire trajectory | `RISK_AND_FAILURE_PLAN.md`'s "adapter failures" risk category requires this to be handled uniformly across adapters, not per-adapter ad hoc | `DATA_SPLIT_PROTOCOL.md` §4 |
| **Common evaluator**: the same evaluation code (performance + risk metrics, per `METRIC_DESIGN.md`) must consume every adapter's accumulated `decisions` trajectory identically — the rolling protocol's *output* format (a sequence of `PolicyDecisionStep`s under one `Q4Policy`) is already schema-uniform; Session 4 should not introduce an adapter-specific evaluation path that bypasses this uniformity | `L1.5`'s entire purpose (`EXPERIMENT_PROTOCOL.md` §5) is a common evaluation engine feeding every downstream L2 group — a non-uniform evaluator would silently break every claim's fairness |

## 3. Known precedent to build on, not relitigate

The existing (non-rolling, single-shot per-adapter) test harness already
demonstrated **0 causality violations across 344 real decisions** spanning
7 Q4-causal adapters (`ADAPTER_CAPABILITY_RECOVERY.md`,
`NEW_ADAPTER_INTEGRATION.md`) — this is real, already-verified evidence
that the causality discipline is achievable at the single-shot level.
Session 4's job, as this session understands it, is extending that same
discipline to **true sequential, multi-step, potentially-stateful rolling
execution** — a materially harder guarantee (state carried across calls,
online refits, dynamic universes) than what has been verified so far. This
handoff should not be read as claiming the rolling case is already solved.

`finrl_adapter.py`'s deliberate, already-correct refusal to expose its
full in-sample trajectory (`decisions=None` by design, because the policy
was trained on the same window it would be asked to decide over) is the
project's own existing precedent for exactly the kind of causality
violation Session 4's rolling protocol must prevent from recurring at
scale once trajectories are generated by true sequential execution rather
than static single-shot calls.

## 4. What this session does NOT decide

- The rolling protocol's implementation, code structure, or file layout —
  entirely Session 4's responsibility.
- Which specific adapters Session 4's protocol supports first — that is an
  engineering sequencing decision for Session 4, informed by but not
  dictated by `DATA_SPLIT_PROTOCOL.md` §5's eligibility tiers.
- Any change to `CONTRACT/schemas.py`, `harness/q4_protocol.py`,
  `harness/execution_engine.py`, or any other file outside
  `docs/experiment_design/`.
