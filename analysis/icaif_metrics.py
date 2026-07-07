"""
analysis/icaif_metrics.py — pure functions for the ICAIF experiment suite:
coverage tables, secondary-field -> atom extraction, calibration statistics,
and the fusion scoring formula.

No file I/O and no plotting here — everything takes DataFrames/dicts in and
returns DataFrames/dicts out, so it is unit-testable without touching disk.
All thresholds live on `Config` (dataclass, not module globals) so callers
can override any of them; the CLI only exposes the two the task asked for
(--horizons, --threshold-bps) directly, everything else is overridable via
an optional --config JSON file (see icaif_experiments.py).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from analysis.icaif_data_loader import AdapterInfo, QUESTIONS


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

@dataclass
class Config:
    threshold_bps: float = 20.0
    horizons: Sequence[int] = (1, 5, 20)

    confidence_bucket_edges: Sequence[float] = (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001)

    overconfidence_min_confidence: float = 0.75
    overconfidence_max_hit_rate: float = 0.55
    overconfidence_min_samples: int = 10

    weak_validation_return_max: float = 0.0
    weak_validation_sharpe_min: float = 0.5
    weak_validation_drawdown_max: float = -0.20
    weak_validation_win_rate_min: float = 0.50

    high_weight_threshold: float = 0.10
    severe_drawdown_threshold: float = -0.20

    strong_signal_strength_min: float = 0.80
    high_confidence_threshold: float = 0.80

    risk_multiplier: Dict[str, float] = None
    validation_multiplier: Dict[str, float] = None
    fusion_buy_threshold: float = 0.25
    fusion_sell_threshold: float = -0.25
    default_missing_confidence: float = 0.5

    def __post_init__(self):
        if self.risk_multiplier is None:
            self.risk_multiplier = {"LOW": 1.0, "MEDIUM": 0.85, "HIGH": 0.60, "EXTREME": 0.30}
        if self.validation_multiplier is None:
            self.validation_multiplier = {"strong": 1.0, "weak": 0.65, "fail": 0.40, "missing": 0.80}

    @classmethod
    def from_overrides(cls, overrides: Optional[Dict[str, Any]] = None) -> "Config":
        cfg = cls()
        for k, v in (overrides or {}).items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


# --------------------------------------------------------------------------- #
# Experiment 1 — coverage
# --------------------------------------------------------------------------- #

EXPECTED_DECLARED_COUNTS = {"Q1": 4, "Q2": 4, "Q3": 8, "Q4": 3, "Q5": 4}


def _observed_questions_by_adapter(df_observed: pd.DataFrame) -> Dict[str, set]:
    observed: Dict[str, set] = {}
    if df_observed is None or df_observed.empty:
        return observed
    for adapter, sub in df_observed.groupby("adapter"):
        qs = set()
        for q in QUESTIONS:
            col = f"{q.lower()}_present"
            if col in sub.columns and sub[col].any():
                qs.add(q)
        observed[adapter] = qs
    return observed


def build_coverage_matrix(adapters: List[AdapterInfo], df_observed: pd.DataFrame) -> pd.DataFrame:
    """adapter x Q matrix. Each cell lists which of {declared, implemented,
    observed} are true for that (adapter, question) pair, e.g.
    'declared+implemented+observed' or 'declared+implemented' (never run) or
    'observed' (undeclared capability caught in the wild)."""
    observed_by_adapter = _observed_questions_by_adapter(df_observed)
    rows = []
    for info in adapters:
        declared = set(info.questions_declared)
        implemented = set(info.questions_implemented)
        observed = observed_by_adapter.get(info.name, set())
        row = {"adapter": info.name}
        for q in QUESTIONS:
            tags = []
            if q in declared:
                tags.append("declared")
            if q in implemented:
                tags.append("implemented")
            if q in observed:
                tags.append("observed")
            row[q] = "+".join(tags) if tags else ""
        rows.append(row)
    return pd.DataFrame(rows).set_index("adapter")


def coverage_audit_findings(adapters: List[AdapterInfo], df_observed: pd.DataFrame) -> pd.DataFrame:
    """Rows flagging any disagreement between declared / implemented / observed
    capability. Never hidden or averaged away — this table IS the audit."""
    observed_by_adapter = _observed_questions_by_adapter(df_observed)
    findings = []
    for info in adapters:
        declared = set(info.questions_declared)
        implemented = set(info.questions_implemented)
        observed = observed_by_adapter.get(info.name)

        if declared != implemented:
            findings.append({
                "adapter": info.name, "kind": "declared_vs_implemented_mismatch",
                "declared": sorted(declared), "implemented": sorted(implemented),
                "observed": sorted(observed) if observed is not None else None,
                "detail": (f"questions_answered={sorted(declared)} but methods actually "
                           f"overridden in source cover {sorted(implemented)}"),
            })
        if observed is None:
            findings.append({
                "adapter": info.name, "kind": "no_observed_results",
                "declared": sorted(declared), "implemented": sorted(implemented),
                "observed": [],
                "detail": "no result JSON found under results/ for this adapter — "
                          "capability is declared/implemented but unverified in practice",
            })
        elif implemented and observed != implemented:
            findings.append({
                "adapter": info.name, "kind": "implemented_vs_observed_mismatch",
                "declared": sorted(declared), "implemented": sorted(implemented),
                "observed": sorted(observed),
                "detail": (f"source implements {sorted(implemented)} but results/ only "
                           f"contains observed output for {sorted(observed)}"),
            })
    return pd.DataFrame(findings)


def check_expected_counts(adapters: List[AdapterInfo]) -> pd.DataFrame:
    """Compares actual declared-count-per-Q against the counts noted in prior
    project discussion. A mismatch is not an error — it just means the prior
    notes are stale relative to the current repo, and this table proves it
    either way instead of asserting a number."""
    actual = {q: 0 for q in QUESTIONS}
    for info in adapters:
        for q in info.questions_declared:
            if q in actual:
                actual[q] += 1
    rows = []
    for q in QUESTIONS:
        expected = EXPECTED_DECLARED_COUNTS.get(q)
        rows.append({
            "question": q,
            "expected_from_prior_notes": expected,
            "actual_declared_count": actual[q],
            "matches": actual[q] == expected,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Experiment 2 — secondary-field value / schema compression
# --------------------------------------------------------------------------- #

PRIMARY_FIELDS: Dict[str, List[str]] = {
    "Q1": ["action"],
    "Q2": ["sentiment_score"],
    "Q3": ["direction", "strength"],
    "Q4": ["weights"],
    "Q5": ["total_return"],
}

SECONDARY_FIELDS: Dict[str, List[str]] = {
    "Q1": ["confidence", "reasoning", "bull_case", "bear_case", "time_horizon"],
    "Q2": ["risk_level", "drivers", "sources"],
    "Q3": ["signal_type", "expected_horizon", "expected_return", "supporting_evidence"],
    "Q4": ["cash_ratio", "regime", "rebalance_freq", "rationale"],
    "Q5": ["sharpe", "max_drawdown", "alpha_vs_benchmark", "calmar", "win_rate",
           "equity_curve", "benchmark", "train_period", "test_period"],
}

ATOM_TAGS = ["momentum", "valuation", "sentiment", "volatility", "liquidity",
             "macro", "earnings", "technical", "factor", "regime", "risk", "unknown"]

ATOM_KEYWORDS: Dict[str, List[str]] = {
    "momentum": ["momentum", "trend", "breakout", "moving average", "macd", "overbought", "oversold"],
    "valuation": ["valuation", "p/e", "pe ratio", "overvalued", "undervalued", "dcf", "fair value", "book value"],
    "sentiment": ["sentiment", "bullish", "bearish", "news", "social media", "reddit", "analyst", "greed", "fear"],
    "volatility": ["volatility", "vix", "implied vol", "realized vol", "swing", "choppy"],
    "liquidity": ["liquidity", "volume", "spread", "order book", "slippage", "illiquid"],
    "macro": ["fed", "interest rate", "inflation", "cpi", "gdp", "macro", "yield curve", "recession"],
    "earnings": ["earnings", "eps", "revenue", "guidance", "quarterly report", "beat estimate", "miss estimate"],
    "technical": ["support", "resistance", "chart pattern", "candlestick", "ema", "sma", "vwap", "technical"],
    "factor": ["factor", "alpha", "importance=", "loading", "ic ", "information coefficient", "ensemble"],
    "regime": ["regime", "bull market", "bear market", "sideways"],
    "risk": ["risk", "drawdown", "downside", "hedge", "stop loss", "exposure"],
}

RISK_WORDS = ["risk", "drawdown", "volatile", "volatility", "downside", "loss", "hedge", "exposure", "leverage"]


def _non_empty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, float) and np.isnan(v):
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def build_field_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """For every (question, field) pair, what fraction of records that answer
    that question have a non-empty value for that field. Kind is 'primary'
    or 'secondary' — used to build compression_loss_summary.csv."""
    rows = []
    for q in QUESTIONS:
        present_col = f"{q.lower()}_present"
        if present_col not in df.columns:
            continue
        sub = df[df[present_col] == True]  # noqa: E712
        n = len(sub)
        for kind, fields in (("primary", PRIMARY_FIELDS[q]), ("secondary", SECONDARY_FIELDS[q])):
            for f in fields:
                col = f"{q.lower()}_{f}"
                n_present = int(sub[col].apply(_non_empty).sum()) if col in sub.columns else 0
                rows.append({
                    "question": q, "field": f, "kind": kind,
                    "n_records_answering_q": n,
                    "n_field_present": n_present,
                    "coverage_ratio": (n_present / n) if n else np.nan,
                })
    return pd.DataFrame(rows)


def build_secondary_field_sparsity(field_coverage: pd.DataFrame) -> pd.DataFrame:
    sec = field_coverage[field_coverage["kind"] == "secondary"].copy()
    sec["sparsity"] = 1 - sec["coverage_ratio"]
    return sec.sort_values(["question", "sparsity"], ascending=[True, False]).reset_index(drop=True)


def tag_text_atoms(text: str) -> List[str]:
    """Coarse keyword tagger — deterministic, no LLM calls. This is a
    heuristic coarse classifier over a fixed tag vocabulary, not a claim of
    semantic understanding; documented as such in PAPER_FINDINGS.md."""
    if not text:
        return []
    low = text.lower()
    tags = [tag for tag, kws in ATOM_KEYWORDS.items() if any(kw in low for kw in kws)]
    return tags or ["unknown"]


def evidence_atoms_from_record(row: pd.Series) -> List[str]:
    texts: List[str] = []
    for col in ("q1_reasoning", "q1_bull_case", "q1_bear_case"):
        v = row.get(col)
        if isinstance(v, str) and v.strip():
            texts.append(v)
    for col in ("q2_drivers", "q3_supporting_evidence"):
        v = row.get(col)
        if isinstance(v, list):
            texts.extend([x for x in v if isinstance(x, str)])
    tags: set = set()
    for t in texts:
        tags.update(tag_text_atoms(t))
    return sorted(tags)


def risk_atoms_from_record(row: pd.Series) -> List[str]:
    atoms: List[str] = []
    risk_level = row.get("q2_risk_level")
    if isinstance(risk_level, str) and risk_level:
        atoms.append(f"risk_level:{risk_level}")
    regime = row.get("q4_regime")
    if isinstance(regime, str) and regime:
        atoms.append(f"regime:{regime}")
    cash_ratio = row.get("q4_cash_ratio")
    if isinstance(cash_ratio, (int, float)) and not pd.isna(cash_ratio) and cash_ratio >= 0.3:
        atoms.append("high_cash_ratio")
    mdd = row.get("q5_max_drawdown")
    if isinstance(mdd, (int, float)) and not pd.isna(mdd):
        if mdd <= -0.20:
            atoms.append("severe_drawdown")
        elif mdd <= -0.10:
            atoms.append("moderate_drawdown")
    reasoning = row.get("q1_reasoning")
    if isinstance(reasoning, str):
        low = reasoning.lower()
        if any(w in low for w in RISK_WORDS):
            atoms.append("risk_language_in_reasoning")
    return atoms


def classify_validation_strength(total_return, sharpe, mdd, win_rate, cfg: Config) -> str:
    if total_return is None and sharpe is None and mdd is None and win_rate is None:
        return "missing"
    if is_weak_validation(total_return, sharpe, mdd, win_rate, cfg):
        outright_fail = (
            total_return is not None and total_return <= cfg.weak_validation_return_max
            and mdd is not None and mdd <= cfg.weak_validation_drawdown_max
        )
        return "fail" if outright_fail else "weak"
    return "strong"


def is_weak_validation(total_return, sharpe, mdd, win_rate, cfg: Config) -> bool:
    checks = []
    if total_return is not None:
        checks.append(total_return <= cfg.weak_validation_return_max)
    if sharpe is not None:
        checks.append(sharpe < cfg.weak_validation_sharpe_min)
    if mdd is not None:
        checks.append(mdd <= cfg.weak_validation_drawdown_max)
    if win_rate is not None:
        checks.append(win_rate < cfg.weak_validation_win_rate_min)
    return any(checks)


def validation_atoms_from_record(row: pd.Series, cfg: Config) -> List[str]:
    if not row.get("q5_present"):
        return []
    status = classify_validation_strength(
        row.get("q5_total_return"), row.get("q5_sharpe"),
        row.get("q5_max_drawdown"), row.get("q5_win_rate"), cfg,
    )
    atoms = ["q5_present", f"validation_status:{status}"]
    ec = row.get("q5_equity_curve")
    if isinstance(ec, list) and len(ec) > 0:
        atoms.append("has_equity_curve")
    return atoms


def build_compression_loss_summary(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Per (question, adapter): how much of the schema's secondary-field
    surface is actually populated, and how many evidence/risk/validation
    atoms that unlocks. This is the quantitative backbone of the
    'headline-only vs. headline+secondary' comparison — deliberately not
    framed as an information-theoretic compression ratio (we don't compute
    entropy here), just a coverage/atoms-recovered count."""
    rows = []
    for q in QUESTIONS:
        present_col = f"{q.lower()}_present"
        if present_col not in df.columns:
            continue
        sub = df[df[present_col] == True]  # noqa: E712
        if sub.empty:
            continue
        for adapter, g in sub.groupby("adapter"):
            n = len(g)
            n_fields_possible = len(SECONDARY_FIELDS[q]) * n
            n_secondary_present = 0
            for f in SECONDARY_FIELDS[q]:
                col = f"{q.lower()}_{f}"
                if col in g.columns:
                    n_secondary_present += int(g[col].apply(_non_empty).sum())

            evidence_atoms = int(g.apply(lambda r: len(evidence_atoms_from_record(r)), axis=1).sum())
            risk_atoms = int(g.apply(lambda r: len(risk_atoms_from_record(r)), axis=1).sum())
            validation_atoms = int(g.apply(lambda r: len(validation_atoms_from_record(r, cfg)), axis=1).sum())

            rows.append({
                "question": q, "adapter": adapter, "n_records": n,
                "secondary_fields_possible": n_fields_possible,
                "secondary_fields_present": n_secondary_present,
                "secondary_field_sparsity": (
                    1 - (n_secondary_present / n_fields_possible) if n_fields_possible else np.nan
                ),
                "evidence_atoms_generated": evidence_atoms,
                "risk_atoms_generated": risk_atoms,
                "validation_atoms_generated": validation_atoms,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Experiment 3 — confidence calibration
# --------------------------------------------------------------------------- #

def bucket_confidence(value: float, cfg: Config) -> str:
    edges = list(cfg.confidence_bucket_edges)
    for lo, hi in zip(edges[:-1], edges[1:]):
        if lo <= value < hi:
            hi_label = min(hi, 1.0)
            return f"{lo:.1f}-{hi_label:.1f}"
    return f"{edges[-2]:.1f}-1.0"


def compute_hit(label: str, future_return: Optional[float], cfg: Config, kind: str) -> Optional[bool]:
    if future_return is None or (isinstance(future_return, float) and np.isnan(future_return)):
        return None
    thr = cfg.threshold_bps / 10000.0
    if kind == "q1":
        if label == "BUY":
            return future_return > thr
        if label == "SELL":
            return future_return < -thr
        if label == "HOLD":
            return abs(future_return) <= thr
    elif kind == "q3":
        if label == "LONG":
            return future_return > thr
        if label == "SHORT":
            return future_return < -thr
        if label == "NEUTRAL":
            return abs(future_return) <= thr
    return None


def build_calibration_table(df_hits: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """df_hits columns required: adapter, question (Q1/Q3), horizon,
    confidence, hit, future_return. Rows with hit=NaN (no realized future
    return yet) are excluded — callers should check `insufficient_data`
    separately rather than let those rows silently disappear."""
    cols = ["adapter", "question", "horizon", "bucket", "sample_count", "avg_confidence",
            "actual_hit_rate", "avg_forward_return", "calibration_error"]
    d = df_hits.dropna(subset=["hit"]).copy()
    if d.empty:
        return pd.DataFrame(columns=cols)

    d["bucket"] = d["confidence"].apply(lambda v: bucket_confidence(v, cfg))
    rows = []
    for (adapter, question, horizon, bucket), g in d.groupby(["adapter", "question", "horizon", "bucket"]):
        avg_conf = float(g["confidence"].mean())
        hit_rate = float(g["hit"].mean())
        rows.append({
            "adapter": adapter, "question": question, "horizon": horizon, "bucket": bucket,
            "sample_count": len(g),
            "avg_confidence": avg_conf,
            "actual_hit_rate": hit_rate,
            "avg_forward_return": float(g["future_return"].mean()),
            "calibration_error": abs(avg_conf - hit_rate),
        })
    return pd.DataFrame(rows, columns=cols)


def flag_overconfidence(calibration_table: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    cols = ["adapter", "question", "horizon", "avg_confidence", "actual_hit_rate", "sample_count"]
    if calibration_table.empty:
        return pd.DataFrame(columns=cols)

    def _agg(g: pd.DataFrame) -> pd.Series:
        w = g["sample_count"]
        return pd.Series({
            "avg_confidence": np.average(g["avg_confidence"], weights=w),
            "actual_hit_rate": np.average(g["actual_hit_rate"], weights=w),
            "sample_count": int(w.sum()),
        })

    agg = calibration_table.groupby(["adapter", "question", "horizon"]).apply(_agg, include_groups=False).reset_index()
    flagged = agg[
        (agg["avg_confidence"] >= cfg.overconfidence_min_confidence)
        & (agg["actual_hit_rate"] <= cfg.overconfidence_max_hit_rate)
        & (agg["sample_count"] >= cfg.overconfidence_min_samples)
    ]
    return flagged.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Experiment 5 — fusion scoring primitives
# --------------------------------------------------------------------------- #

ACTION_SIGN = {"BUY": 1, "LONG": 1, "HOLD": 0, "NEUTRAL": 0, "SELL": -1, "SHORT": -1}


def risk_multiplier_for(risk_level: Optional[str], cfg: Config) -> float:
    if not risk_level:
        return 1.0
    return cfg.risk_multiplier.get(risk_level, 1.0)


def validation_multiplier_for(status: str, cfg: Config) -> float:
    return cfg.validation_multiplier.get(status, cfg.validation_multiplier["missing"])


def contradiction_multiplier_for(n_flags: int, cfg: Config) -> float:
    return 1.0 - min(0.5, 0.1 * n_flags)


def score_to_decision(score: float, cfg: Config, direction_labels=("SELL", "HOLD", "BUY")) -> str:
    if score > cfg.fusion_buy_threshold:
        return direction_labels[2]
    if score < cfg.fusion_sell_threshold:
        return direction_labels[0]
    return direction_labels[1]


def compute_return_based_metrics(decisions: pd.DataFrame) -> Dict[str, Any]:
    """decisions needs columns: signal (-1/0/1), future_return (nullable),
    and optionally ticker/date for per-series turnover. Never fabricates a
    return-based metric when future_return is entirely null."""
    if "future_return" not in decisions.columns or decisions["future_return"].dropna().empty:
        return {"insufficient_data": True,
                "reason": "no realized future returns available yet for this horizon/date range"}

    d = decisions.dropna(subset=["future_return"]).copy()
    directional = d[d["signal"] != 0]

    hit_rate = np.nan
    false_positive_rate = np.nan
    if not directional.empty:
        correct = np.sign(directional["future_return"]) == np.sign(directional["signal"])
        hit_rate = float(correct.mean())
        false_positive_rate = float((~correct).mean())

    strat_returns = d["signal"] * d["future_return"]
    avg_forward_return = float(strat_returns.mean())
    std = strat_returns.std(ddof=1)
    sharpe = float(strat_returns.mean() / std * np.sqrt(252)) if std and not np.isnan(std) and std > 0 else np.nan

    cum = (1 + strat_returns.fillna(0)).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    max_drawdown = float(drawdown.min()) if len(drawdown) else np.nan

    if "ticker" in d.columns and "date" in d.columns:
        # Each ticker group needs >=2 distinct dates to have a turnover signal
        # at all; with only one snapshot per ticker (as in a single comparison
        # run) every diff is NaN — that's a real "not enough time points yet"
        # condition, not a warning-worthy anomaly, so it's suppressed here.
        parts = [g.sort_values("date")["signal"].diff().abs().mean()
                 for _, g in d.groupby("ticker")]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            turnover = float(np.nanmean(parts)) if parts else np.nan
    else:
        turnover = float(d["signal"].diff().abs().mean())

    return {
        "insufficient_data": False,
        "n_samples": len(d),
        "hit_rate": hit_rate,
        "avg_forward_return": avg_forward_return,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "turnover": turnover,
        "false_positive_rate": false_positive_rate,
        "coverage": len(d) / len(decisions) if len(decisions) else np.nan,
    }


def decision_distribution(decisions: pd.Series) -> Dict[str, float]:
    if decisions.empty:
        return {}
    return decisions.value_counts(normalize=True).to_dict()


def decision_stability(a: pd.Series, b: pd.Series) -> float:
    """Fraction of aligned (index-matched) rows where two fusion methods agree."""
    aligned = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if aligned.empty:
        return float("nan")
    return float((aligned["a"] == aligned["b"]).mean())
