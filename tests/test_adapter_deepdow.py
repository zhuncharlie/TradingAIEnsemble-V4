"""
tests/test_adapter_deepdow.py — schema/serialization contract test + fixture
mapping test for adapters/deepdow_adapter.py.

No network calls, no upstream/torch imports: the fixture-mapping tests
exercise adapters.deepdow_adapter._build_decision_step() (the pure
per-day-weights -> PolicyDecisionStep mapping) against a hand-authored
fixture matching the real deepdow GreatNet per-day output shape (see
tests/fixtures/deepdow_fixture.json). Matches this repo's existing test
convention (see CONTRACT/test_harness.py, tests/test_adapter_skfolio.py) —
stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_deepdow -v
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
from adapters.deepdow_adapter import _build_decision_step, _split_train_test

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "deepdow_fixture.json"


class TestDeepdowSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_causal_ordering_round_trips(self):
        step1 = PolicyDecisionStep(
            timestamp="2023-11-28", information_cutoff="2023-11-27",
            target_weights={"AAPL": 0.6, "MSFT": 0.4},
        )
        step2 = PolicyDecisionStep(
            timestamp="2023-11-29", information_cutoff="2023-11-28",
            target_weights={"AAPL": 0.55, "MSFT": 0.45},
        )
        dumped = [step1.model_dump(), step2.model_dump()]
        restored = [PolicyDecisionStep.model_validate(d) for d in dumped]
        self.assertLessEqual(restored[0].information_cutoff, restored[0].timestamp)
        self.assertLessEqual(restored[1].information_cutoff, restored[1].timestamp)
        self.assertLess(restored[0].timestamp, restored[1].timestamp)

    def test_q4_policy_long_only_constraint_rejects_negative_weight(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15",
                                scope=OutputScope.PORTFOLIO, universe=["AAPL", "MSFT"])
        with self.assertRaises(Exception):
            Q4Policy(
                context=context,
                policy_type=PolicyType.FROZEN_LEARNED_POLICY,
                generation_window=TimeWindow(start="2023-06-01", end="2024-01-15"),
                constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
                initial_weights={"AAPL": -0.1, "MSFT": 1.1},
            )

    def test_frozen_learned_policy_type_constructs(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15",
                                scope=OutputScope.PORTFOLIO, universe=["AAPL", "MSFT"])
        q4 = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=TimeWindow(start="2023-06-01", end="2024-01-15"),
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
            update_policy=UpdatePolicy(mode=UpdateMode.NONE, update_frequency="never after initial training"),
            decisions=[
                PolicyDecisionStep(timestamp="2023-11-28", information_cutoff="2023-11-27",
                                    target_weights={"AAPL": 0.5, "MSFT": 0.5}),
            ],
        )
        self.assertEqual(q4.policy_type, "FROZEN_LEARNED_POLICY")
        self.assertEqual(len(q4.decisions), 1)


class TestDeepdowFixtureMapping(unittest.TestCase):
    """Fixture-driven mapping tests — pure function, no network/model calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_build_decision_step_from_fixture(self):
        d = self.fixture["decisions"][0]
        step = _build_decision_step(d["timestamp"], d["information_cutoff"], d["weights"], d["active_tickers"])
        self.assertEqual(step.timestamp, d["timestamp"])
        self.assertEqual(step.information_cutoff, d["information_cutoff"])
        self.assertEqual(step.target_weights, d["weights"])
        self.assertEqual(step.selected_universe, d["active_tickers"])
        self.assertLessEqual(step.information_cutoff, step.timestamp)

    def test_all_fixture_decisions_produce_causally_ordered_trajectory(self):
        steps = [
            _build_decision_step(d["timestamp"], d["information_cutoff"], d["weights"], d["active_tickers"])
            for d in self.fixture["decisions"]
        ]
        for step in steps:
            self.assertLessEqual(step.information_cutoff, step.timestamp)
        timestamps = [s.timestamp for s in steps]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_fixture_weights_are_long_only_and_sum_to_1(self):
        for d in self.fixture["decisions"]:
            weights = d["weights"]
            self.assertTrue(all(w >= 0.0 for w in weights.values()))
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)


class TestDeepdowSplitHelper(unittest.TestCase):
    """Pure helper function — no network/model calls."""

    def test_split_never_leaves_fewer_than_lookback_train_days(self):
        split, n = _split_train_test(n_dates=100, lookback=20)
        self.assertGreaterEqual(split, 21)
        self.assertLess(split, n)

    def test_split_respects_seventy_percent_when_lookback_is_small(self):
        split, n = _split_train_test(n_dates=200, lookback=5)
        self.assertEqual(split, 140)


if __name__ == "__main__":
    unittest.main()
