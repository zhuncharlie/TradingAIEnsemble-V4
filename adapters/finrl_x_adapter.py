"""
adapters/finrl_x_adapter.py — wraps github.com/AI4Finance-Foundation/FinRL-Trading
(Q3 ML-factor stock-selection signal, Q4 DRL portfolio allocation with
regime-aware cash overlay).

============================================================================
Repo search / vetting process (target was "FinRL-X", NOT confirmed to exist
as a literal repo name going in — per session brief, searched thoroughly
before trusting any name match)
============================================================================
  - WebSearch for "FinRL-X github regime switching DRL portfolio" surfaced
    `AI4Finance-Foundation/FinRL-Trading`, whose README literally opens with
    "FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading"
    — i.e. FinRL-X is the *paper/project name*, `FinRL-Trading` is the repo
    name it actually shipped under. Also checked the AI4Finance-Foundation
    org's other satellite repos (FinRL-Meta, FinRL_Podracer, ElegantRL,
    FinRL_Crypto, FinRL-Tutorials) per the session brief's suggestion that
    the real match might be "in the same family under a different name" —
    none of those match the "top-25%-NASDAQ ML factor selection +
    regime-switching DRL allocation" description; FinRL-Trading is the one
    that does.
  - Verified NOT a squat/homonym before trusting it: `gh`/`git` clone
    confirmed it is genuinely under the real `AI4Finance-Foundation` org
    (WebFetch of `github.com/orgs/AI4Finance-Foundation/repositories`
    lists it alongside FinRL/FinRL-Meta/FinGPT/etc.), v1.0.0 released
    2026-03-25, 3.4k stars/1k forks, 317 commits, Apache-2.0 — not
    abandoned or unrelated. README's "Use Case 2 — Rolling Stock Selection
    + DRL" section literally reads: "Quarterly selection of top-25%
    NASDAQ-100 stocks via ML fundamental scoring, combined with DRL-based
    portfolio allocation. Strict no-lookahead semantics prevent data
    leakage." and "Use Case 3 — Adaptive Multi-Asset Rotation" implements
    the regime-switching (Growth Tech / Real Assets / Defensive groups,
    slow 26-week-trend+VIX regime + fast 3-day shock overlay) — this is an
    exact match for the session brief's "adaptive DRL that switches between
    growth/defensive/neutral regimes; selects the top 25% of NASDAQ stocks
    using ML factors, then allocates via DRL", not a loose approximation.
  - Confirmed real, runnable code (not a paper-only or notebook-only repo):
    `src/strategies/ml_bucket_selection.py` (real RandomForest/XGBoost/
    LightGBM/HistGradientBoosting/ExtraTrees/Ridge/Stacking ensemble
    competition, `run_bucket()`), `src/strategies/adaptive_rotation/
    market_regime.py` (real slow/fast regime detection), `src/strategies/
    fundamental_portfolio_drl.py` / `rl_model.py` (real FinRL DRLAgent/
    StockPortfolioEnv usage) all exist as genuine, documented, importable
    Python modules — not vaporware.

============================================================================
Security screening (same checks used for every adapter this session:
eval/exec/os.system/shell=True grep, credential-harvesting grep, file-tree
scan for an unrelated merged subtree like FinGPT's `finogrid/`)
============================================================================
  - `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|subprocess\\.(call|run|Popen)"`
    across `src/`, `examples/`, `deploy.sh` — zero hits.
  - File tree (`src/data`, `src/strategies`, `src/backtest`, `src/trading`,
    `src/web`, `src/config`, `src/tools`, `src/utils`, `examples`, `docs`,
    `figs`) is entirely on-topic for a quant trading platform — no
    unrelated subtree merged under a misleading branch name.
  - `api_key`/`secret`/`password`/`token`/`credential` grep hits are
    confined to: (a) `src/config/settings.py`'s `.env.example` template
    (Alpaca, WRDS, FMP, OpenAI — all read via `os.environ`/pydantic
    `SecretStr`, never hardcoded); (b) `src/data/data_fetcher.py` /
    `backfill_historical_sp500.py` / `ml_bucket_selection.py`'s FMP API
    calls; (c) `src/trading/trade_executor.py` / `performance_analyzer.py`'s
    Alpaca live-trading account code. **This adapter's code path never
    imports or calls any of (c)** — no brokerage/exchange account,
    real money, or live trading is used anywhere.
  - **FMP (Financial Modeling Prep) requirement avoided by design**:
    upstream's *own* ML stock-selection pipeline
    (`ml_bucket_selection.py`) is designed to read from a pre-populated
    SQLite database (`data/finrl_trading.db`, 22,909 quarterly
    fundamental records for ~715 tickers, 2015-2026) that upstream's own
    `fetch_and_store_fundamentals.py` builds by calling FMP's paid-tier
    endpoints (income-statement/balance-sheet/cash-flow/ratios × ~10
    years × hundreds of tickers). That database is not checked into the
    repo (gitignored) and is not reproducible without an FMP API key and
    a very large number of API calls — squarely the kind of "needs data
    you don't have access to" case the brief pre-authorizes a live-yfinance
    scope reduction for (see "Design notes" below). **No FMP, WRDS, Alpaca,
    or any paid/brokerage credential is read, required, or referenced by
    this adapter.** Only `yfinance` (free, public OHLCV + statement data,
    no account) is used, satisfying the brief's stop-condition check.
  - No LLM API key is used or needed anywhere in this adapter (confirmed:
    `openai` appears in FinRL-Trading's `requirements.txt` for an
    unrelated news-sentiment feature this adapter never imports).

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n finrl_x_real python=3.10
    conda activate finrl_x_real
    conda install -c conda-forge xgboost -y
    # (lightgbm deliberately NOT installed — see "SIGSEGV" note below;
    #  upstream's own build_models() already wraps the lightgbm import in
    #  try/except ImportError and just drops it from the model roster, so
    #  omitting it is a supported upstream code path, not a workaround
    #  that fights the library.)
    pip install "yfinance==0.2.66" stable-baselines3[extra] gymnasium \\
                stockstats scikit-learn pandas numpy matplotlib torch \\
                pydantic pydantic-settings pyyaml pandas-market-calendars
    pip install "numpy==1.24.4"
    # PIN numpy back down after installing pandas-market-calendars: that
    # package's own dependency resolver wants numpy>=1.26 (via
    # exchange-calendars), but scipy/sklearn/xgboost in this env were built
    # against numpy<1.25. Re-pinning to 1.24.4 after the fact leaves a pip
    # dependency-conflict *warning* (exchange-calendars wants >=1.26) but
    # importing pandas_market_calendars + scipy + sklearn + xgboost
    # together was verified to work fine at 1.24.4 — same "pin to the
    # vintage the rest of the stack needs" lesson as FinGPT's transformers
    # pin and FinRL's yfinance pin earlier this session.
    git clone --depth 1 https://github.com/AI4Finance-Foundation/FinRL-Trading.git \\
        adapters/vendor/FinRL-Trading
    # This adapter ALSO depends on the separate AI4Finance-Foundation/FinRL
    # package: FinRL-Trading's own DRL modules
    # (src/strategies/fundamental_portfolio_drl.py, rl_model.py) import
    # `finrl.agents.stablebaselines3.models.DRLAgent`,
    # `finrl.meta.env_portfolio_allocation.env_portfolio.StockPortfolioEnv`,
    # etc. — but `finrl` is NOT listed in FinRL-Trading's own
    # requirements.txt/setup.py (those two files appear to be carried over
    # from the original author's separate dev checkout of FinRL sitting on
    # PYTHONPATH). This adapter's Q4 does not call those two specific
    # files (see "Design notes" below for why), but it does need the same
    # `finrl` building blocks they use, so it reuses the identical
    # `adapters/vendor/FinRL` clone + patch that `adapters/finrl_adapter.py`
    # already set up this session (same upstream repo, same eager-import
    # problem, same fix — see `patches/FinRL.diff`, already committed by
    # that session, reused here unmodified — not re-authored):
    #   git clone --depth 1 https://github.com/AI4Finance-Foundation/FinRL.git \\
    #       adapters/vendor/FinRL
    #   # then apply patches/FinRL.diff to adapters/vendor/FinRL/finrl/__init__.py
    # (vendor/ is gitignored either way, so this is just "clone the same
    # public repo to the same local path" — no cross-adapter Python import
    # of `adapters/finrl_adapter.py` itself occurs anywhere in this file.)

Run the harness with that env active:
    conda activate finrl_x_real
    python CONTRACT/test_harness.py --adapter adapters/finrl_x_adapter.py

============================================================================
A real, sandbox-specific crash found and worked around (documented per
"never silently modify vendor code" — this is an *environment* fix, not a
patch to any vendor file, so no patches/*.diff was needed for it)
============================================================================
  `ml_bucket_selection.py`'s own `build_models()` hardcodes `n_jobs=-1` on
  `RandomForestRegressor`, `ExtraTreesRegressor`, and the final
  `StackingRegressor` (upstream's own code, not a parameter this adapter
  controls). In this sandbox (52 visible cores), letting joblib resolve
  `n_jobs=-1` to "use all cores" causes `StackingRegressor.fit()`'s nested
  `cross_val_predict()` to fork/spawn worker processes that each try to
  fit an OpenMP-parallel estimator (`HistGradientBoostingRegressor`, and
  originally `LGBMRegressor` before it was dropped from the install) —
  every one of those workers segfaults
  (`joblib.externals.loky.process_executor.TerminatedWorkerError`,
  `SIGSEGV`/`SIGABRT`), reproduced identically under both the default
  `loky` (process) backend and a `threading` backend, and independent of
  `OMP_NUM_THREADS`/`LOKY_START_METHOD` tuning — i.e. an environment-level
  fork+OpenMP fragility in this sandbox, not a bug in upstream's modeling
  code. Root-caused by testing `RandomForestRegressor`/`XGBRegressor`/
  `LGBMRegressor`/`StackingRegressor` fits individually and finding it's
  specifically triggered by nested nested Parallel() workers that
  themselves invoke an OpenMP-parallel `.fit()`; confirmed
  `loky.cpu_count()` (what joblib's `n_jobs=-1` resolves against) tracks
  `os.sched_getaffinity(0)` on Linux. Fix applied entirely in this
  adapter's own process, around the `run_bucket()` call only: temporarily
  restrict this process's own CPU affinity to a single core
  (`os.sched_setaffinity(0, {0})`) for the duration of that one call, then
  restore the original affinity immediately after. With affinity=1,
  `loky.cpu_count()` resolves to 1, joblib's `Parallel(n_jobs=-1)` takes
  its "n_jobs==1 ⇒ run sequentially in-process, never fork" fast path, and
  `run_bucket()` completes in ~3s with zero crashes. This changes nothing
  about upstream's modeling logic or results (still the same 6-model
  competition, same Stacking ensemble, same feature importances) — it only
  forces those calls to execute sequentially rather than in parallel, and
  only for the few seconds `run_bucket()` runs; DRL training afterwards
  runs with this process's normal, unrestricted affinity. `lightgbm` was
  also left out of the conda env for the same reason (upstream's own
  `build_models()` already treats it as optional via
  `try/except ImportError`), rather than fighting the segfault twice.

============================================================================
Design notes (translation choices made by this adapter, not upstream)
============================================================================
  - **Q3 universe**: upstream's real NASDAQ-100 constituent fetch
    (`fetch_nasdaq100_tickers()`) calls FMP, which this adapter avoids (see
    security section). Substituted a static, hand-picked snapshot of 30
    large, liquid, long-listed NASDAQ-100-style constituents spanning
    growth/tech, healthcare, and consumer/staples names (`NASDAQ_UNIVERSE`
    below) — a scope reduction from "the live ~100-name index membership"
    to "a fixed representative subset", not a reimplementation of
    upstream's selection *logic* (the ranking model itself is 100%
    upstream's `run_bucket()`, untouched).
  - **Fundamentals data source**: upstream's own quarterly-fundamentals
    database (FMP-built, see security section) is replaced with fundamentals
    computed live from `yfinance`'s `Ticker.quarterly_financials` /
    `quarterly_balance_sheet` (free, public, no account) for each name in
    `NASDAQ_UNIVERSE`. Of upstream's 28 `FEATURE_COLS`, this adapter
    computes the 9 that map cleanly onto fields yfinance actually exposes
    (`FEATURE_COLS` below: pe, ps, pb, roe, gross_margin, operating_margin,
    debt_to_equity, cur_ratio, EPS) — same names/semantics as upstream's
    own column list, just a smaller subset, passed as the `feature_cols`
    *argument* to upstream's own `run_bucket(bucket, bdf, feature_cols,
    val_cutoff, val_quarters)` (a real parameter of that function, not a
    hardcoded constant this adapter had to bypass). PE/PS/PB are computed
    as `price / (4 × quarterly_metric)` (crude quarterly-to-annualized
    conversion) rather than upstream's true TTM/annual-filing figures — a
    documented simplification, not upstream logic reimplemented (the
    *model* that consumes these features, and the ranking/ensemble/
    stacking logic around them, is still 100% upstream's own code).
    Missing values are filled with the column's global median and ±inf
    clipped to NaN before filling — matching the data-hygiene step
    upstream's own `ML_STOCK_SELECTION.md` documents ("Fill missing with
    global median, replace inf with 0"), reimplemented here only because
    it's adapter-side glue to get this adapter's own live-fetched data into
    upstream's expected shape (same category as `finrl_adapter.py`'s
    `cov_list` construction).
  - **Fiscal-quarter calendar alignment (adapter-side glue, not upstream
    logic)**: yfinance reports each company's own fiscal quarter-end dates
    (e.g. NVDA's ~Jan/Apr/Jul/Oct cycle vs. AAPL's calendar-quarter cycle),
    whereas upstream's own point-in-time system assumes a single shared
    `datadate` grid (Compustat/FMP-style calendar-quarter convention).
    Without alignment, `run_bucket()`'s date-based train/val/infer split
    (which groups rows by exact `datadate` match) fragments the universe
    across dozens of near-but-not-identical dates instead of comparing all
    30 tickers side by side. This adapter snaps each ticker's actual
    fiscal quarter-end to the *nearest* standard calendar quarter-end
    (03-31/06-30/09-30/12-31) before calling `run_bucket()` — pure date
    bucketing, not a change to the ranking/selection logic itself.
  - **`val_cutoff`/inference window**: because different tickers have
    already-reported as of different numbers of (aligned) quarters, this
    adapter sets `val_cutoff` to the third-most-recent aligned quarter
    (`val_quarters=1`), so `infer_dates` covers the two most recent aligned
    quarters combined — this reproduces upstream's own documented
    "mixed-vintage" idea (`ML_STOCK_SELECTION.md`: "use latest available
    data per ticker") using upstream's own `run_bucket()` unmodified, then
    de-duplicates to one row per ticker (keeping the latest available
    quarter) as a simple adapter-side post-processing step.
  - **Q3 direction/strength**: `direction` = LONG if the ticker's
    `predicted_return` rank places it in upstream's own "top 25%" cutoff
    (mirroring the target description exactly), SHORT if in the bottom
    25%, else NEUTRAL. `strength` = `abs(percentile - 0.5) * 2`, i.e. 0 at
    the median forecast and 1 at either extreme of the cross-sectional
    ranking — an adapter-side confidence proxy (analogous to
    `deepalpha_adapter.py`'s ensemble-dispersion-based `strength`), not an
    upstream-native confidence score (upstream doesn't expose one).
    `supporting_evidence` is upstream's own real per-run
    `feature_importances_`/coefficients for that quarter's best model (top
    3, by upstream's own `importance_records` output), never hardcoded.
  - **Q3 `date` parameter caveat**: yfinance's quarterly statements always
    return the *latest available* reported quarters as of when this
    adapter runs, not "as of the requested `date`" — unlike upstream's own
    point-in-time SQLite database, which can apply an exact
    `--infer-date`/`--val-cutoff` filter to arbitrarily old dates. This
    adapter's fundamentals therefore reflect current data regardless of
    the `date` argument; `date` is passed through to the output for
    labeling only. This is a known limitation of avoiding the paid-FMP
    point-in-time database (see security section) — genuine point-in-time
    historical fundamentals are exactly the "data you don't have access
    to" case the brief anticipates. Price-based inputs (Q4's DRL training
    window) ARE correctly point-in-time (fetched up to `date`).
  - **Q4 universe**: the DRL allocator always trades upstream's own
    ML-selected top-25% subset of `NASDAQ_UNIVERSE` (computed via the same
    cached `run_bucket()` call Q3 uses) — reflecting the target
    description's fixed 2-stage pipeline ("selects the top 25% of NASDAQ
    stocks using ML factors, then allocates via DRL"), not an arbitrary
    caller-supplied ticker basket. The `tickers` argument `q4_portfolio()`
    receives (e.g. the harness's `["AAPL","MSFT","NVDA"]`) is intersected
    with the ML-selected set only as an informational overlap check
    logged into `rationale`; if none of the caller's tickers made the
    cut, the full ML-selected set is used regardless. This mirrors how
    other adapters this session have documented deliberate reinterpretations
    of a CONTRACT argument when the upstream project's own paradigm is
    "select, then allocate" rather than "allocate over exactly what I hand
    you".
  - **Q4 DRL training**: same real-upstream-FinRL building blocks and same
    "train live, scoped down" budget `adapters/finrl_adapter.py` already
    validated this session (`FeatureEngineer`, `YahooDownloader`-equivalent
    yfinance fetch, `StockPortfolioEnv`, `DRLAgent` wrapping real
    `stable_baselines3.A2C`, `TOTAL_TIMESTEPS=3000`,
    `COV_LOOKBACK_DAYS=60`, `HISTORY_DAYS=550`) rather than
    `rl_model.py`'s own `train_a2c`/`train_ppo`/`train_ddpg` helpers, whose
    `total_timesteps` (50000/80000/50000) are hardcoded literals with no
    override parameter — training even one of those three at upstream's
    own hardcoded budget would blow well past the harness's timeouts, let
    alone competing all three as `rl_model.run_models()` does. Using
    upstream FinRL's own `DRLAgent`/`StockPortfolioEnv` API directly (the
    same API `rl_model.py` itself calls) with a documented, reduced
    timestep budget is the same category of scope reduction
    `finrl_adapter.py` already used and documented for its own Q4 — not a
    reimplementation of the reward/environment/policy logic itself (100%
    upstream `stable_baselines3`/`StockPortfolioEnv`).
  - **Q4 `regime`**: computed from upstream's own
    `adaptive_rotation.market_regime.detect_slow_regime()`, fed real
    weekly `^GSPC`/`^VIX` closes (via `yfinance`) and upstream's own
    shipped `AdaptiveRotationConf_v1.2.2.yaml` (loaded via upstream's own
    `config_loader.load_config()`, unmodified). Upstream's
    `SlowRegimeState` (`RISK_ON`/`NEUTRAL`/`RISK_OFF`) is mapped to
    CONTRACT's `Regime` enum as `RISK_ON→BULL`, `NEUTRAL→SIDEWAYS`,
    `RISK_OFF→BEAR` — an adapter-side label mapping, not a change to
    upstream's regime-detection logic. Upstream's own `effective_cash_floor`
    output (from the same regime result) is blended with the DRL policy's
    own (usually ~0) cash allocation via `cash_ratio = max(drl_cash,
    regime_cash_floor)`, rescaling the DRL weights down proportionally if
    the regime's floor is higher — i.e. the regime genuinely modulates the
    final allocation (matching the target description's "switches between
    ...regimes"), using upstream's own regime/cash-floor numbers, not an
    invented rule.
  - Per-(universe) and per-(selected tickers, date) in-memory caching:
    the ML panel/ranking (fundamentals-based, doesn't vary with `date` per
    the caveat above) is fetched and ranked once per process; DRL training
    is cached per (selected-ticker-set, date), matching
    `finrl_adapter.py`'s own caching rationale (the harness calls each Q
    method directly AND again via `adapter.run()` with identical
    arguments).
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Direction,
    Q3Signal,
    Q4Portfolio,
    Regime,
    SignalType,
)

STRATEGIES_DIR = Path(__file__).resolve().parent / "vendor" / "FinRL-Trading" / "src" / "strategies"
FINRL_DEP_DIR = Path(__file__).resolve().parent / "vendor" / "FinRL"
for _p in (STRATEGIES_DIR, FINRL_DEP_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CONFIG_YAML = STRATEGIES_DIR / "AdaptiveRotationConf_v1.2.2.yaml"

# ---------------------------------------------------------------------------
# Scoped-down NASDAQ universe (see header: FMP-based live NASDAQ-100
# constituent fetch avoided; static representative snapshot used instead)
# ---------------------------------------------------------------------------
NASDAQ_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "COST", "NFLX",
    "ADBE", "PEP", "AMD", "CSCO", "INTC", "QCOM", "TXN", "INTU", "AMGN", "HON",
    "SBUX", "BKNG", "GILD", "MDLZ", "ADI", "VRTX", "REGN", "ISRG", "PANW", "LRCX",
]

# Subset of upstream's own FEATURE_COLS this adapter can compute live from
# yfinance quarterly statements (see header "Fundamentals data source").
FEATURE_COLS = ["pe", "ps", "pb", "roe", "gross_margin", "operating_margin",
                "debt_to_equity", "cur_ratio", "EPS"]

TOP_QUANTILE = 0.25          # "top 25%" per the target description
TOTAL_TIMESTEPS = 3000        # DRL training budget — "train live", not paper-scale
COV_LOOKBACK_DAYS = 60        # rolling-covariance window (reduced from upstream tutorial's 252)
HISTORY_DAYS = 550            # ~1.5 calendar years of price history for DRL training windows
MODEL_NAME = "a2c"
INITIAL_AMOUNT = 1_000_000
HMAX = 100
TRANSACTION_COST_PCT = 0.001
REWARD_SCALING = 1e-1

_ML_CACHE: Optional[Tuple[pd.DataFrame, List[dict], List[dict]]] = None
_REGIME_CACHE: Dict[str, object] = {}
_DRL_CACHE: Dict[Tuple[tuple, str], "Q4Portfolio"] = {}


@contextmanager
def _single_core():
    """
    Temporarily restrict this process's own CPU affinity to one core.

    Works around a sandbox-specific SIGSEGV/TerminatedWorkerError in
    upstream's own `run_bucket()` (hardcoded `n_jobs=-1` on several
    estimators) — see header "A real, sandbox-specific crash found and
    worked around". Best-effort: if the platform doesn't support
    `sched_setaffinity` (e.g. non-Linux), this is a no-op.
    """
    try:
        original = os.sched_getaffinity(0)
        os.sched_setaffinity(0, {next(iter(original))})
    except (AttributeError, OSError):
        original = None
    try:
        yield
    finally:
        if original is not None:
            try:
                os.sched_setaffinity(0, original)
            except OSError:
                pass


def _nearest_std_quarter_end(d) -> str:
    """Snap a company's actual fiscal quarter-end to the nearest standard
    calendar quarter-end (03-31/06-30/09-30/12-31) — see header "Fiscal-
    quarter calendar alignment"."""
    d = pd.Timestamp(d)
    candidates = [
        pd.Timestamp(f"{y}-{mmdd}")
        for y in (d.year - 1, d.year, d.year + 1)
        for mmdd in ("03-31", "06-30", "09-30", "12-31")
    ]
    best = min(candidates, key=lambda c: abs((c - d).days))
    return best.strftime("%Y-%m-%d")


