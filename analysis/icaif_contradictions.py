"""
analysis/icaif_contradictions.py — Experiment 4: cross-agent contradiction
detection (rules 1-8 from the ICAIF experiment spec).

Alignment reality check, stated up front because it drives every rule below:
  - Q1Decision and Q2Sentiment both carry `ticker` + `date` -> can be joined
    exactly on (ticker, date), across adapters.
  - Q3Signal also carries `ticker` + `date` -> same exact join.
  - Q4Portfolio carries `date` but NOT `ticker` (weights is a dict keyed by
    ticker, but the envelope itself is portfolio-level).
  - Q5Backtest carries NEITHER `ticker` NOR `date` in CONTRACT/schemas.py —
    only `adapter` + whatever task_id the file was written under.

So rules that only touch Q1/Q2/Q3 (1, 4, 6, 7, 8) are exact (ticker, date)
joins, genuinely cross-agent. Rules that touch Q4 (3, 5) or Q5 (2, 5) are
best-effort: joined on (date, task_id) or task_id alone, which conflates
"same comparison run" with "same ticker" and "same time". This is a
limitation of the current CONTRACT schema, not a bug in this module — it is
reported as such in every output and in PAPER_FINDINGS.md, never silently
tightened or silently ignored.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from analysis.icaif_metrics import Config, classify_validation_strength

RULE_LIMITATIONS = {
    "BUY_WITH_HIGH_RISK": "exact (ticker, date) join across Q1/Q2 — no approximation.",
    "LONG_WITH_WEAK_VALIDATION": (
        "Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on "
        "task_id only: 'this adapter's LONG signal for ticker X' is compared "
        "against 'some Q5 backtest reported in the same comparison run', which "
        "may not be the same strategy or period."
    ),
    "POSITIVE_SENTIMENT_BEAR_REGIME": (
        "Q4Portfolio has no ticker field. Joined on (date, task_id): a "
        "portfolio-level BEAR regime call from one adapter is compared against "
        "per-ticker sentiment from any adapter on the same date."
    ),
    "HIGH_CONFIDENCE_POOR_CALIBRATION": "uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.",
    "HIGH_WEIGHT_HIGH_DRAWDOWN": (
        "Q4Portfolio and Q5Backtest are joined on task_id only (neither carries "
        "both ticker and date). 'high weight on ticker X' and 'severe drawdown' "
        "may come from unrelated adapters/strategies in the same run."
    ),
    "STRONG_SIGNAL_MISSING_EVIDENCE": "single-record check, no join, no approximation.",
    "ACTION_ALPHA_DIRECTION_CONFLICT": "exact (ticker, date) join across Q1/Q3 — no approximation.",
}


# --------------------------------------------------------------------------- #
# Per-question extraction from the flattened records dataframe
# --------------------------------------------------------------------------- #

def _extract(df: pd.DataFrame, q: str, cols: List[str]) -> pd.DataFrame:
    present = f"{q}_present"
    if present not in df.columns:
        return pd.DataFrame(columns=["adapter", "ticker", "date", "task_id"] + cols)
    sub = df[df[present] == True].copy()  # noqa: E712
    keep = ["adapter", "ticker", "date", "task_id"] + [f"{q}_{c}" for c in cols]
    keep = [c for c in keep if c in sub.columns]
    sub = sub[keep].rename(columns={f"{q}_{c}": c for c in cols})
    return sub


def extract_q1(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q1", ["action", "confidence", "reasoning"])


def extract_q2(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q2", ["sentiment_score", "risk_level"])


def extract_q3(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q3", ["direction", "strength", "supporting_evidence"])


def extract_q4(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q4", ["weights", "regime", "cash_ratio"])


def extract_q5(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q5", ["total_return", "sharpe", "max_drawdown", "win_rate"])


def _norm(flag: str, rows: pd.DataFrame, ticker_col=None, date_col=None,
          task_col="task_id", adapter_cols=(), detail_fn=None) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=["flag", "ticker", "date", "task_id", "adapters_involved", "detail"])
    out = pd.DataFrame({
        "flag": flag,
        "ticker": rows[ticker_col] if ticker_col and ticker_col in rows.columns else None,
        "date": rows[date_col] if date_col and date_col in rows.columns else None,
        "task_id": rows[task_col] if task_col in rows.columns else None,
    })
    adapters = []
    for _, r in rows.iterrows():
        names = sorted({str(r[c]) for c in adapter_cols if c in rows.columns and pd.notna(r.get(c))})
        adapters.append(",".join(names))
    out["adapters_involved"] = adapters
    out["detail"] = [detail_fn(r) for _, r in rows.iterrows()] if detail_fn else ""
    out["limitation"] = RULE_LIMITATIONS.get(flag, "")
    return out


# --------------------------------------------------------------------------- #
# Rules 1-8
# --------------------------------------------------------------------------- #

def rule_buy_with_high_risk(q1: pd.DataFrame, q2: pd.DataFrame) -> pd.DataFrame:
    if q1.empty or q2.empty:
        return pd.DataFrame()
    merged = q1[q1["action"] == "BUY"].merge(
        q2[q2["risk_level"].isin(["HIGH", "EXTREME"])],
        on=["ticker", "date"], suffixes=("_q1", "_q2"),
    )
    return _norm(
        "BUY_WITH_HIGH_RISK", merged, "ticker", "date",
        adapter_cols=["adapter_q1", "adapter_q2"],
        detail_fn=lambda r: f"{r['adapter_q1']} says BUY on {r['ticker']}/{r['date']}; "
                             f"{r['adapter_q2']} reports risk_level={r['risk_level']}",
    )


def rule_long_with_weak_validation(q3: pd.DataFrame, q5: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q3.empty or q5.empty:
        return pd.DataFrame()
    q5 = q5.copy()
    q5["validation_status"] = q5.apply(
        lambda r: classify_validation_strength(
            r.get("total_return"), r.get("sharpe"), r.get("max_drawdown"), r.get("win_rate"), cfg
        ), axis=1,
    )
    weak = q5[q5["validation_status"].isin(["weak", "fail"])]
    if weak.empty:
        return pd.DataFrame()
    merged = q3[q3["direction"] == "LONG"].merge(weak, on="task_id", suffixes=("_q3", "_q5"))
    # "ticker" and "date" exist on both sides (q5's copies are all-None, since
    # Q5Backtest has neither field — see module docstring) so merging on
    # task_id alone suffixes every overlapping column, not just date. Resolve
    # both defensively rather than assuming either survives unsuffixed.
    ticker_col = "ticker_q3" if "ticker_q3" in merged.columns else "ticker"
    date_col = "date_q3" if "date_q3" in merged.columns else "date"
    return _norm(
        "LONG_WITH_WEAK_VALIDATION", merged, ticker_col, date_col,
        adapter_cols=["adapter_q3", "adapter_q5"],
        detail_fn=lambda r: f"{r['adapter_q3']} LONG on {r[ticker_col]}; {r['adapter_q5']} "
                             f"validation_status={r['validation_status']} (task {r['task_id']})",
    )


def rule_positive_sentiment_bear_regime(q2: pd.DataFrame, q4: pd.DataFrame) -> pd.DataFrame:
    if q2.empty or q4.empty:
        return pd.DataFrame()
    bear = q4[q4["regime"] == "BEAR"]
    if bear.empty:
        return pd.DataFrame()
    merged = q2[q2["sentiment_score"] > 0].merge(bear, on=["date", "task_id"], suffixes=("_q2", "_q4"))
    # "date" is a merge key so it survives unsuffixed; "ticker" is not a merge
    # key (q4 has no meaningful ticker) but exists on both sides, so it DOES
    # get suffixed — resolve defensively rather than assume "ticker" survives.
    ticker_col = "ticker_q2" if "ticker_q2" in merged.columns else "ticker"
    return _norm(
        "POSITIVE_SENTIMENT_BEAR_REGIME", merged, ticker_col, "date",
        adapter_cols=["adapter_q2", "adapter_q4"],
        detail_fn=lambda r: f"{r['adapter_q2']} sentiment={r['sentiment_score']:.2f} on {r[ticker_col]}/{r['date']}; "
                             f"{r['adapter_q4']} regime=BEAR",
    )


def rule_high_confidence_poor_calibration(q1: pd.DataFrame, overconfidence_flags: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q1.empty or overconfidence_flags is None or overconfidence_flags.empty:
        return pd.DataFrame()
    q1_flags = overconfidence_flags[overconfidence_flags["question"] == "Q1"] if "question" in overconfidence_flags.columns else overconfidence_flags
    poor_adapters = set(q1_flags["adapter"].unique())
    hc = q1[(q1["confidence"] >= cfg.high_confidence_threshold) & (q1["adapter"].isin(poor_adapters))]
    if hc.empty:
        return pd.DataFrame()
    return _norm(
        "HIGH_CONFIDENCE_POOR_CALIBRATION", hc, "ticker", "date",
        adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} confidence={r['confidence']:.2f} on {r['ticker']}/{r['date']}, "
                             f"but is flagged overconfident historically",
    )


def rule_high_weight_high_drawdown(q4: pd.DataFrame, q5: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q4.empty or q5.empty:
        return pd.DataFrame()
    exploded = []
    for _, r in q4.iterrows():
        weights = r.get("weights") or {}
        if not isinstance(weights, dict):
            continue
        for ticker, w in weights.items():
            if w is not None and w >= cfg.high_weight_threshold:
                exploded.append({"adapter": r["adapter"], "task_id": r["task_id"], "date": r["date"],
                                  "ticker": ticker, "weight": w})
    if not exploded:
        return pd.DataFrame()
    q4_high = pd.DataFrame(exploded)
    severe = q5[q5["max_drawdown"] <= cfg.severe_drawdown_threshold]
    if severe.empty:
        return pd.DataFrame()
    merged = q4_high.merge(severe, on="task_id", suffixes=("_q4", "_q5"))
    # task_id is the only merge key; q4_high's real ticker/date and q5's
    # all-None ticker/date both survive as columns, so both get suffixed.
    ticker_col = "ticker_q4" if "ticker_q4" in merged.columns else "ticker"
    date_col = "date_q4" if "date_q4" in merged.columns else "date"
    return _norm(
        "HIGH_WEIGHT_HIGH_DRAWDOWN", merged, ticker_col, date_col,
        adapter_cols=["adapter_q4", "adapter_q5"],
        detail_fn=lambda r: f"{r['adapter_q4']} allocates weight={r['weight']:.2f} to {r[ticker_col]}; "
                             f"{r['adapter_q5']} reports max_drawdown={r['max_drawdown']:.2f}",
    )


def rule_strong_signal_missing_evidence(q3: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q3.empty:
        return pd.DataFrame()

    def _missing(ev) -> bool:
        if not isinstance(ev, list) or len(ev) == 0:
            return True
        return all((not isinstance(x, str)) or (not x.strip()) for x in ev)

    matches = q3[(q3["strength"] >= cfg.strong_signal_strength_min) & (q3["supporting_evidence"].apply(_missing))]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "STRONG_SIGNAL_MISSING_EVIDENCE", matches, "ticker", "date",
        adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} strength={r['strength']:.2f} on {r['ticker']}/{r['date']} "
                             f"with no supporting_evidence",
    )


def rule_action_alpha_direction_conflict(q1: pd.DataFrame, q3: pd.DataFrame) -> pd.DataFrame:
    if q1.empty or q3.empty:
        return pd.DataFrame()
    merged = q1.merge(q3, on=["ticker", "date"], suffixes=("_q1", "_q3"))
    if merged.empty:
        return pd.DataFrame()

    def _conflict(r) -> bool:
        return (r["action"] == "BUY" and r["direction"] == "SHORT") or \
               (r["action"] == "SELL" and r["direction"] == "LONG")

    matches = merged[merged.apply(_conflict, axis=1)]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "ACTION_ALPHA_DIRECTION_CONFLICT", matches, "ticker", "date",
        adapter_cols=["adapter_q1", "adapter_q3"],
        detail_fn=lambda r: f"{r['adapter_q1']} action={r['action']} vs {r['adapter_q3']} direction={r['direction']} "
                             f"on {r['ticker']}/{r['date']}",
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def detect_contradictions(
    df: pd.DataFrame,
    overconfidence_flags: pd.DataFrame,
    cfg: Config,
) -> Dict[str, pd.DataFrame]:
    q1, q2, q3 = extract_q1(df), extract_q2(df), extract_q3(df)
    q4, q5 = extract_q4(df), extract_q5(df)

    cases = pd.concat([
        rule_buy_with_high_risk(q1, q2),
        rule_long_with_weak_validation(q3, q5, cfg),
        rule_positive_sentiment_bear_regime(q2, q4),
        rule_high_confidence_poor_calibration(q1, overconfidence_flags, cfg),
        rule_high_weight_high_drawdown(q4, q5, cfg),
        rule_strong_signal_missing_evidence(q3, cfg),
        rule_action_alpha_direction_conflict(q1, q3),
    ], ignore_index=True) if any([not q1.empty, not q2.empty, not q3.empty, not q4.empty, not q5.empty]) else pd.DataFrame(
        columns=["flag", "ticker", "date", "task_id", "adapters_involved", "detail", "limitation"]
    )

    if cases.empty:
        summary = pd.DataFrame(columns=["flag", "count", "limitation"])
    else:
        summary = (
            cases.groupby("flag")
            .agg(count=("flag", "size"))
            .reset_index()
        )
        summary["limitation"] = summary["flag"].map(RULE_LIMITATIONS)

    return {"cases": cases, "summary": summary}


def build_outcome_comparison(cases: pd.DataFrame, df_hits: pd.DataFrame) -> pd.DataFrame:
    """Compares realized forward returns/hit-rate for records that triggered
    >=1 contradiction flag vs records that triggered none. Only meaningful for
    the rules with an exact (ticker, date) key (1, 4, 6, 7, 8) — rules 2/3/5
    can't be traced back to one specific (adapter, ticker, date, question)
    record given the current schema, so they are excluded here and that
    exclusion is stated in the output, not silently done."""
    cols = ["group", "n_samples", "hit_rate", "avg_forward_return", "insufficient_data"]
    if df_hits is None or df_hits.empty:
        return pd.DataFrame([
            {"group": "flagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
            {"group": "unflagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
        ], columns=cols)

    if cases.empty:
        flagged_keys = set()
    else:
        exact_rules = {"BUY_WITH_HIGH_RISK", "HIGH_CONFIDENCE_POOR_CALIBRATION",
                        "STRONG_SIGNAL_MISSING_EVIDENCE", "ACTION_ALPHA_DIRECTION_CONFLICT"}
        exact_cases = cases[cases["flag"].isin(exact_rules)]
        flagged_keys = set(zip(exact_cases["ticker"], exact_cases["date"]))

    d = df_hits.dropna(subset=["hit"]).copy()
    if d.empty:
        return pd.DataFrame([
            {"group": "flagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
            {"group": "unflagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
        ], columns=cols)

    d["is_flagged"] = d.apply(lambda r: (r.get("ticker"), r.get("date")) in flagged_keys, axis=1)
    rows = []
    for is_flagged, g in d.groupby("is_flagged"):
        rows.append({
            "group": "flagged" if is_flagged else "unflagged",
            "n_samples": len(g),
            "hit_rate": float(g["hit"].mean()),
            "avg_forward_return": float(g["future_return"].mean()),
            "insufficient_data": False,
        })
    present = {r["group"] for r in rows}
    for missing in ({"flagged", "unflagged"} - present):
        rows.append({"group": missing, "n_samples": 0, "hit_rate": np.nan,
                      "avg_forward_return": np.nan, "insufficient_data": True})
    return pd.DataFrame(rows, columns=cols)
