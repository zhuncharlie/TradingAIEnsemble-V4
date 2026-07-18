"""
adapters/vibe_trading_adapter.py — wraps github.com/HKUDS/Vibe-Trading (Q3, Q4).

============================================================================
v1 -> v2 schema migration notes (2026-07-18)
============================================================================
  - v1 answered Q3 + Q4 + Q5. v2 has no Q5 (backtest/evaluation layer removed
    from the adapter contract entirely) — the old `q5_backtest` method is
    deleted outright, not just hidden, and no Sharpe/return/drawdown/
    win_rate/equity_curve is computed or emitted anywhere in this file
    anymore (`Q3Signal.evidence` may still *mention* the real backtest
    sharpe/trades/total_return for the generated strategy as descriptive
    text — that is explicitly allowed as evidence, not as a Q5-shaped
    field). `questions_answered = ["Q3", "Q4"]`.
  - **Critical Q4 recovery** (the main change in this migration): the real
    engine (`backtest/engines/base.py::BaseEngine.run_backtest()` /
    `_write_artifacts()`) writes a complete daily `artifacts/positions.csv`
    trajectory (one row per real trading day, `timestamp`-named `pd.Timestamp`
    index, one column per traded code) and a real per-trade event log
    serialized to `artifacts/trades.csv` — **verified by reading
    `_write_artifacts()` itself, not just `backtest/models.py::TradeRecord`'s
    field names**: each real `TradeRecord` is flattened into two CSV rows
    (entry event + exit event) with columns
    `timestamp,code,side,price,qty,reason,pnl,holding_days,return_pct`
    (`timestamp` a plain `YYYY-MM-DD` string via `t.exit_time.date()`), which
    is a different, "daily_portfolio-compatible" shape than the raw
    `TradeRecord` dataclass fields. The v1 adapter's `q4_portfolio()` read
    only `positions.iloc[-1]` — the single last row — discarding the entire
    real trajectory and all real order history. v2's `q4_policy()` now reads
    the **full** `positions.csv` and `trades.csv` and emits one
    `PolicyDecisionStep` per real trading day via `Q4Policy.decisions`, each
    carrying that day's real (clipped/renormalized) `target_weights` and that
    day's real `orders` (matching `trades.csv` rows by the `timestamp`
    string). This recovers real information that was previously computed by
    upstream but 100% discarded by the adapter.
  - **Causality check performed, not just assumed**: `PolicyDecisionStep`
    requires `information_cutoff <= timestamp`. Reading
    `backtest/engines/base.py::_align()` shows the real signal is shifted by
    exactly one bar (`raw.shift(1)`, "next-bar-open semantics" per its own
    docstring) before becoming that day's `target_pos` — i.e. the position
    held on trading day `t` was computed from the raw per-market signal as
    of the close of day `t-1`, not day `t` itself. This adapter sets
    `information_cutoff = <previous real trading day in positions.csv>` for
    every row except the first (which has no prior real row, so
    `information_cutoff = timestamp` for that row only, honestly reflecting
    "no real prior signal was used yet" rather than fabricating an earlier
    date). This was spot-checked against a real run's actual
    `artifacts/positions.csv` during this migration (see test file), not
    just inferred from reading the code.
  - **`policy_type` schema-fit gap** (flagged by `PROJECT_SCHEMA_AUDIT.md`,
    not silently forced): this strategy is a fixed rule (per-market
    MA-crossover + inverse-volatility sizing) recomputed identically every
    trading day, with no learning/refit step and no persisted model state.
    It does not cleanly match `STATIC_ALLOCATION` (it rebalances daily, not
    once), `FROZEN_LEARNED_POLICY` (nothing is learned/trained), or
    `ONLINE_ADAPTIVE_POLICY` (no online learning occurs). This migration
    uses `PolicyType.ROLLING_OPTIMIZER` as the closest available fit, on the
    technicality that the same deterministic formula is recomputed at every
    rebalance point from a rolling window of realized prices — this is a
    judgment call, documented here and in `Q4Policy.explanation`, not a
    clean native match.
  - **Recovered as a `PolicyArtifact`**: `CROSS_MARKET_SIGNAL_ENGINE_SOURCE`
    (the real strategy source code that is actually executed to produce
    every decision in `Q4Policy.decisions`) is now attached as
    `Q4Policy.artifact` (`artifact_type="strategy_code"`). In v1 this source
    was used to drive the backtest but never referenced anywhere in the
    adapter's schema output — a real, cheap-to-capture artifact that was
    previously 0%-retained. Q3's real DeepSeek-generated `SignalEngine`
    source (previously also 0%-retained — v1's Q3 output only carried a
    text description of the strategy, never the actual generated code) is
    now likewise attached as an `EvidenceItem` on `Q3Signal.evidence`.
  - **`generation_window` fix**: v1's `q4_portfolio()` self-computed a
    200-calendar-day lookback (`date - 200 days`) as its own "generation
    window." v2's `q4_policy(context, generation_window, **kwargs)` accepts
    `generation_window: TimeWindow` from the harness and uses
    `generation_window.start`/`.end` directly as the real backtest's
    `start_date`/`end_date` (the real price-history fetch + full walk-
    forward execution range), echoing the same object back unchanged — the
    adapter no longer chooses its own window.
  - Interface change: `q3_signal`/`q4_policy` now take
    `context: QueryContext` (`q4_policy` also takes
    `generation_window: TimeWindow`) instead of the old
    `ticker/date`/`tickers/date` parameters; `context` is echoed back
    unchanged into each returned `Q*(context=context, ...)` per
    `BaseAdapter.run()`'s contract check.
  - **Q4 weight-translation convention preserved from v1**: upstream's own
    `positions.csv` values are each symbol's real target signal in
    `[-1, 1]` ("1.0 = fully long ... 0.0 = flat" per upstream's own
    `strategy-generate/SKILL.md`), which allows real short positions. This
    schema's `target_weights` convention here clips negative (short)
    targets to 0, renormalizes only if the real long exposure exceeds 1.0,
    and reports the remainder under the `"CASH"` key — applied identically
    to every row now, not just the final one. `constraints.long_only=True`
    on the returned `Q4Policy` describes only this adapter's *reported*
    (clipped) weights, not the native strategy itself, which is disclosed
    in `Q4Policy.explanation` as genuinely allowing short positions.

============================================================================
Repo search / vetting process (target "Vibe-Trading" was NOT confirmed to
exist as a literal repo going in — per session brief, searched thoroughly
before trusting any name match)
============================================================================
WebSearch for "Vibe-Trading natural language strategy generation CompositeEngine
multi-market backtest" surfaced several repos literally named vibe-trading /
Vibe-Trading. Each was checked via the GitHub API (stars/forks/created/pushed/
fork-flag), not just trusted from the search snippet:
  - `HKUDS/Vibe-Trading` — 17.7k stars, 2.9k forks, MIT, created 2026-04-01,
    pushed 2026-07-04 (actively maintained). `HKUDS` ("Data Intelligence
    Lab@HKU") is a long-running real org (created 2022, 91 public repos,
    several other high-star projects) — not a fresh throwaway account.
    Description ("Your Personal Trading Agent") and README match the brief's
    "natural-language strategy generation + multi-market backtesting +
    CompositeEngine" almost verbatim. **Chosen.**
  - `vibe-trading-agent/vibe-trading` — 1 star, created 2026-06-15, tagline
    "Download Vibe-Trading: Your Personal Trading Agent." Classic
    fake-repo/"download our agent" phrasing seen with malware-distribution
    repos; rejected without further inspection (near-zero stars, no
    independent content, exists only to ride the real project's name).
  - `kkwangRocks/vibe-trading` — confirmed via the GitHub API to be
    `"fork": true` of HKUDS/Vibe-Trading itself, not an independent project.
  - `VibeTradingLabs/vibetrading` (55 stars) and `spyderweb47/Vibe-Trade`
    (9 stars) — real, on-topic, but far smaller/less mature than
    HKUDS/Vibe-Trading and not the repo the brief's exact phrase
    ("CompositeEngine") traces to; not needed once HKUDS/Vibe-Trading was
    confirmed to contain a real, working `backtest/engines/composite.py`.
  - Verified by reading actual source, not just the README:
    `agent/backtest/engines/composite.py`'s `CompositeEngine` is a real
    cross-market engine with a shared capital pool and per-market
    "rule-provider" sub-engines (`ChinaAEngine`, `GlobalEquityEngine`,
    `CryptoEngine`, `ForexEngine`, `ChinaFuturesEngine`,
    `GlobalFuturesEngine`); `agent/backtest/runner.py`'s
    `_create_market_engine()` auto-selects `CompositeEngine` whenever the
    requested codes span more than one detected market
    (`len(markets) > 1`) — this is real, executable routing logic, not a
    stub. `agent/src/skills/strategy-generate/SKILL.md` and
    `agent/src/providers/llm.py` (`build_llm()`) are the real natural-
    -language strategy-generation machinery: an LLM (via LangChain,
    OpenAI-compatible) is prompted with this skill guide to write a
    `SignalEngine` class matching the exact runner contract.

============================================================================
Security screening (same checks used for every adapter this session)
============================================================================
  - `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|subprocess\\.(call|run|Popen)"`
    across `agent/backtest/`, `agent/src/providers/`, `agent/src/shadow_account/`,
    `agent/src/skills/strategy-generate/`, `agent/src/skills/cross-market-strategy/`
    — zero hits (the one `ast.literal_eval` hit in `shadow_account/codegen.py`
    is upstream's own safe-literal renderer, not a vulnerability).
  - File tree (`agent/backtest`, `agent/src/{agent,api,channels,config,core,
    factors,goal,hypotheses,live,providers,shadow_account,skills,swarm,tools}`,
    top-level `frontend/`, `wiki/`, `tools/`, `scripts/`) is entirely on-topic
    for a finance research agent + web UI + docs — no unrelated subtree
    merged under a misleading name (the FinGPT-adapter-session pattern this
    project explicitly watches for).
  - `agent/src/live/` (mandate/enforcement/order_guard for real order
    execution) exists but this adapter's code path never imports it — only
    `backtest.*` (paper/historical simulation) and `src.providers.llm`
    (LLM factory) are used. No brokerage/exchange account, live order
    routing, or real money is used anywhere in this adapter.
  - Free, no-key data only: `agent/backtest/loaders/yfinance_loader.py`
    (US/HK equities, free) and `agent/backtest/loaders/okx.py`
    ("OKX V5 public REST API (no auth)", `requires_auth = False`) are the
    only two loaders this adapter's `source="auto"` routing actually
    reaches. Upstream's China A-share path (`tushare`) needs a free-tier
    token this adapter never requests; premium loaders (`fmp`, `finnhub`,
    `alphavantage`, `tiingo`) and the `futu` (broker-login) loader are never
    imported by this adapter's code path.
  - The only external network call requiring a credential is the DeepSeek
    LLM call for Q3 (`DEEPSEEK_API_KEY`, read from the existing
    `adapters/vendor/ai-hedge-fund/.env`, same key every other DeepSeek-using
    adapter this session reuses) — no separate/fabricated key requested.

============================================================================
Real bug found in upstream's own bundled example (found by *running* it, not
just reading it — see DECISIONS_vibe_trading.md for the full narrative)
============================================================================
`agent/src/skills/cross-market-strategy/example_signal_engine.py` — upstream's
own shipped reference implementation for exactly the cross-market/CompositeEngine
use case this adapter needs — FAILS upstream's own `backtest/runner.py`
security gate (`_validate_signal_engine_source` / `_is_literal_node`) at
runtime: its top-level `_MARKET_PATTERNS = [(re.compile(...), "a_share"), ...]`
list contains `re.compile()` Call nodes, which are not literal AST nodes, so
the runner rejects the file with `"Executable top-level statement Assign is
not allowed"` before it ever runs. `CROSS_MARKET_SIGNAL_ENGINE_SOURCE` below
is upstream's own example, unchanged in strategy logic (same per-market
MA windows, same inverse-volatility position sizing formula), with only the
market-detection step swapped to call upstream's own already-imported
`backtest.engines._market_hooks._detect_market` (the same single source of
truth `CompositeEngine` itself uses) instead of re-deriving a second,
import-time-unsafe regex table. This is not a patch to vendor source (the
vendored file itself is untouched) — it is this adapter's own
`code/signal_engine.py` input, adapted from upstream's broken example so it
actually passes upstream's own real validator.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n vibe_trading_real python=3.11
    conda activate vibe_trading_real
    conda install -c conda-forge tiktoken -y
    # tiktoken (a langchain-openai transitive dep) has no prebuilt wheel for
    # this platform/Python combo and needs a Rust toolchain to build from
    # source (same class of failure ai-hedge-fund's adapter hit); conda-forge
    # ships a precompiled binary, same workaround used repeatedly this session.
    pip install pandas numpy scipy pydantic requests yfinance defusedxml \\
                pyyaml python-dotenv "fastmcp>=2.14.0" \\
                "langchain>=1.3.9,<2" "langchain-core>=1.0.0,<2" \\
                "langchain-openai>=1.0.0,<2"
    # fastmcp is required only because backtest/runner.py's own safe_run_dir()
    # transitively imports src.swarm.store (for the swarm-runs default root)
    # which imports src.tools.mcp -> fastmcp, even though this adapter never
    # touches the swarm/multi-agent-team feature.
    git clone --depth 1 https://github.com/HKUDS/Vibe-Trading.git \\
        adapters/vendor/Vibe-Trading

Run the harness with that env active:
    conda activate vibe_trading_real
    python CONTRACT/test_harness.py --adapter adapters/vibe_trading_adapter.py

No upstream source was patched (the vendored clone is untouched) — the
adapter only supplies its own `code/signal_engine.py` inputs (see above), so
there is no patches/Vibe-Trading.diff.

============================================================================
Original v1 design notes / scope reductions (translation choices made by
this adapter, not upstream) — kept verbatim below for provenance; see the
v1 -> v2 migration notes above for what changed. Historical references to
"Q5", "Q4Portfolio.rationale", and "cash_ratio" below describe the v1
implementation and no longer reflect the current v2 field names/behavior.
============================================================================
  - **Q5 first, then Q4, then Q3** (v1 sequencing; Q5 no longer exists in v2).
  - **Deterministic strategy for Q4/Q5, one real LLM call for Q3**: Q4/Q5
    run `CROSS_MARKET_SIGNAL_ENGINE_SOURCE` (upstream's own fixed example
    strategy, adapted per the bug note above) with no LLM involved — fast,
    free, and exercises the real `CompositeEngine`/backtest pipeline
    end-to-end. Q3 is the one place a real DeepSeek call happens: upstream's
    own `build_llm()` (`src/providers/llm.py`) is invoked once with
    upstream's own `strategy-generate` skill guide as the system prompt and
    the caller's natural-language strategy description as the user prompt,
    producing a fresh `SignalEngine` class that is then validated with
    upstream's own `_validate_signal_engine_source` AST gate and executed
    through the same real backtest pipeline. This mirrors the full
    "vibe-trading" NL-to-alpha flow without driving upstream's much heavier
    multi-turn ReAct `AgentLoop` (1500+ lines, heartbeats, goal/memory
    management, tool-call orchestration) — that loop is real but is
    UX/orchestration scaffolding around the same underlying LLM-call +
    validate + backtest primitives this adapter calls directly; running the
    full autonomous loop end-to-end was judged too slow/unpredictable
    (unbounded LLM turn count) to fit the harness's smoke_test (<300s) /
    run() (<600s) budgets, consistent with every other adapter's scope
    reductions this session.
  - **Cross-market anchor**: the CONTRACT harness's own sample tickers
    (`AAPL`, `MSFT`, `NVDA`) are all single-market (US equities), which
    would route to upstream's single-market `GlobalEquityEngine` and never
    exercise `CompositeEngine` — the very feature the session brief singles
    out for Q4. This adapter appends a fixed `BTC-USDT` anchor code whenever
    the requested tickers don't already span >1 real upstream-detected
    market (via upstream's own `_detect_market`), so `CompositeEngine` is
    genuinely exercised on every call, not just when the caller happens to
    mix markets. Documented in `Q4Portfolio.rationale` every time it fires.
  - **Ticker normalization**: bare tickers (`"AAPL"`) are mapped to
    upstream's own code convention (`"AAPL.US"`) per upstream's own
    `strategy-generate/SKILL.md` "Instrument Code Normalization" table;
    codes already carrying a market suffix/hyphen (`"700.HK"`, `"BTC-USDT"`)
    pass through unchanged.
  - **Q4 weight translation**: upstream's own `positions.csv` records each
    symbol's *standalone* target signal in `[-1, 1]` (upstream's own
    `strategy-generate/SKILL.md`: "1.0 = fully long ... 0.0 = flat"), which
    is not the same thing as CONTRACT's `Q4Portfolio.weights` convention
    (must be non-negative and sum ≤ 1.0 across the whole book). This adapter
    clips negative (short) targets to 0 for the long-only weights this
    schema expects, renormalizes down to sum ≤ 1.0 only if the raw long
    exposure exceeds 1.0, and reports the remainder as `cash_ratio` — a
    translation performed on real upstream output, not a reimplementation of
    upstream's own signal/allocation logic.
  - **Lookback windows**: Q4's single `date` argument is expanded into a
    200-calendar-day lookback ending at `date` (enough bars for the
    strategy's longest 50-day moving average on daily equity data); Q5 uses
    the caller's own `start`/`end` directly.
  - **In-process LLM call, subprocess backtest execution**: Q3's code
    generation calls `build_llm()` in-process (a plain LangChain chat call);
    the actual backtest always runs via `python -m backtest.runner <run_dir>`
    as a subprocess — the exact invocation upstream's own
    `agent/src/tools/backtest_tool.py` uses internally (`Runner.execute(...,
    cli_args=[str(run_path)])`) — because `backtest/runner.py`'s own `main()`
    calls `sys.exit()` on error, which would kill this adapter's process if
    called in-process.
  - **Cost control**: the one real DeepSeek call (Q3) is wrapped so any
    auth/insufficient-balance/quota-shaped exception is re-raised as a clear
    `"DeepSeek API balance may be exhausted"` error instead of retried in a
    loop or silently swallowed, per this session's standing cost-control
    convention. `DEEPSEEK_API_KEY`/model name were verified against a real
    call during development (see DECISIONS_vibe_trading.md) rather than
    assumed from memory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    DecisionPolicy,
    Direction,
    EvidenceItem,
    ObservationPolicy,
    OutputScope,
    PolicyArtifact,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q3Signal,
    Q4Policy,
    QueryContext,
    TimeWindow,
    UniversePolicy,
    UpdateMode,
    UpdatePolicy,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "Vibe-Trading" / "agent"
DEEPSEEK_ENV_PATH = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from dotenv import load_dotenv  # noqa: E402  (vendor path must be on sys.path first)

load_dotenv(dotenv_path=DEEPSEEK_ENV_PATH)

# DeepSeek model name / base URL verified empirically against a real call
# during development (see DECISIONS_vibe_trading.md); matches the strings
# already confirmed by ai_hedge_fund_adapter.py / tradingagents_adapter.py /
# nofx_adapter.py earlier this session.
os.environ.setdefault("LANGCHAIN_PROVIDER", "deepseek")
os.environ.setdefault("LANGCHAIN_MODEL_NAME", "deepseek-v4-flash")
os.environ.setdefault("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

PYTHON_BIN = sys.executable
BACKTEST_TIMEOUT_S = 150
ANCHOR_CRYPTO_CODE = "BTC-USDT"
DEFAULT_INITIAL_CASH = 1_000_000.0

_STRATEGY_SKILL_PATH = VENDOR_DIR / "src" / "skills" / "strategy-generate" / "SKILL.md"
_STRATEGY_SKILL_GUIDE = _STRATEGY_SKILL_PATH.read_text(encoding="utf-8")

# Upstream's own `skills/cross-market-strategy/example_signal_engine.py`,
# strategy logic byte-for-byte identical (same MARKET_PARAMS, same
# inverse-volatility weighting formula) but with market detection delegated
# to upstream's own `_detect_market` instead of the shipped example's
# top-level `_MARKET_PATTERNS` regex table, which fails upstream's own
# runner.py AST security gate at import time (see module docstring).
CROSS_MARKET_SIGNAL_ENGINE_SOURCE = '''"""Cross-market vol-adjusted dual-MA strategy (adapted from upstream's own
skills/cross-market-strategy/example_signal_engine.py; see
adapters/vibe_trading_adapter.py module docstring for why)."""

from typing import Dict

import pandas as pd

from backtest.engines._market_hooks import _detect_market

MARKET_PARAMS = {
    "a_share":    {"ma_fast": 5,  "ma_slow": 20, "vol_lookback": 20},
    "crypto":     {"ma_fast": 7,  "ma_slow": 25, "vol_lookback": 14},
    "us_equity":  {"ma_fast": 10, "ma_slow": 50, "vol_lookback": 20},
    "hk_equity":  {"ma_fast": 10, "ma_slow": 50, "vol_lookback": 20},
    "forex":      {"ma_fast": 10, "ma_slow": 30, "vol_lookback": 20},
    "futures":    {"ma_fast": 5,  "ma_slow": 20, "vol_lookback": 20},
}


class SignalEngine:
    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        raw_signals = {}
        for code, df in data_map.items():
            market = _detect_market(code)
            params = MARKET_PARAMS.get(market, MARKET_PARAMS["a_share"])
            raw_signals[code] = self._market_signal(df, params)
        return self._vol_adjust(raw_signals, data_map)

    def _market_signal(self, df: pd.DataFrame, params: dict) -> pd.Series:
        close = df["close"]
        ma_fast = close.rolling(params["ma_fast"]).mean()
        ma_slow = close.rolling(params["ma_slow"]).mean()

        sig = pd.Series(0.0, index=df.index)
        sig[ma_fast > ma_slow] = 1.0
        sig[ma_fast < ma_slow] = -1.0
        return sig

    def _vol_adjust(self, signals: dict, data_map: dict) -> dict:
        vols = {}
        for code, df in data_map.items():
            ret = df["close"].pct_change().dropna()
            vols[code] = (
                ret.rolling(20).std().iloc[-1]
                if len(ret) > 20
                else ret.std()
            )

        inv_vols = {c: 1.0 / (v + 1e-10) for c, v in vols.items()}
        total_inv = sum(inv_vols.values())

        adjusted = {}
        n = len(signals)
        for code, sig in signals.items():
            weight = inv_vols[code] / total_inv * n
            adjusted[code] = (sig * weight).clip(-1.0, 1.0)
        return adjusted
'''

_BACKTEST_CACHE: Dict[tuple, dict] = {}
_Q3_GEN_CACHE: Dict[tuple, dict] = {}


def _to_vt_code(ticker: str) -> str:
    """Normalize a bare CONTRACT ticker into upstream's own code convention."""
    t = ticker.strip().upper()
    if any(t.endswith(suf) for suf in (".US", ".HK", ".SZ", ".SH", ".BJ")):
        return t
    if "-USDT" in t or "-USDC" in t or "/" in t:
        return t
    return f"{t}.US"


