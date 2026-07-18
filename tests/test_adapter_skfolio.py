"""
tests/test_adapter_skfolio.py — schema/serialization contract test + fixture
mapping test for adapters/skfolio_adapter.py.

No network calls, no upstream imports: the fixture-mapping tests exercise
adapters.skfolio_adapter._build_decision_step() (the pure fold-weights ->
PolicyDecisionStep mapping) against a hand-authored fixture matching the
real skfolio.model_selection.WalkForward fold shape (see
tests/fixtures/skfolio_fixture.json). Matches this repo's existing test
convention (see CONTRACT/test_harness.py, tests/test_adapter_finagent.py) —
stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_skfolio -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    OutputScope,
    TimeWindow,
)
from adapters.skfolio_adapter import _build_decision_step

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "skfolio_fixture.json"


class TestSkfolioSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_causal_ordering_round_trips(self):
        step1 = PolicyDecisionStep(
            timestamp="2023-08-28", information_cutoff="2023-08-25",
            target_weights={"AAPL": 0.5, "MSFT": 0.5},
        )
        step2 = PolicyDecisionStep(
            timestamp="2023-09-12", information_cutoff="2023-09-11",
            target_weights={"AAPL": 0.4, "MSFT": 0.6},
        )
        dumped = [step1.model_dump(), step2.model_dump()]
        restored = [PolicyDecisionStep.model_validate(d) for d in dumped]
        self.assertLessEqual(restored[0].information_cutoff, restored[0].timestamp)
        self.assertLessEqual(restored[1].information_cutoff, restored[1].timestamp)
        self.assertLess(restored[0].timestamp, restored[1].timestamp)

    def test_q4_policy_long_only_constraint_rejects_negative_weight(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15",
                                scope=OutputScope.PORTFOLIO, universe=["AAPL", "MSFT"])
        constraints = PortfolioConstraints(long_only=True)
        with self.assertRaises(Exception):
            Q4Policy(
                context=context,
                policy_type=PolicyType.ROLLING_OPTIMIZER,
                generation_window=TimeWindow(start="2023-06-01", end="2024-01-15"),
                constraints=constraints,
                initial_weights={"AAPL": -0.1, "MSFT": 1.1},
            )

    def test_rolling_optimizer_policy_type_constructs(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15",
                                scope=OutputScope.PORTFOLIO, universe=["AAPL", "MSFT"])
        q4 = Q4Policy(
            context=context,
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=TimeWindow(start="2023-06-01", end="2024-01-15"),
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
            decisions=[
                PolicyDecisionStep(timestamp="2023-08-28", information_cutoff="2023-08-25",
                                    target_weights={"AAPL": 0.5, "MSFT": 0.5}),
            ],
        )
        self.assertEqual(q4.policy_type, "ROLLING_OPTIMIZER")
        self.assertEqual(len(q4.decisions), 1)


class TestSkfolioFixtureMapping(unittest.TestCase):
    """Fixture-driven mapping tests — pure function, no network/model calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_build_decision_step_from_fixture(self):
        fold = self.fixture["folds"][0]
        step = _build_decision_step(
            fold["train_end_date"], fold["test_start_date"], fold["weights"],
            fold["active_tickers"], fold["train_size"],
        )
        self.assertEqual(step.timestamp, fold["test_start_date"])
        self.assertEqual(step.information_cutoff, fold["train_end_date"])
        self.assertEqual(step.target_weights, fold["weights"])
        self.assertEqual(step.selected_universe, fold["active_tickers"])
        self.assertLessEqual(step.information_cutoff, step.timestamp)

    def test_all_fixture_folds_produce_causally_ordered_trajectory(self):
        steps = [
            _build_decision_step(f["train_end_date"], f["test_start_date"], f["weights"],
                                  f["active_tickers"], f["train_size"])
            for f in self.fixture["folds"]
        ]
        for step in steps:
            self.assertLessEqual(step.information_cutoff, step.timestamp)
        timestamps = [s.timestamp for s in steps]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_fixture_weights_are_long_only_and_sum_to_1(self):
        for fold in self.fixture["folds"]:
            weights = fold["weights"]
            self.assertTrue(all(w >= 0.0 for w in weights.values()))
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
