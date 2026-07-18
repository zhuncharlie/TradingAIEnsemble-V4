"""
tests/test_adapter_finmem.py — schema/serialization contract test + fixture
mapping test for adapters/finmem_adapter.py.

No network calls, no LLM calls, no puppy.* (FinMem vendor) imports needed —
finmem_adapter.py's heavy upstream imports are all local to methods that
this file does not call. Matches CONTRACT/test_harness.py's stdlib-unittest
convention.

Usage:
    python tests/test_adapter_finmem.py
    python -m unittest tests.test_adapter_finmem -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import Action, OutputScope, Q1Action, QueryContext
from adapters.finmem_adapter import FinMemAdapter, _map_reflection_to_action

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "finmem_fixture.json"


class TestFinMemMetadata(unittest.TestCase):
    def test_metadata_fields_set(self):
        adapter = FinMemAdapter()
        self.assertEqual(adapter.name, "finmem")
        self.assertEqual(adapter.questions_answered, ["Q1"])
        self.assertEqual(
            adapter.upstream_repo,
            "https://github.com/pipiku915/FinMem-LLM-StockTrading",
        )
        self.assertEqual(adapter.requires_env, "finmem_real")


class TestFinMemFixtureMapping(unittest.TestCase):
    """Stage 3: fixture mapping test — real upstream output SHAPE (not a
    real upstream call) mapped through the adapter's pure mapping logic."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixtures = json.load(f)

    def test_buy_maps_to_BUY(self):
        self.assertEqual(_map_reflection_to_action(self.fixtures["buy_example"]), Action.BUY)

    def test_sell_maps_to_SELL(self):
        self.assertEqual(_map_reflection_to_action(self.fixtures["sell_example"]), Action.SELL)

    def test_hold_maps_to_HOLD(self):
        self.assertEqual(_map_reflection_to_action(self.fixtures["hold_example"]), Action.HOLD)

    def test_unexpected_value_falls_back_to_hold_not_crash(self):
        # Real-world robustness: an LLM-produced string outside {buy,sell,hold}
        # must not crash the adapter or silently fabricate a directional action.
        self.assertEqual(
            _map_reflection_to_action(self.fixtures["unexpected_value_example"]), Action.HOLD
        )

    def test_q1action_constructs_from_fixture(self):
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        fixture = self.fixtures["buy_example"]
        result = Q1Action(
            context=context,
            action=_map_reflection_to_action(fixture),
            explanation=fixture.get("summary_reason"),
        )
        self.assertEqual(result.action, "BUY")
        self.assertEqual(result.explanation, fixture["summary_reason"])
        # Serialization round-trip (schema/serialization contract check).
        dumped = result.model_dump()
        restored = Q1Action.model_validate(dumped)
        self.assertEqual(restored.action, result.action)


if __name__ == "__main__":
    unittest.main()