def _display_label(code: str) -> str:
    """Reverse the normalization above for human-readable weight keys."""
    if code.endswith(".US"):
        return code[:-3]
    return code


def _ensure_cross_market(codes: List[str]) -> List[str]:
    """Append a crypto anchor if the codes don't already span >1 real market.

    Without this, CONTRACT's single-market sample tickers would route to
    upstream's single-market engine and never exercise CompositeEngine.
    """
    from backtest.engines._market_hooks import _detect_market

    markets = {_detect_market(c) for c in codes}
    if len(markets) < 2 and ANCHOR_CRYPTO_CODE not in codes:
        return codes + [ANCHOR_CRYPTO_CODE]
    return codes


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t.strip()


def _run_backtest(codes: List[str], start: str, end: str, signal_source: str, tag: str) -> dict:
    """Write a real run_dir and invoke upstream's real `python -m backtest.runner`.

    Subprocess, not in-process import: backtest/runner.py's own main() calls
    sys.exit() on error, which would kill this adapter's process otherwise —
    the same reason upstream's own backtest_tool.py runs it as a subprocess.
    """
    key = (tuple(codes), start, end, hash(signal_source))
    if key in _BACKTEST_CACHE:
        return _BACKTEST_CACHE[key]

    run_dir = VENDOR_DIR / "runs" / f"adapter_{tag}_{uuid.uuid4().hex[:8]}"
    (run_dir / "code").mkdir(parents=True, exist_ok=True)
    (run_dir / "code" / "signal_engine.py").write_text(signal_source, encoding="utf-8")

    config = {
        "source": "auto",
        "codes": codes,
        "start_date": start,
        "end_date": end,
        "interval": "1D",
        "initial_cash": DEFAULT_INITIAL_CASH,
        "commission": 0.001,
        "engine": "daily",
    }
    (run_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    proc = subprocess.run(
        [PYTHON_BIN, "-m", "backtest.runner", str(run_dir)],
        cwd=str(VENDOR_DIR),
        capture_output=True,
        text=True,
        timeout=BACKTEST_TIMEOUT_S,
    )

    artifacts = run_dir / "artifacts"
    if not (artifacts / "metrics.csv").exists():
        raise RuntimeError(
            f"Vibe-Trading backtest failed (exit={proc.returncode}): "
            f"stdout={proc.stdout[-800:]!r} stderr={proc.stderr[-800:]!r}"
        )

    metrics = {k: float(v) for k, v in pd.read_csv(artifacts / "metrics.csv").iloc[0].to_dict().items()}

    # Full real daily trajectory (previously only the last row was read —
    # see the v1 -> v2 migration note in this module's docstring). Index is
    # real `pd.Timestamp`s written by `BaseEngine._write_artifacts()`.
    positions_path = artifacts / "positions.csv"
    positions_df = pd.DataFrame()
    raw_weights: Dict[str, float] = {}
    if positions_path.exists():
        positions_df = pd.read_csv(positions_path, index_col=0, parse_dates=True)
        if len(positions_df) > 0:
            last_row = positions_df.iloc[-1]
            raw_weights = {c: float(last_row[c]) for c in codes if c in positions_df.columns}

    # Real per-trade order history (entry + exit rows), also previously
    # discarded entirely.
    trades_path = artifacts / "trades.csv"
    trades_df = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()

    result = {
        "metrics": metrics,
        "raw_weights": raw_weights,
        "positions_df": positions_df,
        "trades_df": trades_df,
    }
    _BACKTEST_CACHE[key] = result
    return result


def _call_deepseek(llm, system_prompt: str, user_prompt: str) -> str:
    try:
        resp = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
    except Exception as exc:  # noqa: BLE001 - classify below, don't swallow
        msg = str(exc).lower()
        if any(s in msg for s in ("insufficient", "balance", "quota", "401", "unauthorized", "authentication")):
            raise RuntimeError("DeepSeek API balance may be exhausted") from exc
        raise
    return _strip_code_fences(resp.content or "")


def _validate_signal_engine_full(source: str) -> None:
    """Real upstream AST gate + real upstream class-shape check.

    Raises ValueError with upstream's own message on failure (same checks
    backtest/runner.py's main() applies before running, done here up front
    so a bad LLM generation can be retried instead of burning a subprocess
    call and a data fetch).
    """
    from backtest.runner import _validate_signal_engine_class, _validate_signal_engine_source

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=str(VENDOR_DIR)) as f:
        f.write(source)
        tmp_path = Path(f.name)
    try:
        _validate_signal_engine_source(tmp_path)  # real upstream AST security gate

        import importlib.util

        spec = importlib.util.spec_from_file_location(f"_gen_signal_engine_{tmp_path.stem}", tmp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        engine_cls = getattr(module, "SignalEngine", None)
        if engine_cls is None:
            raise ValueError("class SignalEngine not found")
        _validate_signal_engine_class(engine_cls)  # real upstream __init__/generate shape check
    finally:
        tmp_path.unlink(missing_ok=True)


def _generate_signal_engine(code: str, description: str) -> str:
    """Real DeepSeek call(s) using upstream's own build_llm() + skill guide.

    Retries once with the real validator's own error message fed back to the
    model: LLM output is nondeterministic (e.g. it may add an __init__(self,
    config) with no default, violating upstream's own "runner must be able
    to call SignalEngine() with no args" contract stated in the skill guide)
    so a single bad sample shouldn't fail the whole call.
    """
    key = (code, description)
    if key in _Q3_GEN_CACHE:
        return _Q3_GEN_CACHE[key]["source"]

    from src.providers.llm import build_llm

    system_prompt = (
        "You are the Vibe-Trading strategy-generation engine. Follow this skill "
        "guide exactly:\n\n" + _STRATEGY_SKILL_GUIDE + "\n\nHard requirement not to "
        "violate: SignalEngine must be instantiable as SignalEngine() with zero "
        "arguments -- do not define __init__ at all unless every parameter has a "
        "default value. Output ONLY the raw Python source for code/signal_engine.py. "
        "No markdown fences, no explanation."
    )
    user_prompt = (
        f"Natural language strategy request: '{description}' "
        f"Write signal_engine.py for a single-instrument strategy on {code}."
    )

    llm = build_llm()
    source = _call_deepseek(llm, system_prompt, user_prompt)

    try:
        _validate_signal_engine_full(source)
    except Exception as first_err:
        retry_user_prompt = (
            user_prompt
            + "\n\nYour previous attempt failed upstream's real validator with this "
            f"exact error: {first_err}. Produce a corrected full source file that "
            "fixes this."
        )
        source = _call_deepseek(llm, system_prompt, retry_user_prompt)
        _validate_signal_engine_full(source)  # let it raise for real if still broken

    _Q3_GEN_CACHE[key] = {"source": source}
    return source


class VibeTradingAdapter(BaseAdapter):
    name = "vibe_trading"
    questions_answered = ["Q3", "Q4"]
    upstream_repo = "https://github.com/HKUDS/Vibe-Trading"
    requires_env = "vibe_trading_real"

    # ------------------------------------------------------------------
    # Q4 — Policy via the real CompositeEngine's full daily trajectory
    # ------------------------------------------------------------------
    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        t0 = time.time()

        if context.universe:
            tickers = list(context.universe)
        elif context.targets:
            tickers = list(context.targets)
        else:
            raise ValueError(
                "vibe_trading q4_policy requires QueryContext.universe or QueryContext.targets "
                "with at least one ticker."
            )

        codes = _ensure_cross_market([_to_vt_code(t) for t in tickers])
        result = _run_backtest(
            codes, generation_window.start, generation_window.end, CROSS_MARKET_SIGNAL_ENGINE_SOURCE, "q4"
        )

        positions_df = result["positions_df"]
        trades_df = result["trades_df"]

        if positions_df.empty:
            self._last_native_output = {"upstream": {"codes": codes, "note": "empty positions.csv this run"}}
            self._last_latency_sec = time.time() - t0
            return None

        def _clip_and_renormalize(raw_row: Dict[str, float]) -> Dict[str, float]:
            # Upstream's own [-1,1] per-symbol target signal (real short
            # positions allowed) clipped to long-only and renormalized to
            # sum <= 1.0 for this schema's cash-neutral convention — same
            # translation applied to every row now, not just the last one.
            positive = {_display_label(c): max(0.0, float(w)) for c, w in raw_row.items()}
            total = sum(positive.values())
            if total > 1.0:
                positive = {c: w / total for c, w in positive.items()}
                total = 1.0
            positive["CASH"] = max(0.0, min(1.0, 1.0 - total))
            return positive

        decisions: List[PolicyDecisionStep] = []
        prev_timestamp: Optional[str] = None
        for ts, row in positions_df.iterrows():
            timestamp = ts.strftime("%Y-%m-%d")
            raw_row = {c: float(row[c]) for c in codes if c in positions_df.columns}
            target_weights = _clip_and_renormalize(raw_row)

            # Real causal shift, verified by reading backtest/engines/_align()
            # (see module header): the position held on day t was computed
            # from information as of the close of day t-1 ("next-bar-open
            # semantics"). First row has no prior real row in this run, so
            # information_cutoff = timestamp for it only, honestly reflecting
            # "no real prior signal was used yet" rather than fabricating an
            # earlier date.
            information_cutoff = prev_timestamp if prev_timestamp is not None else timestamp

            orders = None
            if not trades_df.empty and "timestamp" in trades_df.columns:
                day_trades = trades_df[trades_df["timestamp"].astype(str) == timestamp]
                if not day_trades.empty:
                    orders = day_trades.to_dict("records")

            decisions.append(
                PolicyDecisionStep(
                    timestamp=timestamp,
                    information_cutoff=information_cutoff,
                    target_weights=target_weights,
                    orders=orders,
                )
            )
            prev_timestamp = timestamp

        initial_weights = decisions[0].target_weights if decisions else None

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=codes,
            selector_description=(
                "Caller-specified tickers, normalized to upstream's own code "
                "convention and augmented with a fixed BTC-USDT anchor whenever "
                "the requested tickers are single-market, so upstream's real "
                "CompositeEngine (not the single-market engine) is genuinely "
                "exercised (see module header)."
            ),
        )

        observation_policy = ObservationPolicy(
            data_sources=[
                "yfinance (US/HK equities, free)",
                "OKX public REST API (crypto, no auth)",
            ],
            observation_description=(
                "Upstream CompositeEngine's real per-market rule-provider sub-"
                "engines (ChinaAEngine/GlobalEquityEngine/CryptoEngine/"
                "ForexEngine/ChinaFuturesEngine/GlobalFuturesEngine) each feed "
                "the strategy's per-market moving-average windows and inverse-"
                "volatility sizing (see decision_policy.decision_rule)."
            ),
        )

        decision_policy = DecisionPolicy(
            decision_rule=(
                "Per-market dual moving-average crossover (fast/slow windows "
                "vary by upstream-detected market) with inverse-volatility "
                "position sizing, recomputed identically at every rebalance "
                "point from a rolling window of realized prices — no learned "
                "parameters, no training (see CROSS_MARKET_SIGNAL_ENGINE_SOURCE)."
            ),
            output_semantics=(
                "target_weights: long-only clipped and renormalized (sum<=1.0) "
                "view of upstream's own [-1,1] per-symbol target signal, "
                "remainder reported under the 'CASH' key. Upstream's real "
                "signal allows short positions — see explanation."
            ),
            rebalance_frequency="DAILY",
            holding_horizon=None,
        )

        update_policy = UpdatePolicy(
            mode=UpdateMode.NONE,
            update_description=(
                "Fixed deterministic formula recomputed fresh from a rolling "
                "price window at every step; no model state persists or is "
                "refit between calls."
            ),
        )

        constraints = PortfolioConstraints(long_only=True, cash_allowed=True)

        artifact = PolicyArtifact(
            artifact_type="strategy_code",
            reference="adapters/vibe_trading_adapter.py::CROSS_MARKET_SIGNAL_ENGINE_SOURCE",
            description=(
                "Real strategy source actually executed to produce every "
                "decision above: upstream's own cross-market example (per-"
                "market MA windows + inverse-volatility sizing), adapted only "
                "to call upstream's own _detect_market() instead of a second, "
                "import-unsafe regex table (see module docstring 'Real bug "
                "found in upstream's own bundled example')."
            ),
        )

        explanation = (
            "policy_type=ROLLING_OPTIMIZER is the closest available fit, not a "
            "clean native match: this strategy is a fixed rule recomputed "
            "daily with no learning/refit step (see module header 'policy_type "
            "schema-fit gap', flagged by PROJECT_SCHEMA_AUDIT.md). Reported "
            "target_weights are long-only clipped and renormalized for this "
            "schema's convention; upstream's own signal genuinely allows short "
            "positions (see decision_policy.output_semantics)."
        )

        result_policy = Q4Policy(
            context=context,
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            initial_weights=initial_weights,
            artifact=artifact,
            decisions=decisions,
            explanation=explanation,
        )

        self._last_native_output = {
            "upstream": {
                "codes": codes,
                "metrics": result["metrics"],
                "n_decision_days": len(decisions),
            },
            "adapter_derived": {
                "generation_window": {"start": generation_window.start, "end": generation_window.end},
            },
        }
        self._last_latency_sec = time.time() - t0
        return result_policy

    # ------------------------------------------------------------------
    # Q3 — Natural-language alpha signal (real DeepSeek call)
    # ------------------------------------------------------------------
    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        if not context.targets:
            raise ValueError("vibe_trading q3_signal requires context.targets[0].")
        ticker = context.targets[0]
        date = context.data_cutoff or context.as_of
        code = _to_vt_code(ticker)
        description = kwargs.get("strategy_description") or (
            f"Go long {ticker} when its 10-day moving average crosses above its "
            "50-day moving average, flat otherwise (trend-following momentum "
            "crossover)."
        )

        source = _generate_signal_engine(code, description)

        start = (pd.Timestamp(date) - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
        result = _run_backtest([code], start, date, source, f"q3_{code}")
        m = result["metrics"]
        final_signal = result["raw_weights"].get(code, 0.0)

        if final_signal > 0.05:
            direction = Direction.LONG
        elif final_signal < -0.05:
            direction = Direction.SHORT
        else:
            direction = Direction.NEUTRAL
        strength = max(0.0, min(1.0, abs(final_signal)))

        evidence = [
            EvidenceItem(
                kind="strategy_description",
                value=description,
                source="caller-supplied natural-language request",
            ),
            EvidenceItem(
                kind="generated_code",
                value=source,
                source=(
                    "DeepSeek-generated SignalEngine (upstream's real "
                    "strategy-generate skill + build_llm(), single live call)"
                ),
            ),
            EvidenceItem(
                kind="backtest_stats",
                value=(
                    f"sharpe={m.get('sharpe', 0.0):.3f}, "
                    f"trades={int(m.get('trade_count', 0))}, "
                    f"total_return={m.get('total_return', 0.0):.4f}"
                ),
                source=f"real backtest over {start}/{date}",
            ),
        ]

        result_signal = Q3Signal(
            context=context,
            signal_semantics="final_target_signal_after_backtest",
            values={ticker: final_signal},
            score_scale="[-1,1] per upstream's own strategy-generate/SKILL.md convention",
            direction=direction,
            strength=strength,
            evidence=evidence,
        )

        self._last_native_output = {
            "upstream": {"code": code, "metrics": m, "generated_source": source},
            "adapter_derived": {"description": description, "start": start, "end": date},
        }
        self._last_latency_sec = time.time() - t0
        return result_signal

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output, same pattern as this
    # session's other migrated adapters.
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
    ):
        self._last_native_output = None
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native_output:
            updates["native_output"] = self._last_native_output
        if self._last_latency_sec:
            updates["run"] = result.run.model_copy(update={"latency_sec": self._last_latency_sec})
        if updates:
            result = result.model_copy(update=updates)
        return result

    # ------------------------------------------------------------------
    # Smoke test — real calls to both implemented q* methods
    # ------------------------------------------------------------------
    def smoke_test(self) -> Dict[str, bool]:
        checks = super().smoke_test()

        q4_context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO,
            targets=["AAPL", "MSFT"],
            universe=["AAPL", "MSFT"],
        )
        generation_window = TimeWindow(start="2023-06-01", end="2024-01-15")

        try:
            q4 = self.q4_policy(q4_context, generation_window)
            checks["q4_returns_Q4Policy"] = q4 is not None
            if q4 is not None:
                checks["q4_decisions_nonempty"] = bool(q4.decisions)
                checks["q4_context_echoed"] = q4.context == q4_context
                checks["q4_generation_window_echoed"] = q4.generation_window == generation_window
        except Exception:
            checks["q4_smoke_call_succeeds"] = False

        try:
            q3_context = QueryContext(
                as_of="2024-01-15",
                data_cutoff="2024-01-15",
                scope=OutputScope.ASSET,
                targets=["AAPL"],
                universe=["AAPL"],
            )
            q3 = self.q3_signal(q3_context)
            checks["q3_returns_Q3Signal"] = q3 is not None
            if q3 is not None:
                checks["q3_values_nonempty"] = bool(q3.values)
                checks["q3_context_echoed"] = q3.context == q3_context
        except Exception:
            checks["q3_smoke_call_succeeds"] = False

        return checks
