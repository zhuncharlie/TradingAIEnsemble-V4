"""
tests/test_q4_execution_engine.py — validates harness/execution_engine.py's
Q4ExecutionEngine end-to-end against in-process fake Q4StepAdapters (no
subprocess, no real conda env, no real adapter import) and
harness/portfolio_state.py's apply_constraints/PortfolioLedger.

Usage:
    python -m unittest tests.test_q4_execution_engine -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    OutputScope,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    TimeWindow,
)
from harness.execution_engine import Q4ExecutionEngine
from harness.portfolio_state import PortfolioLedger, apply_constraints
from harness.q4_protocol import (
    MarketObservation,
    PortfolioState,
    Q4AdapterClassification,
    Q4CausalityViolation,
    Q4FinalizeSummary,
    Q4RunConfig,
)


def make_context(universe=None) -> QueryContext:
    return QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.PORTFOLIO,
                         universe=universe or ["AAPL"])


def make_window() -> TimeWindow:
    return TimeWindow(start="2023-06-01", end="2024-01-15")


def make_observations(n: int, start_day: int = 10) -> List[MarketObservation]:
    return [
        MarketObservation(step_index=i, timestamp=f"2024-01-{start_day+i:02d}",
                           information_cutoff=f"2024-01-{start_day+i-1:02d}")
        for i in range(n)
    ]


class HonestFixedWeightAdapter:
    """A fake, always-causal, honest STEPWISE adapter."""
    name = "fake_fixed_weight"
    init_calls = 0
    step_calls = 0
    finalize_calls = 0

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        self.init_calls += 1
        return Q4Policy(context=context, policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
                         generation_window=generation_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
        self.step_calls += 1
        return PolicyDecisionStep(timestamp=timestamp, information_cutoff=information_cutoff,
                                   target_weights={"AAPL": 0.7, "CASH": 0.3})

    def q4_finalize(self):
        self.finalize_calls += 1
        return Q4FinalizeSummary(policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY)


class ConstraintViolatingAdapter:
    name = "fake_violator"

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        return Q4Policy(context=context, policy_type=PolicyType.STATIC_ALLOCATION,
                         generation_window=generation_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
        return PolicyDecisionStep(timestamp=timestamp, information_cutoff=information_cutoff,
                                   target_weights={"AAPL": -0.2, "MSFT": 1.2})

    def q4_finalize(self):
        return Q4FinalizeSummary(policy_type=PolicyType.STATIC_ALLOCATION)


class CausalityCheatingAdapter:
    name = "fake_cheater"

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        return Q4Policy(context=context, policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
                         generation_window=generation_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
        return PolicyDecisionStep(timestamp=timestamp, information_cutoff="2099-01-01",
                                   target_weights={"AAPL": 1.0})

    def q4_finalize(self):
        return Q4FinalizeSummary(policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY)


class WindowTamperingAdapter:
    name = "fake_tamperer"

    def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
        bad_window = TimeWindow(start="2023-12-01", end=generation_window.end)
        return Q4Policy(context=context, policy_type=PolicyType.STATIC_ALLOCATION,
                         generation_window=bad_window, initial_weights={"AAPL": 1.0})

    def q4_step(self, *a, **kw):
        raise AssertionError("should never be called — initialize fails first")

    def q4_finalize(self):
        raise AssertionError("should never be called — initialize fails first")


class TestQ4ExecutionEngineHappyPath(unittest.TestCase):
    def test_call_counts_and_trajectory(self):
        adapter = HonestFixedWeightAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window())
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(3), Q4AdapterClassification.STEPWISE)
        result = engine.run()

        self.assertEqual(adapter.init_calls, 1)
        self.assertEqual(adapter.step_calls, 3)
        self.assertEqual(adapter.finalize_calls, 1)
        self.assertEqual(result.n_steps, 3)
        self.assertEqual(result.n_causality_violations, 0)
        self.assertEqual(result.n_constraint_violations, 0)
        self.assertEqual(len(result.policy.decisions), 3)
        self.assertEqual(result.classification, Q4AdapterClassification.STEPWISE)

    def test_max_steps_truncates(self):
        adapter = HonestFixedWeightAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                           max_steps=2)
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(5), Q4AdapterClassification.STEPWISE)
        result = engine.run()
        self.assertEqual(result.n_steps, 2)

    def test_assembled_policy_is_schema_valid_and_round_trips(self):
        adapter = HonestFixedWeightAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window())
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(2), Q4AdapterClassification.STEPWISE)
        result = engine.run()
        restored = Q4Policy.model_validate(result.policy.model_dump())
        self.assertEqual(restored, result.policy)


class TestQ4ExecutionEngineConstraints(unittest.TestCase):
    def test_constraint_violations_are_projected_not_silently_dropped(self):
        adapter = ConstraintViolatingAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                           constraints=PortfolioConstraints(long_only=True), projection_mode="clip")
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(1), Q4AdapterClassification.STEPWISE)
        result = engine.run()
        self.assertEqual(result.n_constraint_violations, 1)
        self.assertEqual(result.results[0].decision.target_weights["AAPL"], 0.0)
        self.assertTrue(result.results[0].projection_applied)

    def test_reject_mode_raises(self):
        adapter = ConstraintViolatingAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                           constraints=PortfolioConstraints(long_only=True), projection_mode="reject")
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(1), Q4AdapterClassification.STEPWISE)
        with self.assertRaises(Exception):
            engine.run()


class TestQ4ExecutionEngineCausalityAbort(unittest.TestCase):
    def test_fail_fast_aborts_on_causality_violation(self):
        adapter = CausalityCheatingAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                           fail_fast=True)
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(1), Q4AdapterClassification.STEPWISE)
        with self.assertRaises(Q4CausalityViolation):
            engine.run()

    def test_fail_fast_false_continues_and_counts(self):
        adapter = CausalityCheatingAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                           fail_fast=False)
        engine = Q4ExecutionEngine(adapter, cfg, make_observations(2), Q4AdapterClassification.STEPWISE)
        result = engine.run()
        self.assertEqual(result.n_causality_violations, 2)
        self.assertEqual(result.n_steps, 2)

    def test_generation_window_tampering_rejected_at_initialize(self):
        adapter = WindowTamperingAdapter()
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window())
        engine = Q4ExecutionEngine(adapter, cfg, [], Q4AdapterClassification.STEPWISE)
        with self.assertRaises(Q4CausalityViolation):
            engine.run()


class TestApplyConstraintsAndLedger(unittest.TestCase):
    def test_long_only_clip(self):
        w, v, p = apply_constraints({"AAPL": -0.1, "MSFT": 1.1}, PortfolioConstraints(long_only=True), {}, "clip")
        self.assertEqual(w["AAPL"], 0.0)
        self.assertTrue(p)
        self.assertEqual(len(v), 1)

    def test_no_violation_no_projection(self):
        w, v, p = apply_constraints({"AAPL": 0.5, "CASH": 0.5}, PortfolioConstraints(long_only=True), {}, "clip")
        self.assertEqual(w, {"AAPL": 0.5, "CASH": 0.5})
        self.assertFalse(p)
        self.assertEqual(v, [])

    def test_gross_exposure_scaled_down(self):
        w, v, p = apply_constraints({"AAPL": 0.8, "MSFT": 0.8}, PortfolioConstraints(gross_exposure_limit=1.0), {}, "clip")
        self.assertAlmostEqual(sum(abs(x) for x in w.values()), 1.0, places=6)
        self.assertTrue(p)

    def test_turnover_limit_partial_fill(self):
        prior = {"AAPL": 0.0, "CASH": 1.0}
        target = {"AAPL": 1.0, "CASH": 0.0}
        w, v, p = apply_constraints(target, PortfolioConstraints(turnover_limit=0.3), prior, "clip")
        # full turnover would be 1.0; limited to 0.3 -> only 30% of the way there
        self.assertAlmostEqual(w["AAPL"], 0.3, places=6)
        self.assertTrue(p)

    def test_no_constraints_passthrough(self):
        w, v, p = apply_constraints({"AAPL": 5.0}, None, {}, "clip")
        self.assertEqual(w, {"AAPL": 5.0})
        self.assertFalse(p)

    def test_ledger_advance(self):
        prior = PortfolioState(as_of="2024-01-01", weights={"AAPL": 0.5}, nav=1.0, step_index=0)
        new_state = PortfolioLedger.advance(prior, {"AAPL": 0.8, "CASH": 0.2}, "2024-01-02")
        self.assertEqual(new_state.weights, {"AAPL": 0.8, "CASH": 0.2})
        self.assertEqual(new_state.step_index, 1)
        self.assertEqual(new_state.last_rebalance_timestamp, "2024-01-02")

    def test_ledger_turnover_computation(self):
        prior = PortfolioState(as_of="2024-01-01", weights={"AAPL": 0.5, "CASH": 0.5})
        turnover = PortfolioLedger.turnover(prior, {"AAPL": 1.0, "CASH": 0.0})
        self.assertAlmostEqual(turnover, 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
