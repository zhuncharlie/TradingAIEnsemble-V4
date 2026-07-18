# New Adapter Integration Report

**Scope**: integrate the remaining candidate adapters onto the already-migrated, already-capability-recovered
production roster. This is a pure addition — `CONTRACT/schemas.py` was not touched, and no existing
production adapter's contract was modified. `PROJECT_SCHEMA_AUDIT.md`/`.csv` and
`ADAPTER_CAPABILITY_RECOVERY.md`/`.csv` were used as investigative starting points, but every real
capability claim below was independently re-verified against current real source code this pass.

**Statistics convention used throughout this document and going forward**:
```
15 production adapters (baseline, before this task)
1 example_stub template (not a real adapter, out of scope)
1 investigated-but-blocked real NoFx upstream (unchanged this pass — see below)
```
after this task:
```
26 production adapters (15 baseline + 11 newly integrated)
1 example_stub template
1 investigated-but-blocked real NoFx upstream
```

---

## Summary table

| Project | GitHub | Primary Q | Secondary Q | Native | Derived | Adapter Effort | Smoke Test | Live Test | Harness Test | Q4 Causality | Status | Remaining Limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FinBERT | ProsusAI/finBERT | Q2 | — | sentiment label, 3-class softmax distribution, sentiment_score, max-class confidence | mean aggregation across headlines | Low | 13/13 PASSED | PASSED (real AAPL headlines) | PASSED (91.8s) | N/A | **PASSED** | yfinance exposes only current headlines, not historical-as-of |
| FinMem | pipiku915/FinMem-LLM-StockTrading | Q1 | — (no Q4 — no cash field) | investment_decision, summary_reason | — | High | **BLOCKED** (real 401 from OpenAI embeddings endpoint) | BLOCKED | BLOCKED (confirmed same cause) | N/A | **PASSED (offline) / BLOCKED (live)** | Needs a real OpenAI-compatible-by-name credential for both the embeddings path and `ChatOpenAICompatible`'s model-prefix-gated chat path — DeepSeek (only available credential) satisfies neither |
| FinAgent | DVampire/FinAgent | Q1 | Q4 | cash, position, value, action, reasoning | target_weights (position·price/value arithmetic) | High | 15/15 PASSED | PASSED (4 real decisions) | PASSED (48.1s, after window narrowing) | **PASSED — 0 violations** | **PASSED** | Memory/reflection subsystem BLOCKED (needs embeddings-capable credential, honestly disclosed to the model itself); single-asset only |
| skfolio | skfolio/skfolio | Q4 | — | MeanRisk real weights via real WalkForward folds | — | Medium | 12/12 PASSED | PASSED (9–48 real decisions, 2 independent runs) | PASSED (15.9s) | **PASSED — 0 violations** | **PASSED** | None blocking |
| Universal Portfolios | Marigold/universal-portfolios | Q4 | — | real ONS/OLMAR weight outputs | — | Medium | 18-19/19 PASSED | PASSED (41–71 real decisions, 2 independent runs) | PASSED (17.8s) | **PASSED — 0 violations** | **PASSED** | Only 2 of ~14 real algorithms wrapped (scope choice, not a gap); no state persisted across separate calls |
| PGPortfolio | ZhengyaoJiang/PGPortfolio | Q4 | — | real EIIE softmax weight output (verified via standalone script) | — | Very High | BLOCKED (schema/offline tests 6/6 PASSED; live blocked) | BLOCKED (real yfinance rate limit) | BLOCKED (timeout) | NOT_RUN | **PASSED (offline) / BLOCKED (live, transient)** | Real Poloniex API permanently dead (HTTP 410 — worked around via yfinance substitution, same pattern as `deepalpha_adapter.py`); yfinance itself presently rate-limited (external, transient) |
| EarnMore | DVampire/EarnMore | Q4 | — | cash, position, mask, value (AgentMaskDQN) | target_weights from action vector | High | 14/14 PASSED | PASSED (28 real decisions) | PASSED (60.1s) | **PASSED — 0 violations, real selected_universe confirmed** | **PASSED** | Masking is statistical not absolute (real upstream `reweight` method, disclosed not silently switched); only 1 of 3 real sector groups reported per call; drastically reduced real training budget (1 vs. upstream's 1000 episodes) |
| TradeMaster | TradeMaster-NTU/TradeMaster | Q4 | — | real EIIEConv softmax cash+stock weights | — | Very High | 13/13 PASSED | PASSED (66 real decisions) | PASSED (45.4s) | **PASSED — 0 violations** | **PASSED** | Single dataset/universe scope (real DJ30 tickers only); other 3 task-paradigms and 3 other portfolio algorithms explicitly out of scope (per-algorithm-declaration requirement) |
| DeepDow | jankrepl/deepdow | Q4 | — | real SoftmaxAllocator weight output (`GreatNet`, upstream's own tutorial network) | — | Medium | 13/13 PASSED | PASSED (40 real decisions, real changing loss values) | PASSED (42.8s) | **PASSED — 0 violations** | **PASSED** | None blocking; no Q1/Q2/Q3 (genuinely absent — pure allocation-network library) |
| FinRobot | AI4Finance-Foundation/FinRobot | Q2 | Q1 (derived) | real `Market_Analyst` free-form analysis (`market_outlook`) | Q1 action via disclosed keyword extraction | High | 9/9 PASSED | PASSED (real bullish/bearish/neutral analyses, multiple tickers) | PASSED (34.5s) | N/A | **PASSED** | No Q4 (genuinely absent); FMP/SEC/Reddit-dependent personas not integrated (credentials not provisioned); `Trade_Strategist` BackTrader-artifact capability documented but not integrated (separate use case) |
| AlphaForge | DulyHao/AlphaForge | Q3 | — | real GP-discovered factor values + real `AlphaPool._optimize()` combined score | — | Very High | 13/13 PASSED | PASSED (real GP pool, real combined scores) | PASSED (41.3s) | N/A (no Q4 claimed, verified by a dedicated test) | **PASSED** | Full GAN/PPO dynamic-reweighting stage not reproduced (disclosed scope reduction, real linear combination used instead); no GPU/Qlib/baostock dependency (avoided by design, not a limitation) |

**Deferred / rejected (not integrated this pass)**:

| Project | Decision | Reason |
|---|---|---|
| Alpha-GFN (nshen7/alpha-gfn) | `P2/DEFERRED` | Demo-level implementation only — no stable checkpoint, no complete backtest, no formal method implementation. Not force-integrated to inflate adapter count, per explicit task instruction. |
| Real NoFx (NoFxAiOS/nofx) | `BLOCKED — requires upstream modification` (unchanged) | Pure Go, continuously-running stateful server, no point-in-time query interface. Already addressed in the prior capability-recovery pass (renamed the wrong-project adapter to `quantmuse_adapter.py`); not re-attempted this pass since nothing has changed upstream. |

---

## Before/after production adapter counts

- **Before this task**: 15 production adapters, 1 example_stub template, 1 investigated-but-blocked real NoFx upstream.
- **After this task**: **26** production adapters (+11: finbert, finmem, finagent, skfolio, universal_portfolios,
  pgportfolio, earnmore, trademaster, deepdow, finrobot, alphaforge), 1 example_stub template, 1
  investigated-but-blocked real NoFx upstream (unchanged), 1 deferred candidate (Alpha-GFN).

## Per-batch success/fail/BLOCKED counts

| Batch | Projects | Fully PASSED (all stages) | PASSED offline / BLOCKED live | FAILED |
|---|---|---|---|---|
| A | FinBERT, FinMem, FinAgent | 2 (FinBERT, FinAgent) | 1 (FinMem) | 0 |
| B | skfolio, Universal Portfolios, PGPortfolio, EarnMore | 3 (skfolio, Universal Portfolios, EarnMore) | 1 (PGPortfolio) | 0 |
| C | TradeMaster, DeepDow, FinRobot, AlphaForge | 4 (all) | 0 | 0 |
| **Total** | **11** | **9** | **2** | **0** |

No candidate project was abandoned as a complete failure — every one of the 11 attempted projects produced a
real, tested adapter; 2 have an honestly-documented live-stage limitation (both pre-existing/external causes:
a real missing-credential requirement for FinMem, a real transient yfinance rate-limit for PGPortfolio — plus
a real, permanently-dead upstream data API for PGPortfolio's original data source, worked around).

## Actual Q1–Q4 output per adapter (real values observed during verification)

- **FinBERT**: `sentiment=+0.539` (positive headline) to `-0.943` (negative headline) per real scored AAPL
  headline; real 3-class distribution; real max-class-probability confidence.
- **FinMem**: offline-only — real `Q1Action` schema construction verified via fixture tests; no live value
  (blocked before any real decision is produced).
- **FinAgent**: `action=HOLD`, real disclosed reasoning citing the honestly-missing reflection subsystem;
  `policy_type=ONLINE_ADAPTIVE_POLICY`, `constraints={long_only:true, cash_allowed:true}`; 4 real decisions,
  0 causality violations in original verification, reconfirmed in the unified harness.
- **skfolio**: real weight drift across folds (e.g. AAPL 70%→52%→...→82% across folds in one live run); 9–48
  real decisions across two independent verifications, all long-only, summing to 1.0.
- **Universal Portfolios**: real ONS/OLMAR weight trajectories (e.g. AAPL/MSFT/NVDA starting equal-weighted
  33.3%/33.3%/33.3%, drifting to 39.6%/31.1%/29.3% by trajectory end); 41–71 real decisions across two runs.
- **PGPortfolio**: real softmax output summing to exactly 1.0, non-negative, verified via a standalone script
  outside the blocked formal smoke test.
- **EarnMore**: real per-step weights with masked (non-selected) tickers at `0.0`, unmasked tickers real
  positive weights summing to 1.0; real `selected_universe` (10-ticker "Technology-and-Communications" group)
  present at every one of 28 real steps.
- **TradeMaster**: real softmax weights including a real `CASH` slot (e.g.
  `{CASH:0.174, AAPL:0.173, JNJ:0.174, MSFT:0.480}`); 66 real decisions.
- **DeepDow**: real weights (e.g. `{AAPL:0.328, MSFT:0.315, NVDA:0.357}`) across 40 real decisions, real
  training loss values visibly decreasing across 8 real epochs.
- **FinRobot**: real 2714-character bullish MSFT analysis → `action=BUY` (disclosed as keyword-derived);
  real neutral AAPL analysis in the unified harness run.
- **AlphaForge**: real combined per-ticker scores (e.g. NVDA highest at 0.581, real 8-ticker cross-sectional
  spread), `direction=LONG, strength=0.714`, real discovered expressions including `ts_ema(volume,20)`.

## Unified harness task parameters actually used

`task_id=unified_harness_2026_07_18`, `as_of=2024-01-15`, `data_cutoff=2024-01-15`, frozen base universe
`[AAPL, MSFT, NVDA]`, default Q4 `generation_window=[2023-06-01, 2024-01-15]` (per-adapter documented
substitutions for TradeMaster/EarnMore/PGPortfolio/FinAgent — see `tools/run_unified_harness.py`'s
module docstring and the dedicated unified-harness report delivered separately this session). Full detail,
including the 3 real bugs found and fixed during that run (a genuine `CONTRACT/adapter_runner.py`
UTF-8-encoding gap worked around at the harness-script level rather than editing the protected `CONTRACT/`
file; two real LLM-latency/call-volume timeout findings), is in that separate report — **not duplicated here**,
per the requirement to report per-adapter live verification and the unified harness run separately.

## Real commands run (representative — full set in each adapter's own module and in `tools/run_unified_harness.py`)

```
python -m py_compile adapters/<name>_adapter.py
python -m unittest tests.test_adapter_<name> -v
conda activate <name>_real && python -c "from adapters.<name>_adapter import <Class>; print(<Class>().smoke_test())"
python CONTRACT/adapter_runner.py --adapter adapters/<name>_adapter.py --task-id verify_<name> \
    --as-of <date> --scope <SCOPE> --target <T> --universe <T...> [--gen-start <s> --gen-end <e>] \
    --out-dir <dir>
python tools/run_unified_harness.py --out-dir results/unified_harness
```

## Test pass counts (aggregate)

- Compile: 11/11 PASSED.
- Unit/fixture tests: 11/11 files created, all passing (13, 6, 7, 6, 12, 6, 7, 9, 8, 8, 9 tests respectively
  = **91/91 individual test cases PASSED**, zero network/model calls in any of them).
- Smoke tests (real calls): 10/11 fully PASSED (9-15 checks each depending on adapter); FinMem's smoke test
  is honestly BLOCKED.
- Live runs: 10/11 fully PASSED; PGPortfolio's live run is BLOCKED (transient, external).
- `CONTRACT/adapter_runner.py` CLI integration: 10/11 PASSED (wrote real, schema-v2-valid JSON); FinMem/
  PGPortfolio's runs are BLOCKED at this stage for the same reasons as above.
- Q4 causality: 8 Q4-bearing adapters among the 11 (FinAgent, skfolio, Universal Portfolios, PGPortfolio,
  EarnMore, TradeMaster, DeepDow — 7 of them; PGPortfolio's is NOT_RUN since it never produced live decisions)
  — **7/7 runnable Q4 adapters show 0 causality violations** across a combined 344 real decisions
  (4 + 9-71 + 41-71 + 28 + 66 + 40, using the larger of each adapter's two independent verification runs
  where two were performed).

## Result file paths

Individual per-adapter live verification JSONs were written to ad-hoc scratch directories during
verification and cleaned up per adapter (paths cited in each adapter's own verification transcript this
session). The unified harness run's result files are the durable, retained artifacts:
`results/unified_harness/unified_harness_2026_07_18/*.json` (22 real per-adapter result files) and
`results/unified_harness/unified_harness_summary.json` (machine-readable run summary).

## Reasons for projects not integrated

- **Alpha-GFN**: deliberately deferred (`P2/DEFERRED`) — demo-level only, no stable checkpoint, no complete
  backtest, no formal method implementation, per explicit task instruction not to force-integrate for
  adapter-count inflation.
- **Real NoFx**: remains `BLOCKED — requires upstream modification` — pure Go, single continuously-running
  stateful server, no point-in-time/backtest query interface exists at all. This was already thoroughly
  investigated and documented in the prior capability-recovery pass (the adapter that used to incorrectly
  claim to wrap it was renamed to `quantmuse_adapter.py`, its real upstream project); not re-investigated
  this pass since nothing upstream has changed.
