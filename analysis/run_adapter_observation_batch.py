"""
analysis/run_adapter_observation_batch.py — Data Completion Phase, step 2:
generate real observed Q1-Q5 result JSONs across a diversified multi-asset
universe, for every adapter/question combo that passed the runnability audit
(reports/icaif_experiments/adapter_runnability.csv), then rerun the ICAIF
experiment layer and write a summary.

This is ONE self-contained pipeline (batch -> optional historical extension
-> analysis.icaif_experiments rerun -> summary) so it can run unattended in
the background for hours: nothing about it depends on a human driving each
phase.

Resumability / checkpointing:
  - reads adapter_runnability.csv, only attempts can_run==True rows
  - reads any existing index.csv for this batch_id and skips
    (adapter, q_type, input_id, decision_date) rows already
    success=True and schema_valid=True, unless --force
  - every completed job appends one row to index.csv immediately (flushed +
    fsynced), so a kill at any point leaves a valid, resumable partial index
  - every successful job writes its normalized JSON immediately under
    results/observations/{batch_id}/{decision_date}/{adapter}/{q_type}/{input_id}.json

Concurrency: adapters needing an LLM/API key run in a 2-worker pool (shared
DeepSeek key across most of them); adapters needing no key run in a 4-worker
pool. Within either pool, no two jobs of the SAME adapter ever run at once
(a per-adapter lock) — this both satisfies "never run TradingAgents debates
in parallel" and generally prefers correctness over speed for every adapter,
per the batch brief.

Wall-clock budget: stops LAUNCHING new jobs --launch-cutoff-hours (default 7)
after this process started; in-flight jobs (each individually timeout-capped)
are allowed to finish, then this same process reruns
`python -m analysis.icaif_experiments` and writes
reports/icaif_experiments/OBSERVATION_BATCH_DAY1_SUMMARY.md.

Never calls adapter.run() (which would apply one ticker/date to every
implemented method, wrong for Q4/Q5) — every job invokes exactly one q*_
method via analysis/_probe_one.py --emit-full, in that adapter's own conda
env, wrapped in a hard `timeout`. Never places an order, never touches a
brokerage/exchange account.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import date as date_cls, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.icaif_data_loader import discover_adapters, discover_result_files  # noqa: E402

CONDA_SH = "/home/xqinag/miniconda/etc/profile.d/conda.sh"

TICKER_UNIVERSE = ["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ", "JPM", "XOM", "JNJ", "GLD"]
PORTFOLIO_UNIVERSE = ["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ", "JPM", "XOM", "JNJ", "TLT", "GLD", "CASH"]
HIST_TICKER_UNIVERSE = ["NVDA", "SPY", "QQQ", "JPM", "GLD"]
Q5_WINDOW_DAYS = 30
N_HIST_DATES = 5
HIST_MIN_TRADING_DAYS_BACK = 20

INDEX_FIELDS = [
    "batch_id", "adapter", "q_type", "input_granularity", "ticker_or_universe_id",
    "decision_date", "success", "schema_valid", "runtime_seconds", "timeout",
    "error_message", "raw_output_path", "normalized_output_path",
    "requires_api_key", "requires_broker_credentials", "supports_historical_date", "notes",
]


@dataclass
class Job:
    batch_id: str
    adapter: str
    q_type: str
    env: str
    adapter_file: str
    input_granularity: str
    input_id: str
    decision_date: str
    probe_kwargs: Dict[str, str]
    timeout_s: int
    requires_api_key: bool
    requires_broker_credentials: bool
    supports_historical_date: str
    is_llm: bool
    out_dir: Path
    notes: str = ""


def pick_timeout(adapter: str, q_type: str, requires_api_key: bool) -> int:
    if adapter == "tradingagents" and q_type in ("Q1", "Q2"):
        return 360
    if q_type in ("Q4", "Q5"):
        return 300
    if requires_api_key:
        return 180
    return 120


def load_runnable_rows(csv_path: Path) -> List[dict]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("can_run") == "True":
                rows.append(r)
    return rows


def env_lookup(adapters_dir: Path) -> Dict[str, str]:
    infos = discover_adapters(adapters_dir)
    return {i.name: (i.requires_env or f"{i.name}_real") for i in infos}


def business_days_back(end: date_cls, n_back: int) -> date_cls:
    d = end
    steps = 0
    while steps < n_back:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            steps += 1
    return d


def pick_historical_dates(today: date_cls, n_dates: int, min_trading_days_back: int) -> List[str]:
    """n_dates business days, evenly spaced, all >= min_trading_days_back
    business days before `today` (so 20-trading-day forward returns are
    computable using data up to today)."""
    farthest = business_days_back(today, min_trading_days_back + (n_dates - 1) * 4)
    nearest = business_days_back(today, min_trading_days_back)
    span_days = (nearest - farthest).days
    step = max(1, span_days // max(1, n_dates - 1)) if n_dates > 1 else 0
    dates = []
    d = farthest
    while d <= nearest and len(dates) < n_dates:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += timedelta(days=step if step else 1)
    return dates[:n_dates]


def build_jobs_for_rows(
    rows: List[dict], envs: Dict[str, str], decision_date: str, batch_id: str,
    out_root: Path, tickers: List[str], portfolio: List[str],
) -> List[Job]:
    window_start = (date_cls.fromisoformat(decision_date) - timedelta(days=Q5_WINDOW_DAYS)).isoformat()
    jobs: List[Job] = []
    for r in rows:
        adapter, q = r["adapter"], r["q_type"]
        env = envs.get(adapter, f"{adapter}_real")
        requires_api_key = r["requires_api_key"] == "True"
        requires_broker = r["requires_broker_credentials"] == "True"
        hist_support = r["supports_historical_date"]
        timeout_s = pick_timeout(adapter, q, requires_api_key)
        base_out = out_root / decision_date / adapter / q
        notes = ""
        if adapter == "atlas" and q == "Q3":
            notes = ("KNOWN LIMITATION: atlas's bundled dataset is crypto-perpetuals only "
                      "(2021-11-06..2024-08-14); any equity/ETF ticker requested falls back "
                      "to reporting the same BTCUSDT signal under the requested ticker label "
                      "(self-disclosed in supporting_evidence) — all 10 tickers here will be "
                      "numerically identical to each other.")

        if q in ("Q1", "Q2", "Q3"):
            for ticker in tickers:
                jobs.append(Job(
                    batch_id=batch_id, adapter=adapter, q_type=q, env=env, adapter_file=r.get("adapter_file", f"adapters/{adapter}_adapter.py"),
                    input_granularity="ticker-level", input_id=ticker, decision_date=decision_date,
                    probe_kwargs={"ticker": ticker, "date": decision_date}, timeout_s=timeout_s,
                    requires_api_key=requires_api_key, requires_broker_credentials=requires_broker,
                    supports_historical_date=hist_support, is_llm=requires_api_key,
                    out_dir=base_out, notes=notes,
                ))
        elif q == "Q4":
            jobs.append(Job(
                batch_id=batch_id, adapter=adapter, q_type=q, env=env, adapter_file=f"adapters/{adapter}_adapter.py",
                input_granularity="portfolio-level", input_id="portfolio_universe", decision_date=decision_date,
                probe_kwargs={"tickers": ",".join(portfolio), "date": decision_date}, timeout_s=timeout_s,
                requires_api_key=requires_api_key, requires_broker_credentials=requires_broker,
                supports_historical_date=hist_support, is_llm=requires_api_key,
                out_dir=base_out, notes=notes,
            ))
        elif q == "Q5":
            jobs.append(Job(
                batch_id=batch_id, adapter=adapter, q_type=q, env=env, adapter_file=f"adapters/{adapter}_adapter.py",
                input_granularity="backtest-level", input_id="portfolio_universe", decision_date=decision_date,
                probe_kwargs={"tickers": ",".join(portfolio), "start": window_start, "end": decision_date},
                timeout_s=timeout_s, requires_api_key=requires_api_key, requires_broker_credentials=requires_broker,
                supports_historical_date=hist_support, is_llm=requires_api_key,
                out_dir=base_out, notes=notes,
            ))
    return jobs


# --------------------------------------------------------------------------- #
# Execution engine
# --------------------------------------------------------------------------- #

_adapter_locks: Dict[str, threading.Lock] = {}
_adapter_locks_guard = threading.Lock()


def _lock_for(adapter: str) -> threading.Lock:
    with _adapter_locks_guard:
        if adapter not in _adapter_locks:
            _adapter_locks[adapter] = threading.Lock()
        return _adapter_locks[adapter]


def run_probe_full(job: Job) -> dict:
    cmd = (
        f"source {CONDA_SH} && conda activate {job.env} && "
        f"python {ROOT / 'analysis' / '_probe_one.py'} --adapter {ROOT / job.adapter_file} "
        f"--question {job.q_type} --emit-full"
    )
    for k, v in job.probe_kwargs.items():
        cmd += f" --{k.replace('_', '-')} {v}"

    t0 = time.time()
    try:
        proc = subprocess.run(["timeout", str(job.timeout_s), "bash", "-c", cmd],
                               capture_output=True, text=True, timeout=job.timeout_s + 20)
    except subprocess.TimeoutExpired:
        return {"ok": None, "timed_out": True, "wall_seconds": round(time.time() - t0, 2)}
    wall = round(time.time() - t0, 2)
    if proc.returncode == 124:
        return {"ok": None, "timed_out": True, "wall_seconds": wall, "stderr_tail": proc.stderr[-800:]}

    marker = "===ICAIF_PROBE_RESULT==="
    json_text = proc.stdout.rsplit(marker, 1)[-1].strip() if marker in proc.stdout else (
        proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    )
    try:
        parsed = json.loads(json_text)
        parsed["wall_seconds"] = wall
        parsed["timed_out"] = False
        return parsed
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "timed_out": False, "wall_seconds": wall,
                "error_type": "ProcessCrashed",
                "error_message": (proc.stderr[-500:] or "no parseable output")}


Q_FIELD = {"Q1": "q1", "Q2": "q2", "Q3": "q3", "Q4": "q4", "Q5": "q5"}


def _relative_or_absolute(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def execute_job(job: Job, launch_deadline: Optional[float] = None) -> dict:
    base_row = {
        "batch_id": job.batch_id, "adapter": job.adapter, "q_type": job.q_type,
        "input_granularity": job.input_granularity, "ticker_or_universe_id": job.input_id,
        "decision_date": job.decision_date, "success": False, "schema_valid": False,
        "runtime_seconds": None, "timeout": False, "error_message": "",
        "raw_output_path": "", "normalized_output_path": "",
        "requires_api_key": job.requires_api_key, "requires_broker_credentials": job.requires_broker_credentials,
        "supports_historical_date": job.supports_historical_date, "notes": job.notes,
    }

    # Checked HERE (right before the subprocess actually starts), not at
    # ThreadPoolExecutor.submit() time — submit() is non-blocking and would
    # have queued every job instantly regardless of any deadline check made
    # there, defeating "stop launching new jobs after N hours" entirely.
    if launch_deadline is not None and time.time() > launch_deadline:
        row = dict(base_row)
        row["error_message"] = "not started: launch cutoff reached (resumable — rerun to pick this up)"
        return row

    lock = _lock_for(job.adapter)
    with lock:
        if launch_deadline is not None and time.time() > launch_deadline:
            row = dict(base_row)
            row["error_message"] = "not started: launch cutoff reached while waiting on adapter lock (resumable)"
            return row
        raw = run_probe_full(job)

    row = dict(base_row)
    row["runtime_seconds"] = raw.get("runtime_seconds") or raw.get("wall_seconds")
    row["timeout"] = bool(raw.get("timed_out"))

    if raw.get("timed_out"):
        row["error_message"] = f"timed out after {job.timeout_s}s"
        return row

    if not raw.get("ok"):
        row["error_message"] = f"{raw.get('error_type', 'Unknown')}: {raw.get('error_message', '')}".strip(": ")
        return row

    payload = raw.get("full_payload")
    if payload is None:
        row["error_message"] = "ok=True but no full_payload returned (probe script mismatch)"
        return row

    job.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = job.out_dir / f"{job.input_id}.raw.json"
    norm_path = job.out_dir / f"{job.input_id}.json"

    try:
        raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        sys.path.insert(0, str(ROOT))
        from CONTRACT.schemas import AdapterResult
        envelope_kwargs = {Q_FIELD[job.q_type]: payload}
        ar = AdapterResult(
            adapter=job.adapter, task_id=f"{job.batch_id}__{job.decision_date}",
            native_output={}, adapter_notes=f"observation_batch input_id={job.input_id}",
            **envelope_kwargs,
        )
        norm_path.write_text(ar.model_dump_json(indent=2), encoding="utf-8")
        # success/schema_valid reflect the write+validate having happened;
        # path formatting below is cosmetic and must never flip these back
        # to False (that would make a genuinely-successful job look failed
        # and defeat resumability on the next run).
        row["success"] = True
        row["schema_valid"] = True
        row["raw_output_path"] = _relative_or_absolute(raw_path)
        row["normalized_output_path"] = _relative_or_absolute(norm_path)
    except Exception as e:  # noqa: BLE001 — must record, never crash the batch over one bad payload
        row["error_message"] = f"schema/write error: {type(e).__name__}: {str(e)[:300]}"
        row["schema_valid"] = False

    return row


# --------------------------------------------------------------------------- #
# Index management (resumability)
# --------------------------------------------------------------------------- #

_index_lock = threading.Lock()


def load_completed_keys(index_path: Path) -> set:
    completed = set()
    if not index_path.exists():
        return completed
    with open(index_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("success") == "True" and r.get("schema_valid") == "True":
                key = (r["adapter"], r["q_type"], r["ticker_or_universe_id"], r["decision_date"])
                if r.get("normalized_output_path") and (ROOT / r["normalized_output_path"]).exists():
                    completed.add(key)
    return completed


def append_index_row(index_path: Path, row: dict) -> None:
    with _index_lock:
        write_header = not index_path.exists()
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=INDEX_FIELDS)
            if write_header:
                w.writeheader()
            w.writerow(row)
            f.flush()
            os.fsync(f.fileno())


# --------------------------------------------------------------------------- #
# Batch runner (shared by main batch + historical extension)
# --------------------------------------------------------------------------- #

def run_batch(jobs: List[Job], index_path: Path, completed_keys: set, force: bool,
              launch_deadline: float, log_prefix: str) -> List[dict]:
    pending = [
        j for j in jobs
        if force or (j.adapter, j.q_type, j.input_id, j.decision_date) not in completed_keys
    ]
    skipped = len(jobs) - len(pending)
    print(f"[{log_prefix}] {len(jobs)} total jobs, {skipped} already complete (skipped), {len(pending)} to run.")

    llm_jobs = [j for j in pending if j.is_llm]
    nonllm_jobs = [j for j in pending if not j.is_llm]
    results: List[dict] = []

    def submit_and_drain(executor, job_list, label):
        # All jobs are handed to the executor immediately — submit() just
        # enqueues (non-blocking), it does not "start" a job. The actual
        # launch-cutoff enforcement happens inside execute_job(), right
        # before it invokes the subprocess, so a job still sitting in the
        # pool's internal queue past the deadline gets skipped rather than
        # actually started.
        futures = {executor.submit(execute_job, j, launch_deadline): j for j in job_list}
        cutoff_hit = False
        for fut in as_completed(futures):
            j = futures[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                row = {**{k: "" for k in INDEX_FIELDS}, "batch_id": j.batch_id, "adapter": j.adapter,
                       "q_type": j.q_type, "input_granularity": j.input_granularity,
                       "ticker_or_universe_id": j.input_id, "decision_date": j.decision_date,
                       "success": False, "schema_valid": False, "timeout": False,
                       "error_message": f"executor exception: {type(e).__name__}: {e}"}
            append_index_row(index_path, row)
            results.append(row)
            if "not started: launch cutoff" in row.get("error_message", ""):
                cutoff_hit = True
            status = "OK" if row["success"] else ("TIMEOUT" if row["timeout"] else "FAIL")
            print(f"  [{label}] {j.adapter}/{j.q_type}/{j.input_id} -> {status} ({row.get('runtime_seconds')}s)")
        if cutoff_hit:
            n_not_started = sum(1 for fut in futures if "not started: launch cutoff" in (fut.result().get("error_message") or ""))
            print(f"[{log_prefix}] launch cutoff reached mid-{label}; "
                  f"{n_not_started} {label} job(s) not started this run (resumable — rerun to pick them up).")
        return cutoff_hit

    with ThreadPoolExecutor(max_workers=2) as llm_ex, ThreadPoolExecutor(max_workers=4) as nonllm_ex:
        t_llm = threading.Thread(target=lambda: submit_and_drain(llm_ex, llm_jobs, "llm"))
        t_nonllm = threading.Thread(target=lambda: submit_and_drain(nonllm_ex, nonllm_jobs, "nonllm"))
        t_llm.start(); t_nonllm.start()
        t_llm.join(); t_nonllm.join()

    return results


# --------------------------------------------------------------------------- #
# Historical extension eligibility
# --------------------------------------------------------------------------- #

def historical_eligible_rows(rows: List[dict]) -> List[dict]:
    """No LLM/API key AND static heuristic says historical support is likely
    true. Deliberately excludes TradingAgents and every other LLM-debate
    adapter per the brief, even if their heuristic looked promising."""
    return [
        r for r in rows
        if r["requires_api_key"] == "False"
        and r["supports_historical_date"].startswith("likely true")
    ]


# --------------------------------------------------------------------------- #
# Phase 3: rerun icaif_experiments + write summary
# --------------------------------------------------------------------------- #

def backup_reports_dir(reports_dir: Path) -> Optional[Path]:
    if not reports_dir.exists() or not any(reports_dir.iterdir()):
        return None
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = reports_dir.parent / f"{reports_dir.name}_backup_{stamp}"
    shutil.copytree(reports_dir, backup)
    return backup


def rerun_icaif_experiments(reports_dir: Path) -> None:
    cmd = [
        sys.executable, "-m", "analysis.icaif_experiments",
        "--results-dir", "results", "--adapters-dir", "adapters",
        "--out", str(reports_dir), "--horizons", "1,5,20", "--threshold-bps", "20",
    ]
    print(f"Rerunning: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print("WARNING: icaif_experiments rerun exited non-zero:", proc.stderr[-2000:], file=sys.stderr)


def write_summary(
    reports_dir: Path, index_path: Path, before_matrix, decision_date: str,
    started_at: float, main_jobs_planned: int, hist_jobs_planned: int, ran_historical: bool,
) -> None:
    rows = []
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    total = len(rows)
    succeeded = sum(1 for r in rows if r["success"] == "True")
    failed = sum(1 for r in rows if r["success"] != "True" and r["timeout"] != "True")
    timed_out = sum(1 for r in rows if r["timeout"] == "True")

    per_adapter: Dict[str, Dict[str, int]] = {}
    for r in rows:
        d = per_adapter.setdefault(r["adapter"], {"attempted": 0, "succeeded": 0, "failed": 0, "timed_out": 0})
        d["attempted"] += 1
        if r["success"] == "True":
            d["succeeded"] += 1
        elif r["timeout"] == "True":
            d["timed_out"] += 1
        else:
            d["failed"] += 1

    def runtime_of(r):
        try:
            return float(r["runtime_seconds"])
        except (TypeError, ValueError):
            return -1.0
    slowest = sorted(rows, key=runtime_of, reverse=True)[:10]

    api_failures = [r for r in rows if r["success"] != "True" and r["requires_api_key"] == "True"]

    n_normalized = sum(1 for r in rows if r["normalized_output_path"])
    n_schema_invalid = sum(1 for r in rows if r["success"] == "True" and r["schema_valid"] != "True")

    after_records = discover_result_files(ROOT / "results")
    from analysis.icaif_data_loader import records_to_dataframe
    after_df = records_to_dataframe(after_records)

    def q_coverage(df, q):
        col = f"{q.lower()}_present"
        if df.empty or col not in df.columns:
            return 0
        return int(df[df[col] == True]["adapter"].nunique())  # noqa: E712

    before_cov = {q: (len(before_matrix[before_matrix[q].str.contains("observed", na=False)])
                      if q in before_matrix.columns else 0) for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]}
    after_cov = {q: q_coverage(after_df, q) for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]}

    def read_csv_safe(name):
        import pandas as pd
        p = reports_dir / name
        return pd.read_csv(p) if p.exists() else None

    calib = read_csv_safe("calibration_table.csv")
    calib_by_horizon = {}
    if calib is not None and not calib.empty:
        for h, g in calib.groupby("horizon"):
            calib_by_horizon[int(h)] = int(g["sample_count"].sum())

    contra_summary = read_csv_safe("contradiction_summary.csv")
    n_contradictions = int(contra_summary["count"].sum()) if contra_summary is not None and not contra_summary.empty else 0

    fusion_results = read_csv_safe("fusion_ablation_results.csv")
    fusion_has_returns = (
        fusion_results is not None and not fusion_results.empty
        and "insufficient_data" in fusion_results.columns
        and not fusion_results["insufficient_data"].fillna(False).all()
    )

    calib_readme = reports_dir / "calibration_README.md"
    calib_note = calib_readme.read_text(encoding="utf-8") if calib_readme.exists() else "(not generated)"

    elapsed_h = (time.time() - started_at) / 3600

    lines = [
        "# Observation Batch Day 1 — Summary", "",
        f"Decision date (latest available current snapshot): **{decision_date}**  ",
        f"Data cutoff: prices/news as fetched at run time on {datetime.now().isoformat(timespec='seconds')}  ",
        f"Total wall-clock: **{elapsed_h:.2f} hours**  ",
        f"Historical extension attempted: **{ran_historical}**", "",
        "## Job totals",
        f"- Total attempted (this run + prior resumed rows): **{total}**",
        f"- Succeeded: **{succeeded}**",
        f"- Failed (non-timeout): **{failed}**",
        f"- Timed out: **{timed_out}**",
        f"- Schema-invalid successes: **{n_schema_invalid}**",
        f"- Normalized JSONs on disk (index rows with a path): **{n_normalized}**", "",
        "## Per-adapter results", "",
        "| adapter | attempted | succeeded | failed | timed_out |",
        "|---|---|---|---|---|",
    ]
    for adapter, d in sorted(per_adapter.items()):
        lines.append(f"| {adapter} | {d['attempted']} | {d['succeeded']} | {d['failed']} | {d['timed_out']} |")

    lines += ["", "## Per-Q observed coverage (adapters with >=1 observed result): before vs after", "",
              "| Q | before | after |", "|---|---|---|"]
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        lines.append(f"| {q} | {before_cov.get(q, 0)} | {after_cov.get(q, 0)} |")

    lines += ["", "## Slowest 10 jobs", "",
              "| adapter | q_type | ticker/universe | runtime_s | success |", "|---|---|---|---|---|"]
    for r in slowest:
        lines.append(f"| {r['adapter']} | {r['q_type']} | {r['ticker_or_universe_id']} | "
                      f"{r['runtime_seconds']} | {r['success']} |")

    lines += ["", "## API/LLM failures", ""]
    if api_failures:
        for r in api_failures:
            lines.append(f"- {r['adapter']}/{r['q_type']}/{r['ticker_or_universe_id']}: {r['error_message']}")
    else:
        lines.append("- none")

    lines += [
        "", "## Downstream ICAIF experiment status", "",
        f"- ICAIF experiments now have more observed results: **{sum(after_cov.values()) > sum(before_cov.values())}** "
        f"(sum of per-Q adapter-coverage counts: before={sum(before_cov.values())}, after={sum(after_cov.values())})",
        f"- Contradiction rules fired: **{n_contradictions > 0}** ({n_contradictions} case(s) — see contradiction_summary.csv)",
        "- Calibration sample counts by horizon (trading days): "
        + (", ".join(f"{h}d={n}" for h, n in sorted(calib_by_horizon.items())) if calib_by_horizon else "none computed"),
        f"- Fusion ablation can compute return-based metrics: **{fusion_has_returns}**",
        "", "### calibration_README.md (verbatim)", "```", calib_note, "```", "",
        "## Remaining insufficient_data sections",
        "- Any horizon not listed above under calibration sample counts is still insufficient_data — "
        "see calibration_README.md for exactly which trading days have and haven't elapsed.",
        "- Q4/Q5 contradiction rules (2, 3, 5) remain best-effort task_id/date joins per "
        "CONTRACT/schemas.py's lack of a ticker/date field on Q4Portfolio/Q5Backtest — unchanged by this batch.",
        "", "## Known data-quality caveats from this batch",
        "- `atlas` Q3: bundled dataset is crypto-perpetuals only; every equity/ETF ticker requested falls back "
        "to the same BTCUSDT-derived signal (self-disclosed in its own supporting_evidence). Treat atlas's "
        "10 \"different\" ticker observations as 1 real observation repeated under 10 labels.",
        "- No profitability claim is made anywhere in this batch or its outputs — total_return/sharpe/hit_rate "
        "figures are descriptive of this specific sample, not a claim that any strategy is profitable.",
        "", "## Recommended next batch",
        "- Prioritize widening Q1/Q2 coverage (currently the thinnest — 3-4 adapters vs. 8 for Q3).",
        "- If 5d/20d calibration is still insufficient_data here, the single highest-value next action is simply "
        "waiting real calendar time and rerunning `analysis.icaif_experiments` against the same results/ — no new "
        "adapter runs needed for that specific gap.",
        "- Consider a second historical extension batch (different date range) once more calendar time has passed, "
        "to grow the calibration sample size for Q3 in particular (currently the highest-coverage question).",
        "",
    ]
    (reports_dir / "OBSERVATION_BATCH_DAY1_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {reports_dir / 'OBSERVATION_BATCH_DAY1_SUMMARY.md'}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch-id", default="observation_batch_day1")
    p.add_argument("--adapters-dir", default=str(ROOT / "adapters"))
    p.add_argument("--runnability-csv", default=str(ROOT / "reports" / "icaif_experiments" / "adapter_runnability.csv"))
    p.add_argument("--reports-dir", default=str(ROOT / "reports" / "icaif_experiments"))
    p.add_argument("--out-root", default=str(ROOT / "results" / "observations"))
    p.add_argument("--decision-date", default=None)
    p.add_argument("--budget-hours", type=float, default=8.0)
    p.add_argument("--launch-cutoff-hours", type=float, default=7.0)
    p.add_argument("--historical-cutoff-hours", type=float, default=5.0)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    started_at = time.time()
    launch_deadline = started_at + args.launch_cutoff_hours * 3600
    hard_deadline = started_at + args.budget_hours * 3600

    decision_date = args.decision_date or date_cls.today().isoformat()
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== {args.batch_id} starting at {datetime.now().isoformat(timespec='seconds')} ===")
    print(f"decision_date={decision_date}, budget={args.budget_hours}h, launch_cutoff={args.launch_cutoff_hours}h")

    import pandas as pd
    before_matrix_path = reports_dir / "coverage_matrix.csv"
    before_matrix = pd.read_csv(before_matrix_path, index_col=0) if before_matrix_path.exists() else pd.DataFrame()

    rows = load_runnable_rows(Path(args.runnability_csv))
    envs = env_lookup(Path(args.adapters_dir))
    print(f"Loaded {len(rows)} runnable (adapter, q_type) rows from audit.")

    main_out = Path(args.out_root) / args.batch_id
    main_index = main_out / "index.csv"
    main_jobs = build_jobs_for_rows(rows, envs, decision_date, args.batch_id, main_out,
                                     TICKER_UNIVERSE, PORTFOLIO_UNIVERSE)
    completed = load_completed_keys(main_index)
    run_batch(main_jobs, main_index, completed, args.force, launch_deadline, "main")

    elapsed_after_main = (time.time() - started_at) / 3600
    print(f"Main batch done. Elapsed: {elapsed_after_main:.2f}h")

    ran_historical = False
    hist_jobs_planned = 0
    if elapsed_after_main < args.historical_cutoff_hours and time.time() < launch_deadline:
        hist_rows = historical_eligible_rows(rows)
        if hist_rows:
            print(f"Historical extension eligible adapters: {sorted({r['adapter'] for r in hist_rows})}")
            hist_dates = pick_historical_dates(date_cls.fromisoformat(decision_date), N_HIST_DATES, HIST_MIN_TRADING_DAYS_BACK)
            print(f"Historical decision dates: {hist_dates}")
            hist_batch_id = f"{args.batch_id}_historical_extension"
            hist_out = Path(args.out_root) / hist_batch_id
            hist_index = hist_out / "index.csv"
            hist_completed = load_completed_keys(hist_index)
            all_hist_jobs = []
            for hdate in hist_dates:
                all_hist_jobs.extend(build_jobs_for_rows(
                    hist_rows, envs, hdate, hist_batch_id, hist_out,
                    HIST_TICKER_UNIVERSE, HIST_TICKER_UNIVERSE,
                ))
            hist_jobs_planned = len(all_hist_jobs)
            run_batch(all_hist_jobs, hist_index, hist_completed, args.force, launch_deadline, "historical")
            ran_historical = True
        else:
            print("No adapters qualify for the historical extension (need requires_api_key=False AND "
                  "supports_historical_date startswith 'likely true'). Skipping.")
    else:
        print(f"Skipping historical extension: elapsed={elapsed_after_main:.2f}h >= "
              f"cutoff={args.historical_cutoff_hours}h, or launch deadline passed.")

    backup = backup_reports_dir(reports_dir)
    print(f"Backed up existing reports to: {backup}" if backup else "No prior reports to back up.")

    rerun_icaif_experiments(reports_dir)

    write_summary(reports_dir, main_index, before_matrix, decision_date, started_at,
                  len(main_jobs), hist_jobs_planned, ran_historical)

    total_elapsed_h = (time.time() - started_at) / 3600
    print(f"=== {args.batch_id} complete. Total elapsed: {total_elapsed_h:.2f}h ===")


if __name__ == "__main__":
    main()