def _safe_get(stmt: pd.DataFrame, keys: List[str], col) -> float:
    for k in keys:
        if k in stmt.index and col in stmt.columns:
            v = stmt.loc[k, col]
            if pd.notna(v):
                return float(v)
    return float("nan")


def _build_fundamentals_panel(tickers: List[str]) -> pd.DataFrame:
    """Real yfinance quarterly statements + price history -> a per-
    (ticker, aligned-quarter) panel of upstream-named factor columns, ready
    to hand to upstream's own `run_bucket()`. Adapter-side data-prep glue
    (see header) — the ranking/ensemble logic downstream is 100% upstream."""
    import yfinance as yf

    rows = []
    for tic in tickers:
        try:
            tkr = yf.Ticker(tic)
            qf = tkr.quarterly_financials
            qbs = tkr.quarterly_balance_sheet
            if qf is None or qf.empty or qbs is None or qbs.empty:
                continue
            quarters = sorted(set(qf.columns) & set(qbs.columns))
            if len(quarters) < 4:
                continue
            hist = tkr.history(
                start=quarters[0] - pd.Timedelta(days=10),
                end=quarters[-1] + pd.Timedelta(days=10),
            )["Close"]
            if hist.empty:
                continue
            if hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)

            for q in quarters:
                asof = hist[hist.index <= q]
                price_q = float(asof.iloc[-1]) if len(asof) else float("nan")
                revenue = _safe_get(qf, ["Total Revenue", "Operating Revenue"], q)
                gross_profit = _safe_get(qf, ["Gross Profit"], q)
                op_income = _safe_get(qf, ["Operating Income"], q)
                net_income = _safe_get(qf, ["Net Income", "Net Income Common Stockholders"], q)
                eps = _safe_get(qf, ["Diluted EPS", "Basic EPS"], q)
                shares = _safe_get(qbs, ["Ordinary Shares Number", "Share Issued"], q)
                equity = _safe_get(qbs, ["Stockholders Equity", "Common Stock Equity"], q)
                total_debt = _safe_get(qbs, ["Total Debt"], q)
                cur_assets = _safe_get(qbs, ["Current Assets"], q)
                cur_liab = _safe_get(qbs, ["Current Liabilities"], q)

                market_cap = price_q * shares if shares == shares and price_q == price_q else float("nan")
                pe = price_q / (4 * eps) if eps == eps and eps > 0 else float("nan")
                ps = market_cap / (4 * revenue) if revenue == revenue and revenue > 0 and market_cap == market_cap else float("nan")
                pb = market_cap / equity if equity == equity and equity > 0 and market_cap == market_cap else float("nan")
                roe = (net_income * 4) / equity if equity == equity and equity > 0 and net_income == net_income else float("nan")
                gm = gross_profit / revenue if revenue == revenue and revenue > 0 and gross_profit == gross_profit else float("nan")
                om = op_income / revenue if revenue == revenue and revenue > 0 and op_income == op_income else float("nan")
                dte = total_debt / equity if equity == equity and equity > 0 and total_debt == total_debt else float("nan")
                cr = cur_assets / cur_liab if cur_liab == cur_liab and cur_liab > 0 and cur_assets == cur_assets else float("nan")

                rows.append(dict(
                    tic=tic, datadate=_nearest_std_quarter_end(q), price=price_q,
                    pe=pe, ps=ps, pb=pb, roe=roe, gross_margin=gm, operating_margin=om,
                    debt_to_equity=dte, cur_ratio=cr, EPS=eps,
                ))
        except Exception:
            continue  # a single ticker's data hiccup shouldn't sink the whole panel

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("yfinance returned no usable quarterly fundamentals for the scoped NASDAQ universe")

    for c in FEATURE_COLS:
        df[c] = df[c].replace([np.inf, -np.inf], np.nan)
        df[c] = df[c].fillna(df[c].median())

    df = df.sort_values(["tic", "datadate"]).reset_index(drop=True)
    df["price_next"] = df.groupby("tic")["price"].shift(-1)
    df["y_return"] = np.log(df["price_next"] / df["price"])
    return df


