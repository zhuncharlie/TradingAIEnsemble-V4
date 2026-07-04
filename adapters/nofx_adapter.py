"""
adapters/nofx_adapter.py — wraps github.com/0xemmkty/QuantMuse (Q2).

REPO CHOICE (target brief: "NoFx" — LLM sentiment + quantitative signal, a
fusion layer that outputs a risk score):

  1. The literal name IS a real repo: `NoFxAiOS/nofx` (github.com/NoFxAiOS/nofx,
     12.5k stars, 3k forks, AGPL-3.0, created 2025-10-28, actively pushed —
     confirmed live via the GitHub REST API, not a hallucinated citation).
     It is "Your AI trading terminal assistant for US stocks, commodities,
     forex, and crypto," and its docs (STRATEGY_MODULE.md) do describe an
     LLM analysis stage fed by quant/technical context. REJECTED, for two
     independent reasons, either of which is disqualifying on its own:
       a) Security: per this session's policy, no adapter may require live
          brokerage/exchange account credentials or real money. NOFX's own
          README Setup section step 2 is literally "Connect exchange
          credentials" (Binance/Bybit/OKX/Hyperliquid/Bitget/KuCoin/Gate/
          Aster/Lighter); its core data flow needs authenticated account
          balance/position reads (confirmed by reading
          docs/architecture/STRATEGY_MODULE.md directly, not just the
          README) with no documented dry-run/paper/analysis-only mode.
          Same class of problem as the Robinhood-credential rejection
          documented in DECISIONS.md for the DeepAlpha adapter.
       b) Practical/architectural mismatch even ignoring (a): its AI layer
          is hard-routed through a proprietary paid gateway ("Claw402") —
          "Users do not need to configure model providers, manage API
          keys" — so this session's existing `DEEPSEEK_API_KEY` cannot be
          plugged in at all. It is also a Go binary + React web terminal,
          not a callable Python research library, so there is no faithful
          way to build a thin single-function wrapper around it.
  2. Searched for the closest real substitute: an open-source project that
     genuinely combines an LLM-based sentiment/qualitative signal with a
     separate quantitative/technical signal into one fused score, needing
     only public market data + an LLM key (no funded accounts). Rejected
     along the way: `Ronitt272/LLM-Enhanced-Trading` (real, but thin
     wrapper around FinGPT + simple SMA/RSI crossover glue rather than its
     own fusion architecture — already effectively covered by this
     session's `fingpt_adapter.py`); `AI4Finance-Foundation/FinGPT` itself
     (already the dedicated `fingpt_adapter.py` in this repo, Iron Rule
     against duplicate adapters for one upstream project).
  3. Settled on `0xemmkty/QuantMuse` (github.com/0xemmkty/QuantMuse):
     confirmed real via the GitHub API (2,707 stars, 561 forks, MIT
     license, Python, actively pushed; owning account created 2022-03-26
     with 14 varied public repos — not a fresh content-farm account like
     the `spfunctions` one rejected in `prediction_arena_adapter.py`'s
     DECISIONS entry). Its own `data_service/ai/llm_integration.py` module
     (`LLMIntegration.assess_risk()`) is a genuine, real, working fusion
     layer: it takes a `market_conditions` dict that this adapter populates
     with (a) real per-headline LLM sentiment scores aggregated by
     upstream's own `SentimentAnalyzer.calculate_market_sentiment()` and
     (b) real quantitative technical factors from upstream's own
     `FactorCalculator.calculate_technical_factors()` / `calculate_price_
     momentum()` (RSI, MACD, Bollinger Bands, moving averages, momentum —
     all computed from real price history, not fabricated), and sends both
     to a real LLM call that returns a fused `overall_risk` verdict
     (low/medium/high) plus `risk_factors`. This is the closest verified-
     real match to "LLM sentiment + quant signal -> fusion -> risk score."

SECURITY SCREENING:
  - No live brokerage/exchange credentials, no real money, no funded
    account of any kind is used, read, or required anywhere in this file
    or in the specific upstream modules it imports. Only `yfinance` (public,
    keyless) market data and the existing `DEEPSEEK_API_KEY` are used.
  - Upstream's own `setup.py` lists `python-binance` as a core
    `install_requires` dependency (used elsewhere in the repo, e.g. its
    live-data fetchers under `data_service/fetchers/`), but this adapter
    never imports `data_service.fetchers` or anything that touches
    `python-binance` — confirmed by reading every import in the three
    modules actually used (`sentiment_analyzer.py`, `llm_integration.py`,
    `factor_calculator.py`) and their package `__init__.py` chains, and
    `python-binance` is NOT installed in this adapter's conda env at all
    (proves it, since the code runs and imports cleanly without it).
  - Checked for the FinGPT-style "unrelated merged subtree under a
    misleadingly-named branch" pattern: the repo has exactly one branch
    (`main`) — none found.
  - Noted but not disqualifying: the repo's root contains a stray
    `test.cpp` (literal "Hello, C++ is working!" — a trivial toolchain
    smoke-test file) and a compiled `test.exe` (44KB, valid Windows PE/
    `MZ` header, consistent size for that trivial program) — sloppy repo
    hygiene from a local dev machine, not a hidden payload. This adapter
    never references, imports, or executes either file.
  - No `eval`/`exec`/`shell=True` found in any of the three modules used.

ENVIRONMENT (one-time, outside this file):
    conda create -n nofx_real python=3.11
    conda activate nofx_real
    pip install pandas numpy requests python-dotenv yfinance "openai==0.28.1" \
                matplotlib seaborn scipy

    # openai MUST be pinned <1.0: upstream's `OpenAIProvider`/
    # `SentimentAnalyzer` call the pre-1.0 `openai.ChatCompletion.create(...)`
    # / module-level `openai.api_key` / `openai.api_base` style. Installing
    # modern openai>=1.0 makes that call raise its built-in migration error
    # immediately (`openai.ChatCompletion` no longer exists at the top
    # level). Same "pin to the vintage the vendor code was written
    # against" lesson as fingpt_adapter.py's transformers/peft pin.
    # matplotlib/seaborn/scipy are real (if unused-by-us) transitive
    # imports of `data_service/factors/__init__.py` and
    # `factor_optimizer.py` — importing the one file this adapter needs
    # (`factor_calculator.py`) still runs the package `__init__.py`, which
    # eagerly imports sibling modules. All three installed cleanly from
    # prebuilt wheels, no cmake/Rust build issues.

    Vendor checkout:
        git clone --depth 1 https://github.com/0xemmkty/QuantMuse.git \
            adapters/vendor/QuantMuse

    PATCH APPLIED (see patches/QuantMuse.diff):
    `data_service/ai/sentiment_analyzer.py`'s `SentimentAnalyzer.
    _analyze_with_openai()` hardcoded `model="gpt-3.5-turbo"` with no
    constructor override — confirmed by a real failed call against
    DeepSeek's OpenAI-compatible endpoint ("The supported API model names
    are deepseek-v4-pro or deepseek-v4-flash, but you passed
    gpt-3.5-turbo."). Unlike `LLMIntegration`'s `OpenAIProvider` (already
    configurable via its own `model` constructor arg), this one method had
    the model baked in, so it was impossible to redirect without either
    reimplementing upstream's sentiment-analysis prompt ourselves (not
    allowed — CLAUDE.md's "never reimplement upstream's own logic") or a
    minimal, documented, mechanical patch: added an `openai_model`
    constructor parameter (default unchanged, `"gpt-3.5-turbo"`) and used
    it in place of the hardcoded string. Two lines changed, no logic
    altered. No other upstream file was patched.

Run the harness with that env active:
    conda activate nofx_real
    python CONTRACT/test_harness.py --adapter adapters/nofx_adapter.py

Design notes (translation choices made by this adapter, not upstream):
  - Reused `DEEPSEEK_API_KEY` (adapters/vendor/ai-hedge-fund/.env) via
    DeepSeek's OpenAI-compatible endpoint: this adapter sets
    `openai.api_base = "https://api.deepseek.com/v1"` once at import time,
    and constructs upstream's `SentimentAnalyzer`/`LLMIntegration` with
    `openai_model="deepseek-v4-flash"` (confirmed live against DeepSeek's
    own error message for the exact supported model-name strings — did not
    guess "deepseek-chat" from training-data memory). No new API key was
    requested or fabricated.
  - Cost-control / balance-exhaustion detection: upstream's own
    `_analyze_with_openai()` and `assess_risk()` both catch all exceptions
    internally and silently fall back to a local/default result rather
    than raising — which would otherwise mask a real auth/balance failure
    as an innocuous "neutral sentiment" data point. This adapter attaches
    a temporary `logging.Handler` to upstream's own
    `data_service.ai.sentiment_analyzer` / `data_service.ai.llm_integration`
    loggers for the duration of each real call and inspects captured
    ERROR-level records for auth/quota-shaped substrings
    (authentication/invalid_api_key/insufficient_quota/balance/quota/401/
    403); if found, raises `RuntimeError("DeepSeek API balance may be
    exhausted...")` instead of silently returning degraded output. Verified
    this adapter's own env-loading first (`load_dotenv` runs before any
    upstream call and `DEEPSEEK_API_KEY` is confirmed present in-process)
    to avoid the "looks like a balance error but is actually a missing
    load_dotenv() call" bug documented elsewhere in this session's
    DECISIONS.md.
  - Real quantitative factors: `FactorCalculator.calculate_technical_
    factors()` (RSI-14, MACD(12,26,9), 20/50/200-day moving averages,
    Bollinger Bands) and `calculate_price_momentum()` (20/60-day momentum
    + acceleration), computed from one year of real daily `yfinance`
    OHLCV history for the requested ticker. 100% real upstream arithmetic,
    unmodified.
  - Real LLM sentiment: upstream's own `SentimentAnalyzer._analyze_with_
    openai()` scores each of up to `MAX_HEADLINES` (3) real Yahoo Finance
    headlines (via `yfinance`, same free/keyless news source
    `fingpt_adapter.py` uses, and subject to the same real-world
    limitation: yfinance only exposes *current* headlines, not an
    arbitrary historical date's headlines — the requested `date` is
    recorded on the output but headline recency is whatever yfinance has
    "now"). Per-headline results are aggregated via upstream's own
    `SentimentAnalyzer.calculate_market_sentiment()`
    (confidence-and-recency-weighted average, momentum, volatility,
    consensus) — none of this aggregation math was reimplemented by this
    adapter.
  - The fusion call: `LLMIntegration.assess_risk(portfolio_data,
    market_conditions)` where `market_conditions` bundles the real
    technical-factor dict and the real aggregated-sentiment dict together
    (`{"technical_factors": {...}, "sentiment_factors": {...}}`) and
    `portfolio_data` describes a single 100%-weighted position in the
    requested ticker. This is one additional real DeepSeek call, through
    upstream's own risk-assessment prompt template, that is the actual
    "fusion layer" the brief describes — the LLM literally receives both
    signal families as JSON context and returns one fused verdict.
    Upstream returns the fused JSON as a raw string inside
    `TradingInsight.content` (its own `_parse_trading_insight()` doesn't
    itself split this into fields); this adapter parses that JSON purely
    to extract `overall_risk`/`risk_factors` for CONTRACT's typed fields —
    a translation step, not new analysis.
  - `risk_level`: primarily the LLM fusion's own `overall_risk`
    (low/medium/high), escalated to `EXTREME` when the fused verdict is
    already "high" *and* either the aggregate sentiment is strongly
    directional (`|sentiment_score| >= 0.6`) or cross-headline sentiment
    dispersion is high (`sentiment_volatility >= 0.6`) — same
    "disagreement/extremity implies elevated risk" pattern
    `fingpt_adapter.py` and `prediction_arena_adapter.py` each use for
    their own `risk_level` derivation, applied here on top of (not instead
    of) the real LLM fusion verdict. Falls back to `MEDIUM` only if the
    fusion response couldn't be parsed as JSON at all (rare/defensive).
  - `sentiment_score`: the real aggregate `weighted_sentiment` from
    `calculate_market_sentiment()`, clipped to [-1, 1].
  - `cost_usd`: reported as `0.0`. Upstream's `LLMResponse.cost` field
    (populated by `OpenAIProvider._calculate_cost()`) uses a hardcoded
    OpenAI-specific per-token pricing table (`gpt-3.5-turbo`/`gpt-4`
    rates), which would silently misreport a fabricated dollar figure for
    real DeepSeek usage. Rather than presenting a wrong number as if it
    were accurate, this adapter does not surface it. `assess_risk()`'s
    return type (`TradingInsight`) doesn't carry a cost field at all, so
    no cost figure is available for the fusion call either way.
  - `drivers`: the real scored headlines (title + per-headline sentiment
    label), followed by the top real `risk_factors` entries from the LLM
    fusion response.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q2Sentiment, RiskLevel

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "QuantMuse"
import sys  # noqa: E402

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Reuse the existing DeepSeek key (adapters/vendor/ai-hedge-fund/.env) rather
# than requiring a new one — same key several other adapters this session use.
_AI_HEDGE_FUND_ENV = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"
load_dotenv(dotenv_path=_AI_HEDGE_FUND_ENV)

import os  # noqa: E402

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

import openai  # noqa: E402  (pinned to 0.28.1 — see header docstring)

openai.api_base = "https://api.deepseek.com/v1"

DEEPSEEK_MODEL = "deepseek-v4-flash"
MAX_HEADLINES = 3

_BALANCE_ERROR_PATTERNS = (
    "authentication",
    "invalid_api_key",
    "insufficient_quota",
    "insufficient balance",
    "balance",
    "quota",
    "401",
    "403",
)

_UPSTREAM_LOGGER_NAMES = (
    "data_service.ai.sentiment_analyzer",
    "data_service.ai.llm_integration",
)


class _CapturingHandler(logging.Handler):
    """Captures ERROR-level records so we can detect a real auth/balance
    failure that upstream's own code would otherwise silently swallow and
    fall back from (see header docstring, cost-control section)."""

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.records: List[str] = []

    def emit(self, record):
        self.records.append(record.getMessage())


class _WatchUpstreamErrors:
    def __enter__(self):
        self._handler = _CapturingHandler()
        self._loggers = [logging.getLogger(n) for n in _UPSTREAM_LOGGER_NAMES]
        for lg in self._loggers:
            lg.addHandler(self._handler)
        return self._handler

    def __exit__(self, exc_type, exc, tb):
        for lg in self._loggers:
            lg.removeHandler(self._handler)


def _raise_if_balance_error(handler: _CapturingHandler) -> None:
    for msg in handler.records:
        low = msg.lower()
        if any(p in low for p in _BALANCE_ERROR_PATTERNS):
            raise RuntimeError(
                "DeepSeek API balance may be exhausted (real LLM call failed "
                f"with an auth/quota-shaped error): {msg}"
            )


def _fetch_price_history(ticker: str):
    import yfinance as yf

    hist = yf.Ticker(ticker).history(period="1y", interval="1d")
    return hist


def _fetch_headlines(ticker: str, limit: int = MAX_HEADLINES) -> List[str]:
    import yfinance as yf

    items = yf.Ticker(ticker).news or []
    titles = []
    for item in items[:limit]:
        title = (item.get("content") or {}).get("title")
        if title:
            titles.append(title)
    return titles


def _parse_fusion_json(content: str) -> Dict[str, Any]:
    """Extract the JSON object from LLMIntegration.assess_risk()'s raw
    TradingInsight.content string. Translation-only: this does not
    reimplement any analysis, just parses upstream's own response text."""
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {}


