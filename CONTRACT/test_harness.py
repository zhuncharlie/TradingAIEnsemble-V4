"""
CONTRACT/test_harness.py — Validates an adapter against the schema contract.

Usage:
    python CONTRACT/test_harness.py --adapter adapters/ai_hedge_fund_adapter.py
    python CONTRACT/test_harness.py --adapter adapters/fingpt_adapter.py --smoke

DO NOT MODIFY THIS FILE.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    AdapterResult,
    Q1Decision,
    Q2Sentiment,
    Q3Signal,
    Q4Portfolio,
    Q5Backtest,
)

PASS  = "\033[92m✓\033[0m"
FAIL  = "\033[91m✗\033[0m"
WARN  = "\033[93m!\033[0m"
BOLD  = "\033[1m"
RESET = "\033[0m"

SAMPLE_TICKER  = "AAPL"
SAMPLE_DATE    = "2024-01-15"
SAMPLE_TICKERS = ["AAPL", "MSFT", "NVDA"]
SAMPLE_START   = "2024-01-01"
SAMPLE_END     = "2024-03-31"
SAMPLE_TASK    = "smoke_test"


def load_adapter(path: str) -> BaseAdapter:
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Adapter file not found: {p}")

    spec   = importlib.util.spec_from_file_location("_adapter_module", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # find a BaseAdapter subclass
    candidates = [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseAdapter) and cls is not BaseAdapter
    ]
    if not candidates:
        raise RuntimeError(f"No BaseAdapter subclass found in {p}")
    if len(candidates) > 1:
        print(f"{WARN} Multiple BaseAdapter subclasses found; using {candidates[0].__name__}")
    return candidates[0]()


def check(label: str, fn, *args, **kwargs) -> Tuple[bool, Any, str]:
    """Run fn(*args, **kwargs), return (passed, result, error_message)."""
    try:
        result = fn(*args, **kwargs)
        return True, result, ""
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"


def run_harness(adapter: BaseAdapter, smoke_only: bool = False) -> int:
    """Run all checks. Returns exit code (0=all pass, 1=failures)."""
    failures = 0
    results: List[Tuple[str, bool, str]] = []

    def record(label, passed, detail=""):
        results.append((label, passed, detail))
        icon = PASS if passed else FAIL
        detail_str = f"  → {detail}" if detail else ""
        print(f"  {icon} {label}{detail_str}")
        return passed

    print(f"\n{BOLD}=== Adapter: {adapter.__class__.__name__} ==={RESET}")

    # --- 1. Metadata checks ------------------------------------------------
    print(f"\n{BOLD}[1] Metadata{RESET}")
    record("name is set",               bool(adapter.name),               adapter.name)
    record("questions_answered is set", bool(adapter.questions_answered),  str(adapter.questions_answered))
    record("upstream_repo is set",      bool(adapter.upstream_repo),       adapter.upstream_repo)
    record("questions_answered only contains valid Q labels",
           all(q in {"Q1","Q2","Q3","Q4","Q5"} for q in adapter.questions_answered))

    # --- 2. Smoke test -------------------------------------------------------
    print(f"\n{BOLD}[2] Adapter smoke_test(){RESET}")
    t0  = time.time()
    ok, smoke_result, err = check("smoke_test()", adapter.smoke_test)
    elapsed = time.time() - t0
    if ok:
        if isinstance(smoke_result, dict):
            for k, v in smoke_result.items():
                if not record(f"  smoke: {k}", v):
                    failures += 1
        else:
            record("smoke_test() returned truthy", bool(smoke_result))
        record(f"smoke_test() completed in <300s", elapsed < 300,
               f"{elapsed:.1f}s")
    else:
        record("smoke_test() raised no exception", False, err)
        failures += 1

    if smoke_only:
        _print_summary(results, failures)
        return min(failures, 1)

    # --- 3. Q-method contract checks ----------------------------------------
    print(f"\n{BOLD}[3] Q-method outputs{RESET}")

    for q_label, method, schema_cls, call_kwargs in [
        ("Q1", adapter.q1_decision, Q1Decision,
         dict(ticker=SAMPLE_TICKER, date=SAMPLE_DATE)),
        ("Q2", adapter.q2_sentiment, Q2Sentiment,
         dict(ticker=SAMPLE_TICKER, date=SAMPLE_DATE)),
        ("Q3", adapter.q3_signal, Q3Signal,
         dict(ticker=SAMPLE_TICKER, date=SAMPLE_DATE)),
        ("Q4", adapter.q4_portfolio, Q4Portfolio,
         dict(tickers=SAMPLE_TICKERS, date=SAMPLE_DATE)),
        ("Q5", adapter.q5_backtest, Q5Backtest,
         dict(tickers=SAMPLE_TICKERS, start=SAMPLE_START, end=SAMPLE_END)),
    ]:
        claimed = q_label in adapter.questions_answered
        ok, result, err = check(f"{q_label}()", method, **call_kwargs)

        if not ok:
            if claimed:
                record(f"{q_label}: method raised exception (claimed to answer)", False, err)
                failures += 1
            else:
                record(f"{q_label}: not implemented (not in questions_answered)", True,
                       "skip — correct")
            continue

        if result is None:
            if claimed:
                record(f"{q_label}: returned None but is in questions_answered", False,
                       "must return a value if claimed")
                failures += 1
            else:
                record(f"{q_label}: returned None (not in questions_answered)", True, "skip")
            continue

        # validate schema
        if not isinstance(result, schema_cls):
            record(f"{q_label}: returned correct schema type ({schema_cls.__name__})", False,
                   f"got {type(result).__name__}")
            failures += 1
            continue

        try:
            dumped = result.model_dump()
            schema_cls.model_validate(dumped)
            record(f"{q_label}: Pydantic validation passed", True,
                   f"action={dumped.get('action','—')} conf={dumped.get('confidence','—')}")
        except Exception as ve:
            record(f"{q_label}: Pydantic validation", False, str(ve))
            failures += 1

    # --- 4. AdapterResult envelope ------------------------------------------
    print(f"\n{BOLD}[4] AdapterResult envelope (adapter.run()){RESET}")
    t0  = time.time()
    ok, ar, err = check("adapter.run()", adapter.run,
                        task_id=SAMPLE_TASK,
                        ticker=SAMPLE_TICKER,
                        tickers=SAMPLE_TICKERS,
                        date=SAMPLE_DATE,
                        start=SAMPLE_START,
                        end=SAMPLE_END)
    elapsed = time.time() - t0

    if ok and isinstance(ar, AdapterResult):
        try:
            json_str = ar.model_dump_json(indent=2)
            record("AdapterResult serialises to JSON", True,
                   f"{len(json_str)} bytes")
        except Exception as je:
            record("AdapterResult serialises to JSON", False, str(je))
            failures += 1
        record("adapter.run() completed in <600s", elapsed < 600, f"{elapsed:.1f}s")
    else:
        record("adapter.run() returned AdapterResult", False, err or f"got {type(ar).__name__}")
        failures += 1

    _print_summary(results, failures)
    return min(failures, 1)


def _print_summary(results, failures):
    total  = len(results)
    passed = sum(1 for _, p, _ in results if p)
    print(f"\n{BOLD}Summary: {passed}/{total} checks passed"
          f"{'  — ALL PASS' if failures == 0 else f'  — {failures} FAILURE(S)'}{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="AgentFusion adapter contract validator")
    parser.add_argument("--adapter", required=True, help="Path to adapter .py file")
    parser.add_argument("--smoke",   action="store_true",
                        help="Run only smoke_test() and metadata checks (fast)")
    args = parser.parse_args()

    try:
        adapter = load_adapter(args.adapter)
    except Exception as e:
        print(f"{FAIL} Could not load adapter: {e}")
        sys.exit(1)

    sys.exit(run_harness(adapter, smoke_only=args.smoke))


if __name__ == "__main__":
    main()