def _get_ml_selection() -> Tuple[pd.DataFrame, List[dict], List[dict]]:
    """Cached: build the fundamentals panel and call upstream's own
    `run_bucket()` (real RF/XGB/HistGBM/ExtraTrees/Ridge/Stacking ensemble
    competition, unmodified) to rank the scoped universe by predicted
    forward return. Returns (ranking_df [one row per ticker, most recent
    aligned quarter], model_results, importance_records)."""
    global _ML_CACHE
    if _ML_CACHE is not None:
        return _ML_CACHE

    import ml_bucket_selection as mbs  # upstream, unmodified

    df = _build_fundamentals_panel(NASDAQ_UNIVERSE)
    quarters_all = sorted(df["datadate"].unique())
    if len(quarters_all) < 3:
        raise RuntimeError(f"Not enough aligned quarters ({len(quarters_all)}) to form train/val/infer split")
    val_cutoff = quarters_all[-3]  # see header "val_cutoff/inference window"

    with _single_core():
        infer_b, model_results, importance_records = mbs.run_bucket(
            "nasdaq_top25", df, FEATURE_COLS, val_cutoff=val_cutoff, val_quarters=1,
        )

    ranking = (
        infer_b.sort_values("datadate")
        .drop_duplicates("tic", keep="last")
        .sort_values("predicted_return", ascending=False)
        .reset_index(drop=True)
    )
    ranking["rank_position"] = np.arange(1, len(ranking) + 1)

    _ML_CACHE = (ranking, model_results, importance_records)
    return _ML_CACHE


