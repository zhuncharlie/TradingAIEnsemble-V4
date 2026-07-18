"""
adapters/tests/test_alphagen_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/alphagen_adapter.py.

Requires the `alphagen_real` conda env (torch, stable_baselines3, sb3_contrib,
gymnasium, shimmy, yfinance — see adapters/alphagen_adapter.py header for
setup). No LLM API key needed (pure RL/GP search).

Run with:
    conda run -n alphagen_real python -m unittest adapters.tests.test_alphagen_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.base_adapter import AdapterContractViolation
from CONTRACT.schemas import OutputScope, QueryContext
from adapters.alphagen_adapter import AlphagenAdapter


class TestAlphagenAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = AlphagenAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION,
            targets=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "alphagen")
        self.assertEqual(self.adapter.questions_answered, ["Q3"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_alphagen", context=self.context)
        self.assertIsNotNone(result.q3)
        self.assertEqual(result.q3.context, self.context)
        self.assertGreater(len(result.q3.values), 0)
        self.assertTrue(result.q3.signal_semantics)
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("upstream", result.native_output)


if __name__ == "__main__":
    unittest.main()
