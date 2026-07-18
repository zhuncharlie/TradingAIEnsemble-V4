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

Schema v2.0.0 migration notes (this adapter still answers Q1+Q2 only, same
as v1 — no Q3/Q4 claimed; PROJECT_SCHEMA_AUDIT.md §4.1/§5 found this project
has no standalone alpha-score or portfolio-weight concept at all, so those
remain correctly UNSUPPORTED):

  RE-VERIFICATION AGAINST CURRENT VENDOR CODE (the audit explicitly flagged
  that this vendor repo has moved on since this adapter was first written —
  confirmed true): the vendor now produces genuinely typed, structured
  Pydantic output for the three decision-making agents (Portfolio Manager,
  Research Manager, Trader) and the Sentiment Analyst, via
  `with_structured_output` (tradingagents/agents/schemas.py). Concretely:
    - `PortfolioDecision` (managers/portfolio_manager.py) now has:
      `rating` (still the same 5-tier PortfolioRating enum), plus NEW real
      fields `executive_summary`, `investment_thesis`, `price_target:
      float|None`, `time_horizon: str|None`.
    - `SentimentReport` (analysts/sentiment_analyst.py) now has a NEW real
      `confidence: Literal["low","medium","high"]` field (data-quality-based,
      not market-risk-based — see its own docstring) alongside the existing
      `overall_band` (6-tier `SentimentBand`) and `overall_score` (0-10).
  However, none of these structured Pydantic objects are retained in graph
  state — `render_pm_decision()`/`render_sentiment_report()` convert them to
  markdown immediately (managers/portfolio_manager.py, analysts/
  sentiment_analyst.py) and only the rendered markdown string is stored in
  `final_state["final_trade_decision"]` / `final_state["sentiment_report"]`
  (confirmed in graph/trading_graph.py's `_log_state` and `propagate`). So
  this adapter still regex-parses the deterministic rendered header lines
  rather than importing the vendor's schemas module directly — there is no
  lower-loss real alternative available through the graph's public surface
  without monkey-patching upstream internals, which CLAUDE.md forbids.

  - Cost control / analyst selection: TradingAgents' graph *always* runs the
    bull/bear researcher debate, the 3-way risk debate (aggressive/
    conservative/neutral), the Research Manager, Trader, and Portfolio
    Manager regardless of which analysts are enabled — that debate structure
    is the entire point of the framework, unlike ai-hedge-fund where most
    analysts are optional pure-Python nodes. The one knob this adapter pulls
    is `selected_analysts`, restricted to `["social"]` (the sentiment
    analyst) — the cheapest single analyst, and the one Q2 needs anyway.
    `max_debate_rounds` / `max_risk_discuss_rounds` are left at their
    upstream defaults of 1. A single q1_action()/q2_state() call still makes
    on the order of 9-10 real LLM calls (1 sentiment analyst + bull + bear +
    Research Manager + Trader + 3 risk debators + Portfolio Manager) — there
    is no way to get this framework down to ai-hedge-fund's "1 real call"
    without disabling the debate entirely, which would defeat the reason to
    wrap this specific project.
  - One graph run serves both Q1 and Q2: `_run()` caches the
    `(final_state, decision)` result keyed by `(ticker, date)`, so calling
    both q1_action() and q2_state() for the same ticker/date (as
    `BaseAdapter.run()` and the smoke test both do) triggers the expensive
    graph exactly once, not twice. The `run()` override's native_output
    capture reuses this same cache.
  - Action mapping: upstream's 5-tier `PortfolioRating` (Buy / Overweight /
    Hold / Underweight / Sell — see `tradingagents/agents/schemas.py` and
    `tradingagents/agents/utils/rating.py:parse_rating`) is collapsed onto
    our 3-way Action enum: Buy, Overweight -> BUY; Sell, Underweight -> SELL;
    Hold -> HOLD. Unchanged from v1.
  - Q1 confidence: `PortfolioDecision` has no numeric confidence field at
    all (only the 5-tier rating + prose). This adapter maps the tier's
    distance from "Hold" on the 5-point scale to a fixed confidence value:
    Buy/Sell (the two most decisive tiers) -> 0.85, Overweight/Underweight
    (the two hedged tiers) -> 0.65, Hold -> 0.5, wrapped as
    ConfidenceEstimate(kind=ConfidenceKind.HEURISTIC) — HEURISTIC because
    this number is an adapter-computed bucket-by-tier translation, not
    something the model itself reported as a confidence value. Unchanged
    bucketing from v1, just now typed.
  - Q1 explanation: the rendered `final_trade_decision` markdown (Portfolio
    Manager's own executive_summary + investment_thesis). Passed through
    as-is when non-empty; the v1 fallback template string ("X returned
    rating=Y with no further detail") is DELETED per the v2 migration
    rubric — explanation is genuinely optional in v2, so an empty upstream
    render maps to explanation=None (in practice this should be rare since
    executive_summary/investment_thesis are both required, non-optional
    fields on the real PortfolioDecision).
  - Q1 bull_case / bear_case: `final_state["investment_debate_state"]
    ["bull_history"]` / `["bear_history"]` — the actual bull/bear researcher
    debate transcripts upstream produces. Unchanged from v1.
  - Q1 evidence (RECOVERED in this migration): the real
    `PortfolioDecision.time_horizon` and `PortfolioDecision.price_target`
    fields (both genuinely optional upstream, filled only when the LLM
    chooses to) are extracted from their deterministic rendered lines
    (`**Time Horizon**: ...` / `**Price Target**: ...`) and recorded as
    EvidenceItem(kind="time_horizon"/"price_target", ...) when present.
    Q1Action has no dedicated field for either, so EvidenceItem is the
    honest schema-provided home for them rather than dropping them (v1
    parsed time_horizon but had nowhere canonical to put it either, and
    never touched price_target at all — this is a straightforward,
    low-effort recovery of a real field noted in PROJECT_SCHEMA_AUDIT.md).
    Risk-debate content (aggressive/conservative/neutral) has no dedicated
    Q1Action field either (a rejected OPTIONAL_EXTENSION candidate per the
    audit, §9), but RECOVERED in this capability-recovery pass (2026-07) as
    three `EvidenceItem`s (kind="risk_debate_aggressive"/"_conservative"/
    "_neutral") — the real transcript on
    `final_state["risk_debate_state"]["{aggressive,conservative,neutral}_history"]`,
    verified (managers/portfolio_manager.py) to be the direct input the
    Portfolio Manager's own prompt synthesizes into final_trade_decision.
    Previously discarded entirely despite being real and always computed;
    same EvidenceItem container already used for time_horizon/price_target.
  - Q2 sentiment: the Sentiment Analyst's structured `SentimentReport`
    reports `overall_score` on a 0-10 scale (0=max bearish, 10=max bullish)
    rendered as a markdown header
    (`**Overall Sentiment:** **{band}** (Score: {score}/10)`) on top of a
    prose `narrative` — this adapter regex-parses that deterministic header
    and linearly rescales the 0-10 score to [-1,1] via `(score-5)/5`
    (arithmetic rescaling of a real upstream number, not a re-derivation).
    Mapped to `StateEstimate(dimension="sentiment", value_numeric=...,
    value_category=overall_band, ...)` — `value_category` is the real
    6-tier band string (e.g. "Mildly Bullish"), preserved verbatim instead
    of being discarded as it was in v1 (v1 only kept the rescaled numeric
    score and the separately-invented risk_level bucket).
  - Q2 confidence (RECOVERED — vendor added this field since v1 was
    written): `SentimentReport.confidence` (low/medium/high, based on data
    quality/sample size per its own docstring — NOT a market-risk read) is
    extracted from its deterministic rendered line (`**Confidence:**
    Low/Medium/High`) and mapped to ConfidenceEstimate(kind=
    ConfidenceKind.SELF_REPORTED, method=...) with a disclosed low/medium/
    high -> {0.3, 0.6, 0.9} bucket. SELF_REPORTED because, unlike Q1's
    adapter-invented tier bucket, this is the model's own reported
    assessment of its own output quality — an adapter bucketing choice
    only in the categorical-to-float step, not in what the value means. If
    the header line is absent (e.g. a free-text fallback response with no
    deterministic structure), confidence is left None rather than guessed.
  - `risk_level` (DELETED per migration rubric): v1 invented a market-risk
    bucket as a function of `|overall_score - 5|` because TradingAgents has
    no native risk-level concept and v1's schema forced a `RiskLevel` enum.
    v2's open-vocabulary `StateEstimate.dimension` does not need this
    workaround, and the migration rubric explicitly calls out this kind of
    invented-field-to-satisfy-a-forced-enum pattern for deletion. It is not
    replaced by anything — there is no real upstream field this maps to
    (unlike FinGPT's dispersion statistic, this was pure adapter invention,
    not a real statistic computed over real numbers, so there is nothing
    honest left to preserve under a different name).
  - Q2 evidence: the sentiment analyst deterministically pre-fetches exactly
    three sources every run (tradingagents/agents/analysts/
    sentiment_analyst.py): Yahoo Finance news, StockTwits, and Reddit. That
    fixed, code-verified list is recorded as
    EvidenceItem(kind="data_source", value=...) per source — the same real
    fact v1's `sources` field carried, now in the schema's evidence
    container instead of a bespoke field.
  - Q2 explanation: the full rendered `sentiment_report` text (deterministic
    header + real narrative) is passed through verbatim. v1's
    `_extract_drivers()` heuristic (mechanically splitting the narrative
    into "top lines" to fake a `drivers: List[str]` field) is DELETED per
    the migration rubric — the real narrative field itself is now
    accessible as a whole, richer and lower-loss than a heuristic top-5-
    lines extraction, so there is no reason to keep the extraction hack.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    EvidenceItem,
    OutputScope,
    Q1Action,
    Q2State,
    QueryContext,
    StateEstimate,
    TimeWindow,
)

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

# SentimentReport.confidence (low/medium/high) -> a disclosed float bucket.
# This is the model's OWN reported confidence in its assessment (data
# quality/sample size, per SentimentReport's docstring) — an adapter
# bucketing choice only in the categorical->float step, hence
# ConfidenceKind.SELF_REPORTED rather than HEURISTIC.
_SENTIMENT_CONFIDENCE_MAP = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.9,
}