def _get_regime(date: str):
    """Cached: upstream's own slow-regime detector, fed real weekly
    ^GSPC/^VIX closes and upstream's own shipped YAML config."""
    if date in _REGIME_CACHE:
        return _REGIME_CACHE[date]

    import yfinance as yf
    from adaptive_rotation.config_loader import load_config
    from adaptive_rotation.market_regime import detect_slow_regime

    cfg = load_config(str(CONFIG_YAML))
    as_of = pd.Timestamp(date)
    fetch_start = (as_of - pd.DateOffset(years=4)).strftime("%Y-%m-%d")
    fetch_end = (as_of + pd.DateOffset(days=1)).strftime("%Y-%m-%d")

    spx = yf.download("^GSPC", start=fetch_start, end=fetch_end, progress=False)["Close"].squeeze()
    vix = yf.download("^VIX", start=fetch_start, end=fetch_end, progress=False)["Close"].squeeze()
    spx_weekly = spx.resample("W-FRI").last().dropna()
    vix_weekly = vix.resample("W-FRI").last().dropna()
    if spx_weekly.index.tz is not None:
        spx_weekly.index = spx_weekly.index.tz_localize(None)
        vix_weekly.index = vix_weekly.index.tz_localize(None)

    result = detect_slow_regime(spx_weekly, vix_weekly, as_of, cfg)
    _REGIME_CACHE[date] = result
    return result


