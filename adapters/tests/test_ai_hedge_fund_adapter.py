"""
adapters/tests/test_ai_hedge_fund_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/ai_hedge_fund_adapter.py.

Requires the `ai_hedge_fund_real` conda env and a real DEEPSEEK_API_KEY in
adapters/vendor/ai-hedge-fund/.env (see adapter header for setup). Makes
exactly one real LLM call (portfolio_manager) via run_hedge_fund().

Run with:
    conda run -n ai_hedge_fund_real python -m unittest adapters.tests.test_ai_hedge_fund_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.ai_hedge_fund_adapter import AiHedgeFundAdapter


class TestAiHedgeFundAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = AiHedgeFundAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "ai_hedge_fund")
        self.assertEqual(self.adapter.questions_answered, ["Q1"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_ai_hedge_fund", context=self.context)
        self.assertIsNotNone(result.q1)
        self.assertEqual(result.q1.context, self.context)
        self.assertIn(result.q1.action, ("BUY", "SELL", "HOLD"))
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("decisions", result.native_output)
        self.assertIn("AAPL", result.native_output["decisions"])
        # quantity must be present in the faithfully-preserved native output
        # even though it was discarded by the pre-migration adapter.
        self.assertIn("quantity", result.native_output["decisions"]["AAPL"])


if __name__ == "__main__":
    unittest.main()
