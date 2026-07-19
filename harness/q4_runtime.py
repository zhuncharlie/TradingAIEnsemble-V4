"""
harness/q4_runtime.py — conda-env session orchestration for Q4 stepwise
execution.

Design decision (see Q4_STEPWISE_MIGRATION.md for the full rationale): one
persistent per-adapter session subprocess per Q4ExecutionEngine run, not
one subprocess per step. Several real Q4 adapters (adapters/qlib_adapter.py,
adapters/trademaster_adapter.py, adapters/deepdow_adapter.py,
adapters/finrl_adapter.py, adapters/finrl_x_adapter.py,
adapters/earnmore_adapter.py) pay a real, fixed model-training/data-loading
cost inside q4_initialize() (real torch/qlib fits) that would be paid once
PER STEP under a subprocess-per-step design — infeasible for anything beyond
a handful of steps. A persistent worker process keeps the real adapter-side
state object (a trained model, a live upstream Account/env, an algorithm's
running internal matrices) alive in memory for the session's lifetime,
communicating over a line-delimited-JSON stdin/stdout protocol.

Two halves:
  - Harness-side (imported by tools/*): spawn_session, RemoteQ4StepAdapterProxy,
    Q4SessionHandle, close_session. Runs in the ORCHESTRATOR's own process.
  - Worker-side (`python -m harness.q4_runtime --worker --adapter <path>`):
    runs INSIDE the adapter's own conda env, loads exactly one real adapter
    via CONTRACT.adapter_runner.load_adapter() (reused directly, not
    reimplemented), and dispatches stdin request lines to either the real
    Q4StepAdapter methods (STEPWISE) or a LEGACY_INTERNAL_LOOP replay of the
    adapter's existing single-shot q4_policy() (for the adapters not yet
    migrated to the stepwise protocol — this is the concrete mechanism that
    lets every Q4 adapter satisfy the same Q4ExecutionEngine interface
    without requiring every one of them to be rewritten in this pass).

Nothing here modifies CONTRACT/schemas.py or CONTRACT/base_adapter.py;
CONTRACT.adapter_runner.load_adapter is imported and reused as-is.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import PolicyDecisionStep, Q4Policy, QueryContext, TimeWindow

from harness.q4_protocol import (
    MarketObservation,
    PortfolioState,
    Q4AdapterClassification,
    Q4AdapterSession,
    Q4FinalizeSummary,
    Q4RunConfig,
    Q4StepAdapter,
)

# Same real fix tools/run_unified_harness.py::run_one already uses: `conda
# run`'s subprocess doesn't always inherit an interactive shell's UTF-8
# locale, which can make Path.write_text()-style default-encoding writes
# raise UnicodeEncodeError on real non-ASCII model output.
_UTF8_ENV_OVERRIDES = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


class Q4RuntimeError(RuntimeError):
    """Raised for session/subprocess/protocol failures — distinct from
    Q4CausalityViolation/Q4ConstraintViolation, which are about the
    *content* of a decision, not the transport."""


# ---------------------------------------------------------------------------
# Harness-side: spawn, drive, and tear down a real conda-env session
# ---------------------------------------------------------------------------

class Q4SessionHandle:
    def __init__(self, session_id: str, adapter_name: str, env: str, proc: subprocess.Popen):
        self.session_id = session_id
        self.adapter_name = adapter_name
        self.env = env
        self.proc = proc
        self.step_count = 0
        self.started_at = time.time()
        self.closed = False


def spawn_session(adapter_name: str, env: str, session_id: str) -> Q4SessionHandle:
    """Starts exactly one real `conda run -n <env> ...` subprocess hosting
    one real adapter instance, kept alive for the session's lifetime. Mirrors
    the exact conda run invocation tools/run_unified_harness.py::run_one
    already uses for the existing single-shot CLI, extended with
    `--worker --adapter` for the persistent stdin/stdout protocol."""
    adapter_path = f"adapters/{adapter_name}_adapter.py"
    cmd = [
        "conda", "run", "-n", env, "--no-capture-output",
        "python", "-m", "harness.q4_runtime", "--worker", "--adapter", adapter_path,
    ]
    child_env = dict(os.environ)
    child_env.update(_UTF8_ENV_OVERRIDES)
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, env=child_env,
    )
    return Q4SessionHandle(session_id=session_id, adapter_name=adapter_name, env=env, proc=proc)


def _send(handle: Q4SessionHandle, request: dict, timeout: float) -> dict:
    if handle.closed or handle.proc.poll() is not None:
        stderr_tail = ""
        if handle.proc.stderr:
            try:
                stderr_tail = handle.proc.stderr.read()[-2000:]
            except Exception:
                pass
        raise Q4RuntimeError(
            f"session {handle.session_id} ({handle.adapter_name}) is not running "
            f"(returncode={handle.proc.returncode}). stderr tail: {stderr_tail}"
        )
    line = json.dumps(request)
    handle.proc.stdin.write(line + "\n")
    handle.proc.stdin.flush()

    # subprocess.PIPE readline() has no per-call timeout in the stdlib; a real
    # bounded wait is implemented via the process's own alive-check plus a
    # coarse polling loop, good enough for this harness's real step counts
    # (tens, not millions, of steps per session).
    deadline = time.time() + timeout
    resp_line = None
    while time.time() < deadline:
        resp_line = handle.proc.stdout.readline()
        if resp_line:
            break
        if handle.proc.poll() is not None:
            break
    if not resp_line:
        raise Q4RuntimeError(f"session {handle.session_id} ({handle.adapter_name}) timed out after {timeout}s")
    try:
        return json.loads(resp_line)
    except json.JSONDecodeError as e:
        raise Q4RuntimeError(f"session {handle.session_id}: malformed worker response: {resp_line!r}") from e


def close_session(handle: Q4SessionHandle, timeout: float = 10.0) -> None:
    if handle.closed:
        return
    try:
        if handle.proc.poll() is None:
            handle.proc.stdin.write(json.dumps({"op": "shutdown"}) + "\n")
            handle.proc.stdin.flush()
            handle.proc.wait(timeout=timeout)
    except Exception:
        pass
    finally:
        if handle.proc.poll() is None:
            handle.proc.terminate()
            try:
                handle.proc.wait(timeout=5.0)
            except Exception:
                handle.proc.kill()
        handle.closed = True


class RemoteQ4StepAdapterProxy:
    """Implements the Q4StepAdapter structural interface by driving a real
    Q4SessionHandle's subprocess — Q4ExecutionEngine cannot tell this apart
    from an in-process fake adapter, which is exactly the point."""

    def __init__(self, handle: Q4SessionHandle, timeout_per_call: float = 120.0):
        self.handle = handle
        self.timeout_per_call = timeout_per_call
        self.classification: Optional[Q4AdapterClassification] = None

    def q4_initialize(self, context: QueryContext, generation_window: TimeWindow,
                       initial_portfolio: PortfolioState, run_config: Q4RunConfig) -> Q4Policy:
        resp = _send(self.handle, {
            "op": "initialize",
            "payload": {
                "context": context.model_dump(mode="json"),
                "generation_window": generation_window.model_dump(mode="json"),
                "initial_portfolio": initial_portfolio.model_dump(mode="json"),
                "run_config": run_config.model_dump(mode="json"),
            },
        }, self.timeout_per_call)
        if not resp.get("ok"):
            raise Q4RuntimeError(f"q4_initialize failed: {resp.get('error')}")
        self.classification = Q4AdapterClassification(resp["classification"])
        return Q4Policy.model_validate(resp["result"])

    def q4_step(self, timestamp: str, information_cutoff: str, observation: MarketObservation,
                portfolio_state: PortfolioState) -> PolicyDecisionStep:
        resp = _send(self.handle, {
            "op": "step",
            "payload": {
                "timestamp": timestamp, "information_cutoff": information_cutoff,
                "observation": observation.model_dump(mode="json"),
                "portfolio_state": portfolio_state.model_dump(mode="json"),
            },
        }, self.timeout_per_call)
        self.handle.step_count += 1
        if not resp.get("ok"):
            raise Q4RuntimeError(f"q4_step failed at step {observation.step_index}: {resp.get('error')}")
        return PolicyDecisionStep.model_validate(resp["result"])

    def q4_finalize(self) -> Q4FinalizeSummary:
        resp = _send(self.handle, {"op": "finalize", "payload": {}}, self.timeout_per_call)
        if not resp.get("ok"):
            raise Q4RuntimeError(f"q4_finalize failed: {resp.get('error')}")
        return Q4FinalizeSummary.model_validate(resp["result"])


# ---------------------------------------------------------------------------
# Worker-side: runs inside the adapter's own conda env
# ---------------------------------------------------------------------------

class _LegacyReplayState:
    """LEGACY_INTERNAL_LOOP fallback: the adapter only implements the
    existing single-shot q4_policy(). Called once on 'initialize', its real
    decisions list (if any) is cached and replayed one PolicyDecisionStep
    per subsequent 'step' request — never fabricating more decisions than
    the adapter's own q4_policy() call actually produced."""

    def __init__(self):
        self.decisions: List[PolicyDecisionStep] = []
        self.cursor = 0
        self.policy: Optional[Q4Policy] = None


