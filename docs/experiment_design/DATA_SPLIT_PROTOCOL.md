# Data Split Protocol

Grounds `EXPERIMENT_PROTOCOL.md`'s experiment groups in a strict temporal
and adapter-eligibility protocol. Built read-only from `CONTRACT/schemas.py`
(field names/causality contract), `PROJECT_SCHEMA_AUDIT.md`,
`ADAPTER_CAPABILITY_RECOVERY.md`, and `NEW_ADAPTER_INTEGRATION.md`
(real adapter live-readiness facts). No adapter, schema, or harness file
was modified to produce this document.

---

## 1. The four intervals and their purpose

| Interval | Purpose | Who may fit what here |
|---|---|---|
| **Train** (upstream) | Where each adapter's *own* model/policy was originally fit — outside this project's control for most adapters (pretrained LLMs, pre-trained factor models, RL policies trained by their own upstream repo). Recorded, not re-run, except where an adapter's own retraining is part of its native operation (e.g. skfolio's `WalkForward` refit, PGPortfolio's `rolling_train()`). | Upstream project code only — this protocol never trains an upstream model. |
| **Calibration** | Fitting L1.2's calibration mapping (confidence → realized outcome) and any Layer 1 diagnostic threshold (e.g. the "adapter-relative extreme risk" threshold in `EXPERIMENT_PROTOCOL.md` §2.2). | L1.2's calibration curves, the contradiction ontology's adapter-relative thresholds. |
| **Validation** | Fitting anything that is *itself* part of a Layer 2 method: L2.1's fusion weights, L2.2's router, L2.5's policy selector, L2.6's meta-model. **Not** where H1's practical-significance threshold is fixed — that happens earlier, during the pilot stage on Calibration-interval data (§1.1); Validation is where the already-locked threshold is *applied* to the pooled H1 test. | Fusion weights, router parameters, meta-model parameters. Pre-registered thresholds/definitions (H1's ontology, §2.2/§2.4) are fixed before any data is touched at all; their pilot-computed *numeric value* (§1.1) is locked before Validation begins, not fit here. |
| **Untouched final test** | One-shot evaluation of every claim (H1–H7) after everything above is frozen. | Nothing is fit here. Read-only evaluation only. |

**Hard rule, non-negotiable (corrected — Session 3 protocol consistency
audit, Task B1)**: a prior version of this sentence claimed "calibrator
fit, contradiction-threshold fit, router fit, and meta-model fit all happen
on validation only," which directly contradicted the table two lines above
(which correctly assigns calibrator/threshold fitting to the **Calibration**
interval, not Validation). The corrected, single rule, matching the table
exactly: **confidence calibrators, adapter-relative risk thresholds, and
Layer 1 diagnostic normalization are fit on the Calibration interval only;
Layer 2 method parameters (fusion weights, router parameters, meta-model
parameters, policy-selector hyperparameters) are fit on the Validation
interval only; nothing is fit on the untouched final test interval, ever.**
This is stated identically in `EXPERIMENT_PROTOCOL.md` §2.4/§9 and
`RISK_AND_FAILURE_PLAN.md` — if any of those three files' wording still
implies calibrator fitting happens on Validation rather than Calibration,
that wording is stale and this paragraph is the corrected source of truth.

### 1.1 How the "pilot stage" relates to these four intervals (added — Task B1)

`EXPERIMENT_DEPENDENCY_MAP.md` defines four **process stages** (pilot →
screening → full validation → final test) — a different axis from this
section's four **data intervals** (train/calibration/validation/test).
These were previously left unreconciled, which is what produced the
apparent conflict between `EXPERIMENT_PROTOCOL.md` §2.4 ("the [H1 power/
threshold] procedure... at the pilot stage... before the validation stage
begins") and this file's old Validation-interval row (which read as if the
threshold were fixed *during* the Validation interval). **Resolution,
fixed now**: the pilot *stage* is a small-scale rehearsal that runs
end-to-end machinery (including H1's power-analysis procedure,
`EXPERIMENT_PROTOCOL.md` §2.4) on a small subset of the **Calibration
interval's** data (never Validation, never Test) — chosen because the
Calibration interval is exactly where this protocol's own threshold-fitting
already lives (§1's table). The pilot stage's output (the locked
practical-significance threshold, the locked minimum-coverage floor, the
locked K for L1.2, the locked generic-disagreement-covariate formula
choice where any remained open) is then carried forward and applied,
unchanged, when the full Calibration-interval fitting and Validation-
interval fitting later run at full scale. In interval terms: **the pilot
stage never touches Validation or Test data at all** — it is entirely a
small-scale, early rehearsal on (a subset of) Calibration-interval data,
temporally and data-wise prior to both the full Calibration-interval fit
and the Validation-interval fit, not a stage that runs "inside" Validation.

## 2. Cutoff definitions (schema-native, not invented)

`CONTRACT/schemas.py`'s `QueryContext` already carries `as_of` (decision
timestamp) and `data_cutoff` (latest information timestamp used), and
`PolicyDecisionStep` carries `information_cutoff` with an enforced
`information_cutoff <= timestamp` invariant. This protocol does not
introduce new cutoff semantics — it specifies **which values these fields
must take in each interval**:

