"""
analysis/icaif_experiments.py — CLI orchestrator for the ICAIF experiment
suite (Experiments 1-5) built on top of the existing Q1-Q5 harness.

    python -m analysis.icaif_experiments \\
        --results-dir results --adapters-dir adapters \\
        --out reports/icaif_experiments \\
        --horizons 1,5,20 --threshold-bps 20

Nothing here hard-codes an adapter count, a ticker list, or a date — every
number in the outputs is discovered from the repo (adapters/*.py) and from
results/**/*.json at run time. See reports/icaif_experiments/README.md for
how to rerun this and reports/icaif_experiments/PAPER_FINDINGS.md for the
narrative this is meant to support.

Runs in any env with pandas + matplotlib + yfinance (deepalpha_real already
has all three, see README.md) — it never imports an adapter module.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from analysis.icaif_data_loader import (
    YFinanceFutureReturnProvider,
    discover_adapters,
    discover_result_files,
    records_to_dataframe,
)
from analysis.icaif_contradictions import (
    build_outcome_comparison,
    detect_contradictions,
    extract_q1,
    extract_q2,
    extract_q3,
)
from analysis.icaif_fusion import build_fusion_ablation_results, compute_fusion_decisions, explain_case
from analysis.icaif_metrics import (
    ATOM_TAGS,
    Config,
    build_calibration_table,
    build_coverage_matrix,
    build_compression_loss_summary,
    build_field_coverage,
    build_secondary_field_sparsity,
    check_expected_counts,
    compute_hit,
    coverage_audit_findings,
    evidence_atoms_from_record,
    flag_overconfidence,
    risk_atoms_from_record,
    validation_atoms_from_record,
)
from analysis import icaif_plots as plots

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Experiment 1 — adapter coverage audit
# --------------------------------------------------------------------------- #

def build_adapter_inventory(adapters, df: pd.DataFrame) -> pd.DataFrame:
    n_records = df.groupby("adapter").size().to_dict() if not df.empty else {}
    n_errors = (
        df[df["is_error"] == True].groupby("adapter").size().to_dict()  # noqa: E712
        if not df.empty else {}
    )
    rows = []
    for info in adapters:
        rows.append({
            "adapter": info.name, "file": info.file, "class_name": info.class_name,
            "upstream_repo": info.upstream_repo, "requires_env": info.requires_env,
            "questions_declared": ",".join(info.questions_declared),
            "questions_implemented": ",".join(info.questions_implemented),
            "n_result_records": n_records.get(info.name, 0),
            "n_error_records": n_errors.get(info.name, 0),
        })
    return pd.DataFrame(rows)


def run_experiment_1(adapters, df: pd.DataFrame, out: Path) -> Dict[str, pd.DataFrame]:
    coverage_matrix = build_coverage_matrix(adapters, df)
    field_coverage = build_field_coverage(df)
    sparsity = build_secondary_field_sparsity(field_coverage)
    inventory = build_adapter_inventory(adapters, df)
    findings = coverage_audit_findings(adapters, df)
    expected_check = check_expected_counts(adapters)

    coverage_matrix.to_csv(out / "coverage_matrix.csv")
    field_coverage.to_csv(out / "field_coverage.csv", index=False)
    sparsity.to_csv(out / "secondary_field_sparsity.csv", index=False)
    inventory.to_csv(out / "adapter_inventory.csv", index=False)
    findings.to_csv(out / "coverage_audit_findings.csv", index=False)
    expected_check.to_csv(out / "expected_vs_actual_declared_counts.csv", index=False)

    plots.plot_coverage_heatmap(coverage_matrix, out / "fig_01_adapter_q_coverage_heatmap.png")
    plots.plot_field_coverage_bar(field_coverage, out / "fig_02_field_coverage_bar.png")

    return {
        "coverage_matrix": coverage_matrix, "field_coverage": field_coverage,
        "sparsity": sparsity, "inventory": inventory,
        "findings": findings, "expected_check": expected_check,
    }


# --------------------------------------------------------------------------- #
# Experiment 2 — secondary-field value / schema compression
# --------------------------------------------------------------------------- #

def build_atom_tables(df: pd.DataFrame, cfg: Config):
    ev_rows, risk_rows, val_rows = [], [], []
    for _, r in df.iterrows():
        base = {"adapter": r.get("adapter"), "ticker": r.get("ticker"),
                "date": r.get("date"), "task_id": r.get("task_id")}
        if r.get("q1_present") or r.get("q2_present") or r.get("q3_present"):
            ev_rows.append({**base, "evidence_atoms": ",".join(evidence_atoms_from_record(r))})
        risk = risk_atoms_from_record(r)
        if risk:
            risk_rows.append({**base, "risk_atoms": ",".join(risk)})
        val = validation_atoms_from_record(r, cfg)
        if val:
            val_rows.append({**base, "validation_atoms": ",".join(val)})
    return (
        pd.DataFrame(ev_rows, columns=["adapter", "ticker", "date", "task_id", "evidence_atoms"]),
        pd.DataFrame(risk_rows, columns=["adapter", "ticker", "date", "task_id", "risk_atoms"]),
        pd.DataFrame(val_rows, columns=["adapter", "ticker", "date", "task_id", "validation_atoms"]),
    )


def build_evidence_cluster_matrix(evidence_atoms_df: pd.DataFrame) -> pd.DataFrame:
    if evidence_atoms_df.empty:
        return pd.DataFrame()
    adapters = sorted(evidence_atoms_df["adapter"].dropna().unique())
    mat = pd.DataFrame(0, index=adapters, columns=ATOM_TAGS)
    for _, r in evidence_atoms_df.iterrows():
        tags = [t for t in str(r["evidence_atoms"]).split(",") if t]
        for t in tags:
            if t in mat.columns:
                mat.loc[r["adapter"], t] += 1
    return mat.loc[:, (mat.sum(axis=0) > 0)] if mat.to_numpy().sum() > 0 else mat


def run_experiment_2(df: pd.DataFrame, cfg: Config, out: Path) -> Dict[str, pd.DataFrame]:
    compression = build_compression_loss_summary(df, cfg)
    evidence_atoms, risk_atoms, validation_atoms = build_atom_tables(df, cfg)
    cluster_matrix = build_evidence_cluster_matrix(evidence_atoms)

    compression.to_csv(out / "compression_loss_summary.csv", index=False)
    evidence_atoms.to_csv(out / "evidence_atoms.csv", index=False)
    risk_atoms.to_csv(out / "risk_atoms.csv", index=False)
    validation_atoms.to_csv(out / "validation_atoms.csv", index=False)

    sparsity = build_secondary_field_sparsity(build_field_coverage(df))
    plots.plot_secondary_field_sparsity(sparsity, out / "fig_03_secondary_field_sparsity.png")
    plots.plot_secondary_field_value_by_q(compression, out / "fig_04_secondary_field_value_by_q.png")
    plots.plot_evidence_cluster_map(cluster_matrix, out / "fig_05_evidence_cluster_map.png")

    return {"compression": compression, "evidence_atoms": evidence_atoms,
            "risk_atoms": risk_atoms, "validation_atoms": validation_atoms}


# --------------------------------------------------------------------------- #
# Experiment 3 — confidence calibration
# --------------------------------------------------------------------------- #

def build_df_hits(df: pd.DataFrame, provider, cfg: Config) -> pd.DataFrame:
    rows = []
    for _, r in extract_q1(df).iterrows():
        for h in cfg.horizons:
            fr = _safe_future_return(provider, r["ticker"], r["date"], h)
            rows.append({
                "adapter": r["adapter"], "question": "Q1", "ticker": r["ticker"], "date": r["date"],
                "horizon": h, "label": r["action"], "confidence": r.get("confidence"),
                "future_return": fr, "hit": compute_hit(r["action"], fr, cfg, "q1"),
            })
    for _, r in extract_q3(df).iterrows():
        for h in cfg.horizons:
            fr = _safe_future_return(provider, r["ticker"], r["date"], h)
            rows.append({
                "adapter": r["adapter"], "question": "Q3", "ticker": r["ticker"], "date": r["date"],
                "horizon": h, "label": r["direction"], "confidence": r.get("strength"),
                "future_return": fr, "hit": compute_hit(r["direction"], fr, cfg, "q3"),
            })
    return pd.DataFrame(rows, columns=["adapter", "question", "ticker", "date", "horizon",
                                        "label", "confidence", "future_return", "hit"])


def _safe_future_return(provider, ticker, date, horizon) -> Optional[float]:
    if provider is None or ticker is None or date is None:
        return None
    try:
        return provider.get_future_return(ticker, date, horizon)
    except Exception:
        return None


def run_experiment_3(df: pd.DataFrame, provider, cfg: Config, out: Path) -> Dict:
    df_hits = build_df_hits(df, provider, cfg)
    calibration_table = build_calibration_table(df_hits, cfg)
    overconfidence_flags = flag_overconfidence(calibration_table, cfg)

    calibration_table.to_csv(out / "calibration_table.csv", index=False)
    overconfidence_flags.to_csv(out / "overconfidence_flags.csv", index=False)

    plots.plot_reliability_diagram_q1(calibration_table, out / "fig_06_reliability_diagram_q1.png")
    plots.plot_reliability_diagram_q3(calibration_table, out / "fig_07_reliability_diagram_q3.png")
    plots.plot_calibration_error_by_adapter(calibration_table, out / "fig_08_calibration_error_by_adapter.png")

    n_total = len(df_hits)
    n_with_return = int(df_hits["future_return"].notna().sum()) if n_total else 0
    readme_lines = [
        "# Calibration data availability", "",
        f"Total (adapter, question, ticker, date, horizon) rows attempted: {n_total}",
        f"Rows with a realized future return: {n_with_return}",
        "",
        "## Per-horizon availability",
    ]
    if n_total:
        for h, g in df_hits.groupby("horizon"):
            avail = int(g["future_return"].notna().sum())
            readme_lines.append(f"- horizon={h}: {avail}/{len(g)} rows have a realized future return")
        dates = sorted(set(df_hits["date"].dropna()))
        readme_lines += ["", f"Decision dates present in results/: {dates}",
                          "A horizon's rows stay `future_return=NaN` (marked insufficient_data downstream, "
                          "never fabricated) until that many trading days have actually elapsed after the "
                          "decision date — see analysis/icaif_data_loader.py:YFinanceFutureReturnProvider."]
    else:
        readme_lines.append("No Q1/Q3 records with both a ticker and a date were found under results/.")
    (out / "calibration_README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    return {"df_hits": df_hits, "calibration_table": calibration_table,
            "overconfidence_flags": overconfidence_flags}


# --------------------------------------------------------------------------- #
# Experiment 4 — cross-agent contradiction detection
# --------------------------------------------------------------------------- #

def run_experiment_4(df: pd.DataFrame, overconfidence_flags: pd.DataFrame, df_hits: pd.DataFrame,
                      cfg: Config, out: Path) -> Dict:
    result = detect_contradictions(df, overconfidence_flags, cfg)
    cases, summary = result["cases"], result["summary"]
    outcome_comparison = build_outcome_comparison(cases, df_hits)

    cases.to_csv(out / "contradiction_cases.csv", index=False)
    summary.to_csv(out / "contradiction_summary.csv", index=False)
    outcome_comparison.to_csv(out / "contradiction_outcome_comparison.csv", index=False)

    plots.plot_contradiction_counts(summary, out / "fig_09_contradiction_counts.png")
    plots.plot_flagged_vs_unflagged_returns(outcome_comparison, out / "fig_10_flagged_vs_unflagged_forward_returns.png")

    return {"cases": cases, "summary": summary, "outcome_comparison": outcome_comparison}


# --------------------------------------------------------------------------- #
# Experiment 5 — fusion ablation
# --------------------------------------------------------------------------- #

def run_experiment_5(df: pd.DataFrame, cases: pd.DataFrame, provider, cfg: Config, out: Path) -> Dict:
    decisions = compute_fusion_decisions(
        df, cases, cfg,
        future_return_lookup=(provider.get_future_return if provider else None),
        horizon=cfg.horizons[0],
    )
    results = build_fusion_ablation_results(decisions, cfg)

    decisions.to_csv(out / "fusion_decisions.csv", index=False)
    results.to_csv(out / "fusion_ablation_results.csv", index=False)

    plots.plot_fusion_ablation_metrics(results, out / "fig_11_fusion_ablation_metrics.png")
    plots.plot_decision_distribution_by_method(results, out / "fig_12_decision_distribution_by_method.png")

    example_ticker, example_date, explanation = None, None, None
    if not decisions.empty:
        for candidate in ("NVDA",):
            sub = decisions[decisions["ticker"] == candidate]
            if not sub.empty:
                example_ticker, example_date = candidate, sub.iloc[0]["date"]
                break
        if example_ticker is None:
            example_ticker, example_date = decisions.iloc[0]["ticker"], decisions.iloc[0]["date"]
        explanation = explain_case(df, cases, cfg, example_ticker, example_date,
                                    future_return_lookup=(provider.get_future_return if provider else None),
                                    horizon=cfg.horizons[0])
    plots.plot_final_decision_waterfall(explanation, out / "fig_13_final_decision_waterfall_example.png",
                                         ticker=example_ticker or "")

    return {"decisions": decisions, "results": results}


# --------------------------------------------------------------------------- #
# Case studies
# --------------------------------------------------------------------------- #

def build_case_study(ticker: str, df: pd.DataFrame, cases: pd.DataFrame, cfg: Config, provider, out_path: Path) -> None:
    q1, q2, q3 = extract_q1(df), extract_q2(df), extract_q3(df)
    sub1, sub2, sub3 = q1[q1["ticker"] == ticker], q2[q2["ticker"] == ticker], q3[q3["ticker"] == ticker]
    dates = sorted({d for d in list(sub1["date"]) + list(sub2["date"]) + list(sub3["date"]) if d})

    lines = [f"# Case Study: {ticker}", ""]
    if not dates:
        lines.append(f"No Q1/Q2/Q3 records found for **{ticker}** in the current `results/` data. "
                      "This case study will populate automatically once an adapter run includes this ticker "
                      "— nothing below is fabricated.")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return

    for date in dates:
        lines += [f"## {date}", "", "### Headline signals"]
        for _, r in sub1[sub1["date"] == date].iterrows():
            conf = r.get("confidence")
            lines.append(f"- **{r['adapter']}** (Q1): action={r['action']}, "
                          f"confidence={conf:.2f}" if conf is not None else f"- **{r['adapter']}** (Q1): action={r['action']}")
        for _, r in sub2[sub2["date"] == date].iterrows():
            lines.append(f"- **{r['adapter']}** (Q2): sentiment_score={r['sentiment_score']:.2f}, "
                          f"risk_level={r['risk_level']}")
        for _, r in sub3[sub3["date"] == date].iterrows():
            lines.append(f"- **{r['adapter']}** (Q3): direction={r['direction']}, strength={r['strength']:.2f}")

        lines += ["", "### Secondary fields / evidence"]
        day_rows = df[(df["ticker"] == ticker) & (df["date"] == date)]
        any_secondary = False
        for _, r in day_rows.iterrows():
            if isinstance(r.get("q1_reasoning"), str) and r["q1_reasoning"].strip():
                lines.append(f"- {r['adapter']} reasoning: {r['q1_reasoning']}")
                any_secondary = True
            if isinstance(r.get("q3_supporting_evidence"), list) and r["q3_supporting_evidence"]:
                lines.append(f"- {r['adapter']} supporting_evidence: {r['q3_supporting_evidence']}")
                any_secondary = True
        if not any_secondary:
            lines.append("- none populated for this date")

        lines += ["", "### Detected contradictions"]
        flags = cases[(cases["ticker"] == ticker) & (cases["date"] == date)] if not cases.empty else pd.DataFrame()
        if flags.empty:
            lines.append("- none detected")
        else:
            for _, f in flags.iterrows():
                lines.append(f"- **{f['flag']}**: {f['detail']} _(limitation: {f['limitation']})_")

        lines += ["", "### Fusion decision"]
        explanation = explain_case(df, cases, cfg, ticker, date,
                                    future_return_lookup=(provider.get_future_return if provider else None),
                                    horizon=cfg.horizons[0])
        if explanation.get("found"):
            lines.append(f"- majority_vote: {explanation['majority_decision']}")
            lines.append(f"- confidence_weighted_vote: {explanation['confidence_weighted_decision']}")
            lines.append(
                f"- interwoven_calibrated_fusion: **{explanation['final_decision']}** "
                f"(score={explanation['final_score']:.3f}; risk_mult={explanation['risk_multiplier']:.2f}, "
                f"validation_mult={explanation['validation_multiplier']:.2f}, "
                f"contradiction_mult={explanation['contradiction_multiplier']:.2f}, "
                f"boost={'yes' if explanation['evidence_boost_applied'] else 'no'})"
            )
            if explanation["final_decision"] != explanation["majority_decision"]:
                lines.append("- **Differs from majority vote** because of the multipliers above.")
            else:
                lines.append("- Same as majority vote for this case.")
            fr = explanation.get("future_return")
            lines.append(
                f"- realized future return (h={explanation['future_return_horizon']}): {fr:.4f}"
                if fr is not None else
                "- realized future return: insufficient_data (not enough trading days elapsed yet)"
            )
        else:
            lines.append("- no fusable Q1/Q3 votes found for this (ticker, date)")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Report generation
# --------------------------------------------------------------------------- #

def write_readme(out: Path, args: argparse.Namespace, adapters, df: pd.DataFrame) -> None:
    n_adapters = len(adapters)
    n_records = len(df)
    n_error = int(df["is_error"].sum()) if not df.empty else 0
    text = f"""# ICAIF Experiment Suite — Outputs

