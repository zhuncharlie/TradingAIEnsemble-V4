"""
CONTRACT/adapter_runner.py — dynamically loads one adapter, runs its
Q1-Q4 methods, validates the result against schema v2, and writes it to
results/{task_id}/{adapter_name}.json.

This is the execution counterpart to CONTRACT/test_harness.py, which is a
pure schema-contract test suite and does not load or run real adapters.
This file is the new, independent runner: it is the only place in CONTRACT/
that imports and instantiates a live adapter.

Usage:
    python CONTRACT/adapter_runner.py --adapter adapters/your_adapter.py \\
        --task-id my_task --as-of 2026-01-31 --scope ASSET --target NVDA \\
        --universe NVDA

    # Q4 policies additionally need a harness-supplied generation window:
    python CONTRACT/adapter_runner.py --adapter adapters/your_adapter.py \\
        --task-id my_task --as-of 2026-01-31 --scope PORTFOLIO \\
        --universe-id GLOBAL_LIQUID_ASSETS_V1 \\
        --gen-start 2020-01-01 --gen-end 2023-12-31

Only responsible for one adapter, one run. Multi-adapter, multi-conda-env
orchestration across the whole adapter roster lives in
analysis/collect_results.py and is out of scope here.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.base_adapter import VALID_QUESTIONS, AdapterContractViolation, BaseAdapter
from CONTRACT.schemas import AdapterResult, OutputScope, QueryContext, TimeWindow

from pydantic import ValidationError

PASS  = "\033[92m✓\033[0m"
FAIL  = "\033[91m✗\033[0m"
WARN  = "\033[93m!\033[0m"
BOLD  = "\033[1m"
RESET = "\033[0m"


class RunnerError(Exception):
    """Any failure that should abort the run with a clear message, no traceback."""


def load_adapter(path: str) -> BaseAdapter:
    p = Path(path).resolve()
    if not p.exists():
        raise RunnerError(f"Adapter file not found: {p}")

    spec = importlib.util.spec_from_file_location("_adapter_module", p)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise RunnerError(f"Could not import {p}: {type(e).__name__}: {e}") from e

    candidates = [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseAdapter) and cls is not BaseAdapter
    ]
    if not candidates:
        raise RunnerError(f"No BaseAdapter subclass found in {p}")
    if len(candidates) > 1:
        print(f"{WARN} Multiple BaseAdapter subclasses found; using {candidates[0].__name__}")

    try:
        return candidates[0]()
    except Exception as e:
        raise RunnerError(f"Could not instantiate {candidates[0].__name__}: {type(e).__name__}: {e}") from e


def check_metadata(adapter: BaseAdapter) -> None:
    print(f"\n{BOLD}[1] Metadata{RESET}")
    checks = {
        "name is set": bool(adapter.name),
        "questions_answered is set": bool(adapter.questions_answered),
        "questions_answered only contains Q1-Q4": all(
            q in VALID_QUESTIONS for q in adapter.questions_answered
        ),
        "upstream_repo is set": bool(adapter.upstream_repo),
    }
    failed = [label for label, ok in checks.items() if not ok]
    for label, ok in checks.items():
        print(f"  {PASS if ok else FAIL} {label}")
    if failed:
        raise RunnerError(f"Adapter metadata invalid: {', '.join(failed)}")


def build_context(args: argparse.Namespace) -> QueryContext:
    try:
        return QueryContext(
            as_of=args.as_of,
            data_cutoff=args.data_cutoff or args.as_of,
            scope=OutputScope(args.scope),
            targets=args.target or None,
            universe=args.universe or None,
            universe_id=args.universe_id,
            horizon=args.horizon,
        )
    except ValidationError as e:
        raise RunnerError(f"Invalid --as-of/--data-cutoff/--scope/--target/--universe combination:\n{e}") from e


def build_generation_window(args: argparse.Namespace) -> Optional[TimeWindow]:
    if not args.gen_start and not args.gen_end:
        return None
    if not (args.gen_start and args.gen_end):
        raise RunnerError("--gen-start and --gen-end must both be supplied, or both omitted")
    try:
        return TimeWindow(start=args.gen_start, end=args.gen_end)
    except ValidationError as e:
        raise RunnerError(f"Invalid generation window:\n{e}") from e


def parse_kwargs(pairs) -> dict:
    kwargs = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise RunnerError(f"--kwarg values must be key=value, got: {pair!r}")
        key, _, value = pair.partition("=")
        kwargs[key] = value
    return kwargs


def run_adapter(
    adapter: BaseAdapter,
    task_id: str,
    context: QueryContext,
    generation_window: Optional[TimeWindow],
    extra_kwargs: dict,
) -> AdapterResult:
    print(f"\n{BOLD}[2] Running adapter.run(){RESET}")
    try:
        result = adapter.run(
            task_id=task_id,
            context=context,
            generation_window=generation_window,
            **extra_kwargs,
        )
    except ValidationError as e:
        raise RunnerError(f"adapter.run() produced a v2-schema-invalid result:\n{e}") from e
    except AdapterContractViolation as e:
        raise RunnerError(f"adapter.run() violated a harness invariant: {e}") from e
    except Exception as e:
        raise RunnerError(f"adapter.run() raised {type(e).__name__}: {e}") from e
    print(f"  {PASS} adapter.run() returned an AdapterResult")
    return result


def validate_against_schema(result: AdapterResult) -> None:
    print(f"\n{BOLD}[3] Re-validating against schema v2{RESET}")
    try:
        payload = result.model_dump(mode="json")
        restored = AdapterResult.model_validate(payload)
    except ValidationError as e:
        raise RunnerError(f"Result failed schema v2 re-validation:\n{e}") from e
    if restored != result:
        raise RunnerError("Result changed after a JSON round-trip through schema v2 — non-deterministic serialization")
    print(f"  {PASS} AdapterResult validates cleanly against schema v2 ({result.run.schema_version})")


def write_result(result: AdapterResult, out_dir: Path, task_id: str, adapter_name: str) -> Path:
    print(f"\n{BOLD}[4] Writing result JSON{RESET}")
    out_path = out_dir / task_id / f"{adapter_name}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_path.write_text(result.model_dump_json(indent=2))
    except OSError as e:
        raise RunnerError(f"Could not write {out_path}: {e}") from e
    print(f"  {PASS} wrote {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="v2 adapter runner: load, run, validate, write one AdapterResult")
    parser.add_argument("--adapter", required=True, help="Path to adapter .py file")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--as-of", required=True, help="QueryContext.as_of")
    parser.add_argument("--data-cutoff", default=None, help="QueryContext.data_cutoff (defaults to --as-of)")
    parser.add_argument("--scope", default="ASSET", choices=[s.value for s in OutputScope])
    parser.add_argument("--target", nargs="*", default=None, help="QueryContext.targets")
    parser.add_argument("--universe", nargs="*", default=None, help="QueryContext.universe")
    parser.add_argument("--universe-id", default=None)
    parser.add_argument("--horizon", default=None)
    parser.add_argument("--gen-start", default=None, help="Q4 generation_window.start")
    parser.add_argument("--gen-end", default=None, help="Q4 generation_window.end")
    parser.add_argument("--kwarg", nargs="*", default=None, help="Extra key=value pairs forwarded to the adapter's q*() methods")
    parser.add_argument("--out-dir", default=str(ROOT / "results"))
    args = parser.parse_args()

    try:
        adapter = load_adapter(args.adapter)
        check_metadata(adapter)
        context = build_context(args)
        generation_window = build_generation_window(args)
        extra_kwargs = parse_kwargs(args.kwarg)

        result = run_adapter(adapter, args.task_id, context, generation_window, extra_kwargs)
        validate_against_schema(result)
        out_path = write_result(result, Path(args.out_dir), args.task_id, adapter.name)

        print(f"\n{BOLD}Summary: {PASS} {adapter.name} -> {out_path}{RESET}\n")
        return 0

    except RunnerError as e:
        print(f"\n{FAIL} {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