- **Calibration/validation/test windows are experiment-execution-layer
  concepts, not adapter-output concepts** — `Q4Policy.generation_window`'s
  own docstring is explicit on this: *"Validation/test windows are not part
  of this contract — they belong to the harness/experiment execution
  layer, not to the adapter's policy output."* This protocol is exactly
  that execution layer. Adapters continue to only ever see and record
  `as_of`/`data_cutoff`/`generation_window`; they must never be told
  "this call is the test set" (that knowledge belongs only to this
  protocol and its evaluation code, never to the decision-producing call
  itself — an adapter branching its behavior on which split it's being
  asked about would be a leakage channel).
- **Prediction horizon vs. outcome measurement**: a decision with
  `context.horizon = "20d"` made at `as_of = T` requires realized outcome
  data through `T+20 trading days` to compute `E` (`EXPERIMENT_PROTOCOL.md`
  §2.3). That `T+20` outcome window belongs to the *interval T falls in*,
  not to whatever interval `T+20` happens to land in — see §3's embargo
  rule below for why this matters.

## 3. Embargo / purge rule (concrete, not generic)

Because `E` for a decision at time `T` with horizon `h` requires data
through `T+h`, a naive contiguous calibration→validation→test split leaks:
the last `h` trading days of the calibration interval would have their
labels computed using data that falls inside the validation interval.

**Rule**: insert an embargo gap of **at least `max(h)` trading days**
(i.e., at least 20 trading days, the longest candidate horizon) between
every pair of adjacent intervals (train/calibration boundary,
calibration/validation boundary, validation/test boundary). No decision
within the embargo gap is used for fitting *or* evaluation in either
adjacent interval — it is simply excluded, not double-counted. This
directly extends the same causality discipline `CONTRACT/schemas.py`
already enforces for `PolicyDecisionStep.information_cutoff` to the
evaluation layer, which the schema explicitly disclaims responsibility for.

## 4. Shared Evaluation Protocol — field-level specification

Expands `EXPERIMENT_PROTOCOL.md` §4's three tracks. Every field below must
be **fixed once, before pilot stage begins**, and used identically for
every adapter compared on the Controlled Scientific Track:

