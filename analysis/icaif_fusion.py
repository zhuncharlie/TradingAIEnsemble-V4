"""
analysis/icaif_fusion.py — Experiment 5: fusion ablation.

Three methods, one shared (ticker, date) grouping across every adapter's
Q1/Q3 signal at that point:

  A. majority_vote                 — unweighted sign of the vote count
  B. confidence_weighted_vote      — weighted by confidence/strength
  C. interwoven_calibrated_fusion  — B, then penalised by risk / weak
                                      validation / contradiction flags, and
                                      modestly boosted when independent
                                      adapters' evidence atoms corroborate
                                      the same direction

All three share the same decision thresholds (Config.fusion_buy_threshold /
fusion_sell_threshold) so "decision distribution by method" is an apples to
apples comparison, not an artifact of different cutoffs per method.

Q4/Q5 alignment reuses the same best-effort (task_id-only) join documented in
icaif_contradictions.py — Q5Backtest carries neither ticker nor date.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from analysis.icaif_contradictions import extract_q1, extract_q3, extract_q4, extract_q5
from analysis.icaif_metrics import (
    ACTION_SIGN,
    Config,
    classify_validation_strength,
    compute_return_based_metrics,
    contradiction_multiplier_for,
    decision_distribution,
    decision_stability,
    evidence_atoms_from_record,
    risk_multiplier_for,
    score_to_decision,
    validation_multiplier_for,
)

FutureReturnLookup = Callable[[str, str, int], Optional[float]]


def _q2_extract(df: pd.DataFrame) -> pd.DataFrame:
    from analysis.icaif_contradictions import extract_q2
    return extract_q2(df)


def _build_vote_rows(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (ticker, date, adapter, question) directional vote."""
    q1 = extract_q1(df)
    q3 = extract_q3(df)
    rows = []
    for _, r in q1.iterrows():
        if r["action"] not in ACTION_SIGN:
            continue
        rows.append({
            "ticker": r["ticker"], "date": r["date"], "adapter": r["adapter"],
            "question": "Q1", "label": r["action"], "signal": ACTION_SIGN[r["action"]],
            "weight_raw": r.get("confidence"), "weight_is_default": pd.isna(r.get("confidence")),
        })
    for _, r in q3.iterrows():
        if r["direction"] not in ACTION_SIGN:
            continue
        rows.append({
            "ticker": r["ticker"], "date": r["date"], "adapter": r["adapter"],
            "question": "Q3", "label": r["direction"], "signal": ACTION_SIGN[r["direction"]],
            "weight_raw": r.get("strength"), "weight_is_default": pd.isna(r.get("strength")),
        })
    return pd.DataFrame(rows, columns=["ticker", "date", "adapter", "question", "label",
                                        "signal", "weight_raw", "weight_is_default"])


def _risk_lookup(df: pd.DataFrame, cfg: Config) -> Dict[tuple, float]:
    """(ticker, date) -> most conservative (lowest) risk multiplier across any
    adapter's Q2 for that ticker/date. Missing -> 1.0 (no penalty applied)."""
    q2 = _q2_extract(df)
    out: Dict[tuple, float] = {}
    for (ticker, date), g in q2.groupby(["ticker", "date"]):
        mults = [risk_multiplier_for(rl, cfg) for rl in g["risk_level"] if isinstance(rl, str)]
        if mults:
            out[(ticker, date)] = min(mults)
    return out


def _validation_lookup(df: pd.DataFrame, cfg: Config) -> Dict[str, float]:
    """task_id -> most conservative (lowest) validation multiplier across any
    Q5 record in that comparison run (best-effort, see module docstring).

    Context-aware (analysis/icaif_alignment.py, not a CONTRACT/schemas.py
    change): a Q5 record whose ctx_alignment_source could recover real
    batch context (index_csv/task_id_pattern) is trusted as computed; one
    with NO recoverable context at all (ctx_alignment_source in
    {None, "none", "filename_pattern"} — e.g. the legacy
    comparison_2026-07-02 batch) is additionally capped at the "missing"
    multiplier, since an unconfirmed join shouldn't be trusted more than no
    validation data at all. Return type is unchanged (Dict[str, float]) so
    every downstream Exp5 output column stays exactly as before."""
    q5 = extract_q5(df)
    out: Dict[str, float] = {}
    for task_id, g in q5.groupby("task_id"):
        mults = []
        for _, r in g.iterrows():
            status = classify_validation_strength(
                r.get("total_return"), r.get("sharpe"), r.get("max_drawdown"), r.get("win_rate"), cfg,
            )
            mult = validation_multiplier_for(status, cfg)
            if r.get("ctx_alignment_source") in (None, "none", "filename_pattern"):
                mult = min(mult, cfg.validation_multiplier.get("missing", 0.8))
            mults.append(mult)
        if mults:
            out[task_id] = min(mults)
    return out


