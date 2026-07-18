"""
adapters/finrl_x_adapter.py — wraps github.com/AI4Finance-Foundation/FinRL-Trading
(Q2 real rule-based regime state, Q3 ML-factor stock-selection signal, Q4 DRL
portfolio allocation with regime-aware cash overlay).

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
    python CONTRACT/adapter_runner.py --adapter adapters/finrl_x_adapter.py ...

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
  code. Fix applied entirely in this adapter's own process, around the
  `run_bucket()` call only: temporarily restrict this process's own CPU
  affinity to a single core (`os.sched_setaffinity(0, {0})`) for the
  duration of that one call, then restore the original affinity
  immediately after. This changes nothing about upstream's modeling logic
  or results (still the same 6-model competition, same Stacking ensemble,
  same feature importances) — it only forces those calls to execute
  sequentially rather than in parallel, and only for the few seconds
  `run_bucket()` runs; DRL training afterwards runs with this process's
  normal, unrestricted affinity. `lightgbm` was also left out of the conda
  env for the same reason (upstream's own `build_models()` already treats
  it as optional via `try/except ImportError`), rather than fighting the
  segfault twice.

============================================================================
Schema v2.0.0 migration notes (this file was originally written against a
v1 five-question contract; this is a structural v1 -> v2 migration, not a
rename — see PROJECT_SCHEMA_AUDIT.md §4.3/§5/§7/§8 for the audit findings
this migration implements)
============================================================================
  - **Q2 ADDED (recovered field-semantics fix, not a new capability)**: v1
    folded upstream's real rule-based regime detector
    (`adaptive_rotation.market_regime.detect_slow_regime()` — real
    `RISK_ON`/`NEUTRAL`/`RISK_OFF` state + `risk_score` + `cash_floor`,
    fed real weekly `^GSPC`/`^VIX` closes) into the old Q4 schema's
    `regime` field. v2's `Q4Policy` has no `regime` field at all by design
    (see `CONTRACT/schemas.py::Q4Policy` docstring: "Market regime is
    deliberately not a field here — it lives on Q2 as an open
    StateEstimate"). This migration adds `q2_state()`, calling the exact
    same real `detect_slow_regime()` the Q4 path already calls (via the
    shared `_get_regime()` cache — never computed twice), and returns its
    real `state.value` (`"risk_on"`/`"neutral"`/`"risk_off"`, used verbatim
    as `value_category` — no lossy remapping onto an invented BULL/BEAR/
    SIDEWAYS enum, since v2's `StateEstimate.dimension` is open-vocabulary)
    plus the real integer `risk_score` (0-3) as `value_numeric`. The same
    real `cash_floor` this produces still feeds Q4's cash overlay (see
    below) — Q2 and Q4 read one real computation, not two.
  - **Q3 `values`/`expected_returns`**: upstream's real
    `predicted_return` per ticker (a genuine out-of-sample model forecast
    of `log(next_quarter_close/current_quarter_close)`, not a historical
    correlation — confirmed by reading `run_bucket()`'s own training
    target `y_return`) is used directly for both `values` and
    `expected_returns`. `direction`/`strength` (singular fields in v2,
    unlike a per-ticker triple) are only populated when exactly one target
    ticker is requested and in-scope, using the same top/bottom-25%-based
    convention as before; for multi-ticker/cross-sectional requests they
    are left `None` rather than forcing an arbitrary single label onto a
    ranking that spans many assets — a judgment call, not an upstream
    limitation. `evidence` is upstream's own real per-run
    `importance_records` (feature/importance/model/rank), never hardcoded.
  - **Q4 `generation_window`**: now a required, harness-supplied
    `TimeWindow` parameter (same fix as `adapters/finrl_adapter.py`'s own
    migration) — the adapter no longer computes its own
    `fetch_start = date - HISTORY_DAYS` internally. `generation_window.
    start`/`.end` are used directly as the real DRL price-fetch/training
    range (`_train_and_allocate()`), then echoed back unchanged in the
    returned `Q4Policy.generation_window`.
  - **Q4 `universe_policy.mode="dynamic"`**: the real ML-selected top-25%
    subset of the scoped universe genuinely varies by call (it depends on
    the live-fetched fundamentals ranking), unlike plain FinRL's fixed
    caller-supplied ticker list — `"dynamic"`, not `"fixed"`, is the
    honest value here.
  - **Q4 `constraints`**: `long_only=True` is code-verified (the DRL
    policy's own softmax weights are `max(0.0, ...)`-clipped before any
    regime adjustment, and the regime cash-floor overlay only ever scales
    the remaining weights down by a `[0,1]` factor — never negative).
    `net_exposure_min=net_exposure_max=1.0` reflects that the policy is
    always fully invested (DRL weights + `CASH` sum to 1 by construction),
    with `CASH` able to be non-zero whenever the real regime cash floor
    exceeds the DRL policy's own (usually ~0) cash allocation — unlike
    plain FinRL, which is always ~fully invested with ~0 cash. This is a
    materially different, correct value, not copied from
    `finrl_adapter.py`.
  - **Known limitation preserved, not silently fixed**: this adapter's
    fundamentals data (yfinance `quarterly_financials`/
    `quarterly_balance_sheet`) is NOT point-in-time — it always returns
    the latest available reported quarters regardless of the requested
    `context.as_of`/`data_cutoff`, unlike upstream's own FMP-backed
    point-in-time SQLite database (avoided here — see security section).
    This is documented honestly in `adapter_notes` on every result, not
    silently patched over. Price-based inputs (Q4's DRL training window,
    Q2's regime detector) ARE correctly point-in-time.

============================================================================
Design notes (translation choices made by this adapter, not upstream) —
carried over from the original build, still accurate post-migration
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
    (`FEATURE_COLS` below), passed as the `feature_cols` *argument* to
    upstream's own `run_bucket(bucket, bdf, feature_cols, val_cutoff,
    val_quarters)` (a real parameter of that function, not a hardcoded
    constant this adapter had to bypass). PE/PS/PB are computed as
    `price / (4 × quarterly_metric)` (crude quarterly-to-annualized
    conversion) rather than upstream's true TTM/annual-filing figures — a
    documented simplification, not upstream logic reimplemented (the
    *model* that consumes these features, and the ranking/ensemble/
    stacking logic around them, is still 100% upstream's own code).
    Missing values are filled with the column's global median and ±inf
    clipped to NaN before filling — matching the data-hygiene step
    upstream's own `ML_STOCK_SELECTION.md` documents.
  - **Fiscal-quarter calendar alignment (adapter-side glue, not upstream
    logic)**: yfinance reports each company's own fiscal quarter-end dates,
    whereas upstream's own point-in-time system assumes a single shared
    `datadate` grid. This adapter snaps each ticker's actual fiscal
    quarter-end to the *nearest* standard calendar quarter-end
    (03-31/06-30/09-30/12-31) before calling `run_bucket()` — pure date
    bucketing, not a change to the ranking/selection logic itself.
  - **`val_cutoff`/inference window**: this adapter sets `val_cutoff` to
    the third-most-recent aligned quarter (`val_quarters=1`), so
    `infer_dates` covers the two most recent aligned quarters combined —
    reproducing upstream's own documented "mixed-vintage" idea using
    upstream's own `run_bucket()` unmodified, then de-duplicating to one
    row per ticker (keeping the latest available quarter).
  - **Q4 DRL training**: same real-upstream-FinRL building blocks and same
    "train live, scoped down" budget `adapters/finrl_adapter.py` already
    validated this session (`FeatureEngineer`, `YahooDownloader`-equivalent
    yfinance fetch, `StockPortfolioEnv`, `DRLAgent` wrapping real
    `stable_baselines3.A2C`, `TOTAL_TIMESTEPS=3000`,
    `COV_LOOKBACK_DAYS=60`) rather than `rl_model.py`'s own
    `train_a2c`/`train_ppo`/`train_ddpg` helpers, whose hardcoded
    `total_timesteps` (50000/80000/50000) have no override parameter and
    would blow well past the harness's timeouts. Using upstream FinRL's own
    `DRLAgent`/`StockPortfolioEnv` API directly (the same API `rl_model.py`
    itself calls) with a documented, reduced timestep budget is the same
    category of scope reduction `finrl_adapter.py` already used — not a
    reimplementation of the reward/environment/policy logic itself (100%
    upstream `stable_baselines3`/`StockPortfolioEnv`).
  - **Q4 universe**: the DRL allocator always trades upstream's own
    ML-selected top-25% subset of `NASDAQ_UNIVERSE` (computed via the same
    cached `run_bucket()` call Q3 uses) — reflecting the target
    description's fixed 2-stage pipeline ("selects the top 25% of NASDAQ
    stocks using ML factors, then allocates via DRL"), not an arbitrary
    caller-supplied ticker basket. `context.targets`/`context.universe` are
    intersected with the ML-selected set only as an informational overlap
    check logged into `explanation`; if none of the caller's targets made
    the cut, the full ML-selected set is used regardless.
  - Per-(universe) and per-(selected tickers, generation_window) in-memory
    caching: the ML panel/ranking (fundamentals-based, doesn't vary with
    `as_of` per the caveat above) is fetched and ranked once per process;
    DRL training is cached per (selected-ticker-set, generation_window)
    (harness callers may invoke a q* method directly AND again via
    `adapter.run()` with identical arguments).
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
    DecisionPolicy,
    Direction,
    EvidenceItem,
    ObservationPolicy,
    OutputScope,
    PolicyType,
    PortfolioConstraints,
    Q2State,
    Q3Signal,
    Q4Policy,
    QueryContext,
    StateEstimate,
    TimeWindow,
    UniversePolicy,
    UpdateMode,
    UpdatePolicy,
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
MODEL_NAME = "a2c"
INITIAL_AMOUNT = 1_000_000
HMAX = 100
TRANSACTION_COST_PCT = 0.001
REWARD_SCALING = 1e-1

KNOWN_LIMITATIONS_NOTE = (
    "Known limitation (yfinance fundamentals are NOT point-in-time): Q3's predicted_return "
    "and Q4's ML-selected universe are both driven by yfinance quarterly_financials/"
    "quarterly_balance_sheet, which always return the latest available reported quarters as "
    "of process run time, regardless of context.as_of/data_cutoff. Upstream's own point-in-time "
    "FMP-backed SQLite database is not used here (avoided to keep this adapter free of a paid "
    "API key — see module header). Price-based inputs (Q4's DRL training window over "
    "generation_window, Q2's regime detector as of data_cutoff) ARE correctly point-in-time."
)

_ML_CACHE: Optional[Tuple[pd.DataFrame, List[dict], List[dict]]] = None
_REGIME_CACHE: Dict[str, object] = {}
_DRL_CACHE: Dict[Tuple[tuple, str, str], Dict[str, float]] = {}


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
    ^GSPC/^VIX closes and upstream's own shipped YAML config. Shared by
    both q2_state() and q4_policy() so the real detect_slow_regime() call
    happens once per (process, date), never duplicated."""
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


