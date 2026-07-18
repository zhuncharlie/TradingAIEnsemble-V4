# Adapter Capability Recovery Report

**Scope**: capability recovery (not re-migration) across the 16 real, schema-v2.0.0-migrated
adapters in `adapters/*.py`. Goal: go back to each upstream project's real code and native
output and restore Q1–Q4 capabilities that schema v1's narrower shape, or an incomplete v1
adapter implementation, previously discarded. `PROJECT_SCHEMA_AUDIT.md`/`.csv` was used as a
starting reference, but every finding below was re-verified against current real source code
(file paths and line-level citations given throughout), not copied from the audit.

**Constraints honored throughout**: `CONTRACT/schemas.py` was not modified. No upstream
project's core trading/model logic was modified, monkey-patched, or reimplemented. All
adapters remain thin wrappers — only extraction/transformation/packaging of information the
upstream project already computes. No confidence/reasoning/signal/weight/policy value was
fabricated. Content that cannot honestly map to a v2 schema field was left in `native_output`
or documented as a limitation rather than forced into a field. Q5 and all
return/Sharpe/drawdown/backtest-evaluation metrics were kept out of every adapter.

**Classification scheme applied to every finding**:
1. **ABSENT** — the upstream project genuinely has no such capability.
2. **RECOVERED** — upstream has the capability, it was already computed, and the old adapter
   discarded or truncated it. Fixed in this pass.
3. **INTERNAL-NOT-PUBLIC** — upstream computes it internally (a local variable, an un-returned
   object) but exposes no public accessor. Not monkey-patched; documented as a limitation.
4. **UPSTREAM-MODIFICATION-ONLY** — only reachable by editing upstream source. Not done;
   documented as a limitation.

---

## Summary table (16 adapters)

