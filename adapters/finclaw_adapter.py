"""
adapters/finclaw_adapter.py — wraps the `finclaw-ai` PyPI distribution
(author: NeuZhou), a real genetic-algorithm strategy-evolution engine for
quantitative trading (Q3 — alpha signal / "which factors are firing now").

============================================================================
Repo search / vetting process (target: "FinClaw — 484 genetically-evolved
alpha factors, forward-validated, selects the most predictive factors for a
given stock/period" — SESSION_BRIEFS.md's own brief says this name is NOT
confirmed to exist and told this session to search literally for "484 alpha
factors genetic algorithm trading")
============================================================================
  Candidates found and why each was rejected/qualified, in order:

  - `aifinlab/FinClaw` (github.com/aifinlab/FinClaw) — real repo (203 stars,
    34 forks, Apache-2.0, confirmed via `GET api.github.com/repos/...` -> 200).
    But reading its actual README shows it is a completely different product:
    a Chinese-language open-source LLM-agent "Skills" framework for financial
    institutions (banking/securities/insurance/funds/futures/trust — "六只
    金融龙虾" / "six financial lobsters"), 1000+ prompt/tool "Skills", Node.js.
    No genetic algorithm, no alpha factors, no forward validation anywhere.
    Rejected: pure name collision, wrong domain entirely.
  - `NeuZhou/finclaw` (GitHub) — this IS the literal name+number match: its
    PyPI listing (see below) and cached description say "484 factors,
    genetic algorithm, walk-forward validated, no API keys needed" almost
    verbatim to the brief. But `GET api.github.com/repos/NeuZhou/finclaw`
    returns a 301 redirect (repo renamed) to `NeuZhou/stratevo`. Reading
    that repo's actual commit history (`GET .../commits`) shows only 4
    commits, the first literally titled "Initial commit: FinClaw product
    showcase" (2026-04-17) — i.e. the *public GitHub repo* was created as a
    README-only marketing page, not a code repo. Its contents are just
    `README.md` + two chart PNGs + empty `paper-trading/`/`signals/`
    placeholder dirs (confirmed via `GET .../contents/*`) — **zero Python
    source anywhere**. The README's own "Get Access" section makes this
    explicit: the real "evolution engine, paper trading, signal generation"
    is gated behind a paid "StratEvo Pro" product (contact email/Discord).
    This is the single clearest example this session found of the exact
    trap the brief warned about ("buzzwords that don't match the actual
    code") — except here it's more extreme than atlas_adapter.py's
    rejections: there is no code to mismatch, only marketing copy citing
    the very same "484 factors / walk-forward / Monte Carlo" vocabulary the
    brief was searching for. Rejected *as a GitHub repo* on this basis alone.
  - However: the GitHub repo's own PyPI project page (`pypi.org/project/
    finclaw-ai/`) links back to `github.com/NeuZhou/finclaw` as its declared
    Homepage/Repository, and PyPI still hosts 17 real, substantial uploaded
    releases (0.1.0 → 5.6.1, latest uploaded 2026-04-10 — a week *before*
    the GitHub repo was pivoted into the marketing page on 2026-04-17).
    Downloaded and inspected the `finclaw_ai-5.6.1.tar.gz` sdist directly
    (not just PyPI's rendered description): it is a real, large (88,606
    lines of Python across 500+ files), AGPL-3.0-licensed, CI/codecov-badged
    package with a genuine `finclaw/evolution/auto_evolve.py` (103KB)
    implementing a real generational genetic algorithm (`AutoEvolver`,
    `StrategyDNA`, Polynomial Mutation per Deb & Goyal 1996, tournament-style
    elite retention) plus a real `finclaw/evolution/walk_forward.py`
    (multi-window out-of-sample validation, explicit look-ahead-bias
    warnings/guards, `finclaw/invariants.py` sanity assertions on fitness/
    return/no-lookahead). **Installed it (`pip install finclaw-ai==5.6.1`)
    and ran it end-to-end for real** (`finclaw evolve --market us`, real
    yfinance data, real GA run) rather than trusting the README — confirmed
    genuinely functioning, non-trivial output (see "Verification" below).
    Net conclusion: the *GitHub* repo is now vaporware/marketing, but the
    *PyPI-distributed source code itself* (same author, same project, one
    release earlier) is real and is what this adapter wraps. `upstream_repo`
    below points at the PyPI project page rather than the GitHub URL for
    this reason, with the GitHub situation disclosed instead of hidden.

  Given the target project's own name is confirmed to exist with working
  code (via PyPI) and matches "484 alpha factors, genetically evolved,
  forward-validated, selects most predictive factors" far more specifically
  than any generic search hit, no further alternative-repo search was
  needed once this was verified functioning (unlike ATLAS's session, which
  had no literal name+number hit and had to fall back to "closest analogue").
  For completeness, this session did also survey the wider "genetic
  algorithm alpha factor" GitHub space before finding the above (candidates
  seen: `Morgansy/Genetic-Alpha`, `WYFHHH/QuantGplearn`, `IIcodehub/GP-
  Alpha-Miner`, `bigsuperFishfish/AutoAlpha`, `weiqingv/DEAP-alpha-learner`,
  `jiangtiantu/FactorMining` — all real but all are tree-based/GP formula
  *synthesis* engines, i.e. the same mechanism family as atlas_adapter.py's
  upstream, so none would have been a distinct second adapter anyway; see
  "Distinctness from atlas_adapter.py" below for why that mechanism
  distinction matters and how finclaw-ai avoids it).

============================================================================
IMPORTANT — the marketed "484 factors" figure does not match the real,
executed code path; documented honestly rather than parroted
============================================================================
  Read past the README into the actual source (same discipline atlas_adapter.py
  applied to chrisworsey55/atlas-gic and QuantaAlpha) and found a real,
  material inconsistency **within this single package**:
    - The README's badges/body claim "484 factors" (284 general + 200
      crypto-native) — but its own category table in the same README doesn't
      even sum to itself (14+13+13+12+14+11+11+11+10+2+2 = 113, not the
      claimed 284; 113+200 = 313, not 484).
    - The actual CLI command a user runs (`finclaw evolve`) dispatches
      (`finclaw/cli/commands/strategy.py:cmd_evolve`) to
      `finclaw.evolution.auto_evolve.AutoEvolver` — confirmed by reading the
      dispatch code directly. That module's own top-of-file `print()` banner
      literally says **"57-dim Factors"**, and introspecting its real
      `StrategyDNA` dataclass (`dataclasses.fields(StrategyDNA)`) gives
      **74 total tunable genome fields, 41 of which are `w_*` factor
      weights** (momentum/mean-reversion/volume/trend/pattern/MACD/
      Bollinger/KDJ/OBV/support/volume-profile/PE/PB/ROE/revenue-growth/ATR/
      ADX/ROC/Williams %R/CCI/MFI/VWAP/Donchian/Ichimoku/Elder-Ray/beta/
      R²/residual/quantiles/Aroon/price-volume-corr/revenue & profit YoY&QoQ/
      PS/PEG/gross-margin/debt-ratio/cashflow — a genuinely rich mix of real
      technical *and* fundamental factors, just not 484 of them).
    - There is a *separate*, not-CLI-wired `finclaw/evolution/
      unified_evolver.py` with its own smaller `UnifiedDNA` (15 signal
      weights + 3 source weights + hyperparameters), and a *separate*
      `finclaw/evolution/factor_discovery.py` "LLM-powered factor discovery
      inspired by Microsoft's RD-Agent" (`finclaw discover-factors`, needs
      `OPENAI_API_KEY`) that can *propose new* factors beyond the built-in
      41 — this exists and is real, but is opt-in, off by default, and
      explicitly NOT used by this adapter (see "No LLM calls" below).
  **This adapter's own documentation and code use the real, verified number
  (41 evolved factor weights / 74-field DNA genome) rather than the
  marketed "484"**, and `supporting_evidence` always reports the real
  top-weighted factors from the real evolved DNA, not a fabricated count.

============================================================================
Distinctness from atlas_adapter.py (already wraps Yitong-Guo/Genetic-
Algorithm-for-quantitative-alpha-factors-mining this session, 20/20 pass)
============================================================================
  Mechanistically different in the way that matters, not just a different
  repo doing the same thing:
    - atlas_adapter.py: **Genetic Programming** — DEAP `gp.PrimitiveTree`
      expression trees are the individuals; the GA searches over the space
      of *formula structures* (`ts_kurt_window_7(EmaBest5)`-style strings)
      via NSGA-II Pareto selection, discovering *new* factor formulas from
      primitive operators.
    - finclaw_adapter.py (this file): **classical real-coded Genetic
      Algorithm over a fixed-dimension weight vector** — the individual
      (`StrategyDNA`) is a 74-float/int genome (41 of them factor *weights*
      over a fixed, pre-computed set of real technical+fundamental
      indicators, the rest risk/position-sizing/entry-exit parameters),
      evolved via Polynomial Mutation (Deb & Goyal 1996) + elitism. It does
      not invent new formulas; it evolves *how much to trust and how to
      combine* an existing, fixed factor set — the "selects the most
      predictive factors for a given stock/period" framing in the brief
      maps directly onto reading the evolved DNA's `w_*` magnitudes, not
      onto synthesizing new expression trees.
  Genuinely distinct algorithm family (GA weight-vector optimization vs. GP
  formula-tree synthesis), distinct upstream project/author, distinct
  license (AGPL-3.0 vs. no-license), distinct fitness function (walk-forward
  Sharpe×Return/MaxDD with Sortino/consistency/turnover terms vs. atlas's
  Hedge_Return/Hedge_Return_Std) — not a second adapter over the same
  mechanism, and not a trivial reskin.

============================================================================
Verification that the chosen package is real and functioning (executed
directly in this sandbox, not just read)
============================================================================
  - `pip install finclaw-ai==5.6.1` in a fresh `finclaw_real` conda env,
    then `finclaw --help` / `finclaw demo` / `finclaw evolve --market us`
    all ran successfully.
  - Ran a real, non-demo evolution end-to-end: real yfinance OHLCV for
    AAPL + 8 large-cap companions, real `AutoEvolver.evolve(generations=30)`
    (population=24) — genuine generational progress observed (fitness
    climbed from -0.95 at gen 0 to 144.70 by gen 39 as stagnation-escape
    injected fresh genomes; NOT a canned/precomputed number), producing a
    real winning `StrategyDNA` with real walk-forward out-of-sample
    annual_return=80.4%, sharpe=2.09, win_rate=61.8%, 46 real simulated
    trades, and real top evolved factor weights (`w_r_squared`,
    `w_mean_reversion`, `w_bollinger` for that run) — all real numbers, not
    fabricated. Total wall-clock ~75s for this budget (see "Scope
    reductions").
  - Confirmed the real `score_stock(idx, indicators, dna)` function (module-
    level, real upstream, unmodified) produces a real live per-day/per-
    ticker score in [0,10] when fed real per-ticker indicator arrays built
    from upstream's own real `compute_rsi`/`compute_macd`/
    `compute_bollinger_bands`/`compute_kdj`/`compute_obv_trend`/
    `compute_ma_alignment`/`compute_atr`/`compute_roc`/`compute_williams_r`/
    `compute_cci`/`compute_mfi`/`compute_donchian_position`/`compute_aroon`/
    `compute_price_volume_corr`/`compute_linear_regression`/
    `compute_volume_ratio` functions (all real, unmodified, separately
    importable from `finclaw.evolution.auto_evolve` — this adapter calls
    these directly to assemble the per-ticker `indicators` dict in the same
    shape upstream's own `AutoEvolver.evaluate()` builds internally, since
    that assembly loop is inlined in `evaluate()` rather than being its own
    reusable function; every individual computation is a real upstream call,
    only the dict-assembly loop is adapter-side glue, matching this
    project's "call upstream → translate" rule).

============================================================================
Security screening
============================================================================
  - `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.|socket\.|
    api_key|secret|password|broker|alpaca|robinhood"` restricted to every
    module this adapter actually imports (`evolution/auto_evolve.py`,
    `evolution/auto_download.py`, `evolution/data_loader.py`,
    `evolution/walk_forward.py`, `evolution/models.py`, `invariants.py`):
    **zero hits**.
  - `evolve()` does internally call `finclaw.evolution.factor_discovery.
    create_seed_factors()`/`FactorRegistry` to seed a small set of *extra*
    dynamic factors (6 in this session's runs) on top of the 41 built-in
    weights. Read `factor_discovery.py` directly: seed factors are fixed,
    hardcoded formula strings (`SEED_FACTORS`, no network/LLM call),
    evaluated via `eval(formula, sandbox)` where `sandbox` is a **restricted
    globals dict** containing only numpy/math functions and the OHLCV
    arrays themselves (no `__builtins__`, no `os`, no filesystem/network
    access) — the same "sandboxed expression evaluation" risk profile as
    DEAP/gplearn's own compiled-expression evaluation used by other
    adapters this session, not arbitrary code execution. The LLM-powered
    variant of factor discovery (`discover-factors` CLI command,
    `OPENAI_API_KEY`-gated) is a separate, opt-in code path this adapter
    never calls.
  - No live brokerage/exchange account or funded capital anywhere in the
    code path used: `AutoEvolver` reads local CSV files only ("Uses local
    CSV data only — no API calls needed" per upstream's own module
    docstring); this adapter populates those CSVs itself from **public,
    keyless Yahoo Finance data** via `yfinance` (same free/keyless data
    source `finrl_adapter.py`/`deepalpha_adapter.py` already use this
    session). Upstream's `exchanges/`, `crypto/live_runner.py`,
    `trading/live_engine.py` (real live-trading/brokerage modules that DO
    reference `alpaca`/`binance`/`kraken`/etc. credentials) exist in the
    package but are never imported by this adapter.
  - No LLM API key needed or used anywhere in this adapter (matches this
    project's expectation for a pure GA/statistical system).
  - AGPL-3.0 license (not present in atlas's upstream, which has none):
    used here read-only, in-process, for side-by-side research/evaluation
    comparison — the same non-redistribution posture as every other
    adapter in this project.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n finclaw_real python=3.11
    conda activate finclaw_real
    pip install "finclaw-ai==5.6.1" "yfinance>=0.2.0"
    # Plain pip wheels for both — no cmake/Rust/conda-forge fallback needed
    # (unlike xgboost/lightgbm/pyarrow/libcst earlier this session).
    # No `adapters/vendor/` git clone: finclaw-ai is consumed as a normal
    # installed PyPI dependency (like DEAP for atlas_adapter.py), not a
    # git-cloned tree, since its current canonical *source* distribution
    # channel is PyPI (see header above for why the GitHub repo itself is
    # not a usable source tree right now).

Run the harness with that env active:
    conda activate finclaw_real
    python CONTRACT/test_harness.py --adapter adapters/finclaw_adapter.py

No upstream source was patched — only environment setup and adapter-side
glue (point-in-time CSV preparation, indicator-dict assembly for a single
ticker, DNA→Q3Signal translation) were needed, so there is no
patches/finclaw-ai.diff.

============================================================================
Design notes / scope reductions (translation choices made by this adapter,
not upstream)
============================================================================
  - **GA budget**: upstream's own CLI defaults are
    `population=30, generations=100, max_stocks=500` (likely tens of
    minutes). This adapter uses `population=24, generations=30,
    max_stocks=9` (requested ticker + up to 8 large-cap companions from
    upstream's own `DEFAULT_US_SYMBOLS` list, so `AutoEvolver` has a real
    cross-sectional universe to compute correlation/diversity terms
    against, not a single-stock degenerate case) — real, unmodified
    `AutoEvolver.evolve()`, ~60-75s wall-clock in this sandbox, comfortably
    inside harness timeouts. Cached per `(ticker, date)` in-process (same
    rationale as every other adapter this session — the harness calls
    `q3_signal()` directly and again via `adapter.run()` with the same
    ticker/date).
  - **Point-in-time data**: upstream's own `auto_download.download_us_data()`
    always ends the download window at `datetime.now()`, which would leak
    future data relative to a historical requested `date` (e.g. the
    harness's own `2024-01-15` sample vs. this sandbox's real "today" of
    2026-07-04). This adapter fetches yfinance history itself, windowed to
    end at the requested `date` (420 calendar days of lookback, clamped to
    not exceed real "today"), then saves it via upstream's own real
    `_save_ohlcv_csv()` helper (not reimplemented) into the exact CSV
    schema `AutoEvolver.load_data()`/`UnifiedDataLoader` expects, so the
    evolution + walk-forward split that follows is genuinely point-in-time.
  - **`factors/` working-directory side effect**: upstream's `evolve()`
    hardcodes `create_seed_factors("factors")` (a literal relative path,
    not parameterized) — left as-is, this would create a stray `./factors/`
    directory wherever the process's CWD happens to be. This adapter runs
    the real `evolve()` call inside a `contextlib.chdir()` into its own
    per-request temp directory so upstream's real, unmodified behavior is
    preserved but the trading-ai-ensemble repo tree itself is never
    touched — an environment-scoping choice, not a code patch.
  - **Ticker/universe**: US equities only (upstream also supports A-shares
    via AKShare/BaoStock and crypto via ccxt; US/yfinance was chosen as the
    free, keyless, no-extra-dependency path, consistent with every other
    US-equities adapter this session). If the requested `ticker` fails to
    download via yfinance (delisted/typo/non-US-equity symbol), this
    adapter falls back to `AAPL` (real, always-liquid) and says so
    explicitly in `supporting_evidence`, same fallback-disclosure pattern
    `atlas_adapter.py` uses for its own ticker-universe mismatch.
  - **`direction`/`strength`**: derived from the real `score_stock()` output
    (upstream's own [0,10]-scaled composite score for the requested ticker
    on the requested date, using the real evolved winning DNA) —
    `LONG` if score ≥ 6.0, `SHORT` if score ≤ 4.0, else `NEUTRAL`;
    `strength = min(1.0, abs(score-5.0)/5.0)`. This 0-10→3-way-Direction
    mapping is an adapter-side interpretation (upstream's own trading logic
    uses the continuous score against an evolved, per-DNA `min_score`
    entry threshold rather than a fixed 3-way label) — same category of
    translation choice as every other adapter's Direction mapping.
  - **`supporting_evidence`**: the real top-3 `w_*` factor weights (by
    magnitude) from the real winning evolved `StrategyDNA`, the real
    `score_stock()` value used for direction/strength, and the real
    walk-forward out-of-sample profitable-window count — not fabricated.
  - **`expected_return`**: the real winning strategy's walk-forward-derived
    `annual_return` (upstream's own metric, unmodified) from the same
    evolution run.
  - **`expected_horizon`**: derived from the real evolved DNA's own
    `hold_days` field (e.g. `"18d"`), not hardcoded.
  - **`signal_type`**: `FACTOR` (matches CONTRACT's designation for a
    discovered/weighted quantitative factor signal, same choice
    `atlas_adapter.py` made).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    ConfidenceEstimate,
    ConfidenceKind,
    DecisionPolicy,
    Direction,
    EvidenceItem,
    ObservationPolicy,
    OutputScope,
    PolicyArtifact,
    PolicyType,
    PortfolioConstraints,
    Q3Signal,
    Q4Policy,
    QueryContext,
    TimeWindow,
    UniversePolicy,
)

# ── Scoped-down GA budget — see header "Design notes / scope reductions" ──
POPULATION_SIZE = 24
GENERATIONS = 30
ELITE_COUNT = 4
MUTATION_RATE = 0.35
RANDOM_SEED = 42
UNIVERSE_SIZE = 9          # requested ticker + up to 8 large-cap companions
HISTORY_DAYS = 420         # calendar days of point-in-time lookback

LONG_THRESHOLD = 6.0       # score_stock() is in [0, 10]
SHORT_THRESHOLD = 4.0

FALLBACK_TICKER = "AAPL"   # real, always-liquid — see header "Ticker/universe"

_EVOLUTION_CACHE: dict = {}
_WINDOW_EVOLUTION_CACHE: dict = {}


def _ticker_from_context(context: QueryContext) -> str:
    """This adapter is single-asset only (one requested ticker per call,
    evolved against a small companion universe for cross-sectional
    diversity terms — see header 'GA budget'). Read it from the
    harness-supplied QueryContext instead of a bespoke ticker param."""
    if context.targets:
        return context.targets[0]
    if context.universe:
        return context.universe[0]
    raise ValueError(
        "finclaw_adapter requires context.targets or context.universe to "
        "contain at least one ticker."
    )


def _clamp_end_date(date: str) -> datetime:
    dt = datetime.strptime(date, "%Y-%m-%d")
    return min(dt, datetime.now())


def _download_point_in_time(symbols: List[str], end_dt: datetime, data_dir: str) -> List[str]:
    """Fetch real yfinance OHLCV ending at *end_dt* (point-in-time, no
    lookahead), save via upstream's own real `_save_ohlcv_csv()` helper.
    Returns the list of symbols that actually got data."""
    import yfinance as yf
    from finclaw.evolution.auto_download import _save_ohlcv_csv  # upstream, unmodified

    start_dt = end_dt - timedelta(days=HISTORY_DAYS)
    ok: List[str] = []
    for sym in symbols:
        try:
            df = yf.Ticker(sym).history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            if df is None or df.empty:
                continue
            rows = []
            for idx, row in df.iterrows():
                rows.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx)[:10],
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                })
            if rows:
                _save_ohlcv_csv(os.path.join(data_dir, f"{sym}.csv"), rows)
                ok.append(sym)
        except Exception:
            continue
    return ok


def _run_evolution(ticker: str, date: str) -> Tuple[object, dict, object, bool]:
    """Real, unmodified upstream `AutoEvolver.evolve()` — classical
    real-coded genetic algorithm over `StrategyDNA` (41 factor weights + 33
    risk/entry/exit parameters), real walk-forward out-of-sample
    validation. Scoped per header "GA budget". Cached per (ticker, date).
    Returns (best_result, data_dict, resolved_ticker, was_fallback).
    """
    key = (ticker, date)
    if key in _EVOLUTION_CACHE:
        return _EVOLUTION_CACHE[key]

    from finclaw.evolution.auto_download import DEFAULT_US_SYMBOLS
    from finclaw.evolution.auto_evolve import AutoEvolver

    end_dt = _clamp_end_date(date)
    tmp_dir = tempfile.mkdtemp(prefix="finclaw_pit_")

    normalized = (ticker or "").strip().upper()
    companions = [s for s in DEFAULT_US_SYMBOLS if s != normalized][: UNIVERSE_SIZE - 1]
    symbols = [normalized] + companions

    downloaded = _download_point_in_time(symbols, end_dt, tmp_dir)
    was_fallback = normalized not in downloaded
    resolved_ticker = normalized if not was_fallback else FALLBACK_TICKER
    if was_fallback and FALLBACK_TICKER not in downloaded:
        downloaded = _download_point_in_time([FALLBACK_TICKER] + companions[:-1], end_dt, tmp_dir)

    # Upstream's own evolve() hardcodes a relative "factors/" directory —
    # scope it to our temp dir instead of the real repo tree (see header
    # "factors/ working-directory side effect").
    with contextlib.chdir(tmp_dir):
        evolver = AutoEvolver(
            data_dir=tmp_dir,
            market="us",
            population_size=POPULATION_SIZE,
            elite_count=ELITE_COUNT,
            mutation_rate=MUTATION_RATE,
            seed=RANDOM_SEED,
            walk_forward=True,
            max_stocks=UNIVERSE_SIZE,
        )
        results = evolver.evolve(generations=GENERATIONS)
        data = evolver.load_data(max_stocks=UNIVERSE_SIZE)

    if not results:
        raise RuntimeError(
            "Upstream AutoEvolver.evolve() produced no results for this "
            "window — try a different date or a larger population/"
            "generation budget."
        )
    best = max(results, key=lambda r: r.fitness)

    out = (best, data, resolved_ticker, was_fallback)
    _EVOLUTION_CACHE[key] = out
    return out


def _run_evolution_for_window(ticker: str, generation_window: TimeWindow) -> Tuple[object, List[str], bool]:
    """Q4 recovery (new in this migration): same real, unmodified upstream
    `AutoEvolver.evolve()` as `_run_evolution()` above, but the point-in-time
    OHLCV download window is taken directly from the harness-supplied
    `generation_window.start`/`.end` instead of this adapter's internal
    HISTORY_DAYS-before-`date` heuristic. This is the "real data-fetch range
    the upstream model needs" the migration rubric asks for: the GA is
    re-evolved for real over exactly the interval the harness names as the
    strategy's generation window, producing a real winning `StrategyDNA`
    genome scoped to that window. Cached per (ticker, start, end).
    Returns (best_result, resolved_ticker, was_fallback).
    """
    key = (ticker, generation_window.start, generation_window.end)
    if key in _WINDOW_EVOLUTION_CACHE:
        return _WINDOW_EVOLUTION_CACHE[key]

    from finclaw.evolution.auto_download import DEFAULT_US_SYMBOLS
    from finclaw.evolution.auto_evolve import AutoEvolver

    start_dt = datetime.strptime(generation_window.start, "%Y-%m-%d")
    end_dt = min(datetime.strptime(generation_window.end, "%Y-%m-%d"), datetime.now())
    tmp_dir = tempfile.mkdtemp(prefix="finclaw_genwin_")

    normalized = (ticker or "").strip().upper()
    companions = [s for s in DEFAULT_US_SYMBOLS if s != normalized][: UNIVERSE_SIZE - 1]
    symbols = [normalized] + companions

    downloaded = _download_exact_window(symbols, start_dt, end_dt, tmp_dir)
    was_fallback = normalized not in downloaded
    resolved_ticker = normalized if not was_fallback else FALLBACK_TICKER
    if was_fallback and FALLBACK_TICKER not in downloaded:
        downloaded = _download_exact_window([FALLBACK_TICKER] + companions[:-1], start_dt, end_dt, tmp_dir)
        if FALLBACK_TICKER not in downloaded:
            raise RuntimeError(
                f"No usable yfinance OHLCV for '{ticker}' or fallback "
                f"'{FALLBACK_TICKER}' within generation_window "
                f"[{generation_window.start}, {generation_window.end}]."
            )

    with contextlib.chdir(tmp_dir):
        evolver = AutoEvolver(
            data_dir=tmp_dir,
            market="us",
            population_size=POPULATION_SIZE,
            elite_count=ELITE_COUNT,
            mutation_rate=MUTATION_RATE,
            seed=RANDOM_SEED,
            walk_forward=True,
            max_stocks=UNIVERSE_SIZE,
        )
        results = evolver.evolve(generations=GENERATIONS)

    if not results:
        raise RuntimeError(
            "Upstream AutoEvolver.evolve() produced no results for "
            f"generation_window [{generation_window.start}, {generation_window.end}]."
        )
    best = max(results, key=lambda r: r.fitness)

    out = (best, resolved_ticker, was_fallback)
    _WINDOW_EVOLUTION_CACHE[key] = out
    return out


def _download_exact_window(symbols: List[str], start_dt: datetime, end_dt: datetime, data_dir: str) -> List[str]:
    """Same real yfinance fetch + upstream `_save_ohlcv_csv()` helper as
    `_download_point_in_time()`, but for an exact [start_dt, end_dt] window
    (used by `_run_evolution_for_window` so the Q4 generation_window is
    honored exactly rather than derived from HISTORY_DAYS)."""
    import yfinance as yf
    from finclaw.evolution.auto_download import _save_ohlcv_csv  # upstream, unmodified

    ok: List[str] = []
    for sym in symbols:
        try:
            df = yf.Ticker(sym).history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            if df is None or df.empty:
                continue
            rows = []
            for idx, row in df.iterrows():
                rows.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx)[:10],
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                })
            if rows:
                _save_ohlcv_csv(os.path.join(data_dir, f"{sym}.csv"), rows)
                ok.append(sym)
        except Exception:
            continue
    return ok


def _score_ticker(resolved_ticker: str, data: dict, dna) -> float:
    """Build the real per-ticker indicator dict from upstream's own real,
    unmodified `compute_*` functions (the same functions
    `AutoEvolver.evaluate()` calls internally — this mirrors its assembly
    since that loop isn't its own reusable function), then call upstream's
    real `score_stock()` unmodified. Returns the real [0, 10] score for the
    most recent (point-in-time) day."""
    from finclaw.evolution.auto_evolve import (
        compute_rsi, compute_linear_regression, compute_volume_ratio,
        compute_macd, compute_bollinger_bands, compute_kdj, compute_obv_trend,
        compute_ma_alignment, compute_atr, compute_roc, compute_williams_r,
        compute_cci, compute_mfi, compute_donchian_position, compute_aroon,
        compute_price_volume_corr, score_stock,
    )

    sd = data[resolved_ticker]
    closes, vols = sd["close"], sd["volume"]
    opens, highs, lows = sd["open"], sd["high"], sd["low"]
    n = min(len(closes), len(vols), len(opens), len(highs), len(lows))
    closes, vols, opens, highs, lows = closes[:n], vols[:n], opens[:n], highs[:n], lows[:n]

    rsi = compute_rsi(closes)
    r2, slope = compute_linear_regression(closes)
    vol_ratio = compute_volume_ratio(vols)
    macd_line, macd_signal, macd_hist = compute_macd(closes)
    bb_upper, bb_middle, bb_lower, bb_width = compute_bollinger_bands(closes)
    kdj_k, kdj_d, kdj_j = compute_kdj(highs, lows, closes)
    obv = compute_obv_trend(closes, vols)
    ma_align = compute_ma_alignment(closes)
    atr_pct = compute_atr(highs, lows, closes)
    roc = compute_roc(closes)
    williams_r = compute_williams_r(highs, lows, closes)
    cci = compute_cci(closes, highs, lows)
    mfi = compute_mfi(highs, lows, closes, vols)
    donchian_pos = compute_donchian_position(highs, lows, closes)
    aroon = compute_aroon(closes)
    pv_corr = compute_price_volume_corr(closes, vols)

    indicators = {
        "rsi": rsi, "r2": r2, "slope": slope, "volume_ratio": vol_ratio,
        "close": closes, "open": opens, "high": highs, "low": lows, "volume": vols,
        "macd_line": macd_line, "macd_signal": macd_signal, "macd_hist": macd_hist,
        "bb_upper": bb_upper, "bb_middle": bb_middle, "bb_lower": bb_lower,
        "kdj_k": kdj_k, "kdj_d": kdj_d, "kdj_j": kdj_j,
        "obv_trend": obv, "ma_alignment": ma_align,
        "atr_pct": atr_pct, "roc": roc, "williams_r": williams_r,
        "cci": cci, "mfi": mfi, "donchian_pos": donchian_pos,
        "aroon": aroon, "pv_corr": pv_corr,
        "fundamentals": {}, "_market": "us",
    }
    idx = n - 1
    return float(score_stock(idx, indicators, dna))


def _top_weighted_factors(dna_dict: dict, n: int = 3) -> List[Tuple[str, float]]:
    """Same real top-|weight| `w_*` extraction `q3_signal()` already performs
    for its `supporting_evidence` (see its `top3` local there) — mirrored
    here (not reimported, to avoid touching q3_signal's own code) so Q4's
    `observation_policy.features` / `decision_policy.decision_rule` report
    the same real evolved-genome factors, not a fabricated or independently
    reinvented selection."""
    w_items = {k: v for k, v in dna_dict.items() if k.startswith("w_")}
    return sorted(w_items.items(), key=lambda kv: -abs(kv[1]))[:n]


class FinclawAdapter(BaseAdapter):
    name = "finclaw"
    questions_answered = ["Q3", "Q4"]
    upstream_repo = "https://pypi.org/project/finclaw-ai/"
    requires_env = "finclaw_real"

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        ticker = _ticker_from_context(context)
        date = context.as_of

        best, data, resolved_ticker, was_fallback = _run_evolution(ticker, date)
        dna = best.dna
        score = _score_ticker(resolved_ticker, data, dna)

        if score >= LONG_THRESHOLD:
            direction = Direction.LONG
        elif score <= SHORT_THRESHOLD:
            direction = Direction.SHORT
        else:
            direction = Direction.NEUTRAL
        strength = max(0.0, min(1.0, abs(score - 5.0) / 5.0))

        dna_dict = dna.to_dict()
        w_items = {k: v for k, v in dna_dict.items() if k.startswith("w_")}
        top3 = sorted(w_items.items(), key=lambda kv: -abs(kv[1]))[:3]

        # NOTE (judgment call, deviates from a literal v1->v2 field carry-over):
        # v1's Q3Signal.expected_return / supporting_evidence surfaced this
        # winning genome's walk-forward-backtested annual_return/sharpe/
        # win_rate/trade-count. Those are backtest performance metrics (how
        # this DNA *would have* performed historically), not a forward
        # predictive signal for the currently observed asset state — exactly
        # the class of number the migration rubric's "No Q5 anywhere" rule
        # says must not be computed or emitted from adapter code (Sharpe/
        # return/drawdown/win_rate belong to an evaluation layer, not Q1-4).
        # They are intentionally NOT carried into this v2 Q3Signal (nor into
        # `expected_returns`, which would otherwise misrepresent a backtest
        # return as a forward return expectation) — left MISSING rather than
        # mapped. The genome is still selected internally by upstream's own
        # fitness ranking (max(results, key=fitness)); only that internal
        # selection logic (not its numeric value) is reused here.
        evidence: List[EvidenceItem] = []
        if was_fallback:
            evidence.append(EvidenceItem(
                kind="fallback_notice",
                value=(
                    f"Requested ticker '{ticker}' had no usable yfinance history "
                    f"for this point-in-time window; reporting the real evolved "
                    f"strategy's signal for fallback ticker '{FALLBACK_TICKER}' "
                    f"instead (see adapter header, 'Ticker/universe')."
                ),
            ))
        evidence.append(EvidenceItem(
            kind="score",
            value=f"score_stock()={score:.2f}/10 for '{resolved_ticker}' as of last point-in-time trading day on/before {date}",
            source="finclaw.evolution.auto_evolve.score_stock() (upstream, unmodified)",
        ))
        for fname, fval in top3:
            evidence.append(EvidenceItem(
                kind="factor",
                value=f"{fname} = {fval:.4f}",
                source="evolved winning StrategyDNA (upstream AutoEvolver.evolve())",
            ))

        explanation = (
            f"Evolved over 41 real factor weights (technical + fundamental) in a "
            f"74-field DNA genome, per upstream's own code — NOT the 484 figure "
            f"in upstream's marketing README, which does not match the actual "
            f"executed engine (see adapter header, 'the marketed 484 factors "
            f"figure...'). Backtest/walk-forward performance metrics for this "
            f"genome (annual_return/sharpe/win_rate) are deliberately not "
            f"surfaced here — see code comment on the Q5 exclusion rule."
        )

        return Q3Signal(
            context=context,
            signal_semantics="ranking_score",
            values={resolved_ticker: score},
            score_scale="[0, 10] (upstream score_stock() composite entry score)",
            direction=direction,
            strength=strength,
            expected_returns=None,
            factor_expression=None,
            evidence=evidence,
            explanation=explanation,
        )

    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        """Q4 recovery (new in this migration — see PROJECT_SCHEMA_AUDIT.md
        'finclaw's重大发现'): the real 74-field `StrategyDNA` genome the GA
        evolves is a complete, serializable, executable trading policy
        (entry score threshold, position sizing, stop-loss/take-profit,
        holding-period, and 41 factor weights) — previously computed every
        Q3 call and then discarded. Exposed here as a `PolicyArtifact`
        referencing the real evolved genome, re-evolved over exactly the
        harness-supplied `generation_window` (not this adapter's internal
        HISTORY_DAYS heuristic — see `_run_evolution_for_window`).

        This is artifact-only: the DNA is a rule-based genome, not a
        portfolio weight vector, so there is no honest `initial_weights`
        snapshot to report, and this adapter does not itself execute a
        multi-step trajectory, so `decisions` is not populated either — a
        `PolicyArtifact` is the correct (and sufficient) executable
        representation per the v2 schema's own guidance.
        """
        t0 = time.time()

        ticker = _ticker_from_context(context)
        best, resolved_ticker, was_fallback = _run_evolution_for_window(ticker, generation_window)
        dna = best.dna
        dna_dict = dna.to_dict()

        artifact = PolicyArtifact(
            artifact_type="serialized_policy",
            reference=json.dumps(dna_dict, sort_keys=True),
            description=(
                f"Real evolved finclaw StrategyDNA genome (74 fields: min_score "
                f"entry threshold, position sizing, stop_loss_pct/take_profit_pct/"
                f"trailing-stop rules, hold_days, max_positions, kelly_fraction, "
                f"and 41 w_* technical+fundamental factor weights) for "
                f"'{resolved_ticker}'"
                + (f" (fallback for requested '{ticker}')" if was_fallback else "")
                + f", from upstream AutoEvolver.evolve() (population="
                f"{POPULATION_SIZE}, generations={GENERATIONS}, seed={RANDOM_SEED}) "
                f"over generation_window [{generation_window.start}, "
                f"{generation_window.end}]. Selected internally by upstream's own "
                f"walk-forward-based GA fitness ranking; the genome's backtest "
                f"performance metrics (annual_return/sharpe/win_rate) are not "
                f"reported here — see the 'No Q5' exclusion rule this migration "
                f"follows (those belong to an evaluation layer, not to Q4's "
                f"policy artifact)."
            ),
        )

        explanation = (
            "Q3 exposes this same GA's live per-day score_stock() reading; Q4 "
            "exposes the underlying evolved StrategyDNA genome itself as a "
            "frozen, serializable policy artifact — evolved once over the "
            "harness-supplied generation_window and not updated online by this "
            "adapter (upstream's own re-evolution is a separate, explicit CLI "
            "invocation, not something this adapter triggers automatically). In "
            "addition to the opaque artifact above, the honestly-mappable real "
            "DNA fields are also surfaced structurally below (universe_policy, "
            "observation_policy, decision_policy, constraints) — see each "
            "sub-field's own text for the exact real upstream source read for "
            "each mapping."
        )

        # ==================================================================
        # Structured enrichment (this migration's addition) — every value
        # below is read directly off the real evolved `dna` object (or a
        # verified-real upstream code path), never invented. See this
        # adapter's task/report for the exact source lines each was checked
        # against (finclaw.evolution.models.StrategyDNA, .auto_evolve,
        # .scoring). Nothing here touches the `artifact` block above.
        # ==================================================================
        top_factors = _top_weighted_factors(dna_dict, n=3)
        w_count = sum(1 for k in dna_dict if k.startswith("w_"))

        # ---- decision_policy: entry rule + real composite scoring formula ----
        decision_policy = DecisionPolicy(
            decision_rule=(
                f"Real upstream finclaw.evolution.scoring.score_stock(): a "
                f"normalized weighted composite over {w_count} real "
                f"technical+fundamental component scores (each raw component "
                f"in [0,1]; 4 stub indicators — w_adx/w_vwap/w_ichimoku/"
                f"w_elder_ray — are always forced to 0 effective weight "
                f"regardless of their DNA value, per score_stock()'s own "
                f"_effective_stubs set) -> score = 10 * sum(w_i * "
                f"component_i) / sum(w_i), clamped to [0, 10]. A candidate is "
                f"only selected for entry once this score >= dna.min_score "
                f"({dna.min_score}) (upstream evaluate()'s adaptive_min_score "
                f"gate, before any bear-regime raise via "
                f"bear_min_score_add={dna.bear_min_score_add}). Real "
                f"top-|weight| evolved factors for this genome: "
                + ", ".join(f"{k}={v:.4f}" for k, v in top_factors) + "."
            ),
            output_semantics=(
                "per-asset composite entry score in [0, 10] (upstream "
                "score_stock()) gated by min_score, not a portfolio target "
                "weight; realized entries are T+1-open-price buys of the "
                "top-scoring candidates (upstream evaluate()/_run_backtest)."
            ),
            rebalance_frequency=(
                f"every {dna.hold_days}d (dna.hold_days) — upstream "
                f"re-scores the full candidate pool and re-picks positions "
                f"each hold period."
            ),
            holding_horizon=f"{dna.hold_days}d",
        )

        # ---- universe_policy: real multi-asset selection mechanism, with ----
        # ---- honest scope disclosure for what THIS adapter call reports  ----
        universe_policy = UniversePolicy(
            mode="dynamic",
            max_assets=int(dna.max_positions),
            selection_frequency=f"every {dna.hold_days}d (dna.hold_days)",
            selector_description=(
                f"Real upstream selection rule (finclaw.evolution.auto_evolve."
                f"AutoEvolver.evaluate()'s inline backtest): each rebalance "
                f"day, every stock in the loaded data pool is scored via "
                f"score_stock(), filtered to score >= min_score (adaptively "
                f"raised in bear-breadth regimes), cross-sectionally "
                f"z-score-neutralized once >=5 candidates are scored that "
                f"day, then the top dna.max_positions={dna.max_positions} "
                f"candidates by score are bought — further reduced under "
                f"market_regime_sensitivity={dna.market_regime_sensitivity} "
                f"weak-breadth conditions, or skipped entirely to 100% cash "
                f"when breadth < min_breadth_to_trade="
                f"{dna.min_breadth_to_trade}. This is real, upstream-enforced "
                f"multi-asset rotation logic, not fabricated. HOWEVER: this "
                f"adapter's own translation only ever feeds AutoEvolver a "
                f"small internal companion pool (requested ticker + up to "
                f"{UNIVERSE_SIZE - 1} large-cap DEFAULT_US_SYMBOLS — see "
                f"_run_evolution_for_window) so the GA has cross-sectional "
                f"statistics to score against, and this adapter's own "
                f"q3_signal()/q4_policy() report only the single requested "
                f"asset '{resolved_ticker}' back to the harness "
                f"(context.scope=ASSET) — this call is NOT itself a "
                f"multi-asset portfolio-selection result, only a reflection "
                f"of the real mechanism the underlying genome would run if "
                f"given a full universe."
            ),
        )

        # ---- observation_policy: real top-weighted factors this genome uses ----
        observation_policy = ObservationPolicy(
            features=[name for name, _ in top_factors],
            lookback_window=(
                f"[{generation_window.start}, {generation_window.end}] "
                f"(real yfinance OHLCV window used to re-evolve this genome; "
                f"see _run_evolution_for_window)"
            ),
            data_sources=["yfinance OHLCV (US equities, point-in-time)"],
            observation_description=(
                f"score_stock() reads a {w_count}-dimension real w_* factor "
                f"set (technical indicators from upstream's own compute_rsi/"
                f"compute_macd/compute_bollinger_bands/compute_kdj/"
                f"compute_obv_trend/... functions, plus fundamental factors "
                f"that are evolved but score as neutral 0.5 here since this "
                f"adapter passes an empty fundamentals dict — see "
                f"_score_ticker()). `features` above lists only the "
                f"top-{len(top_factors)}-|weight| factors in this specific "
                f"evolved genome, not the full input space."
            ),
        )

        # ---- constraints: only fields honestly expressible from real DNA ----
        active_constraints: List[str] = []

        if dna.stop_loss_per_day and dna.stop_loss_per_day > 0.01:
            active_constraints.append(
                f"stop_loss_per_day={dna.stop_loss_per_day} (adaptive: "
                f"effective stop = min(stop_loss_per_day * hold_days, "
                f"stop_loss_pct={dna.stop_loss_pct}), real upstream "
                f"evaluate())"
            )
        else:
            active_constraints.append(
                f"stop_loss_pct={dna.stop_loss_pct} (fixed %, real upstream "
                f"evaluate(); stop_loss_per_day=0 means the adaptive variant "
                f"is inactive per upstream's own convention)"
            )

        if dna.profit_target_scaling and dna.profit_target_scaling > 0.01:
            active_constraints.append(
                f"take_profit_pct={dna.take_profit_pct} scaled by "
                f"profit_target_scaling={dna.profit_target_scaling} "
                f"(signal-strength-scaled target, real upstream evaluate())"
            )
        else:
            active_constraints.append(
                f"take_profit_pct={dna.take_profit_pct} (fixed %, real "
                f"upstream evaluate(); profit_target_scaling=0 means the "
                f"score-scaled variant is inactive per upstream's own "
                f"convention)"
            )

        if dna.trailing_stop_enabled > 0.5:
            active_constraints.append(
                f"trailing_stop active (trailing_stop_enabled="
                f"{dna.trailing_stop_enabled} > 0.5 per upstream's own "
                f"on/off convention): trailing_activation_pct="
                f"{dna.trailing_activation_pct}, trailing_stop_pct="
                f"{dna.trailing_stop_pct}"
            )
        else:
            active_constraints.append(
                f"trailing_stop_enabled={dna.trailing_stop_enabled} "
                f"(<=0.5 => disabled per upstream's own convention; no "
                f"trailing stop applied)"
            )

        if dna.time_decay_exit and dna.time_decay_exit > 0.01:
            active_constraints.append(
                f"time_decay_exit={dna.time_decay_exit} (progressively "
                f"tightens the stop loss after half the hold period, real "
                f"upstream evaluate())"
            )

        if dna.min_breadth_to_trade and dna.min_breadth_to_trade > 0.01:
            active_constraints.append(
                f"min_breadth_to_trade={dna.min_breadth_to_trade} (goes 100% "
                f"cash when market breadth falls below this, real upstream "
                f"evaluate(); 0 means always-trade per upstream's own "
                f"convention)"
            )

        if dna.market_regime_sensitivity and dna.market_regime_sensitivity > 0.01:
            active_constraints.append(
                f"market_regime_sensitivity={dna.market_regime_sensitivity} "
                f"(reduces effective max concurrent positions in "
                f"weak-breadth regimes, real upstream evaluate())"
            )

        if dna.weekly_trend_confirm and dna.weekly_trend_confirm > 0.5:
            active_constraints.append(
                f"weekly_trend_confirm={dna.weekly_trend_confirm} (>0.5 => "
                f"enabled per upstream's own convention): requires a weekly "
                f"5MA>20MA uptrend before entry"
            )

        if dna.trend_exit_enabled and dna.trend_exit_enabled > 0.5:
            active_constraints.append(
                f"trend_exit_enabled={dna.trend_exit_enabled} (>0.5 => "
                f"enabled per upstream's own convention): exits early if the "
                f"5-day MA crosses below the 10-day MA while holding"
            )

        for field_name, label in (
            ("bear_stop_loss_mult", "tightens stop_loss_pct"),
            ("bear_take_profit_mult", "lowers the take_profit_pct target"),
            ("bear_hold_days_mult", "shortens hold_days"),
        ):
            val = getattr(dna, field_name)
            if val is not None and abs(val - 1.0) > 0.001:
                active_constraints.append(
                    f"{field_name}={val} ({label} in bear-breadth regimes, "
                    f"real upstream evaluate(); 1.0 = no change is "
                    f"upstream's own no-op convention)"
                )

        # NOTE (limitation, report explicitly): dna.sector_max_pct is a real,
        # declared, GA-evolvable StrategyDNA field (see models.py's
        # _PARAM_RANGES) but is NEVER read anywhere in the executed
        # auto_evolve.py evaluate()/backtest path (verified via `grep -rn
        # sector_max_pct` across the whole finclaw package — its only two
        # hits are its own dataclass declaration and mutation range; zero
        # references in auto_evolve.py). Reporting it as an active
        # constraint would be dishonest (upstream itself does not enforce
        # it), so it is intentionally left OUT of additional_constraints —
        # see this adapter's task report for the "computed/evolved but not
        # enforced by upstream's own code" classification.

        constraints = PortfolioConstraints(
            # Verified, not assumed: this adapter always constructs
            # AutoEvolver(market="us", ...) (see _run_evolution_for_window),
            # and upstream's own auto_evolve.py only dispatches to its
            # separate shorts/leverage-capable crypto engine when
            # self.market == "crypto" (see the `_run_backtest_dispatch`
            # branch); for market="us" the inline equity backtest is used,
            # which only ever computes long entries (buy at entry_price,
            # exit at stop/target/trailing-stop/hold-days) — no short/borrow
            # code path is reachable for this adapter's configuration.
            long_only=True,
            # dna.capital_utilization is upstream's own real "fraction of
            # total capital to deploy across positions" (auto_evolve.py:
            # `cap_util = getattr(dna, 'capital_utilization', 1.0)`); since
            # the strategy is long-only, gross deployed capital is directly
            # bounded by this fraction (Kelly sizing can only scale
            # exposure down further, never above it — kelly_scale is
            # clamped to <= 1.0).
            gross_exposure_limit=float(dna.capital_utilization),
            additional_constraints=active_constraints,
        )

        return Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            constraints=constraints,
            artifact=artifact,
            explanation=explanation,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

        result = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = result is not None
        if result is not None:
            checks["direction_is_valid"] = result.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["strength_in_range"] = result.strength is not None and 0.0 <= result.strength <= 1.0
            checks["evidence_nonempty"] = bool(result.evidence)

        # Upstream's own AutoEvolver.load_data() only loads stocks with
        # >= 60 trading days of history (see auto_evolve.py's load_data()
        # docstring/min_days=60) — a window narrower than ~120 calendar
        # days (accounting for weekends/holidays) yields "Loaded 0 stocks"
        # and a real RuntimeError, not a bug in this adapter.
        generation_window = TimeWindow(start="2023-08-01", end="2024-01-15")
        q4_result = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = q4_result is not None
        if q4_result is not None:
            checks["q4_artifact_present"] = q4_result.artifact is not None
            checks["q4_decision_policy_present"] = q4_result.decision_policy is not None
            checks["q4_holding_horizon_set"] = bool(
                q4_result.decision_policy and q4_result.decision_policy.holding_horizon
            )
            checks["q4_universe_policy_present"] = q4_result.universe_policy is not None
            checks["q4_max_assets_positive_int"] = bool(
                q4_result.universe_policy
                and isinstance(q4_result.universe_policy.max_assets, int)
                and q4_result.universe_policy.max_assets > 0
            )
            checks["q4_observation_features_nonempty"] = bool(
                q4_result.observation_policy and q4_result.observation_policy.features
            )
            checks["q4_constraints_present"] = q4_result.constraints is not None
            checks["q4_long_only_true"] = bool(
                q4_result.constraints and q4_result.constraints.long_only is True
            )
            checks["q4_additional_constraints_nonempty"] = bool(
                q4_result.constraints and q4_result.constraints.additional_constraints
            )
        return checks
