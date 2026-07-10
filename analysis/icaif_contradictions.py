"""
analysis/icaif_contradictions.py — Experiment 4: cross-agent contradiction
detection framework.

19 rules across 5 categories (cross_question, intra_record, evidence,
calibration, temporal), each registered in RULE_REGISTRY with its category,
alignment tier, input fields, atoms used, severity, and limitation text — one
source of truth that drives the CSV `limitation`/`category`/`severity`
columns AND the auto-generated `contradiction_rulebook.md`, so the two can
never drift apart.

Alignment reality check — the reason `alignment_confidence` has 5 raw values
(single_record, exact, context_exact, best_effort, low_confidence; the
summary rolls single_record into "exact" since neither has join ambiguity):
  - Q1Decision, Q2Sentiment, Q3Signal all carry `ticker` + `date` -> exact
    (ticker, date) joins across adapters ("exact").
  - Q4Portfolio carries `date` but NOT `ticker`; Q5Backtest carries NEITHER
    ticker NOR date in CONTRACT/schemas.py (read-only — left untouched this
    session per explicit instruction).
  - `analysis.icaif_alignment.recover_context` recovers REAL (never
    fabricated) decision_date/universe/window context for these records
    from index.csv (tier 1, high confidence), the task_id
    f"{batch_id}__{date}" naming convention (tier 2, medium confidence), or
    the legacy `{adapter}__{ticker}.json` filename convention (tier 3, low
    confidence) — see that module's docstring for the full fallback chain.
  - A best-effort (Q4/Q5-touching) rule upgrades to "context_exact" when
    the recovered context is high/medium confidence AND the ticker under
    test is a confirmed member of that batch's known universe; it stays
    "best_effort" when context exists but is weaker/unconfirmed, and drops
    to "low_confidence" when no context could be recovered at all (task_id
    string matching only, e.g. the legacy comparison_2026-07-02 batch).
  - Single-record ("intra_record"/most "evidence") rules need no join at
    all, so they get alignment_confidence="single_record".
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from analysis.icaif_metrics import (
    BEARISH_WORDS,
    BULLISH_WORDS,
    Config,
    classify_validation_strength,
    evidence_atoms_from_record,
    risk_atoms_from_record,
    validation_atoms_from_record,
)

# --------------------------------------------------------------------------- #
# Rule registry — single source of truth for category/alignment/severity/
# input fields/atoms/limitation text. Every rule function below looks up its
# own metadata here instead of repeating it inline, so contradiction_cases.csv
# and contradiction_rulebook.md can never disagree with each other.
# --------------------------------------------------------------------------- #

RULE_REGISTRY: Dict[str, dict] = {
    "BUY_WITH_HIGH_RISK": {
        "category": "cross_question", "alignment": "exact_join", "severity": "high",
        "input_fields": ["q1.action", "q2.risk_level"], "atoms_used": [],
        "description": "Q1 BUY on (ticker, date) while another adapter's Q2 reports HIGH/EXTREME risk_level for the same (ticker, date).",
        "limitation": "exact (ticker, date) join across Q1/Q2 — no approximation.",
    },
    "LONG_WITH_WEAK_VALIDATION": {
        "category": "cross_question", "alignment": "best_effort", "severity": "medium",
        "input_fields": ["q3.direction", "q5.total_return", "q5.sharpe", "q5.max_drawdown", "q5.win_rate"], "atoms_used": [],
        "description": "Q3 LONG paired with a same-batch Q5 backtest classified weak/fail by classify_validation_strength.",
        "limitation": "Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id "
                       "(upgraded to context_exact when analysis/icaif_alignment.py confirms the ticker is a "
                       "member of the batch's known portfolio_universe) — never a guarantee the Q5 backtest "
                       "is really about this adapter's strategy for this ticker.",
    },
    "POSITIVE_SENTIMENT_BEAR_REGIME": {
        "category": "cross_question", "alignment": "best_effort", "severity": "low",
        "input_fields": ["q2.sentiment_score", "q4.regime"], "atoms_used": [],
        "description": "Q2 sentiment_score > 0 paired with a same-date Q4 regime=BEAR.",
        "limitation": "Q4Portfolio has no ticker field. Joined on (date, task_id) — a portfolio-level "
                       "regime call is compared against per-ticker sentiment from any adapter on the same date.",
    },
    "HIGH_WEIGHT_HIGH_DRAWDOWN": {
        "category": "cross_question", "alignment": "best_effort", "severity": "high",
        "input_fields": ["q4.weights", "q5.max_drawdown"], "atoms_used": [],
        "description": "Q4 allocates >=high_weight_threshold to a ticker while a same-batch Q5 reports severe max_drawdown.",
        "limitation": "Q4Portfolio and Q5Backtest are joined on task_id only (neither carries both ticker "
                       "and date) — upgraded to universe-confirmed when the ticker is in the batch's known universe.",
    },
    "ACTION_ALPHA_DIRECTION_CONFLICT": {
        "category": "cross_question", "alignment": "exact_join", "severity": "medium",
        "input_fields": ["q1.action", "q3.direction"], "atoms_used": [],
        "description": "Q1 BUY vs Q3 SHORT, or Q1 SELL vs Q3 LONG, on the same (ticker, date) — same adapter or cross-adapter.",
        "limitation": "exact (ticker, date) join across Q1/Q3 — no approximation.",
    },
    "SENTIMENT_RISK_INTRA_CONFLICT": {
        "category": "intra_record", "alignment": "single_record", "severity": "medium",
        "input_fields": ["q2.sentiment_score", "q2.risk_level"], "atoms_used": [],
        "description": "A single Q2 record reports sentiment_score > 0 while also reporting risk_level=EXTREME.",
        "limitation": "single-record check, no join, no approximation.",
    },
    "DIRECTION_RETURN_INTRA_CONFLICT": {
        "category": "intra_record", "alignment": "single_record", "severity": "medium",
        "input_fields": ["q3.direction", "q3.expected_return"], "atoms_used": [],
        "description": "A single Q3 record reports direction=LONG with expected_return<0, or direction=SHORT with expected_return>0.",
        "limitation": "single-record check, no join, no approximation.",
    },
    "BULL_REGIME_HIGH_CASH": {
        "category": "intra_record", "alignment": "single_record", "severity": "medium",
        "input_fields": ["q4.regime", "q4.cash_ratio"], "atoms_used": [],
        "description": "A single Q4 record reports regime=BULL while also holding a cash_ratio >= intra_record_high_cash_in_bull.",
        "limitation": "single-record check, no join, no approximation.",
    },
    "POSITIVE_RETURN_WEAK_RISK_ADJUSTED": {
        "category": "intra_record", "alignment": "single_record", "severity": "high",
        "input_fields": ["q5.total_return", "q5.sharpe", "q5.max_drawdown"], "atoms_used": [],
        "description": "A single Q5 record reports total_return>0 but sharpe below intra_record_weak_risk_adjusted_sharpe "
                       "AND max_drawdown at or beyond intra_record_weak_risk_adjusted_drawdown.",
        "limitation": "single-record check, no join, no approximation.",
    },
    "STRONG_SIGNAL_MISSING_EVIDENCE": {
        "category": "evidence", "alignment": "single_record", "severity": "low",
        "input_fields": ["q3.strength", "q3.supporting_evidence"], "atoms_used": [],
        "description": "Q3 strength >= strong_signal_strength_min with an empty/missing supporting_evidence list.",
        "limitation": "single-record check, no join, no approximation.",
    },
    "HEADLINE_EVIDENCE_MISMATCH": {
        "category": "evidence", "alignment": "single_record", "severity": "medium",
        "input_fields": ["q1.action", "q1.reasoning", "q3.direction", "q3.supporting_evidence"], "atoms_used": [],
        "description": "A bullish headline (BUY/LONG) whose own reasoning/evidence text is keyword-dominated by "
                       "bearish language, or a bearish headline dominated by bullish language.",
        "limitation": "keyword-heuristic text valence check (BEARISH_WORDS/BULLISH_WORDS), not semantic "
                       "understanding — see icaif_metrics.py.",
    },
    "SAME_DIRECTION_ZERO_ATOM_OVERLAP": {
        "category": "evidence", "alignment": "exact_join", "severity": "low",
        "input_fields": ["q1.action", "q3.direction"], "atoms_used": ["evidence_atoms"],
        "description": ">=2 adapters agree on direction for the same (ticker, date) but share zero evidence-atom tags.",
        "limitation": "exact (ticker, date) join; evidence atoms are a coarse 12-tag keyword vocabulary, not NLU.",
    },
    "OPPOSITE_DIRECTION_ATOM_OVERLAP": {
        "category": "evidence", "alignment": "exact_join", "severity": "medium",
        "input_fields": ["q1.action", "q3.direction"], "atoms_used": ["evidence_atoms"],
        "description": "Adapters disagree on direction for the same (ticker, date) yet share >=1 evidence-atom tag — "
                       "they're reasoning about the same topic and still reaching opposite conclusions.",
        "limitation": "exact (ticker, date) join; evidence atoms are a coarse 12-tag keyword vocabulary, not NLU.",
    },
    "RISK_ATOMS_BUT_BULLISH_HEADLINE": {
        "category": "evidence", "alignment": "single_record", "severity": "high",
        "input_fields": ["q1.action", "q3.direction"], "atoms_used": ["risk_atoms"],
        "description": "A record's own risk_atoms include a severe-risk tag (risk_level:EXTREME, severe_drawdown, "
                       "or risk_language_in_reasoning) while its headline is still BUY/LONG.",
        "limitation": "single-record check; risk_atoms themselves may draw on other Q's fields for the same "
                       "(ticker, date) — see risk_atoms_from_record in icaif_metrics.py.",
    },
    "VALIDATION_FAIL_BUT_STRONG_BULLISH": {
        "category": "evidence", "alignment": "best_effort", "severity": "high",
        "input_fields": ["q3.direction", "q3.strength", "q1.action", "q1.confidence"], "atoms_used": ["validation_atoms"],
        "description": "A same-batch Q5 record's validation_atoms indicate validation_status:fail while a strong "
                       "bullish Q1/Q3 signal exists (confidence/strength >= high_confidence_threshold).",
        "limitation": "Q5Backtest has no ticker/date field — joined on task_id, upgraded to universe-confirmed "
                       "when possible, same limitation as LONG_WITH_WEAK_VALIDATION.",
    },
    "HIGH_CONFIDENCE_POOR_CALIBRATION": {
        "category": "calibration", "alignment": "exact_join", "severity": "high",
        "input_fields": ["q1.confidence"], "atoms_used": [],
        "description": "Q1 confidence >= high_confidence_threshold from an adapter formally flagged overconfident "
                       "(Experiment 3's overconfidence_flags.csv: avg_confidence/hit_rate/sample_count gated).",
        "limitation": "uses Experiment 3's overconfidence flags per (adapter, question, horizon) — no ticker/date approximation beyond that.",
    },
    "CONFIDENCE_IN_POOR_CALIBRATION_BUCKET": {
        "category": "calibration", "alignment": "exact_join", "severity": "high",
        "input_fields": ["q1.confidence", "q3.strength"], "atoms_used": [],
        "description": "A record's own confidence/strength falls into a calibration bucket (adapter, question, "
                       "horizon) whose calibration_error >= calibration_bucket_poor_error — catches adapters "
                       "whose poor bucket has too few samples to trip the formally-gated overconfidence flag.",
        "limitation": "exact join on (adapter, question, confidence bucket) against Experiment 3's calibration_table.csv; "
                       "small buckets (see fig_16) make this noisier than HIGH_CONFIDENCE_POOR_CALIBRATION.",
    },
    "SYSTEMATIC_OVERCONFIDENCE": {
        "category": "calibration", "alignment": "exact_join", "severity": "high",
        "input_fields": ["q1.confidence", "q3.strength"], "atoms_used": [],
        "description": "An adapter is formally flagged overconfident at >= systematic_overconfidence_min_horizons "
                       "distinct horizons — every high-confidence record from that adapter is flagged.",
        "limitation": "adapter-level pattern from Experiment 3's overconfidence_flags.csv, applied to every "
                       "qualifying record from that adapter — not a per-record independent check.",
    },
    "TEMPORAL_FLIP_UNEXPLAINED": {
        "category": "temporal", "alignment": "best_effort", "severity": "medium",
        "input_fields": ["q1.action", "q3.direction", "date"], "atoms_used": [],
        "description": "Same adapter, same ticker, flips BUY->SELL/LONG->SHORT (or reverse) within "
                       "temporal_window_days, with no Q2/Q4/Q5 record in that window suggesting a regime, "
                       "risk, or validation change that would explain it.",
        "limitation": "best-effort: only checks whether *any* Q2/Q4/Q5 record exists in the window with a "
                       "different risk_level/regime/validation_status, not that it *caused* the flip — and can't "
                       "distinguish a genuine signal change from adapter-side non-determinism (see deepalpha's "
                       "own same-day self-contradiction, found via ACTION_ALPHA_DIRECTION_CONFLICT).",
    },
}

EXACT_RULES = {name for name, meta in RULE_REGISTRY.items() if meta["alignment"] == "exact_join"}
SINGLE_RECORD_RULES = {name for name, meta in RULE_REGISTRY.items() if meta["alignment"] == "single_record"}
BEST_EFFORT_RULES = {name for name, meta in RULE_REGISTRY.items() if meta["alignment"] == "best_effort"}


# --------------------------------------------------------------------------- #
# Per-question extraction from the flattened records dataframe
# --------------------------------------------------------------------------- #

from analysis.icaif_alignment import CTX_FIELDS

_BASE_COLS = ["adapter", "ticker", "date", "task_id"] + CTX_FIELDS


def _extract(df: pd.DataFrame, q: str, cols: List[str]) -> pd.DataFrame:
    """Always returns every column in _BASE_COLS + cols, even when the
    underlying df never populated a given q{n}_{field} key at all (e.g. no
    record in this df ever answered this question) — callers must be able
    to safely reference e.g. q3["direction"] on an empty-but-shaped result
    without a KeyError, only an empty/False mask."""
    present = f"{q}_present"
    if present not in df.columns:
        return pd.DataFrame(columns=_BASE_COLS + cols)
    sub = df[df[present] == True].copy()  # noqa: E712
    keep = _BASE_COLS + [f"{q}_{c}" for c in cols]
    keep = [c for c in keep if c in sub.columns]
    sub = sub[keep].rename(columns={f"{q}_{c}": c for c in cols})
    for c in _BASE_COLS + cols:
        if c not in sub.columns:
            sub[c] = None
    return sub


def extract_q1(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q1", ["action", "confidence", "reasoning"])


def extract_q2(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q2", ["sentiment_score", "risk_level"])


def extract_q3(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q3", ["direction", "strength", "supporting_evidence", "expected_return"])


def extract_q4(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q4", ["weights", "regime", "cash_ratio"])


def extract_q5(df: pd.DataFrame) -> pd.DataFrame:
    return _extract(df, "q5", ["total_return", "sharpe", "max_drawdown", "win_rate"])


def _ticker_in_universe(ticker: Optional[str], universe: Optional[List[str]]) -> bool:
    if not ticker or not isinstance(universe, list):
        return False
    return ticker in universe


def _get_suffixed(row: pd.Series, base: str, suffix: str):
    """After a merge with suffixes=('_a','_b'), a column that existed on
    both sides becomes f'{base}{suffix}'; a column unique to one side keeps
    its bare name. Try the suffixed form first, fall back to bare."""
    key = f"{base}{suffix}"
    if key in row.index:
        return row.get(key)
    return row.get(base)


def _classify_best_effort_alignment(row: pd.Series, ticker: Optional[str], task_id: Optional[str]):
    """Returns (alignment_confidence, alignment_key_used) for a best-effort
    (Q4/Q5-touching) rule, using the ctx_* context recovered by
    analysis.icaif_alignment — never upgrading past what that module
    actually recovered.
      - context_exact: ctx confidence is high/medium AND ticker is a
        confirmed member of the recovered universe.
      - best_effort:    ctx was recovered (some source != none) but doesn't
        confirm this specific ticker.
      - low_confidence: no context could be recovered at all (source=none
        or filename_pattern) — pure task_id string matching."""
    ctx_source = row.get("ctx_alignment_source")
    ctx_conf = row.get("ctx_alignment_confidence")
    universe = row.get("ctx_portfolio_universe") or row.get("ctx_ticker_universe")

    if ctx_source in (None, "none", "filename_pattern"):
        return "low_confidence", f"task_id={task_id} only (no recoverable context)"

    if ctx_conf in ("high", "medium") and _ticker_in_universe(ticker, universe):
        return "context_exact", f"task_id={task_id} + ctx_alignment_source={ctx_source} confirmed ticker={ticker} in known universe"

    return "best_effort", f"task_id={task_id} + ctx_alignment_source={ctx_source} (ticker={ticker} not confirmed in known universe)"


def _summary_tier(alignment_confidence: str) -> str:
    """Maps the 5 raw per-case values down to the 4 buckets requested for
    contradiction_summary.csv (single_record has no join ambiguity, same as
    exact_join, so it rolls into 'exact')."""
    if alignment_confidence in ("single_record", "exact_join"):
        return "exact"
    return alignment_confidence  # context_exact / best_effort / low_confidence pass through


def _norm(flag: str, rows: pd.DataFrame, ticker_col=None, date_col=None,
          task_col="task_id", adapter_cols=(), detail_fn=None,
          alignment_fn=None) -> pd.DataFrame:
    meta = RULE_REGISTRY[flag]
    cols = ["flag", "category", "severity", "alignment_confidence", "alignment_tier",
            "exact_or_best_effort", "alignment_source", "alignment_key_used",
            "ticker", "date", "task_id", "adapters_involved", "source_fields", "source_atoms",
            "detail", "limitation"]
    if rows.empty:
        return pd.DataFrame(columns=cols)

    out = pd.DataFrame({
        "flag": flag,
        "category": meta["category"],
        "severity": meta["severity"],
        "ticker": rows[ticker_col] if ticker_col and ticker_col in rows.columns else None,
        "date": rows[date_col] if date_col and date_col in rows.columns else None,
        "task_id": rows[task_col] if task_col in rows.columns else None,
    })

    adapters = []
    for _, r in rows.iterrows():
        names = sorted({str(r[c]) for c in adapter_cols if c in rows.columns and pd.notna(r.get(c))})
        adapters.append(",".join(names))
    out["adapters_involved"] = adapters

    alignment_confidence: List[str] = []
    alignment_source: List[str] = []
    alignment_key_used: List[str] = []
    for i, (_, r) in enumerate(rows.iterrows()):
        ticker = out.iloc[i]["ticker"]
        task_id = out.iloc[i]["task_id"]
        if meta["alignment"] == "single_record":
            alignment_confidence.append("single_record")
            alignment_source.append(str(r.get("ctx_alignment_source") or "n/a"))
            alignment_key_used.append("single_record (no join)")
        elif meta["alignment"] == "exact_join":
            alignment_confidence.append("exact")
            alignment_source.append("schema")
            alignment_key_used.append(f"(ticker={ticker}, date={out.iloc[i]['date']}) exact")
        else:
            if alignment_fn is not None:
                conf, key = alignment_fn(r, ticker, task_id)
            else:
                conf, key = _classify_best_effort_alignment(r, ticker, task_id)
            alignment_confidence.append(conf)
            alignment_source.append(str(r.get("ctx_alignment_source") or "none"))
            alignment_key_used.append(key)

    out["alignment_confidence"] = alignment_confidence
    out["alignment_tier"] = [_summary_tier(a) for a in alignment_confidence]
    out["alignment_source"] = alignment_source
    out["alignment_key_used"] = alignment_key_used
    out["exact_or_best_effort"] = out["alignment_tier"].apply(lambda t: "exact" if t == "exact" else "best_effort")
    out["source_fields"] = ",".join(meta["input_fields"])
    out["source_atoms"] = ",".join(meta["atoms_used"])
    out["detail"] = [detail_fn(r) for _, r in rows.iterrows()] if detail_fn else ""
    out["limitation"] = meta["limitation"]
    return out[cols]


# --------------------------------------------------------------------------- #
# Category 1 — cross_question
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
    ticker_col = "ticker_q3" if "ticker_q3" in merged.columns else "ticker"
    date_col = "date_q3" if "date_q3" in merged.columns else "date"
    return _norm(
        "LONG_WITH_WEAK_VALIDATION", merged, ticker_col, date_col,
        adapter_cols=["adapter_q3", "adapter_q5"],
        detail_fn=lambda r: f"{r['adapter_q3']} LONG on {r[ticker_col]}; {r['adapter_q5']} "
                             f"validation_status={r['validation_status']} (task {r['task_id']})",
        alignment_fn=lambda r, t, tid: _classify_best_effort_alignment(
            pd.Series({
                "ctx_alignment_source": _get_suffixed(r, "ctx_alignment_source", "_q5"),
                "ctx_alignment_confidence": _get_suffixed(r, "ctx_alignment_confidence", "_q5"),
                "ctx_portfolio_universe": _get_suffixed(r, "ctx_portfolio_universe", "_q5"),
                "ctx_ticker_universe": _get_suffixed(r, "ctx_ticker_universe", "_q5"),
            }), t, tid,
        ),
    )


def rule_positive_sentiment_bear_regime(q2: pd.DataFrame, q4: pd.DataFrame) -> pd.DataFrame:
    if q2.empty or q4.empty:
        return pd.DataFrame()
    bear = q4[q4["regime"] == "BEAR"]
    if bear.empty:
        return pd.DataFrame()
    merged = q2[q2["sentiment_score"] > 0].merge(bear, on=["date", "task_id"], suffixes=("_q2", "_q4"))
    ticker_col = "ticker_q2" if "ticker_q2" in merged.columns else "ticker"
    return _norm(
        "POSITIVE_SENTIMENT_BEAR_REGIME", merged, ticker_col, "date",
        adapter_cols=["adapter_q2", "adapter_q4"],
        detail_fn=lambda r: f"{r['adapter_q2']} sentiment={r['sentiment_score']:.2f} on {r[ticker_col]}/{r['date']}; "
                             f"{r['adapter_q4']} regime=BEAR",
        alignment_fn=lambda r, t, tid: _classify_best_effort_alignment(
            pd.Series({
                "ctx_alignment_source": _get_suffixed(r, "ctx_alignment_source", "_q4"),
                "ctx_alignment_confidence": _get_suffixed(r, "ctx_alignment_confidence", "_q4"),
                "ctx_portfolio_universe": _get_suffixed(r, "ctx_portfolio_universe", "_q4"),
                "ctx_ticker_universe": _get_suffixed(r, "ctx_ticker_universe", "_q4"),
            }), t, tid,
        ),
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
    ticker_col = "ticker_q4" if "ticker_q4" in merged.columns else "ticker"
    date_col = "date_q4" if "date_q4" in merged.columns else "date"
    return _norm(
        "HIGH_WEIGHT_HIGH_DRAWDOWN", merged, ticker_col, date_col,
        adapter_cols=["adapter_q4", "adapter_q5"],
        detail_fn=lambda r: f"{r['adapter_q4']} allocates weight={r['weight']:.2f} to {r[ticker_col]}; "
                             f"{r['adapter_q5']} reports max_drawdown={r['max_drawdown']:.2f}",
        alignment_fn=lambda r, t, tid: _classify_best_effort_alignment(
            pd.Series({
                "ctx_alignment_source": _get_suffixed(r, "ctx_alignment_source", "_q5"),
                "ctx_alignment_confidence": _get_suffixed(r, "ctx_alignment_confidence", "_q5"),
                "ctx_portfolio_universe": _get_suffixed(r, "ctx_portfolio_universe", "_q5"),
                "ctx_ticker_universe": _get_suffixed(r, "ctx_ticker_universe", "_q5"),
            }), t, tid,
        ),
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
# Category 2 — intra_record (single record, no join)
# --------------------------------------------------------------------------- #

def rule_sentiment_risk_intra_conflict(q2: pd.DataFrame) -> pd.DataFrame:
    if q2.empty:
        return pd.DataFrame()
    matches = q2[(q2["sentiment_score"] > 0) & (q2["risk_level"] == "EXTREME")]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "SENTIMENT_RISK_INTRA_CONFLICT", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} sentiment={r['sentiment_score']:.2f} but risk_level=EXTREME "
                             f"on {r['ticker']}/{r['date']}",
    )


def rule_direction_return_intra_conflict(q3: pd.DataFrame) -> pd.DataFrame:
    if q3.empty:
        return pd.DataFrame()
    sub = q3.dropna(subset=["expected_return"])
    matches = sub[
        ((sub["direction"] == "LONG") & (sub["expected_return"] < 0)) |
        ((sub["direction"] == "SHORT") & (sub["expected_return"] > 0))
    ]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "DIRECTION_RETURN_INTRA_CONFLICT", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} direction={r['direction']} but expected_return={r['expected_return']:.4f} "
                             f"on {r['ticker']}/{r['date']}",
    )


def rule_bull_regime_high_cash(q4: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q4.empty:
        return pd.DataFrame()
    matches = q4[(q4["regime"] == "BULL") & (q4["cash_ratio"] >= cfg.intra_record_high_cash_in_bull)]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "BULL_REGIME_HIGH_CASH", matches, None, "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} regime=BULL but cash_ratio={r['cash_ratio']:.2f} on {r['date']}",
    )


def rule_positive_return_weak_risk_adjusted(q5: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q5.empty:
        return pd.DataFrame()
    sub = q5.dropna(subset=["total_return", "sharpe", "max_drawdown"])
    matches = sub[
        (sub["total_return"] > 0)
        & (sub["sharpe"] < cfg.intra_record_weak_risk_adjusted_sharpe)
        & (sub["max_drawdown"] <= cfg.intra_record_weak_risk_adjusted_drawdown)
    ]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "POSITIVE_RETURN_WEAK_RISK_ADJUSTED", matches, None, "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} total_return={r['total_return']:.4f} but sharpe={r['sharpe']:.2f} "
                             f"and max_drawdown={r['max_drawdown']:.2f} (task {r['task_id']})",
    )


# --------------------------------------------------------------------------- #
# Category 3 — evidence (uses text / atoms)
# --------------------------------------------------------------------------- #

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
        "STRONG_SIGNAL_MISSING_EVIDENCE", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} strength={r['strength']:.2f} on {r['ticker']}/{r['date']} "
                             f"with no supporting_evidence",
    )


def _text_valence(texts: List[str]) -> Dict[str, int]:
    """Deterministic keyword count, not sentiment analysis — see BEARISH_WORDS/BULLISH_WORDS."""
    blob = " ".join(t.lower() for t in texts if isinstance(t, str))
    return {
        "bearish": sum(blob.count(w) for w in BEARISH_WORDS),
        "bullish": sum(blob.count(w) for w in BULLISH_WORDS),
    }


def rule_headline_evidence_mismatch(df: pd.DataFrame) -> pd.DataFrame:
    """Single-record check across whichever of Q1/Q3 a row has. Iterates the
    raw flattened df directly (not extract_q1/q3) since it needs both
    headline direction and free-text fields on the same row."""
    if df.empty:
        return pd.DataFrame()
    rows = []
    for _, r in df.iterrows():
        headline, texts = None, []
        if r.get("q1_present"):
            headline = r.get("q1_action")
            texts = [r.get("q1_reasoning")]
        elif r.get("q3_present"):
            headline = r.get("q3_direction")
            texts = list(r.get("q3_supporting_evidence") or [])
        if headline not in ("BUY", "LONG", "SELL", "SHORT"):
            continue
        valence = _text_valence(texts)
        if valence["bearish"] == 0 and valence["bullish"] == 0:
            continue
        mismatch = (
            (headline in ("BUY", "LONG") and valence["bearish"] > valence["bullish"]) or
            (headline in ("SELL", "SHORT") and valence["bullish"] > valence["bearish"])
        )
        if mismatch:
            rows.append({
                "adapter": r["adapter"], "ticker": r.get("ticker"), "date": r.get("date"),
                "task_id": r.get("task_id"), "headline": headline,
                "bearish_count": valence["bearish"], "bullish_count": valence["bullish"],
            })
    if not rows:
        return pd.DataFrame()
    matches = pd.DataFrame(rows)
    return _norm(
        "HEADLINE_EVIDENCE_MISMATCH", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} headline={r['headline']} on {r['ticker']}/{r['date']} but text "
                             f"has {r['bearish_count']} bearish-word hits vs {r['bullish_count']} bullish-word hits",
    )


def _evidence_atom_lookup(df: pd.DataFrame) -> Dict[tuple, set]:
    """(adapter, ticker, date) -> set of evidence atom tags, from whichever
    of Q1/Q2/Q3 that row answers."""
    out: Dict[tuple, set] = {}
    for _, r in df.iterrows():
        if not (r.get("q1_present") or r.get("q2_present") or r.get("q3_present")):
            continue
        key = (r["adapter"], r.get("ticker"), r.get("date"))
        out[key] = set(evidence_atoms_from_record(r))
    return out


def rule_atom_overlap_vs_direction(df: pd.DataFrame, q1: pd.DataFrame, q3: pd.DataFrame, cfg: Config) -> Dict[str, pd.DataFrame]:
    """Produces both SAME_DIRECTION_ZERO_ATOM_OVERLAP and
    OPPOSITE_DIRECTION_ATOM_OVERLAP from one pass over (ticker, date) groups
    with >=2 directional votes, reusing evidence_atoms_from_record."""
    atom_lut = _evidence_atom_lookup(df)
    votes = []
    for _, r in q1.iterrows():
        if r["action"] in ("BUY", "SELL"):
            votes.append({"adapter": r["adapter"], "ticker": r["ticker"], "date": r["date"],
                          "task_id": r["task_id"], "sign": 1 if r["action"] == "BUY" else -1})
    for _, r in q3.iterrows():
        if r["direction"] in ("LONG", "SHORT"):
            votes.append({"adapter": r["adapter"], "ticker": r["ticker"], "date": r["date"],
                          "task_id": r["task_id"], "sign": 1 if r["direction"] == "LONG" else -1})
    if len(votes) < cfg.evidence_overlap_min_records:
        return {"SAME_DIRECTION_ZERO_ATOM_OVERLAP": pd.DataFrame(), "OPPOSITE_DIRECTION_ATOM_OVERLAP": pd.DataFrame()}

    vdf = pd.DataFrame(votes)
    same_rows, opp_rows = [], []
    for (ticker, date), g in vdf.groupby(["ticker", "date"]):
        if len(g) < cfg.evidence_overlap_min_records:
            continue
        pairs = [(i, j) for i in g.index for j in g.index if i < j]
        for i, j in pairs:
            a, b = g.loc[i], g.loc[j]
            atoms_a = atom_lut.get((a["adapter"], ticker, date), set())
            atoms_b = atom_lut.get((b["adapter"], ticker, date), set())
            overlap = atoms_a & atoms_b
            row = {"ticker": ticker, "date": date, "task_id": a["task_id"],
                   "adapter_a": a["adapter"], "adapter_b": b["adapter"],
                   "atoms_a": ",".join(sorted(atoms_a)), "atoms_b": ",".join(sorted(atoms_b)),
                   "overlap": ",".join(sorted(overlap))}
            if a["sign"] == b["sign"] and not overlap and (atoms_a or atoms_b):
                same_rows.append(row)
            elif a["sign"] != b["sign"] and overlap:
                opp_rows.append(row)

    result = {}
    if same_rows:
        m = pd.DataFrame(same_rows)
        result["SAME_DIRECTION_ZERO_ATOM_OVERLAP"] = _norm(
            "SAME_DIRECTION_ZERO_ATOM_OVERLAP", m, "ticker", "date",
            adapter_cols=["adapter_a", "adapter_b"],
            detail_fn=lambda r: f"{r['adapter_a']} and {r['adapter_b']} agree on direction for {r['ticker']}/{r['date']} "
                                 f"but share zero evidence-atom tags ({r['atoms_a']} vs {r['atoms_b']})",
        )
    else:
        result["SAME_DIRECTION_ZERO_ATOM_OVERLAP"] = pd.DataFrame()
    if opp_rows:
        m = pd.DataFrame(opp_rows)
        result["OPPOSITE_DIRECTION_ATOM_OVERLAP"] = _norm(
            "OPPOSITE_DIRECTION_ATOM_OVERLAP", m, "ticker", "date",
            adapter_cols=["adapter_a", "adapter_b"],
            detail_fn=lambda r: f"{r['adapter_a']} and {r['adapter_b']} disagree on direction for {r['ticker']}/{r['date']} "
                                 f"yet share evidence-atom tags: {r['overlap']}",
        )
    else:
        result["OPPOSITE_DIRECTION_ATOM_OVERLAP"] = pd.DataFrame()
    return result


def rule_risk_atoms_but_bullish_headline(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for _, r in df.iterrows():
        headline = None
        if r.get("q1_present") and r.get("q1_action") == "BUY":
            headline = "BUY"
        elif r.get("q3_present") and r.get("q3_direction") == "LONG":
            headline = "LONG"
        if headline is None:
            continue
        atoms = risk_atoms_from_record(r)
        severe = [a for a in atoms if a.startswith("risk_level:EXTREME") or a == "severe_drawdown"
                  or a == "risk_language_in_reasoning"]
        if severe:
            rows.append({"adapter": r["adapter"], "ticker": r.get("ticker"), "date": r.get("date"),
                        "task_id": r.get("task_id"), "headline": headline, "risk_atoms": ",".join(severe)})
    if not rows:
        return pd.DataFrame()
    matches = pd.DataFrame(rows)
    return _norm(
        "RISK_ATOMS_BUT_BULLISH_HEADLINE", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} headline={r['headline']} on {r['ticker']}/{r['date']} but risk_atoms={r['risk_atoms']}",
    )


def rule_validation_fail_but_strong_bullish(df: pd.DataFrame, q1: pd.DataFrame, q3: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    keep_cols = ["adapter", "ticker", "date", "task_id"]
    strong = pd.concat([
        q1[(q1["action"] == "BUY") & (q1["confidence"] >= cfg.high_confidence_threshold)][keep_cols].assign(label="BUY"),
        q3[(q3["direction"] == "LONG") & (q3["strength"] >= cfg.high_confidence_threshold)][keep_cols].assign(label="LONG"),
    ], ignore_index=True) if not (q1.empty and q3.empty) else pd.DataFrame()
    if strong.empty:
        return pd.DataFrame()

    # task_id -> that Q5 record's own ctx (the side lacking ticker/date, so
    # its recovered context is what determines join trustworthiness here).
    fail_task_ctx: Dict[str, dict] = {}
    for _, r in df.iterrows():
        if r.get("q5_present"):
            atoms = validation_atoms_from_record(r, cfg)
            if "validation_status:fail" in atoms:
                fail_task_ctx[r.get("task_id")] = {
                    "ctx_alignment_source": r.get("ctx_alignment_source"),
                    "ctx_alignment_confidence": r.get("ctx_alignment_confidence"),
                    "ctx_portfolio_universe": r.get("ctx_portfolio_universe"),
                    "ctx_ticker_universe": r.get("ctx_ticker_universe"),
                }
    if not fail_task_ctx:
        return pd.DataFrame()

    matches = strong[strong["task_id"].isin(fail_task_ctx.keys())]
    if matches.empty:
        return pd.DataFrame()
    return _norm(
        "VALIDATION_FAIL_BUT_STRONG_BULLISH", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} strong {r['label']} on {r['ticker']}/{r['date']}, but task {r['task_id']} "
                             f"contains a Q5 record with validation_status:fail",
        alignment_fn=lambda r, t, tid: _classify_best_effort_alignment(
            pd.Series(fail_task_ctx.get(r["task_id"], {})), t, tid,
        ),
    )


# --------------------------------------------------------------------------- #
# Category 4 — calibration
# --------------------------------------------------------------------------- #

def rule_high_confidence_poor_calibration(q1: pd.DataFrame, overconfidence_flags: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if q1.empty or overconfidence_flags is None or overconfidence_flags.empty:
        return pd.DataFrame()
    q1_flags = overconfidence_flags[overconfidence_flags["question"] == "Q1"] if "question" in overconfidence_flags.columns else overconfidence_flags
    poor_adapters = set(q1_flags["adapter"].unique())
    hc = q1[(q1["confidence"] >= cfg.high_confidence_threshold) & (q1["adapter"].isin(poor_adapters))]
    if hc.empty:
        return pd.DataFrame()
    return _norm(
        "HIGH_CONFIDENCE_POOR_CALIBRATION", hc, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} confidence={r['confidence']:.2f} on {r['ticker']}/{r['date']}, "
                             f"but is flagged overconfident historically",
    )


def rule_confidence_in_poor_calibration_bucket(q1: pd.DataFrame, q3: pd.DataFrame,
                                                calibration_table: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if calibration_table is None or calibration_table.empty:
        return pd.DataFrame()
    poor = calibration_table[calibration_table["calibration_error"] >= cfg.calibration_bucket_poor_error]
    if poor.empty:
        return pd.DataFrame()

    def bucket_of(v: float) -> str:
        edges = list(cfg.confidence_bucket_edges)
        for lo, hi in zip(edges[:-1], edges[1:]):
            if lo <= v < hi:
                return f"{lo:.1f}-{min(hi, 1.0):.1f}"
        return f"{edges[-2]:.1f}-1.0"

    poor_keys = set(zip(poor["adapter"], poor["question"], poor["bucket"]))
    rows = []
    for _, r in q1.dropna(subset=["confidence"]).iterrows():
        key = (r["adapter"], "Q1", bucket_of(r["confidence"]))
        if key in poor_keys:
            rows.append({**r.to_dict(), "question": "Q1", "value": r["confidence"], "bucket": key[2]})
    for _, r in q3.dropna(subset=["strength"]).iterrows():
        key = (r["adapter"], "Q3", bucket_of(r["strength"]))
        if key in poor_keys:
            rows.append({**r.to_dict(), "question": "Q3", "value": r["strength"], "bucket": key[2]})
    if not rows:
        return pd.DataFrame()
    matches = pd.DataFrame(rows)
    return _norm(
        "CONFIDENCE_IN_POOR_CALIBRATION_BUCKET", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} {r['question']} value={r['value']:.2f} (bucket {r['bucket']}) on "
                             f"{r['ticker']}/{r['date']} falls in a historically poorly-calibrated bucket",
    )


def rule_systematic_overconfidence(q1: pd.DataFrame, q3: pd.DataFrame, overconfidence_flags: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if overconfidence_flags is None or overconfidence_flags.empty:
        return pd.DataFrame()
    counts = overconfidence_flags.groupby("adapter")["horizon"].nunique()
    systemic_adapters = set(counts[counts >= cfg.systematic_overconfidence_min_horizons].index)
    if not systemic_adapters:
        return pd.DataFrame()

    rows = []
    for _, r in q1.dropna(subset=["confidence"]).iterrows():
        if r["adapter"] in systemic_adapters and r["confidence"] >= cfg.high_confidence_threshold:
            rows.append({**r.to_dict(), "question": "Q1", "value": r["confidence"]})
    for _, r in q3.dropna(subset=["strength"]).iterrows():
        if r["adapter"] in systemic_adapters and r["strength"] >= cfg.high_confidence_threshold:
            rows.append({**r.to_dict(), "question": "Q3", "value": r["strength"]})
    if not rows:
        return pd.DataFrame()
    matches = pd.DataFrame(rows)
    return _norm(
        "SYSTEMATIC_OVERCONFIDENCE", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} is flagged overconfident at >= {cfg.systematic_overconfidence_min_horizons} "
                             f"horizons; {r['question']} value={r['value']:.2f} on {r['ticker']}/{r['date']}",
    )


# --------------------------------------------------------------------------- #
# Category 5 — temporal
# --------------------------------------------------------------------------- #

def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def rule_temporal_flip_unexplained(q1: pd.DataFrame, q3: pd.DataFrame, q2: pd.DataFrame,
                                    q4: pd.DataFrame, q5: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    votes = []
    for _, r in q1.iterrows():
        if r["action"] in ("BUY", "SELL"):
            votes.append({"adapter": r["adapter"], "ticker": r["ticker"], "date": r["date"],
                          "sign": 1 if r["action"] == "BUY" else -1, "label": r["action"], "question": "Q1"})
    for _, r in q3.iterrows():
        if r["direction"] in ("LONG", "SHORT"):
            votes.append({"adapter": r["adapter"], "ticker": r["ticker"], "date": r["date"],
                          "sign": 1 if r["direction"] == "LONG" else -1, "label": r["direction"], "question": "Q3"})
    if not votes:
        return pd.DataFrame()
    vdf = pd.DataFrame(votes)
    vdf["dt"] = vdf["date"].apply(_parse_date)
    vdf = vdf.dropna(subset=["dt"])

    context_dates = []
    for src_df, kind in ((q2, "risk"), (q4, "regime"), (q5, "validation")):
        for _, r in src_df.iterrows():
            d = _parse_date(r.get("date"))
            if d is not None:
                context_dates.append({"adapter": r["adapter"], "dt": d, "kind": kind})
    ctx_df = pd.DataFrame(context_dates) if context_dates else pd.DataFrame(columns=["adapter", "dt", "kind"])

    rows = []
    for (adapter, ticker), g in vdf.groupby(["adapter", "ticker"]):
        g = g.sort_values("dt")
        for i in range(len(g) - 1):
            a, b = g.iloc[i], g.iloc[i + 1]
            gap_days = (b["dt"] - a["dt"]).days
            if a["sign"] != 0 and b["sign"] != 0 and a["sign"] != b["sign"] and 0 < gap_days <= cfg.temporal_window_days:
                window_ctx = ctx_df[
                    (ctx_df["adapter"] == adapter) & (ctx_df["dt"] > a["dt"]) & (ctx_df["dt"] <= b["dt"])
                ] if not ctx_df.empty else ctx_df
                if window_ctx.empty:
                    rows.append({
                        "adapter": adapter, "ticker": ticker, "date": b["date"], "task_id": None,
                        "from_label": a["label"], "to_label": b["label"], "from_date": a["date"], "gap_days": gap_days,
                    })
    if not rows:
        return pd.DataFrame()
    matches = pd.DataFrame(rows)
    return _norm(
        "TEMPORAL_FLIP_UNEXPLAINED", matches, "ticker", "date", adapter_cols=["adapter"],
        detail_fn=lambda r: f"{r['adapter']} flipped {r['from_label']}({r['from_date']}) -> {r['to_label']}({r['date']}) "
                             f"on {r['ticker']} within {r['gap_days']}d, no Q2/Q4/Q5 record in between",
        # ticker+date on both sides of the flip come straight from Q1/Q3's
        # own exact schema fields (not a Q4/Q5 join) — the real uncertainty
        # here is the *causal* "was it really unexplained" claim, not a join
        # ambiguity, so this is a fixed classification, not ctx-derived.
        alignment_fn=lambda r, t, tid: ("best_effort", "exact ticker+date from Q1/Q3, but "
                                         "'unexplained' is a coarse window-presence check, not a causal test"),
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def detect_contradictions(
    df: pd.DataFrame,
    overconfidence_flags: pd.DataFrame,
    cfg: Config,
    calibration_table: Optional[pd.DataFrame] = None,
) -> Dict[str, pd.DataFrame]:
    q1, q2, q3 = extract_q1(df), extract_q2(df), extract_q3(df)
    q4, q5 = extract_q4(df), extract_q5(df)

    atom_rules = rule_atom_overlap_vs_direction(df, q1, q3, cfg)

    rule_outputs = [
        rule_buy_with_high_risk(q1, q2),
        rule_long_with_weak_validation(q3, q5, cfg),
        rule_positive_sentiment_bear_regime(q2, q4),
        rule_high_weight_high_drawdown(q4, q5, cfg),
        rule_action_alpha_direction_conflict(q1, q3),
        rule_sentiment_risk_intra_conflict(q2),
        rule_direction_return_intra_conflict(q3),
        rule_bull_regime_high_cash(q4, cfg),
        rule_positive_return_weak_risk_adjusted(q5, cfg),
        rule_strong_signal_missing_evidence(q3, cfg),
        rule_headline_evidence_mismatch(df),
        atom_rules["SAME_DIRECTION_ZERO_ATOM_OVERLAP"],
        atom_rules["OPPOSITE_DIRECTION_ATOM_OVERLAP"],
        rule_risk_atoms_but_bullish_headline(df, cfg),
        rule_validation_fail_but_strong_bullish(df, q1, q3, cfg),
        rule_high_confidence_poor_calibration(q1, overconfidence_flags, cfg),
        rule_confidence_in_poor_calibration_bucket(q1, q3, calibration_table, cfg),
        rule_systematic_overconfidence(q1, q3, overconfidence_flags, cfg),
        rule_temporal_flip_unexplained(q1, q3, q2, q4, q5, cfg),
    ]

    non_empty = [r for r in rule_outputs if not r.empty]
    cols = ["flag", "category", "severity", "alignment_confidence", "alignment_tier",
            "exact_or_best_effort", "alignment_source", "alignment_key_used",
            "ticker", "date", "task_id", "adapters_involved", "source_fields", "source_atoms",
            "detail", "limitation"]
    cases = pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame(columns=cols)

    if cases.empty:
        summary = pd.DataFrame(columns=["flag", "category", "count", "limitation"])
        category_summary = pd.DataFrame(columns=["category", "count", "n_rules_fired"])
        alignment_summary = pd.DataFrame(
            [{"alignment_tier": t, "count": 0} for t in ("exact", "context_exact", "best_effort", "low_confidence")]
        )
    else:
        summary = cases.groupby(["flag", "category"]).agg(count=("flag", "size")).reset_index()
        summary["limitation"] = summary["flag"].map(lambda f: RULE_REGISTRY[f]["limitation"])
        category_summary = cases.groupby("category").agg(
            count=("flag", "size"), n_rules_fired=("flag", "nunique"),
        ).reset_index()
        # The 4-tier breakdown requested: exact / context_exact / best_effort
        # / low_confidence — reindexed so every tier appears even at count 0.
        raw_counts = cases["alignment_tier"].value_counts()
        alignment_summary = pd.DataFrame({
            "alignment_tier": ["exact", "context_exact", "best_effort", "low_confidence"],
            "count": [int(raw_counts.get(t, 0)) for t in ("exact", "context_exact", "best_effort", "low_confidence")],
        })

    return {"cases": cases, "summary": summary, "category_summary": category_summary,
            "alignment_summary": alignment_summary}


def build_coverage_audit() -> pd.DataFrame:
    """One unified table answering: for every rule that DOES run, is it
    exact / running because of context enrichment / best-effort-only; and
    for every rule that DOESN'T run (yet), why not — never faked, always
    explained. Combines what used to be two separate concerns because the
    task asked for one file that draws this line explicitly."""
    cols = ["item", "kind", "capability_tier", "detectable_now", "detail", "required_missing_fields"]
    rows: List[dict] = []

    for flag, meta in RULE_REGISTRY.items():
        if meta["alignment"] in ("exact_join", "single_record"):
            tier = "exact_now"
            detail = "No Q4/Q5 join needed — runs on schema-native ticker+date (or a single record)."
        else:
            tier = "context_enrichment_or_best_effort"
            detail = ("Runs today via analysis/icaif_alignment.py's context recovery — upgrades to "
                       "context_exact when index.csv/task_id context confirms the ticker is in the batch's "
                       "known universe, else stays best_effort or drops to low_confidence for records with "
                       "no recoverable context (e.g. the legacy comparison_2026-07-02 batch).")
        rows.append({
            "item": flag, "kind": "implemented_rule", "capability_tier": tier, "detectable_now": True,
            "detail": detail, "required_missing_fields": "",
        })

    theoretical_gaps = [
        {
            "item": "Exact per-ticker Q4/Q5 alignment (not just context-confirmed best-effort)",
            "why_not_detectable": "Q4Portfolio has no ticker field and Q5Backtest has neither ticker nor date in "
                                   "CONTRACT/schemas.py — left unmodified this session per explicit instruction. "
                                   "Most Q4/Q5 adapters (finrl, finrl_x, vibe_trading) are genuinely portfolio-level, "
                                   "not single-asset, so even a schema fix would not make every Q4/Q5 record exactly "
                                   "alignable — the context layer (icaif_alignment.py) already closes most of the "
                                   "practical gap without touching the contract.",
            "required_missing_fields": "Q4Portfolio.ticker (Optional), Q5Backtest.ticker (Optional), Q5Backtest.decision_date (Optional) — would need maintainer sign-off",
        },
        {
            "item": "True walk-forward same-decision consistency (query the same adapter twice at an identical (ticker, date) to isolate model non-determinism from genuine signal change)",
            "why_not_detectable": "Current data has exactly one observation per (adapter, question, ticker, date); "
                                   "deepalpha's Q1-vs-Q3 same-day disagreement was only found via "
                                   "ACTION_ALPHA_DIRECTION_CONFLICT's cross-question join, not a repeat-run comparison.",
            "required_missing_fields": "repeated observations at identical (adapter, ticker, date) inputs",
        },
        {
            "item": "Causal validation that a temporal flip was actually explained by a regime/risk/validation change (vs. merely co-occurring in the same window)",
            "why_not_detectable": "TEMPORAL_FLIP_UNEXPLAINED checks only whether ANY Q2/Q4/Q5 record exists in the "
                                   "window with a different value, not that it caused the flip.",
            "required_missing_fields": "denser same-adapter time series (currently up to 7 distinct dates for the "
                                        "densest adapter, deepalpha; most adapters have 1-5)",
        },
        {
            "item": "Cross-adapter temporal consistency (does adapter A's signal flip correlate with adapter B's flip on the same ticker)",
            "why_not_detectable": "Out of scope for this round — would need a dedicated cross-adapter time-alignment "
                                   "rule, deferred to keep this expansion's rule count auditable rather than open-ended.",
            "required_missing_fields": "none technically — a design/scope decision, not a data gap",
        },
        {
            "item": "Upstream-capability-vs-wrapped-capability contradiction (an adapter's real upstream project has a "
                    "module — e.g. qlib's qlib/backtest/, RD-Agent's QlibFactorRunner — that could answer an "
                    "additional Q but was never wrapped)",
            "why_not_detectable": "This is a static-code-audit question about adapters/*.py and their vendored "
                                   "upstream repos, not a property of any single result record.",
            "required_missing_fields": "a separate upstream-capability audit script, not a contradiction rule",
        },
    ]
    for g in theoretical_gaps:
        rows.append({
            "item": g["item"], "kind": "theoretical_gap", "capability_tier": "not_implementable_now",
            "detectable_now": False, "detail": g["why_not_detectable"],
            "required_missing_fields": g["required_missing_fields"],
        })

    return pd.DataFrame(rows, columns=cols)


def build_rulebook_md() -> str:
    lines = ["# Contradiction Rulebook", "",
             "Auto-generated from `RULE_REGISTRY` in `analysis/icaif_contradictions.py` — "
             "if this file and `contradiction_cases.csv`'s `limitation` column ever disagree, "
             "the registry is the bug, not the generator.", ""]
    by_category: Dict[str, List[str]] = {}
    for flag, meta in RULE_REGISTRY.items():
        by_category.setdefault(meta["category"], []).append(flag)

    for category in ["cross_question", "intra_record", "evidence", "calibration", "temporal"]:
        if category not in by_category:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for flag in by_category[category]:
            meta = RULE_REGISTRY[flag]
            lines += [
                f"### {flag}",
                f"- **alignment**: {meta['alignment']}",
                f"- **severity**: {meta['severity']}",
                f"- **input fields**: {', '.join(meta['input_fields'])}",
                f"- **atoms used**: {', '.join(meta['atoms_used']) if meta['atoms_used'] else '(none)'}",
                f"- **description**: {meta['description']}",
                f"- **limitation**: {meta['limitation']}",
                "",
            ]
    return "\n".join(lines)


def build_outcome_comparison(cases: pd.DataFrame, df_hits: pd.DataFrame) -> pd.DataFrame:
    """Compares realized forward returns/hit-rate for records that triggered
    >=1 contradiction flag vs records that triggered none, broken down by
    category in addition to the overall flagged/unflagged split. Only rules
    with an exact (ticker, date) key can be traced back to one specific
    (adapter, ticker, date, question) record — best-effort/single-record
    rules that don't carry a ticker are excluded from this specific
    comparison and that exclusion is stated, not hidden."""
    cols = ["group", "n_samples", "hit_rate", "avg_forward_return", "insufficient_data"]
    if df_hits is None or df_hits.empty:
        return pd.DataFrame([
            {"group": "flagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
            {"group": "unflagged", "n_samples": 0, "hit_rate": np.nan, "avg_forward_return": np.nan, "insufficient_data": True},
        ], columns=cols)

    if cases.empty:
        flagged_keys = set()
    else:
        exact_cases = cases[cases["exact_or_best_effort"] == "exact"]
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
