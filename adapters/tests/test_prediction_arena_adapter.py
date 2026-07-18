"""
adapters/tests/test_prediction_arena_adapter.py — minimal v2-schema
construction + real-run smoke test for adapters/prediction_arena_adapter.py.

Requires the `prediction_arena_real` conda env (forecasting-tools vendor
checkout, litellm, requests — see adapters/prediction_arena_adapter.py header
for setup) plus a working `DEEPSEEK_API_KEY` in
adapters/vendor/ai-hedge-fund/.env (reused, not a new key) and live network
access to the public, keyless Kalshi API.

Run with:
    conda run -n prediction_arena_real python -m unittest adapters.tests.test_prediction_arena_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.prediction_arena_adapter import PredictionArenaAdapter


class TestPredictionArenaAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = PredictionArenaAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
            universe=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "prediction_arena")
        self.assertEqual(self.adapter.questions_answered, ["Q2"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_prediction_arena", context=self.context)
        self.assertIsNotNone(result.q2)
        self.assertEqual(result.q2.context, self.context)
        self.assertGreaterEqual(len(result.q2.states), 1)

        forecast_state = next(
            (s for s in result.q2.states if s.dimension == "forecast_probability"), None
        )
        self.assertIsNotNone(forecast_state)
        self.assertIsNotNone(forecast_state.value_numeric)
        self.assertTrue(0.0 <= forecast_state.value_numeric <= 1.0)
        self.assertIsNotNone(forecast_state.value_distribution)
        self.assertAlmostEqual(
            sum(forecast_state.value_distribution.values()), 1.0, places=6
        )
        self.assertIsNotNone(forecast_state.confidence)
        self.assertTrue(forecast_state.evidence)

        divergence_state = next(
            (s for s in result.q2.states if s.dimension == "forecast_market_divergence"), None
        )
        self.assertIsNotNone(divergence_state)
        self.assertIn(divergence_state.value_category, ("LOW", "MEDIUM", "HIGH", "EXTREME"))

        self.assertIsNone(result.q1)
        self.assertIsNone(result.q3)
        self.assertIsNone(result.q4)


if __name__ == "__main__":
    unittest.main()
