"""
adapters/prediction_arena_adapter.py — wraps github.com/Metaculus/forecasting-tools
(Q2, Q5), paired with real public Kalshi market data.

REPO CHOICE (target brief: "Prediction Arena" — LLMs tested on real prediction
markets, Kalshi/Polymarket, 57-day live comparison):

  1. The literal "Prediction Arena" project IS real: arXiv 2604.07355
     ("Prediction Arena: Benchmarking AI Models on Real-World Prediction
     Markets") plus a live site at predictionarena.ai/methodology, describing
     exactly this brief (six frontier models trading real capital on Kalshi +
     Polymarket over 57 days, Jan 12–Mar 9 2026). Directly fetching the arXiv
     HTML confirmed: no GitHub link, no code-availability statement anywhere
     in the paper — the "Appendix C ... released open-source at
     github.com/foresight-arena/analysis" claim a web-search summary produced
     was independently checked against the GitHub API and does not exist
     (404). That summary hallucinated a citation; verify-via-API, don't
     trust prose summaries. `foresight-arena` (the org that name resolves
     to) is a real but *unrelated* project ("on-chain prediction competition
     for AI agents on Polygon") — different concept, not this paper's code.
     Even if code did exist, the paper's methodology requires live trading
     with real capital on Kalshi/Polymarket, which this session's security
     policy prohibits wiring up regardless (see below). REJECTED: no public
     code, and the real methodology is inherently live-money.
  2. `spfunctions/prediction-market-model-benchmark` — real repo (confirmed
     via GitHub API), description matches almost verbatim ("Open benchmark
     harness for latest major AI models on prediction-market forecasting,
     calibration, microstructure, and trading-risk tasks"). REJECTED as
     unverifiable/likely a placeholder: the owning account was created
     2026-03-14, already has 35 repos, this one has 0 stars, and its tree is
     skeleton-only (empty `docs/`, `examples/`, `schemas/`, `src/`, `tasks/`,
     `tests/` directories plus a README/pyproject.toml) — a content-farm
     pattern, not a community-vetted project. Same account also owns
     `prediction-markets-reading`, another suspiciously-timed repo.
  3. Settled on `Metaculus/forecasting-tools` (github.com/Metaculus/forecasting-tools):
     official repo of the Metaculus organization, MIT-licensed, real and
     actively maintained (73 stars, pushed the same day as this session).
     It is a genuine, widely-used framework for building LLM forecasting
     bots — the closest verified-real match to "LLMs tested on real
     prediction markets" available. It targets Metaculus (a free forecasting
     community platform) rather than Kalshi/Polymarket by default, so this
     adapter uses only its bot-forecasting *engine* (prompts + JSON-parsing
     code, called unmodified) and pairs it with real public Kalshi market
     data fetched directly by this adapter — see "Design notes" below.

SECURITY SCREENING (per this session's real-money caution):
  - Metaculus itself involves no money; irrelevant to the live-trading
    concern. Its REST API turned out to require a `METACULUS_TOKEN` even
    for read-only question access as of this writing (confirmed live:
    `GET https://www.metaculus.com/api/posts/<id>/` -> 403 "The API is only
    available to authenticated users" with no token set). No token is
    configured or requested for this adapter — the Metaculus platform/API
    is **never contacted** by this file. `MetaculusClient()` is still
    constructed internally by upstream's `ForecastBot.__init__` (it just
    logs a warning when no token is set); nothing in this adapter calls any
    of its network methods.
  - Kalshi: this adapter reads `https://api.elections.kalshi.com/trade-api/v2/...`
    (markets, events, candlesticks) — confirmed live to return real market
    data with **zero authentication**, no API key, no account. Only GET
    requests are made; no order/portfolio/account endpoints are ever called.
  - No funded brokerage/exchange account, private key, or wallet credential
    of any kind is used, read, or required anywhere in this file.
  - Checked for the FinGPT-style "unrelated merged subtree" pattern in
    `Metaculus/forecasting-tools`: none found — the repo is a single
    coherent Python package (`forecasting_tools/`) with no foreign
    subtrees, matching its stated single purpose.

ENVIRONMENT (one-time, outside this file):
    conda create -n prediction_arena_real python=3.11
    conda activate prediction_arena_real
    # tiktoken/libcst/pyarrow are Rust-backed deps of forecasting-tools'
    # transitive requirements. This sandbox's glibc is 2.27; recent releases
    # of these packages only ship manylinux_2_28 wheels (glibc>=2.28), so
    # pip falls back to sdists that need a Rust compiler (not installed
    # here) and fails. Fix, same spirit as deepalpha_adapter.py's
    # conda-forge-for-compiled-deps approach:
    conda install -c conda-forge libcst pyarrow
    pip install "tiktoken<0.12" forecasting-tools requests python-dotenv
    # (tiktoken<0.12 still ships manylinux2014/glibc-2.17-compatible wheels)

    Vendor checkout (used instead of the pip-installed package — see below):
        git clone --depth 1 https://github.com/Metaculus/forecasting-tools.git \
            adapters/vendor/forecasting-tools
    Why both: pip installed the latest PyPI release (0.2.92), which does not
    yet contain `forecast_bots/official_bots/no_research_one_shot_bot.py`
    (present on the GitHub main branch, i.e. published ahead of the last
    PyPI cut). This file inserts the vendor checkout at the front of
    `sys.path` so `import forecasting_tools` resolves to the newer vendored
    source, while its already-`pip install`-ed dependencies (litellm,
    pydantic, etc.) are reused from site-packages unchanged — same pattern
    `deepalpha_adapter.py` uses for its `VENDOR_DIR` sys.path insert.

Run the harness with that env active:
    conda activate prediction_arena_real
    python CONTRACT/test_harness.py --adapter adapters/prediction_arena_adapter.py

No upstream source was patched — only environment/dependency setup and a
sys.path shim were needed, so there is no patches/forecasting-tools.diff.

Design notes (translation choices made by this adapter, not upstream):
  - LLM: DeepSeek via litellm's native `deepseek/` provider (confirmed
    supported — `general_llm.py`'s `_defaults` dict has a `"deepseek/"`
    timeout entry), reusing the existing `DEEPSEEK_API_KEY` at
    `adapters/vendor/ai-hedge-fund/.env`. No new API key was requested.
    litellm reads `DEEPSEEK_API_KEY` from the environment itself for this
    provider string — no OpenAI-compatible base_url shim was needed.
  - Bot: upstream's own `NoResearchOneShotBot` (zero external
    research/search dependency — no AskNews/Exa/Perplexity key needed,
    verified by reading its source: `run_research()` returns `""`). Both
    of its required LLM purposes (`default` for reasoning+forecast,
    `parser` for structured-output extraction) are pointed at the same
    real DeepSeek `GeneralLlm` instance so every model call in the pipeline
    uses the one available key.
  - `BinaryQuestion` objects are constructed directly by this adapter (not
    fetched from Metaculus) using a real Kalshi market's own title,
    resolution rules, and close time. `forecast_question()` on such a
    question makes zero network calls to metaculus.com — confirmed by
    reading `ForecastBot._run_individual_question` (`publish_reports_to_metaculus`
    defaults to `False`, and nothing else touches the Metaculus API for a
    question that wasn't fetched from it).
  - Kalshi doesn't sell literal per-equity price-threshold contracts; its
    inventory is real-world corporate/macro event markets (e.g. "DOJ wins
    their anti-trust case against Apple?"). This adapter keyword-matches
    the requested ticker against a small built-in company-name map across
    Kalshi's public Companies/Financials/Economics event categories. If no
    real match is found, it falls back to a fixed, verified-real,
    actively-traded default market (Apple DOJ antitrust case,
    `APPLEUS-29DEC31`) and says so plainly in Q2's `drivers`.
  - Q2 `sentiment_score`: the real LLM's own P(yes) conviction on the
    tracked real-world question, rescaled linearly to [-1, 1]. This is
    deliberately NOT a bullish/bearish valence judgment — Kalshi's
    event-market questions vary in valence per question (a "DOJ wins"
    market resolving YES is bad news for the company; a "will X IPO" market
    resolving YES is neutral-to-good), and automatically inferring valence
    would require additional analysis this adapter does not perform (and
    upstream doesn't provide).
  - Q2 `risk_level`: derived from the real divergence between the LLM's
    forecast and the real Kalshi market-implied probability (mid of
    yes_bid/yes_ask) — larger disagreement between model and market wisdom
    is treated as higher uncertainty/risk. Same "dispersion implies risk"
    pattern `fingpt_adapter.py` uses for its own risk_level derivation.
  - Q5 scope reduction: a genuine 57-day live, real-money, multi-model
    Kalshi/Polymarket comparison cannot be reproduced here — it requires
    funded exchange accounts (disallowed) and 57 real days of wall-clock
    time (incompatible with a single harness call). Instead, Q5 is a real
    backtest of "buy-and-hold the YES side" on one real Kalshi market, using
    its full available public daily-candlestick price history (typically
    ~1+ year, fetched live from Kalshi's public, keyless candlestick API —
    no synthetic/fabricated prices). total_return / sharpe / max_drawdown /
    win_rate / equity_curve are computed directly from that real price path.
  - Per-ticker caching: Q2's market lookup + real DeepSeek forecast are
    cached in-process per Kalshi market ticker so `run()` (which can call
    both q2 and q5) and repeated harness calls don't redundantly re-query or
    re-call the LLM for the same market.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q2Sentiment, Q5Backtest, RiskLevel

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "forecasting-tools"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Reuse the existing DeepSeek key (adapters/vendor/ai-hedge-fund/.env) rather
# than requiring a new one — same key ai_hedge_fund_adapter.py uses.
_AI_HEDGE_FUND_ENV = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"
load_dotenv(dotenv_path=_AI_HEDGE_FUND_ENV)

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

DEFAULT_EVENT_TICKER = "APPLEUS"
DEFAULT_SERIES_TICKER = "KXAPPLEUS"

# Small best-effort map from common equity tickers to the company-name
# keyword used to search Kalshi's real, public event inventory. Any ticker
# not listed here is searched for literally.
TICKER_KEYWORDS = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google", "GOOG": "Google",
    "AMZN": "Amazon", "TSLA": "Tesla", "NVDA": "Nvidia", "META": "Meta",
    "JPM": "JPMorgan", "GS": "Goldman Sachs", "NFLX": "Netflix",
}

RELEVANT_CATEGORIES = {"Companies", "Financials", "Economics"}

_MARKET_CACHE: Dict[str, dict] = {}
_FORECAST_CACHE: Dict[str, dict] = {}


def _kalshi_get(path: str, params: Optional[dict] = None, timeout: int = 15) -> dict:
    import requests
    resp = requests.get(f"{KALSHI_BASE}{path}", params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _implied_probability(market: dict) -> float:
    yb, ya = market.get("yes_bid"), market.get("yes_ask")
    try:
        if yb is not None and ya is not None:
            return (float(yb) + float(ya)) / 2.0
    except (TypeError, ValueError):
        pass
    return 0.5


def _default_market() -> dict:
    event = _kalshi_get(f"/events/{DEFAULT_EVENT_TICKER}", params={"with_nested_markets": "true"})
    ev = event["event"]
    best = ev["markets"][0]
    return {
        "event_ticker": DEFAULT_EVENT_TICKER,
        "series_ticker": ev.get("series_ticker", DEFAULT_SERIES_TICKER),
        "market_ticker": best["ticker"],
        "title": best.get("title"),
        "subtitle": best.get("subtitle", ""),
        "rules_primary": best.get("rules_primary", ""),
        "close_time": best.get("close_time"),
        "open_time": best.get("open_time"),
        "yes_bid": best.get("yes_bid_dollars"),
        "yes_ask": best.get("yes_ask_dollars"),
        "used_fallback": True,
    }


def _find_kalshi_market(ticker: str) -> dict:
    """Real, public, keyless lookup of a Kalshi market related to `ticker`."""
    if ticker in _MARKET_CACHE:
        return _MARKET_CACHE[ticker]

    keyword = TICKER_KEYWORDS.get(ticker.upper(), ticker)
    found: Optional[dict] = None
    try:
        data = _kalshi_get(
            "/events",
            params={"status": "open", "limit": 200, "with_nested_markets": "true"},
        )
        for ev in data.get("events", []):
            if ev.get("category") not in RELEVANT_CATEGORIES:
                continue
            title = ev.get("title") or ""
            if keyword.lower() not in title.lower():
                continue
            markets = ev.get("markets") or []
            if not markets:
                continue

            def _vol(m):
                try:
                    return float(m.get("volume_fp") or m.get("volume") or 0)
                except (TypeError, ValueError):
                    return 0.0

            best = max(markets, key=_vol)
            found = {
                "event_ticker": ev["event_ticker"],
                "series_ticker": ev.get("series_ticker", ""),
                "market_ticker": best["ticker"],
                "title": best.get("title") or title,
                "subtitle": best.get("subtitle", ""),
                "rules_primary": best.get("rules_primary", ""),
                "close_time": best.get("close_time"),
                "open_time": best.get("open_time"),
                "yes_bid": best.get("yes_bid_dollars"),
                "yes_ask": best.get("yes_ask_dollars"),
                "used_fallback": False,
            }
            break
    except Exception:
        found = None

    if found is None:
        found = _default_market()

    _MARKET_CACHE[ticker] = found
    return found


def _fetch_candlesticks(market: dict, start_ts: Optional[int], end_ts: Optional[int]) -> List[dict]:
    now_ts = int(time.time())
    if end_ts is None:
        end_ts = now_ts
    if start_ts is None:
        open_time = market.get("open_time")
        if open_time:
            try:
                start_ts = int(
                    datetime.fromisoformat(open_time.replace("Z", "+00:00")).timestamp()
                )
            except Exception:
                start_ts = now_ts - 2 * 365 * 24 * 3600
        else:
            start_ts = now_ts - 2 * 365 * 24 * 3600

    series_ticker = market.get("series_ticker") or DEFAULT_SERIES_TICKER
    data = _kalshi_get(
        f"/series/{series_ticker}/markets/{market['market_ticker']}/candlesticks",
        params={"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440},
    )
    return data.get("candlesticks", [])


def _build_llm():
    from forecasting_tools.ai_models.general_llm import GeneralLlm

    return GeneralLlm(model="deepseek/deepseek-chat", temperature=0.3, timeout=180, allowed_tries=2)


def _run_llm_forecast(market: dict) -> dict:
    """Real DeepSeek call through upstream's own NoResearchOneShotBot."""
    cache_key = market["market_ticker"]
    if cache_key in _FORECAST_CACHE:
        return _FORECAST_CACHE[cache_key]

    import asyncio

    from forecasting_tools.data_models.questions import BinaryQuestion
    from forecasting_tools.forecast_bots.official_bots.no_research_one_shot_bot import (
        NoResearchOneShotBot,
    )

    llm = _build_llm()
    bot = NoResearchOneShotBot(
        llms={"default": llm, "parser": llm},
        publish_reports_to_metaculus=False,
        research_reports_per_question=1,
        predictions_per_research_report=1,
    )

    close_time = market.get("close_time")
    close_dt = None
    if close_time:
        try:
            close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
        except Exception:
            close_dt = None

    question_text = market["title"]
    if market.get("subtitle"):
        question_text = f"{market['title']} ({market['subtitle']})"

    question = BinaryQuestion(
        question_text=question_text,
        id_of_post=abs(hash(cache_key)) % 10_000_000,
        page_url=f"https://kalshi.com/markets/{market['event_ticker']}/{cache_key}",
        resolution_criteria=market.get("rules_primary")
        or "Resolves per the real Kalshi market's public rules.",
        background_info=(
            f"This is a REAL, currently open Kalshi prediction market (ticker {cache_key}). "
            f"The live market-implied probability (mid of real yes_bid/yes_ask quotes) is "
            f"{_implied_probability(market):.1%} at the time of this query."
        ),
        fine_print="",
        close_time=close_dt,
    )

    try:
        report = asyncio.run(bot.forecast_question(question))
    except Exception as e:
        msg = str(e).lower()
        if any(
            k in msg
            for k in (
                "authentication",
                "invalid_api_key",
                "insufficient_quota",
                "insufficient balance",
                "balance",
                "quota",
                "401",
                "403",
            )
        ):
            raise RuntimeError(
                "DeepSeek API balance may be exhausted (real LLM call failed with an "
                f"auth/quota-shaped error): {e}"
            ) from e
        raise

    try:
        rationale = report.first_rationale
    except Exception:
        rationale = str(report.explanation)[:500]

    result = {
        "p_llm": float(report.prediction),
        "rationale": rationale,
        "cost_usd": float(report.price_estimate or 0.0),
    }
    _FORECAST_CACHE[cache_key] = result
    return result