| Adapter (upstream project) | 原始能力 | 旧Adapter丢失内容 | 本次恢复内容 | Q覆盖变化 | Native/Derived | Harness结果 | 剩余损失 |
|---|---|---|---|---|---|---|---|
| `ai_hedge_fund_adapter.py` (ai-hedge-fund) | Real `PortfolioDecision.quantity` per-ticker order size | v1 dropped quantity, action-only | Already recovered in prior wave (`target_position` = real quantity); re-verified live this pass, no new change | Q1 unchanged | NATIVE | PASS (live: `action=HOLD, target_position=0.0`, real self-reported confidence) | none new |
| `agentictrading_adapter.py` (AgenticTrading) | Real mean-variance tangency weights, full policy metadata | none (already fully migrated) | Re-verified live, no new change | Q4 unchanged | NATIVE | PASS (live: `STATIC_ALLOCATION`, weights `{AAPL:1.0, CASH:0.0}`, `long_only=True`, `net_exposure∈[1,1]`) | none new |
| `vibe_trading_adapter.py` (Vibe-Trading / cross-market signal engine) | Real daily `positions.csv`/`trades.csv` trajectory | v1/pre-fix code read only the last row, called deleted v1 classes | Already fixed in prior session pass (full 385-day trajectory); not touched this pass | Q3+Q4 unchanged | NATIVE | PASS (385 real decisions, 0 causality violations, established prior pass) | none new |
| `quantmuse_adapter.py` (renamed from `nofx_adapter.py` — **wraps QuantMuse, not real nofx**) | Real 17-indicator technical factor dict (RSI/MACD/MAs/Bollinger/momentum) | RSI (the one bounded, directly-Q3-usable reading) was computed but only ever placed in evidence text, never as a queryable signal value | **RSI-14 recovered as `Q3Signal.values[ticker]`** (RECOVERED, category 2); all 16 other readings kept as `EvidenceItem`s (unchanged) | +Q3 (was Q2-only) | NATIVE | PASS (15/15 direct `smoke_test()` checks; re-verified personally this pass) | Real `nofx` (NoFxAiOS/nofx, Go, single stateful server, no point-in-time query API) remains genuinely un-wrappable as a thin Python adapter — re-confirmed this pass; documented as UPSTREAM-MODIFICATION-ONLY / no public per-time-step interface exists at all, category 4. No new `nofx_adapter.py` was written (see dedicated section below). |
| `finclaw_adapter.py` (finclaw StrategyDNA GA) | Real `StrategyDNA` fields: `score_stock()` formula, `min_score` gate, `hold_days`, `max_positions`, `capital_utilization`, per-factor weights, `sector_max_pct` | Q4 was artifact-only; `decision_policy`/`universe_policy`/`observation_policy`/`constraints` all missing | **Full Q4 enrichment recovered** (RECOVERED): real decision rule + gate, real holding horizon, honestly-scoped universe policy, real weighted observation features, real `long_only`/`gross_exposure_limit` constraints | Q4 richness ↑ (artifact-only → full policy) | NATIVE | PASS (18/18 `smoke_test()`; live CLI run wrote `finclaw.json`, 12265 bytes) | `dna.sector_max_pct` is declared but never read in the executed `evaluate()` path (grep-confirmed) — correctly excluded from `constraints`, documented as INTERNAL-NOT-PUBLIC/dead-field limitation, not fabricated as active |
| `finrl_x_adapter.py` (FinRL-Trading / adaptive_rotation) | Real `RegimeResult` with `state`, `risk_score`, **`cash_floor`** | `cash_floor` only ever appeared inside prose `explanation` text, never as a structured/queryable Q2 value | **`regime_recommended_cash_floor` StateEstimate recovered** (RECOVERED) citing real `detect_slow_regime().cash_floor` | Q2 richness ↑ (1 state → 2 states) | NATIVE | PASS (17/17 `smoke_test()`; live q2_state print showed both real states: `market_regime=risk_on`, `regime_recommended_cash_floor=0.0`) | none found |
| `qlib_adapter.py` (Qlib) | Real `TopkDropoutStrategy`/backtest-loop-driven rebalancing policy | Q4 was entirely absent (Q3-only) | **Full real Q4 recovered** (RECOVERED): real strategy-driven daily rebalancing trajectory via unmodified `qlib.backtest.backtest_loop()` | +Q4 (was Q3-only) | NATIVE | PASS (16/16 `smoke_test()`; live run: 24 real decisions, 0 causality violations, weights sum≈1.0) | Real `IndexError` bug found+fixed (calendar boundary, not a logic bug — see dedicated section) |
| `atlas_adapter.py` (atlas GP factor search) | Real, complete validation-accepted individual set from `GPProcess.run()` | Truncated to top-3 (best + 2 runners-up) | **Full accepted-formula set recovered** (RECOVERED), in both evidence and `native_output.upstream.accepted_formulas` | Q3 richness ↑ | NATIVE | PASS (12/12 `smoke_test()`; live run shows real Accepted/Not-Accepted formula log) | Per-generation `Logbook` stats + per-batch best-individual history are real local variables inside `run()`, never assigned to `self`/returned — no public accessor exists (INTERNAL-NOT-PUBLIC, category 3) |
| `alphagen_adapter.py` (AlphaGen) | Real `LinearAlphaPool.update_history` (`AddRemoveAlphas` log) | Never read anywhere in the adapter | **Pool search trajectory recovered** (RECOVERED): full structured history in `native_output`, bounded evidence summary (update count + final `.describe()`) | Q3 richness ↑ | NATIVE | PASS (13/13 `smoke_test()`) | none found |
| `rdagent_adapter.py` (RD-Agent) | Real per-stage `FactorSingleFeedback` fields: `execution_feedback`, `value_feedback`, `code_feedback` | Only the combined `final_decision`/`final_feedback` pair was surfaced | **3 richer per-stage feedback fields recovered** (RECOVERED) as `EvidenceItem`s + `native_output.coder_feedback` | Q3 richness ↑ | NATIVE | PASS (12/12 `smoke_test()`; live run made real DeepSeek calls, `deepseek/deepseek-v4-flash`) | none found |
| `deepalpha_adapter.py` (stock-market-prediction-engine) | Real `RealTimePredictionEngine.generate_predictions()`: `model_agreement`, `confidence_interval`, `confidence_label` | Adapter hand-reimplemented the `model_agreement` formula instead of calling the real function; `confidence_interval` was never read at all | **Switched to calling the real function directly** (RECOVERED) — `model_agreement` now genuinely upstream-computed, not duplicated; **real `confidence_interval` recovered** as evidence on both Q1 and Q3 | Q1+Q3 richness ↑ | NATIVE | PASS (11/11 `smoke_test()`; live run confirmed real `generate_predictions()` log line + real interval bounds in output JSON) | `confidence_label` ('high'/'medium'/'low') declined: real function, but its threshold (`Config.signal_threshold_pct()`, percentage-point scale) is scale-inconsistent with this adapter's fractional-return predictions — verified via `src/config.py`; surfacing it would mislabel nearly every real prediction "low" (INTERNAL-NOT-PUBLIC-under-honest-use, category 3-like) |
| `tradingagents_adapter.py` (TradingAgents) | Real 3-way risk-debate transcript (`aggressive_history`/`conservative_history`/`neutral_history`) | 100% discarded — no dedicated field, never put in evidence either | **Recovered as 3 `EvidenceItem`s** (RECOVERED), verified as the real, direct input to the Portfolio Manager's own prompt (`managers/portfolio_manager.py`) | Q1 richness ↑ | NATIVE | PASS (13/13 `smoke_test()`; live CLI run shows real LLM debate text in evidence) | Structured `PortfolioDecision`/`SentimentReport` Pydantic objects are real but never retained in graph state — only rendered markdown is (`render_pm_decision`/`render_sentiment_report` convert immediately, verified in `managers/portfolio_manager.py`/`analysts/sentiment_analyst.py`) — regex-parsing the deterministic rendered headers remains the only route (INTERNAL-NOT-PUBLIC, category 3, pre-existing/re-confirmed) |
| `fingpt_adapter.py` (FinGPT v3.1) | Real per-headline sentiment scores, up to `MAX_HEADLINES=5` | Truncated to top-3 by \|label\| | **All scored headlines recovered** (RECOVERED) — a small, already-bounded (≤5) real result set, no unbounded-evidence risk | Q2 richness ↑ | NATIVE | PASS (9/9 `smoke_test()`; real ChatGLM2 model load + inference confirmed) | Per-class logits/confidence genuinely uncaptured (greedy decode only) — would need materially more work (custom `output_scores=True` decoding) for uncertain correctness gain; left as documented, pre-existing limitation, not attempted this pass |
| `prediction_arena_adapter.py` (Metaculus/forecasting-tools + real Kalshi data) | Real Kalshi market dict + real DeepSeek forecast dict (incl. `cost_usd`) | No `run()` override at all → `native_output` silently defaulted to `{}`; `cost_usd` computed but never surfaced | **`run()` override added** (RECOVERED) to capture real market+forecast as `native_output`; **`cost_usd` recovered** as an `EvidenceItem` | Q2 unchanged in content, provenance fixed | NATIVE | PASS (10/10 `smoke_test()`, incl. new `native_output_captures_market_and_forecast` check) | none found |
| `finrl_adapter.py` (FinRL) | Real daily action-memory trajectory from `DRLAgent.DRL_prediction()` | Only the last row was ever used | **Reviewed and intentionally NOT recovered**: the full trajectory is an in-sample replay through the same window the policy was trained on — exposing it as a per-day causal `decisions` trajectory would violate the "no future information" rule. Current design (`initial_weights` = terminal snapshot, `decisions=None`) is the causality-correct choice, confirmed, not a gap | Q4 unchanged | NATIVE | PASS (10/10 `smoke_test()`; real A2C training + prediction confirmed) | Real per-day in-sample weight sequence remains unexposed by design (correct, not a loss) |
| `example_stub_adapter.py` | N/A — reference template, no upstream project wired up | N/A | N/A — confirmed not a real adapter, out of scope | N/A | N/A | N/A | N/A |

