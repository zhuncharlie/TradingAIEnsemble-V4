"""
analysis/icaif_data_loader.py — discovery layer for the ICAIF experiment suite.

Two independent sources of truth are kept deliberately separate (Experiment 1
exists to *compare* them, not to merge them away):

  * declared / implemented capability -> static AST scan of adapters/*.py
  * observed capability               -> actual result JSONs under results/

This module never imports an adapter module — adapters have mutually
incompatible pinned dependencies and must not be imported into one process
(see analysis/build_visualizations.py and DECISIONS.md). Everything here is
either filesystem discovery or JSON parsing, so it can run in any plain env
with pandas (no adapter-specific conda env needed).

Nothing in this file hard-codes an adapter count or an adapter name list —
`discover_adapters` / `discover_result_files` walk the repo at call time.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

QUESTIONS: List[str] = ["Q1", "Q2", "Q3", "Q4", "Q5"]

Q_METHOD: Dict[str, str] = {
    "Q1": "q1_decision",
    "Q2": "q2_sentiment",
    "Q3": "q3_signal",
    "Q4": "q4_portfolio",
    "Q5": "q5_backtest",
}
METHOD_Q = {v: k for k, v in Q_METHOD.items()}

# Files under adapters/ that are not real adapters and must be excluded from
# every count in this module (per CLAUDE.md: example_stub_adapter.py is the
# reference implementation, not a deliverable).
NON_ADAPTER_FILES = {"example_stub_adapter.py"}


# --------------------------------------------------------------------------- #
# Declared / implemented capability — static source scan, no imports
# --------------------------------------------------------------------------- #

@dataclass
class AdapterInfo:
    file: str
    class_name: str
    name: str
    questions_declared: List[str] = field(default_factory=list)
    questions_implemented: List[str] = field(default_factory=list)
    upstream_repo: str = ""
    requires_env: str = ""

    @property
    def declared_implemented_mismatch(self) -> bool:
        return set(self.questions_declared) != set(self.questions_implemented)


def _literal_or_none(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _is_trivial_none_stub(fn: ast.AST) -> bool:
    """True if a q*_ method body is just the BaseAdapter default (`return None`,
    optionally preceded by a docstring) — i.e. re-declared but not overridden."""
    stmts = list(fn.body)
    if (
        stmts
        and isinstance(stmts[0], ast.Expr)
        and isinstance(stmts[0].value, ast.Constant)
        and isinstance(stmts[0].value.value, str)
    ):
        stmts = stmts[1:]
    if len(stmts) == 1 and isinstance(stmts[0], ast.Return):
        ret = stmts[0].value
        if ret is None or (isinstance(ret, ast.Constant) and ret.value is None):
            return True
    return False


def _parse_adapter_file(path: Path) -> Optional[AdapterInfo]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return None

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
        if "BaseAdapter" not in base_names:
            continue

        name = ""
        questions_declared: List[str] = []
        upstream_repo = ""
        requires_env = ""
        implemented_methods: List[str] = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                targets = [t.id for t in item.targets if isinstance(t, ast.Name)]
                value = _literal_or_none(item.value)
                if "name" in targets and isinstance(value, str):
                    name = value
                elif "questions_answered" in targets and isinstance(value, list):
                    questions_declared = list(value)
                elif "upstream_repo" in targets and isinstance(value, str):
                    upstream_repo = value
                elif "requires_env" in targets and isinstance(value, str):
                    requires_env = value
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name in METHOD_Q and not _is_trivial_none_stub(item):
                    implemented_methods.append(item.name)

        questions_implemented = [
            q for q, m in Q_METHOD.items() if m in implemented_methods
        ]
        return AdapterInfo(
            file=str(path),
            class_name=node.name,
            name=name or path.stem.replace("_adapter", ""),
            questions_declared=questions_declared,
            questions_implemented=questions_implemented,
            upstream_repo=upstream_repo,
            requires_env=requires_env,
        )
    return None


def discover_adapters(adapters_dir: Path) -> List[AdapterInfo]:
    """Scan adapters_dir/*.py (no recursion into vendor/) and return one
    AdapterInfo per class that subclasses BaseAdapter. Excludes the reference
    stub and any vendor/ tree. Never imports the files it reads."""
    adapters_dir = Path(adapters_dir)
    infos: List[AdapterInfo] = []
    for path in sorted(adapters_dir.glob("*.py")):
        if path.name in NON_ADAPTER_FILES or path.name.startswith("_"):
            continue
        info = _parse_adapter_file(path)
        if info is not None:
            infos.append(info)
    return infos


# --------------------------------------------------------------------------- #
# Observed capability — actual result JSONs under results/
# --------------------------------------------------------------------------- #

@dataclass
class ResultRecord:
    path: str
    task_id: str
    adapter: str
    ticker: Optional[str]
    date: Optional[str]
    is_error: bool
    error: Optional[str]
    q1: Optional[dict]
    q2: Optional[dict]
    q3: Optional[dict]
    q4: Optional[dict]
    q5: Optional[dict]


def _extract_date(payload: dict) -> Optional[str]:
    for q in ("q1", "q2", "q3", "q4"):
        v = payload.get(q)
        if isinstance(v, dict) and v.get("date"):
            return v["date"]
    return None


def _extract_ticker(payload: dict, path: Path) -> Optional[str]:
    for q in ("q1", "q2", "q3"):
        v = payload.get(q)
        if isinstance(v, dict) and v.get("ticker"):
            return v["ticker"]
    stem = path.stem
    if "__" in stem:
        return stem.split("__", 1)[1]
    return None


def discover_result_files(results_dir: Path) -> List[ResultRecord]:
    """Walk results_dir recursively for AdapterResult-shaped JSON files.

    Handles two shapes actually produced by this repo's analysis/_run_one.py:
      - a full AdapterResult envelope (has "adapter", "task_id", "q1".."q5")
      - an error payload written on adapter.run() failure (has "adapter",
        "ticker", "date", "error", no q1..q5 keys)
    Anything else (price_history.csv, stray non-AdapterResult json) is skipped.

    Explicitly skips `*.raw.json` sidecars (written by
    analysis/run_adapter_observation_batch.py alongside each normalized
    envelope) — a raw single-question dump (e.g. a bare Q1Decision dict)
    still has its own "adapter" field, so without this filter it would slip
    past the "adapter" in payload check above and inflate record counts with
    an all-None row (q1..q5 all None, since the raw dict has no "q1" key at
    its top level) even though it doesn't corrupt Q1-Q5 extraction itself.
    """
    results_dir = Path(results_dir)
    records: List[ResultRecord] = []
    if not results_dir.exists():
        return records

    for path in sorted(results_dir.rglob("*.json")):
        if path.name.endswith(".raw.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict) or "adapter" not in payload:
            continue

        if "error" in payload and "q1" not in payload:
            records.append(ResultRecord(
                path=str(path),
                task_id=payload.get("task_id", path.parent.name),
                adapter=payload["adapter"],
                ticker=payload.get("ticker") or _extract_ticker({}, path),
                date=payload.get("date"),
                is_error=True,
                error=payload["error"],
                q1=None, q2=None, q3=None, q4=None, q5=None,
            ))
            continue

        records.append(ResultRecord(
            path=str(path),
            task_id=payload.get("task_id", path.parent.name),
            adapter=payload["adapter"],
            ticker=_extract_ticker(payload, path),
            date=_extract_date(payload),
            is_error=False,
            error=None,
            q1=payload.get("q1"), q2=payload.get("q2"), q3=payload.get("q3"),
            q4=payload.get("q4"), q5=payload.get("q5"),
        ))
    return records


# --------------------------------------------------------------------------- #
# Flattening helpers shared by every experiment module
# --------------------------------------------------------------------------- #

def records_to_dataframe(records: List[ResultRecord]) -> pd.DataFrame:
    """One row per ResultRecord, with q{n}_{field} columns flattened out.
    Rows are kept even when every q-slot is None (e.g. a pure error record) so
    that Experiment 1 can still count them as an attempted-but-failed run."""
    rows = []
    for r in records:
        row: Dict[str, Any] = {
            "path": r.path, "task_id": r.task_id, "adapter": r.adapter,
            "ticker": r.ticker, "date": r.date,
            "is_error": r.is_error, "error": r.error,
        }
        for qname, payload in (("q1", r.q1), ("q2", r.q2), ("q3", r.q3),
                                ("q4", r.q4), ("q5", r.q5)):
            row[f"{qname}_present"] = payload is not None
            if isinstance(payload, dict):
                for k, v in payload.items():
                    row[f"{qname}_{k}"] = v
        rows.append(row)
    return pd.DataFrame(rows)


def load_all(results_dir: Path, adapters_dir: Path) -> Dict[str, Any]:
    adapters = discover_adapters(adapters_dir)
    records = discover_result_files(results_dir)
    df = records_to_dataframe(records)
    return {
        "adapters": adapters,
        "records": records,
        "df": df,
    }


# --------------------------------------------------------------------------- #
# FutureReturnProvider — forward-only price lookups for Experiment 3
# --------------------------------------------------------------------------- #

class FutureReturnProvider:
    """Interface: given (ticker, decision_date, horizon in trading days),
    return the realized forward return, or None if it isn't observable yet.
    Implementations must never use data at or before decision_date as
    "future" data, and must never fabricate a value when fewer than
    `horizon` trading days have elapsed since decision_date."""

    def get_future_return(self, ticker: str, decision_date: str, horizon: int) -> Optional[float]:
        raise NotImplementedError


class YFinanceFutureReturnProvider(FutureReturnProvider):
    """Caches daily closes under data/cache/prices/{ticker}.csv. Tries a live
    yfinance refresh on every ticker touched (cheap, daily granularity); on
    any failure (offline, rate-limited, delisted ticker) falls back to
    whatever is already cached, and to None if nothing is cached either —
    never invents a price."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._frames: Dict[str, Optional[pd.DataFrame]] = {}

    def _cache_path(self, ticker: str) -> Path:
        safe = ticker.replace("/", "_")
        return self.cache_dir / f"{safe}.csv"

    def _load_ticker(self, ticker: str) -> Optional[pd.DataFrame]:
        if ticker in self._frames:
            return self._frames[ticker]

        df: Optional[pd.DataFrame] = None
        cache_path = self._cache_path(ticker)
        if cache_path.exists():
            try:
                df = pd.read_csv(cache_path, parse_dates=["Date"])
            except Exception:
                df = None

        try:
            import yfinance as yf
            fresh = yf.Ticker(ticker).history(period="2y", interval="1d")
            if fresh is not None and not fresh.empty:
                fresh = fresh.reset_index()[["Date", "Close"]]
                fresh["Date"] = pd.to_datetime(fresh["Date"]).dt.tz_localize(None)
                df = fresh
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(cache_path, index=False)
        except Exception:
            pass  # offline / rate-limited: keep whatever cache already had

        if df is not None:
            df = df.sort_values("Date").reset_index(drop=True)
        self._frames[ticker] = df
        return df

    def get_future_return(self, ticker: str, decision_date: str, horizon: int) -> Optional[float]:
        df = self._load_ticker(ticker)
        if df is None or df.empty:
            return None
        try:
            d0 = pd.Timestamp(decision_date)
        except (ValueError, TypeError):
            return None

        before_or_on = df[df["Date"] <= d0]
        after = df[df["Date"] > d0].reset_index(drop=True)
        if before_or_on.empty or len(after) < horizon:
            return None  # not enough trading days have elapsed yet — no fabrication

        base_price = float(before_or_on.iloc[-1]["Close"])
        future_price = float(after.iloc[horizon - 1]["Close"])
        if base_price == 0:
            return None
        return future_price / base_price - 1.0