_REGIME_TO_CONTRACT = {
    "risk_on": Regime.BULL,
    "neutral": Regime.SIDEWAYS,
    "risk_off": Regime.BEAR,
}


def _fetch_and_engineer(tickers: List[str], fetch_start: str, fetch_end: str) -> pd.DataFrame:
    """Real yfinance data via upstream FinRL's own YahooDownloader +
    FeatureEngineer, plus the same adapter-side rolling-covariance
    ('cov_list') glue `finrl_adapter.py` documented and validated this
    session (upstream's own StockPortfolioEnv requires it as input)."""
    from finrl import config
    from finrl.meta.preprocessor.preprocessors import FeatureEngineer
    from finrl.meta.preprocessor.yahoodownloader import YahooDownloader

    raw = YahooDownloader(start_date=fetch_start, end_date=fetch_end, ticker_list=tickers).fetch_data()
    if raw.empty:
        raise RuntimeError(f"yfinance/YahooDownloader returned no data for {tickers} [{fetch_start},{fetch_end})")

    fe = FeatureEngineer(
        use_technical_indicator=True,
        tech_indicator_list=config.INDICATORS,
        use_vix=False,
        use_turbulence=False,
        user_defined_feature=False,
    )
    df = fe.preprocess_data(raw)
    df = df.sort_values(["date", "tic"], ignore_index=True)

    unique_dates = df.date.unique()
    if len(unique_dates) <= COV_LOOKBACK_DAYS + 5:
        raise RuntimeError(
            f"Not enough trading days ({len(unique_dates)}) for a "
            f"{COV_LOOKBACK_DAYS}-day covariance lookback — widen the date range."
        )

    cov_list, dates_out = [], []
    for i in range(COV_LOOKBACK_DAYS, len(unique_dates)):
        window = df[(df.date >= unique_dates[i - COV_LOOKBACK_DAYS]) & (df.date <= unique_dates[i - 1])]
        price_pivot = window.pivot_table(index="date", columns="tic", values="close")
        rets = price_pivot.pct_change().dropna()
        cov_list.append(rets.cov().values)
        dates_out.append(unique_dates[i])

    df_cov = pd.DataFrame({"date": dates_out, "cov_list": cov_list})
    df = df.merge(df_cov, on="date")
    df = df.sort_values(["date", "tic"]).reset_index(drop=True)
    return df


