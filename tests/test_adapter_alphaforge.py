"""
tests/test_adapter_alphaforge.py — schema/serialization contract test +
fixture mapping test for adapters/alphaforge_adapter.py.

No network calls, no real GP search / AlphaPool call: the fixture-mapping
test exercises the adapter's own pure `_rank_direction_strength()` mapping
function directly against tests/fixtures/alphaforge_fixture.json (shaped
like a real combined_score_last_row + pool state dict). Matches this
repo's existing test convention (see CONTRACT/test_harness.py) — stdlib
unittest only.

Usage:
    python -m unittest tests.test_adapter_alphaforge -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    ConfidenceEstimate,
    ConfidenceKind,
    Direction,
    EvidenceItem,
    OutputScope,
    Q3Signal,
    QueryContext,
)
from adapters.alphaforge_adapter import _rank_direction_strength, _resolve_universe

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "alphaforge_fixture.json"


def _load_fixture() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


class TestAlphaForgeSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_q3signal_constructs_and_round_trips(self):
        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION, targets=["AAPL"], universe=["AAPL", "MSFT"],
        )
        sig = Q3Signal(
            context=context,
            signal_semantics="factor_value",
            values={"AAPL": 0.84, "MSFT": 0.21},
            direction=Direction.LONG,
            strength=0.9,
            factor_expression="ts_ema(volume,20)",
            confidence=ConfidenceEstimate(value=0.6, kind=ConfidenceKind.MODEL_MARGIN, raw_value=0.2),
            evidence=[EvidenceItem(kind="factor_expression", value="ts_ema(volume,20) (combination_weight=0.05)")],
        )
        dumped = sig.model_dump()
        restored = Q3Signal.model_validate(dumped)
        self.assertEqual(restored.values["AAPL"], 0.84)
        self.assertEqual(restored.direction, "LONG")

    def test_q4_not_claimed_anywhere_in_module(self):
        # AlphaForge's real combination weights are alpha-factor weights,
        # not portfolio weights — this adapter must never claim Q4.
        # BaseAdapter.run() only calls q4_policy() when "Q4" is listed in
        # questions_answered (CONTRACT/base_adapter.py), and this adapter
        # never imports/constructs Q4Policy anywhere in its own module
        # source (a stub q4_policy() is always inherited from BaseAdapter,
        # so its mere presence isn't itself meaningful).
        import adapters.alphaforge_adapter as mod
        import inspect
        self.assertNotIn("Q4", mod.AlphaForgeAdapter.questions_answered)
        self.assertNotIn("Q4Policy", dir(mod))
        source = inspect.getsource(mod)
        self.assertNotIn("Q4Policy", source)
        self.assertNotIn("def q4_policy", source)

    def test_values_dict_requires_nonempty(self):
        context = QueryContext(as_of="2024-01-15", data_cutoff="2024-01-15", scope=OutputScope.CROSS_SECTION)
        with self.assertRaises(Exception):
            Q3Signal(context=context, signal_semantics="factor_value", values={})


class TestAlphaForgeFixtureMapping(unittest.TestCase):
    """Exercises the adapter's own pure mapping logic against a hand-authored
    realistic fixture — no network, no GP search, no torch model call."""

    def setUp(self):
        self.fixture = _load_fixture()
        self.values = self.fixture["combined_score_last_row"]

    def test_top_ranked_ticker_is_long(self):
        # AAPL has the highest real combined score in the fixture (0.842)
        # -> should rank 1/8 -> top percentile -> LONG.
        direction, strength, rank_position, pct = _rank_direction_strength("AAPL", self.values)
        self.assertEqual(direction, Direction.LONG)
        self.assertEqual(rank_position, 1)
        self.assertAlmostEqual(pct, 1.0)
        self.assertGreater(strength, 0.9)

    def test_bottom_ranked_ticker_is_short(self):
        # META has the lowest real combined score (-0.612) -> rank 8/8 -> SHORT.
        direction, strength, rank_position, pct = _rank_direction_strength("META", self.values)
        self.assertEqual(direction, Direction.SHORT)
        self.assertEqual(rank_position, 8)
        self.assertAlmostEqual(pct, 0.0)

    def test_middle_ranked_ticker_is_neutral(self):
        # JPM (0.088) sits mid-pack (rank 3/8, pct ~0.714) -> NEUTRAL under
        # the default TOP_PCT=0.2 threshold.
        direction, _, rank_position, pct = _rank_direction_strength("JPM", self.values)
        self.assertEqual(direction, Direction.NEUTRAL)
        self.assertEqual(rank_position, 3)

    def test_strength_always_in_unit_range(self):
        for ticker in self.values:
            _, strength, _, _ = _rank_direction_strength(ticker, self.values)
            self.assertGreaterEqual(strength, 0.0)
            self.assertLessEqual(strength, 1.0)

    def test_fixture_pool_weights_sum_is_small_not_portfolio_scale(self):
        # Sanity check on the fixture itself: real AlphaPool combination
        # weights are factor-combination weights (small, L1-penalized), NOT
        # portfolio weights that must sum to ~1 — confirms the fixture
        # matches real AlphaPool._optimize() output shape, not a portfolio
        # weight vector.
        total = sum(self.fixture["pool_weights"])
        self.assertLess(total, 1.0)

    def test_resolve_universe_includes_requested_ticker_first(self):
        universe, _ = _resolve_universe("nvda")
        self.assertEqual(universe[0], "NVDA")
        self.assertEqual(len(universe), 8)


if __name__ == "__main__":
    unittest.main()
