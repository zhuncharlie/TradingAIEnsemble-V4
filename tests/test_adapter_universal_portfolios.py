"""
tests/test_adapter_universal_portfolios.py — schema/serialization contract
test + fixture mapping test for adapters/universal_portfolios_adapter.py.

No network calls, no real Algo.run() call: the fixture-mapping test builds a
synthetic pandas weights DataFrame (tests/fixtures/universal_portfolios_fixture.json,
shaped like a real AlgoResult.B) and exercises the adapter's own pure
`_build_decisions()` mapping function directly. Matches this repo's existing
test convention (see CONTRACT/test_harness.py) — stdlib unittest only.

Usage:
    python -m unittest tests.test_adapter_universal_portfolios -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from CONTRACT.schemas import (
    PolicyDecisionStep,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    OutputScope,
    TimeWindow,
    PolicyType,
)
from adapters.universal_portfolios_adapter import (
    ALGO_REGISTRY,
    _build_decisions,
    _load_algo_class,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "universal_portfolios_fixture.json"


def _load_fixture() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


class TestUniversalPortfoliosSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code involved."""

    def test_policy_decision_step_round_trips(self):
        step = PolicyDecisionStep(
            timestamp="2024-01-04",
            information_cutoff="2024-01-03",
            selected_universe=["AAPL", "MSFT", "NVDA"],
            target_weights={"AAPL": 0.5, "MSFT": 0.3, "NVDA": 0.2},
        )
        dumped = step.model_dump()
        reparsed = PolicyDecisionStep.model_validate(dumped)
        self.assertEqual(reparsed.timestamp, "2024-01-04")
        self.assertLessEqual(reparsed.information_cutoff, reparsed.timestamp)

    def test_q4_policy_online_adaptive_constructs(self):
        context = QueryContext(
            as_of="2024-01-08",
            data_cutoff="2024-01-08",
            scope=OutputScope.PORTFOLIO,
            universe=["AAPL", "MSFT", "NVDA"],
        )
        gw = TimeWindow(start="2024-01-02", end="2024-01-08")
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=gw,
            initial_weights={"AAPL": 0.34, "MSFT": 0.33, "NVDA": 0.33},
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
        )
        self.assertEqual(policy.policy_type, "ONLINE_ADAPTIVE_POLICY")
        self.assertEqual(policy.generation_window, gw)

    def test_negative_weight_rejected_by_long_only_semantics(self):
        # PortfolioConstraints doesn't itself validate weight signs (that's a
        # harness-level check), but a PolicyDecisionStep with a negative
        # weight should still construct (schema is permissive) — the
        # adapter's own smoke_test() is what asserts non-negativity for its
        # real output. This test just confirms the schema doesn't silently
        # coerce or reject in a way that would mask a real bug.
        step = PolicyDecisionStep(
            timestamp="2024-01-04",
            information_cutoff="2024-01-03",
            target_weights={"AAPL": -0.1, "MSFT": 1.1},
        )
        self.assertEqual(step.target_weights["AAPL"], -0.1)


class TestUniversalPortfoliosFixtureMapping(unittest.TestCase):
    """Fixture-driven mapping test — no network, no real Algo.run() call."""

    def setUp(self):
        self.fixture = _load_fixture()
        self.tickers = self.fixture["tickers"]
        self.B = pd.DataFrame(
            self.fixture["weights_rows"],
            index=pd.to_datetime(self.fixture["dates"]),
        )[self.tickers]
        self.min_history = self.fixture["min_history"]

    def test_build_decisions_drops_warmup_rows(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        # 5 real rows, min_history=2 -> rows [2,3,4] are post-warmup candidates,
        # row index 0 is skipped globally (no prior cutoff), so with
        # min_history=2 all of rows 2,3,4 qualify (i >= min_history and i != 0).
        self.assertEqual(len(decisions), 3)

    def test_build_decisions_causal_ordering(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        for d in decisions:
            self.assertLessEqual(d.information_cutoff, d.timestamp)
            self.assertNotEqual(d.information_cutoff, d.timestamp)
        timestamps = [d.timestamp for d in decisions]
        self.assertEqual(timestamps, sorted(timestamps))
        self.assertEqual(len(timestamps), len(set(timestamps)))

    def test_build_decisions_information_cutoff_is_prior_row_date(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        # First real decision (index 2, date 2024-01-04) must cite index 1's
        # date (2024-01-03) as its information_cutoff, not index 0's or its own.
        self.assertEqual(decisions[0].timestamp, "2024-01-04")
        self.assertEqual(decisions[0].information_cutoff, "2024-01-03")

    def test_build_decisions_weights_match_fixture_row(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        expected = self.fixture["weights_rows"][2]
        for ticker, expected_w in expected.items():
            self.assertAlmostEqual(decisions[0].target_weights[ticker], expected_w, places=6)

    def test_build_decisions_all_weights_sum_to_1(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        for d in decisions:
            self.assertAlmostEqual(sum(d.target_weights.values()), 1.0, places=6)

    def test_build_decisions_selected_universe_matches_tickers(self):
        decisions = _build_decisions(self.B, self.min_history, self.tickers)
        for d in decisions:
            self.assertEqual(d.selected_universe, self.tickers)

    def test_build_decisions_too_short_window_yields_empty(self):
        short_B = self.B.iloc[:1]
        decisions = _build_decisions(short_B, min_history=0, tickers=self.tickers)
        self.assertEqual(decisions, [])


class TestUniversalPortfoliosAlgoRegistry(unittest.TestCase):
    def test_hindsight_algorithms_not_registered(self):
        self.assertNotIn("bcrp", ALGO_REGISTRY)
        self.assertNotIn("best_markowitz", ALGO_REGISTRY)

    def test_unknown_algo_raises(self):
        with self.assertRaises(ValueError):
            _load_algo_class("bcrp")
        with self.assertRaises(ValueError):
            _load_algo_class("not_a_real_algo")


if __name__ == "__main__":
    unittest.main()