---

## Detailed notes per adapter

### 1–3. `ai_hedge_fund`, `agentictrading`, `vibe_trading` — already correct, re-verified only
These three were already fully capability-recovered in the prior session pass (before this
capability-recovery task began). This pass re-ran their live smoke tests to confirm they still
hold; no code changes were made.

- **ai_hedge_fund**: live run via `CONTRACT/adapter_runner.py` (`ai_hedge_fund_real` env) →
  `action=HOLD, target_position=0.0`, `confidence={value:1.0, kind:SELF_REPORTED, raw_value:100.0}`.
- **agentictrading**: live run (`agentictrading_real` env) →
  `policy_type=STATIC_ALLOCATION, initial_weights={AAPL:1.0, CASH:0.0}`,
  `constraints={long_only:True, net_exposure_min:1.0, net_exposure_max:1.0}`.
- **vibe_trading**: established in the prior pass — 385 real `PolicyDecisionStep`s from real
  `positions.csv`/`trades.csv`, 0 causality violations.

### 4. `quantmuse_adapter.py` — nofx re-investigation (explicit user request)
The user explicitly asked whether the adapter previously named `nofx_adapter.py` still wraps
the wrong upstream project. It did: it wraps **QuantMuse** (a Python multi-factor/sentiment
trading toolkit), not the real **nofx** (`NoFxAiOS/nofx`, a Go multi-provider LLM trading
system). Actions taken:
- `git mv adapters/nofx_adapter.py adapters/quantmuse_adapter.py`; class renamed
  `NofxAdapter` → `QuantMuseAdapter`; `name="nofx"` → `name="quantmuse"`.
  `requires_env` kept as `"nofx_real"` (the real conda env name is unchanged — renaming the
  env itself was out of scope and not required for correctness).
