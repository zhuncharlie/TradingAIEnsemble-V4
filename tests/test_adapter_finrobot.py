"""
tests/test_adapter_finrobot.py — schema/serialization contract test +
fixture mapping test for adapters/finrobot_adapter.py.

No network calls, no LLM calls: the fixture-mapping test seeds
FinRobotAdapter._cache directly with a realistic, already-processed
_run_market_analyst() output shape (tests/fixtures/finrobot_fixture.json)
so q1_action()/q2_state()'s real mapping code runs against realistic
values without invoking autogen/DeepSeek. Matches this repo's existing
test convention (see CONTRACT/test_harness.py, tests/test_adapter_finbert.py)
— stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_finrobot -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, Q1Action, Q2State, QueryContext, StateEstimate
from adapters.finrobot_adapter import FinRobotAdapter

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "finrobot_fixture.json"


class TestFinRobotSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_state_estimate_with_value_text_round_trips(self):
        state = StateEstimate(dimension="market_outlook", value_text="Bullish on AAPL given strong fundamentals.")
        dumped = state.model_dump()
        restored = StateEstimate.model_validate(dumped)
        self.assertEqual(restored.dimension, "market_outlook")
        self.assertIn("Bullish", restored.value_text)

    def test_q1action_action_semantics_discloses_derived_status(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.ASSET, targets=["AAPL"])
        q1 = Q1Action(context=context, action="BUY", action_semantics="DERIVED via keyword extraction")
        restored = Q1Action.model_validate(q1.model_dump())
        self.assertIn("DERIVED", restored.action_semantics)


class TestFinRobotFixtureMapping(unittest.TestCase):
    """Adapter mapping logic, driven by a realistic captured fixture — no live calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def _make_context(self, ticker=None, as_of=None):
        return QueryContext(
            as_of=as_of or self.fixture["as_of"],
            data_cutoff=as_of or self.fixture["as_of"],
            scope=OutputScope.ASSET,
            targets=[ticker or self.fixture["ticker"]],
        )

    def _seed(self, adapter, fixture=None):
        fixture = fixture or self.fixture
        key = (fixture["ticker"], fixture["as_of"])
        adapter._cache[key] = fixture

    def test_q2_state_captures_real_reply_verbatim(self):
        adapter = FinRobotAdapter()
        self._seed(adapter)
        context = self._make_context()

        result = adapter.q2_state(context)
        self.assertIsInstance(result, Q2State)
        self.assertEqual(len(result.states), 1)
        state = result.states[0]
        self.assertEqual(state.dimension, "market_outlook")
        self.assertIn("bullish", state.value_text.lower())
        self.assertEqual(len(state.evidence), 1)
        self.assertEqual(state.evidence[0].kind, "llm_conversation")

    def test_q1_action_extracts_bullish_as_buy(self):
        adapter = FinRobotAdapter()
        self._seed(adapter)
        context = self._make_context()

        result = adapter.q1_action(context)
        self.assertIsInstance(result, Q1Action)
        self.assertEqual(result.action, "BUY")
        self.assertIn("DERIVED", result.action_semantics)
        self.assertIsNone(result.confidence)  # no honest numeric confidence from free-form prose

    def test_q1_action_extracts_bearish_as_sell(self):
        fixture = dict(self.fixture)
        fixture["ticker"] = "TSLA"
        fixture["full_reply"] = "Weak demand signals and margin compression suggest a bearish outlook for TSLA."
        adapter = FinRobotAdapter()
        self._seed(adapter, fixture)
        context = self._make_context(ticker="TSLA")

        result = adapter.q1_action(context)
        self.assertEqual(result.action, "SELL")

    def test_q1_action_extracts_neutral_as_hold(self):
        fixture = dict(self.fixture)
        fixture["ticker"] = "MSFT"
        fixture["full_reply"] = "Mixed signals overall; the outlook is neutral pending more data."
        adapter = FinRobotAdapter()
        self._seed(adapter, fixture)
        context = self._make_context(ticker="MSFT")

        result = adapter.q1_action(context)
        self.assertEqual(result.action, "HOLD")

    def test_q1_action_none_when_no_keyword_found_not_defaulted_to_hold(self):
        fixture = dict(self.fixture)
        fixture["ticker"] = "NVDA"
        fixture["full_reply"] = "The company reported quarterly earnings in line with expectations."
        adapter = FinRobotAdapter()
        self._seed(adapter, fixture)
        context = self._make_context(ticker="NVDA")

        result = adapter.q1_action(context)
        self.assertIsNone(result)  # must not fabricate a HOLD when no real keyword was found

    def test_q2_state_honest_when_no_reply_captured(self):
        fixture = {"ticker": "ZZZZ", "as_of": "2024-01-15", "full_reply": "", "messages": []}
        adapter = FinRobotAdapter()
        self._seed(adapter, fixture)
        context = self._make_context(ticker="ZZZZ")

        result = adapter.q2_state(context)
        self.assertEqual(result.states[0].value_category, "no_reply_captured")
        self.assertEqual(result.states[0].confidence.value, 0.0)


if __name__ == "__main__":
    unittest.main()
