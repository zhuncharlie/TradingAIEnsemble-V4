"""
adapters/example_stub_adapter.py — Minimal reference implementation.

Copy this file, rename it, and fill in the real upstream calls.
Run: python CONTRACT/test_harness.py --adapter adapters/example_stub_adapter.py
"""

import time
from typing import List, Optional

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Action, Q1Decision, Q2Sentiment, RiskLevel


class ExampleStubAdapter(BaseAdapter):
    # ------------------------------------------------------------------
    # Required class-level metadata
    # ------------------------------------------------------------------
    name               = "example_stub"
    questions_answered = ["Q1", "Q2"]
    upstream_repo      = "https://github.com/FILL_IN/upstream-project"
    requires_env       = ""   # leave empty if no separate conda env needed

    # ------------------------------------------------------------------
    # Q1 — Buy / Sell / Hold decision
    # ------------------------------------------------------------------
    def q1_decision(self, ticker: str, date: str, **kwargs) -> Optional[Q1Decision]:
        t0 = time.time()

        # ── Replace the lines below with real upstream API calls ──────
        # from vendor.myproject import analyze
        # result = analyze(ticker, date)
        # action = Action.BUY if result["signal"] > 0 else Action.SELL
        # confidence = abs(result["signal"])
        # reasoning  = result["summary"]
        # ─────────────────────────────────────────────────────────────

        action     = Action.HOLD          # placeholder
        confidence = 0.5                  # placeholder
        reasoning  = "Stub adapter — replace with real upstream call."

        return Q1Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            bull_case=None,
            bear_case=None,
            time_horizon="1d",
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Q2 — Sentiment
    # ------------------------------------------------------------------
    def q2_sentiment(self, ticker: str, date: str, **kwargs) -> Optional[Q2Sentiment]:
        t0 = time.time()

        # ── Replace with real upstream sentiment call ─────────────────
        score      = 0.0
        risk_level = RiskLevel.MEDIUM
        drivers    = ["no real data — stub"]
        # ─────────────────────────────────────────────────────────────

        return Q2Sentiment(
            sentiment_score=score,
            risk_level=risk_level,
            drivers=drivers,
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Smoke test (fast, ≤ 1 real call)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()  # metadata checks
        result = self.q1_decision("AAPL", "2024-01-15")
        checks["q1_returns_Q1Decision"] = result is not None
        checks["action_is_valid"]       = result.action in ("BUY", "SELL", "HOLD")
        return checks
