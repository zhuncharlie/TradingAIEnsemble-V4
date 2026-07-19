"""
tests/test_q4_causality.py — validates harness/execution_engine.py's
causality-enforcement functions in isolation.

CONTRACT/schemas.py::PolicyDecisionStep's docstring states the
"information_cutoff <= timestamp" rule but explicitly does not enforce it
("safe ordering comparison is left to a layer that can parse a guaranteed
datetime format" — schemas.py:464-468). This file is what verifies that
layer (harness/execution_engine.py's enforce_causality/audit_trajectory)
actually does the job.

No network calls, no real adapter imports, no subprocess.

Usage:
    python -m unittest tests.test_q4_causality -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import PolicyDecisionStep
from harness.execution_engine import _parse_ts, audit_trajectory, enforce_causality
from harness.q4_protocol import MarketObservation, Q4CausalityViolation


def obs(step_index=0, timestamp="2024-01-15", information_cutoff="2024-01-14"):
    return MarketObservation(step_index=step_index, timestamp=timestamp, information_cutoff=information_cutoff)


def decision(timestamp="2024-01-15", information_cutoff="2024-01-14", **kw):
    return PolicyDecisionStep(timestamp=timestamp, information_cutoff=information_cutoff, **kw)


class TestParseTs(unittest.TestCase):
    def test_iso_date_parses(self):
        dt = _parse_ts("2024-01-15")
        self.assertEqual((dt.year, dt.month, dt.day), (2024, 1, 15))

    def test_iso_datetime_parses(self):
        dt = _parse_ts("2024-01-15T10:30:00")
        self.assertEqual(dt.hour, 10)

    def test_pandas_fallback_for_slash_dates(self):
        dt = _parse_ts("2024/01/15")
        self.assertEqual((dt.year, dt.month, dt.day), (2024, 1, 15))

    def test_garbage_raises_causality_violation(self):
        with self.assertRaises(Q4CausalityViolation):
            _parse_ts("not-a-real-date-at-all-xyz")


class TestEnforceCausality(unittest.TestCase):
    def test_valid_decision_passes(self):
        enforce_causality(decision(timestamp="2024-01-15", information_cutoff="2024-01-14"),
                           obs(timestamp="2024-01-15", information_cutoff="2024-01-14"))
        # no exception = pass

    def test_equal_cutoff_and_timestamp_passes(self):
        enforce_causality(decision(timestamp="2024-01-15", information_cutoff="2024-01-15"),
                           obs(timestamp="2024-01-15", information_cutoff="2024-01-15"))

    def test_mismatched_decision_timestamp_rejected(self):
        with self.assertRaises(Q4CausalityViolation):
            enforce_causality(decision(timestamp="2024-01-16", information_cutoff="2024-01-14"),
                               obs(timestamp="2024-01-15", information_cutoff="2024-01-14"))

    def test_cutoff_after_timestamp_rejected(self):
        # The observation itself is valid (its own cutoff <= its own
        # timestamp); the DECISION is the one claiming a later cutoff.
        with self.assertRaises(Q4CausalityViolation):
            enforce_causality(decision(timestamp="2024-01-15", information_cutoff="2024-01-16"),
                               obs(timestamp="2024-01-15", information_cutoff="2024-01-15"))

    def test_cutoff_beyond_disclosed_observation_cutoff_rejected(self):
        """Adapter claims to have used information later than what the
        harness actually disclosed this step — stronger than the schema's
        own rule, catches real lookahead an adapter might smuggle in."""
        with self.assertRaises(Q4CausalityViolation):
            enforce_causality(decision(timestamp="2024-01-15", information_cutoff="2024-01-15"),
                               obs(timestamp="2024-01-15", information_cutoff="2024-01-14"))

    def test_non_iso_timestamp_format_still_checked(self):
        enforce_causality(decision(timestamp="2024/01/15", information_cutoff="2024/01/14"),
                           obs(timestamp="2024/01/15", information_cutoff="2024/01/14"))


class TestAuditTrajectory(unittest.TestCase):
    def test_empty_trajectory_clean(self):
        self.assertEqual(audit_trajectory([]), [])

    def test_single_valid_step_clean(self):
        self.assertEqual(audit_trajectory([decision()]), [])

    def test_strictly_increasing_clean(self):
        decisions = [decision(timestamp=f"2024-01-{d:02d}", information_cutoff=f"2024-01-{d-1:02d}") for d in (15, 16, 17)]
        self.assertEqual(audit_trajectory(decisions), [])

    def test_non_increasing_timestamps_flagged(self):
        decisions = [decision(timestamp="2024-01-16", information_cutoff="2024-01-15"),
                     decision(timestamp="2024-01-15", information_cutoff="2024-01-14")]
        violations = audit_trajectory(decisions)
        self.assertTrue(any("before" in v for v in violations))

    def test_duplicate_timestamps_flagged(self):
        decisions = [decision(timestamp="2024-01-15", information_cutoff="2024-01-14"),
                     decision(timestamp="2024-01-15", information_cutoff="2024-01-14")]
        violations = audit_trajectory(decisions)
        self.assertTrue(any("duplicates" in v for v in violations))

    def test_per_step_causality_violation_flagged(self):
        decisions = [decision(timestamp="2024-01-15", information_cutoff="2024-01-16")]
        violations = audit_trajectory(decisions)
        self.assertTrue(any("after timestamp" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