def _regime_native_dict(regime_result) -> dict:
    """Faithful, JSON-safe representation of upstream's real SlowRegimeResult
    dataclass (state/signals/group_cap/cash_floor/is_persistent/metadata)."""
    s = regime_result.signals
    return {
        "state": regime_result.state.value,
        "group_cap": float(regime_result.group_cap),
        "cash_floor": float(regime_result.cash_floor),
        "is_persistent": bool(regime_result.is_persistent),
        "signals": {
            "trend_deterioration": bool(s.trend_deterioration),
            "drawdown_stress": bool(s.drawdown_stress),
            "volatility_stress": bool(s.volatility_stress),
            "risk_score": int(s.risk_score),
            "spx_price": float(s.spx_price),
            "spx_ma_26w": float(s.spx_ma_26w),
            "spx_drawdown_13w": float(s.spx_drawdown_13w),
            "vix_z_score": float(s.vix_z_score),
        },
    }


def _ranking_native_records(ranking: pd.DataFrame) -> List[dict]:
    cols = ["tic", "datadate", "predicted_return", "best_model", "rank_position"]
    out = []
    for _, r in ranking[cols].iterrows():
        out.append({
            "tic": str(r["tic"]),
            "datadate": str(r["datadate"]),
            "predicted_return": float(r["predicted_return"]),
            "best_model": str(r["best_model"]),
            "rank_position": int(r["rank_position"]),
        })
    return out


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
            f"{COV_LOOKBACK_DAYS}-day covariance lookback — widen generation_window."
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


