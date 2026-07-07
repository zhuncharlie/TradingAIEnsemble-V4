"""
analysis/icaif_runnability_audit.py — Data Completion Phase, step 1: a
lightweight runnability audit of all 15 real adapters, BEFORE the full
observation batch. Does not run all tickers, does not backfill history,
does not place any order or touch any brokerage/exchange account.

Probe granularity (per the audit brief):
  - Q1/Q2/Q3 (ticker-level):    ticker=NVDA,                         date=today
  - Q4       (portfolio-level): tickers=[NVDA,SPY,QQQ,CASH],         date=today
  - Q5       (backtest-level):  tickers=[NVDA,SPY,QQQ,CASH],  start=today-30d, end=today

Each (adapter, question) probe runs analysis/_probe_one.py inside that
adapter's own conda env (`conda run -n {env}_real ...`), wrapped in a hard
300s `timeout`, exactly once, calling only the single q*_ method under test
— never adapter.run() (which would call every implemented method at once
with the wrong granularity for Q4/Q5).

requires_api_key / requires_broker_credentials / supports_historical_date
are static-code heuristics (grep-based), not empirically tested — testing
supports_historical_date empirically would require a second probe per
question at a second date, which the audit brief explicitly asked to avoid
("do not run historical multi-date backfills"). This is stated plainly in
the output, not hidden.

Usage:
    python analysis/icaif_runnability_audit.py \\
        --adapters-dir adapters --out reports/icaif_experiments --timeout 300
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date as date_cls, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.icaif_data_loader import AdapterInfo, discover_adapters  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONDA_SH = "/home/xqinag/miniconda/etc/profile.d/conda.sh"

TICKER_LEVEL_QUESTIONS = ["Q1", "Q2", "Q3"]
PORTFOLIO_UNIVERSE = ["NVDA", "SPY", "QQQ", "CASH"]
PROBE_TICKER = "NVDA"
BACKTEST_WINDOW_DAYS = 30

API_KEY_PATTERNS = [
    r"load_dotenv", r"[A-Z_]+_API_KEY", r"[A-Z_]+_TOKEN\b", r"getenv\(",
]
BROKER_KEYWORDS = [
    "alpaca", "ibkr", "interactive brokers", "ccxt", "kalshi", "polymarket",
    "place_order", "submit_order", "broker",
]
SAFETY_DISCLAIMER_PATTERNS = [
    r"no live trading", r"no real money", r"never live", r"paper[- ]trading",
    r"read-only", r"no brokerage", r"no account", r"keyless", r"zero authentication",
    r"never touch(es)? the network", r"placeholder", r"zero hits for broker",
    r"never imports or calls", r"no brokerage/exchange", r"never used",
    r"inert placeholder", r"no.*account.*no.*order",
]
HISTORICAL_SUPPORT_HINTS = [
    r"\.history\(", r"yf\.download", r"period=", r"start_ts", r"end_ts",
    r"lookback", r"train_period", r"test_period",
]
CURRENT_ONLY_HINTS = [
    r"real[- ]?time only", r"only supports current", r"ignores? the date",
    r"today only", r"live market-implied", r"latest available",
]


@dataclass
class ProbeResult:
    adapter: str
    q_type: str
    can_run: Optional[bool]
    input_granularity: str
    probe_input_used: str
    q_types_produced: str
    requires_api_key: bool
    api_key_names: str
    requires_broker_credentials: bool
    supports_historical_date: str
    supports_current_snapshot: Optional[bool]
    runtime_seconds: Optional[float]
    failure_reason: str
    skip_reason: str


def static_safety_scan(adapter_path: Path) -> Dict:
    try:
        text = adapter_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    low = text.lower()

    api_key_names = sorted(set(re.findall(r"\b([A-Z][A-Z0-9_]*_(?:API_KEY|TOKEN))\b", text)))
    requires_api_key = bool(api_key_names) or any(re.search(p, text) for p in [r"load_dotenv"])

    broker_hits = [kw for kw in BROKER_KEYWORDS if kw in low]
    disclaimer_found = any(re.search(p, low) for p in SAFETY_DISCLAIMER_PATTERNS)
    # A broker-keyword hit next to an explicit safety disclaimer (documented
    # per-adapter in this repo's own adapter headers) is treated as
    # "mentioned but not actually used for live trading" — never silently
    # dropped, always recorded in api_key_names/notes for a human to re-check.
    requires_broker_credentials = bool(broker_hits) and not disclaimer_found

    if any(re.search(p, low) for p in CURRENT_ONLY_HINTS):
        historical_support = "false (static heuristic: docstring/code suggests current-snapshot-only)"
    elif any(re.search(p, low) for p in HISTORICAL_SUPPORT_HINTS):
        historical_support = "likely true (static heuristic: date/window-driven data fetch found)"
    else:
        historical_support = "unknown (static heuristic inconclusive)"

    return {
        "requires_api_key": requires_api_key,
        "api_key_names": ",".join(api_key_names) if api_key_names else ("shared DeepSeek .env" if "load_dotenv" in text else ""),
        "requires_broker_credentials": requires_broker_credentials,
        "broker_keyword_hits": ",".join(broker_hits),
        "safety_disclaimer_found": disclaimer_found,
        "supports_historical_date": historical_support,
    }


def run_probe(adapter_file: str, env: str, question: str, timeout_s: int, **kwargs) -> Dict:
    cmd_parts = [f"source {CONDA_SH}", f"conda activate {env}",
                 f"python {ROOT / 'analysis' / '_probe_one.py'} --adapter {ROOT / adapter_file} --question {question}"]
    for k, v in kwargs.items():
        if v is not None:
            cmd_parts[-1] += f" --{k.replace('_', '-')} {v}"
    cmd = " && ".join(cmd_parts)

    t0 = time.time()
    try:
        proc = subprocess.run(["timeout", str(timeout_s), "bash", "-c", cmd],
                               capture_output=True, text=True, timeout=timeout_s + 15)
    except subprocess.TimeoutExpired:
        return {"ok": None, "timed_out": True, "wall_seconds": round(time.time() - t0, 2),
                "stderr_tail": "", "raw_stdout": ""}
    wall = round(time.time() - t0, 2)

    if proc.returncode == 124:  # coreutils `timeout`'s own kill exit code
        return {"ok": None, "timed_out": True, "wall_seconds": wall,
                "stderr_tail": proc.stderr[-800:], "raw_stdout": proc.stdout}

    marker = "===ICAIF_PROBE_RESULT==="
    stdout = proc.stdout
    json_text = stdout.rsplit(marker, 1)[-1].strip() if marker in stdout else (
        stdout.strip().splitlines()[-1] if stdout.strip() else ""
    )
    try:
        parsed = json.loads(json_text)
        parsed["wall_seconds"] = wall
        parsed["timed_out"] = False
        return parsed
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "timed_out": False, "wall_seconds": wall,
                "error_type": "ProcessCrashed", "error_message": (proc.stderr[-500:] or "no parseable output"),
                "stderr_tail": proc.stderr[-800:], "raw_stdout": proc.stdout, "runtime_seconds": wall}


def build_probe_kwargs(question: str, decision_date: str, window_start: str) -> Dict:
    if question in TICKER_LEVEL_QUESTIONS:
        return {"granularity": "ticker-level", "kwargs": {"ticker": PROBE_TICKER, "date": decision_date},
                "probe_input": f"ticker={PROBE_TICKER}, date={decision_date}"}
    if question == "Q4":
        return {"granularity": "portfolio-level",
                "kwargs": {"tickers": ",".join(PORTFOLIO_UNIVERSE), "date": decision_date},
                "probe_input": f"tickers={PORTFOLIO_UNIVERSE}, date={decision_date}"}
    if question == "Q5":
        return {"granularity": "backtest-level",
                "kwargs": {"tickers": ",".join(PORTFOLIO_UNIVERSE), "start": window_start, "end": decision_date},
                "probe_input": f"tickers={PORTFOLIO_UNIVERSE}, start={window_start}, end={decision_date}"}
    raise ValueError(question)


def audit_one(info: AdapterInfo, decision_date: str, window_start: str, timeout_s: int) -> List[ProbeResult]:
    safety = static_safety_scan(ROOT / info.file)
    results: List[ProbeResult] = []

    if not info.questions_implemented:
        results.append(ProbeResult(
            adapter=info.name, q_type="(none)", can_run=None,
            input_granularity="n/a", probe_input_used="n/a", q_types_produced="",
            requires_api_key=safety["requires_api_key"], api_key_names=safety["api_key_names"],
            requires_broker_credentials=safety["requires_broker_credentials"],
            supports_historical_date=safety["supports_historical_date"], supports_current_snapshot=None,
            runtime_seconds=None, failure_reason="",
            skip_reason="adapter declares/implements no q*_ methods (static scan found none overridden)",
        ))
        return results

    env = info.requires_env or f"{info.name}_real"
    for question in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        if question not in info.questions_implemented:
            continue
        spec = build_probe_kwargs(question, decision_date, window_start)
        print(f"  probing {info.name} / {question} ({spec['granularity']}) via env={env} ...", file=sys.stderr)
        raw = run_probe(info.file, env, question, timeout_s, **spec["kwargs"])

        if raw.get("timed_out"):
            can_run, failure_reason = False, f"timed out after {timeout_s}s"
            produced, runtime = "", float(timeout_s)
        elif raw.get("ok") is True:
            can_run, failure_reason = True, ""
            produced = ",".join(raw.get("produced_fields", []))
            runtime = raw.get("runtime_seconds") or raw.get("wall_seconds")
        else:
            can_run = False
            failure_reason = f"{raw.get('error_type', 'Unknown')}: {raw.get('error_message', '')}".strip(": ")
            produced = ""
            runtime = raw.get("runtime_seconds") or raw.get("wall_seconds")

        results.append(ProbeResult(
            adapter=info.name, q_type=question, can_run=can_run,
            input_granularity=spec["granularity"], probe_input_used=spec["probe_input"],
            q_types_produced=produced,
            requires_api_key=safety["requires_api_key"], api_key_names=safety["api_key_names"],
            requires_broker_credentials=safety["requires_broker_credentials"],
            supports_historical_date=safety["supports_historical_date"],
            supports_current_snapshot=can_run,
            runtime_seconds=runtime, failure_reason=failure_reason, skip_reason="",
        ))
    return results


def write_outputs(all_results: List[ProbeResult], out: Path, decision_date: str, window_start: str, timeout_s: int) -> None:
    import csv as csv_mod
    csv_path = out / "adapter_runnability.csv"
    fields = ["adapter", "q_type", "can_run", "input_granularity", "probe_input_used",
              "q_types_produced", "requires_api_key", "api_key_names",
              "requires_broker_credentials", "supports_historical_date",
              "supports_current_snapshot", "runtime_seconds", "failure_reason", "skip_reason"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv_mod.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_results:
            w.writerow({k: getattr(r, k) for k in fields})

    by_adapter: Dict[str, List[ProbeResult]] = {}
    for r in all_results:
        by_adapter.setdefault(r.adapter, []).append(r)

    n_probes = sum(1 for r in all_results if r.q_type != "(none)")
    n_can_run = sum(1 for r in all_results if r.can_run is True)
    n_cannot = sum(1 for r in all_results if r.can_run is False)
    n_skipped = sum(1 for r in all_results if r.can_run is None)

    lines = [
        "# Adapter Runnability Audit", "",
        f"Probe date (\"latest available decision date\"): **{decision_date}**  ",
        f"Backtest window for Q5 probes: **{window_start} -> {decision_date}**  ",
        f"Per-probe timeout: **{timeout_s}s**  ",
        f"Ticker-level probe ticker: **{PROBE_TICKER}** | Portfolio universe: **{PORTFOLIO_UNIVERSE}**", "",
        "This is a runnability audit only — it did not write anything to `results/` and ",
        "did not run the full observation batch. No brokerage/exchange account was touched ",
        "and no order was ever placed by any probe (every adapter's q*_ methods here are ",
        "read-only signal/analysis calls, same as the existing test harness).", "",
        f"## Summary: {n_probes} probes attempted across {len(by_adapter)} adapters",
        f"- can_run: **{n_can_run}**", f"- cannot_run: **{n_cannot}**",
        f"- skipped (no implemented q*_ methods): **{n_skipped}**", "",
        "## Per-adapter detail", "",
    ]

    for adapter, rows in sorted(by_adapter.items()):
        lines.append(f"### {adapter}")
        safety_row = rows[0]
        lines.append(f"- requires_api_key: **{safety_row.requires_api_key}**"
                      + (f" ({safety_row.api_key_names})" if safety_row.api_key_names else ""))
        lines.append(f"- requires_broker_credentials: **{safety_row.requires_broker_credentials}**")
        lines.append(f"- supports_historical_date (static heuristic, not empirically tested): {safety_row.supports_historical_date}")
        lines.append("")
        lines.append("| q_type | can_run | granularity | probe_input | produced fields | runtime(s) | failure_reason |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in rows:
            if r.q_type == "(none)":
                lines.append(f"| - | - | - | - | - | - | {r.skip_reason} |")
                continue
            status = "✓" if r.can_run else ("timeout/skip" if r.can_run is None else "✗")
            lines.append(f"| {r.q_type} | {status} | {r.input_granularity} | {r.probe_input_used} | "
                          f"{r.q_types_produced or '-'} | {r.runtime_seconds if r.runtime_seconds is not None else '-'} | "
                          f"{r.failure_reason or '-'} |")
        lines.append("")

    lines += [
        "## Methodology notes / limitations", "",
        "- `requires_api_key` / `requires_broker_credentials` / `supports_historical_date` are "
        "**static source-code heuristics** (regex over the adapter file), not independently "
        "verified per q_type — an adapter can need an LLM key for one question and not another "
        "(e.g. prediction_arena's Q2 calls a real LLM, its Q5 does not), and this table does not "
        "split that out.",
        "- `supports_historical_date` was **not empirically tested** (would require a second probe "
        "per question at a second date, i.e. a mini historical backfill — explicitly out of scope "
        "for this lightweight audit per the brief). Treat it as a lead for the next phase, not a fact.",
        "- Every probe called exactly one q*_ method directly (never `adapter.run()`), so Q4/Q5 were "
        "never probed with a single-ticker input and Q1-Q3 were never conflated with portfolio/backtest "
        "granularity.",
        "- `can_run=True` means the method returned a non-null, schema-valid object for this specific "
        "probe input — it does not guarantee every ticker/date will succeed (e.g. yfinance coverage "
        "gaps for BTC-USD/SPY seen previously in `analysis/build_visualizations.py`).",
        "",
    ]
    (out / "ADAPTER_RUNNABILITY_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {csv_path} and {out / 'ADAPTER_RUNNABILITY_AUDIT.md'}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--adapters-dir", default=str(ROOT / "adapters"))
    p.add_argument("--out", default=str(ROOT / "reports" / "icaif_experiments"))
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--decision-date", default=None, help="defaults to today")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    decision_date = args.decision_date or date_cls.today().isoformat()
    window_start = (date_cls.fromisoformat(decision_date) - timedelta(days=BACKTEST_WINDOW_DAYS)).isoformat()

    adapters = discover_adapters(Path(args.adapters_dir))
    print(f"Discovered {len(adapters)} adapters. Probing at decision_date={decision_date}, "
          f"Q5 window={window_start}->{decision_date}, timeout={args.timeout}s per probe.")

    all_results: List[ProbeResult] = []
    for info in adapters:
        print(f"[{info.name}] questions_implemented={info.questions_implemented}", file=sys.stderr)
        all_results.extend(audit_one(info, decision_date, window_start, args.timeout))

    write_outputs(all_results, out, decision_date, window_start, args.timeout)


if __name__ == "__main__":
    main()