def _train_and_allocate(tickers: List[str], date: str) -> Dict[str, float]:
    """Real upstream FinRL DRL training (StockPortfolioEnv + DRLAgent
    wrapping real stable_baselines3.A2C), scoped down per header "Q4 DRL
    training". Returns the final-day softmax-normalized weights."""
    from finrl import config
    from finrl.agents.stablebaselines3.models import DRLAgent
    from finrl.meta.env_portfolio_allocation.env_portfolio import StockPortfolioEnv
    from finrl.meta.preprocessor.preprocessors import data_split

    end_ts = pd.Timestamp(date)
    fetch_start = (end_ts - pd.DateOffset(days=HISTORY_DAYS)).strftime("%Y-%m-%d")
    fetch_end = (end_ts + pd.DateOffset(days=1)).strftime("%Y-%m-%d")

    df = _fetch_and_engineer(tickers, fetch_start, fetch_end)
    train_df = data_split(df, fetch_start, fetch_end)

    stock_dim = len(tickers)
    env_gym = StockPortfolioEnv(
        df=train_df, hmax=HMAX, initial_amount=INITIAL_AMOUNT,
        transaction_cost_pct=TRANSACTION_COST_PCT, state_space=stock_dim,
        stock_dim=stock_dim, tech_indicator_list=config.INDICATORS,
        action_space=stock_dim, reward_scaling=REWARD_SCALING,
    )
    env_vec, _ = env_gym.get_sb_env()
    agent = DRLAgent(env=env_vec)
    model = agent.get_model(MODEL_NAME, model_kwargs=config.A2C_PARAMS, verbose=0)
    trained = DRLAgent.train_model(model=model, tb_log_name=MODEL_NAME, total_timesteps=TOTAL_TIMESTEPS)

    _, actions_df = DRLAgent.DRL_prediction(model=trained, environment=env_gym)
    last_row = actions_df.iloc[-1]
    weights = {tic: max(0.0, float(w)) for tic, w in last_row.items()}
    total_w = sum(weights.values())
    if total_w > 1.0:
        weights = {k: v / total_w for k, v in weights.items()}
    return weights


