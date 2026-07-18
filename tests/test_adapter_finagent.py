"""
tests/test_adapter_finagent.py — schema/serialization contract test + fixture
mapping test for adapters/finagent_adapter.py.

No network calls, no upstream imports: the fixture-mapping tests exercise
adapters.finagent_adapter._weights_from_info() (the pure cash/position/
price/value -> target_weights derivation) and the BUY/SELL/HOLD -> Action
mapping directly, against a hand-authored fixture matching the real
EnvironmentTrading.step() info-dict shape (see
tests/fixtures/finagent_fixture.json). Matches this repo's existing test
convention (see CONTRACT/test_harness.py, tests/test_adapter_finbert.py) —
stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_finagent -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    Action,
    OutputScope,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    TimeWindow,
)
from adapters.finagent_adapter import _ACTION_TO_ENV, _ACTION_TO_SCHEMA, _weights_from_info

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "finagent_fixture.json"


class TestFinAgentSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_causal_ordering_round_trips(self):
        step1 = PolicyDecisionStep(
            timestamp="2024-01-03", information_cutoff="2024-01-02",
            target_weights={"AAPL": 0.8, "CASH": 0.2},
        )
        step2 = PolicyDecisionStep(
            timestamp="2024-01-04", information_cutoff="2024-01-03",
            target_weights={"AAPL": 0.0, "CASH": 1.0},
        )
        dumped = [step1.model_dump(), step2.model_dump()]
        restored = [PolicyDecisionStep.model_validate(d) for d in dumped]
        self.assertLessEqual(restored[0].information_cutoff, restored[0].timestamp)
        self.assertLessEqual(restored[1].information_cutoff, restored[1].timestamp)
        self.assertLess(restored[0].timestamp, restored[1].timestamp)

    def test_q4_policy_long_only_constraint_rejects_negative_weight(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.ASSET, targets=["AAPL"])
        with self.assertRaises(Exception):
            Q4Policy(
                context=context,
                policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
                generation_window=TimeWindow(start="2024-01-01", end="2024-01-15"),
                constraints=PortfolioConstraints(long_only=True),
                initial_weights={"AAPL": -0.1, "CASH": 1.1},
            )


class TestFinAgentFixtureMapping(unittest.TestCase):
    """Adapter mapping logic, driven by a real-shaped fixture — no live calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_weights_from_flat_info(self):
        info = self.fixture["flat_step"]
        weights = _weights_from_info(info, "AAPL")
        self.assertAlmostEqual(weights["AAPL"], 0.0)
        self.assertAlmostEqual(weights["CASH"], 1.0)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)

    def test_weights_from_post_buy_info(self):
        info = self.fixture["post_buy_step"]
        weights = _weights_from_info(info, "AAPL")
        expected_position_weight = (info["position"] * info["price"]) / info["value"]
        expected_cash_weight = info["cash"] / info["value"]
        self.assertAlmostEqual(weights["AAPL"], expected_position_weight, places=6)
        self.assertAlmostEqual(weights["CASH"], expected_cash_weight, places=6)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        # long-only: both components must be non-negative (real environment
        # never allows shorting/leverage — see module docstring)
        self.assertGreaterEqual(weights["AAPL"], 0.0)
        self.assertGreaterEqual(weights["CASH"], 0.0)

    def test_weights_satisfy_portfolio_constraints_schema_check(self):
        info = self.fixture["post_buy_step"]
        weights = _weights_from_info(info, "AAPL")
        # constructing a Q4Policy with these weights under long_only=True
        # must not raise (proves the derived weights are schema-valid)
        context = QueryContext(as_of=info["date"], data_cutoff=info["date"], scope=OutputScope.ASSET, targets=["AAPL"])
        q4 = Q4Policy(
            context=context,
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=TimeWindow(start="2024-01-01", end="2024-01-15"),
            constraints=PortfolioConstraints(long_only=True, cash_allowed=True),
            initial_weights=weights,
        )
        self.assertEqual(q4.initial_weights["AAPL"], weights["AAPL"])

    def test_action_string_maps_to_schema_action(self):
        raw = self.fixture["raw_decision_response"]
        action_str = raw["action"].strip().upper()
        self.assertIn(action_str, _ACTION_TO_SCHEMA)
        self.assertEqual(_ACTION_TO_SCHEMA[action_str], Action.HOLD)
        self.assertEqual(_ACTION_TO_ENV[action_str], 0)

    def test_all_three_action_strings_map_cleanly(self):
        for s, expected_schema, expected_env in (
            ("BUY", Action.BUY, 1), ("SELL", Action.SELL, -1), ("HOLD", Action.HOLD, 0),
        ):
            self.assertEqual(_ACTION_TO_SCHEMA[s], expected_schema)
            self.assertEqual(_ACTION_TO_ENV[s], expected_env)


if __name__ == "__main__":
    unittest.main()
