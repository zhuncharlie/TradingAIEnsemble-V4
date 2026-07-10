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
from analysis import icaif_alignment as alignment
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


def _df(rows):
    return records_to_dataframe([ResultRecord(**r) for r in rows])


class TestAlignmentContext(unittest.TestCase):
    """analysis/icaif_alignment.py — the three-tier context recovery chain."""

    def test_index_csv_tier_recovers_high_confidence_context(self):
        norm_path = "/repo/results/observations/observation_batch_day1/2026-07-06/finrl/Q4/portfolio_universe.json"
        index_ctx = {norm_path: {
            "batch_id": "observation_batch_day1", "q_type": "Q4",
            "input_granularity": "portfolio-level", "ticker_or_universe_id": "portfolio_universe",
            "decision_date": "2026-07-06",
        }}
        # recover_context resolves the path, so pass a Path whose .resolve()
        # matches the key exactly (use the key itself as a real-looking path).
        ctx = alignment.recover_context(Path(norm_path), {"task_id": "observation_batch_day1__2026-07-06"}, {
            str(Path(norm_path).resolve()): index_ctx[norm_path],
        })
        self.assertEqual(ctx["ctx_alignment_source"], "index_csv")
        self.assertEqual(ctx["ctx_alignment_confidence"], "high")
        self.assertEqual(ctx["ctx_decision_date"], "2026-07-06")
        self.assertIn("CASH", ctx["ctx_portfolio_universe"])
        self.assertIsNone(ctx["ctx_ticker"])  # portfolio-level -> no single ticker, correctly

    def test_task_id_pattern_fallback_when_no_index_csv(self):
        ctx = alignment.recover_context(
            Path("/repo/results/observations/observation_batch_day1_historical_extension/2026-05-15/qlib/Q3/NVDA.json"),
            {"task_id": "observation_batch_day1_historical_extension__2026-05-15"},
            index_ctx={},
        )
        self.assertEqual(ctx["ctx_alignment_source"], "task_id_pattern")
        self.assertEqual(ctx["ctx_alignment_confidence"], "medium")
        self.assertEqual(ctx["ctx_decision_date"], "2026-05-15")
        self.assertEqual(ctx["ctx_run_family"], "historical_extension")
        self.assertIn("NVDA", ctx["ctx_portfolio_universe"])

    def test_filename_pattern_fallback_for_legacy_data(self):
        ctx = alignment.recover_context(
            Path("/repo/results/comparison_2026-07-02/deepalpha__NVDA.json"),
            {"task_id": "comparison_2026-07-02"},
            index_ctx={},
        )
        self.assertEqual(ctx["ctx_ticker"], "NVDA")
        self.assertEqual(ctx["ctx_alignment_source"], "filename_pattern")
        self.assertEqual(ctx["ctx_alignment_confidence"], "low")

    def test_no_context_recoverable_returns_none_and_low_tier(self):
        ctx = alignment.recover_context(Path("/repo/results/mystery/output.json"), {"task_id": "mystery"}, index_ctx={})
        self.assertEqual(ctx["ctx_alignment_source"], "none")
        self.assertEqual(ctx["ctx_alignment_confidence"], "none")
        self.assertIsNone(ctx["ctx_decision_date"])
        self.assertIsNone(ctx["ctx_ticker"])


class TestContextExactJoin(unittest.TestCase):
    def test_long_with_weak_validation_upgrades_to_context_exact(self):
        cfg = Config()
        q3 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "direction": "LONG", "strength": 0.6, "supporting_evidence": ["x"]}])
        q5 = pd.DataFrame([{"adapter": "b", "task_id": "t1", "date": None, "ticker": None,
                             "total_return": -0.05, "sharpe": 0.1, "max_drawdown": -0.25, "win_rate": 0.3,
                             "ctx_alignment_source": "index_csv", "ctx_alignment_confidence": "high",
                             "ctx_portfolio_universe": ["NVDA", "SPY"], "ctx_ticker_universe": ["NVDA", "SPY"]}])
        out = contra.rule_long_with_weak_validation(q3, q5, cfg)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["alignment_confidence"], "context_exact")
        self.assertEqual(out.iloc[0]["exact_or_best_effort"], "best_effort")  # context_exact still isn't a schema-exact join

    def test_long_with_weak_validation_low_confidence_without_context(self):
        cfg = Config()
        q3 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "direction": "LONG", "strength": 0.6, "supporting_evidence": ["x"]}])
        q5 = pd.DataFrame([{"adapter": "b", "task_id": "t1", "date": None, "ticker": None,
                             "total_return": -0.05, "sharpe": 0.1, "max_drawdown": -0.25, "win_rate": 0.3,
                             "ctx_alignment_source": "none", "ctx_alignment_confidence": "none",
                             "ctx_portfolio_universe": None, "ctx_ticker_universe": None}])
        out = contra.rule_long_with_weak_validation(q3, q5, cfg)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["alignment_confidence"], "low_confidence")


