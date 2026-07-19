"""
tests/test_point_in_time_guards.py — §九's automatic point-in-time / causality
checks: generation_window.end <= test_window.start, no future data in
observations, strictly time-increasing decisions, and that a real leakage
attempt HARD STOPS (raises) rather than merely logging a warning.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from CONTRACT.schemas import PolicyDecisionStep
from harness.execution_engine import audit_trajectory, enforce_causality
from harness.observations import (
    build_observations,
    check_generation_test_split,
    resolve_rebalance_schedule,
    resolve_test_window_dates,
)
from harness.q4_protocol import MarketObservation, Q4CausalityViolation


class TestGenerationTestSplit(unittest.TestCase):
    def test_valid_split_passes(self):
        check_generation_test_split("2024-01-15", "2024-01-16")  # no raise

    def test_equal_boundary_allowed(self):
        check_generation_test_split("2024-01-15", "2024-01-15")  # no raise

    def test_generation_overlapping_test_window_hard_stops(self):
        with self.assertRaises(Q4CausalityViolation):
            check_generation_test_split("2024-02-01", "2024-01-15")

    def test_violation_raises_not_just_warns(self):
        # A real, common leakage mistake: generation_window mistakenly set to
        # extend past test_window.start. Must raise immediately.
        with self.assertRaises(Q4CausalityViolation):
            check_generation_test_split("2024-06-01", "2024-01-01")


class TestObservationConstructionNoFutureLeakage(unittest.TestCase):
    def test_first_observation_cutoff_equals_own_timestamp(self):
        obs = build_observations(["2024-01-02", "2024-01-03", "2024-01-04"], ["AAPL"])
        self.assertEqual(obs[0].information_cutoff, obs[0].timestamp)

    def test_subsequent_observations_cutoff_is_prior_real_date(self):
        dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
        obs = build_observations(dates, ["AAPL"])
        self.assertEqual(obs[1].information_cutoff, dates[0])
        self.assertEqual(obs[2].information_cutoff, dates[1])

    def test_no_observation_cutoff_ever_after_its_timestamp(self):
        dates = [f"2024-01-{d:02d}" for d in range(2, 20)]
        obs = build_observations(dates, ["AAPL", "MSFT"])
        for o in obs:
            self.assertLessEqual(o.information_cutoff, o.timestamp)

    def test_observations_are_strictly_time_ordered(self):
        dates = [f"2024-01-{d:02d}" for d in range(2, 15)]
        obs = build_observations(dates, ["AAPL"])
        timestamps = [o.timestamp for o in obs]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_non_monotonic_input_dates_are_rejected(self):
        with self.assertRaises(Q4CausalityViolation):
            build_observations(["2024-01-05", "2024-01-01", "2024-01-06"], ["AAPL"])

    def test_bar_only_contains_real_supplied_prices(self):
        prices = pd.DataFrame(
            {"AAPL": [100.0, 101.0]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        obs = build_observations(["2024-01-02", "2024-01-03"], ["AAPL"], prices=prices)
        self.assertEqual(obs[0].bar["AAPL"]["close"], 100.0)
        self.assertEqual(obs[1].bar["AAPL"]["close"], 101.0)

    def test_bar_none_when_no_prices_supplied(self):
        obs = build_observations(["2024-01-02", "2024-01-03"], ["AAPL"])
        for o in obs:
            self.assertIsNone(o.bar)


class TestRebalanceSchedule(unittest.TestCase):
    def test_daily_uses_every_date(self):
        dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
        self.assertEqual(resolve_rebalance_schedule(dates, "daily"), dates)

    def test_monthly_keeps_first_real_day_per_month(self):
        dates = ["2024-01-02", "2024-01-15", "2024-02-01", "2024-02-20"]
        sched = resolve_rebalance_schedule(dates, "monthly")
        self.assertEqual(sched, ["2024-01-02", "2024-02-01"])

    def test_schedule_only_drawn_from_real_observed_dates(self):
        # A synthetic calendar could propose a rebalance date that isn't a
        # real trading day; resolve_rebalance_schedule must never invent one.
        dates = ["2024-01-02", "2024-01-03"]
        sched = resolve_rebalance_schedule(dates, "weekly")
        for d in sched:
            self.assertIn(d, dates)

    def test_is_rebalance_point_flag_reflects_schedule(self):
        dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
        schedule = ["2024-01-02", "2024-01-04"]
        obs = build_observations(dates, ["AAPL"], rebalance_schedule=schedule)
        self.assertTrue(obs[0].is_rebalance_point)
        self.assertFalse(obs[1].is_rebalance_point)
        self.assertTrue(obs[2].is_rebalance_point)


class TestTestWindowDateResolution(unittest.TestCase):
    def test_dates_drawn_only_from_real_price_index(self):
        prices = pd.DataFrame(
            {"AAPL": [1, 2, 3]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"]),
        )
        dates = resolve_test_window_dates(prices, "2024-01-01", "2024-01-31")
        self.assertEqual(dates, ["2024-01-02", "2024-01-03", "2024-01-05"])
        # 2024-01-04 is not a real trading day in this panel; must not appear.
        self.assertNotIn("2024-01-04", dates)

    def test_empty_intersection_raises(self):
        prices = pd.DataFrame({"AAPL": [1]}, index=pd.to_datetime(["2024-01-02"]))
        with self.assertRaises(RuntimeError):
            resolve_test_window_dates(prices, "2025-01-01", "2025-01-31")


class TestDecisionLevelLeakageHardStops(unittest.TestCase):
    """enforce_causality (execution_engine.py) is the second, stronger layer
    that checks the adapter's ACTUAL returned decision against the harness's
    own disclosed observation -- this is where a real leakage attempt by a
    cheating/buggy adapter would be caught, distinct from the harness's own
    observation-construction guards above."""

    def _obs(self, timestamp="2024-01-05", cutoff="2024-01-04"):
        return MarketObservation(step_index=0, timestamp=timestamp, information_cutoff=cutoff)

    def test_decision_cutoff_beyond_disclosed_cutoff_hard_stops(self):
        obs = self._obs()
        cheating_decision = PolicyDecisionStep(
            timestamp="2024-01-05", information_cutoff="2024-01-05",  # claims same-day info
            target_weights={"AAPL": 1.0},
        )
        with self.assertRaises(Q4CausalityViolation):
            enforce_causality(cheating_decision, obs)

    def test_valid_decision_passes(self):
        obs = self._obs()
        decision = PolicyDecisionStep(
            timestamp="2024-01-05", information_cutoff="2024-01-04",
            target_weights={"AAPL": 1.0},
        )
        enforce_causality(decision, obs)  # no raise

    def test_trajectory_audit_flags_non_increasing_sequence(self):
        decisions = [
            PolicyDecisionStep(timestamp="2024-01-05", information_cutoff="2024-01-04", target_weights={"AAPL": 1.0}),
            PolicyDecisionStep(timestamp="2024-01-03", information_cutoff="2024-01-02", target_weights={"AAPL": 1.0}),
        ]
        violations = audit_trajectory(decisions)
        self.assertTrue(violations)


if __name__ == "__main__":
    unittest.main()