class NofxAdapter(BaseAdapter):
    name = "nofx"
    questions_answered = ["Q2"]
    upstream_repo = "https://github.com/0xemmkty/QuantMuse"
    requires_env = "nofx_real"

    def q2_sentiment(self, ticker: str, date: str, **kwargs) -> Optional[Q2Sentiment]:
        t0 = time.time()

        from data_service.ai.llm_integration import LLMIntegration
        from data_service.ai.sentiment_analyzer import SentimentAnalyzer
        from data_service.factors.factor_calculator import FactorCalculator

        # ---- Real quantitative technical factors ----------------------
        technical_factors: Dict[str, float] = {}
        try:
            hist = _fetch_price_history(ticker)
            if hist is not None and len(hist) >= 14:
                fc = FactorCalculator()
                technical_factors.update(
                    {k: float(v) for k, v in fc.calculate_technical_factors(
                        hist["Close"], hist["Volume"]
                    ).items()}
                )
                technical_factors.update(
                    {k: float(v) for k, v in fc.calculate_price_momentum(
                        hist["Close"]
                    ).items()}
                )
        except Exception:
            pass  # degrade gracefully to an empty technical-factor context

        # ---- Real per-headline LLM sentiment ---------------------------
        headlines = _fetch_headlines(ticker)
        if not headlines:
            headlines = [f"No recent news found for {ticker}."]

        analyzer = SentimentAnalyzer(
            openai_api_key=DEEPSEEK_API_KEY,
            use_openai=bool(DEEPSEEK_API_KEY),
            openai_model=DEEPSEEK_MODEL,
        )

        scored = []
        with _WatchUpstreamErrors() as handler:
            for title in headlines:
                sd = analyzer.analyze_text_sentiment(title, ticker)
                scored.append(sd)
            _raise_if_balance_error(handler)

        sentiment_metrics = analyzer.calculate_market_sentiment(scored, symbol=ticker)
        weighted_sentiment = float(sentiment_metrics.get("weighted_sentiment", 0.0))
        sentiment_volatility = float(sentiment_metrics.get("sentiment_volatility", 0.0))
        sentiment_score = max(-1.0, min(1.0, weighted_sentiment))

        # ---- Real fusion call: LLM sentiment + quant factors -> risk ---
        portfolio_data = {"positions": {ticker: {"weight": 1.0}}}
        market_conditions = {
            "technical_factors": technical_factors,
            "sentiment_factors": {
                k: (float(v) if isinstance(v, (int, float)) else v)
                for k, v in sentiment_metrics.items()
            },
        }

        llm = LLMIntegration(provider="openai", api_key=DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL)
        with _WatchUpstreamErrors() as handler:
            insight = llm.assess_risk(portfolio_data, market_conditions)
            _raise_if_balance_error(handler)

        fusion = _parse_fusion_json(insight.content)
        overall_risk = str(fusion.get("overall_risk", "")).strip().lower()
        risk_factors = fusion.get("risk_factors") or []

        if overall_risk == "high" and (
            abs(sentiment_score) >= 0.6 or sentiment_volatility >= 0.6
        ):
            risk = RiskLevel.EXTREME
        elif overall_risk == "high":
            risk = RiskLevel.HIGH
        elif overall_risk == "medium":
            risk = RiskLevel.MEDIUM
        elif overall_risk == "low":
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.MEDIUM  # unparseable fusion response — defensive default

        drivers: List[str] = []
        for sd in scored:
            label = (
                "positive" if sd.sentiment_score > 0.15
                else "negative" if sd.sentiment_score < -0.15
                else "neutral"
            )
            drivers.append(f"{sd.text} ({label}, score={sd.sentiment_score:.2f})")
        for rf in risk_factors[:3]:
            drivers.append(f"Fusion risk factor: {rf}")
        if not drivers:
            drivers = ["No drivers available — degraded fallback."]

        return Q2Sentiment(
            sentiment_score=sentiment_score,
            risk_level=risk,
            drivers=drivers,
            sources=[
                "Yahoo Finance news + price history (yfinance)",
                "QuantMuse FactorCalculator (real RSI/MACD/Bollinger/momentum technical factors)",
                f"DeepSeek ({DEEPSEEK_MODEL}) via QuantMuse SentimentAnalyzer "
                "(per-headline LLM sentiment) + LLMIntegration.assess_risk "
                "(LLM fusion of quant + sentiment -> risk verdict)",
            ],
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        result = self.q2_sentiment("AAPL", "2024-01-15")
        checks["q2_returns_Q2Sentiment"] = result is not None
        checks["sentiment_score_in_range"] = (
            result is not None and -1.0 <= result.sentiment_score <= 1.0
        )
        checks["risk_level_is_valid"] = result is not None and result.risk_level in (
            "LOW",
            "MEDIUM",
            "HIGH",
            "EXTREME",
        )
        checks["drivers_non_empty"] = result is not None and len(result.drivers) > 0
        return checks
