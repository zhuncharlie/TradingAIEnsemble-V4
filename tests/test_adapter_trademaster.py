"""
tests/test_adapter_trademaster.py — schema/serialization contract test +
fixture mapping test for adapters/trademaster_adapter.py.

No network calls, no upstream imports: the fixture-mapping tests exercise
adapters.trademaster_adapter._build_decision_step() (the pure raw-step ->
PolicyDecisionStep mapping) against a hand-authored fixture matching the
real TradeMaster PortfolioManagementEIIEEnvironment/EIIEConv output shape
(see tests/fixtures/trademaster_fixture.json). Matches this repo's existing
test convention (see CONTRACT/test_harness.py, tests/test_adapter_skfolio.py)
— stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_trademaster -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

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
    UpdateMode,
    UpdatePolicy,
)
from adapters.trademaster_adapter import _build_decision_step, _tickers_from_context

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "trademaster_fixture.json"


class TestTradeMasterSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_causal_ordering_round_trips(self):
        step1 = PolicyDecisionStep(
            timestamp="2021-06-02", information_cutoff="2021-06-01",
            selected_universe=["AAPL", "MSFT"],
            target_weights={"CASH": 0.1, "AAPL": 0.5, "MSFT": 0.4},
        )
        step2 = PolicyDecisionStep(
            timestamp="2021-06-03", information_cutoff="2021-06-02",
            selected_universe=["AAPL", "MSFT"],
            target_weights={"CASH": 0.0, "AAPL": 0.6, "MSFT": 0.4},
        )
        dumped = [step1.model_dump(), step2.model_dump()]
        restored = [PolicyDecisionStep.model_validate(d) for d in dumped]
        self.assertLessEqual(restored[0].information_cutoff, restored[0].timestamp)
        self.assertLessEqual(restored[1].information_cutoff, restored[1].timestamp)
        self.assertLess(restored[0].timestamp, restored[1].timestamp)

    def test_q4_policy_long_only_constraint_rejects_negative_weight(self):
        context = QueryContext(
            as_of="2021-12-31", data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO, universe=["AAPL", "MSFT"],
        )
        generation_window = TimeWindow(start="2021-01-04", end="2021-12-31")
        step = PolicyDecisionStep(
            timestamp="2021-06-02", information_cutoff="2021-06-01",
            target_weights={"CASH": 0.1, "AAPL": -0.2, "MSFT": 1.1},
        )
        # Q4Policy itself validates decisions[*].target_weights against
        # constraints.long_only — this real, negative weight must be
        # rejected at construction time, confirming the schema-level
        # enforcement this adapter relies on (it never needs its own
        # separate long-only check beyond emitting real softmax weights).
        with self.assertRaises(ValueError):
            Q4Policy(
                context=context,
                policy_type=PolicyType.FROZEN_LEARNED_POLICY,
                generation_window=generation_window,
                constraints=PortfolioConstraints(long_only=True),
                decisions=[step],
            )

    def test_frozen_learned_policy_with_update_mode_none_constructs(self):
        context = QueryContext(
            as_of="2021-12-31", data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO, universe=["AAPL"],
        )
        generation_window = TimeWindow(start="2021-01-04", end="2021-12-31")
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            update_policy=UpdatePolicy(mode=UpdateMode.NONE),
            initial_weights={"CASH": 0.2, "AAPL": 0.8},
        )
        self.assertEqual(policy.policy_type, "FROZEN_LEARNED_POLICY")
        self.assertEqual(policy.update_policy.mode, "NONE")


class TestTradeMasterFixtureMapping(unittest.TestCase):
    """Offline mapping tests against a hand-authored fixture — no network,
    no real TradeMaster/torch imports required."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_build_decision_step_from_fixture(self):
        raw = self.fixture["raw_steps"][0]
        step = _build_decision_step(raw)
        self.assertIsInstance(step, PolicyDecisionStep)
        self.assertEqual(step.timestamp, "2021-06-02")
        self.assertEqual(step.information_cutoff, "2021-06-01")
        self.assertEqual(step.selected_universe, ["AAPL", "JNJ", "MSFT"])
        self.assertAlmostEqual(sum(step.target_weights.values()), 1.0, places=6)

    def test_all_fixture_steps_are_causally_ordered_and_long_only(self):
        steps = [_build_decision_step(r) for r in self.fixture["raw_steps"]]
        for s in steps:
            self.assertLessEqual(s.information_cutoff, s.timestamp)
            self.assertTrue(all(v >= -1e-9 for v in s.target_weights.values()))
            self.assertAlmostEqual(sum(s.target_weights.values()), 1.0, places=6)
        for i in range(1, len(steps)):
            self.assertLess(steps[i - 1].timestamp, steps[i].timestamp)

    def test_fixture_steps_construct_valid_q4policy_trajectory(self):
        context = QueryContext(
            as_of="2021-06-04", data_cutoff="2021-06-04",
            scope=OutputScope.PORTFOLIO, universe=["AAPL", "JNJ", "MSFT"],
        )
        generation_window = TimeWindow(start="2021-01-04", end="2021-06-04")
        decisions = [_build_decision_step(r) for r in self.fixture["raw_steps"]]
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            constraints=PortfolioConstraints(long_only=True, cash_allowed=True),
            decisions=decisions,
        )
        self.assertEqual(len(policy.decisions), 3)
        self.assertEqual(policy.generation_window.start, "2021-01-04")


class TestTradeMasterTickerSelection(unittest.TestCase):
    """_tickers_from_context is pure and offline-testable."""

    def test_real_dj30_tickers_pass_through(self):
        context = QueryContext(
            as_of="2021-12-31", data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO, universe=["MSFT", "AAPL"],
        )
        self.assertEqual(_tickers_from_context(context), ["AAPL", "MSFT"])

    def test_unrelated_ticker_raises_without_silent_substitution(self):
        context = QueryContext(
            as_of="2021-12-31", data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO, universe=["NOTAREALTICKERXYZ"],
        )
        with self.assertRaises(ValueError):
            _tickers_from_context(context)

    def test_mixed_real_and_unreal_ticker_keeps_only_real(self):
        context = QueryContext(
            as_of="2021-12-31", data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO, universe=["AAPL", "NOTAREALTICKERXYZ"],
        )
        self.assertEqual(_tickers_from_context(context), ["AAPL"])


if __name__ == "__main__":
    unittest.main()