def _contradiction_count_lookup(cases: pd.DataFrame) -> Dict[tuple, int]:
    if cases is None or cases.empty:
        return {}
    counts: Dict[tuple, int] = {}
    for _, r in cases.iterrows():
        key = (r.get("ticker"), r.get("date"))
        if key[0] is None:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _evidence_boost_lookup(df: pd.DataFrame, votes: pd.DataFrame) -> Dict[tuple, bool]:
    """(ticker, date) -> True if >=2 adapters vote the same non-zero direction
    AND their Q1/Q3 evidence atoms (reasoning / drivers / supporting_evidence)
    share at least one coarse tag. This is the only 'boost' condition — a
    single adapter's own conviction never boosts itself."""
    atoms_by_row: Dict[int, List[str]] = {}
    for idx, r in df.iterrows():
        atoms_by_row[idx] = evidence_atoms_from_record(r)

    # Re-derive which df row each vote came from, to fetch its atoms.
    q1 = extract_q1(df).reset_index().rename(columns={"index": "src_idx"})
    q3 = extract_q3(df).reset_index().rename(columns={"index": "src_idx"})

    out: Dict[tuple, bool] = {}
    for (ticker, date), g in votes.groupby(["ticker", "date"]):
        directional = g[g["signal"] != 0]
        if len(directional) < 2:
            out[(ticker, date)] = False
            continue
        for sign in (1, -1):
            same_dir = directional[directional["signal"] == sign]
            if len(same_dir) < 2:
                continue
            tagsets = []
            for _, vr in same_dir.iterrows():
                src = q1 if vr["question"] == "Q1" else q3
                match = src[(src["ticker"] == vr["ticker"]) & (src["date"] == vr["date"]) & (src["adapter"] == vr["adapter"])]
                if not match.empty:
                    tagsets.append(set(atoms_by_row.get(match.iloc[0]["src_idx"], [])))
            if len(tagsets) >= 2 and set.intersection(*tagsets):
                out[(ticker, date)] = True
                break
        else:
            out[(ticker, date)] = False
    return out


