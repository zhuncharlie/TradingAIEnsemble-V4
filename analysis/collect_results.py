"""
analysis/collect_results.py — run all registered adapters across a fixed
ticker list, each in its own conda env, and collect their AdapterResults.

Part of the comparison/analysis layer (not an adapter itself — this is the
one place in the project that's explicitly meant to know about all adapters
at once, per the project's own stated purpose in CLAUDE.md: "see how
different frameworks answer it — consensus vs. divergence, side by side").

The three adapters have mutually incompatible pinned dependencies (FinGPT
needs transformers==4.41.2, ai-hedge-fund needs a Rust-built tiktoken via
poetry, DeepAlpha needs conda-forge xgboost/lightgbm) and cannot be imported
into one Python process — see DECISIONS.md. This script shells out to each
adapter's own conda env via `conda run`.

Usage:
    python analysis/collect_results.py --task-id comparison_2026-07-02
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TICKERS = ["AAPL", "NVDA", "TSLA", "BTC-USD", "SPY"]

ADAPTERS = [
    ("adapters/ai_hedge_fund_adapter.py", "ai_hedge_fund_real"),
    ("adapters/fingpt_adapter.py", "fingpt_real"),
    ("adapters/deepalpha_adapter.py", "deepalpha_real"),
]

CONDA_SH = "/home/xqinag/miniconda/etc/profile.d/conda.sh"


def run_one(adapter_path: str, env: str, ticker: str, date: str, task_id: str) -> bool:
    cmd = (
        f"source {CONDA_SH} && conda activate {env} && "
        f"python {ROOT / 'analysis' / '_run_one.py'} "
        f"--adapter {ROOT / adapter_path} --ticker {ticker} --date {date} --task-id {task_id}"
    )
    proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=900)
    print(proc.stdout.strip())
    if proc.returncode != 0 or "FAIL" in proc.stdout:
        print(proc.stderr[-2000:], file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--date", default=None, help="Defaults to today (YYYY-MM-DD)")
    parser.add_argument("--tickers", nargs="*", default=TICKERS)
    args = parser.parse_args()

    from datetime import date as date_cls
    date_str = args.date or date_cls.today().isoformat()

    results = {}
    for adapter_path, env in ADAPTERS:
        for ticker in args.tickers:
            key = (Path(adapter_path).stem, ticker)
            ok = run_one(adapter_path, env, ticker, date_str, args.task_id)
            results[key] = ok

    failures = [k for k, ok in results.items() if not ok]
    print(f"\n{len(results) - len(failures)}/{len(results)} adapter x ticker runs succeeded")
    if failures:
        print("Failures (see per-run JSON in results/ for error detail):")
        for adapter_name, ticker in failures:
            print(f"  - {adapter_name} / {ticker}")


if __name__ == "__main__":
    main()
