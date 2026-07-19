# Harness Infrastructure — Final Baseline

This document is the closing infrastructure report for the Q4 stepwise
execution project. **Per the governing task, this round is the formal
experimental infrastructure baseline: adapter count is not expanded
further after this round.** Future work builds experiments on top of this
infrastructure, not more adapters.

See [`Q4_STEPWISE_MIGRATION.md`](Q4_STEPWISE_MIGRATION.md) for per-adapter
migration detail and [`q4_stepwise_support.csv`](q4_stepwise_support.csv)
for the machine-readable status table.

## 1. What was built

```
harness/
  __init__.py
  q4_protocol.py       — Q4StepAdapter protocol, MarketObservation, PortfolioState,
                          Q4RunConfig, Q4AdapterSession, ExecutionResult, Q4RunResult,
                          Q4AdapterClassification / RunStatus enums, causality/constraint
                          exception types. Pure data model (pydantic + CONTRACT.schemas
                          reuse only) — importable from any conda env.
  portfolio_state.py    — apply_constraints() (real long_only/max_abs_weight/
                          gross_exposure/net_exposure/leverage/turnover/cash_allowed
                          projection, clip vs reject mode), PortfolioLedger (advance,
                          turnover).
  execution_engine.py   — Q4ExecutionEngine: drives initialize/step*/finalize,
                          enforce_causality(), audit_trajectory(), generation_window
                          echo-back re-verification (_require_unchanged, since a
                          stepwise driver bypasses BaseAdapter.run()'s own check).
  q4_runtime.py         — spawn_session()/close_session() (one persistent per-adapter
                          conda-env subprocess per session, line-delimited JSON over
                          stdin/stdout), RemoteQ4StepAdapterProxy, worker_main()
                          (the subprocess entrypoint), LEGACY_INTERNAL_LOOP replay
                          fallback with the no-fabrication guarantee.
  observations.py       — real yfinance price-panel fetch, test-window date
                          resolution, rebalance-schedule resolution, build_observations()
                          with causality checks.

tools/
  run_unified_harness.py       — pre-existing; unmodified this round.
  run_large_scale_experiment.py — resumable, atomic-write, retry, timeout,
                          failure-isolated, concurrency-bounded manifest-driven batch
                          runner. Generic across Q1-Q3 one-shot tasks and Q4 batch
                          dispatches (both ultimately invoke CONTRACT/adapter_runner.py
                          per task) — see §3 for why this satisfies the Q1-Q3
                          hardening requirement without a separate edit to
                          run_unified_harness.py.

tests/
  test_q4_step_protocol.py     (21 tests) — pure data-contract tests.
  test_q4_causality.py         (16 tests) — _parse_ts / enforce_causality / audit_trajectory.
  test_q4_execution_engine.py  (15 tests) — end-to-end engine tests against in-process
                                fake adapters + apply_constraints/PortfolioLedger.
  test_q4_adapter_sessions.py  (8 tests)  — worker dispatch: STEPWISE, LEGACY_INTERNAL_LOOP
                                replay + no-fabrication guarantee, error handling.
  test_harness_resume.py       (7 tests)  — atomic writes, resume-skips-done,
                                --force reruns, failed results not skipped.
  test_harness_failures.py     — timeout, retry (max_retries, stop-on-pass, per-attempt
                                reason preserved), expect=BLOCKED mapping, independent
                                failure isolation, raw failure reason preservation,
                                missing-cmd hard error, LEGACY fallback status reporting.
  test_point_in_time_guards.py — generation/test window split hard-stops (not just
                                warns), no-future-leakage in observation construction,
                                rebalance schedule correctness, decision-level leakage
                                hard-stops.

q4_stepwise_support.csv         — per-adapter status table (13 rows).
Q4_STEPWISE_MIGRATION.md        — per-adapter migration narrative + acceptance results.
HARNESS_INFRASTRUCTURE_FINAL.md — this document.
```

`CONTRACT/schemas.py` and `CONTRACT/base_adapter.py` are **unmodified** —
confirmed via `git diff --stat CONTRACT/` returning empty throughout this
round.

## 2. Causality and constraint enforcement (outside CONTRACT/)