def compute_fusion_decisions(
    df: pd.DataFrame,
    cases: pd.DataFrame,
    cfg: Config,
    future_return_lookup: Optional[FutureReturnLookup] = None,
    horizon: Optional[int] = None,
) -> pd.DataFrame:
    """One row per (ticker, date) with all three methods' scores/decisions."""
    horizon = horizon or cfg.horizons[0]
    votes = _build_vote_rows(df)
    if votes.empty:
        return pd.DataFrame(columns=[
            "ticker", "date", "n_adapters_voting",
            "majority_vote_score", "majority_vote_decision",
            "confidence_weighted_score", "confidence_weighted_decision",
            "interwoven_score", "interwoven_decision",
            "risk_multiplier", "validation_multiplier", "contradiction_multiplier",
            "evidence_boost_applied", "future_return", "future_return_horizon",
        ])

    risk_lut = _risk_lookup(df, cfg)
    val_lut = _validation_lookup(df, cfg)
    contra_lut = _contradiction_count_lookup(cases)
    boost_lut = _evidence_boost_lookup(df, votes)

    q4 = extract_q4(df)
    task_by_ticker_date: Dict[tuple, str] = {}
    q1_task = extract_q1(df)
    for _, r in q1_task.iterrows():
        task_by_ticker_date[(r["ticker"], r["date"])] = r["task_id"]
    for _, r in extract_q3(df).iterrows():
        task_by_ticker_date.setdefault((r["ticker"], r["date"]), r["task_id"])

    rows = []
    for (ticker, date), g in votes.groupby(["ticker", "date"]):
        signals = g["signal"].to_numpy()

        # A. majority_vote — unweighted sign of the vote sum
        majority_score = float(np.sign(signals.sum())) if len(signals) else 0.0
        majority_decision = score_to_decision(majority_score, cfg)

        # B. confidence_weighted_vote
        weights = g["weight_raw"].fillna(cfg.default_missing_confidence).to_numpy(dtype=float)
        weight_sum = weights.sum()
        cw_score = float((signals * weights).sum() / weight_sum) if weight_sum else 0.0
        cw_decision = score_to_decision(cw_score, cfg)

        # C. interwoven_calibrated_fusion
        risk_mult = risk_lut.get((ticker, date), 1.0)
        task_id = task_by_ticker_date.get((ticker, date))
        val_mult = val_lut.get(task_id, cfg.validation_multiplier["missing"])
        n_flags = contra_lut.get((ticker, date), 0)
        contra_mult = contradiction_multiplier_for(n_flags, cfg)
        boosted = bool(boost_lut.get((ticker, date), False))
        boost_mult = 1.10 if boosted else 1.0

        interwoven_raw = cw_score * risk_mult * val_mult * contra_mult * boost_mult
        interwoven_score = float(np.clip(interwoven_raw, -1.0, 1.0))
        interwoven_decision = score_to_decision(interwoven_score, cfg)

        future_return = None
        if future_return_lookup is not None:
            try:
                future_return = future_return_lookup(ticker, date, horizon)
            except Exception:
                future_return = None

        rows.append({
            "ticker": ticker, "date": date, "n_adapters_voting": g["adapter"].nunique(),
            "majority_vote_score": majority_score, "majority_vote_decision": majority_decision,
            "confidence_weighted_score": cw_score, "confidence_weighted_decision": cw_decision,
            "interwoven_score": interwoven_score, "interwoven_decision": interwoven_decision,
            "risk_multiplier": risk_mult, "validation_multiplier": val_mult,
            "contradiction_multiplier": contra_mult, "evidence_boost_applied": boosted,
            "future_return": future_return, "future_return_horizon": horizon,
            "any_confidence_defaulted": bool(g["weight_is_default"].any()),
        })
    return pd.DataFrame(rows)


