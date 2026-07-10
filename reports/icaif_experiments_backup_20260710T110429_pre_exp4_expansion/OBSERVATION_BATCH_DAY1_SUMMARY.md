# Observation Batch Day 1 — Summary

Decision date (latest available current snapshot): **2026-07-06**  
Data cutoff: prices/news as fetched at run time on 2026-07-06T16:07:41  
Total wall-clock: **3.47 hours**  
Historical extension attempted: **True**

## Job totals

**Corrected 2026-07-06: the auto-generated version of this section only counted
the main batch's index.csv (157 jobs) and omitted the historical extension's
separate index.csv (135 more jobs) — both ran and both are real, checkpointed
data; only this markdown's tallying was incomplete. Numbers below are the
main batch + historical extension combined.**

- Total attempted (main + historical extension): **292** (157 main + 135 historical)
- Succeeded: **249**
- Failed (non-timeout): **0**
- Timed out: **43**
- Schema-invalid successes: **0**
- Normalized JSONs on disk (index rows with a path): **249**

## Per-adapter results (main + historical extension combined)

| adapter | attempted | succeeded | failed | timed_out | batch(es) |
|---|---|---|---|---|---|
| agentictrading | 1 | 1 | 0 | 0 | main |
| ai_hedge_fund | 10 | 10 | 0 | 0 | main |
| alphagen | 35 | 10 | 0 | 25 | main+historical |
| atlas | 35 | 17 | 0 | 18 | main+historical |
| deepalpha | 70 | 70 | 0 | 0 | main+historical |
| finclaw | 10 | 10 | 0 | 0 | main |
| fingpt | 10 | 10 | 0 | 0 | main |
| finrl | 12 | 12 | 0 | 0 | main+historical |
| finrl_x | 11 | 11 | 0 | 0 | main |
| nofx | 10 | 10 | 0 | 0 | main |
| prediction_arena | 11 | 11 | 0 | 0 | main |
| qlib | 35 | 35 | 0 | 0 | main+historical |
| rdagent | 10 | 10 | 0 | 0 | main |
| tradingagents | 20 | 20 | 0 | 0 | main |
| vibe_trading | 12 | 12 | 0 | 0 | main |

Note: alphagen (25/35 timed out) and atlas (18/35 timed out) are GA/RL-based
adapters whose per-run convergence time varies — the 120s non-LLM timeout
was tight for some historical dates. Every timeout is resumable (rerun the
same command; index.csv-based caching skips everything already done).

## Per-Q observed coverage (adapters with >=1 observed result): before vs after

| Q | before | after |
|---|---|---|
| Q1 | 2 | 3 |
| Q2 | 1 | 4 |
| Q3 | 1 | 8 |
| Q4 | 0 | 3 |
| Q5 | 0 | 4 |

## Slowest 10 jobs

| adapter | q_type | ticker/universe | runtime_s | success |
|---|---|---|---|---|
| tradingagents | Q2 | MSFT | 355.98 | True |
| tradingagents | Q1 | XOM | 316.17 | True |
| tradingagents | Q1 | QQQ | 287.76 | True |
| tradingagents | Q2 | AAPL | 283.93 | True |
| tradingagents | Q2 | NVDA | 280.6 | True |
| tradingagents | Q2 | QQQ | 279.48 | True |
| tradingagents | Q1 | TSLA | 271.2 | True |
| tradingagents | Q1 | JPM | 270.8 | True |
| tradingagents | Q1 | SPY | 266.64 | True |
| tradingagents | Q2 | SPY | 266.43 | True |

## API/LLM failures

- none

## Downstream ICAIF experiment status

**Corrected 2026-07-06 16:14: the first post-batch rerun of `analysis.icaif_experiments`
crashed partway through Experiment 4 (contradiction detection) on a real bug —
`rule_long_with_weak_validation`'s (and two sibling rules') detail-string
lambdas assumed a bare `ticker` column would survive a `task_id`-only merge,
which held by coincidence in every prior run (Q3+Q5 real data never
co-existed before), and broke the instant real data made both sides
non-empty. This silently left Experiment 4's outputs stale (from an earlier
manual test run) and meant Experiment 5, the case studies, and
PAPER_FINDINGS.md never regenerated in that run at all — the "0 contradictions
fired" / "5 fusion groups" numbers first written here were wrong. Fixed the
three affected rules (`analysis/icaif_contradictions.py`), added two
regression tests that specifically exercise the collision, reran the full
unit test suite (25/25 pass), then reran `analysis.icaif_experiments`
cleanly. Numbers below are from that clean rerun.**

