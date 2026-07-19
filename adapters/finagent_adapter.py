"""
adapters/finagent_adapter.py — wraps github.com/DVampire/FinAgent (Q1 + Q4).

Repo: real clone at adapters/vendor/FinAgent, commit 17248a0b (2024-08-31).

============================================================================
Why FinAgent (of the 3 Batch-A LLM-agent projects) is the one that can
honestly support Q4 weights
============================================================================
Verified by reading finagent/environment/trading.py directly:
`EnvironmentTrading` tracks `self.cash`, `self.position` (a scalar int —
single-asset), and `self.value = self.cash + self.position * price`
real-time, and its real per-step info dict explicitly returns
`"value"`/`"cash"`/`"position"` (trading.py:175-177, 277-279). This is
NATIVE, real, upstream-tracked state — cleanly, honestly derivable into
`target_weights = {ticker: position*price/value, "CASH": cash/value}`
(DERIVED, since the weight-fraction framing is this adapter's own
transformation, but the underlying cash/position/value are NATIVE). No
shorting or leverage is possible: `eval_buy_position()` caps buy size by
`cash/price`, `eval_sell_position()` caps sell size by current `position`
(trading.py:189-227) — verified by reading the full buy()/sell()/step()
methods; `constraints=PortfolioConstraints(long_only=True, cash_allowed=True)`
reflects this real, code-verified guarantee.

Contrast with FinMem (separate adapter, separate fork): FinMem's own
`Portfolio` class has no cash field at all (only a ±1/0 share-direction
counter), so target_weights cannot be derived there.

============================================================================
A real, pre-existing look-ahead in EnvironmentTrading.get_state() — fixed
at the adapter's configuration boundary, not by touching upstream
============================================================================
`get_state()` (trading.py) builds its observation window as
`[self.day - look_back_days, self.day + look_forward_days]` — i.e. by
default (the project's own shipped `configs/exp/trading/AAPL.py` sets
`look_forward_days = long_term_next_date_range = 14`) every real state
observation includes 14 days of *future* price/news data relative to the
decision day. This is a genuine, pre-existing upstream characteristic (not
introduced by this adapter), presumably intended for the agent to reason
about known future events (e.g. earnings dates) in the original research
setting — but it is a real causality violation for this harness's
"information_cutoff <= timestamp" requirement if used as-is.

Fix: this adapter always constructs `EnvironmentTrading` with
`look_forward_days=0` — a real, exposed constructor parameter (not a code
edit), which makes `get_state()`'s window `[day-look_back_days, day]`
inclusive of only the current and past days. Verified: with
`look_forward_days=0`, `days_future = self.prices_df.index[min(self.day+0,
len-1)]` = the current day itself, so no future date is ever included.
Disclosed here rather than silently deviating from the shipped config.

============================================================================
A real, verified infrastructure limitation: the reflection/memory pipeline
requires an embeddings-capable API this project's only available credential
(DeepSeek) does not provide — BLOCKED, not routed around
============================================================================
FinAgent's full decision pipeline (as driven by tools/main.py, the
project's own real entry point) is: latest/past market-intelligence
summary -> low-level reflection -> high-level reflection -> decision, each
a real LLM call, with the reflection stages retrieving relevant past
entries from a real vector memory (`finagent/query/diverse_query.py`,
class `DiverseQuery`). Verified by reading `DiverseQuery.diverse_query()`
(diverse_query.py:21-41): it calls `self.provider.embed_query(query_text)`
UNCONDITIONALLY on every query, including against a completely empty/fresh
memory (there is no size check before the embed call). `OpenAIProvider`
(finagent/provider/provider.py) uses the real `openai.OpenAI` Python SDK,
which supports DeepSeek-routing via a real, documented, unmodified SDK
mechanism (setting `OPENAI_BASE_URL` in the environment before
construction, since `self.client = OpenAI(api_key=key)` at provider.py:97
passes no explicit `base_url` and the SDK falls back to that env var) — and
this genuinely works for real chat completions (verified live, see the
adapter's live-run report). But DeepSeek's API is chat-completions-only; it
has no `/embeddings` endpoint, so any real call into `embed_query()` fails.
This project's only legitimately available credential in this sandbox is
DEEPSEEK_API_KEY (read from adapters/vendor/ai-hedge-fund/.env, the same
key several sibling adapters in this repo already reuse) — no embeddings-
capable key is available, and this adapter does not go looking for one
beyond that single established path.

Resolution (disclosed, not fabricated): this adapter calls the real,
unmodified `finagent.prompt.trading.decision.DecisionTrading` class
directly — the same real class, real `check_keys=["action","reasoning"]`
backoff-validated call, real DeepSeek completion — but supplies an honest,
literal disclosure string (not a fabricated summary) for the 6 template
placeholders that would otherwise be filled by the blocked reflection
stages (`past_market_intelligence_summary`, `latest_market_intelligence_summary`,
`past_low_level_reflection`, `latest_low_level_reflection`,
`past_high_level_reflection`, `latest_high_level_reflection`). Verified via
the real template files (res/prompts/template/valid/trading/decision.html
and its `res/prompts/module/trading/*.html` iframe includes) that the
OTHER real inputs this call needs — real per-step `price`/`cash`/`position`/
`total_profit`/`total_return` from `EnvironmentTrading`, and real static
per-ticker metadata from `res/prompts/asset_infos/exp_stocks.json` (ships
with the repo, includes AAPL) — do NOT require the memory/reflection
subsystem at all. This is a real, reduced-scope, but still real and
unmodified upstream call: the memory/reflection layer is precisely
BLOCKED (infrastructure/credential-missing, not "no public interface" —
the interface is public, the required embeddings backend is simply
unavailable here) and is never faked or routed around.

============================================================================
Design notes
============================================================================
  - Single-asset scope only (EnvironmentTrading.position is a scalar int).
  - `q1_action`: one real decision at `context.as_of`, using real
    environment state at that day plus the honest reflection-disclosure
    above; `Q1Action.explanation` carries the real model reasoning.
  - `q4_policy`: drives the real environment causally, day by day, across
    the harness-supplied `generation_window` (kept short in the default
    smoke test — every step is a real, metered DeepSeek call), building one
    real `PolicyDecisionStep` per real trading day, with
    `information_cutoff` fixed to that day's date (look_forward_days=0
    proves no later information is used) and strictly increasing
    `timestamp`s. `policy_type=ONLINE_ADAPTIVE_POLICY` (a fresh real LLM
    decision, from real current environment state, every step; no frozen
    model, no persisted training).
  - `generation_window` is read-only: echoed back exactly as supplied,
    never widened/narrowed by this adapter (enforced by
    CONTRACT/base_adapter.py's AdapterContractViolation check).
  - No Q5/return/Sharpe/drawdown anywhere in this file.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    DecisionPolicy,
    ObservationPolicy,
    OutputScope,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q1Action,
    Q4Policy,
    QueryContext,
    TimeWindow,
    UniversePolicy,
    UpdateMode,
    UpdatePolicy,
)
from harness.q4_protocol import MarketObservation, PortfolioState, Q4FinalizeSummary, Q4RunConfig

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "FinAgent"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Reuse the DeepSeek key already provisioned for ai_hedge_fund_adapter.py —
# the only credential legitimately available for this repo. Not searched
# for elsewhere.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env")

COMP_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
LOOK_BACK_DAYS = 5           # trading days of real observation lookback
LOOK_FORWARD_DAYS = 0        # causality fix — see module header
DATA_FETCH_BUFFER_DAYS = 20  # extra calendar days fetched before start_date to clear LOOK_BACK_DAYS warm-up
INITIAL_AMOUNT = 1e4
TRANSACTION_COST_PCT = 1e-3
TRADER_PREFERENCE = "moderate_trader"  # a real trader-persona file shipped in res/prompts/trader/

_RELECTION_DISCLOSURE = (
    "Not computed for this run. FinAgent's real memory/reflection subsystem "
    "(market-intelligence summary + low-level + high-level reflection) "
    "requires an embeddings-capable LLM API call "
    "(finagent.query.DiverseQuery.diverse_query -> provider.embed_query(), "
    "called unconditionally even against an empty memory). The only "
    "credential available to this adapter (DeepSeek) is chat-completions-"
    "only and has no /embeddings endpoint, so this stage is honestly "
    "skipped rather than faked. Base this decision only on the real "
    "current price/cash/position/return state below."
)


def _ticker_from_context(context: QueryContext) -> str:
    if context.targets:
        return context.targets[0]
    if context.universe:
        return context.universe[0]
    raise ValueError("finagent_adapter requires context.targets or context.universe with 1 ticker (single-asset only).")


def _asset_info(ticker: str) -> dict:
    """Real, shipped per-ticker metadata (res/prompts/asset_infos/*.json)."""
    for fname in ("exp_stocks.json", "dj30.json"):
        path = VENDOR_DIR / "res" / "prompts" / "asset_infos" / fname
        if path.exists():
            data = json.loads(path.read_text())
            if ticker in data:
                return data[ticker]
    return {
        "name": ticker, "symbol": ticker, "exchange": "UNKNOWN",
        "sector": "UNKNOWN", "industry": "UNKNOWN", "description": f"{ticker} (metadata not found in shipped asset_infos)",
    }


def _fetch_and_write_dataset(ticker: str, start_date: str, end_date: str, root: Path) -> Path:
    """
    Real yfinance OHLCV + real yfinance news headlines, written into the
    exact parquet/txt layout finagent.data.dataset.Dataset expects
    (finagent/data/dataset.py: _load_prices/_load_news/_init_assets).
    This is adapter-side data-prep glue (same category as e.g.
    finrl_adapter.py's rolling-covariance construction) — not a
    modification of Dataset/EnvironmentTrading themselves.
    """
    import yfinance as yf

    fetch_start = (pd.Timestamp(start_date) - pd.Timedelta(days=DATA_FETCH_BUFFER_DAYS)).strftime("%Y-%m-%d")
    fetch_end = (pd.Timestamp(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    hist = yf.Ticker(ticker).history(start=fetch_start, end=fetch_end, interval="1d", auto_adjust=False)
    if hist.empty:
        raise RuntimeError(f"yfinance returned no OHLCV history for {ticker} [{fetch_start},{fetch_end})")
    hist = hist.reset_index()
    price_df = pd.DataFrame({
        "timestamp": pd.to_datetime(hist["Date"]).dt.tz_localize(None),
        "open": hist["Open"].astype(float),
        "high": hist["High"].astype(float),
        "low": hist["Low"].astype(float),
        "close": hist["Close"].astype(float),
        "adj_close": hist["Adj Close"].astype(float),
        "volume": hist["Volume"].astype(float),
    })

    # Real yfinance headlines (same source/method as fingpt_adapter.py /
    # ai_hedge_fund_adapter.py) — yfinance only exposes *current* latest
    # headlines, not an arbitrary historical date's headlines; honestly
    # may be empty for a backdated window (real limitation, not faked).
    raw_news = yf.Ticker(ticker).news or []
    rows = []
    for item in raw_news:
        content = item.get("content") or {}
        title = content.get("title")
        if not title:
            continue
        pub = content.get("pubDate") or content.get("displayTime")
        try:
            ts = pd.Timestamp(pub).tz_localize(None) if pub else pd.Timestamp(end_date)
        except Exception:
            ts = pd.Timestamp(end_date)
        rows.append({
            "timestamp": ts,
            "type": "news",
            "source": "Yahoo Finance",
            "title": title,
            "text": (content.get("summary") or content.get("description") or title),
        })
    news_df = pd.DataFrame(rows, columns=["timestamp", "type", "source", "title", "text"])

    (root / "price").mkdir(parents=True, exist_ok=True)
    (root / "news").mkdir(parents=True, exist_ok=True)
    price_df.to_parquet(root / "price" / f"{ticker}.parquet")
    news_df.to_parquet(root / "news" / f"{ticker}.parquet")
    (root / "assets.txt").write_text(ticker + "\n")
    return root


def _build_env(ticker: str, start_date: str, end_date: str):
    """Real finagent.data.dataset.Dataset + finagent.environment.trading.EnvironmentTrading,
    fed real yfinance-sourced data, with the look_forward_days=0 causality fix (see module header)."""
    from finagent.data.dataset import Dataset
    from finagent.environment.trading import EnvironmentTrading

    tmp_root = Path(tempfile.mkdtemp(prefix="finagent_adapter_"))
    _fetch_and_write_dataset(ticker, start_date, end_date, tmp_root)

    dataset = Dataset(
        root=str(tmp_root),
        price_path="price",
        news_path="news",
        guidance_path=None,
        sentiment_path=None,
        economics_path=None,
        assets_path="assets.txt",
        interval="1d",
        workdir="workdir",
        tag="adapter_run",
    )
    env = EnvironmentTrading(
        mode="valid",
        dataset=dataset,
        selected_asset=ticker,
        asset_type="company",
        start_date=start_date,
        end_date=end_date,
        look_back_days=LOOK_BACK_DAYS,
        look_forward_days=LOOK_FORWARD_DAYS,
        initial_amount=INITIAL_AMOUNT,
        transaction_cost_pct=TRANSACTION_COST_PCT,
        discount=1.0,
    )
    return env, tmp_root


_PROVIDER_CACHE: dict = {}


def _get_provider():
    """Real finagent.provider.provider.OpenAIProvider, routed to DeepSeek
    via the real openai SDK's OPENAI_BASE_URL env-var fallback (see module
    header) — not a code modification."""
    if "provider" in _PROVIDER_CACHE:
        return _PROVIDER_CACHE["provider"]

    from finagent.provider.provider import OpenAIProvider

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not set (expected in adapters/vendor/ai-hedge-fund/.env)."
        )
    os.environ["OPENAI_API_KEY"] = deepseek_key
    os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL

    cfg_path = Path(tempfile.mkdtemp(prefix="finagent_provider_")) / "provider_config.json"
    cfg_path.write_text(json.dumps({
        "key_var": "OPENAI_API_KEY",
        "emb_model": "text-embedding-3-small",  # never actually invoked — see module header
        "comp_model": COMP_MODEL,
        "is_azure": False,
    }))
    provider = OpenAIProvider(provider_cfg_path=str(cfg_path))
    _PROVIDER_CACHE["provider"] = provider
    return provider


def _real_decision(env, info: dict, ticker: str, exp_scratch: Path) -> Tuple[str, str, dict]:
    """Real, unmodified finagent.prompt.trading.decision.DecisionTrading call.
    Returns (action_str, reasoning_str, raw_response_dict)."""
    from finagent.prompt.trading.decision import DecisionTrading

    asset = _asset_info(ticker)
    template_path = VENDOR_DIR / "res" / "prompts" / "template" / "valid" / "trading" / "decision.html"
    template_html = template_path.read_text()

    params = {
        "trader_preference": TRADER_PREFERENCE,
        "asset_symbol": asset.get("symbol", ticker),
        "asset_name": asset.get("name", ticker),
        "asset_exchange": asset.get("exchange", "UNKNOWN"),
        "asset_sector": asset.get("sector", "UNKNOWN"),
        "asset_industry": asset.get("industry", "UNKNOWN"),
        "asset_description": asset.get("description", ""),
        "past_market_intelligence_summary": _RELECTION_DISCLOSURE,
        "latest_market_intelligence_summary": _RELECTION_DISCLOSURE,
        "past_low_level_reflection": _RELECTION_DISCLOSURE,
        "latest_low_level_reflection": _RELECTION_DISCLOSURE,
        "past_high_level_reflection": _RELECTION_DISCLOSURE,
        "latest_high_level_reflection": _RELECTION_DISCLOSURE,
    }

    prompt = DecisionTrading(model=COMP_MODEL)
    provider = _get_provider()
    state = env.get_state()

    res = prompt.run(
        state=state,
        info=info,
        template=template_html,
        params=params,
        memory=None,
        provider=provider,
        diverse_query=None,
        exp_path=str(exp_scratch),
        save_dir=f"day_{info['date']}",
        call_provider=True,
    )
    response_dict = res["response_dict"]
    action = str(response_dict["action"]).strip().upper()
    reasoning = str(response_dict.get("reasoning", "")).strip()
    return action, reasoning, response_dict


_ACTION_TO_ENV = {"BUY": 1, "SELL": -1, "HOLD": 0}
_ACTION_TO_SCHEMA = {"BUY": Action.BUY, "SELL": Action.SELL, "HOLD": Action.HOLD}


def _weights_from_info(info: dict, ticker: str) -> Dict[str, float]:
    """Real cash/position/price/value (EnvironmentTrading.step()'s own real
    info dict, trading.py:277-279) -> a DERIVED target_weights fraction.
    Pure function, no upstream/network calls — kept separate so it can be
    fixture-tested deterministically (see tests/test_adapter_finagent.py)."""
    value, cash, position, price = info["value"], info["cash"], info["position"], info["price"]
    if not value:
        return {ticker: 0.0, "CASH": 1.0}
    return {ticker: (position * price) / value, "CASH": cash / value}


class FinAgentAdapter(BaseAdapter):
    name = "finagent"
    questions_answered = ["Q1", "Q4"]
    upstream_repo = "https://github.com/DVampire/FinAgent"
    requires_env = "finagent_real"

    def __init__(self):
        super().__init__()
        self._last_native_output: Optional[dict] = None
        self._session: Optional[dict] = None

    # ------------------------------------------------------------------
    # Q1 — single real decision at context.as_of
    # ------------------------------------------------------------------
    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        ticker = _ticker_from_context(context)
        as_of = context.as_of

        window_start = (pd.Timestamp(as_of) - pd.Timedelta(days=LOOK_BACK_DAYS * 3)).strftime("%Y-%m-%d")
        env, scratch = _build_env(ticker, window_start, as_of)
        _, info = env.reset()
        # advance to the last real trading day <= as_of (reset() lands on init_day, which
        # is the first bar >= window_start — walk forward with HOLD, a real no-op env.step,
        # to reach the requested as_of day without fabricating any decision along the way)
        while info["date"] < as_of and not env.day >= env.end_day:
            _, _, done, _, info = env.step(0)
            if done:
                break

        action_str, reasoning, raw = _real_decision(env, info, ticker, scratch)
        env_action = _ACTION_TO_ENV.get(action_str, 0)

        explanation = reasoning or None

        self._last_native_output = {
            "upstream": {
                "ticker": ticker, "date": info["date"], "action": action_str,
                "reasoning": reasoning, "raw_response": raw,
                "info": info,
            }
        }

        return Q1Action(
            context=context,
            action=_ACTION_TO_SCHEMA.get(action_str, Action.HOLD),
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Q4 — real causal trajectory across generation_window
    # ------------------------------------------------------------------
    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        ticker = _ticker_from_context(context)

        env, scratch = _build_env(ticker, generation_window.start, generation_window.end)
        _, info = env.reset()

        decisions: List[PolicyDecisionStep] = []
        native_steps = []
        done = False
        while not done:
            action_str, reasoning, raw = _real_decision(env, info, ticker, scratch)
            env_action = _ACTION_TO_ENV.get(action_str, 0)

            pre_date = info["date"]
            state, reward, done, truncated, info = env.step(env_action)

            weights = _weights_from_info(info, ticker)

            decisions.append(PolicyDecisionStep(
                timestamp=info["date"],
                information_cutoff=pre_date,  # decision was made using state as of pre_date (look_forward_days=0)
                target_weights=weights,
                explanation=reasoning or None,
            ))
            native_steps.append({"date": info["date"], "action": action_str, "reasoning": reasoning, "info": info, "raw_response": raw})

        if not decisions:
            raise RuntimeError(f"finagent q4_policy produced zero real steps for {ticker} over {generation_window}")

        last = decisions[-1]
        constraints = PortfolioConstraints(long_only=True, cash_allowed=True)

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=[ticker],
            selector_description="Single-asset scope — EnvironmentTrading.position is a scalar int (verified via finagent/environment/trading.py), no multi-asset selection exists in this project.",
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{LOOK_BACK_DAYS}_trading_days",
            features=["price", "cash", "position", "total_profit", "total_return", "recent_news_headlines"],
            data_sources=["yfinance (adapter-fetched, real OHLCV + real headlines)"],
            observation_description=(
                "Real EnvironmentTrading.get_state() window, constructed with look_forward_days=0 "
                "(adapter-level causality fix — see module docstring; upstream's own shipped config "
                "defaults to look_forward_days=14, a real look-ahead this adapter does not use)."
            ),
        )
        decision_policy = DecisionPolicy(
            decision_rule=(
                "Real finagent.prompt.trading.decision.DecisionTrading LLM call (check_keys=['action','reasoning'], "
                "backoff-validated), real DeepSeek completion, real current environment state as input. "
                "Reflection/memory-retrieval stages are honestly skipped (see module header) — blocked by a "
                "missing embeddings-capable credential, not fabricated."
            ),
            output_semantics="BUY/SELL/HOLD -> real EnvironmentTrading.step() order sizing -> target_weights derived from real post-step cash/position/value.",
            rebalance_frequency="DAILY",
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.ONLINE_LEARNING,
            update_frequency="per real trading day",
            update_description="A fresh real LLM decision is requested every day from real, current environment state; no persisted/frozen model.",
        )

        self._last_native_output = {"upstream": {"ticker": ticker, "steps": native_steps}}

        return Q4Policy(
            context=context,
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            initial_weights=last.target_weights,
            decisions=decisions,
            explanation=(
                f"Real day-by-day EnvironmentTrading trajectory for {ticker} over "
                f"[{generation_window.start}, {generation_window.end}]: {len(decisions)} real "
                f"decisions, each from a real DeepSeek call via finagent's own DecisionTrading class."
            ),
        )

    # ------------------------------------------------------------------
    # Q4 stepwise protocol (harness/q4_protocol.py) — additive only.
    # Externalizes the exact same real env.reset()/_real_decision()/env.step()
    # loop q4_policy() already runs above, so the harness (not this adapter)
    # controls step timing. q4_policy() itself is untouched byte-for-byte.
    # ------------------------------------------------------------------
    def q4_initialize(
        self,
        context: QueryContext,
        generation_window: TimeWindow,
        initial_portfolio: PortfolioState,
        run_config: Q4RunConfig,
    ) -> Q4Policy:
        ticker = _ticker_from_context(context)
        env, scratch = _build_env(ticker, generation_window.start, generation_window.end)
        _, info = env.reset()

        self._session = {
            "env": env, "scratch": scratch, "ticker": ticker,
            "info": info, "done": False, "step_count": 0, "native_steps": [],
        }

        constraints = PortfolioConstraints(long_only=True, cash_allowed=True)
        universe_policy = UniversePolicy(
            mode="fixed", fixed_assets=[ticker],
            selector_description="Single-asset scope — EnvironmentTrading.position is a scalar int (verified via finagent/environment/trading.py), no multi-asset selection exists in this project.",
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{LOOK_BACK_DAYS}_trading_days",
            features=["price", "cash", "position", "total_profit", "total_return", "recent_news_headlines"],
            data_sources=["yfinance (adapter-fetched, real OHLCV + real headlines)"],
            observation_description=(
                "Real EnvironmentTrading.get_state() window, constructed with look_forward_days=0 "
                "(adapter-level causality fix — see module docstring)."
            ),
        )
        decision_policy = DecisionPolicy(
            decision_rule=(
                "Real finagent.prompt.trading.decision.DecisionTrading LLM call per real trading day, "
                "real DeepSeek completion, real current environment state as input. Reflection/memory "
                "stages are honestly skipped (see module header) — blocked by a missing "
                "embeddings-capable credential, not fabricated."
            ),
            output_semantics="BUY/SELL/HOLD -> real EnvironmentTrading.step() order sizing -> target_weights derived from real post-step cash/position/value.",
            rebalance_frequency="DAILY",
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.ONLINE_LEARNING,
            update_frequency="per real trading day",
            update_description="A fresh real LLM decision is requested every day from real, current environment state; no persisted/frozen model.",
        )
        return Q4Policy(
            context=context, policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy, observation_policy=observation_policy,
            decision_policy=decision_policy, update_policy=update_policy, constraints=constraints,
        )

    def q4_step(
        self,
        timestamp: str,
        information_cutoff: str,
        observation: MarketObservation,
        portfolio_state: PortfolioState,
    ) -> PolicyDecisionStep:
        if self._session is None:
            raise RuntimeError("q4_step called before q4_initialize")
        s = self._session
        if s["done"]:
            raise RuntimeError("q4_step called after the real EnvironmentTrading episode already reached done=True")

        env, info, ticker, scratch = s["env"], s["info"], s["ticker"], s["scratch"]

        real_cutoff = info["date"]
        if real_cutoff != information_cutoff:
            raise ValueError(
                f"harness-disclosed information_cutoff={information_cutoff!r} does not match this "
                f"session's own real current environment date ({real_cutoff!r}) — observation stream "
                f"is misaligned with this adapter's real sequential environment state"
            )

        action_str, reasoning, raw = _real_decision(env, info, ticker, scratch)
        env_action = _ACTION_TO_ENV.get(action_str, 0)

        pre_date = info["date"]
        state, reward, done, truncated, info = env.step(env_action)
        weights = _weights_from_info(info, ticker)

        if info["date"] != timestamp:
            raise ValueError(
                f"harness-disclosed timestamp={timestamp!r} does not match this session's real "
                f"post-step environment date ({info['date']!r}) for pre_date={pre_date!r}"
            )

        s["info"] = info
        s["done"] = bool(done)
        s["step_count"] += 1
        s["native_steps"].append({"date": info["date"], "action": action_str, "reasoning": reasoning, "info": info, "raw_response": raw})

        return PolicyDecisionStep(
            timestamp=timestamp, information_cutoff=information_cutoff,
            target_weights=weights, explanation=reasoning or None,
        )

    def q4_finalize(self) -> Q4FinalizeSummary:
        if self._session is None:
            raise RuntimeError("q4_finalize called before q4_initialize")
        s = self._session
        summary = Q4FinalizeSummary(
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            update_policy=UpdatePolicy(
                mode=UpdateMode.ONLINE_LEARNING,
                update_frequency="per real trading day",
                update_description="A fresh real LLM decision is requested every day from real, current environment state; no persisted/frozen model.",
            ),
            explanation=(
                f"Real day-by-day EnvironmentTrading stepwise session for {s['ticker']}: "
                f"{s['step_count']} real q4_step() calls, each from a real DeepSeek call via "
                f"finagent's own DecisionTrading class."
            ),
        )
        self._last_native_output = {"upstream": {"ticker": s["ticker"], "steps": s["native_steps"]}}
        self._session = None
        return summary

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output
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
        self._last_native_output = None
        result = super().run(
            task_id, context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes,
            field_mappings=field_mappings, **kwargs,
        )
        if native_output is None and self._last_native_output:
            result = result.model_copy(update={"native_output": self._last_native_output})
        return result

    # ------------------------------------------------------------------
    # Smoke test — real calls (real DeepSeek completions)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-01-16",
            data_cutoff="2024-01-16",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

        q1 = self.q1_action(context)
        checks["q1_returns_Q1Action"] = q1 is not None
        if q1 is not None:
            checks["q1_action_is_valid"] = q1.action in ("BUY", "SELL", "HOLD")
            checks["q1_context_echoed"] = q1.context == context

        generation_window = TimeWindow(start="2024-01-08", end="2024-01-12")
        q4 = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = q4 is not None
        if q4 is not None:
            checks["q4_context_echoed"] = q4.context == context
            checks["q4_generation_window_echoed"] = q4.generation_window == generation_window
            checks["q4_decisions_nonempty"] = bool(q4.decisions)
            if q4.decisions:
                checks["q4_causality_ok"] = all(d.information_cutoff <= d.timestamp for d in q4.decisions)
                timestamps = [d.timestamp for d in q4.decisions]
                checks["q4_timestamps_increasing"] = timestamps == sorted(timestamps)
                checks["q4_weights_long_only"] = all(
                    w >= -1e-9 for d in q4.decisions for w in (d.target_weights or {}).values()
                )
                checks["q4_weights_sum_near_1"] = all(
                    abs(sum((d.target_weights or {}).values()) - 1.0) < 1e-6 for d in q4.decisions
                )
        return checks
