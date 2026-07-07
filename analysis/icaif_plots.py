"""
analysis/icaif_plots.py — the 13 figures for the ICAIF experiment suite.

matplotlib only (no plotly/kaleido dependency here, unlike
analysis/build_visualizations.py) so this runs in any env with
matplotlib+pandas — deepalpha_real already has both, see reports/icaif_experiments/README.md.

Every function is defensive about missing/insufficient data: if there's
nothing to plot, it still writes a PNG with an explanatory placeholder
message rather than crashing the whole pipeline or silently skipping the
file (a paper reader who opens fig_07 and finds nothing should see *why*,
not a missing file).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

STATUS_SCORE = {
    "": 0,
    "declared": 1,
    "implemented": 1,
    "declared+implemented": 2,
    "observed": 1,
    "declared+observed": 1.5,
    "implemented+observed": 1.5,
    "declared+implemented+observed": 3,
}


def _placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True, fontsize=11)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_coverage_heatmap(coverage_matrix: pd.DataFrame, path: Path) -> None:
    """fig_01 — answers: which adapters declare/implement/actually-produced
    output for which Q? Anomalous combos (e.g. observed without declared) get
    a distinct mid-tone so they visually stand out from clean progressions."""
    if coverage_matrix.empty:
        _placeholder(path, "Adapter x Q Coverage", "No adapters discovered.")
        return

    questions = list(coverage_matrix.columns)
    adapters = list(coverage_matrix.index)
    z = coverage_matrix.map(lambda v: STATUS_SCORE.get(v, 0)).to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(1.4 * len(questions) + 2, 0.35 * len(adapters) + 2))
    im = ax.imshow(z, cmap="YlGn", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(questions)), questions)
    ax.set_yticks(range(len(adapters)), adapters, fontsize=8)
    for i in range(len(adapters)):
        for j in range(len(questions)):
            label = coverage_matrix.iloc[i, j] or "-"
            ax.text(j, i, label, ha="center", va="center", fontsize=6)
    ax.set_title("Adapter x Q Coverage — declared / implemented / observed\n"
                 "(darker = more of the three agree; short label = which apply)")
    fig.colorbar(im, ax=ax, label="agreement score (0=none, 3=all three)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_field_coverage_bar(field_coverage: pd.DataFrame, path: Path) -> None:
    """fig_02 — answers: within each Q, how complete is the primary field vs.
    the average secondary field, across every record that answers that Q?"""
    if field_coverage.empty:
        _placeholder(path, "Field Coverage", "No result records discovered under results/.")
        return

    summary = (
        field_coverage.groupby(["question", "kind"])["coverage_ratio"]
        .mean().reset_index()
    )
    questions = sorted(summary["question"].unique())
    x = np.arange(len(questions))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, kind in enumerate(["primary", "secondary"]):
        vals = [summary[(summary["question"] == q) & (summary["kind"] == kind)]["coverage_ratio"].mean()
                for q in questions]
        ax.bar(x + (i - 0.5) * width, vals, width, label=kind)
    ax.set_xticks(x, questions)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("mean coverage ratio (non-empty / records answering Q)")
    ax.set_title("Primary vs. Secondary Field Coverage by Question\n"
                 "(low secondary bars = headline-only comparison would discard real content)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_secondary_field_sparsity(sparsity: pd.DataFrame, path: Path) -> None:
    """fig_03 — answers: which specific secondary fields are the sparsest
    across the adapters that could report them?"""
    if sparsity.empty:
        _placeholder(path, "Secondary Field Sparsity", "No secondary-field data available.")
        return

    labels = [f"{q}.{f}" for q, f in zip(sparsity["question"], sparsity["field"])]
    fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * len(labels))))
    ax.barh(labels, sparsity["sparsity"], color="indianred")
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("sparsity (1 - coverage ratio)")
    ax.set_title("Secondary-Field Sparsity\n(fields adapters rarely populate, sorted worst-first per Q)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_secondary_field_value_by_q(compression: pd.DataFrame, path: Path) -> None:
    """fig_04 — answers: how many evidence / risk / validation atoms does the
    secondary-field surface actually unlock, per question?"""
    if compression.empty:
        _placeholder(path, "Secondary-Field Value by Q", "No records with secondary fields available.")
        return

    agg = compression.groupby("question")[
        ["evidence_atoms_generated", "risk_atoms_generated", "validation_atoms_generated"]
    ].sum()
    questions = list(agg.index)
    x = np.arange(len(questions))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, col in enumerate(["evidence_atoms_generated", "risk_atoms_generated", "validation_atoms_generated"]):
        ax.bar(x + (i - 1) * width, agg[col], width, label=col.replace("_generated", ""))
    ax.set_xticks(x, questions)
    ax.set_ylabel("atoms generated (summed across adapters)")
    ax.set_title("Secondary-Field Value by Question\n"
                 "(atoms only exist because secondary fields were read — headline-only view produces zero)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_evidence_cluster_map(atom_counts: pd.DataFrame, path: Path) -> None:
    """fig_05 — answers: which adapters' evidence leans on which coarse
    topics (momentum, valuation, risk, ...)? atom_counts: adapter x tag counts."""
    if atom_counts.empty:
        _placeholder(path, "Evidence Cluster Map", "No evidence atoms extracted (no reasoning/drivers/supporting_evidence text found).")
        return

    fig, ax = plt.subplots(figsize=(1.1 * len(atom_counts.columns) + 3, 0.4 * len(atom_counts.index) + 2))
    im = ax.imshow(atom_counts.to_numpy(dtype=float), cmap="Purples", aspect="auto")
    ax.set_xticks(range(len(atom_counts.columns)), atom_counts.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(atom_counts.index)), atom_counts.index, fontsize=8)
    for i in range(len(atom_counts.index)):
        for j in range(len(atom_counts.columns)):
            v = int(atom_counts.iloc[i, j])
            if v:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=7)
    ax.set_title("Evidence Atom Cluster Map — adapter x coarse topic tag")
    fig.colorbar(im, ax=ax, label="occurrences")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _reliability_diagram(calibration_table: pd.DataFrame, question: str, path: Path, title: str) -> None:
    sub = calibration_table[calibration_table["question"] == question] if "question" in calibration_table.columns else pd.DataFrame()
    if sub.empty:
        _placeholder(path, title,
                     f"insufficient_data: no realized-return calibration samples for {question} yet.\n"
                     "Requires forward trading days to have elapsed since the decision date — see calibration_README.md.")
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "--", color="gray", label="perfect calibration")
    for adapter, g in sub.groupby("adapter"):
        g = g.sort_values("avg_confidence")
        ax.scatter(g["avg_confidence"], g["actual_hit_rate"], s=g["sample_count"] * 8 + 20, alpha=0.7, label=adapter)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("avg confidence / strength in bucket")
    ax.set_ylabel("actual hit rate")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_reliability_diagram_q1(calibration_table: pd.DataFrame, path: Path) -> None:
    _reliability_diagram(calibration_table, "Q1", path,
                          "Q1 Reliability Diagram — confidence vs. realized hit rate\n"
                          "(above diagonal = underconfident, below = overconfident)")


def plot_reliability_diagram_q3(calibration_table: pd.DataFrame, path: Path) -> None:
    _reliability_diagram(calibration_table, "Q3", path,
                          "Q3 Reliability Diagram — strength vs. realized hit rate\n"
                          "(above diagonal = underconfident, below = overconfident)")


def plot_calibration_error_by_adapter(calibration_table: pd.DataFrame, path: Path) -> None:
    """fig_08 — answers: which adapters are best/worst calibrated overall?"""
    if calibration_table.empty:
        _placeholder(path, "Calibration Error by Adapter",
                     "insufficient_data: no realized-return calibration samples yet.")
        return

    agg = calibration_table.groupby("adapter").apply(
        lambda g: np.average(g["calibration_error"], weights=g["sample_count"]), include_groups=False
    ).sort_values()
    fig, ax = plt.subplots(figsize=(7, max(3, 0.4 * len(agg))))
    ax.barh(agg.index, agg.values, color="steelblue")
    ax.set_xlabel("|avg_confidence - actual_hit_rate| (sample-weighted)")
    ax.set_title("Calibration Error by Adapter\n(lower is better calibrated)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_contradiction_counts(summary: pd.DataFrame, path: Path) -> None:
    """fig_09 — answers: which contradiction rules actually fire, and how often?"""
    if summary.empty:
        _placeholder(path, "Contradiction Counts", "No contradictions detected with current data.")
        return

    fig, ax = plt.subplots(figsize=(9, max(3, 0.5 * len(summary))))
    order = summary.sort_values("count", ascending=True)
    ax.barh(order["flag"], order["count"], color="darkorange")
    ax.set_xlabel("number of flagged cases")
    ax.set_title("Cross-Agent Contradiction Counts by Rule")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_flagged_vs_unflagged_returns(outcome_comparison: pd.DataFrame, path: Path) -> None:
    """fig_10 — answers: do flagged (contradictory) decisions actually perform
    worse than unflagged ones, when realized returns exist?"""
    if outcome_comparison.empty or outcome_comparison["insufficient_data"].all():
        _placeholder(path, "Flagged vs. Unflagged Forward Returns",
                     "insufficient_data: no realized forward returns available yet to compare "
                     "flagged vs. unflagged contradiction cases.")
        return

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(outcome_comparison["group"], outcome_comparison["avg_forward_return"],
           color=["darkorange", "steelblue"])
    for i, r in outcome_comparison.iterrows():
        n = r["n_samples"]
        ax.text(i, r["avg_forward_return"], f"n={n}", ha="center",
                va="bottom" if r["avg_forward_return"] >= 0 else "top")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_ylabel("avg forward return")
    ax.set_title("Forward Returns: Flagged vs. Unflagged Records\n(exact-join rules only, see contradiction_outcome_comparison.csv)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_fusion_ablation_metrics(results: pd.DataFrame, path: Path) -> None:
    """fig_11 — answers: does the interwoven fusion actually improve
    return-based metrics over majority/confidence-weighted voting?"""
    if results.empty:
        _placeholder(path, "Fusion Ablation Metrics", "No fusion decisions computed.")
        return
    if "insufficient_data" in results.columns and results["insufficient_data"].fillna(False).all():
        _placeholder(path, "Fusion Ablation Metrics",
                     "insufficient_data: no realized forward returns yet — see fusion_ablation_results.csv "
                     "for coverage/decision-distribution-only metrics.")
        return

    metrics = ["hit_rate", "avg_forward_return", "sharpe"]
    available = [m for m in metrics if m in results.columns]
    fig, axes = plt.subplots(1, len(available), figsize=(5 * len(available), 4))
    if len(available) == 1:
        axes = [axes]
    for ax, m in zip(axes, available):
        ax.bar(results["method"], results[m], color=["gray", "steelblue", "seagreen"])
        ax.set_title(m)
        ax.tick_params(axis="x", rotation=25)
    fig.suptitle("Fusion Ablation — Return-Based Metrics by Method")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_decision_distribution_by_method(results: pd.DataFrame, path: Path) -> None:
    """fig_12 — answers: does interwoven fusion actually reduce disagreement
    (e.g. fewer forced BUY/SELL, more considered HOLD) vs. naive voting?"""
    if results.empty or not {"pct_buy", "pct_hold", "pct_sell"}.issubset(results.columns):
        _placeholder(path, "Decision Distribution by Method", "No fusion decisions computed.")
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    bottom = np.zeros(len(results))
    for col, color in [("pct_sell", "indianred"), ("pct_hold", "lightgray"), ("pct_buy", "seagreen")]:
        ax.bar(results["method"], results[col], bottom=bottom, label=col.replace("pct_", ""), color=color)
        bottom += results[col].to_numpy(dtype=float)
    ax.set_ylabel("fraction of (ticker, date) decisions")
    ax.set_title("Decision Distribution by Fusion Method")
    ax.tick_params(axis="x", rotation=15)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_final_decision_waterfall(explanation: Optional[Dict], path: Path, ticker: str = "") -> None:
    """fig_13 — answers: concretely, how does interwoven fusion arrive at a
    different number than a naive confidence-weighted vote, step by step?"""
    if not explanation or not explanation.get("found"):
        _placeholder(path, "Final Decision Waterfall",
                     f"No fusable (ticker, date) example available{f' for {ticker}' if ticker else ''}.")
        return

    steps = [
        ("confidence-\nweighted", explanation["confidence_weighted_score"]),
        ("x risk_mult", explanation["after_risk"]),
        ("x validation_\nmult", explanation["after_validation"]),
        ("x contradiction_\nmult", explanation["after_contradiction"]),
        ("final\n(after boost)", explanation["final_score"]),
    ]
    labels = [s[0] for s in steps]
    values = [s[1] for s in steps]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["steelblue"] * (len(values) - 1) + ["seagreen" if values[-1] >= 0 else "indianred"]
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom" if v >= 0 else "top")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(f"Interwoven Fusion Score Waterfall — {explanation['ticker']} / {explanation['date']}\n"
                 f"final decision: {explanation['final_decision']} "
                 f"(confidence-weighted-only would say: {explanation['confidence_weighted_decision']})")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
