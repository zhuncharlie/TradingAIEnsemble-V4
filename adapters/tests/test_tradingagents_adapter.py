"""
adapters/tests/test_tradingagents_adapter.py — minimal v2-schema construction
+ real-run smoke test for adapters/tradingagents_adapter.py.

Requires the `tradingagents_real` conda env and a real DEEPSEEK_API_KEY in
adapters/vendor/ai-hedge-fund/.env (shared with the ai_hedge_fund adapter —
see adapter header). Makes ~9-10 real LLM calls per graph run (the full
analyst -> bull/bear debate -> risk debate -> portfolio manager pipeline);
Q1 and Q2 share one cached run so this test file only triggers it once.

Run with:
    conda run -n tradingagents_real python -m unittest adapters.tests.test_tradingagents_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.tradingagents_adapter import TradingAgentsAdapter


class TestTradingAgentsAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = TradingAgentsAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "tradingagents")
        self.assertEqual(self.adapter.questions_answered, ["Q1", "Q2"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_tradingagents", context=self.context)
        self.assertIsNotNone(result.q1)
        self.assertIsNotNone(result.q2)
        self.assertEqual(result.q1.context, self.context)
        self.assertEqual(result.q2.context, self.context)
        self.assertIn(result.q1.action, ("BUY", "SELL", "HOLD"))
        dims = {s.dimension for s in result.q2.states}
        self.assertIn("sentiment", dims)
        # risk_level must NOT reappear under any dimension name -- deleted
        # per migration rubric, not replaced by anything.
        self.assertNotIn("risk_level", dims)
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("sentiment_report", result.native_output)
        self.assertIn("final_trade_decision", result.native_output)


if __name__ == "__main__":
    unittest.main()
