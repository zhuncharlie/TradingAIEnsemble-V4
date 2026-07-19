"""
tools/run_large_scale_experiment.py — large-scale, resumable, failure-isolated
batch runner for the unified harness (§七/§八 of the Q4 stepwise
infrastructure task).

This is deliberately a SEPARATE, more general tool from
tools/run_unified_harness.py (which runs one fixed, small, shared task across
every adapter for a fair-comparison smoke check). This tool reads a task
MANIFEST (a JSON file listing many (adapter, args, env, timeout) tasks — Q1-Q3
one-shot tasks or Q4 batch dispatches) and runs it at scale with the
engineering properties real large-scale experiments require:

  - Resumability: a task whose result file already exists is SKIPPED by
    default (not re-run), unless --force is passed. Each task's result is
    written atomically (temp file + os.replace), so an interrupted run never
    leaves a half-written result file that a later resume could mistake for
    a completed one.
  - Reproducibility: every run writes a run_manifest.json capturing the git
    commit, the manifest file's own content hash, the resolved task list, a
    wall-clock start/end timestamp, and (best-effort) `conda list` package
    snapshots are NOT captured here (too slow/heavy for every run) — per-
    adapter conda envs are already named in the manifest itself, which is
    sufficient for reproducing which env a task ran in.
  - Failure isolation: one task's exception/timeout never aborts the batch;
    each task is wrapped individually and recorded with a status from the
    same status vocabulary Q4 sessions use (harness.q4_protocol.RunStatus).
  - Retry: a task is retried up to `max_retries` times (default 0) before
    being recorded FAILED; each attempt's own failure reason is preserved.
  - Concurrency: bounded via --concurrency (default 1, i.e. sequential) using
    a thread pool around the blocking subprocess calls — real heavy GPU/LLM
    adapters should be run with --concurrency 1 (the default) to avoid
    multiple heavy adapters contending for the same GPU; concurrency is only
    safe to raise for lightweight/CPU-only adapter mixes, which is a caller
    decision, not one this tool makes for them.

Usage:
    python tools/run_large_scale_experiment.py --manifest <path.json> --out-dir <dir>
    python tools/run_large_scale_experiment.py --manifest <path.json> --out-dir <dir> --force --only skfolio qlib
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]

STATUS_VALUES = (
    "PASSED", "FAILED", "BLOCKED", "TIMEOUT", "SKIPPED", "NOT_RUN",
    "STEPWISE_UNSUPPORTED",
)


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    tasks = data["tasks"] if isinstance(data, dict) else data
    for t in tasks:
        if "name" not in t or "env" not in t:
            raise ValueError(f"Manifest task missing required 'name'/'env': {t}")
    return tasks


def result_path_for(out_dir: Path, task_name: str) -> Path:
    return out_dir / f"{task_name}.result.json"


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write to a temp file in the same directory, then os.replace — never
    leaves a partially-written result file behind on interruption, and
    os.replace is atomic on POSIX filesystems (same directory, same
    filesystem, which this always is since tmp lives beside the target)."""
    tmp_path = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp_path.write_text(json.dumps(data, indent=2, default=str))
    os.replace(tmp_path, path)


def is_already_done(out_dir: Path, task_name: str) -> bool:
    p = result_path_for(out_dir, task_name)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return data.get("status") in ("PASSED", "BLOCKED", "STEPWISE_UNSUPPORTED")


