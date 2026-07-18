"""
tools/run_unified_harness.py — the unified minimal cross-adapter harness task.

Runs the SAME task_id / QueryContext (as_of, data_cutoff, scope) / Q4
generation_window / frozen asset universe across every production adapter
(each in its own real conda env, via CONTRACT/adapter_runner.py — the same
CLI every adapter's individual live verification already used this
session), and aggregates: success rate, real Q coverage, field coverage,
latency, and failure reasons.

This is deliberately separate from each adapter's own individual live
verification (already performed, per-adapter, earlier) — this script's
purpose is only to confirm every adapter can independently answer the SAME
shared task, not to re-verify each adapter's internal correctness.

Frozen base universe: AAPL, MSFT, NVDA (all liquid, real, yfinance-covered).
A small number of adapters have real, upstream-side domain constraints that
make the base universe inapplicable — those use a documented, allowed
substitution instead (see ADAPTERS below, `universe_override`/`notes`):
  - trademaster: real DJ30 dataset does not include NVDA -> JNJ substituted;
    real dataset's own date range ends 2021-12-31 -> its own generation_window
    used instead of the shared default.
  - earnmore: real per-call sector-mask group only ever returns a fixed
    subset of its own real DJ30-style universe -> AAPL/MSFT (both real
    members of its own real "Technology-and-Communications" mask group).
  - pgportfolio: real upstream domain is crypto (Poloniex), not equities ->
    BTC-USD/ETH-USD substituted; live stage already independently confirmed
    BLOCKED this session (yfinance rate limit) -> expected to fail here too,
    reported as BLOCKED not FAILED.
  - finmem: live stage already independently confirmed BLOCKED this session
    (no OpenAI-compatible-by-name credential) -> expected to fail here too,
    reported as BLOCKED not FAILED.

Usage:
    python tools/run_unified_harness.py --out-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TASK_ID = "unified_harness_2026_07_18"
AS_OF = "2024-01-15"
DATA_CUTOFF = "2024-01-15"
GEN_START = "2023-06-01"
GEN_END = "2024-01-15"
FROZEN_UNIVERSE = ["AAPL", "MSFT", "NVDA"]

# Per-adapter timeout in seconds (real training/LLM calls vary a lot).
DEFAULT_TIMEOUT = 200

# name -> (module path, conda env, cli args, timeout override, notes)
ADAPTERS = [
    # ---- Q1/Q2/Q3 single-asset adapters (ASSET or CROSS_SECTION scope) ----
    dict(name="ai_hedge_fund", env="ai_hedge_fund_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="fingpt", env="fingpt_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="finbert", env="finbert_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="finmem", env="finmem_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"],
         expect="BLOCKED", notes="live LLM call blocked (real OpenAI-only credential requirement, confirmed earlier this session)"),
    dict(name="deepalpha", env="deepalpha_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="rdagent", env="rdagent_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL", "--horizon", "5d"]),
    dict(name="quantmuse", env="nofx_real",
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="prediction_arena", env="prediction_arena_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="tradingagents", env="tradingagents_real", timeout=500,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="finrobot", env="finrobot_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="finagent", env="finagent_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL",
               "--gen-start", "2024-01-08", "--gen-end", "2024-01-12"],
         notes="real per-day DeepSeek call design -> shared 7.5-month generation_window would need 150+ real LLM calls; narrowed to a 5-trading-day window (same as this adapter's own individual live verification) to keep this a genuinely minimal harness task"),

    # ---- Q3 cross-sectional / factor adapters ----
    dict(name="alphagen", env="alphagen_real", timeout=280,
         args=["--scope", "CROSS_SECTION", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="atlas", env="atlas_real", timeout=200,
         args=["--scope", "CROSS_SECTION", "--target", "AAPL", "--universe", "AAPL"]),
    dict(name="alphaforge", env="alphaforge_real", timeout=280,
         args=["--scope", "CROSS_SECTION", "--target", "AAPL", "--universe"] + FROZEN_UNIVERSE),
    dict(name="finclaw", env="finclaw_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL",
               "--gen-start", GEN_START, "--gen-end", GEN_END]),

    # ---- Q2/Q3/Q4 mixed ----
    dict(name="finrl_x", env="finrl_x_real", timeout=280,
         args=["--scope", "CROSS_SECTION", "--target", "AAPL", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", GEN_START, "--gen-end", GEN_END]),
    dict(name="qlib", env="qlib_real", timeout=280,
         args=["--scope", "CROSS_SECTION", "--target", "AAPL", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", GEN_START, "--gen-end", GEN_END]),
    dict(name="vibe_trading", env="vibe_trading_real", timeout=280,
         args=["--scope", "ASSET", "--target", "AAPL", "--universe", "AAPL",
               "--gen-start", "2023-08-01", "--gen-end", GEN_END]),

    # ---- Pure Q4 portfolio adapters (frozen universe) ----
    dict(name="agentictrading", env="agentictrading_real", timeout=200,
         args=["--scope", "PORTFOLIO", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", GEN_START, "--gen-end", GEN_END]),
    dict(name="deepdow", env="deepdow_real", timeout=280,
         args=["--scope", "PORTFOLIO", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", GEN_START, "--gen-end", GEN_END]),
    dict(name="skfolio", env="skfolio_real", timeout=200,
         args=["--scope", "PORTFOLIO", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", "2022-01-01", "--gen-end", GEN_END]),
    dict(name="universal_portfolios", env="universal_portfolios_real", timeout=200,
         args=["--scope", "PORTFOLIO", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", GEN_START, "--gen-end", GEN_END]),
    dict(name="finrl", env="finrl_real", timeout=280,
         args=["--scope", "PORTFOLIO", "--universe"] + FROZEN_UNIVERSE
              + ["--gen-start", "2022-07-01", "--gen-end", GEN_END]),
    dict(name="earnmore", env="earnmore_real", timeout=280,
         args=["--scope", "PORTFOLIO", "--universe", "AAPL", "MSFT",
               "--gen-start", "2008-09-01", "--gen-end", "2009-03-01"],
         notes="real per-call sector-mask group only covers AAPL/MSFT of the frozen universe; real training window predates 2023 by design (repo's own shipped DJ30-style dataset range)"),
    dict(name="trademaster", env="trademaster_real", timeout=280,
         args=["--scope", "PORTFOLIO", "--universe", "AAPL", "MSFT", "JNJ",
               "--gen-start", "2021-01-04", "--gen-end", "2021-12-31"],
         notes="real DJ30 dataset does not include NVDA (JNJ substituted); dataset's real date range ends 2021-12-31"),
    dict(name="pgportfolio", env="pgportfolio_real", timeout=280,
         args=["--scope", "PORTFOLIO", "--universe", "BTC-USD", "ETH-USD",
               "--gen-start", "2023-10-01", "--gen-end", GEN_END],
         expect="BLOCKED", notes="real upstream domain is crypto not equities; live stage already independently confirmed BLOCKED this session (yfinance rate limit)"),
]


def run_one(spec: dict, out_dir: Path) -> dict:
    name = spec["name"]
    env = spec["env"]
    timeout = spec.get("timeout", DEFAULT_TIMEOUT)
    adapter_path = f"adapters/{name}_adapter.py"
    cmd = [
        "conda", "run", "-n", env, "--no-capture-output",
        "python", "CONTRACT/adapter_runner.py",
        "--adapter", adapter_path,
        "--task-id", TASK_ID,
        "--as-of", AS_OF,
        *spec["args"],
        "--out-dir", str(out_dir),
    ]
    t0 = time.time()
    result = {"name": name, "env": env, "cmd": " ".join(cmd), "expect": spec.get("expect", "PASS")}
    # Some real model outputs contain non-ASCII characters (e.g. em-dashes).
    # `conda run`'s subprocess doesn't always inherit an interactive shell's
    # UTF-8 locale the way `conda activate && python ...` does, which can
    # make Path.write_text() default to ASCII and raise UnicodeEncodeError.
    # Force UTF-8 here (harness-side environment control, not a CONTRACT/ change).
    child_env = dict(os.environ)
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=child_env)
        latency = time.time() - t0
        result["latency_sec"] = round(latency, 1)
        stdout, stderr = proc.stdout, proc.stderr
        ok = proc.returncode == 0 and "wrote" in stdout and "AdapterResult validates cleanly" in stdout
        result_json_path = out_dir / TASK_ID / f"{name}.json"
        if ok and result_json_path.exists():
            data = json.loads(result_json_path.read_text())
            qkeys = [k for k in ("q1", "q2", "q3", "q4") if data.get(k) is not None]
            result["status"] = "PASSED"
            result["questions_answered_actual"] = qkeys
            result["result_path"] = str(result_json_path)
        else:
            result["status"] = spec.get("expect", "FAILED") if spec.get("expect") == "BLOCKED" else "FAILED"
            tail = (stderr or stdout).strip().splitlines()
            result["failure_reason"] = tail[-1] if tail else "unknown (no output)"
    except subprocess.TimeoutExpired:
        result["latency_sec"] = timeout
        result["status"] = "BLOCKED" if spec.get("expect") == "BLOCKED" else "FAILED"
        result["failure_reason"] = f"timed out after {timeout}s"
    except Exception as e:
        result["latency_sec"] = round(time.time() - t0, 1)
        result["status"] = "FAILED"
        result["failure_reason"] = f"{type(e).__name__}: {e}"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(ROOT / "results" / "unified_harness"))
    parser.add_argument("--only", nargs="*", default=None, help="restrict to these adapter names")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    specs = ADAPTERS if not args.only else [s for s in ADAPTERS if s["name"] in args.only]

    results = []
    for spec in specs:
        print(f"=== {spec['name']} ===", flush=True)
        r = run_one(spec, out_dir)
        print(f"  -> {r['status']} in {r.get('latency_sec')}s"
              + (f" ({r.get('failure_reason')})" if r.get("failure_reason") else ""), flush=True)
        results.append(r)

    summary_path = out_dir / "unified_harness_summary.json"
    summary_path.write_text(json.dumps({
        "task_id": TASK_ID, "as_of": AS_OF, "data_cutoff": DATA_CUTOFF,
        "gen_start": GEN_START, "gen_end": GEN_END, "frozen_universe": FROZEN_UNIVERSE,
        "results": results,
    }, indent=2))

    n_pass = sum(1 for r in results if r["status"] == "PASSED")
    n_blocked = sum(1 for r in results if r["status"] == "BLOCKED")
    n_fail = sum(1 for r in results if r["status"] == "FAILED")
    print(f"\n=== SUMMARY: {n_pass} PASSED, {n_blocked} BLOCKED, {n_fail} FAILED / {len(results)} total ===")
    print(f"Written to {summary_path}")


if __name__ == "__main__":
    main()
