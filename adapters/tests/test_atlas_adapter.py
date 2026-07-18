"""
adapters/tests/test_atlas_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/atlas_adapter.py.

Requires the `atlas_real` conda env (deap, pandas, numpy, torch — see
adapters/atlas_adapter.py header for setup). No LLM API key needed (pure
DEAP genetic-programming search over the repo's own bundled crypto panel).

Run with:
    conda run -n atlas_real python -m unittest adapters.tests.test_atlas_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import OutputScope, QueryContext
from adapters.atlas_adapter import AtlasAdapter, FALLBACK_TOKEN


class TestAtlasAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = AtlasAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION,
            targets=[FALLBACK_TOKEN],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "atlas")
        self.assertEqual(self.adapter.questions_answered, ["Q3"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_atlas", context=self.context)
        self.assertIsNotNone(result.q3)
        self.assertEqual(result.q3.context, self.context)
        self.assertGreater(len(result.q3.values), 0)
        self.assertTrue(result.q3.factor_expression)
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("upstream", result.native_output)


if __name__ == "__main__":
    unittest.main()
