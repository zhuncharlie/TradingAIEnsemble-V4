"""
analysis/icaif_alignment.py — alignment context layer.

Recovers real (never fabricated) run context for every result record —
which decision date, which ticker or portfolio universe, which backtest
window — WITHOUT touching CONTRACT/schemas.py (read-only; Q4Portfolio has
no ticker field and Q5Backtest has neither ticker nor date, by design of
this session's explicit instruction not to modify the contract).

Three fallback tiers, tried in order, each cheaper/less certain than the
last. Every ctx_* field a tier can't fill stays None — nothing here ever
guesses or interpolates a date/ticker that isn't directly recoverable:

  1. index_csv        (confidence=high)    — direct row lookup in the
     index.csv that analysis/run_adapter_observation_batch.py itself wrote
     at generation time. Gives decision_date, ticker_or_universe_id,
     input_granularity, batch_id verbatim — the single most authoritative
     source, since it's what actually parameterized the adapter call.
  2. task_id_pattern   (confidence=medium) — task_id follows this repo's
     own f"{batch_id}__{decision_date}" convention (still true for records
     whose index.csv row is missing/stale, e.g. if index.csv were deleted
     but the JSON kept). Recovers decision_date + batch_id, then a known
     per-batch universe table for portfolio_universe/ticker_universe.
  3. filename_pattern  (confidence=low)    — `{adapter}__{ticker}.json`
     stem convention used by the ORIGINAL comparison_2026-07-02 batch
     (analysis/_run_one.py), which predates both index.csv and the
     "__{date}" task_id convention. Recovers ticker only.

Anything that matches none of these gets alignment_source="none",
alignment_confidence="none", and every ctx_* field stays None.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]

# Mirrors analysis/run_adapter_observation_batch.py's own constants. Not
# imported from there directly — that module already imports FROM
# icaif_data_loader (which imports FROM this module), so importing it here
# would be circular. These are small, stable, and documented as a mirror.
TICKER_LEVEL_UNIVERSES: Dict[str, List[str]] = {
    "observation_batch_day1": ["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ", "JPM", "XOM", "JNJ", "GLD"],
    "observation_batch_day1_historical_extension": ["NVDA", "SPY", "QQQ", "JPM", "GLD"],
}
PORTFOLIO_LEVEL_UNIVERSES: Dict[str, List[str]] = {
    "observation_batch_day1": ["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ", "JPM", "XOM", "JNJ", "TLT", "GLD", "CASH"],
    "observation_batch_day1_historical_extension": ["NVDA", "SPY", "QQQ", "JPM", "GLD"],
}
RUN_FAMILY_BY_BATCH: Dict[str, str] = {
    "observation_batch_day1": "main_batch",
    "observation_batch_day1_historical_extension": "historical_extension",
}
Q5_WINDOW_DAYS = 30  # mirrors run_adapter_observation_batch.py's Q5_WINDOW_DAYS

_TASK_ID_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

CTX_FIELDS = [
    "ctx_decision_date", "ctx_ticker", "ctx_ticker_universe", "ctx_portfolio_universe",
    "ctx_start", "ctx_end", "ctx_question", "ctx_input_id", "ctx_run_family",
    "ctx_alignment_source", "ctx_alignment_confidence",
]


def _empty_ctx() -> Dict[str, Any]:
    return {f: None for f in CTX_FIELDS}


# --------------------------------------------------------------------------- #
# Tier 1 — index.csv
# --------------------------------------------------------------------------- #

def load_index_csv_context(results_dir: Path) -> Dict[str, dict]:
    """path (resolved absolute string) -> index.csv row dict, scanning every
    index.csv under results_dir (both the main batch and the historical
    extension write their own). A path present in more than one index.csv
    (shouldn't happen — batch_id is part of the output path — but handled
    defensively) keeps the first row found."""
    context: Dict[str, dict] = {}
    results_dir = Path(results_dir)
    if not results_dir.exists():
        return context
    for index_path in sorted(results_dir.rglob("index.csv")):
        try:
            with open(index_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    norm_path = row.get("normalized_output_path")
                    if not norm_path:
                        continue
                    resolved = str((ROOT / norm_path).resolve()) if not Path(norm_path).is_absolute() else str(Path(norm_path).resolve())
                    context.setdefault(resolved, row)
        except (OSError, csv.Error):
            continue
    return context


def _from_index_row(row: dict) -> Dict[str, Any]:
    ctx = _empty_ctx()
    batch_id = row.get("batch_id")
    decision_date = row.get("decision_date") or None
    granularity = row.get("input_granularity")
    input_id = row.get("ticker_or_universe_id")

    ctx["ctx_decision_date"] = decision_date
    ctx["ctx_input_id"] = input_id
    ctx["ctx_run_family"] = RUN_FAMILY_BY_BATCH.get(batch_id, batch_id)
    ctx["ctx_ticker_universe"] = list(TICKER_LEVEL_UNIVERSES.get(batch_id, []) or []) or None
    ctx["ctx_portfolio_universe"] = list(PORTFOLIO_LEVEL_UNIVERSES.get(batch_id, []) or []) or None
    ctx["ctx_alignment_source"] = "index_csv"
    ctx["ctx_alignment_confidence"] = "high"

    if granularity == "ticker-level":
        ctx["ctx_ticker"] = input_id
    # portfolio-level / backtest-level: ctx_ticker stays None — correct,
    # these are genuinely not about one ticker.

    if granularity == "backtest-level" and decision_date:
        try:
            from datetime import date as date_cls, timedelta
            end = date_cls.fromisoformat(decision_date)
            ctx["ctx_end"] = decision_date
            ctx["ctx_start"] = (end - timedelta(days=Q5_WINDOW_DAYS)).isoformat()
        except ValueError:
            pass

    q_type = row.get("q_type")
    if q_type:
        ctx["ctx_question"] = q_type
    return ctx


# --------------------------------------------------------------------------- #
# Tier 2 — task_id pattern
# --------------------------------------------------------------------------- #

def _from_task_id(task_id: str) -> Dict[str, Any]:
    ctx = _empty_ctx()
    if not task_id or "__" not in task_id:
        return ctx
    candidate_batch, candidate_date = task_id.rsplit("__", 1)
    if not _TASK_ID_DATE_RE.fullmatch(candidate_date):
        # still try to recover *a* date anywhere in the string, lower trust
        m = _TASK_ID_DATE_RE.search(task_id)
        if not m:
            return ctx
        ctx["ctx_decision_date"] = m.group(0)
        ctx["ctx_alignment_source"] = "task_id_pattern"
        ctx["ctx_alignment_confidence"] = "medium"
        return ctx

    ctx["ctx_decision_date"] = candidate_date
    ctx["ctx_run_family"] = RUN_FAMILY_BY_BATCH.get(candidate_batch, candidate_batch)
    ctx["ctx_ticker_universe"] = list(TICKER_LEVEL_UNIVERSES.get(candidate_batch, []) or []) or None
    ctx["ctx_portfolio_universe"] = list(PORTFOLIO_LEVEL_UNIVERSES.get(candidate_batch, []) or []) or None
    ctx["ctx_alignment_source"] = "task_id_pattern"
    ctx["ctx_alignment_confidence"] = "medium"
    return ctx


# --------------------------------------------------------------------------- #
# Tier 3 — filename pattern ({adapter}__{ticker}.json, the original
# comparison_2026-07-02 batch's own convention, predates index.csv/task_id
# dates entirely)
# --------------------------------------------------------------------------- #

def _from_filename(path: Path) -> Dict[str, Any]:
    ctx = _empty_ctx()
    stem = path.stem
    if "__" in stem:
        _, ticker = stem.split("__", 1)
        if ticker:
            ctx["ctx_ticker"] = ticker
            ctx["ctx_alignment_source"] = "filename_pattern"
            ctx["ctx_alignment_confidence"] = "low"
            ctx["ctx_run_family"] = "legacy_comparison"
    return ctx


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def recover_context(path: Path, payload: dict, index_ctx: Optional[Dict[str, dict]] = None) -> Dict[str, Any]:
    """Best-effort, tiered, never-fabricated context recovery for one
    result record. `index_ctx` is the output of load_index_csv_context,
    passed in once per discover_result_files() call rather than re-scanned
    per file."""
    path = Path(path)
    index_ctx = index_ctx or {}

    ctx = _empty_ctx()

    resolved = str(path.resolve())
    if resolved in index_ctx:
        ctx.update({k: v for k, v in _from_index_row(index_ctx[resolved]).items() if v is not None})

    if ctx["ctx_alignment_source"] is None:
        task_id = payload.get("task_id", path.parent.name)
        tctx = _from_task_id(task_id)
        if tctx["ctx_alignment_source"] is not None:
            ctx.update(tctx)

    if ctx["ctx_ticker"] is None:
        fctx = _from_filename(path)
        if fctx.get("ctx_ticker"):
            ctx["ctx_ticker"] = fctx["ctx_ticker"]
            if ctx["ctx_alignment_source"] is None:
                ctx["ctx_alignment_source"] = fctx["ctx_alignment_source"]
                ctx["ctx_alignment_confidence"] = fctx["ctx_alignment_confidence"]
                ctx["ctx_run_family"] = ctx["ctx_run_family"] or fctx["ctx_run_family"]

    # ctx_question: fall back to whichever q-slot the payload actually has,
    # if index.csv didn't already set it (index.csv always has q_type, so
    # this only fires for tier-2/3 records).
    if ctx["ctx_question"] is None:
        for q in ("q1", "q2", "q3", "q4", "q5"):
            if payload.get(q) is not None:
                ctx["ctx_question"] = q.upper()
                break

    if ctx["ctx_alignment_source"] is None:
        ctx["ctx_alignment_source"] = "none"
        ctx["ctx_alignment_confidence"] = "none"

    return ctx