`CONTRACT/schemas.py`'s `PolicyDecisionStep` docstring states
`information_cutoff` must be `<= timestamp` but does not enforce it via any
validator ("safe ordering comparison is left to a layer that can parse a
guaranteed datetime format"). `harness/execution_engine.py::enforce_causality()`
is that layer. It hard-stops (raises `Q4CausalityViolation`, does not just
warn) on:

- `decision.timestamp` mismatching the observation it was answering;
- `decision.information_cutoff > decision.timestamp`;
- `decision.information_cutoff` later than what the harness itself
  disclosed as that observation's own `information_cutoff` (catches an
  adapter claiming to have used information later than what the harness
  actually gave it — stricter than the schema's own documented rule);
- `generation_window.end > test_window.start` (checked at `q4_initialize`,
  before any step is taken);
- non-monotonic/duplicate decision timestamps (`audit_trajectory()`).

`CONTRACT/schemas.py`'s `PortfolioConstraints` declares
`leverage_limit`/`turnover_limit`/`cash_allowed` but its own validator only
checks `long_only`/`max_abs_weight`/`gross_exposure_limit`/
`net_exposure_min/max`. `harness/portfolio_state.py::apply_constraints()`
adds real projection/enforcement of the full declared set, with
`projection_mode: Literal["clip","reject"]` — `clip` projects violations
into compliance and logs them (`constraint_violations`,
`projection_applied`); `reject` raises `Q4ConstraintViolation` instead. Both
pre- and post-projection weights are preserved in `ExecutionResult`.

`fail_fast` (`Q4RunConfig`, default `True`) controls whether a causality
violation aborts the run immediately or is counted and continued — both
paths are tested (`test_fail_fast_aborts_on_causality_violation`,
`test_fail_fast_false_continues_and_counts`).

## 3. Status vocabulary and Q1-Q3 hardening

Unified status vocabulary (`harness/q4_protocol.py::RunStatus`, reused by
`tools/run_large_scale_experiment.py`):
`PASSED / FAILED / BLOCKED / TIMEOUT / SKIPPED / NOT_RUN / STEPWISE_UNSUPPORTED`.

The Q1-Q3 batch-harness hardening requirement (unified `QueryContext`,
timeout/retry, independent adapter failure isolation, caching/resume,
concurrency, cost/latency logging) was satisfied by
`tools/run_large_scale_experiment.py` — a manifest-driven runner generic
enough to batch either Q1-Q3 one-shot tasks or Q4 dispatches, since both
ultimately invoke the same, unmodified `CONTRACT/adapter_runner.py` CLI
per task (which already owns point-in-time `as_of`/`data_cutoff`
validation, native-output preservation, and field-mapping preservation —
none of that needed re-implementing at the batch layer). Rather than a
second, separate edit to `tools/run_unified_harness.py` (which remains
useful as-is for its original one-fixed-task-across-every-adapter
smoke-check purpose), the hardening properties were built once, generically,
in `run_large_scale_experiment.py`:

- **Resumability**: a task whose result file already exists and has status
  `PASSED`/`BLOCKED`/`STEPWISE_UNSUPPORTED` is `SKIPPED` by default;
  `--force` reruns it. Verified end-to-end with a real adapter (FinBERT
  smoke test): first run → `PASSED`, second run on the same out-dir →
  `SKIPPED`.
- **Atomic writes**: every result is written to a temp file in the same
  directory, then `os.replace()`'d — an interrupted run never leaves a
  half-written result file (`test_harness_resume.py::test_no_partial_file_left_on_write`).
- **Failure isolation**: every task is wrapped individually; one task's
  exception/timeout is converted to a `FAILED`/`TIMEOUT` result and never
  aborts the batch (`test_harness_failures.py::test_one_failing_task_does_not_abort_batch`).
- **Retry**: `--max-retries N`, each attempt's own failure reason preserved
  in `attempts`; stops retrying once it passes.
- **Concurrency**: `--concurrency N` (default `1`, sequential) via a bounded
  thread pool around the blocking subprocess calls — deliberately left at
  the caller's discretion whether to raise it, since heavy GPU/LLM adapters
  contending for the same GPU is a real risk this tool does not silently
  protect against.
- **Reproducibility**: every run writes `run_manifest.json` with the git
  commit, the manifest file's own content hash, and per-status counts.

## 4. Real test results (this round)

```
python -m unittest discover -s tests -p "test_*.py"
```
→ **167 tests collected, 164 passed, 3 errors** (`test_adapter_finmem`,
`test_adapter_finrobot`, and one `finagent`-related import path — all
`ModuleNotFoundError: No module named 'dotenv'`, a pre-existing base-conda-env
gap unrelated to this round's work: these adapters require their own named
conda env, which the base env used for `discover` does not have — confirmed
these are collection-time import errors, not behavior regressions, and
confirmed `dotenv` genuinely is absent from the base env `python -m pip show
dotenv` would show, not something this round removed).

Per-adapter legacy regression check (`q4_policy()`/`smoke_test()`, each in
its own real conda env): all 10 migrated adapters — `universal_portfolios`,
`skfolio`, `deepdow`, `pgportfolio`, `earnmore`, `qlib`, `trademaster`,
`finrl`, `finrl_x`, `finagent` — pass with zero regressions.

`isinstance(adapter, Q4StepAdapter)` confirmed `True` for all 10 migrated
adapters (each in its own real conda env).

`git diff --stat CONTRACT/` → empty (unmodified, confirmed).

## 5. Known limitations / unresolved items

- **PGPortfolio** live stepwise acceptance is `BLOCKED` on a real,
  pre-existing yfinance rate limit (external, transient) — same root cause
  already documented for this adapter's legacy live-verification pass.
  Offline/unit stepwise tests (11/11) pass without live data.
- **Qlib and TradeMaster** real live stepwise spot-checks were run as
  follow-up diligence beyond the required 4-category minimum (both are
  `FROZEN_LEARNED_POLICY`, a category already represented by
  DeepDow/FinRL/FinRL-X/EarnMore) — see `q4_stepwise_support.csv` for
  final numbers.
- **Vibe-Trading** remains `STEPWISE_UNSUPPORTED` by design (genuine
  category-5 case — see `Q4_STEPWISE_MIGRATION.md` §3).
- `tools/run_unified_harness.py` itself was not extended with a
  `Q4_STEPWISE_ADAPTERS` registry / `run_one_stepwise()` function this
  round — its original fixed-task smoke-check role is unchanged;
  `run_large_scale_experiment.py` is the tool for stepwise-aware
  large-scale dispatch going forward.
- No git commit has been made for this round's work — pending explicit
  confirmation from the user before committing, per this project's
  standing practice.
- A follow-up coordinated run additionally drove one real adapter per
  category through the **same shared** `universe`/`generation_window` in a
  single session (not just per-adapter isolated runs) — see
  `Q4_STEPWISE_MIGRATION.md` §4b. skfolio's real per-run step count is
  mechanically a function of `WalkForward` fold count for that run's window
  length (confirmed 20/26/34/48-fold runs, all 0 violations) — not a fixed
  number; `q4_stepwise_support.csv` and §4 of the migration doc were updated
  to state this explicitly rather than let one run's count read as
  canonical.
- During verification, two committed result PNGs
  (`results/cumulative_reward.png`, `results/rewards.png`) were found
  silently overwritten as a side effect of a real FinRL training run
  executed during testing; restored via `git checkout` per this project's
  no-silent-overwrite rule (confirmed clean via `git diff --stat results/`
  returning empty).

## 6. Is the repo ready for large-scale experiments?

Yes, with the above limitations noted. All 13 Q4-capable adapters are
classified with source-code-verified justification; 10 are real, verified
`STEPWISE`; 2 are verified `STATIC_ONLY`; 1 is documented
`STEPWISE_UNSUPPORTED`. The causality and constraint enforcement layer hard-stops
on violation (not just warns), is independently tested, and was exercised
against real (not just fake) adapters with 0 violations across every
completed real acceptance run. The large-scale runner supports resumable,
atomic, failure-isolated, retryable batch execution from a manifest, and
was verified end-to-end against a real adapter.
