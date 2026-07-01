"""
CONTRACT/base_adapter.py — Abstract base class every adapter must inherit.

DO NOT MODIFY THIS FILE.

Implementation rules:
  1. Subclass BaseAdapter in your adapters/{name}_adapter.py file.
  2. Set `name` (snake_case, unique) and `questions_answered` as class attributes.
  3. Implement only the q* methods your upstream project actually supports.
     Methods you don't implement return None by default — that is correct.
  4. Never import from another adapter file.
  5. Run `python CONTRACT/test_harness.py --adapter adapters/your_file.py`
     to validate before committing.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar, Dict, List, Optional

from CONTRACT.schemas import (
    AdapterResult,
    Q1Decision,
    Q2Sentiment,
    Q3Signal,
    Q4Portfolio,
    Q5Backtest,
)


class BaseAdapter(ABC):
    """
    Wraps one upstream trading-AI project and exposes its outputs
    through the five canonical Q-schema methods.

    Minimum viable implementation: override at least ONE q* method.
    All others default to None (meaning "this project doesn't answer this question").
    """

    # --- class-level metadata (override in your subclass) ---
    name: ClassVar[str] = ""
    """Unique snake_case identifier, e.g. 'ai_hedge_fund'. Used as the JSON filename."""

    questions_answered: ClassVar[List[str]] = []
    """Which questions this adapter answers: subset of ["Q1","Q2","Q3","Q4","Q5"]."""

    upstream_repo: ClassVar[str] = ""
    """GitHub URL of the project being wrapped. For documentation only."""

    requires_env: ClassVar[str] = ""
    """conda env name if a separate env is required, else empty string."""

    # ------------------------------------------------------------------ #
    # Q-schema methods — override the ones your project supports          #
    # ------------------------------------------------------------------ #

    def q1_decision(
        self,
        ticker: str,
        date: str,
        **kwargs,
    ) -> Optional[Q1Decision]:
        """Single-stock BUY/SELL/HOLD decision."""
        return None

    def q2_sentiment(
        self,
        ticker: str,
        date: str,
        **kwargs,
    ) -> Optional[Q2Sentiment]:
        """Market sentiment score and risk level."""
        return None

    def q3_signal(
        self,
        ticker: str,
        date: str,
        **kwargs,
    ) -> Optional[Q3Signal]:
        """Alpha signal or anomaly detection."""
        return None

    def q4_portfolio(
        self,
        tickers: List[str],
        date: str,
        **kwargs,
    ) -> Optional[Q4Portfolio]:
        """Portfolio weight allocation across multiple tickers."""
        return None

    def q5_backtest(
        self,
        tickers: List[str],
        start: str,
        end: str,
        **kwargs,
    ) -> Optional[Q5Backtest]:
        """Historical backtest performance metrics."""
        return None

    # ------------------------------------------------------------------ #
    # Convenience: build a complete AdapterResult envelope               #
    # ------------------------------------------------------------------ #

    def run(
        self,
        task_id: str,
        ticker: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        native_output: Optional[dict] = None,
        adapter_notes: str = "",
        **kwargs,
    ) -> AdapterResult:
        """
        Call all implemented q* methods and bundle results into AdapterResult.
        Adapters can override this if they need a different call sequence.
        """
        q1 = self.q1_decision(ticker, date, **kwargs)        if ticker and date  else None
        q2 = self.q2_sentiment(ticker, date, **kwargs)       if ticker and date  else None
        q3 = self.q3_signal(ticker, date, **kwargs)          if ticker and date  else None
        q4 = self.q4_portfolio(tickers or [], date, **kwargs) if date            else None
        q5 = self.q5_backtest(tickers or [], start, end, **kwargs) if start      else None

        return AdapterResult(
            adapter=self.name,
            task_id=task_id,
            q1=q1, q2=q2, q3=q3, q4=q4, q5=q5,
            native_output=native_output or {},
            adapter_notes=adapter_notes,
        )

    # ------------------------------------------------------------------ #
    # Smoke test — override for adapter-specific quick checks            #
    # ------------------------------------------------------------------ #

    def smoke_test(self) -> Dict[str, bool]:
        """
        Run a minimal self-check. Returns {check_name: passed}.
        Must complete in under 5 minutes and make at most 1 real API call.
        Default implementation just checks the class metadata is set.
        """
        return {
            "name_set":               bool(self.name),
            "questions_answered_set": bool(self.questions_answered),
            "upstream_repo_set":      bool(self.upstream_repo),
        }
