"""
analysis/_probe_one.py — invoke exactly ONE q*_ method on ONE adapter, for
the Data-Completion-Phase runnability audit (analysis/icaif_runnability_audit.py).

Unlike analysis/_run_one.py (which calls adapter.run() and populates every
implemented q* method with the same ticker/date), this probes a single
question with the input granularity that question actually needs:
  - Q1/Q2/Q3: one ticker + one date
  - Q4:       a ticker universe + one date
  - Q5:       a ticker universe + a start/end window

Prints exactly one JSON object to stdout and exits 0 on a completed attempt
(success or a caught application error) — the orchestrator distinguishes
success from failure by the "ok" field, not by exit code. A non-zero exit
or empty stdout means the process itself crashed/was killed (e.g. by the
orchestrator's `timeout` wrapper), which the orchestrator treats as a
timeout/crash rather than a clean failure.

Never places an order, never touches a brokerage/exchange account — it only
calls the adapter's read-only q*_ method, exactly like the existing harness.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.test_harness import load_adapter  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", required=True)
    p.add_argument("--question", required=True, choices=["Q1", "Q2", "Q3", "Q4", "Q5"])
    p.add_argument("--ticker", default=None)
    p.add_argument("--tickers", default=None, help="comma-separated")
    p.add_argument("--date", default=None)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--emit-full", action="store_true",
                    help="include the full model_dump() payload in the result "
                         "(used by the observation batch runner to save real output; "
                         "the runnability audit doesn't need this)")
    args = p.parse_args()

    tickers = args.tickers.split(",") if args.tickers else None
    result = {
        "adapter": None, "question": args.question, "ok": False,
        "produced_fields": [], "error_type": None, "error_message": None,
        "runtime_seconds": None,
    }

    t0 = time.time()
    try:
        adapter = load_adapter(args.adapter)
        result["adapter"] = adapter.name

        if args.question == "Q1":
            out = adapter.q1_decision(args.ticker, args.date)
        elif args.question == "Q2":
            out = adapter.q2_sentiment(args.ticker, args.date)
        elif args.question == "Q3":
            out = adapter.q3_signal(args.ticker, args.date)
        elif args.question == "Q4":
            out = adapter.q4_portfolio(tickers, args.date)
        elif args.question == "Q5":
            out = adapter.q5_backtest(tickers, args.start, args.end)
        else:
            out = None

        result["runtime_seconds"] = round(time.time() - t0, 2)
        if out is None:
            result["ok"] = False
            result["error_type"] = "NoneReturned"
            result["error_message"] = "q*_ method returned None (declared/implemented but produced no output for this input)"
        else:
            result["ok"] = True
            result["produced_fields"] = sorted(
                k for k, v in out.model_dump().items()
                if v is not None and v != [] and v != {} and v != ""
            )
            if args.emit_full:
                result["full_payload"] = out.model_dump(mode="json")
    except Exception as e:  # noqa: BLE001 — audit needs to see every failure mode, not just expected ones
        result["runtime_seconds"] = round(time.time() - t0, 2)
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)[:500]

    # Some upstream libraries (e.g. ai-hedge-fund's progress bar) write to
    # stdout without a trailing newline, which can glue onto this line. A
    # unique sentinel lets the orchestrator find the JSON regardless of what
    # came before it, instead of naively trusting "last line after splitlines()".
    print("\n===ICAIF_PROBE_RESULT===")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