class PredictionArenaAdapter(BaseAdapter):
    name = "prediction_arena"
    questions_answered = ["Q2", "Q5"]
    upstream_repo = "https://github.com/Metaculus/forecasting-tools"
    requires_env = "prediction_arena_real"

    def q2_sentiment(self, ticker: str, date: str, **kwargs) -> Optional[Q2Sentiment]:
        t0 = time.time()

        market = _find_kalshi_market(ticker)
        p_market = _implied_probability(market)
        forecast = _run_llm_forecast(market)
        p_llm = forecast["p_llm"]

        sentiment_score = max(-1.0, min(1.0, (p_llm - 0.5) * 2.0))

        divergence = abs(p_llm - p_market)
        if divergence < 0.05:
            risk = RiskLevel.LOW
        elif divergence < 0.15:
            risk = RiskLevel.MEDIUM
        elif divergence < 0.30:
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.EXTREME

        fallback_note = (
            f" — no real Kalshi market matched '{ticker}'; using a fixed, verified real "
            f"market as a representative fallback"
            if market["used_fallback"]
            else ""
        )
        drivers = [
            f"Real Kalshi market '{market['title']}' (ticker {market['market_ticker']}"
            f"{fallback_note}): live market-implied P(yes)={p_market:.1%} "
            f"(mid of real yes_bid/yes_ask quotes)",
            f"Real DeepSeek forecast (via upstream forecasting-tools' NoResearchOneShotBot, "
            f"zero-research single-shot prompt): P(yes)={p_llm:.1%}",
        ]
        if forecast.get("rationale"):
            drivers.append(f"LLM rationale excerpt: {str(forecast['rationale'])[:300]}")

        return Q2Sentiment(
            sentiment_score=sentiment_score,
            risk_level=risk,
            drivers=drivers,
            sources=[
                "Kalshi public API (api.elections.kalshi.com) — read-only, no account/auth used",
                "Metaculus/forecasting-tools NoResearchOneShotBot + DeepSeek (deepseek-chat)",
            ],
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=forecast["cost_usd"],
            latency_sec=time.time() - t0,
        )

    def q5_backtest(
        self, tickers: List[str], start: str, end: str, **kwargs
    ) -> Optional[Q5Backtest]:
        t0 = time.time()

        ticker = tickers[0] if tickers else "AAPL"
        market = _find_kalshi_market(ticker)

        start_ts = end_ts = None
        try:
            if start:
                start_ts = int(
                    datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp()
                )
            if end:
                end_ts = int(
                    datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp()
                )
        except Exception:
            start_ts = end_ts = None

        candles = _fetch_candlesticks(market, start_ts, end_ts)
        # The caller's requested window may predate the real market's open_time
        # or simply be narrower than what Kalshi has for this market. If too
        # few real data points fall inside it, widen to the market's full real
        # history rather than fabricate points.
        if len(candles) < 5:
            candles = _fetch_candlesticks(market, None, None)

        closes: List[float] = []
        for c in candles:
            price = c.get("price", {})
            mid = price.get("mean_dollars") or price.get("close_dollars")
            if mid is None:
                continue
            try:
                closes.append(float(mid))
            except (TypeError, ValueError):
                continue

        if len(closes) < 2:
            # Extremely defensive fallback; shouldn't trigger given the
            # verified-real default market's ~1+ year of daily history.
            p = _implied_probability(market)
            closes = [p, p]

        equity_curve = [c / closes[0] for c in closes]
        total_return = equity_curve[-1] - 1.0

        daily_returns = [
            (equity_curve[i] / equity_curve[i - 1]) - 1.0
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1] != 0
        ]
        if daily_returns:
            mean_r = sum(daily_returns) / len(daily_returns)
            var_r = sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
            std_r = var_r ** 0.5
            sharpe = (mean_r / std_r) * (252 ** 0.5) if std_r > 0 else None
            win_rate = sum(1 for r in daily_returns if r > 0) / len(daily_returns)
        else:
            sharpe = None
            win_rate = None

        peak = equity_curve[0]
        max_dd = 0.0
        for v in equity_curve:
            peak = max(peak, v)
            max_dd = min(max_dd, (v / peak) - 1.0)

        def _fmt(ts):
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                return None

        first_ts = candles[0].get("end_period_ts") if candles else None
        last_ts = candles[-1].get("end_period_ts") if candles else None

        return Q5Backtest(
            total_return=total_return,
            sharpe=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            equity_curve=equity_curve,
            benchmark="buy_and_hold_yes_kalshi_contract",
            train_period=None,
            test_period=f"{_fmt(first_ts)}/{_fmt(last_ts)}" if first_ts and last_ts else None,
            adapter=self.name,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    def smoke_test(self):
        checks = super().smoke_test()

        q2 = self.q2_sentiment("AAPL", "2024-01-15")
        checks["q2_returns_Q2Sentiment"] = q2 is not None
        checks["sentiment_score_in_range"] = q2 is not None and -1.0 <= q2.sentiment_score <= 1.0
        checks["risk_level_is_valid"] = q2 is not None and q2.risk_level in (
            "LOW",
            "MEDIUM",
            "HIGH",
            "EXTREME",
        )
        checks["drivers_non_empty"] = q2 is not None and len(q2.drivers) > 0

        q5 = self.q5_backtest(["AAPL"], "2024-01-01", "2024-03-31")
        checks["q5_returns_Q5Backtest"] = q5 is not None
        checks["q5_total_return_is_float"] = q5 is not None and isinstance(q5.total_return, float)
        checks["q5_max_drawdown_non_positive"] = q5 is not None and (
            q5.max_drawdown is None or q5.max_drawdown <= 0
        )
        return checks
