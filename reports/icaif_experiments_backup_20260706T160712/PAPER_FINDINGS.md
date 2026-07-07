# Paper Findings — ICAIF Experiment Suite

Generated from the actual repo state at run time — every number below traces
to a CSV in this directory, nothing is asserted without a corresponding file.

## 1. Does Q1-Q5 cover the observed adapter capabilities?

12 declared/implemented/observed mismatch(es) found — see
`coverage_audit_findings.csv`. Expected-vs-actual declared counts
(Q1~4/Q2~4/Q3~8/Q4~3/Q5~4 from prior project notes) do NOT all match
current repo state — see `expected_vs_actual_declared_counts.csv`.

## 2. Which fields are sparse or adapter-specific?

Sparsest secondary fields overall:
  - Q1.bull_case: 100% sparse
  - Q1.bear_case: 100% sparse
  - Q1.confidence: 0% sparse
  - Q1.reasoning: 0% sparse
  - Q1.time_horizon: 0% sparse

Full detail in `secondary_field_sparsity.csv` and `compression_loss_summary.csv`.

## 3. What information is lost by headline-only comparison?

See `fig_04_secondary_field_value_by_q.png` and `compression_loss_summary.csv`
for evidence/risk/validation atom counts unlocked only by reading secondary
fields — a headline-only comparison (action/sentiment_score/direction+strength/
weights/total_return alone) recovers zero of these atoms by construction.

## 4. Are confidence/strength scores calibrated?

5 (adapter, question, horizon, bucket) cells computed; 0 flagged overconfident. See `calibration_table.csv`, `overconfidence_flags.csv`,
`fig_06_reliability_diagram_q1.png`, `fig_07_reliability_diagram_q3.png`.

## 5. What contradictions are detected?

0 contradiction case(s) across the 8 rules — see
`contradiction_summary.csv` for counts by rule and `contradiction_cases.csv`
for the full case list (each row states its own alignment limitation).

## 6. Does interwoven fusion improve over majority vote or confidence-weighted vote?

See fusion_ablation_results.csv. Decision-distribution and disagreement-reduction comparisons
are available regardless of return data — see
`fig_12_decision_distribution_by_method.png` and the
`decision_stability_vs_other_methods` column in `fusion_ablation_results.csv`.

## 7. What are the limitations?

- Q4Portfolio and Q5Backtest carry no `ticker` field, and Q5Backtest carries
  no `date` field either (see CONTRACT/schemas.py) — every rule/metric that
  touches Q4 or Q5 is a best-effort task_id/date join, not an exact
  same-time-same-ticker comparison. Documented per-row in
  `contradiction_cases.csv`'s `limitation` column.
- Calibration and fusion return-metrics depend on real elapsed trading time
  after each recorded decision date — see `calibration_README.md` for exactly
  what's available as of this run.
- Evidence/risk atom tagging is a fixed-vocabulary keyword heuristic
  (`analysis/icaif_metrics.py:ATOM_KEYWORDS`), not a semantic classifier —
  tags are coarse and deterministic by design, not a claim of NLU.
- `results/` currently reflects whichever adapters have been run via
  `analysis/collect_results.py` — adapters with no result JSON are visible in
  `coverage_audit_findings.csv` as `no_observed_results`, not silently omitted.
