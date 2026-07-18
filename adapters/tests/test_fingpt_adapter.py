"""
adapters/tests/test_fingpt_adapter.py — minimal v2-schema construction +
real-run smoke test for adapters/fingpt_adapter.py.

Requires the `fingpt_real` conda env and the FinGPT v3.1 (ChatGLM2-6B base +
LoRA) weights cached locally (see adapter header for setup/download). No LLM
API key needed — this is a local HF model, GPU inference only. Makes one
real forward pass per fetched headline (typically <=5).

Run with:
    conda run -n fingpt_real python -m unittest adapters.tests.test_fingpt_adapter -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from unittest import mock

from CONTRACT.schemas import ConfidenceKind, OutputScope, QueryContext
from adapters import fingpt_adapter
from adapters.fingpt_adapter import FinGPTAdapter


class TestFinGPTAdapterV2(unittest.TestCase):
    def setUp(self):
        self.adapter = FinGPTAdapter()
        self.context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

    def test_metadata(self):
        self.assertEqual(self.adapter.name, "fingpt")
        self.assertEqual(self.adapter.questions_answered, ["Q2"])

    def test_smoke_test_real_run(self):
        checks = self.adapter.smoke_test()
        for label, ok in checks.items():
            self.assertTrue(ok, f"smoke_test check failed: {label}")

    def test_run_produces_valid_envelope(self):
        result = self.adapter.run(task_id="unit_test_fingpt", context=self.context)
        self.assertIsNotNone(result.q2)
        self.assertEqual(result.q2.context, self.context)
        dims = {s.dimension for s in result.q2.states}
        self.assertIn("sentiment", dims)
        self.assertIsInstance(result.native_output, dict)
        self.assertIn("scored", result.native_output)

    def test_no_headlines_path_is_honest_not_fabricated(self):
        # Force the no-headlines branch (no real network call, no GPU call)
        # and check it reports an honest zero-confidence heuristic state
        # instead of running the model on a fabricated placeholder headline.
        with mock.patch.object(fingpt_adapter, "_fetch_headlines", return_value=[]), \
             mock.patch.object(fingpt_adapter, "_score_text") as mock_score:
            adapter = FinGPTAdapter()
            q2 = adapter.q2_state(self.context)
            mock_score.assert_not_called()
            self.assertEqual(len(q2.states), 1)
            state = q2.states[0]
            self.assertEqual(state.dimension, "sentiment")
            self.assertEqual(state.value_numeric, 0.0)
            self.assertIsNotNone(state.confidence)
            self.assertEqual(state.confidence.value, 0.0)
            self.assertEqual(state.confidence.kind, ConfidenceKind.HEURISTIC)
            self.assertIn("no", q2.explanation.lower())


if __name__ == "__main__":
    unittest.main()