| Field | Controlled Scientific Track value (fixed at pilot stage) |
|---|---|
| `as_of` sequence | One shared trading-calendar sequence, not per-adapter |
| `data_cutoff` | Equal to `as_of` unless an adapter has a documented, disclosed reporting lag (record the lag, do not silently equalize it away) |
| Horizon set | {1d, 5d, 20d} — Session 1's candidate horizons, reused verbatim |
| Universe / universe mapping | One frozen base universe (reusing the precedent already established in `NEW_ADAPTER_INTEGRATION.md`'s unified harness run, `[AAPL, MSFT, NVDA]`, extended per pilot-stage sample-size needs) **plus an explicit per-adapter universe-mapping table** for adapters with native universe restrictions (e.g. TradeMaster's DJ30-only scope, EarnMore's sector-grouped universes) — an adapter whose native universe cannot cover the shared universe is either excluded from that specific Controlled comparison or evaluated only on its native-universe subset, with the reduced scope stated explicitly, never silently generalized |
| Trading calendar | One shared calendar; the already-real, already-fixed Qlib calendar-boundary `IndexError` (`ADAPTER_CAPABILITY_RECOVERY.md`) is the concrete precedent for why this must be pinned explicitly, not left to each adapter's own data-fetch logic |
| Transaction cost model | One shared cost schedule, swept across 2–3 regimes per `EXPERIMENT_PROTOCOL.md` X.3 (zero/realistic/stressed) |
| Benchmark | One shared benchmark (e.g. equal-weight buy-and-hold over the shared universe) for all Q4/portfolio comparisons |
| Execution delay | One shared assumption (e.g. decisions execute at next available trading timestamp after `as_of`) |
| Risk-free rate | One shared source/series for Sharpe/Sortino computation |
| Rebalancing assumption | One shared rebalance-frequency-and-timing rule per adapter class (rolling/online adapters rebalance at their own native cadence, recorded; static adapters are evaluated buy-and-hold from `initial_weights`) |
| Missing-output policy | If an adapter fails to return a decision at a legal rebalance point: hold the prior position (never assume cash, never assume "no penalty" — record as a `constraint_violations`-style event) |
| Failure handling | A failed/errored adapter call at one step does not retroactively invalidate prior steps; log and exclude that step only, report the failure rate as a metric (`RISK_AND_FAILURE_PLAN.md`) |
| Cash treatment | `"CASH"` key convention already used in `PolicyDecisionStep.target_weights` (per schema) is the canonical cash representation project-wide |
| Leverage / exposure audit | Every step's gross/net exposure checked against `PortfolioConstraints` if declared; undeclared constraints are not assumed (schema explicitly does not default to long-only/no-leverage) |
| Result aggregation | Pre-registered aggregation method across assets/regimes/horizons (see `METRIC_DESIGN.md`) fixed before any result is computed, not chosen post-hoc to flatter one method |

## 5. Adapter eligibility tiers for the historical main experiment

Directly answers the task brief's instruction that this session defines
*eligibility criteria*, not a final adapter list (that is Session 3's
registry). Derived from real, already-observed facts in
`ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md` — not
invented:

- **TIER-1 (historical main-experiment eligible)**: adapter has (a) a live
  `CONTRACT/adapter_runner.py` **PASS**, (b) a genuinely point-in-time-
  capable data source (see the explicit PIT caveat below — schema-PASS is
  necessary but not sufficient), and (c) either a real causal Q4
  `decisions` trajectory (0 causality violations already demonstrated) or
  an honestly single-point policy. Examples already meeting (a): qlib,
  alphagen, rdagent, atlas, deepalpha, tradingagents, finrl, quantmuse,
  finclaw, finrl_x, ai_hedge_fund, agentictrading, vibe_trading, finagent,
  skfolio, universal_portfolios, earnmore, trademaster, deepdow, finrobot,
  alphaforge — subject to (b)/(c) re-verification at the pilot stage
  (`EXPERIMENT_DEPENDENCY_MAP.md`), not assumed automatically transferable
  from a schema-level PASS.
- **TIER-2 (current-context / diagnostic-only, not historical main
  experiment)**: adapters with a real, documented live-stage limitation:
  - **FinMem** — live-**BLOCKED** on a real missing OpenAI-compatible
    embeddings credential (`NEW_ADAPTER_INTEGRATION.md`); usable only in a
    current-context/offline-schema diagnostic role until the credential
    gap is resolved outside this session's scope.
  - **PGPortfolio** — live-**BLOCKED** on a real dead upstream data API
    (Poloniex HTTP 410, permanently gone) plus a transient yfinance rate
    limit in its substitute path; offline/schema tests pass. Same
    diagnostic-only tier until re-verified live.
  - **FinBERT** — schema/live **PASSED**, but its data source (yfinance
    headlines) **"exposes only current headlines, not historical
    as-of"** (`NEW_ADAPTER_INTEGRATION.md`, verbatim limitation) — this is
    a genuine point-in-time failure for any *historical* backtest-style
    main experiment, even though the adapter itself runs live without
    error. FinBERT is eligible for **current-context/live-only** roles
    (e.g. a live pilot slice), not for the historical Controlled
    Scientific Track main experiment, until a historical-headline source
    is substituted (out of this session's scope to arrange).
- **TIER-3 (coverage-study only, excluded from any claim-bearing
  experiment)**:
  - **Alpha-GFN** — explicitly deferred (`P2/DEFERRED`,
    `NEW_ADAPTER_INTEGRATION.md`), demo-level only, no stable checkpoint,
    no formal method implementation. Not integrated as a production adapter
    at all; cannot be TIER-1/2.
  - **Real NoFx** (`NoFxAiOS/nofx`) — confirmed **BLOCKED — requires
    upstream modification**, a single continuously-running stateful Go
    server with no point-in-time query interface; no adapter exists for it
    (the file that used to claim this name actually wraps QuantMuse, a
    different real project, correctly renamed `quantmuse_adapter.py`).
    Genuinely un-wrappable under this project's thin-adapter constraint —
    a coverage-study footnote only, never a claim-bearing input.

**Re-verification requirement**: this tier assignment is a snapshot from
`ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md`'s existing
verification runs. Before the historical main experiment (not the pilot),
Session 3's registry must confirm each TIER-1 adapter's live/PIT status
has not regressed (credentials expire, upstream APIs change — PGPortfolio's
own history already shows an upstream API dying permanently mid-project).

## 6. Regime-labeling causality rule

For `EXPERIMENT_PROTOCOL.md` L1.4/L2.2: a regime label for `as_of = T` must
be computable using **only information with timestamp <= `data_cutoff` at
T** — i.e., the regime classifier itself is subject to the same
`information_cutoff <= timestamp` discipline as any adapter decision. A
regime classifier fit once on the full historical span (including data
after T) and then applied retroactively to label T is a leakage channel
disguised as "just labeling," not a decision — this protocol treats regime
labeling as a decision-equivalent artifact for causality purposes.
Concretely: if a regime classifier requires fitting (e.g. a rolling
volatility-percentile threshold), the fit window must itself respect the
train/calibration/validation/test boundaries in §1 — a regime threshold may
not be fit on data spanning into validation or test.

## 7. Handling of known non-causal artifacts

`finrl_adapter.py`'s deliberate `decisions=None` design
(`ADAPTER_CAPABILITY_RECOVERY.md` §15 — a full in-sample action-memory
trajectory would replay a policy trained on the same window, violating
no-future-information) is the project's own precedent for a class of risk
this protocol must guard against project-wide, not just for that one
adapter: **any adapter whose Q4 trajectory was generated by a policy
trained end-to-end on the same window it is being asked to decide over is
ineligible for TIER-1 historical evaluation on that trajectory**, regardless
of whether the adapter's schema-level output looks like a normal causal
`decisions` list. This must be checked per-adapter at the pilot stage
(`EXPERIMENT_DEPENDENCY_MAP.md`), not assumed safe by default.
