# Adapter Runnability Audit

Probe date ("latest available decision date"): **2026-07-06**  
Backtest window for Q5 probes: **2026-06-06 -> 2026-07-06**  
Per-probe timeout: **300s**  
Ticker-level probe ticker: **NVDA** | Portfolio universe: **['NVDA', 'SPY', 'QQQ', 'CASH']**

This is a runnability audit only — it did not write anything to `results/` and 
did not run the full observation batch. No brokerage/exchange account was touched 
and no order was ever placed by any probe (every adapter's q*_ methods here are 
read-only signal/analysis calls, same as the existing test harness).

## Summary: 22 probes attempted across 15 adapters
- can_run: **22**
- cannot_run: **0**
- skipped (no implemented q*_ methods): **0**

## Per-adapter detail

### agentictrading
- requires_api_key: **True** (ALPACA_API_KEY,ANTHROPIC_API_KEY,COMMONSTACK_API_KEY,DEEPSEEK_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q5 | ✓ | backtest-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], start=2026-06-06, end=2026-07-06 | adapter,alpha_vs_benchmark,benchmark,calmar,cost_usd,equity_curve,latency_sec,max_drawdown,sharpe,test_period,total_return | 10.61 | - |

### ai_hedge_fund
- requires_api_key: **True** (DEEPSEEK_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q1 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | action,adapter,confidence,cost_usd,date,latency_sec,reasoning,ticker,time_horizon | 13.21 | - |

### alphagen
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 99.08 | - |

### atlas
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 26.06 | - |

### deepalpha
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q1 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | action,adapter,confidence,cost_usd,date,latency_sec,reasoning,ticker,time_horizon | 12.01 | - |
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 11.88 | - |

### finclaw
- requires_api_key: **True** (OPENAI_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 90.42 | - |

### fingpt
- requires_api_key: **True** (HF_TOKEN)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): unknown (static heuristic inconclusive)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q2 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,drivers,latency_sec,risk_level,sentiment_score,sources,ticker | 79.54 | - |

### finrl
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q4 | ✓ | portfolio-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], date=2026-07-06 | adapter,cash_ratio,cost_usd,date,latency_sec,rationale,rebalance_freq,regime,weights | 57.26 | - |
| Q5 | ✓ | backtest-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], start=2026-06-06, end=2026-07-06 | adapter,alpha_vs_benchmark,benchmark,calmar,cost_usd,equity_curve,latency_sec,max_drawdown,sharpe,test_period,total_return,train_period,win_rate | 55.35 | - |

### finrl_x
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): false (static heuristic: docstring/code suggests current-snapshot-only)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 61.21 | - |
| Q4 | ✓ | portfolio-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], date=2026-07-06 | adapter,cash_ratio,cost_usd,date,latency_sec,rationale,rebalance_freq,regime,weights | 116.43 | - |

### nofx
- requires_api_key: **True** (DEEPSEEK_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q2 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,drivers,latency_sec,risk_level,sentiment_score,sources,ticker | 30.96 | - |

### prediction_arena
- requires_api_key: **True** (DEEPSEEK_API_KEY,METACULUS_TOKEN)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): false (static heuristic: docstring/code suggests current-snapshot-only)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q2 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,drivers,latency_sec,risk_level,sentiment_score,sources,ticker | 25.64 | - |
| Q5 | ✓ | backtest-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], start=2026-06-06, end=2026-07-06 | adapter,benchmark,cost_usd,equity_curve,latency_sec,max_drawdown,sharpe,test_period,total_return,win_rate | 13.2 | - |

### qlib
- requires_api_key: **False**
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,expected_return,latency_sec,signal_type,strength,supporting_evidence,ticker | 19.1 | - |

### rdagent
- requires_api_key: **True** (DEEPSEEK_API_KEY,OPENAI_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,latency_sec,signal_type,strength,supporting_evidence,ticker | 56.18 | - |

### tradingagents
- requires_api_key: **True** (DEEPSEEK_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): unknown (static heuristic inconclusive)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q1 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | action,adapter,bear_case,bull_case,confidence,cost_usd,date,latency_sec,reasoning,ticker,time_horizon | 290.18 | - |
| Q2 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,drivers,latency_sec,risk_level,sentiment_score,sources,ticker | 274.9 | - |

### vibe_trading
- requires_api_key: **True** (DEEPSEEK_API_KEY)
- requires_broker_credentials: **False**
- supports_historical_date (static heuristic, not empirically tested): likely true (static heuristic: date/window-driven data fetch found)

| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |
|---|---|---|---|---|---|---|
| Q3 | ✓ | ticker-level | ticker=NVDA, date=2026-07-06 | adapter,cost_usd,date,direction,expected_horizon,latency_sec,signal_type,strength,supporting_evidence,ticker | 29.96 | - |
| Q4 | ✓ | portfolio-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], date=2026-07-06 | adapter,cash_ratio,cost_usd,date,latency_sec,rationale,rebalance_freq,weights | 14.68 | - |
| Q5 | ✓ | backtest-level | tickers=['NVDA', 'SPY', 'QQQ', 'CASH'], start=2026-06-06, end=2026-07-06 | adapter,alpha_vs_benchmark,benchmark,calmar,cost_usd,equity_curve,latency_sec,max_drawdown,sharpe,test_period,total_return,win_rate | 14.16 | - |

## Methodology notes / limitations

- `requires_api_key` / `requires_broker_credentials` / `supports_historical_date` are **static source-code heuristics** (regex over the adapter file), not independently verified per q_type — an adapter can need an LLM key for one question and not another (e.g. prediction_arena's Q2 calls a real LLM, its Q5 does not), and this table does not split that out.
- `supports_historical_date` was **not empirically tested** (would require a second probe per question at a second date, i.e. a mini historical backfill — explicitly out of scope for this lightweight audit per the brief). Treat it as a lead for the next phase, not a fact.
- Every probe called exactly one q*_ method directly (never `adapter.run()`), so Q4/Q5 were never probed with a single-ticker input and Q1-Q3 were never conflated with portfolio/backtest granularity.
- `can_run=True` means the method returned a non-null, schema-valid object for this specific probe input — it does not guarantee every ticker/date will succeed (e.g. yfinance coverage gaps for BTC-USD/SPY seen previously in `analysis/build_visualizations.py`).
