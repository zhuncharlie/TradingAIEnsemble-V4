# Experiment Q&A Notes — Calibration (Exp 3) & Contradictions (Exp 4)

Consolidates the follow-up analysis done in chat after the observation batch,
so these tables/findings aren't only sitting in conversation history. Every
number here traces back to a CSV already in this directory
(`calibration_table.csv`, `contradiction_cases.csv`, `contradiction_summary.csv`)
plus direct adapter source inspection (`adapters/*.py`).

## Where each self-reported confidence/strength value actually comes from

| Adapter | Field | Formula | What it actually measures |
|---|---|---|---|
| ai_hedge_fund | Q1 confidence | `raw["confidence"] / 100` | Upstream LLM's own stated 0-100 confidence, verbatim |
| tradingagents | Q1 confidence | Fixed lookup: `{buy:0.85, sell:0.85, overweight:0.65, underweight:0.65, hold:0.5}` | Not adapter-derived at all — a constant assigned by rating category |
| deepalpha | Q1 confidence | `1 - min(dispersion/0.1, 1)`, `dispersion = std(xgb_pred, lgb_pred)` | XGBoost/LightGBM inter-model agreement, NOT predictive accuracy |
| deepalpha | Q3 strength | `min(1, abs(prediction)/0.05)` | Magnitude of predicted return, not correctness |
| alphagen / atlas / qlib / finrl_x | Q3 strength | `abs(cross-sectional percentile - 0.5) * 2` (identical formula in all four) | How extreme the factor value ranks today vs. peers — not validated predictive power |
| finclaw | Q3 strength | `min(1, abs(score-5)/5)` on an internal 0-10 score | Distance from a neutral internal score |
| rdagent | Q3 strength | `min(1, abs(corr))`, corr = factor-vs-forward-return correlation computed once on the training window | A stale training-period fit statistic, applied uniformly regardless of the current query |
| vibe_trading | Q3 strength | `abs(final_signal)` | Composite internal signal magnitude |

## Full calibration table (adapter x question x horizon, weighted-aggregated)

| adapter | question | horizon | n | avg_confidence | actual_hit_rate | calibration_error |
|---|---|---|---|---|---|---|
| ai_hedge_fund | Q1 | 1 | 5 | 0.40 | 0.00 | 0.40 |
| deepalpha | Q1 | 1 | 30 | 0.97 | 0.53 | 0.43 |
| deepalpha | Q1 | 5 | 25 | 0.97 | 0.32 | **0.65** |
| deepalpha | Q1 | 20 | 20 | 0.97 | 0.60 | 0.37 |
| alphagen | Q3 | 1 | 9 | 0.62 | 0.33 | 0.29 |
| alphagen | Q3 | 5 | 9 | 0.62 | 0.33 | 0.29 |
| alphagen | Q3 | 20 | 7 | 0.63 | 0.00 | 0.63 |
| atlas | Q3 | 1 | 10 | 0.59 | 0.10 | 0.49 |
| atlas | Q3 | 5 | 10 | 0.59 | 0.30 | 0.29 |
| atlas | Q3 | 20 | 8 | 0.59 | 0.00 | 0.59 |
| deepalpha | Q3 | 1 | 30 | 0.27 | 0.53 | 0.45 |
| deepalpha | Q3 | 5 | 25 | 0.27 | 0.36 | 0.26 |
| deepalpha | Q3 | 20 | 20 | 0.27 | 0.60 | 0.55 |
| qlib | Q3 | 1 | 25 | 0.41 | 0.08 | 0.33 |
| qlib | Q3 | 5 | 25 | 0.41 | 0.20 | 0.21 |
| qlib | Q3 | 20 | 20 | 0.40 | 0.15 | 0.25 |
| finclaw / finrl_x / rdagent / tradingagents / vibe_trading | — | — | **0** | — | — | 100% dated 2026-07-06, 0 trading days elapsed yet |

## The 8 contradiction rules — provenance

**These 8 rules and their default thresholds were specified verbatim by the
user in the original ICAIF-experiment-layer task prompt — not derived from
any published taxonomy or academic reference, and not independently designed
by the assistant.** They are practitioner heuristics, implemented exactly as
specified in `analysis/icaif_contradictions.py`.