- ICAIF experiments now have more observed results: **True** (sum of per-Q adapter-coverage counts: before=4, after=22 — Q1=3, Q2=4, Q3=8, Q4=3, Q5=4)
- Contradiction rules fired: **True** — **129 total cases** across all 5 exact/best-effort rules:
  ACTION_ALPHA_DIRECTION_CONFLICT=27, BUY_WITH_HIGH_RISK=15, HIGH_CONFIDENCE_POOR_CALIBRATION=39,
  HIGH_WEIGHT_HIGH_DRAWDOWN=5, LONG_WITH_WEAK_VALIDATION=43 (see contradiction_summary.csv / contradiction_cases.csv)
- Calibration sample counts by horizon (trading days): 1d=109, 5d=94, 20d=75
- Fusion ablation can compute return-based metrics: **True**, across **40** (ticker, date) groups
  (not 5 — that was the stale pre-fix number). majority_vote hit_rate=0.61, confidence_weighted/interwoven
  hit_rate=0.57 each; decision_stability_vs_other_methods: majority=0.60, confidence_weighted=0.75, interwoven=0.70
  (see fusion_ablation_results.csv, fusion_decisions.csv)
- Contradiction outcome comparison currently shows **278 flagged samples, 0 unflagged** — with 129 cases
  spanning 5 rule types hitting most adapters, nearly every calibration-eligible record ends up flagged by
  at least one rule in this batch, so the flagged-vs-unflagged forward-return comparison has no unflagged
  baseline yet to contrast against (see contradiction_outcome_comparison.csv). Worth revisiting with tighter
  rule thresholds in a future batch if a real contrast is wanted.

### calibration_README.md (verbatim)
```
# Calibration data availability

Total (adapter, question, ticker, date, horizon) rows attempted: 621
Rows with a realized future return: 278

## Per-horizon availability
- horizon=1: 109/207 rows have a realized future return
- horizon=5: 94/207 rows have a realized future return
- horizon=20: 75/207 rows have a realized future return

Decision dates present in results/: ['2026-05-15', '2026-05-21', '2026-05-27', '2026-06-02', '2026-06-08', '2026-07-02', '2026-07-06']
A horizon's rows stay `future_return=NaN` (marked insufficient_data downstream, never fabricated) until that many trading days have actually elapsed after the decision date — see analysis/icaif_data_loader.py:YFinanceFutureReturnProvider.
```

## Remaining insufficient_data sections
- Any horizon not listed above under calibration sample counts is still insufficient_data — see calibration_README.md for exactly which trading days have and haven't elapsed.
- Q4/Q5 contradiction rules (2, 3, 5) remain best-effort task_id/date joins per CONTRACT/schemas.py's lack of a ticker/date field on Q4Portfolio/Q5Backtest — unchanged by this batch.

## Known data-quality caveats from this batch
- `atlas` Q3: bundled dataset is crypto-perpetuals only; every equity/ETF ticker requested falls back to the same BTCUSDT-derived signal (self-disclosed in its own supporting_evidence). Treat atlas's 10 "different" ticker observations as 1 real observation repeated under 10 labels.
- No profitability claim is made anywhere in this batch or its outputs — total_return/sharpe/hit_rate figures are descriptive of this specific sample, not a claim that any strategy is profitable.

## Recommended next batch
- Prioritize widening Q1/Q2 coverage (currently the thinnest — 3-4 adapters vs. 8 for Q3).
- If 5d/20d calibration is still insufficient_data here, the single highest-value next action is simply waiting real calendar time and rerunning `analysis.icaif_experiments` against the same results/ — no new adapter runs needed for that specific gap.
- Consider a second historical extension batch (different date range) once more calendar time has passed, to grow the calibration sample size for Q3 in particular (currently the highest-coverage question).
