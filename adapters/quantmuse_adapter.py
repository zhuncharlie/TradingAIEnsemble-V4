"""
adapters/quantmuse_adapter.py — wraps github.com/0xemmkty/QuantMuse (Q2, Q3).

RENAME NOTE (this file was `adapters/nofx_adapter.py` until this task): this
adapter was originally named after the "NoFx" target brief even though its
actual upstream is `0xemmkty/QuantMuse` — the literal `NoFxAiOS/nofx` GitHub
project was investigated and rejected (see "REPO CHOICE" below) and
QuantMuse was substituted as the closest real match. That left a
file/class named `nofx_adapter.py`/`NofxAdapter` wrapping a project that has
nothing to do with NoFx, which is misleading on inspection. This task
re-verified that the real `NoFxAiOS/nofx` project is still infeasible to
wrap faithfully as of 2026-07-16/17 (see "2026-07 RE-VERIFICATION ADDENDUM"
appended near the end of this docstring, added without altering the
original rejection analysis below) and renamed this file/class/`name` to
match its actual upstream (`nofx_adapter.py`/`NofxAdapter`/`"nofx"` ->
`quantmuse_adapter.py`/`QuantMuseAdapter`/`"quantmuse"`), freeing the
`nofx_adapter.py` filename for a possible future adapter that genuinely
wraps NoFx if it ever becomes wrappable. The original rejection rationale,
security screening, environment notes, and design notes below are kept
verbatim as historical record — only the file/class/`name` identifiers
changed, plus a new "Q3 CAPABILITY RECOVERY" section and the verification
addendum were appended.

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
    python CONTRACT/adapter_runner.py --adapter adapters/quantmuse_adapter.py ...

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

============================================================================
Q3 CAPABILITY RECOVERY (added on rename, this task) — surfacing the real
technical-factor dict as a standalone Q3 signal instead of only folding it
into Q2's risk-assessment context
============================================================================
  Source read directly for this recovery:
  `adapters/vendor/QuantMuse/data_service/factors/factor_calculator.py`,
  specifically `FactorCalculator.calculate_technical_factors()` (rsi, macd,
  macd_signal, macd_histogram, ma_20/50/200, price_vs_ma20/50/200,
  bb_upper/bb_lower/bb_position — all computed from real price history) and
  `.calculate_price_momentum()` (momentum_{20,60,252}d,
  momentum_accel_{20,60,252}d). Also read `.calculate_all_factors()` to check
  for an upstream-native composite/aggregate score across factor families:
  it only concatenates the per-family dicts (momentum + volatility +
  technical + volume + value + quality + size) with no weighting or
  combination logic of its own — there is no real single "composite factor
  value" this adapter could honestly surface.

  Mapping decision: per CLAUDE.md's fabrication rule, this adapter does NOT
  invent its own cross-factor weighted average (that would be new,
  adapter-authored "analysis" masquerading as upstream signal). Instead,
  `q3_signal()` surfaces RSI-14 (`factors['rsi']` from
  `calculate_technical_factors()`) as the single `Q3Signal.values[ticker]`
  entry, because among the ~13 real readings this method computes it is the
  one that is (a) bounded to a fixed, well-defined [0,100] scale (unlike
  MACD/momentum, whose magnitude depends on the ticker's price level and
  lookback), (b) named by upstream's own `factor_categories['technical']`
  taxonomy as a canonical technical-factor entry, and (c) designed to be
  read standalone (unlike MACD, which needs a signal-line crossover to mean
  anything, or `price_vs_ma*`, which needs a peer/baseline). All other real
  technical/momentum readings this call produces are NOT discarded — they
  are attached as `EvidenceItem`s (kind="technical_indicator") with their
  real numeric values and an explicit upstream source citation.
  `direction`/`strength` are deliberately left `None`: mapping RSI's
  conventional 70/30 overbought/oversold thresholds onto a LONG/SHORT call
  would itself be a new adapter-authored interpretive layer beyond what was
  verified as real upstream output — left unset rather than fabricated.
  `signal_semantics` is set to the schema's own documented example value
  shape, `"factor_value"`, qualified with which specific factor it is.

  Known limitation, disclosed rather than silently fixed: like Q2's
  technical-factor computation this method reuses, `_fetch_price_history()`
  calls `yfinance`'s `period="1y"` history, which returns the most recent
  year of daily bars as of wall-clock call time — NOT a point-in-time
  history ending at `context.data_cutoff`/`context.as_of`. This was already
  true of Q2's technical-factor usage before this task; Q3 inherits the
  same limitation rather than introducing a new one, and it is noted here
  explicitly (via `explanation`) since Q3's "signal/alpha" framing raises
  the causality bar CLAUDE.md sets for time-dependent outputs.

  Classification of what was and was not recovered (see final report for
  the full breakdown): the technical-factor dict itself was previously
  computed-but-discarded (only fed into Q2's LLM risk-assessment context,
  never surfaced as typed output) — now recovered as Q3 `values`/`evidence`.
  No other QuantMuse capability was found to be computed-but-hidden behind
  a private/non-public API, and none required an upstream patch beyond the
  existing `patches/QuantMuse.diff` already documented above.

============================================================================
2026-07 RE-VERIFICATION ADDENDUM — is the real NoFxAiOS/nofx still
infeasible to wrap? (added on rename, this task; original rejection
analysis above is preserved unchanged)
============================================================================
  Re-fetched the live repo (github.com/NoFxAiOS/nofx, GitHub API confirms
  12,576 stars, 3,013 forks, AGPL-3.0, `pushed_at: 2026-07-16` — actively
  maintained, not stale) plus a fresh shallow clone, and re-read
  README.md, docs/architecture/STRATEGY_MODULE.md, SECURITY.md,
  DISCLAIMER.md, and `api/launch_preflight.go` directly (not just prose
  summaries). Findings, some of which have genuinely changed since the
  original rejection and some of which have not:

  1. LLM provider lock-in (part of original blocker (b)) — CHANGED, no
     longer disqualifying on its own: current README ("Models" section):
     "Eight providers with your own keys — DeepSeek, OpenAI, Claude, Qwen,
     Gemini, Grok, Kimi, MiniMax — including custom endpoints and model
     names. Or no keys at all: Claw402 ... A wallet on Base replaces every
     API key." `api/launch_preflight.go`'s `checkLaunchAIWallet()` confirms
     in code that the Claw402 fee-wallet check is *skipped* for any
     non-Claw402 provider ("Non-claw402 providers pay per API key, so both
     checks are skipped."). So a real DeepSeek key genuinely can be plugged
     in today — the original "hard-routed through a proprietary paid
     gateway with no way to plug in DEEPSEEK_API_KEY" claim no longer holds
     as stated.
  2. Not a callable Python library — UNCHANGED, still fully disqualifying
     on its own: the fresh clone is 278 `.go` files vs. 2 unrelated `.py`
     files (CI coverage/PR-comment scripts under `.github/workflows/`, not
     part of the trading system). No `setup.py`/`pyproject.toml`/wheel/
     PyPI package exists anywhere in the tree. The architecture is a Go API
     server + JWT auth + a React/TypeScript web terminal (README's own
     ASCII architecture diagram). There is no Python import surface at all
     to build a thin `CONTRACT`-conformant wrapper around — this adapter
     pattern requires importing upstream Python code directly, which is
     structurally impossible here regardless of the credentials question.
  3. Live-funds-only / no dry-run mode — PARTIALLY CHANGED, but the net
     effect is still disqualifying: `api/launch_preflight.go`'s exchange
     funds check treats testnet specially ("Testnet balances are play
     money — warn instead of block"), and `exchange.Testnet` is a real,
     documented per-exchange config flag (SECURITY.md and DISCLAIMER.md
     both explicitly recommend "Test on testnet first" / "Start with paper
     trading or testnet environments"). So, contrary to the original
     text's "no documented dry-run mode" framing, a genuine no-real-money
     testnet path is documented and code-verified for exchanges that
     expose one (Binance, Hyperliquid). However, this does not make NOFX
     wrappable: NOFX has no batch/point-in-time query API at all — it is
     architected as a single continuously-running Autopilot loop inside a
     stateful multi-user web server (JWT auth, encrypted credential store,
     live dashboard), not a stateless function callable once per
     `context.as_of`. No backtest/historical-replay capability was found
     anywhere in the Go source (grepped for backtest/historical
     replay/point-in-time — the only hits were in an unrelated third-party
     research PDF summary vendored under `docs/research/`, about a
     different project, HKUDS's "AI-Trader" benchmark, not NOFX itself).
     Even fully testnet-funded and BYO-keyed, there is no way to ask NOFX
     "what would you have decided as of 2024-01-15 with data cutoff
     2024-01-15" the way every other adapter in this repo can.
  Conclusion: still REJECTED. The credentials/gateway-lock-in objections
  have softened (point 1 fully, point 3 partially), but point 2 — no
  Python import surface, only a live continuously-running Go/web
  application with no stateless point-in-time decision API — is on its own
  a complete, currently-true, structural blocker to building a faithful
  thin wrapper under this repo's adapter contract. No new
  `adapters/nofx_adapter.py` was written (see step 3 of this task).
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
from CONTRACT.schemas import (
    ConfidenceEstimate,
    ConfidenceKind,
    EvidenceItem,
    OutputScope,
    Q2State,
    Q3Signal,
    QueryContext,
    StateEstimate,
)

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


# Per-ticker cache for the real technical-factor dict (see module header,
# "Q3 CAPABILITY RECOVERY"). q2_state() and q3_signal() both need this exact
# same real FactorCalculator computation; caching means BaseAdapter.run()
# calling both in one pass (questions_answered = ["Q2", "Q3"]) never
# recomputes it or re-fetches yfinance price history twice.
_TECH_FACTORS_CACHE: Dict[str, Dict[str, float]] = {}


def _get_technical_factors(ticker: str) -> Dict[str, float]:
    if ticker in _TECH_FACTORS_CACHE:
        return dict(_TECH_FACTORS_CACHE[ticker])

    from data_service.factors.factor_calculator import FactorCalculator

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
        pass  # degrade gracefully to an empty technical-factor dict

    _TECH_FACTORS_CACHE[ticker] = dict(technical_factors)
    return technical_factors


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


class QuantMuseAdapter(BaseAdapter):
    name = "quantmuse"
    questions_answered = ["Q2", "Q3"]
    upstream_repo = "https://github.com/0xemmkty/QuantMuse"
    # Conda env name is unchanged: the actual environment `nofx_real` (per
    # `conda env list`) still exists and is what this adapter runs under;
    # renaming a live conda environment is outside this task's scope
    # (code-only rename — see module header "RENAME NOTE"). The env's own
    # setup instructions above (git clone / pip installs) are unaffected.
    requires_env = "nofx_real"

    def __init__(self):
        super().__init__()
        self._last_native: Dict[str, dict] = {}

    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        t0 = time.time()

        if not context.targets:
            raise ValueError("quantmuse q2_state requires context.targets[0] (single-asset only).")
        ticker = context.targets[0]
        date = context.data_cutoff or context.as_of

        from data_service.ai.llm_integration import LLMIntegration
        from data_service.ai.sentiment_analyzer import SentimentAnalyzer

        # ---- Real quantitative technical factors (shared cache with
        # q3_signal() — see _get_technical_factors) --------------------
        technical_factors = _get_technical_factors(ticker)

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

        # Open-vocabulary risk category (v2 has no closed RiskLevel enum —
        # "EXTREME" here is the same adapter-authored disagreement-escalation
        # rule as v1, just no longer forced into a fixed 4-value enum).
        if overall_risk == "high" and (
            abs(sentiment_score) >= 0.6 or sentiment_volatility >= 0.6
        ):
            risk_category = "EXTREME"
        elif overall_risk == "high":
            risk_category = "HIGH"
        elif overall_risk == "medium":
            risk_category = "MEDIUM"
        elif overall_risk == "low":
            risk_category = "LOW"
        else:
            risk_category = "MEDIUM"  # unparseable fusion response — defensive default

        sentiment_evidence = [
            EvidenceItem(
                kind="news",
                value=(
                    f"{sd.text} ("
                    + ("positive" if sd.sentiment_score > 0.15 else "negative" if sd.sentiment_score < -0.15 else "neutral")
                    + f", score={sd.sentiment_score:.2f})"
                ),
                source="Yahoo Finance news (yfinance) + QuantMuse SentimentAnalyzer per-headline LLM sentiment",
            )
            for sd in scored
        ]

        risk_evidence = [
            EvidenceItem(kind="model_output", value=f"Fusion risk factor: {rf}", source="QuantMuse LLMIntegration.assess_risk()")
            for rf in risk_factors[:3]
        ]
        if technical_factors:
            risk_evidence.append(
                EvidenceItem(
                    kind="technical_indicator",
                    value=", ".join(f"{k}={v:.3f}" for k, v in list(technical_factors.items())[:5]),
                    source="QuantMuse FactorCalculator (real RSI/MACD/Bollinger/momentum technical factors)",
                )
            )

        states = [
            StateEstimate(
                dimension="sentiment",
                value_numeric=sentiment_score,
                scale="[-1,1]",
                confidence=ConfidenceEstimate(
                    value=max(0.0, min(1.0, 1.0 - sentiment_volatility)),
                    kind=ConfidenceKind.HEURISTIC,
                    raw_value=sentiment_volatility,
                    method="1 - sentiment_volatility (adapter heuristic, not an upstream-native confidence)",
                ),
                evidence=sentiment_evidence or None,
            ),
            StateEstimate(
                dimension="risk",
                value_category=risk_category,
                evidence=risk_evidence or None,
            ),
        ]

        result = Q2State(context=context, states=states)

        self._last_native["q2"] = {
            "upstream": {
                "sentiment_metrics": sentiment_metrics,
                "technical_factors": technical_factors,
                "fusion_overall_risk": overall_risk,
                "fusion_risk_factors": risk_factors,
                "fusion_raw_content": insight.content,
            },
            "adapter_derived": {"ticker": ticker, "date": date, "risk_category": risk_category},
        }
        self._last_latency_sec = getattr(self, "_last_latency_sec", 0.0) + (time.time() - t0)
        return result

    # ------------------------------------------------------------------
    # Q3 — real technical factors (RSI-14) surfaced as a standalone signal.
    # See module header "Q3 CAPABILITY RECOVERY" for the full mapping
    # rationale: no upstream-native cross-factor composite exists, so a
    # single bounded, standalone-interpretable real factor (RSI-14) is used
    # as `values`, and every other real factor reading is preserved as
    # `evidence` rather than discarded.
    # ------------------------------------------------------------------
    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        if not context.targets:
            raise ValueError("quantmuse q3_signal requires context.targets[0] (single-asset only).")
        ticker = context.targets[0]
        date = context.data_cutoff or context.as_of

        technical_factors = _get_technical_factors(ticker)
        if not technical_factors or "rsi" not in technical_factors:
            return None  # insufficient real price history (< 14 bars) to compute any real factor

        rsi_value = technical_factors["rsi"]

        evidence = [
            EvidenceItem(
                kind="technical_indicator",
                value=f"{k}={v:.4f}",
                source=(
                    "QuantMuse FactorCalculator.calculate_technical_factors()/"
                    "calculate_price_momentum() (real figures from 1y yfinance OHLCV history)"
                ),
            )
            for k, v in technical_factors.items()
            if k != "rsi"
        ]

        explanation = (
            f"RSI-14 (14-period relative strength index) is upstream QuantMuse's own real "
            f"FactorCalculator.calculate_technical_factors() output for {ticker} as of yfinance's "
            f"most recent 1-year daily history at call time. No upstream-native composite/aggregate "
            f"exists across FactorCalculator's ~13 real technical/momentum readings "
            f"(calculate_all_factors() only concatenates per-family dicts, no combination logic of "
            f"its own) -- per CLAUDE.md's fabrication rule this adapter does not invent a weighted "
            f"average across them. RSI-14 was chosen as the single `values` entry because it is "
            f"bounded to a fixed [0,100] scale and is upstream's own canonical standalone technical "
            f"reading (unlike MACD, which needs a signal-line crossover, or price_vs_ma*, which needs "
            f"a peer baseline, to be meaningful alone). All other real readings "
            f"(macd/macd_signal/macd_histogram, ma_20/50/200, price_vs_ma20/50/200, "
            f"bb_upper/bb_lower/bb_position, momentum_{{20,60,252}}d, momentum_accel_*) are attached "
            f"as evidence, not discarded. direction/strength are left unset: applying RSI's "
            f"conventional 70/30 overbought/oversold thresholds to derive a LONG/SHORT call would be "
            f"a new adapter-authored interpretive layer, not verified real upstream output. "
            f"Known limitation: yfinance's period='1y' price fetch is relative to wall-clock call "
            f"time, not point-in-time as of {date} (same limitation already present in this "
            f"adapter's Q2 technical-factor usage before this recovery)."
        )

        result = Q3Signal(
            context=context,
            signal_semantics=(
                "factor_value: RSI-14 (QuantMuse FactorCalculator.calculate_technical_factors -- "
                "a single named real technical factor reading, not a forecast or cross-factor composite)"
            ),
            values={ticker: float(rsi_value)},
            score_scale="[0,100] RSI (conventionally <30 'oversold', >70 'overbought' -- not applied here as a direction/strength call, see explanation)",
            direction=None,
            strength=None,
            expected_returns=None,
            factor_expression=None,
            confidence=None,
            evidence=evidence or None,
            explanation=explanation,
        )

        self._last_native["q3"] = {
            "upstream": {"technical_factors": technical_factors},
            "adapter_derived": {"ticker": ticker, "date": date, "rsi_used": rsi_value},
        }
        self._last_latency_sec = getattr(self, "_last_latency_sec", 0.0) + (time.time() - t0)
        return result

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output, same pattern as this
    # session's other migrated adapters. Unlike a single-q-method adapter
    # (e.g. finrl_adapter.py), this adapter answers both Q2 and Q3, so
    # native output from each is kept under its own key (self._last_native)
    # rather than one overwriting the other, and latency is accumulated
    # across whichever q* methods BaseAdapter.run() actually calls.
    # ------------------------------------------------------------------
    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window=None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ):
        self._last_native = {}
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native:
            updates["native_output"] = self._last_native
        if self._last_latency_sec:
            updates["run"] = result.run.model_copy(update={"latency_sec": self._last_latency_sec})
        if updates:
            result = result.model_copy(update=updates)
        return result

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
            universe=["AAPL"],
        )
        result = self.q2_state(context)
        checks["q2_returns_Q2State"] = result is not None
        if result is not None:
            checks["q2_context_echoed"] = result.context == context
            checks["q2_states_nonempty"] = len(result.states) >= 1
            sentiment_states = [s for s in result.states if s.dimension == "sentiment"]
            checks["sentiment_state_present"] = len(sentiment_states) == 1
            if sentiment_states:
                checks["sentiment_score_in_range"] = -1.0 <= sentiment_states[0].value_numeric <= 1.0
            risk_states = [s for s in result.states if s.dimension == "risk"]
            checks["risk_state_present"] = len(risk_states) == 1
            if risk_states:
                checks["risk_category_is_valid"] = risk_states[0].value_category in ("LOW", "MEDIUM", "HIGH", "EXTREME")

        q3 = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = q3 is not None
        if q3 is not None:
            checks["q3_context_echoed"] = q3.context == context
            checks["q3_values_nonempty"] = len(q3.values) > 0
            checks["q3_rsi_in_range"] = 0.0 <= q3.values.get("AAPL", -1.0) <= 100.0
        return checks