class FinRLXAdapter(BaseAdapter):
    name = "finrl_x"
    questions_answered = ["Q3", "Q4"]
    upstream_repo = "https://github.com/AI4Finance-Foundation/FinRL-Trading"
    requires_env = "finrl_x_real"

    # ------------------------------------------------------------------
    # Q3 — ML-factor stock-selection signal
    # ------------------------------------------------------------------
    def q3_signal(self, ticker: str, date: str, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()
        ranking, model_results, importance_records = _get_ml_selection()
        n = len(ranking)
        top_cut = max(1, round(TOP_QUANTILE * n))

        row = ranking[ranking.tic == ticker]
        if row.empty:
            return Q3Signal(
                signal_type=SignalType.FACTOR,
                direction=Direction.NEUTRAL,
                strength=0.0,
                supporting_evidence=[
                    f"{ticker} is outside this adapter's scoped {n}-name NASDAQ "
                    f"universe (see NASDAQ_UNIVERSE in adapters/finrl_x_adapter.py) "
                    f"— no ML factor ranking available for it."
                ],
                expected_horizon="1q",
                expected_return=None,
                adapter=self.name, ticker=ticker, date=date,
                cost_usd=0.0, latency_sec=time.time() - t0,
            )

        rank = int(row["rank_position"].iloc[0])
        pct = (n - rank) / (n - 1) if n > 1 else 0.5
        is_top25 = rank <= top_cut
        is_bottom25 = rank > (n - top_cut)
        direction = Direction.LONG if is_top25 else Direction.SHORT if is_bottom25 else Direction.NEUTRAL
        strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))

        best_model = row["best_model"].iloc[0]
        best_importances = sorted(
            [r for r in importance_records if r["model"] == best_model and r["is_best"]],
            key=lambda r: r["rank"],
        )[:3]
        if best_importances:
            supporting_evidence = [f"{r['feature']} (importance={r['importance']:.3f}, model={best_model})" for r in best_importances]
        else:
            supporting_evidence = [f"predicted_return rank {rank}/{n} (model={best_model})"]

        expected_return = float(row["predicted_return"].iloc[0])

        return Q3Signal(
            signal_type=SignalType.FACTOR,
            direction=direction,
            strength=strength,
            supporting_evidence=supporting_evidence,
            expected_horizon="1q",
            expected_return=expected_return,
            adapter=self.name, ticker=ticker, date=date,
            cost_usd=0.0, latency_sec=time.time() - t0,
        )

    # ------------------------------------------------------------------
    # Q4 — DRL portfolio allocation over the ML-selected top-25% subset
    # ------------------------------------------------------------------
    def q4_portfolio(self, tickers: List[str], date: str, **kwargs) -> Optional[Q4Portfolio]:
        t0 = time.time()
        ranking, _, _ = _get_ml_selection()
        n = len(ranking)
        top_cut = max(2, round(TOP_QUANTILE * n))
        selected = ranking.head(top_cut)["tic"].tolist()

        cache_key = (tuple(sorted(selected)), date)
        if cache_key in _DRL_CACHE:
            cached = _DRL_CACHE[cache_key]
            cached.latency_sec = time.time() - t0
            return cached

        overlap = sorted(set(tickers or []) & set(selected))

        weights = _train_and_allocate(selected, date)
        drl_cash = max(0.0, 1.0 - sum(weights.values()))

        regime_result = _get_regime(date)
        regime_label = _REGIME_TO_CONTRACT.get(regime_result.state.value, Regime.SIDEWAYS)
        regime_cash_floor = float(regime_result.cash_floor)

        cash_ratio = max(drl_cash, regime_cash_floor)
        if cash_ratio > drl_cash and drl_cash < 1.0:
            scale = (1.0 - cash_ratio) / (1.0 - drl_cash)
            weights = {k: v * scale for k, v in weights.items()}
        cash_ratio = max(0.0, min(1.0, cash_ratio))

        rationale = (
            f"Portfolio is upstream FinRL-Trading's own top-{int(TOP_QUANTILE*100)}% "
            f"ML-selected subset of a {n}-name scoped NASDAQ universe "
            f"({', '.join(selected)}), allocated by a real {MODEL_NAME.upper()} policy "
            f"(upstream FinRL's own DRLAgent wrapping stable_baselines3.A2C, trained "
            f"live for {TOTAL_TIMESTEPS} timesteps on real yfinance history through "
            f"{date}). Upstream's own slow-regime detector "
            f"(adaptive_rotation.market_regime, real weekly ^GSPC/^VIX data) reports "
            f"'{regime_result.state.value}' (risk_score={regime_result.signals.risk_score}), "
            f"contributing a {regime_cash_floor:.0%} cash floor overlay on top of the "
            f"DRL policy's own {drl_cash:.1%} cash allocation. "
            + (
                f"{len(overlap)} of the caller-requested tickers ({', '.join(overlap)}) "
                f"are in the ML-selected set."
                if overlap else
                "None of the caller-requested tickers were in the ML-selected top-25% "
                "set this cycle; the full ML-selected set is used instead (see "
                "adapters/finrl_x_adapter.py header, 'Q4 universe')."
            )
        )

        result = Q4Portfolio(
            weights=weights,
            cash_ratio=cash_ratio,
            rationale=rationale,
            regime=regime_label,
            rebalance_freq="DAILY",
            adapter=self.name,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )
        _DRL_CACHE[cache_key] = result
        return result

    # ------------------------------------------------------------------
    # Smoke test — real q3 + q4 calls, not stubs
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        q3 = self.q3_signal("AAPL", "2024-01-15")
        checks["q3_returns_Q3Signal"] = q3 is not None
        if q3 is not None:
            checks["q3_direction_valid"] = q3.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["q3_strength_in_range"] = 0.0 <= q3.strength <= 1.0

        q4 = self.q4_portfolio(["AAPL", "MSFT", "NVDA"], "2024-01-15")
        checks["q4_returns_Q4Portfolio"] = q4 is not None
        if q4 is not None:
            w_sum = sum(q4.weights.values())
            checks["q4_weights_nonnegative"] = all(v >= 0.0 for v in q4.weights.values())
            checks["q4_weights_sum_le_1"] = w_sum <= 1.0 + 1e-6
            checks["q4_cash_ratio_in_range"] = 0.0 <= q4.cash_ratio <= 1.0

        return checks
