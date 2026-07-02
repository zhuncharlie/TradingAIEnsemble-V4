"""
analysis/_run_one.py — invoke ONE adapter for ONE ticker in its own conda env,
write the resulting AdapterResult to results/{task_id}/{adapter_name}.json.

This is NOT an adapter (doesn't subclass BaseAdapter) and is not imported by
any adapter file — it's part of the comparison/analysis layer, which is
explicitly allowed to know about multiple adapters (that's the point of the
ensemble project). Each adapter still runs in its own conda env via
subprocess from analysis/collect_results.py, since the three adapters have
mutually incompatible pinned dependencies (see DECISIONS.md) and cannot be
imported into one Python process.

Usage:
    python analysis/_run_one.py --adapter adapters/fingpt_adapter.py \
        --ticker NVDA --date 2026-07-02 --task-id comparison_2026-07-02
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.test_harness import load_adapter  # reuses the harness's own loader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    adapter = load_adapter(args.adapter)
    out_dir = ROOT / "results" / args.task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{adapter.name}__{args.ticker}.json"

    try:
        result = adapter.run(
            task_id=args.task_id,
            ticker=args.ticker,
            tickers=[args.ticker],
            date=args.date,
        )
        out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f"OK {adapter.name} {args.ticker} -> {out_path}")
    except Exception as e:
        error_payload = {
            "adapter": adapter.name,
            "ticker": args.ticker,
            "date": args.date,
            "error": f"{type(e).__name__}: {e}",
        }
        out_path.write_text(json.dumps(error_payload, indent=2), encoding="utf-8")
        print(f"FAIL {adapter.name} {args.ticker}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