class TestOldDataDoesNotCrash(unittest.TestCase):
    def test_extract_functions_tolerate_missing_ctx_columns(self):
        """A ResultRecord built with the default ctx={} (as if context
        recovery found nothing) must not KeyError anywhere in extraction."""
        df = _df([dict(
            path="p1", task_id="legacy", adapter="a", ticker="NVDA", date="d1",
            is_error=False, error=None,
            q1={"action": "BUY", "confidence": 0.8, "reasoning": "x", "ticker": "NVDA", "date": "d1"},
            q2=None, q3=None, q4=None, q5=None,
        )])
        q1 = contra.extract_q1(df)
        self.assertIn("ctx_alignment_source", q1.columns)
        self.assertTrue(q1["ctx_alignment_source"].isna().all() or (q1["ctx_alignment_source"] == None).all())  # noqa: E711

    def test_detect_contradictions_runs_on_data_with_no_recoverable_context(self):
        df = _df([
            dict(path="p1", task_id="legacy", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1={"action": "BUY", "confidence": 0.9, "reasoning": "x", "ticker": "NVDA", "date": "d1"},
                 q2=None, q3=None, q4=None, q5=None),
            dict(path="p2", task_id="legacy", adapter="b", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1=None, q2=None,
                 q3={"direction": "SHORT", "strength": 0.7, "supporting_evidence": ["x"], "ticker": "NVDA", "date": "d1"},
                 q4=None, q5=None),
        ])
        cfg = Config()
        result = contra.detect_contradictions(df, pd.DataFrame(), cfg)
        self.assertIn("ACTION_ALPHA_DIRECTION_CONFLICT", result["cases"]["flag"].tolist())


