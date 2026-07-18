"""
tests/test_adapter_earnmore.py — schema/serialization contract test + fixture
mapping test for adapters/earnmore_adapter.py.

No network calls, no upstream imports, no real training: the fixture-mapping
tests exercise adapters.earnmore_adapter._weights_from_action_vector() and
._selected_universe_from_mask() (the pure real-info-vector -> schema-shape
derivations) directly, against a hand-authored fixture matching the real
EnvironmentPV.step() info["action"] vector shape and the real
aux_stocks[id]["mask"] shape (see tests/fixtures/earnmore_fixture.json).
Matches this repo's existing test convention (see CONTRACT/test_harness.py,
tests/test_adapter_finagent.py) — stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_earnmore -v
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
from adapters.earnmore_adapter import _selected_universe_from_mask, _weights_from_action_vector

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "earnmore_fixture.json"


class TestEarnMoreSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_with_selected_universe_round_trips(self):
        step = PolicyDecisionStep(
            timestamp="2009-01-22",
            information_cutoff="2009-01-21",
            selected_universe=["AAPL", "AMGN"],
            target_weights={"AAPL": 0.5, "AMGN": 0.3, "CASH": 0.2},
        )
        restored = PolicyDecisionStep.model_validate(step.model_dump())
        self.assertLessEqual(restored.information_cutoff, restored.timestamp)
        self.assertEqual(restored.selected_universe, ["AAPL", "AMGN"])
        self.assertAlmostEqual(sum(restored.target_weights.values()), 1.0, places=6)

    def test_q4_policy_frozen_learned_with_decisions_trajectory_constructs(self):
        context = QueryContext(as_of="2009-03-01", data_cutoff="2009-03-01", scope=OutputScope.PORTFOLIO)
        decisions = [
            PolicyDecisionStep(
                timestamp="2009-01-22", information_cutoff="2009-01-21",
                selected_universe=["AAPL", "AMGN"],
                target_weights={"AAPL": 0.5, "AMGN": 0.3, "CASH": 0.2},
            ),
            PolicyDecisionStep(
                timestamp="2009-01-23", information_cutoff="2009-01-22",
                selected_universe=["AAPL", "AMGN"],
                target_weights={"AAPL": 0.4, "AMGN": 0.4, "CASH": 0.2},
            ),
        ]
        q4 = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=TimeWindow(start="2008-09-01", end="2009-03-01"),
            update_policy=UpdatePolicy(mode=UpdateMode.NONE),
            constraints=PortfolioConstraints(long_only=True, cash_allowed=True),
            decisions=decisions,
        )
        self.assertEqual(len(q4.decisions), 2)
        self.assertLess(q4.decisions[0].timestamp, q4.decisions[1].timestamp)

    def test_q4_policy_long_only_rejects_negative_weight(self):
        context = QueryContext(as_of="2009-03-01", data_cutoff="2009-03-01", scope=OutputScope.PORTFOLIO)
        with self.assertRaises(Exception):
            Q4Policy(
                context=context,
                policy_type=PolicyType.FROZEN_LEARNED_POLICY,
                generation_window=TimeWindow(start="2008-09-01", end="2009-03-01"),
                constraints=PortfolioConstraints(long_only=True),
                initial_weights={"AAPL": -0.1, "CASH": 1.1},
            )


class TestEarnMoreFixtureMapping(unittest.TestCase):
    """Adapter mapping logic, driven by a real-shaped fixture — no live calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_weights_from_action_vector_maps_cash_and_stocks_by_index(self):
        stocks = self.fixture["stocks"]
        vec = self.fixture["action_vector_step0"]
        weights = _weights_from_action_vector(vec, stocks)
        self.assertAlmostEqual(weights["CASH"], vec[0])
        for j, tic in enumerate(stocks):
            self.assertAlmostEqual(weights[tic], vec[j + 1])
        self.assertEqual(set(weights.keys()), {"CASH", *stocks})

    def test_weights_from_action_vector_sums_to_one_on_a_normalized_vector(self):
        stocks = ["A", "B", "C"]
        vec = [0.2, 0.3, 0.3, 0.2]  # cash + 3 stocks, real softmax-style, sums to 1
        weights = _weights_from_action_vector(vec, stocks)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)

    def test_selected_universe_from_mask_excludes_masked_tickers(self):
        stocks = self.fixture["stocks"]
        mask = self.fixture["mask_group1_technology"]
        selected = _selected_universe_from_mask(mask, stocks)
        self.assertEqual(selected, ["AAPL", "AMGN"])
        for excluded in ("AXP", "BA", "CAT"):
            self.assertNotIn(excluded, selected)

    def test_trajectory_pair_is_causally_ordered_and_schema_valid(self):
        step0 = PolicyDecisionStep.model_validate(self.fixture["trajectory_pair"]["step0"])
        step1 = PolicyDecisionStep.model_validate(self.fixture["trajectory_pair"]["step1"])
        self.assertLessEqual(step0.information_cutoff, step0.timestamp)
        self.assertLessEqual(step1.information_cutoff, step1.timestamp)
        self.assertLess(step0.timestamp, step1.timestamp)
        # step1's information_cutoff must not be later than step0's timestamp
        # (no future-information leakage between consecutive real steps)
        self.assertLessEqual(step1.information_cutoff, step0.timestamp)
        self.assertAlmostEqual(sum(step0.target_weights.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