def build_fusion_ablation_results(decisions: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Per method: decision distribution, disagreement/agreement with the
    other two methods, and — only if realized returns exist — hit_rate /
    avg_forward_return / sharpe / max_drawdown / turnover / false_positive_rate."""
    methods = {
        "majority_vote": ("majority_vote_score", "majority_vote_decision"),
        "confidence_weighted_vote": ("confidence_weighted_score", "confidence_weighted_decision"),
        "interwoven_calibrated_fusion": ("interwoven_score", "interwoven_decision"),
    }
    sign_map = {"BUY": 1, "HOLD": 0, "SELL": -1}
    rows = []
    for method, (score_col, decision_col) in methods.items():
        if decisions.empty or decision_col not in decisions.columns:
            rows.append({"method": method, "coverage": 0, "insufficient_data": True,
                         "reason": "no (ticker, date) groups with at least one Q1/Q3 vote"})
            continue

        dist = decision_distribution(decisions[decision_col])
        m = decisions.assign(signal=decisions[decision_col].map(sign_map))
        return_metrics = compute_return_based_metrics(m[["signal", "future_return", "ticker", "date"]])

        row = {
            "method": method,
            "n_ticker_date_groups": len(decisions),
            "pct_buy": dist.get("BUY", 0.0), "pct_hold": dist.get("HOLD", 0.0), "pct_sell": dist.get("SELL", 0.0),
        }
        row.update(return_metrics)
        rows.append(row)

    pairs = [("majority_vote", "confidence_weighted_vote"),
             ("confidence_weighted_vote", "interwoven_calibrated_fusion"),
             ("majority_vote", "interwoven_calibrated_fusion")]
    pairwise_stability: Dict[str, float] = {}
    if not decisions.empty:
        idx = pd.MultiIndex.from_frame(decisions[["ticker", "date"]])
        series = {
            "majority_vote": pd.Series(decisions["majority_vote_decision"].values, index=idx),
            "confidence_weighted_vote": pd.Series(decisions["confidence_weighted_decision"].values, index=idx),
            "interwoven_calibrated_fusion": pd.Series(decisions["interwoven_decision"].values, index=idx),
        }
        for a, b in pairs:
            pairwise_stability[f"{a}_vs_{b}"] = decision_stability(series[a], series[b])

    results = pd.DataFrame(rows)
    if not results.empty:
        def _avg_stability_for(method: str) -> float:
            vals = [v for k, v in pairwise_stability.items() if method in k.split("_vs_")]
            vals = [v for v in vals if v == v]  # drop NaN
            return float(np.mean(vals)) if vals else float("nan")
        results["decision_stability_vs_other_methods"] = results["method"].apply(_avg_stability_for)
        for pair_name, val in pairwise_stability.items():
            results[f"pairwise_stability::{pair_name}"] = val
    return results


def explain_case(
    df: pd.DataFrame,
    cases: pd.DataFrame,
    cfg: Config,
    ticker: str,
    date: str,
    future_return_lookup: Optional[FutureReturnLookup] = None,
    horizon: Optional[int] = None,
) -> Dict:
    """Step-by-step breakdown of the interwoven fusion score for one
    (ticker, date), reused by fig_13's waterfall chart and by the case-study
    markdown files. Returns None-safe defaults when the ticker/date pair has
    no votes at all."""
    horizon = horizon or cfg.horizons[0]
    votes = _build_vote_rows(df)
    g = votes[(votes["ticker"] == ticker) & (votes["date"] == date)]
    if g.empty:
        return {"ticker": ticker, "date": date, "found": False}

    signals = g["signal"].to_numpy()
    majority_score = float(np.sign(signals.sum())) if len(signals) else 0.0
    weights = g["weight_raw"].fillna(cfg.default_missing_confidence).to_numpy(dtype=float)
    weight_sum = weights.sum()
    cw_score = float((signals * weights).sum() / weight_sum) if weight_sum else 0.0

    risk_lut = _risk_lookup(df, cfg)
    val_lut = _validation_lookup(df, cfg)
    contra_lut = _contradiction_count_lookup(cases)
    boost_lut = _evidence_boost_lookup(df, votes)

    q1_task = extract_q1(df)
    task_id = None
    match = q1_task[(q1_task["ticker"] == ticker) & (q1_task["date"] == date)]
    if not match.empty:
        task_id = match.iloc[0]["task_id"]
    else:
        match3 = extract_q3(df)
        match3 = match3[(match3["ticker"] == ticker) & (match3["date"] == date)]
        if not match3.empty:
            task_id = match3.iloc[0]["task_id"]

    risk_mult = risk_lut.get((ticker, date), 1.0)
    val_mult = val_lut.get(task_id, cfg.validation_multiplier["missing"])
    n_flags = contra_lut.get((ticker, date), 0)
    contra_mult = contradiction_multiplier_for(n_flags, cfg)
    boosted = bool(boost_lut.get((ticker, date), False))
    boost_mult = 1.10 if boosted else 1.0

    after_risk = cw_score * risk_mult
    after_val = after_risk * val_mult
    after_contra = after_val * contra_mult
    final_score = float(np.clip(after_contra * boost_mult, -1.0, 1.0))

    flags_here = []
    if cases is not None and not cases.empty:
        flags_here = cases[(cases["ticker"] == ticker) & (cases["date"] == date)]["flag"].tolist()

    future_return = None
    if future_return_lookup is not None:
        try:
            future_return = future_return_lookup(ticker, date, horizon)
        except Exception:
            future_return = None

    return {
        "ticker": ticker, "date": date, "found": True,
        "votes": g.to_dict(orient="records"),
        "majority_score": majority_score, "majority_decision": score_to_decision(majority_score, cfg),
        "confidence_weighted_score": cw_score, "confidence_weighted_decision": score_to_decision(cw_score, cfg),
        "risk_multiplier": risk_mult, "after_risk": after_risk,
        "validation_multiplier": val_mult, "after_validation": after_val,
        "contradiction_multiplier": contra_mult, "n_contradiction_flags": n_flags, "after_contradiction": after_contra,
        "evidence_boost_applied": boosted, "boost_multiplier": boost_mult,
        "final_score": final_score, "final_decision": score_to_decision(final_score, cfg),
        "contradiction_flags": flags_here,
        "future_return": future_return, "future_return_horizon": horizon,
    }