_SENTIMENT_HEADER_RE = re.compile(
    r"\*\*Overall Sentiment:\*\*\s*\*\*([^*]+)\*\*\s*\(Score:\s*([\d.]+)/10\)",
    re.IGNORECASE,
)
_SENTIMENT_CONFIDENCE_RE = re.compile(
    r"\*\*Confidence:\*\*\s*(\w+)",
    re.IGNORECASE,
)
_TIME_HORIZON_RE = re.compile(r"\*\*Time Horizon\*\*:\s*(.+)", re.IGNORECASE)
_PRICE_TARGET_RE = re.compile(r"\*\*Price Target\*\*:\s*([\d.]+)", re.IGNORECASE)

_DEFAULT_SOURCES = ["Yahoo Finance news", "StockTwits", "Reddit"]


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
    # Q1 — Buy / Sell / Hold action
    # ------------------------------------------------------------------
    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        if not context.targets:
            raise ValueError("tradingagents q1_action requires context.targets == [ticker]")
        ticker = context.targets[0]
        date = context.as_of

        final_state, decision = self._run(ticker, date)

        raw_rating = str(decision or "hold").strip().lower()
        action = _ACTION_MAP.get(raw_rating, Action.HOLD)
        confidence = ConfidenceEstimate(
            value=_CONFIDENCE_MAP.get(raw_rating, 0.5),
            kind=ConfidenceKind.HEURISTIC,
            method=(
                "bucket-by-tier mapping of the 5-tier PortfolioDecision.rating "
                "distance from Hold: Buy/Sell=0.85, Overweight/Underweight=0.65, "
                "Hold=0.5 (adapter-invented bucket over a real categorical rating, "
                "not a native upstream confidence value)"
            ),
        )

        rendered_decision = str(final_state.get("final_trade_decision") or "").strip()
        explanation = rendered_decision if rendered_decision else None

        debate = final_state.get("investment_debate_state") or {}
        bull_case = str(debate.get("bull_history") or "").strip() or None
        bear_case = str(debate.get("bear_history") or "").strip() or None

        evidence = []
        m_horizon = _TIME_HORIZON_RE.search(rendered_decision)
        if m_horizon:
            evidence.append(EvidenceItem(kind="time_horizon", value=m_horizon.group(1).strip()))
        m_price = _PRICE_TARGET_RE.search(rendered_decision)
        if m_price:
            evidence.append(EvidenceItem(kind="price_target", value=m_price.group(1).strip()))

        # Recovered (previously discarded, category 2 — real, always computed,
        # never surfaced anywhere): the 3-way risk debate (aggressive/
        # conservative/neutral) is a real transcript on
        # final_state["risk_debate_state"], the direct input the Portfolio
        # Manager synthesizes into final_trade_decision (verified in
        # managers/portfolio_manager.py: prompt includes
        # `state["risk_debate_state"]["history"]`). There is no dedicated
        # Q1Action field for it (same as v1/the prior audit found), but
        # EvidenceItem is a real, general-purpose container already used the
        # same way for bull_case/bear_case's sibling debate — so it is no
        # longer dropped.
        risk_debate = final_state.get("risk_debate_state") or {}
        for key, kind in (
            ("aggressive_history", "risk_debate_aggressive"),
            ("conservative_history", "risk_debate_conservative"),
            ("neutral_history", "risk_debate_neutral"),
        ):
            text = str(risk_debate.get(key) or "").strip()
            if text:
                evidence.append(EvidenceItem(
                    kind=kind,
                    value=text,
                    source="TradingAgents risk_debate_state (real aggressive/conservative/neutral risk-debator transcript, verified read directly by managers/portfolio_manager.py's own prompt)",
                ))

        return Q1Action(
            context=context,
            action=action,
            confidence=confidence,
            explanation=explanation,
            bull_case=bull_case,
            bear_case=bear_case,
            evidence=evidence or None,
        )

    # ------------------------------------------------------------------
    # Q2 — Sentiment state
    # ------------------------------------------------------------------
    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        if not context.targets:
            raise ValueError("tradingagents q2_state requires context.targets == [ticker]")
        ticker = context.targets[0]
        date = context.as_of

        final_state, _decision = self._run(ticker, date)

        sentiment_text = str(final_state.get("sentiment_report") or "")
        m = _SENTIMENT_HEADER_RE.search(sentiment_text)
        band = m.group(1).strip() if m else None
        score_0_10 = float(m.group(2)) if m else 5.0
        sentiment_value = max(-1.0, min(1.0, (score_0_10 - 5.0) / 5.0))

        confidence = None
        m_conf = _SENTIMENT_CONFIDENCE_RE.search(sentiment_text)
        if m_conf:
            level = m_conf.group(1).strip().lower()
            if level in _SENTIMENT_CONFIDENCE_MAP:
                confidence = ConfidenceEstimate(
                    value=_SENTIMENT_CONFIDENCE_MAP[level],
                    kind=ConfidenceKind.SELF_REPORTED,
                    method=(
                        f"upstream SentimentReport.confidence ({level}, based on data "
                        "quality/sample size per upstream's own docstring) mapped to "
                        "{low:0.3, medium:0.6, high:0.9}"
                    ),
                )

        evidence = [EvidenceItem(kind="data_source", value=src) for src in _DEFAULT_SOURCES]

        sentiment_state = StateEstimate(
            dimension="sentiment",
            value_numeric=sentiment_value,
            value_category=band,
            scale="[-1,1], linearly rescaled from real upstream 0-10 overall_score via (score-5)/5",
            confidence=confidence,
            evidence=evidence,
        )

        return Q2State(
            context=context,
            states=[sentiment_state],
            explanation=sentiment_text or None,
        )

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output, reusing the same
    # cached graph run q1_action()/q2_state() will use.
    # ------------------------------------------------------------------
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
        if native_output is None and context.targets:
            ticker = context.targets[0]
            date = context.as_of
            final_state, decision = self._run(ticker, date)
            # final_state contains LangGraph message objects that are not
            # JSON-serializable as-is; preserve the real fields this adapter
            # actually reads faithfully rather than dumping the whole graph
            # state (which is the same faithful-representation approach
            # ai_hedge_fund_adapter.py and fingpt_adapter.py use for their
            # own non-trivially-serializable upstream returns).
            native_output = {
                "ticker": ticker,
                "date": date,
                "decision": decision,
                "final_trade_decision": final_state.get("final_trade_decision"),
                "sentiment_report": final_state.get("sentiment_report"),
                "investment_debate_state": {
                    "bull_history": (final_state.get("investment_debate_state") or {}).get("bull_history"),
                    "bear_history": (final_state.get("investment_debate_state") or {}).get("bear_history"),
                },
            }
        return super().run(
            task_id,
            context,
            generation_window=generation_window,
            native_output=native_output,
            adapter_notes=adapter_notes,
            field_mappings=field_mappings,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Smoke test (real calls — TradingAgents' debate architecture means
    # this necessarily makes ~9-10 real LLM calls, not 1; see header)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

        q1 = self.q1_action(context)
        checks["q1_returns_Q1Action"] = q1 is not None
        checks["action_is_valid"] = q1.action in ("BUY", "SELL", "HOLD")
        checks["bull_case_populated"] = bool(q1.bull_case)
        checks["bear_case_populated"] = bool(q1.bear_case)
        # Recovered-capability check: real risk-debate transcript should now
        # surface as evidence (at least one of the 3 debator kinds).
        checks["q1_evidence_includes_risk_debate"] = any(
            (e.kind or "").startswith("risk_debate_") for e in (q1.evidence or [])
        )

        # Same context as above -> hits the _run() cache, no second real
        # graph execution.
        q2 = self.q2_state(context)
        checks["q2_returns_Q2State"] = q2 is not None
        checks["states_non_empty"] = len(q2.states) >= 1
        sentiment = next((s for s in q2.states if s.dimension == "sentiment"), None)
        checks["sentiment_state_present"] = sentiment is not None
        if sentiment is not None and sentiment.value_numeric is not None:
            checks["sentiment_value_in_range"] = -1.0 <= sentiment.value_numeric <= 1.0

        return checks