def _train_and_allocate(tickers: List[str], fetch_start: str, fetch_end: str) -> Dict[str, float]:
    """Real upstream FinRL DRL training (StockPortfolioEnv + DRLAgent
    wrapping real stable_baselines3.A2C), scoped down per header "Q4 DRL
    training". [fetch_start, fetch_end] is the harness-supplied
    generation_window, used directly as the real price-fetch/training
    range (v2: no adapter-computed window). Returns the final-day
    softmax-normalized weights."""
    from finrl.agents.stablebaselines3.models import DRLAgent
    from finrl.meta.preprocessor.preprocessors import data_split

    # yfinance's own fetch end is exclusive; widen by one day so the last
    # calendar day of the harness-supplied window is actually included in
    # the real price fetch. Does not change the recorded generation_window
    # itself (see q4_policy) — only this network call's end-exclusive quirk.
    fetch_end_inclusive = (pd.Timestamp(fetch_end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    df = _fetch_and_engineer(tickers, fetch_start, fetch_end_inclusive)
    train_df = data_split(df, fetch_start, fetch_end_inclusive)

    stock_dim = len(tickers)
    from finrl import config
    from finrl.meta.env_portfolio_allocation.env_portfolio import StockPortfolioEnv

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
    questions_answered = ["Q2", "Q3", "Q4"]
    upstream_repo = "https://github.com/AI4Finance-Foundation/FinRL-Trading"
    requires_env = "finrl_x_real"

    def __init__(self):
        super().__init__()
        self._last_native: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Q2 — real rule-based market-regime state (recovered from v1's Q4
    # field-semantics mismatch — see module header)
    # ------------------------------------------------------------------
    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        asof_date = context.data_cutoff or context.as_of
        regime_result = _get_regime(asof_date)
        signals = regime_result.signals

        evidence = [
            EvidenceItem(
                kind="model_feature", value=f"trend_deterioration={signals.trend_deterioration}",
                source="adaptive_rotation.market_regime.compute_slow_regime_signals",
                reference="SPX vs 26-week moving average",
            ),
            EvidenceItem(
                kind="model_feature", value=f"drawdown_stress={signals.drawdown_stress}",
                source="adaptive_rotation.market_regime.compute_slow_regime_signals",
                reference="13-week SPX drawdown >= 10%",
            ),
            EvidenceItem(
                kind="model_feature", value=f"volatility_stress={signals.volatility_stress}",
                source="adaptive_rotation.market_regime.compute_slow_regime_signals",
                reference="3-year robust VIX z-score >= 3.0",
            ),
        ]

        state = StateEstimate(
            dimension="market_regime",
            value_category=regime_result.state.value,
            value_numeric=float(signals.risk_score),
            scale="risk_score in {0,1,2,3} (0->risk_on, 1->neutral, 2-3->risk_off); "
                  "value_category is upstream's own tri-level label",
            observation_window="26-week SPX trend MA / 13-week SPX drawdown / 3-year robust VIX z-score",
            confidence=None,
            evidence=evidence,
        )

        # Capability recovery: cash_floor was previously only mentioned in
        # this method's prose `explanation` and in Q4's own explanation text
        # (adaptive_rotation.market_regime.detect_slow_regime's real
        # `RegimeResult.cash_floor`) — never a structured, queryable value.
        # It's a real, regime-derived recommendation (not a policy decision
        # itself, since the actual portfolio cash allocation is Q4's to make),
        # so it belongs as its own Q2 dimension alongside market_regime.
        cash_floor_state = StateEstimate(
            dimension="regime_recommended_cash_floor",
            value_numeric=float(regime_result.cash_floor),
            scale="[0,1] fraction of portfolio recommended to hold as cash, per this regime",
            evidence=[
                EvidenceItem(
                    kind="model_feature",
                    value=f"cash_floor={regime_result.cash_floor:.4f} for regime={regime_result.state.value}",
                    source="adaptive_rotation.market_regime.detect_slow_regime (RegimeResult.cash_floor)",
                    reference="same real regime computation that feeds Q4's cash-floor overlay (see q4_policy)",
                )
            ],
        )

        explanation = (
            f"Upstream FinRL-Trading's own rule-based slow-regime detector "
            f"(adaptive_rotation.market_regime.detect_slow_regime, real weekly ^GSPC/^VIX "
            f"closes as of {asof_date}) reports '{regime_result.state.value}' "
            f"(risk_score={signals.risk_score}/3, cash_floor={regime_result.cash_floor:.0%}, "
            f"also reported structurally as its own StateEstimate below). "
            f"This is the same real regime computation that feeds the cash-floor overlay on "
            f"this adapter's Q4 policy (see q4_policy) — v1 folded this into Q4's own `regime` "
            f"field; v2 routes it here since market_regime is a state of the world, not a "
            f"policy property (see CONTRACT/schemas.py Q4Policy docstring)."
        )

        self._last_native["q2"] = _regime_native_dict(regime_result)

        return Q2State(context=context, states=[state, cash_floor_state], explanation=explanation)

    # ------------------------------------------------------------------
    # Q3 — ML-factor stock-selection signal
    # ------------------------------------------------------------------
    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        ranking, model_results, importance_records = _get_ml_selection()
        n = len(ranking)
        top_cut = max(1, round(TOP_QUANTILE * n))
        bottom_cut = n - top_cut
        universe_tics = set(ranking["tic"])

        requested = list(context.targets or context.universe or [])
        targets = [t for t in requested if t in universe_tics]
        out_of_scope = [t for t in requested if t not in universe_tics]
        if not targets:
            # No requested ticker is in this adapter's scoped universe --
            # fall back to the full scoped ranking rather than fabricating
            # a value for a ticker with no real model output.
            targets = ranking["tic"].tolist()

        values: Dict[str, float] = {}
        expected_returns: Dict[str, float] = {}
        for tic in targets:
            row = ranking[ranking.tic == tic]
            if row.empty:
                continue
            pred = float(row["predicted_return"].iloc[0])
            values[tic] = pred
            expected_returns[tic] = pred

        if not values:
            return None

        direction = None
        strength = None
        if len(targets) == 1 and targets[0] in universe_tics:
            row = ranking[ranking.tic == targets[0]]
            rank = int(row["rank_position"].iloc[0])
            pct = (n - rank) / (n - 1) if n > 1 else 0.5
            is_top = rank <= top_cut
            is_bottom = rank > bottom_cut
            direction = Direction.LONG if is_top else Direction.SHORT if is_bottom else Direction.NEUTRAL
            strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))

        best_model = str(ranking.iloc[0]["best_model"]) if n else None
        best_importances = sorted(
            [r for r in importance_records if r.get("model") == best_model and r.get("is_best")],
            key=lambda r: r["rank"],
        )[:3] if best_model else []
        evidence = [
            EvidenceItem(
                kind="model_feature",
                value=f"{r['feature']} (importance={r['importance']:.3f})",
                source=f"ml_bucket_selection.run_bucket importance_records (model={r['model']})",
            )
            for r in best_importances
        ] or None

        explanation = (
            f"predicted_return is upstream FinRL-Trading's own out-of-sample regression "
            f"prediction (best_model={best_model} of a real RF/XGBoost/HistGBM/ExtraTrees/"
            f"Ridge/Stacking competition, ml_bucket_selection.run_bucket()) of "
            f"log(next_quarter_close / current_quarter_close) over a scoped {n}-name "
            f"NASDAQ-style universe. Fundamentals inputs are yfinance's latest-available "
            f"quarterly statements, NOT point-in-time as of context.as_of/data_cutoff (see "
            f"adapter_notes — a known limitation of avoiding the paid FMP point-in-time "
            f"database)."
            + (f" Requested target(s) outside this adapter's scoped universe: {out_of_scope}." if out_of_scope else "")
        )

        self._last_native["q3"] = {
            "ranking": _ranking_native_records(ranking),
            "model_results": model_results,
            "importance_records": importance_records,
        }

        return Q3Signal(
            context=context,
            signal_semantics="predicted_return (real out-of-sample model forecast of next-quarter log price return)",
            values=values,
            score_scale="log return, unitless",
            direction=direction,
            strength=strength,
            expected_returns=expected_returns,
            factor_expression=None,
            confidence=None,
            evidence=evidence,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Q4 — DRL portfolio allocation over the ML-selected top-25% subset,
    # with a real regime-based cash-floor overlay
    # ------------------------------------------------------------------
    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        ranking, _, _ = _get_ml_selection()
        n = len(ranking)
        top_cut = max(2, round(TOP_QUANTILE * n))
        selected = ranking.head(top_cut)["tic"].tolist()

        cache_key = (tuple(sorted(selected)), generation_window.start, generation_window.end)
        if cache_key in _DRL_CACHE:
            weights = dict(_DRL_CACHE[cache_key])
        else:
            weights = _train_and_allocate(selected, generation_window.start, generation_window.end)
            _DRL_CACHE[cache_key] = dict(weights)

        drl_cash = max(0.0, 1.0 - sum(weights.values()))

        asof_date = context.data_cutoff or context.as_of
        regime_result = _get_regime(asof_date)
        regime_cash_floor = float(regime_result.cash_floor)

        cash_ratio = max(drl_cash, regime_cash_floor)
        if cash_ratio > drl_cash and drl_cash < 1.0:
            scale = (1.0 - cash_ratio) / (1.0 - drl_cash)
            weights = {k: v * scale for k, v in weights.items()}

        initial_weights = {k: v for k, v in weights.items() if v > 0.0}
        non_cash_total = sum(initial_weights.values())
        initial_weights["CASH"] = max(0.0, 1.0 - non_cash_total)

        requested = set(context.targets or context.universe or [])
        overlap = sorted(requested & set(selected))

        explanation = (
            f"Universe is upstream FinRL-Trading's own top-{int(TOP_QUANTILE*100)}% ML-selected "
            f"subset of a {n}-name scoped NASDAQ-style universe ({', '.join(selected)}), from the "
            f"same real ml_bucket_selection.run_bucket() ranking Q3 uses. Weights are the "
            f"final-day allocation from a real {MODEL_NAME.upper()} policy (upstream FinRL's own "
            f"DRLAgent wrapping stable_baselines3.A2C), trained live for {TOTAL_TIMESTEPS} "
            f"timesteps on real yfinance price history over the harness-supplied generation "
            f"window [{generation_window.start}, {generation_window.end}]. Upstream's own "
            f"rule-based slow-regime detector (adaptive_rotation.market_regime, real weekly "
            f"^GSPC/^VIX data as of {asof_date} — see q2_state for the same real regime output) "
            f"reports '{regime_result.state.value}' (risk_score={regime_result.signals.risk_score}), "
            f"contributing a {regime_cash_floor:.0%} cash floor blended with the DRL policy's own "
            f"{drl_cash:.1%} cash allocation via cash_ratio=max(drl_cash, regime_cash_floor), "
            f"rescaling the remaining weights down proportionally. "
            + (
                f"{len(overlap)} of the caller-requested target(s)/universe ({', '.join(overlap)}) "
                f"are in the ML-selected set."
                if overlap else
                "None of the caller-requested targets/universe were in this cycle's ML-selected "
                "top-25% set; the full ML-selected set is used regardless (see module header, "
                "'Q4 universe')."
            )
        )

        universe_policy = UniversePolicy(
            mode="dynamic",
            max_assets=top_cut,
            selection_frequency="varies with underlying fundamentals cadence (quarterly)",
            selector_description=(
                "Top-25% of a scoped NASDAQ-style universe by predicted_return, real ML "
                "ensemble ranking via upstream ml_bucket_selection.run_bucket() (same "
                "computation as this adapter's Q3 signal)."
            ),
        )

        observation_policy = ObservationPolicy(
            lookback_window=f"{COV_LOOKBACK_DAYS} trading days rolling covariance over the harness-supplied generation window",
            data_sources=[
                "yfinance OHLCV via upstream FinRL YahooDownloader",
                "yfinance ^GSPC/^VIX weekly closes (regime detector)",
            ],
            observation_description=(
                "Upstream FinRL FeatureEngineer technical indicators + adapter-side rolling "
                "return-covariance matrix (StockPortfolioEnv's required cov_list input)."
            ),
        )

        decision_policy = DecisionPolicy(
            decision_rule=(
                "Real A2C DRL policy (stable_baselines3 via upstream FinRL DRLAgent/"
                "StockPortfolioEnv) trained over generation_window; final-day softmax "
                "portfolio weights over the ML-selected top-25% universe, cash-floor-adjusted "
                "by upstream's own rule-based regime detector."
            ),
            output_semantics="target portfolio weights (non-negative, sum to 1 including CASH)",
        )

        update_policy = UpdatePolicy(
            mode=UpdateMode.NONE,
            update_description=(
                "Policy is retrained from scratch each time q4_policy() is called over a given "
                "generation_window; no online learning occurs after generation."
            ),
        )

        constraints = PortfolioConstraints(
            long_only=True,
            net_exposure_min=1.0,
            net_exposure_max=1.0,
        )

        self._last_native["q4"] = {
            "selected_universe": selected,
            "drl_weights_after_regime_overlay": weights,
            "drl_cash_pre_regime": drl_cash,
            "regime": _regime_native_dict(regime_result),
            "generation_window": {"start": generation_window.start, "end": generation_window.end},
        }

        return Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            initial_weights=initial_weights,
            artifact=None,
            decisions=None,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # run() override — attach a faithful native_output (captured as a side
    # effect of the real q2/q3/q4 calls BaseAdapter.run() makes) and the
    # known-limitations note, matching this session's established v2
    # convention (see adapters/alphagen_adapter.py).
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
        self._last_native = {}
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native:
            updates["native_output"] = self._last_native
        if adapter_notes is None:
            updates["adapter_notes"] = KNOWN_LIMITATIONS_NOTE
        if updates:
            result = result.model_copy(update=updates)
        return result

    # ------------------------------------------------------------------
    # Smoke test — real q2 + q3 + q4 calls, not stubs
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION,
            targets=["AAPL"],
        )

        q2 = self.q2_state(context)
        checks["q2_returns_Q2State"] = q2 is not None
        if q2 is not None:
            checks["q2_context_echoed_unchanged"] = q2.context == context
            checks["q2_has_market_regime_dimension"] = any(s.dimension == "market_regime" for s in q2.states)
            cash_floor_states = [s for s in q2.states if s.dimension == "regime_recommended_cash_floor"]
            checks["q2_has_cash_floor_dimension"] = len(cash_floor_states) == 1
            if cash_floor_states:
                checks["q2_cash_floor_in_range"] = 0.0 <= cash_floor_states[0].value_numeric <= 1.0

        q3 = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = q3 is not None
        if q3 is not None:
            checks["q3_context_echoed_unchanged"] = q3.context == context
            checks["q3_values_nonempty"] = len(q3.values) > 0

        generation_window = TimeWindow(start="2022-07-01", end="2024-01-15")
        q4 = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = q4 is not None
        if q4 is not None:
            checks["q4_context_echoed_unchanged"] = q4.context == context
            checks["q4_generation_window_echoed_unchanged"] = q4.generation_window == generation_window
            w = q4.initial_weights or {}
            checks["q4_weights_nonnegative"] = all(v >= -1e-9 for v in w.values())
            checks["q4_weights_sum_to_1"] = abs(sum(w.values()) - 1.0) < 1e-6

        return checks
