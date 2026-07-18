"""
tests/test_adapter_pgportfolio.py — schema/serialization contract test +
fixture mapping test for adapters/pgportfolio_adapter.py.

No network calls, no TensorFlow/tflearn import, no real training: the
fixture-mapping test constructs a Q4Policy directly from a hand-authored,
realistic terminal-weights fixture (tests/fixtures/pgportfolio_fixture.json)
shaped like a real pgportfolio.learn.nnagent.NNAgent.decide_by_history()
output, so this file can run in any environment (it does not require the
pgportfolio_real conda env's TF1/tflearn stack). Matches this repo's
existing test convention (see CONTRACT/test_harness.py) — stdlib unittest
only.

Usage:
    python -m unittest tests.test_adapter_pgportfolio -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    OutputScope,
    PolicyArtifact,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    TimeWindow,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "pgportfolio_fixture.json"


class TestPGPortfolioSchemaContract(unittest.TestCase):
    """Pure schema/serialization checks — no adapter code, no TF/tflearn import."""

    def test_frozen_learned_policy_with_weights_round_trips(self):
        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO, targets=["BTC-USD"], universe=["BTC-USD", "ETH-USD"],
        )
        window = TimeWindow(start="2023-10-01", end="2024-01-15")
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=window,
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
            initial_weights={"CASH": 0.1, "BTC-USD": 0.5, "ETH-USD": 0.4},
            artifact=PolicyArtifact(artifact_type="model_checkpoint", description="test"),
        )
        dumped = policy.model_dump()
        reparsed = Q4Policy(**dumped)
        self.assertEqual(reparsed.policy_type, "FROZEN_LEARNED_POLICY")
        self.assertAlmostEqual(sum(reparsed.initial_weights.values()), 1.0)

    def test_long_only_constraint_rejects_negative_weight(self):
        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO, universe=["BTC-USD"],
        )
        window = TimeWindow(start="2023-10-01", end="2024-01-15")
        with self.assertRaises(Exception):
            Q4Policy(
                context=context,
                policy_type=PolicyType.FROZEN_LEARNED_POLICY,
                generation_window=window,
                constraints=PortfolioConstraints(long_only=True),
                initial_weights={"CASH": 1.2, "BTC-USD": -0.2},
            )

    def test_decisions_none_is_not_masqueraded_as_trajectory(self):
        """A single frozen-query result must not populate `decisions`."""
        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO, universe=["BTC-USD"],
        )
        window = TimeWindow(start="2023-10-01", end="2024-01-15")
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=window,
            initial_weights={"CASH": 1.0},
        )
        self.assertIsNone(policy.decisions)


class TestPGPortfolioFixtureMapping(unittest.TestCase):
    """Fixture-driven mapping test — mirrors what q4_policy() does with a
    real decide_by_history()-shaped result, without importing TF/tflearn."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE_PATH) as f:
            cls.fixture = json.load(f)

    def test_fixture_weights_are_nonnegative_and_sum_to_1(self):
        weights = self.fixture["terminal_weights"]
        self.assertTrue(all(v >= 0 for v in weights.values()))
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=3)

    def test_fixture_maps_to_valid_q4policy(self):
        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO,
            universe=self.fixture["tickers"],
        )
        window = TimeWindow(
            start=self.fixture["generation_window"]["start"],
            end=self.fixture["generation_window"]["end"],
        )
        policy = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=window,
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
            initial_weights=self.fixture["terminal_weights"],
            artifact=PolicyArtifact(artifact_type="model_checkpoint", description="fixture"),
        )
        self.assertEqual(policy.context, context)
        self.assertEqual(policy.generation_window, window)


class TestPGPortfolioMetadata(unittest.TestCase):
    def test_metadata_fields_set_without_importing_tf(self):
        """
        Import-only smoke check: adapters/pgportfolio_adapter.py itself must
        import cleanly without a TF1/tflearn env (those imports are deferred
        inside functions, not at module level) so this offline test suite
        can run in any environment.
        """
        from adapters.pgportfolio_adapter import PGPortfolioAdapter

        a = PGPortfolioAdapter()
        self.assertEqual(a.name, "pgportfolio")
        self.assertEqual(a.questions_answered, ["Q4"])
        self.assertEqual(a.upstream_repo, "https://github.com/ZhengyaoJiang/PGPortfolio")


if __name__ == "__main__":
    unittest.main()
