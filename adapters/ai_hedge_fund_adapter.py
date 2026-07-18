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

Schema v2.0.0 migration notes (this adapter now answers Q1 only, same as v1 —
no new Q layer claimed):
  - Only ONE analyst ("technical_analyst") is enabled by default. It is a
    purely rule-based analyst (no LLM call) — see src/agents/technicals.py.
    risk_management_agent is also non-LLM. That leaves exactly ONE real LLM
    call per q1_action() invocation: portfolio_manager. This keeps the
    "real" smoke test cheap/fast while still exercising the full LangGraph
    pipeline end-to-end.
  - date range: upstream's own CLI defaults to a 3-month lookback window
    when only an end date is given (src/cli/input.py:resolve_dates). This
    adapter replicates that same default so technical indicators have
    enough history to compute. Under v2 this fetch window is still an
    adapter-internal constant (not a harness-supplied generation_window —
    this adapter has no Q4, so there is no such window to accept).
  - action mapping: upstream's 5-way action space (buy/sell/short/cover/hold)
    is collapsed onto our 3-way Action enum: buy, cover -> BUY (both are
    "go/return long"); sell, short -> SELL (both are "go/return short");
    hold -> HOLD.
  - confidence: upstream's real `PortfolioDecision.confidence` is an int
    0-100 (see src/agents/portfolio_manager.py::PortfolioDecision). Mapped to
    ConfidenceEstimate(value=confidence/100, kind=SELF_REPORTED, raw_value=
    the original 0-100 int) — this is the LLM's own self-reported conviction,
    not a calibrated probability or a score derived by this adapter.
  - target_position (RECOVERED in this migration — see PROJECT_SCHEMA_AUDIT.md
    §4.1/§7/§8): upstream's real `PortfolioDecision.quantity` (an integer
    share count computed by the portfolio_manager LLM call, constrained
    deterministically by compute_allowed_actions()) was read into the v1
    adapter's `Q1Decision.reasoning` prompt context only implicitly and never
    surfaced as a canonical field — the v1 adapter discarded it entirely.
    This migration reads it and signs it by action: buy/cover (increase or
    return to long) -> +quantity; sell/short (reduce or go short) ->
    -quantity; hold -> 0. This is a direct, disclosed sign transform of a
    real upstream integer, not a fabrication.
  - explanation: upstream's real `PortfolioDecision.reasoning` string is
    passed through as-is when non-empty. The v1 fallback template string
    ("X returned action=Y with no further detail") is deleted per the v2
    migration rubric — explanation is genuinely optional in v2, so an empty
    upstream reasoning now maps to explanation=None instead of a fabricated
    placeholder sentence.
  - bull_case / bear_case: this project has no bull/bear debate concept
    (unlike TradingAgents) — both remain None, as in v1.
  - evidence: not populated. The only structured upstream signal available
    to this adapter (the technical_analyst's rule-based output) is consumed
    internally by run_hedge_fund()'s own graph and not returned to this
    adapter as a separate object; fabricating an EvidenceItem from anything
    else would not be honestly traceable to a native_path.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil.relativedelta import relativedelta

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    OutputScope,
    Q1Action,
    QueryContext,
    TimeWindow,
)

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

# Sign convention for target_position, keyed by the raw 5-way upstream
# action: buy/cover increase or restore long exposure (positive); sell/short
# reduce or open short exposure (negative); hold is a no-op (zero). This is
# the same 5-way -> 3-way collapse as _ACTION_MAP, just signed instead of
# bucketed, so a signed magnitude survives even though BUY/SELL/HOLD alone
# cannot distinguish "cover a short" from "open a new long".
_POSITION_SIGN = {
    "buy": 1.0,
    "cover": 1.0,
    "sell": -1.0,
    "short": -1.0,
    "hold": 0.0,
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

    def __init__(self):
        super().__init__()
        # Cache keyed by (ticker, as_of): one real run_hedge_fund() graph
        # invocation serves both q1_action() and the run() override's
        # native_output capture, so calling both (as BaseAdapter.run() does)
        # never re-runs the real LLM call for the same context.
        self._cache: dict[tuple[str, str], dict] = {}

    def _run(self, ticker: str, date: str) -> dict:
        key = (ticker, date)
        if key in self._cache:
            return self._cache[key]

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

        self._cache[key] = raw
        return raw

    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        if not context.targets:
            raise ValueError("ai_hedge_fund q1_action requires context.targets == [ticker]")
        ticker = context.targets[0]
        date = context.as_of

        raw = self._run(ticker, date)

        raw_action = str(raw.get("action", "hold")).lower()
        action = _ACTION_MAP.get(raw_action, Action.HOLD)

        raw_confidence = raw.get("confidence")
        confidence = None
        if raw_confidence is not None:
            confidence = ConfidenceEstimate(
                value=max(0.0, min(1.0, float(raw_confidence) / 100.0)),
                kind=ConfidenceKind.SELF_REPORTED,
                raw_value=float(raw_confidence),
                method="upstream PortfolioDecision.confidence (int 0-100) / 100",
            )

        raw_quantity = raw.get("quantity")
        target_position = None
        if raw_quantity is not None:
            sign = _POSITION_SIGN.get(raw_action, 0.0)
            target_position = sign * float(raw_quantity)

        reasoning = str(raw.get("reasoning") or "").strip()
        explanation = reasoning if reasoning else None

        return Q1Action(
            context=context,
            action=action,
            target_position=target_position,
            confidence=confidence,
            explanation=explanation,
            bull_case=None,
            bear_case=None,
            evidence=None,
        )

    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window: Optional[TimeWindow] = None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ) -> AdapterResult:
        """
        Overridden solely to attach a faithful `native_output` (the real,
        untouched upstream PortfolioDecision dict for this ticker — action,
        quantity, confidence, reasoning — as parsed from run_hedge_fund()'s
        own JSON response). No business logic changes; context/generation_
        window checks and RunMetadata construction are still done by
        super().run(). Pre-populating self._cache here means the subsequent
        q1_action() call super().run() makes internally reuses this same
        real result instead of invoking the LLM a second time.
        """
        if native_output is None and context.targets:
            native_output = {"decisions": {context.targets[0]: self._run(context.targets[0], context.as_of)}}
        return super().run(
            task_id,
            context,
            generation_window=generation_window,
            native_output=native_output,
            adapter_notes=adapter_notes,
            field_mappings=field_mappings,
            **kwargs,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        result = self.q1_action(context)
        checks["q1_returns_Q1Action"] = result is not None
        checks["action_is_valid"] = result.action in ("BUY", "SELL", "HOLD")
        if result.confidence is not None:
            checks["confidence_in_range"] = 0.0 <= result.confidence.value <= 1.0
        return checks
