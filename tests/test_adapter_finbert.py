"""
tests/test_adapter_finbert.py — schema/serialization contract test + fixture
mapping test for adapters/finbert_adapter.py.

No network calls, no model load: the fixture-mapping test seeds
FinBERTAdapter._cache directly with a real, previously-captured
finbert.finbert.predict() output (tests/fixtures/finbert_fixture.json) so
q2_state()'s real mapping code runs against real values without invoking
yfinance or loading ProsusAI/finbert. Matches this repo's existing test
convention (see CONTRACT/test_harness.py) — stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_finbert -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, Q2State, QueryContext, StateEstimate
from adapters.finbert_adapter import FinBERTAdapter

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "finbert_fixture.json"


class TestFinBERTSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_state_estimate_with_distribution_round_trips(self):
        state = StateEstimate(
            dimension="sentiment",
            value_numeric=0.0123,
            value_distribution={"positive": 0.4, "negative": 0.35, "neutral": 0.25},
            scale="[-1,1]",
        )
        dumped = state.model_dump()
        restored = StateEstimate.model_validate(dumped)
        self.assertEqual(restored.dimension, "sentiment")
        self.assertAlmostEqual(restored.value_numeric, 0.0123)
        self.assertAlmostEqual(sum(restored.value_distribution.values()), 1.0, places=6)

    def test_q2_state_requires_context(self):
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        q2 = Q2State(context=context, states=[StateEstimate(dimension="sentiment", value_numeric=0.5)])
        self.assertEqual(q2.context.targets, ["AAPL"])
        # round-trip
        restored = Q2State.model_validate(q2.model_dump())
        self.assertEqual(restored.states[0].dimension, "sentiment")


class TestFinBERTFixtureMapping(unittest.TestCase):
    """Adapter mapping logic, driven by a real (previously captured) fixture — no live calls."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def _make_context(self):
        return QueryContext(
            as_of=self.fixture["date"],
            data_cutoff=self.fixture["date"],
            scope=OutputScope.ASSET,
            targets=[self.fixture["ticker"]],
        )

    def test_mapping_produces_correct_q2_state(self):
        adapter = FinBERTAdapter()
        key = (self.fixture["ticker"], self.fixture["date"])
        adapter._cache[key] = self.fixture  # seed cache -> _run() skips real yfinance/model calls

        context = self._make_context()
        result = adapter.q2_state(context)

        self.assertIsInstance(result, Q2State)
        self.assertEqual(len(result.states), 1)
        sentiment = result.states[0]
        self.assertEqual(sentiment.dimension, "sentiment")

        # real fixture values: sentiment_score 0.9284 and -0.9036 -> mean ~0.0124
        expected_mean = (0.9283559918403625 + -0.9036055207252502) / 2
        self.assertAlmostEqual(sentiment.value_numeric, expected_mean, places=6)

        self.assertIsNotNone(sentiment.value_distribution)
        self.assertAlmostEqual(
            sum(sentiment.value_distribution.values()), 1.0, delta=0.05
        )

        # evidence must cover both real fixture headlines, none dropped
        self.assertEqual(len(sentiment.evidence), 2)

        self.assertIsNotNone(sentiment.confidence)
        self.assertGreaterEqual(sentiment.confidence.value, 0.0)
        self.assertLessEqual(sentiment.confidence.value, 1.0)

    def test_no_headlines_path_is_honest_not_fabricated(self):
        adapter = FinBERTAdapter()
        key = ("ZZZZ", "2024-01-15")
        adapter._cache[key] = {"ticker": "ZZZZ", "date": "2024-01-15", "headlines": [], "scored": []}

        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["ZZZZ"],
        )
        result = adapter.q2_state(context)
        self.assertEqual(result.states[0].value_numeric, 0.0)
        self.assertEqual(result.states[0].confidence.value, 0.0)
        self.assertIn("No recent", result.explanation)


if __name__ == "__main__":
    unittest.main()
