"""
tests/test_q4_adapter_sessions.py — validates harness/q4_runtime.py's
worker-side dispatch logic (worker_main / _dispatch) in isolation.

No real `conda run` subprocess is spawned here — worker_main() is called
directly with io.StringIO-backed fake stdin/stdout, driving a real (but
temp-file-based, in-repo-Python-env) fake adapter loaded via the real,
reused CONTRACT.adapter_runner.load_adapter(). This matches this repo's
existing convention of fixture-driven adapter tests with no network/
subprocess (e.g. tests/test_adapter_universal_portfolios.py).

Usage:
    python -m unittest tests.test_q4_adapter_sessions -v
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext, TimeWindow
from harness.q4_protocol import PortfolioState, Q4RunConfig
from harness.q4_runtime import worker_main

_STEPWISE_ADAPTER_SRC = '''
from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q4Policy, PolicyType, PolicyDecisionStep

class FakeStepwiseAdapter(BaseAdapter):
    name = "fake_stepwise"
    questions_answered = ["Q4"]
    upstream_repo = "https://example.com/fake"

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        return Q4Policy(context=context, policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
                         generation_window=generation_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
        return PolicyDecisionStep(timestamp=timestamp, information_cutoff=information_cutoff,
                                   target_weights={"AAPL": 0.5, "CASH": 0.5})

    def q4_finalize(self):
        from harness.q4_protocol import Q4FinalizeSummary
        return Q4FinalizeSummary(policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY)
'''

_LEGACY_ADAPTER_SRC = '''
from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q4Policy, PolicyType, PolicyDecisionStep

class FakeLegacyAdapter(BaseAdapter):
    name = "fake_legacy"
    questions_answered = ["Q4"]
    upstream_repo = "https://example.com/fake"

    def q4_policy(self, context, generation_window, **kwargs):
        decisions = [
            PolicyDecisionStep(timestamp="2024-01-16", information_cutoff="2024-01-15", target_weights={"AAPL": 0.5}),
            PolicyDecisionStep(timestamp="2024-01-17", information_cutoff="2024-01-16", target_weights={"AAPL": 0.6}),
        ]
        return Q4Policy(context=context, policy_type=PolicyType.FROZEN_LEARNED_POLICY,
                         generation_window=generation_window, decisions=decisions)
'''

_ERRORING_ADAPTER_SRC = '''
from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q4Policy, PolicyType

class FakeErroringAdapter(BaseAdapter):
    name = "fake_erroring"
    questions_answered = ["Q4"]
    upstream_repo = "https://example.com/fake"

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        return Q4Policy(context=context, policy_type=PolicyType.STATIC_ALLOCATION,
                         generation_window=generation_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
        raise ValueError("real per-step failure, e.g. a real upstream training divergence")

    def q4_finalize(self):
        from harness.q4_protocol import Q4FinalizeSummary
        return Q4FinalizeSummary(policy_type=PolicyType.STATIC_ALLOCATION)
'''


def _write_temp_adapter(src: str) -> str:
    fd, path = tempfile.mkstemp(suffix="_adapter.py")
    with os.fdopen(fd, "w") as f:
        f.write(src)
    return path


def _run_worker(adapter_path: str, requests: list) -> list:
    input_stream = io.StringIO("\n".join(json.dumps(r) for r in requests) + "\n")
    output_stream = io.StringIO()
    worker_main(adapter_path, input_stream, output_stream)
    output_stream.seek(0)
    return [json.loads(line) for line in output_stream if line.strip()]


def _ctx_window_cfg_state():
    ctx = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.PORTFOLIO, universe=["AAPL"])
    window = TimeWindow(start="2023-06-01", end="2024-01-15")
    cfg = Q4RunConfig(task_id="t1", session_id="s1", context=ctx, generation_window=window)
    state = PortfolioState(as_of="2024-01-15")
    return ctx, window, cfg, state


def _obs_req(i, ts, cutoff, state):
    return {"op": "step", "payload": {
        "timestamp": ts, "information_cutoff": cutoff,
        "observation": {"step_index": i, "timestamp": ts, "information_cutoff": cutoff},
        "portfolio_state": state.model_dump(mode="json"),
    }}


def _init_req(ctx, window, state, cfg):
    return {"op": "initialize", "payload": {
        "context": ctx.model_dump(mode="json"), "generation_window": window.model_dump(mode="json"),
        "initial_portfolio": state.model_dump(mode="json"), "run_config": cfg.model_dump(mode="json"),
    }}


class TestStepwiseDispatch(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_adapter(_STEPWISE_ADAPTER_SRC)

    def tearDown(self):
        os.unlink(self.path)

    def test_full_session_dispatch(self):
        ctx, window, cfg, state = _ctx_window_cfg_state()
        requests = [
            _init_req(ctx, window, state, cfg),
            _obs_req(0, "2024-01-16", "2024-01-15", state),
            {"op": "finalize", "payload": {}},
            {"op": "shutdown"},
        ]
        responses = _run_worker(self.path, requests)
        self.assertEqual(len(responses), 3)
        self.assertTrue(responses[0]["ok"])
        self.assertEqual(responses[0]["classification"], "STEPWISE")
        self.assertTrue(responses[1]["ok"])
        self.assertEqual(responses[1]["result"]["target_weights"], {"AAPL": 0.5, "CASH": 0.5})
        self.assertTrue(responses[2]["ok"])
        self.assertEqual(responses[2]["result"]["policy_type"], "ONLINE_ADAPTIVE_POLICY")


class TestLegacyReplayDispatch(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_adapter(_LEGACY_ADAPTER_SRC)

    def tearDown(self):
        os.unlink(self.path)

    def test_classification_is_legacy(self):
        ctx, window, cfg, state = _ctx_window_cfg_state()
        responses = _run_worker(self.path, [_init_req(ctx, window, state, cfg), {"op": "shutdown"}])
        self.assertEqual(responses[0]["classification"], "LEGACY_INTERNAL_LOOP")

    def test_replays_real_decisions_in_order(self):
        ctx, window, cfg, state = _ctx_window_cfg_state()
        requests = [
            _init_req(ctx, window, state, cfg),
            _obs_req(0, "2024-01-16", "2024-01-15", state),
            _obs_req(1, "2024-01-17", "2024-01-16", state),
            {"op": "shutdown"},
        ]
        responses = _run_worker(self.path, requests)
        self.assertEqual(responses[1]["result"]["target_weights"], {"AAPL": 0.5})
        self.assertEqual(responses[2]["result"]["target_weights"], {"AAPL": 0.6})

    def test_exhausted_real_decisions_returns_honest_error_not_fabrication(self):
        """The core no-fabrication guarantee: once the real q4_policy() call's
        decisions are exhausted, further step requests must fail honestly,
        never synthesize an additional decision."""
        ctx, window, cfg, state = _ctx_window_cfg_state()
        requests = [
            _init_req(ctx, window, state, cfg),
            _obs_req(0, "2024-01-16", "2024-01-15", state),
            _obs_req(1, "2024-01-17", "2024-01-16", state),
            _obs_req(2, "2024-01-18", "2024-01-17", state),  # only 2 real decisions exist
            {"op": "shutdown"},
        ]
        responses = _run_worker(self.path, requests)
        self.assertFalse(responses[3]["ok"])
        self.assertIn("not fabricating", responses[3]["error"])

    def test_finalize_derives_summary_from_real_policy(self):
        ctx, window, cfg, state = _ctx_window_cfg_state()
        requests = [_init_req(ctx, window, state, cfg), {"op": "finalize", "payload": {}}, {"op": "shutdown"}]
        responses = _run_worker(self.path, requests)
        self.assertEqual(responses[1]["result"]["policy_type"], "FROZEN_LEARNED_POLICY")


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.path = _write_temp_adapter(_ERRORING_ADAPTER_SRC)

    def tearDown(self):
        os.unlink(self.path)

    def test_step_exception_returns_error_response_not_crash(self):
        ctx, window, cfg, state = _ctx_window_cfg_state()
        requests = [
            _init_req(ctx, window, state, cfg),
            _obs_req(0, "2024-01-16", "2024-01-15", state),
            {"op": "finalize", "payload": {}},  # worker must still respond to this
            {"op": "shutdown"},
        ]
        responses = _run_worker(self.path, requests)
        self.assertTrue(responses[0]["ok"])
        self.assertFalse(responses[1]["ok"])
        self.assertIn("real per-step failure", responses[1]["error"])
        self.assertTrue(responses[2]["ok"])  # dispatcher survives a per-request exception

    def test_malformed_json_request_returns_error_not_crash(self):
        input_stream = io.StringIO("not valid json\n" + json.dumps({"op": "shutdown"}) + "\n")
        output_stream = io.StringIO()
        worker_main(self.path, input_stream, output_stream)
        output_stream.seek(0)
        lines = [json.loads(l) for l in output_stream if l.strip()]
        self.assertFalse(lines[0]["ok"])

    def test_unknown_op_returns_error(self):
        responses = _run_worker(self.path, [{"op": "not_a_real_op", "payload": {}}, {"op": "shutdown"}])
        self.assertFalse(responses[0]["ok"])
        self.assertIn("unknown op", responses[0]["error"])


if __name__ == "__main__":
    unittest.main()
