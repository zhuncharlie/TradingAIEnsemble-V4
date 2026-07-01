"""
adapters/ai_hedge_fund_adapter.py — wraps github.com/virattt/ai-hedge-fund (Q1).

Environment setup (one-time, outside this file):
    conda create -n ai_hedge_fund_real python=3.11
    conda activate ai_hedge_fund_real
    conda install -c conda-forge "rust>=1.85"   # tiktoken==0.12.0 needs a Cargo
                                                 # edition-2024-capable Rust to
                                                 # build from source on this
                                                 # machine's glibc 2.27 (no
                                                 # manylinux_2_28 wheel available)
    cd adapters/vendor/ai-hedge-fund && poetry install --no-root
    echo 'DEEPSEEK_API_KEY=sk-...' > adapters/vendor/ai-hedge-fund/.env

Run the harness with that env active:
    conda activate ai_hedge_fund_real
    python CONTRACT/test_harness.py --adapter adapters/ai_hedge_fund_adapter.py

No upstream source was patched — only environment/dependency setup was needed,
so there is no patches/ai-hedge-fund.diff.

Design notes (translation choices made by this adapter, not upstream):
  - Only ONE analyst ("technical_analyst") is enabled by default. It is a
    purely rule-based analyst (no LLM call) — see src/agents/technicals.py.
    risk_management_agent is also non-LLM. That leaves exactly ONE real LLM
    call per q1_decision() invocation: portfolio_manager. This keeps the
    "real" smoke test cheap/fast while still exercising the full LangGraph
    pipeline end-to-end.
  - date range: upstream's own CLI defaults to a 3-month lookback window
    when only an end date is given (src/cli/input.py:resolve_dates). This
    adapter replicates that same default so technical indicators have
    enough history to compute.
  - action mapping: upstream's 5-way action space (buy/sell/short/cover/hold)
    is collapsed onto our 3-way Action enum: buy, cover -> BUY (both are
    "go/return long"); sell, short -> SELL (both are "go/return short");
    hold -> HOLD.
  - confidence: upstream reports an int 0-100; divided by 100 to fit our
    0.0-1.0 float range.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil.relativedelta import relativedelta

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Action, Q1Decision

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund"

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from dotenv import load_dotenv  # noqa: E402  (vendor path must be on sys.path first)

load_dotenv(dotenv_path=VENDOR_DIR / ".env")

from src.main import run_hedge_fund  # noqa: E402

DEFAULT_ANALYSTS = ["technical_analyst"]
MODEL_NAME = "deepseek-v4-pro"
MODEL_PROVIDER = "DeepSeek"

_ACTION_MAP = {
    "buy": Action.BUY,
    "cover": Action.BUY,
    "sell": Action.SELL,
    "short": Action.SELL,
    "hold": Action.HOLD,
}


def _build_portfolio(tickers: list[str]) -> dict:
    return {
        "cash": 100_000.0,
        "margin_requirement": 0.0,
        "margin_used": 0.0,
        "positions": {
            t: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for t in tickers
        },
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }


class AiHedgeFundAdapter(BaseAdapter):
    name = "ai_hedge_fund"
    questions_answered = ["Q1"]
    upstream_repo = "https://github.com/virattt/ai-hedge-fund"
    requires_env = "ai_hedge_fund_real"

    def q1_decision(self, ticker: str, date: str, **kwargs) -> Optional[Q1Decision]:
        t0 = time.time()

        end_dt = datetime.strptime(date, "%Y-%m-%d")
        start_date = (end_dt - relativedelta(months=3)).strftime("%Y-%m-%d")

        if os.environ.get("DEEPSEEK_API_KEY") is None:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. Create adapters/vendor/ai-hedge-fund/.env "
                "with DEEPSEEK_API_KEY=... (never hardcode it here)."
            )

        result = run_hedge_fund(
            tickers=[ticker],
            start_date=start_date,
            end_date=date,
            portfolio=_build_portfolio([ticker]),
            selected_analysts=DEFAULT_ANALYSTS,
            model_name=MODEL_NAME,
            model_provider=MODEL_PROVIDER,
        )

        decisions = (result or {}).get("decisions") or {}
        raw = decisions.get(ticker)
        if raw is None:
            raise RuntimeError(f"ai-hedge-fund returned no decision for {ticker}: {result}")

        raw_action = str(raw.get("action", "hold")).lower()
        action = _ACTION_MAP.get(raw_action, Action.HOLD)
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0)) / 100.0))
        reasoning = str(raw.get("reasoning") or "").strip()
        if len(reasoning) < 10:
            reasoning = f"ai-hedge-fund portfolio_manager returned action={raw_action} with no further detail."

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

    def smoke_test(self):
        checks = super().smoke_test()
        result = self.q1_decision("AAPL", "2024-01-15")
        checks["q1_returns_Q1Decision"] = result is not None
        checks["action_is_valid"] = result.action in ("BUY", "SELL", "HOLD")
        checks["confidence_in_range"] = 0.0 <= result.confidence <= 1.0
        return checks
