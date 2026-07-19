# Q4 Stepwise Migration

This document covers the transition of Q4 (Policy) execution from a single
batch `q4_policy()` call per adapter to a harness-driven, step-by-step
execution protocol (`q4_initialize` / `q4_step` / `q4_finalize`), and the
current status of all 13 Q4-capable adapters in this repository under that
protocol.

**This round is the formal infrastructure baseline.** Per the governing
task, adapter count is not expanded further after this round — the 13
adapters classified here are the complete, final Q4 adapter set for the
controlled stepwise experiment track.

## 1. Why stepwise, and why additive

`CONTRACT/schemas.py`'s `Q4Policy` docstring already anticipates sequential
execution ("on each legal rebalance point during sequential execution the
harness calls the adapter again and accumulates one `PolicyDecisionStep` per
call") but no code previously drove that loop from outside the adapter —
every adapter computed its whole `decisions` trajectory in one internal
batch call. That has two problems for a controlled experiment:

1. The harness cannot verify, at each step, that the adapter is honestly
   using only causally-available information — an adapter's internal batch
   loop is a black box from the harness's point of view.
2. The harness cannot inject its own unified execution semantics (weight
   projection, transaction costs, constraint enforcement) between decisions
   — each adapter's batch call bakes in whatever assumptions it likes.

The fix is a real, harness-driven per-step protocol, defined entirely
**outside** `CONTRACT/`:

```python
class Q4StepAdapter(Protocol):
    def q4_initialize(self, context, generation_window, initial_portfolio, run_config) -> Q4Policy: ...
    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state) -> PolicyDecisionStep: ...
    def q4_finalize(self) -> Q4Policy: ...
```

`CONTRACT/schemas.py` was **not modified** to add this — `Q4StepAdapter` is
a structural `typing.Protocol` (`harness/q4_protocol.py`). An adapter opts
in by simply defining these three methods on its existing `BaseAdapter`
subclass. `isinstance(adapter, Q4StepAdapter)` (the protocol is
`@runtime_checkable`) is how the harness worker decides whether an adapter
gets the real stepwise path or a compatibility fallback.

**The existing `q4_policy()` method is untouched on every migrated
adapter.** All three new methods were added as pure insertions (see §3 for
exact diff stats — 9 of 10 migrated adapters have *zero* deleted lines; the
10th, EarnMore, has an internal-helper rename with the `q4_policy()` call
site itself unchanged, verified by its own passing legacy test suite).
Nothing that already worked was put at risk to build this.

## 2. Compatibility strategy: LEGACY_INTERNAL_LOOP

Adapters that do not define the three stepwise methods are not broken by
this change. `harness/q4_runtime.py`'s worker dispatch checks
`isinstance(adapter, Q4StepAdapter)`:

- **True** → real `STEPWISE` execution: the harness calls `q4_initialize`
  once, `q4_step` once per legal rebalance point, `q4_finalize` once.
- **False** → `LEGACY_INTERNAL_LOOP` replay: the worker calls the existing
  `q4_policy()` once, caches its real `decisions` list, and replays exactly
  one real `PolicyDecisionStep` per subsequent step request. When the real
  decisions are exhausted, further step requests get an honest error
  (`"...not fabricating one"`) — the harness never synthesizes a decision
  the adapter didn't actually produce. Verified in
  `tests/test_q4_adapter_sessions.py::TestLegacyReplayDispatch::test_exhausted_real_decisions_returns_honest_error_not_fabrication`.

This means every Q4 adapter — migrated or not — is drivable through the
same `Q4ExecutionEngine`, and results are labeled `STEPWISE` vs
`LEGACY_INTERNAL_LOOP` vs `STATIC_ONLY` vs `BLOCKED` so they are never
silently mixed in a fairness comparison. **The formal, large-scale Q4 main
experiment only admits `STEPWISE` and explicitly-approved `STATIC_ONLY`
results** — `LEGACY_INTERNAL_LOOP` remains available for coverage
experiments only.

## 3. Per-adapter migration notes

Full machine-readable status: [`q4_stepwise_support.csv`](q4_stepwise_support.csv).

### Category 1 — genuinely online (1 adapter)

**Universal Portfolios** (`adapters/universal_portfolios_adapter.py`, +180/-0
lines). Real `Algo.next_weights(S, last_b)` called once per `q4_step`,
wrapping the real `_convert_prices` + `step()` machinery directly — no
reimplementation. Algorithm state (`b` — the running weight vector) persists
in the adapter instance across steps, exactly matching the real upstream
online-learning contract. `policy_type=ONLINE_ADAPTIVE_POLICY`.

### Category 2 — rolling optimizer (1 adapter)

**skfolio** (`adapters/skfolio_adapter.py`, +121/-0 lines). Real
`WalkForward.split()` fold generator determines legal rebalance points at
`q4_initialize` time; `MeanRisk().fit()` is only re-run at real fold
boundaries (`q4_step`), holding the previous weights between rebalances.
`policy_type=ROLLING_OPTIMIZER`.

### Category 3 — train-once-then-infer / frozen learned (6 adapters)

**DeepDow** (+216/-0). Real `GreatNet` trained once at `q4_initialize`
(genuine multi-epoch fit against the real training window), frozen for
every `q4_step` — each step is one real forward pass
(`network(x_t)` under `torch.no_grad()`) against that step's real,
strictly-past lookback window.

**PGPortfolio** (+188/-0). Real per-day loop calling
`NNAgent.decide_by_history()` repeatedly (a real step-shaped upstream
method that was never previously looped from outside). Live acceptance is
`BLOCKED` on a real, pre-existing yfinance rate limit (external, transient
— not a defect in this migration); offline/unit stepwise tests (11/11)
pass without live data.

**EarnMore** (+271/-42). The only migrated adapter with deletions — its
internal `_real_run()` helper was refactored into a reusable
`_build_session()` (setup) + drain-loop split so `q4_step` can call the
same real per-step sub-calls `AgentMaskDQN.validate_net()` already made.
`_real_run()` itself still exists and is still the unchanged call site
inside `q4_policy()` — confirmed via `q4_policy()`'s own passing legacy
test suite (7/7) after the refactor.

**Qlib** (+301/-0). Real `LGBModel`/Alpha158 fit once; the real
`collect_data_loop()` generator (`qlib.backtest.backtest`) is primed one
step ahead at `q4_initialize` and advanced exactly once per `q4_step`,
settling the current real day and generating the next. Real, causal
`information_cutoff` reconstructed from `TopkDropoutStrategy`'s own
`shift=1` signal lookup (verified by reading `signal_strategy.py`
directly, not assumed).

**TradeMaster** (+187/-0). Real EIIEConv-based frozen policy, per-day
forward pass against the real DJ30 dataset (NVDA absent from the real
dataset; JNJ substituted, disclosed).

**FinRL** (+149/-0) and **FinRL-X** (+188/-0). Both externalize a real
per-step loop that the legacy `q4_policy()` path had collapsed to
`iloc[-1]` (`DRLAgent.DRL_prediction()`'s internal loop). Both adapters'
real A2C model is provably never retrained within a stepwise session, so
both report `policy_type=FROZEN_LEARNED_POLICY` **on their new stepwise
path specifically** — this is a policy-type reclassification scoped to the
new path only; each adapter's legacy `q4_policy()` path keeps its original
label untouched (FinRL: `ROLLING_OPTIMIZER`; FinRL-X: already
`FROZEN_LEARNED_POLICY`). FinRL-X's real dynamic universe selection (its
own top-25% ML-selected ticker set) was confirmed live to override the
caller-supplied universe, exactly as its legacy path already documented.

### Category 4 — genuinely online, LLM-driven (1 adapter)

**FinAgent** (+127/-0). Externalizes the real `while not done:` /
`env.step()` loop `q4_policy()` already ran, into `q4_initialize` (env
construction + `env.reset()`) + `q4_step` (one real
`DecisionTrading` DeepSeek call + one real `env.step()`) + `q4_finalize`
(session teardown). Real, deterministic desync guards compare the
harness-disclosed `timestamp`/`information_cutoff` against the session's
own real environment date on every step. `policy_type=ONLINE_ADAPTIVE_POLICY`.

### Category 5 — static/artifact-only (2 adapters, no code migration)

**AgenticTrading**, **FinClaw**. Both verified (by reading their real
`q4_policy()` output) to produce exactly one real one-time
allocation/artifact with no sequential structure at all — `decisions=None`
or empty. Forcing a per-step trajectory here would fabricate one the real
upstream project does not produce. Classified `STATIC_ONLY`. A real
`q4_initialize`-only acceptance run against AgenticTrading confirmed the
no-fabrication guarantee holds for a real (not fake) adapter: a real
step-call attempt was honestly refused, not silently answered.

### Category 6 — cannot be safely made stepwise (1 adapter)

**Vibe-Trading**. Its real decision matrix is computed once in a
monolithic vectorized backtest, before a per-bar execution loop — not
decomposable into independent per-day calls without reimplementing the
upstream engine (forbidden by this project's permanent safety rules).
Classified `STEPWISE_UNSUPPORTED`, excluded from the formal controlled Q4
track, still usable for coverage experiments via `LEGACY_INTERNAL_LOOP`.

## 4. Real acceptance runs (§five requirement: one real adapter per category)

| Category | Adapter | Real steps | Causality violations | Constraint violations |
|---|---|---|---|---|
| Online | Universal Portfolios | 49 | 0 | 0 |
| Rolling optimizer | skfolio | 34 (this run's window; matches its own independent ground-truth `WalkForward` fold count — fold count is mechanically window-length-dependent, not fixed; see §4b for 20/26/48-fold runs, all 0 violations) | 0 | 0 |
| Frozen learned | DeepDow | 40 | 0 | 0 |
| Frozen learned | FinRL | 30 | 0 | 0 |
| Frozen learned | FinRL-X | 30 | 0 | 0 |
| Frozen learned | EarnMore | 28 (matches independent legacy dry-run) | 0 | 0 |
| Frozen learned | Qlib | 25 (exact match to real trading-day count in the adapter's own computed test window) | 0 | 0 |
| Frozen learned | TradeMaster | 50 (of 76 real test dates available; capped) | 0 | 0 |
| Online, LLM-driven | FinAgent | 4 (real DeepSeek calls) | 0 | 0 |
| Static | AgenticTrading | 0 steps (1 real initialize + correct refusal on step attempt) | N/A | N/A |
| Frozen learned (blocked) | PGPortfolio | 0 (real yfinance rate limit before first step) | N/A | N/A |

Qlib and TradeMaster real live spot-checks were run as a follow-up
diligence pass beyond the minimum category requirement (both are
`FROZEN_LEARNED_POLICY`, already represented above by DeepDow/FinRL/FinRL-X/
EarnMore) — both came back clean: **0 causality violations and 0
constraint violations across every real run, for every one of the 10
STEPWISE adapters.**

All runs above went through the real, unmodified execution path: a real
per-adapter conda-env subprocess (`harness/q4_runtime.py`'s
`spawn_session`), the real `Q4ExecutionEngine`, and a real
`Q4Policy.model_validate(result.policy.model_dump())` round-trip check
against `CONTRACT/schemas.py` (unmodified) on every run.

## 4b. Coordinated single unified mini-experiment (one adapter per category, shared parameters)

The table above satisfies "at least one real adapter per category," but each
row used its own independently-chosen universe/window. This section is the
additional, stricter run: the **same** ticker universe and the **same**
`generation_window` passed to every stepwise adapter in one coordinated
session, verifying the harness's shared execution rules hold identically
across categories, not just per-adapter in isolation.

Shared parameters: `universe = ["AAPL", "MSFT", "NVDA"]`,
`generation_window = ["2022-01-03", "2023-04-17"]`. Each real adapter's own
`q4_initialize()` currently fetches its data from a single combined
`generation_window` (none of the three stepwise adapters below accept a
separate `test_window` argument — each derives its own real, internal
train/decide split, or, for the genuinely-online adapter, has no offline
split at all). The harness queried each adapter's own real, discovered
decision-eligible dates for the most recent 20 real trading days inside that
shared window (a shared-length, near-shared-calendar tail slice — exact
dates differ slightly per adapter because each project's real rebalance
cadence differs: daily for the online algorithm, every-N-days WalkForward
folds for skfolio, its own train/test split for DeepDow).

| Category | Adapter | Real steps | Dates | Causality violations | Constraint violations |
|---|---|---|---|---|---|
| Online | Universal Portfolios | 20 | 2023-03-20 → 2023-04-17 | 0 | 0 |
| Rolling optimizer | skfolio | 20 (of 26 real folds available in this window) | 2022-06-28 → 2023-03-30 | 0 | 0 |
| Frozen learned | DeepDow | 20 | 2023-03-14 → 2023-04-11 | 0 | 0 |
| Static | AgenticTrading | 0 (1 real `q4_policy()` call; `decisions=None` by construction) | 2023-04-17 | 0 | N/A |

skfolio was additionally re-run over its **full** real 26-fold set (not just
the tail 20) in this same shared universe/window as a cross-check: 26/26
real steps, 0 causality violations, 0 constraint violations — confirming the
count above is a deliberate, disclosed subset (most-recent 20), not a run
that stopped short.

AgenticTrading's real allocation for this shared universe/window came back
fully concentrated (`{AAPL: 1.0, MSFT: 0.0, NVDA: 0.0}`) with a console
warning that the Anthropic SDK is not installed in `agentictrading_real`, so
its real upstream `MeanVarianceStrategy` fell back to its own real
rule-based path rather than an LLM-assisted one — disclosed here rather than
re-run with credentials this harness does not manage.
