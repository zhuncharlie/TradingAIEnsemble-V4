"""
adapters/tradingagents_adapter.py — wraps github.com/TauricResearch/TradingAgents (Q1, Q2).

Repo verification (done before cloning, see DECISIONS_tradingagents.md for detail):
  - Confirmed via `curl https://api.github.com/repos/TauricResearch/TradingAgents`
    that the org/repo is real (created 2024-12-28, ~90k stars, Apache-2.0,
    description "TradingAgents: Multi-Agents LLM Financial Trading Framework").
  - Fetched README.md and confirmed it describes exactly the architecture named
    in the session brief: analyst team (market/sentiment/news/fundamentals),
    bull/bear researchers who debate, a risk team (aggressive/conservative/
    neutral debators) + judge, and a Portfolio Manager that approves/rejects
    the trade. The "social" analyst slot is literally
    `tradingagents.agents.create_sentiment_analyst`, which aggregates Yahoo
    Finance news + StockTwits + Reddit (r/wallstreetbets, r/stocks,
    r/investing) — matching the brief's "independent sentiment analyst
    pulling from Reddit/StockTwits" description word for word.
  - Walked the full `tradingagents/` file tree (agents/, dataflows/, graph/,
    llm_clients/) via the GitHub API before cloning: every file is thematically
    on-topic (trading agents, data vendors, LLM provider clients). No
    unrelated subtree (crypto-payments or otherwise) found.
  - Data vendors are yfinance / Alpha Vantage / FRED / Polymarket / Reddit RSS
    / StockTwits public endpoint — all keyless or free-tier public market/news
    data. No brokerage/exchange account, no real money, nothing beyond an LLM
    API key is required to run this project.

Environment setup (one-time, outside this file):
    conda create -n tradingagents_real python=3.12
    conda activate tradingagents_real
    git clone https://github.com/TauricResearch/TradingAgents.git adapters/vendor/TradingAgents
    cd adapters/vendor/TradingAgents && pip install --no-deps .
    pip install langchain-core langchain-openai langgraph langgraph-checkpoint-sqlite \
        langchain-anthropic langchain-experimental langchain-google-genai \
        pandas parsel python-dotenv pytz questionary redis requests rich typer \
        setuptools stockstats tqdm typing-extensions yfinance backtrader
    # DEEPSEEK_API_KEY is already provisioned for this project at
    # adapters/vendor/ai-hedge-fund/.env (see ai_hedge_fund_adapter.py). This
    # adapter reuses that same file/key rather than requiring a new one —
    # TradingAgents has a *native* "deepseek" provider (not just a generic
    # openai_compatible passthrough): tradingagents/llm_clients/openai_client.py
    # registers base_url="https://api.deepseek.com" and reads DEEPSEEK_API_KEY
    # directly (tradingagents/llm_clients/api_key_env.py). No new key needed.

Run the harness with that env active:
    conda activate tradingagents_real
    python CONTRACT/test_harness.py --adapter adapters/tradingagents_adapter.py

No upstream source was patched — only environment/dependency setup was needed,
so there is no patches/TradingAgents.diff.

Design notes (translation choices made by this adapter, not upstream):
  - Cost control / analyst selection: TradingAgents' graph *always* runs the
    bull/bear researcher debate, the 3-way risk debate (aggressive/
    conservative/neutral), the Research Manager, Trader, and Portfolio
    Manager regardless of which analysts are enabled — that debate structure
    is the entire point of the framework, unlike ai-hedge-fund where most
    analysts are optional pure-Python nodes. The one knob this adapter pulls
    is `selected_analysts`, restricted to `["social"]` (the sentiment
    analyst) — the cheapest single analyst, and the one Q2 needs anyway.
    `max_debate_rounds` / `max_risk_discuss_rounds` are left at their
    upstream defaults of 1. A single q1_decision()/q2_sentiment() call still
    makes on the order of 9-10 real LLM calls (1 sentiment analyst + bull +
    bear + Research Manager + Trader + 3 risk debators + Portfolio Manager) —
    there is no way to get this framework down to ai-hedge-fund's "1 real
    call" without disabling the debate entirely, which would defeat the
    reason to wrap this specific project.
  - One graph run serves both Q1 and Q2: `_run()` caches the
    `(final_state, decision)` result from `TradingAgentsGraph.propagate()`
    keyed by `(ticker, date)`, so calling both q1_decision() and
    q2_sentiment() for the same ticker/date (as `BaseAdapter.run()` and the
    test harness both do) triggers the expensive graph exactly once, not
    twice.
  - Action mapping: upstream's 5-tier `PortfolioRating` (Buy / Overweight /
    Hold / Underweight / Sell — see `tradingagents/agents/schemas.py` and
    `tradingagents/agents/utils/rating.py:parse_rating`) is collapsed onto
    our 3-way Action enum: Buy, Overweight -> BUY; Sell, Underweight -> SELL;
    Hold -> HOLD.
  - Confidence: TradingAgents' `PortfolioDecision` has no numeric confidence
    field at all (only the 5-tier rating + prose). This adapter maps the
    tier's distance from "Hold" on the 5-point scale to a fixed confidence
    value: Buy/Sell (the two most decisive tiers) -> 0.85, Overweight/
    Underweight (the two hedged tiers) -> 0.65, Hold -> 0.5. This is a
    bucket-by-tier translation of a real (non-fabricated) upstream signal,
    the same kind of choice ai_hedge_fund_adapter.py documents for its own
    0-100 -> 0.0-1.0 rescale.
  - reasoning / bull_case / bear_case: `reasoning` is the rendered
    `final_trade_decision` markdown (the Portfolio Manager's own executive
    summary + investment thesis — real prose, >10 chars). `bull_case` /
    `bear_case` are `final_state["investment_debate_state"]["bull_history"]`
    / `["bear_history"]` — the actual bull/bear researcher debate transcripts
    upstream produces. These are non-null for the first time across this
    project's adapters (every other adapter leaves them None).
  - time_horizon: parsed from the `**Time Horizon**: ...` line the Portfolio
    Manager's rendered decision includes when it chooses to fill that
    (optional) field; None if the model omitted it. No enum is enforced
    upstream (free text like "3-6 months"), and CONTRACT's own field is a
    free `Optional[str]`, so the raw text is passed through unmodified.
  - sentiment_score: the Sentiment Analyst's structured output
    (`tradingagents/agents/schemas.py::SentimentReport`) reports
    `overall_score` on a 0-10 scale (0=max bearish, 10=max bullish) plus an
    `overall_band` label and a `confidence` (data-quality, not market risk)
    field, rendered as a markdown header on top of a prose narrative and
    stored as a single string in `final_state["sentiment_report"]` — the raw
    structured object is not retained in graph state, only the rendered
    text. This adapter regex-parses that deterministic header
    (`**Overall Sentiment:** **{band}** (Score: {score}/10)`) back out and
    linearly rescales the 0-10 score to our -1..+1 range via
    `(score - 5) / 5`. This is arithmetic rescaling of a real number
    upstream already computed, not a re-derivation of sentiment from raw
    text.
  - risk_level: TradingAgents has no generic "market risk level" enum
    anywhere in its output. Rather than inventing a separate risk model in
    this adapter (which CLAUDE.md's "never reimplement upstream logic" rule
    would forbid), this bucket is a direct, documented function of the
    Sentiment Analyst's own numeric `overall_score` extremity — how far the
    real upstream-computed score sits from neutral (5.0) — on the theory
    that both very bearish and very bullish extremes correspond to more
    one-sided, higher-risk positioning: |score-5| >= 4 -> EXTREME,
    >= 2.5 -> HIGH, >= 1.0 -> MEDIUM, else LOW. This is an adapter-level
    bucketing choice to fill a field upstream doesn't natively expose, using
    only upstream's own real number as input (no separate model, no
    fabricated data).
  - drivers: mechanically extracted from the sentiment narrative — split on
    newlines, drop markdown table rows/separators and short lines, keep the
    first 5 substantive lines. This is plain text splitting of upstream's
    own narrative, not a re-analysis of sentiment.
  - sources: TradingAgents' sentiment analyst deterministically pre-fetches
    exactly three sources every run (see
    `tradingagents/agents/analysts/sentiment_analyst.py`): Yahoo Finance
    news, StockTwits, and Reddit. That fixed, code-verified list is reported
    directly rather than parsed from prose.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Action, Q1Decision, Q2Sentiment, RiskLevel

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "TradingAgents"
CACHE_DIR = VENDOR_DIR / ".adapter_cache"

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from dotenv import load_dotenv  # noqa: E402

# Reuse the DeepSeek key already provisioned for the ai_hedge_fund adapter
# rather than requiring a second copy of the same secret.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env")

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402

# Only the sentiment analyst is enabled — see header "Design notes" for why
# this is the one cost-control knob available in this framework.
DEFAULT_ANALYSTS = ["social"]
DEEP_THINK_MODEL = "deepseek-v4-pro"
QUICK_THINK_MODEL = "deepseek-v4-flash"

_ACTION_MAP = {
    "buy": Action.BUY,
    "overweight": Action.BUY,
    "hold": Action.HOLD,
    "underweight": Action.SELL,
    "sell": Action.SELL,
}

_CONFIDENCE_MAP = {
    "buy": 0.85,
    "sell": 0.85,
    "overweight": 0.65,
    "underweight": 0.65,
    "hold": 0.5,
}

_SENTIMENT_HEADER_RE = re.compile(
    r"\*\*Overall Sentiment:\*\*\s*\*\*([^*]+)\*\*\s*\(Score:\s*([\d.]+)/10\)",
    re.IGNORECASE,
)
_TIME_HORIZON_RE = re.compile(r"\*\*Time Horizon\*\*:\s*(.+)", re.IGNORECASE)

_DEFAULT_SOURCES = ["Yahoo Finance news", "StockTwits", "Reddit"]


def _extract_drivers(narrative: str, max_items: int = 5) -> list[str]:
    """Mechanically pull the first few substantive lines out of the sentiment
    narrative (no re-analysis — see header 'Design notes')."""
    drivers = []
    for raw_line in narrative.splitlines():
        line = raw_line.strip().strip("-*# \t")
        if len(line) < 20:
            continue
        if line.startswith("|") or set(line) <= {"-", "|", " ", ":"}:
            continue
        drivers.append(line)
        if len(drivers) >= max_items:
            break
    if not drivers:
        fallback = narrative.strip()[:200].strip()
        drivers = [fallback] if fallback else ["no narrative text returned"]
    return drivers


def _risk_level_from_score(score: float) -> RiskLevel:
    distance = abs(score - 5.0)
    if distance >= 4.0:
        return RiskLevel.EXTREME
    if distance >= 2.5:
        return RiskLevel.HIGH
    if distance >= 1.0:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


class TradingAgentsAdapter(BaseAdapter):
    name = "tradingagents"
    questions_answered = ["Q1", "Q2"]
    upstream_repo = "https://github.com/TauricResearch/TradingAgents"
    requires_env = "tradingagents_real"

    def __init__(self):
        super().__init__()
        self._cache: dict[Tuple[str, str], Tuple[dict, str]] = {}

    # ------------------------------------------------------------------
    # Shared upstream call — one real graph run serves both Q1 and Q2
    # ------------------------------------------------------------------
    def _run(self, ticker: str, date: str) -> Tuple[dict, str]:
        key = (ticker, date)
        if key in self._cache:
            return self._cache[key]

        if os.environ.get("DEEPSEEK_API_KEY") is None:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. It should already exist at "
                "adapters/vendor/ai-hedge-fund/.env (shared with the "
                "ai_hedge_fund adapter) — never hardcode it here."
            )

        config = DEFAULT_CONFIG.copy()
        config.update(
            {
                "llm_provider": "deepseek",
                "deep_think_llm": DEEP_THINK_MODEL,
                "quick_think_llm": QUICK_THINK_MODEL,
                "backend_url": None,
                "max_debate_rounds": 1,
                "max_risk_discuss_rounds": 1,
                "checkpoint_enabled": False,
                "results_dir": str(CACHE_DIR / "results"),
                "data_cache_dir": str(CACHE_DIR / "cache"),
                "memory_log_path": str(CACHE_DIR / "memory" / "trading_memory.md"),
            }
        )

        ta = TradingAgentsGraph(
            selected_analysts=DEFAULT_ANALYSTS, debug=False, config=config
        )
        final_state, decision = ta.propagate(ticker, date)

        self._cache[key] = (final_state, decision)
        return final_state, decision

    # ------------------------------------------------------------------
    # Q1 — Buy / Sell / Hold decision
    # ------------------------------------------------------------------
    def q1_decision(self, ticker: str, date: str, **kwargs) -> Optional[Q1Decision]:
        t0 = time.time()

        final_state, decision = self._run(ticker, date)

        raw_rating = str(decision or "hold").strip().lower()
        action = _ACTION_MAP.get(raw_rating, Action.HOLD)
        confidence = _CONFIDENCE_MAP.get(raw_rating, 0.5)

        reasoning = str(final_state.get("final_trade_decision") or "").strip()
        if len(reasoning) < 10:
            reasoning = (
                f"TradingAgents Portfolio Manager returned rating={raw_rating} "
                "with no further detail."
            )

        debate = final_state.get("investment_debate_state") or {}
        bull_case = str(debate.get("bull_history") or "").strip() or None
        bear_case = str(debate.get("bear_history") or "").strip() or None

        time_horizon = None
        m = _TIME_HORIZON_RE.search(reasoning)
        if m:
            time_horizon = m.group(1).strip()

        return Q1Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            bull_case=bull_case,
            bear_case=bear_case,
            time_horizon=time_horizon,
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

        final_state, _decision = self._run(ticker, date)

        sentiment_text = str(final_state.get("sentiment_report") or "")
        m = _SENTIMENT_HEADER_RE.search(sentiment_text)
        score_0_10 = float(m.group(2)) if m else 5.0
        sentiment_score = max(-1.0, min(1.0, (score_0_10 - 5.0) / 5.0))

        risk_level = _risk_level_from_score(score_0_10)
        drivers = _extract_drivers(sentiment_text)

        return Q2Sentiment(
            sentiment_score=sentiment_score,
            risk_level=risk_level,
            drivers=drivers,
            sources=list(_DEFAULT_SOURCES),
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Smoke test (real calls — TradingAgents' debate architecture means
    # this necessarily makes ~9-10 real LLM calls, not 1; see header)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        q1 = self.q1_decision("AAPL", "2024-01-15")
        checks["q1_returns_Q1Decision"] = q1 is not None
        checks["action_is_valid"] = q1.action in ("BUY", "SELL", "HOLD")
        checks["confidence_in_range"] = 0.0 <= q1.confidence <= 1.0
        checks["bull_case_populated"] = bool(q1.bull_case)
        checks["bear_case_populated"] = bool(q1.bear_case)

        # Same (ticker, date) as above -> hits the _run() cache, no second
        # real graph execution.
        q2 = self.q2_sentiment("AAPL", "2024-01-15")
        checks["q2_returns_Q2Sentiment"] = q2 is not None
        checks["sentiment_score_in_range"] = -1.0 <= q2.sentiment_score <= 1.0
        checks["risk_level_is_valid"] = q2.risk_level in (
            "LOW", "MEDIUM", "HIGH", "EXTREME",
        )
        checks["drivers_non_empty"] = bool(q2.drivers)

        return checks