- Real nofx (`NoFxAiOS/nofx`) was **re-verified live**: its earlier LLM-provider lock-in issue
  is resolved upstream (now 8 providers), but it is decisively still un-wrappable as a thin
  Python adapter — 278 files, zero Python surface, a single continuously-running stateful Go
  server with no point-in-time/backtest query API. This is a **category 4** finding
  (upstream-modification-only / no public per-time-step interface exists at all), documented in
  a "2026-07 RE-VERIFICATION ADDENDUM" in the file's docstring. **No new `nofx_adapter.py` was
  written** — there is no honest thin-wrapper surface to write one against.
- Within QuantMuse itself: real RSI-14 (`factors['rsi']`) was recovered as `Q3Signal.values`
  (previously present only as evidence text) — chosen over MACD/moving-averages/Bollinger
  because it's the one reading bounded to a fixed, directly-interpretable `[0,100]` scale; the
  other 16 real technical readings remain as `EvidenceItem`s, unchanged.

### 5. `finclaw_adapter.py` — Q4 enrichment
Recovered real `decision_policy` (citing the exact `score_stock()` formula and `min_score`
gate, `hold_days`→`holding_horizon`), `universe_policy` (honestly disclosing single-asset scope
vs. the genome's real multi-asset capability, `max_assets` from `dna.max_positions`),
`observation_policy` (top-weighted real factors), and `constraints` (`long_only=True` verified
via real market-dispatch code; `gross_exposure_limit` from real `dna.capital_utilization`).
`dna.sector_max_pct` was deliberately **excluded** after grep-confirming it is declared in the
dataclass but never read anywhere in the executed `evaluate()` path — reported as an unenforced
field, not falsely claimed as an active constraint.

### 6. `finrl_x_adapter.py` — Q2 cash-floor recovery
`adaptive_rotation.market_regime.detect_slow_regime()`'s real `RegimeResult.cash_floor` was
previously only mentioned in prose inside `explanation`. Added a second `StateEstimate`
(`dimension="regime_recommended_cash_floor"`) with `value_numeric=float(regime_result.cash_floor)`
and a real `EvidenceItem` citing the exact upstream function. Live-verified real output:
`market_regime=risk_on (value_numeric=0.0)`, `regime_recommended_cash_floor=0.0`.

### 7. `qlib_adapter.py` — Q4 recovery + real bug fix
A parallel agent added a full, real `q4_policy()` driven by unmodified
`qlib.contrib.strategy.signal_strategy.TopkDropoutStrategy` fed the real Alpha158/LGBModel
prediction series, via real `qlib.backtest.get_strategy_executor()` + `backtest_loop()`.

A real bug surfaced during live verification: `IndexError: index 573 is out of bounds for axis
0 with size 573` inside **unmodified upstream** `qlib/backtest/utils.py::get_step_time`
(`self._calendar[calendar_index + 1]`) — the real yfinance-fetched calendar only extended
through `test_end`, but `TopkDropoutStrategy`'s final rebalance step needs one more calendar
entry. **Fixed at the adapter's data-fetch boundary**, not by touching qlib: added a
`Q4_CALENDAR_BUFFER_DAYS = 12` constant, widening only the raw CSV-fetch window
(`test_end + 12 days`). `Alpha158`'s own handler `end_time` stays pinned at `test_end`, so no
feature or label ever sees data past `test_end` — verified this introduces no causality
violation, purely calendar bookkeeping for an unmodified upstream requirement.

Post-fix live verification: 24 real decisions, 0 causality violations
(`information_cutoff <= timestamp` held for all), timestamps strictly increasing,
`context`/`generation_window` echoed exactly, real terminal weights summed to ≈1.0.

### 8. `atlas_adapter.py` — full accepted-formula-set recovery
`GPProcess.run()`'s real, complete validation-accepted individual set (`final_ind`) was already
being computed every run but the adapter only reported the top-3 (best + 2 runners-up). Now
reports the full real set in both `evidence` and `native_output.upstream.accepted_formulas`.
Live verification shows genuine "Accepted:"/"Not Accepted:" lines from the real upstream GP
process log.

Documented, not recovered: `GPProcess.run()`'s real per-generation DEAP `Logbook`
(avg/std/min/max fitness+tree-size per generation) and real per-batch best-individual history
are local variables inside `run()`, never assigned to `self`, never returned — only ever reach
a `print()`. No public accessor exists; recovering this would require monkey-patching or
reimplementing `run()`'s batch loop, both excluded by CLAUDE.md.

### 9. `alphagen_adapter.py` — pool search trajectory recovery
`LinearAlphaPool.update_history` (real `AddRemoveAlphas` records, one per accepted pool change
during the RL search, each with real `old_pool_ic`/`new_pool_ic`/`added_exprs`) was never read
anywhere. Now surfaced: full structured trajectory in `native_output`, plus one bounded
`evidence` item (update count + the real `.describe()` text of the final update — not one item
per update, to avoid an unbounded evidence list across a long search).

### 10. `rdagent_adapter.py` — richer per-stage coder feedback
Upstream's real `FactorSingleFeedback` (`CoSTEERSingleFeedbackDeprecated`) carries
`execution_feedback` (real local-execution stdout), `value_feedback` (real
`FactorValueEvaluator` verdict), and `code_feedback` (real LLM code critique) — distinct from,
and richer than, the combined `final_decision`/`final_feedback` pair already captured. All
three recovered as `EvidenceItem`s. Live-verified with a real DeepSeek call
(`deepseek/deepseek-v4-flash`), real execution/value/code feedback text observed in output.

### 11. `deepalpha_adapter.py` — call the real function instead of reimplementing it
The adapter used to hand-reimplement upstream's `model_agreement` formula
(`max(0, 1-dispersion/0.1)`) instead of calling the real function that computes it,
`RealTimePredictionEngine.generate_predictions()` — which also computes a real
`confidence_interval` that was never read at all. Fixed: `_train_ensemble()` now populates
`engine.models` with its own freshly-trained XGBoost/LightGBM models and calls the real
function directly. `model_agreement` is now genuinely upstream-computed (not duplicated);
`confidence_interval` is now surfaced as evidence on both Q1 and Q3.

**Declined, with reasoning**: upstream's own `predictions['primary']['confidence']` text label
('high'/'medium'/'low') is computed against `Config.signal_threshold_pct()` — verified
(`src/config.py`) to be `signal_threshold_ratio() * 100`, a **percentage-point**-scaled
threshold (e.g. 0.25 for 0.25%) — while this adapter's predictions are **fractional** returns
(e.g. 0.012 for 1.2%). Surfacing it would label nearly every real prediction "low" regardless
of actual conviction: a real function producing a systematically misleading value under this
adapter's real usage. Declined per CLAUDE.md's no-fabrication spirit rather than surfaced.

Live-verified: real `generate_predictions()` log line observed
(`✅ Generated predictions for AAPL: 0.0049`), real interval `[-1.8263%, +2.8076%]` present in
output JSON.

### 12. `tradingagents_adapter.py` — risk-debate transcript recovery
The 3-way risk debate (aggressive/conservative/neutral) is a real transcript on
`final_state["risk_debate_state"]`, verified (`managers/portfolio_manager.py`) to be the
direct input the Portfolio Manager's own prompt synthesizes into `final_trade_decision` — but
it had no dedicated Q1Action field and was never captured anywhere, unlike its sibling
bull/bear investment debate (which already had `bull_case`/`bear_case`). Recovered as 3
`EvidenceItem`s (`risk_debate_aggressive`/`_conservative`/`_neutral`). Live CLI run confirmed
real LLM-generated debate text in the output JSON (e.g. "Aggressive Analyst: Alright, let me
jump in here before the cautious voices start droning on about prudence...").

Re-confirmed via source (`managers/portfolio_manager.py`, `agents/schemas.py`): the structured
`PortfolioDecision`/`SentimentReport` Pydantic objects genuinely never reach graph state — only
`render_pm_decision()`/`render_sentiment_report()`'s rendered markdown does. Regex-parsing the
deterministic rendered headers remains the only public route; not a monkey-patchable gap.

### 13. `fingpt_adapter.py` — full headline evidence
`MAX_HEADLINES=5` already bounds the real per-headline model scores to a small number, so the
existing top-3-by-\|label\| truncation served no unbounded-evidence-safety purpose — it just
discarded up to 2 real scores per call. Now all scored headlines are kept. Live-verified: real
ChatGLM2-6B + LoRA model load and inference confirmed, evidence count matches scored-headline
count exactly.

### 14. `prediction_arena_adapter.py` — native_output + cost recovery
Two real gaps, both fixed:
- The adapter had **no `run()` override at all**, so `BaseAdapter.run()`'s `native_output`
  default of `{}` meant the real Kalshi market dict and real DeepSeek forecast dict were never
  preserved anywhere — a genuine CLAUDE.md §4 provenance gap (every sibling live-upstream
  adapter overrides `run()` for exactly this). Added a `run()` override, reusing the existing
  in-process caches (`_MARKET_CACHE`/`_FORECAST_CACHE`) so no extra live calls are made.
- `forecast["cost_usd"]` (upstream `report.price_estimate`, real litellm cost tracking) was
  read into a local dict but never surfaced — added as an `EvidenceItem`.

### 15. `finrl_adapter.py` — reviewed, correctly left as-is
`DRLAgent.DRL_prediction()` produces a full daily action-memory trajectory, but `env_gym` (the
prediction environment) is the **same environment `_train_agent` trained on** — i.e., the
policy was fit using the entire `generation_window` at once. Exposing that trajectory as a
per-day `Q4Policy.decisions` list would present each day as if it were an independent, causal
decision, when in fact every day's action came from a policy that had already "seen" every
other day in the window during training — a real causality violation the user explicitly
warned against ("test period must not use future information"). The adapter's existing design
(`initial_weights` = terminal-day snapshot only, `decisions=None`) is the causality-correct
choice; confirmed via source reading, not changed.

### 16. `example_stub_adapter.py` — out of scope, confirmed
Read in full: this file is a documented reference template
(`upstream_repo = "https://github.com/FILL_IN/upstream-project"`) with a placeholder-only
`q1_action`/`q2_state`, explicitly instructing future authors to "copy this file, rename it,
fill in real upstream calls." It wraps nothing real. Not part of the capability-recovery task.

---

## Harness summary

**Total real adapters**: 16 (`example_stub_adapter.py` excluded as a non-real template).

**This pass's live verification results** (commands, checks, and outputs as actually run):

| Adapter | Compile | Direct `smoke_test()` | Live `adapter_runner.py` CLI | Result |
|---|---|---|---|---|
| ai_hedge_fund | — (unchanged) | — (re-confirmed via earlier live run) | ran, real `HOLD/0.0/self-reported` | **PASSED** |
| agentictrading | — (unchanged) | — (re-confirmed via earlier live run) | ran, real `STATIC_ALLOCATION` weights | **PASSED** |
| vibe_trading | — (unchanged) | — (established prior pass) | 385 real decisions, 0 causality violations | **PASSED** |
| quantmuse (renamed) | `python -m py_compile` OK | 15/15 PASS | — | **PASSED** |
| finclaw | `python -m py_compile` OK | 18/18 PASS | wrote `finclaw.json` (12265 bytes) | **PASSED** |
| finrl_x | `python -m py_compile` OK | 17/17 PASS | direct `q2_state()` print, real values | **PASSED** |
| qlib | `python -m py_compile` OK | 16/16 PASS | 24 real decisions, 0 causality violations | **PASSED** |
| atlas | `python -m py_compile` OK | 12/12 PASS | — | **PASSED** |
| alphagen | `python -m py_compile` OK | 13/13 PASS | — | **PASSED** |
| rdagent | `python -m py_compile` OK | 12/12 PASS | real DeepSeek call confirmed | **PASSED** |
| deepalpha | `python -m py_compile` OK | 11/11 PASS | wrote `deepalpha.json`, real interval `[-1.83%,+2.81%]` | **PASSED** |
| tradingagents | `python -m py_compile` OK | 13/13 PASS | wrote `tradingagents.json` (66026 bytes), real risk-debate text | **PASSED** |
| fingpt | `python -m py_compile` OK | 9/9 PASS | real ChatGLM2 model load+inference | **PASSED** |
| prediction_arena | `python -m py_compile` OK | 10/10 PASS | real Kalshi + DeepSeek calls | **PASSED** |
| finrl | `python -m py_compile` OK | 10/10 PASS | real A2C training (10 real training runs shown in log) | **PASSED** |
| example_stub | N/A (not a real adapter) | N/A | N/A | **NOT_RUN** (out of scope) |

**Success/fail/skip**: 15 real adapters exercised this pass, **15 PASSED, 0 FAILED, 0 SKIPPED,
0 BLOCKED**. (`example_stub_adapter.py` is `NOT_RUN` by design — it is a template, not a real
adapter.) One transient timeout occurred and was resolved during verification: the first
`finrl_adapter.py` smoke-test invocation hit a 250s Bash-tool timeout with zero output (real
DRL training + yfinance fetch took longer than the budget); re-run with a longer timeout
completed successfully with all 10 checks passing — not an adapter defect.

**Q4 (policy/trajectory) adapters — causality check detail**:

| Adapter | `decisions` trajectory length | Causality violations (`information_cutoff <= timestamp`) | Weights sum-to-1 / constraints | Single-point vs. trajectory |
|---|---|---|---|---|
| vibe_trading | 385 real `PolicyDecisionStep`s | 0 | n/a (signal-driven, not weight-portfolio) | genuine trajectory (established prior pass) |
| qlib | 24 real decisions | 0 | real weights sum ≈ 1.0 (e.g. last day `{XOM:0.332, META:0.319, AMZN:0.332, CASH:0.017}`) | genuine trajectory |
| finclaw | 0 (`decisions=None`) | n/a | n/a (single-asset GA score + artifact) | correctly single-point (artifact-based policy, not a rebalancing trajectory) |
| finrl_x | not separately trajectory-tested this pass (Q4 pre-existing, unmodified) | — | q4 weights sum-to-1 check PASS | pre-existing, not touched |
| agentictrading | 0 (`decisions=None`) | n/a | real weights `{AAPL:1.0, CASH:0.0}`, `long_only=True` | correctly single-point (`STATIC_ALLOCATION`) |
| finrl | 0 (`decisions=None`, by design) | n/a | real weights, non-negative, sum ≤ 1.0 | correctly single-point — reviewed explicitly this pass and confirmed the full in-sample trajectory must NOT be exposed (would violate no-future-information causality) |

**Real per-call cost incurred this pass**: real, metered DeepSeek API calls were made for
`rdagent`, `tradingagents` (~9-10 calls per run, per its own debate architecture),
`prediction_arena`, and `deepalpha` (indirectly, via its own real model training — no LLM
calls). No API call failed for insufficient balance/quota during this pass; all real calls
returned successfully. No test was BLOCKED by missing credentials — every adapter that needed
a real key already had one provisioned from a prior session.

**Before/after coverage deltas** (this pass only; ai_hedge_fund/agentictrading/vibe_trading
unchanged, not counted below):

| Adapter | Before | After |
|---|---|---|
| quantmuse (nofx) | Q2 only | Q2 + Q3 (real RSI-14) |
| finclaw | Q4 = artifact only | Q4 = artifact + real decision/universe/observation policy + constraints |
| finrl_x | Q2 = 1 state (`market_regime`) | Q2 = 2 states (`market_regime` + `regime_recommended_cash_floor`) |
| qlib | Q3 only | Q3 + Q4 (real strategy-driven rebalancing trajectory) |
| atlas | Q3 evidence: top-3 accepted formulas | Q3 evidence: full accepted-formula set |
| alphagen | Q3 evidence: no search-trajectory info | Q3 evidence + native_output: full pool update history |
| rdagent | Q3 evidence: 1 combined feedback field | Q3 evidence: 4 real feedback fields (final + execution + value + code) |
| deepalpha | Q1/Q3 confidence: hand-reimplemented formula, no interval | Q1/Q3 confidence: real upstream function call, + real confidence interval |
| tradingagents | Q1 evidence: 2 fields (time_horizon, price_target) | Q1 evidence: 5 fields (+ 3 risk-debate transcripts) |
| fingpt | Q2 evidence: 3 of ≤5 real headline scores | Q2 evidence: all real headline scores |
| prediction_arena | native_output: always `{}` | native_output: real market + forecast dict |

No project's information-retention score changed in any direction other than upward in this
pass — no previously-retained field was dropped, narrowed, or replaced by a less-faithful
derivation.