| # | Flag | Condition |
|---|---|---|
| 1 | BUY_WITH_HIGH_RISK | Q1 BUY + same (ticker,date) Q2 risk_level in {HIGH,EXTREME} |
| 2 | LONG_WITH_WEAK_VALIDATION | Q3 LONG + Q5 (same task_id) shows weak/fail validation |
| 3 | POSITIVE_SENTIMENT_BEAR_REGIME | Q2 sentiment>0 + Q4 (same date) regime=BEAR |
| 4 | HIGH_CONFIDENCE_POOR_CALIBRATION | Q1 confidence>=0.80 + adapter flagged overconfident in Exp 3 |
| 5 | HIGH_WEIGHT_HIGH_DRAWDOWN | Q4 weight>=0.10 on a ticker + Q5 (same task_id) max_drawdown<=-0.20 |
| 6 | STRONG_SIGNAL_MISSING_EVIDENCE | Q3 strength>=0.80 + supporting_evidence empty |
| 7/8 | ACTION_ALPHA_DIRECTION_CONFLICT | Q1 BUY + Q3 SHORT (or Q1 SELL + Q3 LONG), same (ticker,date) |

## 129 cases — breakdown

| Rule | Count | Alignment precision | Notes |
|---|---|---|---|
| LONG_WITH_WEAK_VALIDATION | 43 | best-effort (task_id only) | only 4/43 are same-adapter (vibe_trading); the other 39 pair unrelated adapters |
| HIGH_CONFIDENCE_POOR_CALIBRATION | 39 | exact | 100% deepalpha (39/39) |
| ACTION_ALPHA_DIRECTION_CONFLICT | 27 | exact | 4/27 are deepalpha-vs-itself; 23/27 cross-adapter |
| BUY_WITH_HIGH_RISK | 15 | exact | most involve tradingagents/fingpt/nofx |
| HIGH_WEIGHT_HIGH_DRAWDOWN | 5 | best-effort (task_id only) | finrl/finrl_x paired with prediction_arena — unrelated strategies |
| POSITIVE_SENTIMENT_BEAR_REGIME | 0 | — | no Q4 record has ever reported regime=BEAR yet |
| STRONG_SIGNAL_MISSING_EVIDENCE | 0 | — | supporting_evidence is 100% populated across all 142 Q3 records |

Exact-join total: 81/129 (63%). Best-effort-join total: 48/129 (37%).

Adapter involvement frequency across all 129 cases: deepalpha 83, vibe_trading 24,
tradingagents 20, prediction_arena 15, finrl 15, qlib 12, alphagen 10,
agentictrading 10, fingpt 8, nofx 6, finrl_x 5, finclaw 2, rdagent 1.

## deepalpha's self-contradiction — root cause found in source

4 of the 27 ACTION_ALPHA_DIRECTION_CONFLICT cases are deepalpha vs. itself
(NVDA BUY/SHORT, QQQ SELL/LONG x2, XOM SELL/LONG). Root cause in
`adapters/deepalpha_adapter.py`: `q1_decision` and `q3_signal` each call
`_train_ensemble(ticker)` **independently** — the XGBoost/LightGBM ensemble
is retrained from scratch on every call, with **no fixed random_state and no
caching**. Q1's action uses a nonzero threshold (`prediction > threshold` /
`< -threshold`), Q3's direction uses a bare sign check (`prediction > 0`).
Combined with retraining non-determinism, the same ticker/date can get a
positive `prediction` on one call and a negative one on the next — this is
model-training non-determinism, not two genuinely different reasoning
systems disagreeing.

## Supplementary figures generated for this Q&A (not part of the regular
## icaif_experiments pipeline — see analysis/_ad_hoc_contradiction_viz.py)

- `fig_14_alignment_precision_split.png` — exact (81) vs. best-effort (48) case split
- `fig_15_adapter_involvement_frequency.png` — adapter involvement ranking
- `fig_16_calibration_sample_size_distribution.png` — 28/39 calibration buckets have n<10 (noisy)
