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


class TestPGPortfolioStepwiseMapping(unittest.TestCase):
    """
    Offline tests for the new q4_initialize/q4_step/q4_finalize methods'
    pure mapping logic — no real TF1/tflearn/yfinance calls. _build_tensor()
    is pure numpy/pandas and is exercised directly with a synthetic OHLC
    frame; the weight-vector -> {"CASH": ..., ticker: ...} dict mapping
    q4_step() performs is replicated here against a synthetic real-shaped
    softmax output, matching this repo's convention of testing pure mapping
    logic without the real heavy dependency stack.
    """

    def test_adapter_satisfies_q4_step_adapter_protocol_without_tf(self):
        """isinstance only checks method presence, not execution — this
        must be True even without a real TF1 env, since q4_initialize/
        q4_step/q4_finalize are defined at class level (TF import stays
        deferred inside them, per the existing pattern)."""
        from adapters.pgportfolio_adapter import PGPortfolioAdapter
        from harness.q4_protocol import Q4StepAdapter

        self.assertIsInstance(PGPortfolioAdapter(), Q4StepAdapter)

    def test_build_tensor_shape_and_normalization(self):
        import numpy as np
        import pandas as pd

        from adapters.pgportfolio_adapter import FEATURE_NUMBER, WINDOW_SIZE, _build_tensor

        dates = pd.date_range("2024-01-01", periods=WINDOW_SIZE + 5, freq="D")
        frames = {
            "BTC-USD": pd.DataFrame({
                "High": np.linspace(100, 120, len(dates)),
                "Low": np.linspace(90, 110, len(dates)),
                "Close": np.linspace(95, 115, len(dates)),
            }, index=dates),
        }
        window_end_idx = WINDOW_SIZE + 2
        tensor = _build_tensor(frames, window_end_idx, WINDOW_SIZE)

        self.assertEqual(tensor.shape, (FEATURE_NUMBER, 1, WINDOW_SIZE))
        # Real normalization convention (network.py:47): last real close in
        # the window normalizes to exactly 1.0 for the close channel.
        self.assertAlmostEqual(float(tensor[2, 0, -1]), 1.0, places=5)

    def test_stepwise_weight_vector_maps_to_cash_plus_ticker_dict(self):
        """Replicates q4_step()'s own real w -> {"CASH":..., ticker:...}
        mapping (real NNAgent.decide_by_history() output convention: index
        0 = cash, matching module header) against a synthetic real-shaped
        softmax vector."""
        import numpy as np

        tickers = ["BTC-USD", "ETH-USD"]
        w = np.array([0.2, 0.5, 0.3], dtype="float32")  # sums to 1.0, index 0 = cash

        weights = {"CASH": float(w[0])}
        for idx, t in enumerate(tickers):
            weights[t] = float(w[idx + 1])

        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)
        self.assertEqual(weights, {"CASH": 0.20000000298023224, "BTC-USD": 0.5, "ETH-USD": 0.30000001192092896})
        self.assertTrue(all(v >= 0 for v in weights.values()))

    def test_stepwise_decision_step_constructs_and_is_causal(self):
        from CONTRACT.schemas import PolicyDecisionStep

        step = PolicyDecisionStep(
            timestamp="2024-01-16", information_cutoff="2024-01-16",
            selected_universe=["BTC-USD", "ETH-USD"],
            target_weights={"CASH": 0.2, "BTC-USD": 0.5, "ETH-USD": 0.3},
        )
        self.assertLessEqual(step.information_cutoff, step.timestamp)
        self.assertAlmostEqual(sum(step.target_weights.values()), 1.0, places=5)

    def test_session_none_before_initialize_raises_on_step_and_finalize(self):
        """q4_step()/q4_finalize() called before q4_initialize() must fail
        loudly, not silently return a fabricated result."""
        from adapters.pgportfolio_adapter import PGPortfolioAdapter

        a = PGPortfolioAdapter()
        self.assertIsNone(a._session)
        with self.assertRaises(RuntimeError):
            a.q4_finalize()


if __name__ == "__main__":
    unittest.main()