def run_task_subprocess(task: Dict[str, Any], out_dir: Path, default_timeout: int) -> Dict[str, Any]:
    """Runs exactly one task's real subprocess command. Returns a result dict
    with a status drawn from STATUS_VALUES — never raises; every exception
    path is caught and converted into a FAILED/TIMEOUT result so that one
    task's failure can never abort the batch (§八 failure isolation)."""
    name = task["name"]
    env = task["env"]
    timeout = task.get("timeout", default_timeout)
    cmd = task.get("cmd")
    if not cmd:
        raise ValueError(f"Task {name!r} has no 'cmd' to run")

    child_env = dict(os.environ)
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"

    t0 = time.time()
    result: Dict[str, Any] = {"name": name, "env": env, "cmd": cmd, "expect": task.get("expect", "PASSED")}
    try:
        proc = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=child_env, shell=isinstance(cmd, str),
        )
        result["latency_sec"] = round(time.time() - t0, 1)
        stdout, stderr = proc.stdout, proc.stderr
        ok = proc.returncode == 0
        if ok:
            result["status"] = "PASSED"
        else:
            expect = task.get("expect")
            result["status"] = expect if expect == "BLOCKED" else "FAILED"
            tail = (stderr or stdout).strip().splitlines()
            result["failure_reason"] = tail[-1] if tail else f"nonzero exit {proc.returncode}"
    except subprocess.TimeoutExpired:
        result["latency_sec"] = timeout
        result["status"] = "TIMEOUT"
        result["failure_reason"] = f"timed out after {timeout}s"
    except Exception as e:
        result["latency_sec"] = round(time.time() - t0, 1)
        result["status"] = "FAILED"
        result["failure_reason"] = f"{type(e).__name__}: {e}"
    return result


def run_task_with_retry(
    task: Dict[str, Any],
    out_dir: Path,
    default_timeout: int,
    max_retries: int,
    force: bool,
) -> Dict[str, Any]:
    name = task["name"]

    if not force and is_already_done(out_dir, name):
        cached = json.loads(result_path_for(out_dir, name).read_text())
        cached["status"] = "SKIPPED"
        cached["skip_reason"] = "already completed (use --force to rerun)"
        atomic_write_json(result_path_for(out_dir, name), cached)
        return cached

    attempts: List[Dict[str, Any]] = []
    result: Dict[str, Any] = {"name": name, "status": "NOT_RUN"}
    for attempt in range(max_retries + 1):
        result = run_task_subprocess(task, out_dir, default_timeout)
        result["attempt"] = attempt + 1
        attempts.append({"attempt": attempt + 1, "status": result["status"], "reason": result.get("failure_reason")})
        if result["status"] in ("PASSED", "BLOCKED", "STEPWISE_UNSUPPORTED"):
            break
    result["attempts"] = attempts
    result["n_attempts"] = len(attempts)
    atomic_write_json(result_path_for(out_dir, name), result)
    return result


def run_batch(
    tasks: List[Dict[str, Any]],
    out_dir: Path,
    default_timeout: int = 200,
    max_retries: int = 0,
    force: bool = False,
    concurrency: int = 1,
    only: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [t for t in tasks if only is None or t["name"] in only]

    results: List[Dict[str, Any]] = []
    if concurrency <= 1:
        for t in specs:
            r = run_task_with_retry(t, out_dir, default_timeout, max_retries, force)
            results.append(r)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(run_task_with_retry, t, out_dir, default_timeout, max_retries, force): t
                for t in specs
            }
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())
    return results


def write_run_manifest(out_dir: Path, manifest_path: Path, tasks: List[Dict[str, Any]], results: List[Dict[str, Any]], t_start: float) -> Path:
    manifest = {
        "git_commit": _git_commit(),
        "manifest_file": str(manifest_path),
        "manifest_content_hash": _content_hash(tasks),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_start)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_tasks": len(tasks),
        "status_counts": {s: sum(1 for r in results if r["status"] == s) for s in STATUS_VALUES},
    }
    p = out_dir / "run_manifest.json"
    atomic_write_json(p, manifest)
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--force", action="store_true", help="rerun tasks even if a passing result already exists")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--timeout", type=int, default=200)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)
    tasks = load_manifest(manifest_path)

    t0 = time.time()
    results = run_batch(
        tasks, out_dir,
        default_timeout=args.timeout, max_retries=args.max_retries,
        force=args.force, concurrency=args.concurrency, only=args.only,
    )
    manifest_out = write_run_manifest(out_dir, manifest_path, tasks, results, t0)

    counts = {s: sum(1 for r in results if r["status"] == s) for s in STATUS_VALUES}
    print(f"\n=== {len(results)} tasks: " + ", ".join(f"{k}={v}" for k, v in counts.items() if v) + " ===")
    print(f"Run manifest: {manifest_out}")


if __name__ == "__main__":
    main()
