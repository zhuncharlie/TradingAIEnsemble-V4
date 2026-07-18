"""
adapters/tests/test_rdagent_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/rdagent_adapter.py.

Requires the `rdagent_real` conda env (rdagent, litellm, yfinance, etc. —
see adapters/rdagent_adapter.py header for setup) AND a real DEEPSEEK_API_KEY
(read from adapters/vendor/ai-hedge-fund/.env by the adapter module itself).
This makes real, bounded (~5-8 call) DeepSeek API calls — a real dollar cost,
not free like alphagen/atlas.

Run with:
    conda run -n rdagent_real python -m unittest adapters.tests.test_rdagent_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.rdagent_adapter import RDAgentAdapter


class TestRDAgentAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = RDAgentAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "rdagent")
        self.assertEqual(self.adapter.questions_answered, ["Q3"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope_or_honest_none(self):
        result = self.adapter.run(task_id="unit_test_rdagent", context=self.context)
        # q3 may legitimately be None if the real bounded CoSTEER loop never
        # converges on an accepted implementation (a genuine, disclosed
        # outcome — see adapter header "v1 -> v2.0.0 schema migration notes").
        if result.q3 is not None:
            self.assertEqual(result.q3.context, self.context)
            self.assertGreater(len(result.q3.values), 0)
            self.assertTrue(result.q3.factor_expression)
        self.assertIsInstance(result.native_output, dict)


if __name__ == "__main__":
    unittest.main()
