"""
adapters/tests/test_qlib_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/qlib_adapter.py.

Requires the `qlib_real` conda env (pyqlib, lightgbm, yfinance — see
adapters/qlib_adapter.py header for setup). No LLM API key needed (pure
Alpha158 + LightGBM, CPU only).

Run with:
    conda run -n qlib_real python -m unittest adapters.tests.test_qlib_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.qlib_adapter import QlibAdapter


class TestQlibAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = QlibAdapter()
        # Same ticker/date as QlibAdapter.smoke_test()'s own hardcoded call —
        # qlib's own `qlib.init()` can only be called once per process
        # (upstream raises RecorderInitializationError on a second init with
        # a different provider_uri), so this test suite keeps every real
        # pipeline call in one process on the same (universe, date) cache
        # key deliberately, matching the pattern this session's other
        # migrated Q3 adapters' test files already use (e.g. atlas).
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
            universe=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "qlib")
        self.assertEqual(self.adapter.questions_answered, ["Q3"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_qlib", context=self.context)
        self.assertIsNotNone(result.q3)
        self.assertEqual(result.q3.context, self.context)
        self.assertGreater(len(result.q3.values), 0)
        self.assertEqual(result.q3.signal_semantics, "predicted_return")
        self.assertTrue(result.q3.factor_expression)
        self.assertIn(result.q3.direction, ("LONG", "SHORT", "NEUTRAL"))
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("upstream", result.native_output)
        self.assertIn("predicted_scores", result.native_output["upstream"])


if __name__ == "__main__":
    unittest.main()