## How to rerun

```
conda run -n deepalpha_real python -m analysis.icaif_experiments \\
    --results-dir {args.results_dir} --adapters-dir {args.adapters_dir} \\
    --out {args.out} --horizons {args.horizons} --threshold-bps {args.threshold_bps}
```

`deepalpha_real` is used because it is the one conda env in this repo that
already carries pandas + matplotlib + yfinance (see analysis/build_visualizations.py's
own docstring) — this suite never imports an adapter module, so no other
adapter-specific env is needed.

## What data was used

- Adapters discovered by static source scan of `{args.adapters_dir}/*.py`: **{n_adapters}**
  (excludes `example_stub_adapter.py` and `vendor/`; count is not hard-coded,
  see `adapter_inventory.csv`).
- Result records discovered under `{args.results_dir}/**/*.json`: **{n_records}**
  ({n_error} of which are error payloads from a failed `adapter.run()`).
- Forward/future prices: fetched live via yfinance on each run and cached under
  `data/cache/prices/{{ticker}}.csv`; never fabricated when unavailable.

## Where outputs are saved

All CSVs and PNGs land flat in `{args.out}/`, named `fig_NN_*.png` / `*.csv`
per the experiment they belong to (1: coverage, 2: secondary-field value,
3: calibration, 4: contradictions, 5: fusion ablation), plus:

