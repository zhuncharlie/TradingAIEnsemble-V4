"""
analysis/test_icaif_experiments.py — unit tests for the ICAIF experiment
suite. Uses stdlib unittest (no pytest dependency needed anywhere in this
repo's conda envs). Run with:

    python -m unittest analysis.test_icaif_experiments -v

No network calls, no adapter imports, no dependency on real results/ data —
everything here is synthetic fixtures, deterministic by construction.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from analysis.icaif_data_loader import AdapterInfo, FutureReturnProvider, records_to_dataframe, ResultRecord
from analysis.icaif_metrics import (
    Config,
    bucket_confidence,
    build_calibration_table,
    build_coverage_matrix,
    compute_hit,
    compute_return_based_metrics,
    coverage_audit_findings,
    evidence_atoms_from_record,
    flag_overconfidence,
    risk_atoms_from_record,
    score_to_decision,
    validation_atoms_from_record,
)
from analysis import icaif_contradictions as contra
from analysis import icaif_fusion as fusion


def _row(**kwargs) -> pd.Series:
    base = {
        "adapter": "adapter_a", "ticker": "NVDA", "date": "2026-07-02", "task_id": "t1",
        "is_error": False, "error": None,
        "q1_present": False, "q2_present": False, "q3_present": False,
        "q4_present": False, "q5_present": False,
    }
    base.update(kwargs)
    return pd.Series(base)


class TestCoverageMatrix(unittest.TestCase):
    def test_declared_implemented_observed_agree(self):
        adapters = [AdapterInfo(file="a.py", class_name="A", name="adapter_a",
                                 questions_declared=["Q1"], questions_implemented=["Q1"])]
        df = pd.DataFrame([{"adapter": "adapter_a", "q1_present": True, "q2_present": False,
                             "q3_present": False, "q4_present": False, "q5_present": False}])
        matrix = build_coverage_matrix(adapters, df)
        self.assertEqual(matrix.loc["adapter_a", "Q1"], "declared+implemented+observed")
        self.assertEqual(matrix.loc["adapter_a", "Q2"], "")

    def test_no_observed_results_is_flagged(self):
        adapters = [AdapterInfo(file="a.py", class_name="A", name="adapter_a",
                                 questions_declared=["Q1"], questions_implemented=["Q1"])]
        df = pd.DataFrame(columns=["adapter", "q1_present"])
        findings = coverage_audit_findings(adapters, df)
        self.assertIn("no_observed_results", findings["kind"].tolist())

    def test_declared_vs_implemented_mismatch_flagged(self):
        adapters = [AdapterInfo(file="a.py", class_name="A", name="adapter_a",
                                 questions_declared=["Q1", "Q2"], questions_implemented=["Q1"])]
        df = pd.DataFrame([{"adapter": "adapter_a", "q1_present": True, "q2_present": False,
                             "q3_present": False, "q4_present": False, "q5_present": False}])
        findings = coverage_audit_findings(adapters, df)
        kinds = findings["kind"].tolist()
        self.assertIn("declared_vs_implemented_mismatch", kinds)


class TestSecondaryFieldExtraction(unittest.TestCase):
    def test_evidence_atoms_tag_momentum_and_risk(self):
        row = _row(q1_present=True, q1_reasoning="Strong momentum breakout with elevated drawdown risk")
        atoms = evidence_atoms_from_record(row)
        self.assertIn("momentum", atoms)
        self.assertIn("risk", atoms)

    def test_evidence_atoms_empty_when_no_text(self):
        row = _row(q1_present=True, q1_reasoning=None)
        self.assertEqual(evidence_atoms_from_record(row), [])

    def test_risk_atoms_from_risk_level_and_drawdown(self):
        row = _row(q2_present=True, q2_risk_level="EXTREME", q5_present=True, q5_max_drawdown=-0.30)
        atoms = risk_atoms_from_record(row)
        self.assertIn("risk_level:EXTREME", atoms)
        self.assertIn("severe_drawdown", atoms)

    def test_validation_atoms_missing_when_no_q5(self):
        row = _row(q5_present=False)
        self.assertEqual(validation_atoms_from_record(row, Config()), [])

    def test_validation_atoms_strong(self):
        row = _row(q5_present=True, q5_total_return=0.10, q5_sharpe=1.2, q5_max_drawdown=-0.05, q5_win_rate=0.6)
        atoms = validation_atoms_from_record(row, Config())
        self.assertIn("validation_status:strong", atoms)


class TestConfidenceBucketing(unittest.TestCase):
    def test_bucket_edges(self):
        cfg = Config()
        self.assertEqual(bucket_confidence(0.0, cfg), "0.0-0.5")
        self.assertEqual(bucket_confidence(0.55, cfg), "0.5-0.6")
        self.assertEqual(bucket_confidence(0.95, cfg), "0.9-1.0")
        self.assertEqual(bucket_confidence(1.0, cfg), "0.9-1.0")

    def test_compute_hit_q1_buy(self):
        cfg = Config(threshold_bps=20.0)
        self.assertTrue(compute_hit("BUY", 0.01, cfg, "q1"))
        self.assertFalse(compute_hit("BUY", -0.01, cfg, "q1"))
        self.assertIsNone(compute_hit("BUY", None, cfg, "q1"))

    def test_compute_hit_q1_hold_within_threshold(self):
        cfg = Config(threshold_bps=20.0)
        self.assertTrue(compute_hit("HOLD", 0.0005, cfg, "q1"))
        self.assertFalse(compute_hit("HOLD", 0.01, cfg, "q1"))

    def test_calibration_table_and_overconfidence_flag(self):
        cfg = Config(overconfidence_min_confidence=0.75, overconfidence_max_hit_rate=0.55, overconfidence_min_samples=2)
        rows = []
        for i in range(5):
            rows.append({"adapter": "overconfident_adapter", "question": "Q1", "horizon": 1,
                         "confidence": 0.9, "hit": (i == 0), "future_return": 0.001})
        df_hits = pd.DataFrame(rows)
        table = build_calibration_table(df_hits, cfg)
        self.assertFalse(table.empty)
        flags = flag_overconfidence(table, cfg)
        self.assertIn("overconfident_adapter", flags["adapter"].tolist())


class TestFutureReturnProvider(unittest.TestCase):
    def test_never_fabricates_when_insufficient_future_days(self):
        class TinyProvider(FutureReturnProvider):
            def __init__(self):
                self.df = pd.DataFrame({
                    "Date": pd.to_datetime(["2026-07-01", "2026-07-02", "2026-07-03"]),
                    "Close": [100.0, 101.0, 102.0],
                })

            def get_future_return(self, ticker, decision_date, horizon):
                d0 = pd.Timestamp(decision_date)
                after = self.df[self.df["Date"] > d0].reset_index(drop=True)
                before = self.df[self.df["Date"] <= d0]
                if before.empty or len(after) < horizon:
                    return None
                return float(after.iloc[horizon - 1]["Close"] / before.iloc[-1]["Close"] - 1.0)

        p = TinyProvider()
        self.assertIsNone(p.get_future_return("X", "2026-07-02", 20))
        self.assertIsNotNone(p.get_future_return("X", "2026-07-02", 1))


class TestContradictionRules(unittest.TestCase):
    def test_buy_with_high_risk(self):
        q1 = pd.DataFrame([{"ticker": "NVDA", "date": "2026-07-02", "adapter": "a", "task_id": "t1",
                             "action": "BUY", "confidence": 0.8, "reasoning": "x"}])
        q2 = pd.DataFrame([{"ticker": "NVDA", "date": "2026-07-02", "adapter": "b", "task_id": "t1",
                             "sentiment_score": 0.1, "risk_level": "EXTREME"}])
        out = contra.rule_buy_with_high_risk(q1, q2)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["flag"], "BUY_WITH_HIGH_RISK")

    def test_action_alpha_direction_conflict_both_directions(self):
        q1 = pd.DataFrame([
            {"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1", "action": "BUY", "confidence": 0.8, "reasoning": "x"},
            {"ticker": "TSLA", "date": "d1", "adapter": "a", "task_id": "t1", "action": "SELL", "confidence": 0.8, "reasoning": "x"},
        ])
        q3 = pd.DataFrame([
            {"ticker": "NVDA", "date": "d1", "adapter": "b", "task_id": "t1", "direction": "SHORT", "strength": 0.7, "supporting_evidence": ["x"]},
            {"ticker": "TSLA", "date": "d1", "adapter": "b", "task_id": "t1", "direction": "LONG", "strength": 0.7, "supporting_evidence": ["x"]},
        ])
        out = contra.rule_action_alpha_direction_conflict(q1, q3)
        self.assertEqual(len(out), 2)

    def test_strong_signal_missing_evidence(self):
        q3 = pd.DataFrame([
            {"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1", "direction": "LONG",
             "strength": 0.9, "supporting_evidence": []},
            {"ticker": "TSLA", "date": "d1", "adapter": "a", "task_id": "t1", "direction": "LONG",
             "strength": 0.9, "supporting_evidence": ["factor X"]},
        ])
        out = contra.rule_strong_signal_missing_evidence(q3, Config())
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["ticker"], "NVDA")

    def test_no_data_returns_empty_not_error(self):
        empty = pd.DataFrame()
        self.assertTrue(contra.rule_buy_with_high_risk(empty, empty).empty)
        self.assertTrue(contra.rule_action_alpha_direction_conflict(empty, empty).empty)

    def test_long_with_weak_validation_documents_limitation(self):
        # q5 carries its own (all-None) ticker/date columns here, matching
        # what extract_q5() actually produces from the real flattened df —
        # this collision (both sides have "ticker"/"date") is exactly what
        # made the real detail_fn crash with a bare r['ticker'] KeyError
        # once real Q3+Q5 data coexisted (see icaif_contradictions.py fix).
        q3 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "direction": "LONG", "strength": 0.6, "supporting_evidence": ["x"]}])
        q5 = pd.DataFrame([{"adapter": "b", "task_id": "t1", "date": None, "ticker": None,
                             "total_return": -0.05, "sharpe": 0.1, "max_drawdown": -0.25, "win_rate": 0.3}])
        out = contra.rule_long_with_weak_validation(q3, q5, Config())
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["ticker"], "NVDA")
        self.assertIn("task_id", out.iloc[0]["limitation"])

    def test_positive_sentiment_bear_regime_ticker_collision(self):
        q2 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "sentiment_score": 0.5, "risk_level": "LOW"}])
        q4 = pd.DataFrame([{"adapter": "b", "task_id": "t1", "date": "d1", "ticker": None,
                             "weights": {"NVDA": 0.2}, "regime": "BEAR", "cash_ratio": 0.1}])
        out = contra.rule_positive_sentiment_bear_regime(q2, q4)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["ticker"], "NVDA")

    def test_high_weight_high_drawdown_ticker_collision(self):
        q4 = pd.DataFrame([{"adapter": "a", "task_id": "t1", "date": "d1", "ticker": None,
                             "weights": {"NVDA": 0.5}, "regime": "BULL", "cash_ratio": 0.0}])
        q5 = pd.DataFrame([{"adapter": "b", "task_id": "t1", "date": None, "ticker": None,
                             "total_return": -0.1, "sharpe": 0.2, "max_drawdown": -0.3, "win_rate": 0.4}])
        out = contra.rule_high_weight_high_drawdown(q4, q5, Config())
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["ticker"], "NVDA")


class TestFusionMethods(unittest.TestCase):
    def _df(self, rows):
        return records_to_dataframe([ResultRecord(**r) for r in rows])

    def test_majority_vote_unanimous_buy(self):
        df = self._df([
            dict(path="p1", task_id="t1", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1={"action": "BUY", "confidence": 0.9, "reasoning": "x", "ticker": "NVDA", "date": "d1"},
                 q2=None, q3=None, q4=None, q5=None),
            dict(path="p2", task_id="t1", adapter="b", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1=None, q2=None,
                 q3={"direction": "LONG", "strength": 0.8, "supporting_evidence": ["x"], "ticker": "NVDA", "date": "d1"},
                 q4=None, q5=None),
        ])
        cfg = Config()
        decisions = fusion.compute_fusion_decisions(df, pd.DataFrame(), cfg, future_return_lookup=None)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions.iloc[0]["majority_vote_decision"], "BUY")

    def test_interwoven_penalizes_high_risk(self):
        df = self._df([
            dict(path="p1", task_id="t1", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1={"action": "BUY", "confidence": 0.9, "reasoning": "x", "ticker": "NVDA", "date": "d1"},
                 q2=None, q3=None, q4=None, q5=None),
            dict(path="p2", task_id="t1", adapter="b", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1=None,
                 q2={"sentiment_score": 0.1, "risk_level": "EXTREME", "drivers": ["x"], "ticker": "NVDA", "date": "d1"},
                 q3=None, q4=None, q5=None),
        ])
        cfg = Config()
        cases = contra.detect_contradictions(df, pd.DataFrame(), cfg)["cases"]
        decisions = fusion.compute_fusion_decisions(df, cases, cfg, future_return_lookup=None)
        row = decisions.iloc[0]
        self.assertLess(row["interwoven_score"], row["confidence_weighted_score"])

    def test_score_to_decision_thresholds(self):
        cfg = Config(fusion_buy_threshold=0.25, fusion_sell_threshold=-0.25)
        self.assertEqual(score_to_decision(0.3, cfg), "BUY")
        self.assertEqual(score_to_decision(-0.3, cfg), "SELL")
        self.assertEqual(score_to_decision(0.0, cfg), "HOLD")


class TestMissingDataBehavior(unittest.TestCase):
    def test_return_metrics_insufficient_data_when_all_null(self):
        decisions = pd.DataFrame({"signal": [1, -1, 0], "future_return": [None, None, None]})
        result = compute_return_based_metrics(decisions)
        self.assertTrue(result["insufficient_data"])

    def test_return_metrics_computed_when_data_present(self):
        decisions = pd.DataFrame({
            "signal": [1, -1, 1], "future_return": [0.01, 0.02, -0.01],
            "ticker": ["A", "B", "A"], "date": ["d1", "d1", "d2"],
        })
        result = compute_return_based_metrics(decisions)
        self.assertFalse(result["insufficient_data"])
        self.assertIn("hit_rate", result)


if __name__ == "__main__":
    unittest.main()