def _dispatch(adapter, request: dict, legacy_state: _LegacyReplayState) -> dict:
    op = request.get("op")
    payload = request.get("payload", {})
    try:
        if op == "initialize":
            context = QueryContext.model_validate(payload["context"])
            generation_window = TimeWindow.model_validate(payload["generation_window"])
            initial_portfolio = PortfolioState.model_validate(payload["initial_portfolio"])
            run_config = Q4RunConfig.model_validate(payload["run_config"])

            if isinstance(adapter, Q4StepAdapter):
                policy = adapter.q4_initialize(context, generation_window, initial_portfolio, run_config)
                return {"ok": True, "classification": Q4AdapterClassification.STEPWISE.value,
                        "result": policy.model_dump(mode="json")}

            # LEGACY_INTERNAL_LOOP: call the existing single-shot method once.
            policy = adapter.q4_policy(context, generation_window)
            legacy_state.policy = policy
            legacy_state.decisions = list(policy.decisions) if policy.decisions else []
            legacy_state.cursor = 0
            return {"ok": True, "classification": Q4AdapterClassification.LEGACY_INTERNAL_LOOP.value,
                     "result": policy.model_dump(mode="json")}

        elif op == "step":
            observation = MarketObservation.model_validate(payload["observation"])
            portfolio_state = PortfolioState.model_validate(payload["portfolio_state"])

            if isinstance(adapter, Q4StepAdapter):
                decision = adapter.q4_step(payload["timestamp"], payload["information_cutoff"],
                                            observation, portfolio_state)
                return {"ok": True, "result": decision.model_dump(mode="json")}

            # LEGACY_INTERNAL_LOOP replay: return the next REAL cached decision,
            # never fabricating one beyond what q4_policy() actually produced.
            if legacy_state.cursor >= len(legacy_state.decisions):
                return {"ok": False, "error": (
                    f"LEGACY_INTERNAL_LOOP adapter's real q4_policy() produced only "
                    f"{len(legacy_state.decisions)} real decision(s); step {observation.step_index} "
                    f"has no corresponding real decision to replay (not fabricating one)"
                )}
            decision = legacy_state.decisions[legacy_state.cursor]
            legacy_state.cursor += 1
            return {"ok": True, "result": decision.model_dump(mode="json")}

        elif op == "finalize":
            if isinstance(adapter, Q4StepAdapter):
                summary = adapter.q4_finalize()
                return {"ok": True, "result": summary.model_dump(mode="json")}

            policy = legacy_state.policy
            summary = Q4FinalizeSummary(
                policy_type=policy.policy_type, update_policy=policy.update_policy,
                universe_policy=policy.universe_policy, artifact=policy.artifact,
                explanation=policy.explanation,
            )
            return {"ok": True, "result": summary.model_dump(mode="json")}

        else:
            return {"ok": False, "error": f"unknown op {op!r}"}

    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def worker_main(adapter_path: str, input_stream: IO[str] = sys.stdin, output_stream: IO[str] = None) -> None:
    """The persistent per-session worker loop. `input_stream`/`output_stream`
    are injectable (real sys.stdin/stdout in production, io.StringIO-backed
    fakes in tests/test_q4_adapter_sessions.py) so this dispatch logic is
    testable with zero real subprocess spawning.

    Real, verbose adapters (e.g. adapters/earnmore_adapter.py's real upstream
    dataset/training progress prints, matching many other real ML/RL
    libraries wrapped in this repo) write plain print()/stdout output during
    q4_initialize()/q4_step() — those real writes go through the process-
    global sys.stdout, the SAME stream this protocol's line-delimited-JSON
    responses are written to by default, corrupting the wire format the
    moment any adapter prints anything. Fix: capture the real protocol
    output stream BEFORE redirecting the process-global sys.stdout to
    sys.stderr for the worker's whole lifetime, so adapter-internal print()
    calls never reach the protocol channel — only this function's own
    explicit output_stream.write() calls do."""
    real_output_stream = output_stream if output_stream is not None else sys.stdout
    if output_stream is None:
        # Real fix: redirect the process-global stream print() implicitly
        # targets, not the already-captured real_output_stream reference.
        sys.stdout = sys.stderr

    from CONTRACT.adapter_runner import load_adapter

    adapter = load_adapter(adapter_path)
    legacy_state = _LegacyReplayState()

    output_stream = real_output_stream
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            output_stream.write(json.dumps({"ok": False, "error": f"malformed request: {line!r}"}) + "\n")
            output_stream.flush()
            continue

        if request.get("op") == "shutdown":
            break

        response = _dispatch(adapter, request, legacy_state)
        output_stream.write(json.dumps(response) + "\n")
        output_stream.flush()


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true", required=True)
    parser.add_argument("--adapter", required=True)
    args = parser.parse_args()
    worker_main(args.adapter)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