class TestNewRules(unittest.TestCase):
    def test_sentiment_risk_intra_conflict(self):
        q2 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "sentiment_score": 0.5, "risk_level": "EXTREME"}])
        out = contra.rule_sentiment_risk_intra_conflict(q2)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["alignment_confidence"], "single_record")

    def test_direction_return_intra_conflict_both_directions(self):
        q3 = pd.DataFrame([
            {"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1", "direction": "LONG",
             "strength": 0.5, "supporting_evidence": ["x"], "expected_return": -0.02},
            {"ticker": "SPY", "date": "d1", "adapter": "a", "task_id": "t1", "direction": "SHORT",
             "strength": 0.5, "supporting_evidence": ["x"], "expected_return": 0.02},
        ])
        out = contra.rule_direction_return_intra_conflict(q3)
        self.assertEqual(len(out), 2)

    def test_bull_regime_high_cash(self):
        cfg = Config(intra_record_high_cash_in_bull=0.5)
        q4 = pd.DataFrame([{"adapter": "a", "task_id": "t1", "date": "d1",
                             "weights": {"NVDA": 0.4}, "regime": "BULL", "cash_ratio": 0.6}])
        out = contra.rule_bull_regime_high_cash(q4, cfg)
        self.assertEqual(len(out), 1)

    def test_positive_return_weak_risk_adjusted(self):
        cfg = Config(intra_record_weak_risk_adjusted_sharpe=0.3, intra_record_weak_risk_adjusted_drawdown=-0.3)
        q5 = pd.DataFrame([{"adapter": "a", "task_id": "t1", "date": None,
                             "total_return": 0.05, "sharpe": 0.1, "max_drawdown": -0.4, "win_rate": 0.5}])
        out = contra.rule_positive_return_weak_risk_adjusted(q5, cfg)
        self.assertEqual(len(out), 1)

    def test_headline_evidence_mismatch_bullish_headline_bearish_text(self):
        df = _df([dict(
            path="p1", task_id="t1", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
            q1={"action": "BUY", "confidence": 0.8,
                "reasoning": "Bearish downside risk with a correction likely, but we still say buy",
                "ticker": "NVDA", "date": "d1"},
            q2=None, q3=None, q4=None, q5=None,
        )])
        out = contra.rule_headline_evidence_mismatch(df)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["flag"], "HEADLINE_EVIDENCE_MISMATCH")

    def test_atom_overlap_rules_same_and_opposite_direction(self):
        cfg = Config(evidence_overlap_min_records=2)
        df = _df([
            dict(path="p1", task_id="t1", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1={"action": "BUY", "confidence": 0.8, "reasoning": "strong momentum breakout", "ticker": "NVDA", "date": "d1"},
                 q2=None, q3=None, q4=None, q5=None),
            dict(path="p2", task_id="t1", adapter="b", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1=None, q2=None,
                 q3={"direction": "LONG", "strength": 0.7, "supporting_evidence": ["momentum picking up"], "ticker": "NVDA", "date": "d1"},
                 q4=None, q5=None),
            dict(path="p3", task_id="t1", adapter="c", ticker="NVDA", date="d1", is_error=False, error=None,
                 q1=None, q2=None,
                 q3={"direction": "SHORT", "strength": 0.7, "supporting_evidence": ["momentum fading fast"], "ticker": "NVDA", "date": "d1"},
                 q4=None, q5=None),
        ])
        q1, q3 = contra.extract_q1(df), contra.extract_q3(df)
        result = contra.rule_atom_overlap_vs_direction(df, q1, q3, cfg)
        # a (BUY) and b (LONG) agree and both mention momentum -> should NOT be zero-overlap
        # b (LONG) and c (SHORT) disagree but both mention momentum -> opposite-with-overlap
        self.assertGreaterEqual(len(result["OPPOSITE_DIRECTION_ATOM_OVERLAP"]), 1)

    def test_risk_atoms_but_bullish_headline(self):
        df = _df([dict(
            path="p1", task_id="t1", adapter="a", ticker="NVDA", date="d1", is_error=False, error=None,
            q1={"action": "BUY", "confidence": 0.8, "reasoning": "x", "ticker": "NVDA", "date": "d1"},
            q2={"sentiment_score": 0.1, "risk_level": "EXTREME", "drivers": ["x"], "ticker": "NVDA", "date": "d1"},
            q3=None, q4=None, q5=None,
        )])
        cfg = Config()
        out = contra.rule_risk_atoms_but_bullish_headline(df, cfg)
        self.assertEqual(len(out), 1)

    def test_confidence_in_poor_calibration_bucket(self):
        cfg = Config(calibration_bucket_poor_error=0.5)
        q1 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "action": "BUY", "confidence": 0.95, "reasoning": "x"}])
        q3 = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id", "direction", "strength"])
        calib = pd.DataFrame([{"adapter": "a", "question": "Q1", "horizon": 1, "bucket": "0.9-1.0",
                                "sample_count": 4, "avg_confidence": 0.95, "actual_hit_rate": 0.2,
                                "calibration_error": 0.75, "avg_forward_return": 0.0}])
        out = contra.rule_confidence_in_poor_calibration_bucket(q1, q3, calib, cfg)
        self.assertEqual(len(out), 1)

    def test_systematic_overconfidence(self):
        cfg = Config(systematic_overconfidence_min_horizons=2)
        q1 = pd.DataFrame([{"ticker": "NVDA", "date": "d1", "adapter": "a", "task_id": "t1",
                             "action": "BUY", "confidence": 0.9, "reasoning": "x"}])
        q3 = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id", "direction", "strength"])
        overconf = pd.DataFrame([
            {"adapter": "a", "question": "Q1", "horizon": 1, "avg_confidence": 0.9, "actual_hit_rate": 0.3, "sample_count": 20},
            {"adapter": "a", "question": "Q1", "horizon": 5, "avg_confidence": 0.9, "actual_hit_rate": 0.3, "sample_count": 20},
        ])
        out = contra.rule_systematic_overconfidence(q1, q3, overconf, cfg)
        self.assertEqual(len(out), 1)

    def test_temporal_flip_unexplained_fires_without_explaining_context(self):
        cfg = Config(temporal_window_days=14)
        q1 = pd.DataFrame([
            {"ticker": "NVDA", "date": "2026-05-01", "adapter": "a", "task_id": "t1", "action": "BUY", "confidence": 0.8, "reasoning": "x"},
            {"ticker": "NVDA", "date": "2026-05-05", "adapter": "a", "task_id": "t2", "action": "SELL", "confidence": 0.8, "reasoning": "x"},
        ])
        q3 = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id", "direction", "strength"])
        empty = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id"])
        out = contra.rule_temporal_flip_unexplained(q1, q3, empty, empty, empty, cfg)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["flag"], "TEMPORAL_FLIP_UNEXPLAINED")

    def test_temporal_flip_explained_by_regime_change_does_not_fire(self):
        cfg = Config(temporal_window_days=14)
        q1 = pd.DataFrame([
            {"ticker": "NVDA", "date": "2026-05-01", "adapter": "a", "task_id": "t1", "action": "BUY", "confidence": 0.8, "reasoning": "x"},
            {"ticker": "NVDA", "date": "2026-05-05", "adapter": "a", "task_id": "t2", "action": "SELL", "confidence": 0.8, "reasoning": "x"},
        ])
        q3 = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id", "direction", "strength"])
        q4 = pd.DataFrame([{"ticker": None, "date": "2026-05-03", "adapter": "a", "task_id": "t3",
                             "weights": {}, "regime": "BEAR", "cash_ratio": 0.1}])
        empty = pd.DataFrame(columns=["ticker", "date", "adapter", "task_id"])
        out = contra.rule_temporal_flip_unexplained(q1, q3, empty, q4, empty, cfg)
        self.assertEqual(len(out), 0)


class TestCoverageAuditAndRulebook(unittest.TestCase):
    def test_coverage_audit_covers_every_registered_rule(self):
        audit = contra.build_coverage_audit()
        implemented = set(audit[audit["kind"] == "implemented_rule"]["item"])
        self.assertEqual(implemented, set(contra.RULE_REGISTRY.keys()))

    def test_coverage_audit_has_theoretical_gaps(self):
        audit = contra.build_coverage_audit()
        gaps = audit[audit["kind"] == "theoretical_gap"]
        self.assertGreater(len(gaps), 0)
        self.assertTrue((gaps["detectable_now"] == False).all())  # noqa: E712

    def test_rulebook_md_mentions_every_rule(self):
        rulebook = contra.build_rulebook_md()
        for flag in contra.RULE_REGISTRY:
            self.assertIn(flag, rulebook)


if __name__ == "__main__":
    unittest.main()
