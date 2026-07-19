"""
tests/test_q4_step_protocol.py — validates harness/q4_protocol.py's data
contract and structural typing in isolation.

No network calls, no real adapter imports, no subprocess — stdlib unittest
only, matching CONTRACT/test_harness.py's convention.

Usage:
    python -m unittest tests.test_q4_step_protocol -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from CONTRACT.schemas import (
    OutputScope,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    QueryContext,
    TimeWindow,
)
from harness.q4_protocol import (
    ExecutionResult,
    MarketObservation,
    Q4AdapterClassification,
    Q4AdapterSession,
    Q4CausalityViolation,
    Q4ConstraintViolation,
    Q4FinalizeSummary,
    Q4RunConfig,
    Q4RunResult,
    Q4StepAdapter,
    PortfolioState,
    RunStatus,
)


def make_context() -> QueryContext:
    return QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.PORTFOLIO,
                         universe=["AAPL", "MSFT", "NVDA"])


def make_window() -> TimeWindow:
    return TimeWindow(start="2023-06-01", end="2024-01-15")


class TestMarketObservation(unittest.TestCase):
    def test_valid_construction(self):
        obs = MarketObservation(step_index=0, timestamp="2024-01-15", information_cutoff="2024-01-14",
                                 universe=["AAPL"])
        self.assertEqual(obs.step_index, 0)
        self.assertTrue(obs.is_rebalance_point)

    def test_cutoff_after_timestamp_rejected(self):
        with self.assertRaises(ValidationError):
            MarketObservation(step_index=0, timestamp="2024-01-14", information_cutoff="2024-01-15")

    def test_cutoff_equal_timestamp_allowed(self):
        obs = MarketObservation(step_index=0, timestamp="2024-01-15", information_cutoff="2024-01-15")
        self.assertEqual(obs.timestamp, obs.information_cutoff)

    def test_negative_step_index_rejected(self):
        with self.assertRaises(ValidationError):
            MarketObservation(step_index=-1, timestamp="2024-01-15", information_cutoff="2024-01-14")

    def test_optional_bar_and_features(self):
        obs = MarketObservation(
            step_index=1, timestamp="2024-01-16", information_cutoff="2024-01-15",
            bar={"AAPL": {"close": 185.0}}, features={"rsi": 55.2},
        )
        self.assertEqual(obs.bar["AAPL"]["close"], 185.0)
        self.assertEqual(obs.features["rsi"], 55.2)

    def test_round_trip(self):
        obs = MarketObservation(step_index=2, timestamp="2024-01-17", information_cutoff="2024-01-16",
                                 universe=["AAPL", "MSFT"])
        restored = MarketObservation.model_validate(obs.model_dump())
        self.assertEqual(obs, restored)


class TestPortfolioState(unittest.TestCase):
    def test_valid_construction(self):
        ps = PortfolioState(as_of="2024-01-15", weights={"AAPL": 0.6, "CASH": 0.4})
        self.assertEqual(ps.nav, 1.0)
        self.assertEqual(ps.step_index, 0)

    def test_default_empty_weights(self):
        ps = PortfolioState(as_of="2024-01-15")
        self.assertEqual(ps.weights, {})

    def test_round_trip(self):
        ps = PortfolioState(as_of="2024-01-16", weights={"AAPL": 1.0}, nav=1.05, step_index=3,
                             last_rebalance_timestamp="2024-01-10")
        restored = PortfolioState.model_validate(ps.model_dump())
        self.assertEqual(ps, restored)


class TestQ4RunConfig(unittest.TestCase):
    def test_valid_construction(self):
        cfg = Q4RunConfig(
            task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
            rebalance_schedule=["2023-12-01", "2023-12-15"],
            constraints=PortfolioConstraints(long_only=True),
        )
        self.assertEqual(cfg.projection_mode, "clip")
        self.assertTrue(cfg.fail_fast)

    def test_projection_mode_literal_enforced(self):
        with self.assertRaises(ValidationError):
            Q4RunConfig(
                task_id="t1", session_id="s1", context=make_context(), generation_window=make_window(),
                projection_mode="not_a_real_mode",
            )

    def test_round_trip(self):
        cfg = Q4RunConfig(task_id="t1", session_id="s1", context=make_context(), generation_window=make_window())
        restored = Q4RunConfig.model_validate(cfg.model_dump())
        self.assertEqual(cfg, restored)


class TestExecutionResultAndSummary(unittest.TestCase):
    def _decision(self) -> PolicyDecisionStep:
        return PolicyDecisionStep(timestamp="2024-01-15", information_cutoff="2024-01-14",
                                   target_weights={"AAPL": 1.0})

    def test_execution_result_construction(self):
        res = ExecutionResult(
            step_index=0, decision=self._decision(),
            pre_trade_state=PortfolioState(as_of="2024-01-14"),
        )
        self.assertTrue(res.causality_ok)
        self.assertEqual(res.constraint_violations, [])

    def test_finalize_summary_construction(self):
        summary = Q4FinalizeSummary(policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY)
        self.assertEqual(summary.policy_type, PolicyType.ONLINE_ADAPTIVE_POLICY)

    def test_session_defaults(self):
        session = Q4AdapterSession(session_id="s1", adapter_name="universal_portfolios")
        self.assertEqual(session.step_count, 0)
        self.assertFalse(session.initialized)
        self.assertFalse(session.finalized)


class TestClassificationAndStatusVocabularies(unittest.TestCase):
    def test_classification_values(self):
        self.assertEqual(
            {c.value for c in Q4AdapterClassification},
            {"STEPWISE", "LEGACY_INTERNAL_LOOP", "STATIC_ONLY", "BLOCKED"},
        )

    def test_run_status_values(self):
        self.assertEqual(
            {s.value for s in RunStatus},
            {"PASSED", "FAILED", "BLOCKED", "TIMEOUT", "SKIPPED", "NOT_RUN", "STEPWISE_UNSUPPORTED"},
        )

    def test_exceptions_are_runtime_errors(self):
        self.assertTrue(issubclass(Q4CausalityViolation, RuntimeError))
        self.assertTrue(issubclass(Q4ConstraintViolation, RuntimeError))


class TestQ4StepAdapterStructuralTyping(unittest.TestCase):
    def test_full_implementation_matches(self):
        class FullStepAdapter:
            def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
                pass

            def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
                pass

            def q4_finalize(self):
                pass

        self.assertIsInstance(FullStepAdapter(), Q4StepAdapter)

    def test_legacy_only_adapter_does_not_match(self):
        class LegacyOnlyAdapter:
            def q4_policy(self, context, generation_window):
                pass

        self.assertNotIsInstance(LegacyOnlyAdapter(), Q4StepAdapter)

    def test_partial_implementation_does_not_match(self):
        class PartialAdapter:
            def q4_initialize(self, context, generation_window, initial_portfolio, run_config):
                pass

            def q4_step(self, timestamp, information_cutoff, observation, portfolio_state):
                pass
            # missing q4_finalize

        self.assertNotIsInstance(PartialAdapter(), Q4StepAdapter)


if __name__ == "__main__":
    unittest.main()
