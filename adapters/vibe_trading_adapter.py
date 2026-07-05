"""
adapters/vibe_trading_adapter.py — wraps github.com/HKUDS/Vibe-Trading (Q3, Q4, Q5).

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
Design notes / scope reductions (translation choices made by this adapter,
not upstream)
============================================================================
  - **Q5 first, then Q4, then Q3**, per the session brief's own sequencing.
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
from CONTRACT.schemas import Direction, Q3Signal, Q4Portfolio, Q5Backtest, SignalType

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
    equity = pd.read_csv(artifacts / "equity.csv")
    equity_curve = [float(v) for v in (equity["equity"] / DEFAULT_INITIAL_CASH).tolist()]

    raw_weights: Dict[str, float] = {}
    positions_path = artifacts / "positions.csv"
    if positions_path.exists():
        positions = pd.read_csv(positions_path)
        if len(positions) > 0:
            last_row = positions.iloc[-1]
            raw_weights = {c: float(last_row[c]) for c in codes if c in positions.columns}

    result = {"metrics": metrics, "equity_curve": equity_curve, "raw_weights": raw_weights}
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
    questions_answered = ["Q3", "Q4", "Q5"]
    upstream_repo = "https://github.com/HKUDS/Vibe-Trading"
    requires_env = "vibe_trading_real"

    # ------------------------------------------------------------------
    # Q5 — Backtest (built first, per session brief sequencing)
    # ------------------------------------------------------------------
    def q5_backtest(self, tickers: List[str], start: str, end: str, **kwargs) -> Optional[Q5Backtest]:
        t0 = time.time()
        codes = _ensure_cross_market([_to_vt_code(t) for t in tickers])
        result = _run_backtest(codes, start, end, CROSS_MARKET_SIGNAL_ENGINE_SOURCE, "q5")
        m = result["metrics"]

        return Q5Backtest(
            total_return=m["total_return"],
            sharpe=m.get("sharpe"),
            max_drawdown=m.get("max_drawdown"),
            alpha_vs_benchmark=m.get("excess_return"),
            calmar=m.get("calmar"),
            win_rate=max(0.0, min(1.0, m.get("win_rate", 0.0))),
            equity_curve=result["equity_curve"],
            benchmark="equal_weight_bnh",
            test_period=f"{start}/{end}",
            adapter=self.name,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Q4 — Portfolio allocation via real CompositeEngine positions
    # ------------------------------------------------------------------
    def q4_portfolio(self, tickers: List[str], date: str, **kwargs) -> Optional[Q4Portfolio]:
        t0 = time.time()
        codes = _ensure_cross_market([_to_vt_code(t) for t in tickers])
        end = date
        start = (pd.Timestamp(date) - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
        result = _run_backtest(codes, start, end, CROSS_MARKET_SIGNAL_ENGINE_SOURCE, "q4")

        raw_weights = result["raw_weights"]
        positive = {_display_label(c): max(0.0, w) for c, w in raw_weights.items()}
        total = sum(positive.values())
        if total > 1.0:
            positive = {c: w / total for c, w in positive.items()}
            total = 1.0
        cash_ratio = max(0.0, min(1.0, 1.0 - total))

        anchor_note = ""
        if ANCHOR_CRYPTO_CODE in codes and len({t.upper() for t in tickers}) == len(codes) - 1:
            anchor_note = (
                f" A {ANCHOR_CRYPTO_CODE} anchor position was added because the "
                "requested tickers were single-market, so the real upstream "
                "CompositeEngine (not the single-market engine) is exercised."
            )

        rationale = (
            "Real upstream CompositeEngine (github.com/HKUDS/Vibe-Trading) cross-"
            f"market run over {codes} using upstream's own vol-adjusted dual-"
            "moving-average example strategy (per-market MA windows, inverse-"
            "volatility position sizing). Final target weights read directly "
            "from upstream's own artifacts/positions.csv, clipped to long-only "
            "and renormalized to sum <= 1.0 for this schema's cash-neutral "
            "convention." + anchor_note
        )

        return Q4Portfolio(
            weights=positive,
            cash_ratio=cash_ratio,
            rationale=rationale,
            regime=None,
            rebalance_freq="DAILY",
            adapter=self.name,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Q3 — Natural-language alpha signal (real DeepSeek call)
    # ------------------------------------------------------------------
    def q3_signal(self, ticker: str, date: str, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()
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

        supporting_evidence = [
            f"DeepSeek-generated SignalEngine (upstream's real strategy-generate "
            f"skill + build_llm(), single live call) implementing: {description}",
            f"Real backtest over {start}/{date}: sharpe={m.get('sharpe', 0.0):.3f}, "
            f"trades={int(m.get('trade_count', 0))}, total_return={m.get('total_return', 0.0):.4f}",
        ]

        return Q3Signal(
            signal_type=SignalType.MOMENTUM,
            direction=direction,
            strength=strength,
            supporting_evidence=supporting_evidence,
            expected_horizon="1w",
            expected_return=None,
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Smoke test — real calls to all three implemented q* methods
    # ------------------------------------------------------------------
    def smoke_test(self) -> Dict[str, bool]:
        checks = super().smoke_test()

        try:
            q5 = self.q5_backtest(["AAPL"], "2024-01-01", "2024-03-31")
            checks["q5_returns_Q5Backtest"] = q5 is not None
            checks["q5_total_return_is_float"] = isinstance(q5.total_return, float)
            checks["q5_max_drawdown_non_positive"] = (q5.max_drawdown is None) or (q5.max_drawdown <= 1e-9)
        except Exception:
            checks["q5_smoke_call_succeeds"] = False

        try:
            q4 = self.q4_portfolio(["AAPL", "MSFT"], "2024-01-15")
            checks["q4_returns_Q4Portfolio"] = q4 is not None
            checks["q4_weights_nonnegative"] = all(w >= 0.0 for w in q4.weights.values())
            checks["q4_weights_sum_valid"] = sum(q4.weights.values()) <= 1.001
            checks["q4_cash_ratio_valid"] = 0.0 <= q4.cash_ratio <= 1.0
        except Exception:
            checks["q4_smoke_call_succeeds"] = False

        try:
            q3 = self.q3_signal("AAPL", "2024-01-15")
            checks["q3_returns_Q3Signal"] = q3 is not None
            checks["q3_direction_valid"] = q3.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["q3_strength_in_range"] = 0.0 <= q3.strength <= 1.0
        except Exception:
            checks["q3_smoke_call_succeeds"] = False

        return checks