- `calibration_README.md` — which horizons had realized returns and why others didn't
- `case_study_NVDA.md`, `case_study_SPY.md`
- `PAPER_FINDINGS.md` — the narrative synthesis

## What was skipped because of missing data

See `calibration_README.md` for the exact per-horizon breakdown. In short:
any figure/table whose caption or first row says `insufficient_data` means
there were not yet enough realized trading days since the recorded decision
date(s) to compute a forward return at that horizon — this is expected the
first time this pipeline is run against a fresh comparison batch, and will
fill in as time passes and/or more `analysis/collect_results.py` runs are
added.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_paper_findings(out: Path, e1: Dict, e2: Dict, e3: Dict, e4: Dict, e5: Dict) -> None:
    expected_ok = e1["expected_check"]["matches"].all() if not e1["expected_check"].empty else None
    mismatches = e1["findings"]
    n_mismatch = len(mismatches)

    sparsest = e1["sparsity"].head(5)
    sparsest_lines = [f"  - {q}.{f}: {s:.0%} sparse"
                       for q, f, s in zip(sparsest["question"], sparsest["field"], sparsest["sparsity"])] \
        if not sparsest.empty else ["  - (no data)"]

    calib = e3["calibration_table"]
    calibrated_note = (
        "insufficient_data — no realized forward returns yet, see calibration_README.md"
        if calib.empty else
        f"{len(calib)} (adapter, question, horizon, bucket) cells computed; "
        f"{len(e3['overconfidence_flags'])} flagged overconfident"
    )

    n_contradictions = e4["cases"]["flag"].count() if not e4["cases"].empty else 0
    fusion_results = e5["results"]
    fusion_note = "Insufficient_data — see fusion_ablation_results.csv for coverage-only metrics" \
        if fusion_results.empty or fusion_results.get("insufficient_data", pd.Series(dtype=bool)).fillna(False).all() \
        else "See fusion_ablation_results.csv"

    text = f"""# Paper Findings — ICAIF Experiment Suite

Generated from the actual repo state at run time — every number below traces
to a CSV in this directory, nothing is asserted without a corresponding file.

## 1. Does Q1-Q5 cover the observed adapter capabilities?

{n_mismatch} declared/implemented/observed mismatch(es) found — see
`coverage_audit_findings.csv`. Expected-vs-actual declared counts
(Q1~4/Q2~4/Q3~8/Q4~3/Q5~4 from prior project notes) {'match' if expected_ok else 'do NOT all match'}
current repo state — see `expected_vs_actual_declared_counts.csv`.

## 2. Which fields are sparse or adapter-specific?

Sparsest secondary fields overall:
{chr(10).join(sparsest_lines)}

Full detail in `secondary_field_sparsity.csv` and `compression_loss_summary.csv`.

## 3. What information is lost by headline-only comparison?

See `fig_04_secondary_field_value_by_q.png` and `compression_loss_summary.csv`
for evidence/risk/validation atom counts unlocked only by reading secondary
fields — a headline-only comparison (action/sentiment_score/direction+strength/
weights/total_return alone) recovers zero of these atoms by construction.

## 4. Are confidence/strength scores calibrated?

{calibrated_note}. See `calibration_table.csv`, `overconfidence_flags.csv`,
`fig_06_reliability_diagram_q1.png`, `fig_07_reliability_diagram_q3.png`.

## 5. What contradictions are detected?

{n_contradictions} contradiction case(s) across the 8 rules — see
`contradiction_summary.csv` for counts by rule and `contradiction_cases.csv`
for the full case list (each row states its own alignment limitation).

## 6. Does interwoven fusion improve over majority vote or confidence-weighted vote?

{fusion_note}. Decision-distribution and disagreement-reduction comparisons
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
"""
    (out / "PAPER_FINDINGS.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ICAIF experiment suite for the trading-ai-ensemble harness")
    p.add_argument("--results-dir", default=str(ROOT / "results"))
    p.add_argument("--adapters-dir", default=str(ROOT / "adapters"))
    p.add_argument("--out", default=str(ROOT / "reports" / "icaif_experiments"))
    p.add_argument("--horizons", default="1,5,20")
    p.add_argument("--threshold-bps", type=float, default=20.0)
    p.add_argument("--cache-dir", default=str(ROOT / "data" / "cache" / "prices"))
    p.add_argument("--config", default=None, help="optional JSON file overriding any Config field")
    p.add_argument("--no-price-fetch", action="store_true",
                    help="skip yfinance entirely (coverage/secondary-field/contradiction-skeleton/"
                         "fusion-skeleton only; calibration and return metrics report insufficient_data)")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    overrides: Dict = {}
    if args.config:
        overrides.update(json.loads(Path(args.config).read_text()))
    horizons = tuple(int(h) for h in str(args.horizons).split(",") if h.strip())
    overrides["horizons"] = horizons
    overrides["threshold_bps"] = args.threshold_bps
    cfg = Config.from_overrides(overrides)

    adapters = discover_adapters(Path(args.adapters_dir))
    records = discover_result_files(Path(args.results_dir))
    df = records_to_dataframe(records)

    provider = None if args.no_price_fetch else YFinanceFutureReturnProvider(Path(args.cache_dir))

    print(f"Discovered {len(adapters)} adapters, {len(df)} result records "
          f"({int(df['is_error'].sum()) if not df.empty else 0} error payloads).")

    e1 = run_experiment_1(adapters, df, out)
    e2 = run_experiment_2(df, cfg, out)
    e3 = run_experiment_3(df, provider, cfg, out)
    e4 = run_experiment_4(df, e3["overconfidence_flags"], e3["df_hits"], cfg, out)
    e5 = run_experiment_5(df, e4["cases"], provider, cfg, out)

    build_case_study("NVDA", df, e4["cases"], cfg, provider, out / "case_study_NVDA.md")
    build_case_study("SPY", df, e4["cases"], cfg, provider, out / "case_study_SPY.md")

    write_readme(out, args, adapters, df)
    write_paper_findings(out, e1, e2, e3, e4, e5)

    print(f"Done. Outputs written to {out}")


if __name__ == "__main__":
    main()
