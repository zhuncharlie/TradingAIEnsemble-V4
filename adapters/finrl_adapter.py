"""
adapters/finrl_adapter.py — wraps github.com/AI4Finance-Foundation/FinRL
(Q4 portfolio allocation, Q5 backtest performance).

Repo verification (per CLAUDE.md's own "Registered Adapters" table, which
already names this exact repo/questions for finrl_adapter.py):
  - Confirmed via WebSearch + `gh api repos/AI4Finance-Foundation/FinRL`
    substitute (no `gh` binary in this sandbox, used the GitHub REST-backed
    search instead) that the org/repo is real and actively maintained.
  - README (fetched via WebFetch) confirms: DRL framework for algorithmic
    stock trading, "train-test-trade" pipeline, PPO/A2C/DDPG/TD3/SAC via
    Stable-Baselines3 (+ ElegantRL/RLlib), 14+ data providers including
    Yahoo Finance (no credentials) and Alpaca (credentials only if you
    choose that data source — this adapter does not), a dedicated
    portfolio-allocation application/environment, DOW-30-style
    benchmarking. Matches the brief exactly.
  - setup.py: `python_requires=">=3.7"`, classifiers through 3.12.
    requirements.txt: yfinance, stable-baselines3[extra], gymnasium,
    stockstats, scikit-learn, torch (via sb3), no brokerage-only deps in
    the base install.

Security screening (file-tree scan + eval/exec/shell=True/os.system grep +
username/password/login/api_key/secret_key grep across the cloned repo,
same checks used for the FinGPT/DeepAlpha adapters this session):
  - File tree (`finrl/agents`, `finrl/applications`, `finrl/meta/env_*`,
    `finrl/meta/data_processors`, `finrl/meta/preprocessor`, `unit_tests`,
    `examples`, `docs`) is entirely on-topic for a DRL trading framework —
    no unrelated subtree like FinGPT's `finogrid/` crypto-payments merge.
  - `os.system("rm -f ...")` in `finrl/meta/data_processors/func.py` is a
    scratch-file cleanup helper, not a shell-injection/credential risk.
  - `username`/`password`/`login`/`api_key`/`secret_key` only appear in
    *alternative, optional* data-source processors this adapter never
    imports or calls: `processor_joinquant.py` (Chinese JoinQuant acct),
    `processor_sinopac.py` / `preprocessor/shioajidownloader.py` (Taiwan
    Sinopac/Shioaji brokerage login), `processor_alpaca.py` (Alpaca paper-
    trading keys), `processor_wrds.py` (paid WRDS academic subscription).
    This adapter's data path is exclusively
    `finrl.meta.preprocessor.yahoodownloader.YahooDownloader`, which wraps
    `yfinance` — free, public OHLCV data, no account/credentials of any
    kind. No live brokerage/exchange credentials or real money are used
    anywhere in this adapter, satisfying the brief's stop-condition check.

Patch (patches/FinRL.diff, applied to adapters/vendor/FinRL/finrl/__init__.py):
    The unpatched `finrl/__init__.py` eagerly does
    `from finrl.trade import trade` / `from finrl.train import train` /
    `from finrl.test import test` at package-import time. That import chain
    pulls in `AlpacaPaperTrading` (needs the `alpaca`/`alpaca_trade_api`
    live-brokerage SDKs) and `finrl.meta.data_processor.DataProcessor`
    (which unconditionally imports `WrdsProcessor`, requiring the paid WRDS
    academic database package just to *import*, not even to use). None of
    this adapter's calls need `finrl.train`/`finrl.test`/`finrl.trade` —
    it calls `FeatureEngineer`, `YahooDownloader`, `StockPortfolioEnv`, and
    `DRLAgent` directly, which is the same set of building blocks FinRL's
    own portfolio-allocation tutorials use. Wrapped those three imports in
    `try/except ImportError: pass` so `import finrl` (and any submodule
    import that doesn't specifically need test/trade/train) no longer
    requires those optional brokerage/paid-data-vendor SDKs to be
    installed. Verified (by temporarily blocking those imports via a
    `sys.meta_path` finder) that none of `FeatureEngineer`/
    `YahooDownloader`/`StockPortfolioEnv`/`DRLAgent`/`config` actually need
    them once the patch is in place.

Environment setup (one-time, outside this file):
    conda create -n finrl_real python=3.10
    conda activate finrl_real
    # torch/stable-baselines3/gymnasium installed fine via pip in this env
    # (no cmake/Rust build issues hit for this stack, unlike xgboost/
    # lightgbm/pyarrow earlier this session).
    pip install stable-baselines3[extra] gymnasium stockstats scikit-learn \
                pandas numpy matplotlib torch
    pip install "yfinance==0.2.66"
    # PIN yfinance to 0.2.66, NOT latest: FinRL's own
    # YahooDownloader.fetch_data() calls `yf.download(tic, ..., proxy=proxy)`
    # unconditionally (proxy=None by default). yfinance>=1.0 (tested 1.4.1)
    # removed the `proxy` kwarg from `download()` entirely (moved to
    # `yf.set_config(proxy=...)`), raising
    # `TypeError: download() got an unexpected keyword argument 'proxy'`
    # on every call. 0.2.66 (last 0.2.x release) still accepts it — no
    # vendor source was patched for this, just a version pin, same
    # philosophy as FinGPT's transformers/peft/accelerate pin this session.
    git clone --depth 1 https://github.com/AI4Finance-Foundation/FinRL.git \
        adapters/vendor/FinRL
    # then apply patches/FinRL.diff to adapters/vendor/FinRL/finrl/__init__.py

Run the harness with that env active:
    conda activate finrl_real
    python CONTRACT/test_harness.py --adapter adapters/finrl_adapter.py

Design notes (translation choices made by this adapter, not upstream):
  - No pretrained weights shipped or used: like DeepAlpha, FinRL's own repo
    ships no trained model checkpoints (its README/tutorials assume you run
    `finrl/train.py`-style scripts yourself against whatever ticker/date
    range you want). This is not a scope reduction forced by missing
    artifacts — it is FinRL's normal, documented usage pattern — but the
    training budget below IS a deliberate scope reduction from "full paper-
    scale training" to "minimum viable, train live", per the same
    substitution DeepAlpha used:
      - Tickers: whatever the caller passes (harness uses AAPL/MSFT/NVDA),
        not the full DOW-30 upstream's own tutorials train on.
      - `TOTAL_TIMESTEPS = 3000` (vs. tens/hundreds of thousands in
        upstream's own published benchmarks) using upstream's own default
        `A2C_PARAMS` from `finrl.config` (`n_steps=5`, unmodified).
        Algorithm: A2C (fastest of FinRL's five supported SB3 algorithms;
        real `stable_baselines3.A2C` via upstream's own `DRLAgent`, not
        reimplemented).
      - Real yfinance OHLCV data (via upstream's own `YahooDownloader`),
        ~1.5 years of history per call, not upstream's own curated
        DOW-30-since-2009-style datasets.
      - End-to-end (fetch + feature-engineer + train 3000 steps + rollout)
        measured ~15-25s for 3 tickers in this environment — well inside
        the harness's smoke_test (<300s) and run() (<600s) budgets.
  - Data-prep glue code (adapter-side, not upstream logic): FinRL's own
    `StockPortfolioEnv` requires a `cov_list` column (rolling covariance
    matrix of returns per date) that isn't produced by upstream's own
    `FeatureEngineer.preprocess_data()` — it's data plumbing shown in
    FinRL's own public tutorial notebooks (in the separate FinRL-Tutorials
    repo, not this repo's checked-in code) rather than a library function.
    This adapter reproduces that same rolling-covariance construction
    (pandas `.pivot_table` + `.pct_change().cov()` over a lookback window)
    as required input plumbing for upstream's own environment class — the
    portfolio-allocation decision logic itself (the DRL policy, the reward,
    the softmax weight normalization) is 100% upstream's own
    `StockPortfolioEnv`/`DRLAgent` code, never reimplemented here. This is
    the same kind of "adapter must assemble upstream's own expected input
    shape" glue DeepAlpha needed (excluding raw OHLCV columns before
    training).
    `COV_LOOKBACK_DAYS = 60` trading days, reduced from the 252 (~1
    calendar year) used in FinRL's own published tutorial, purely to keep
    the required history window (and therefore the yfinance fetch) small
    enough to comfortably clear the harness's time budget with room to
    spare; documented here as a scope reduction, not a bug.
  - Q4 `weights` / `cash_ratio`: trains upstream's own A2C policy on the
    ~1.5y window ending at the requested `date`, then takes the *last row*
    of upstream's own `DRLAgent.DRL_prediction()` → `save_action_memory()`
    output (the model's own softmax-normalized portfolio weights for the
    final day in that window) as the current allocation. Upstream's own
    `StockPortfolioEnv.softmax_normalization()` always yields non-negative
    weights summing to 1.0, so `cash_ratio` is computed as
    `max(0.0, 1.0 - sum(weights))` (effectively 0.0 by construction — this
    policy is always fully invested, never holds cash, matching upstream's
    own environment design) rather than hardcoded.
  - Q4 `regime`: NOT derived from the DRL model (upstream's env doesn't
    label regimes). Adapter-side heuristic over the same real price data
    already fetched: equal-weighted realized return of the requested
    tickers over the trailing 30 trading days — >+2% → BULL, <-2% → BEAR,
    else SIDEWAYS. Documented as a simple auxiliary classification, not a
    model output, exactly like DeepAlpha's Q3 `expected_return` distinction
    between model output and adapter-derived fields.
  - Q5 `total_return`/`sharpe`/`max_drawdown`/`calmar`/`win_rate`/
    `equity_curve`: trains upstream's own A2C policy on the window before
    `start`, then runs upstream's own `DRLAgent.DRL_prediction()` on a
    *fresh, held-out* `StockPortfolioEnv` built only from the
    `[start, end)` test rows (real out-of-sample rollout, not in-sample).
    `equity_curve` is the cumulative product of the `daily_return` series
    upstream's own env returns via `save_asset_memory()` (normalized to
    start at 1.0, per the schema's own field description).
    `sharpe = sqrt(252) * mean(daily_return) / std(daily_return)` is the
    exact annualized-Sharpe formula `StockPortfolioEnv.step()` itself
    already computes and prints internally on the terminal step (see
    `finrl/meta/env_portfolio_allocation/env_portfolio.py`) — recomputed
    here from upstream's own returned `daily_return` series (not a new
    metric formula, not printed/returned by upstream directly, so it has
    to be recomputed from upstream's own output data).
    `max_drawdown` (always ≤0) and `calmar` are standard equity-curve
    arithmetic over that same real, upstream-produced `equity_curve` —
    not upstream logic to begin with (upstream's tutorials use the
    separate `pyfolio` package for these, not vendored into this repo's
    checked-in code), so computed directly here.
  - Q5 `alpha_vs_benchmark`: equal-weight buy-and-hold return over the same
    real `[start, end)` price data (first-vs-last close per ticker,
    equal-weighted) minus the model's `total_return` — pure arithmetic on
    real fetched prices, matching the schema's own
    `benchmark="equal_weight_bnh"` default, not a call into any upstream
    benchmarking code.
  - Per-(tickers,date) and per-(tickers,start,end) in-memory caching: the
    test harness calls each Q method directly AND again via `adapter.run()`
    with identical arguments; without caching this would retrain the DRL
    policy twice per method for the same inputs. Same pattern as
    DeepAlpha's per-ticker cache.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q4Portfolio, Q5Backtest, Regime

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "FinRL"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

COV_LOOKBACK_DAYS = 60          # trading days of rolling-covariance window (reduced from upstream tutorial's 252)
HISTORY_DAYS = 550              # ~1.5 calendar years of history fetched for training windows (pd.DateOffset
                                 # doesn't support fractional years, so this is expressed directly in days)
TOTAL_TIMESTEPS = 3000          # DRL training budget — "train live", not paper-scale
MODEL_NAME = "a2c"              # fastest of FinRL's 5 supported SB3 algorithms
INITIAL_AMOUNT = 1_000_000
HMAX = 100
TRANSACTION_COST_PCT = 0.001
REWARD_SCALING = 1e-1

_Q4_CACHE: Dict[Tuple[tuple, str], "Q4Portfolio"] = {}
_Q5_CACHE: Dict[Tuple[tuple, str, str], "Q5Backtest"] = {}


def _fetch_and_engineer(tickers: List[str], fetch_start: str, fetch_end: str) -> pd.DataFrame:
    """Real yfinance data (upstream's own YahooDownloader) + upstream's own
    FeatureEngineer, plus adapter-side rolling-covariance ('cov_list') glue
    that upstream's own StockPortfolioEnv requires as input (see header)."""
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


def _make_env(df_slice: pd.DataFrame, tickers: List[str]):
    from finrl import config
    from finrl.meta.env_portfolio_allocation.env_portfolio import StockPortfolioEnv

    stock_dim = len(tickers)
    return StockPortfolioEnv(
        df=df_slice,
        hmax=HMAX,
        initial_amount=INITIAL_AMOUNT,
        transaction_cost_pct=TRANSACTION_COST_PCT,
        state_space=stock_dim,
        stock_dim=stock_dim,
        tech_indicator_list=config.INDICATORS,
        action_space=stock_dim,
        reward_scaling=REWARD_SCALING,
    )


def _train_agent(train_df: pd.DataFrame, tickers: List[str]):
    """Real upstream training: upstream's own StockPortfolioEnv + DRLAgent
    (wrapping real stable_baselines3.A2C), upstream's own default A2C_PARAMS."""
    from finrl import config
    from finrl.agents.stablebaselines3.models import DRLAgent

    env_gym = _make_env(train_df, tickers)
    env_vec, _ = env_gym.get_sb_env()
    agent = DRLAgent(env=env_vec)
    model = agent.get_model(MODEL_NAME, model_kwargs=config.A2C_PARAMS, verbose=0)
    trained = DRLAgent.train_model(model=model, tb_log_name=MODEL_NAME, total_timesteps=TOTAL_TIMESTEPS)
    return trained, env_gym


def _equal_weight_bnh_return(df_slice: pd.DataFrame, tickers: List[str]) -> float:
    """Real-price arithmetic benchmark, not upstream model logic."""
    pivot = df_slice.pivot_table(index="date", columns="tic", values="close").sort_index()
    pivot = pivot[[t for t in tickers if t in pivot.columns]]
    per_ticker_return = pivot.iloc[-1] / pivot.iloc[0] - 1.0
    return float(per_ticker_return.mean())


class FinRLAdapter(BaseAdapter):
    name = "finrl"
    questions_answered = ["Q4", "Q5"]
    upstream_repo = "https://github.com/AI4Finance-Foundation/FinRL"
    requires_env = "finrl_real"

    # ------------------------------------------------------------------
    # Q4 — Portfolio allocation
    # ------------------------------------------------------------------
    def q4_portfolio(self, tickers: List[str], date: str, **kwargs) -> Optional[Q4Portfolio]:
        t0 = time.time()
        tickers = list(tickers)
        cache_key = (tuple(sorted(tickers)), date)
        if cache_key in _Q4_CACHE:
            cached = _Q4_CACHE[cache_key]
            cached.latency_sec = time.time() - t0
            return cached

        from finrl.agents.stablebaselines3.models import DRLAgent
        from finrl.meta.preprocessor.preprocessors import data_split

        end_ts = pd.Timestamp(date)
        fetch_start = (end_ts - pd.DateOffset(days=HISTORY_DAYS)).strftime("%Y-%m-%d")
        fetch_end = (end_ts + pd.DateOffset(days=1)).strftime("%Y-%m-%d")  # yfinance end is exclusive

        df = _fetch_and_engineer(tickers, fetch_start, fetch_end)
        # StockPortfolioEnv expects upstream's own data_split() indexing (date
        # factorized into an integer index shared by all tickers on that date)
        # rather than a plain 0..N-1 row index — see DECISIONS_finrl.md.
        train_df = data_split(df, fetch_start, fetch_end)
        trained, env_gym = _train_agent(train_df, tickers)
        _, actions_df = DRLAgent.DRL_prediction(model=trained, environment=env_gym)

        last_row = actions_df.iloc[-1]
        weights = {tic: max(0.0, float(w)) for tic, w in last_row.items()}
        total_w = sum(weights.values())
        if total_w > 1.0:
            weights = {k: v / total_w for k, v in weights.items()}
            total_w = 1.0
        cash_ratio = max(0.0, min(1.0, 1.0 - total_w))

        trailing = df[df.date >= df.date.unique()[-min(30, len(df.date.unique()))]]
        trailing_return = _equal_weight_bnh_return(trailing, tickers)
        regime = Regime.BULL if trailing_return > 0.02 else Regime.BEAR if trailing_return < -0.02 else Regime.SIDEWAYS

        rationale = (
            f"Weights are the final-day allocation from a real {MODEL_NAME.upper()} policy "
            f"(upstream FinRL's own DRLAgent wrapping stable_baselines3.A2C), trained live for "
            f"{TOTAL_TIMESTEPS} timesteps on {', '.join(tickers)}'s real yfinance history from "
            f"{fetch_start} to {date} (upstream's own StockPortfolioEnv reward = portfolio value, "
            f"upstream's own softmax weight normalization — no pretrained checkpoint was available "
            f"or used). Trailing 30-day equal-weight realized return {trailing_return:+.2%} → "
            f"heuristic regime label {regime.value if hasattr(regime,'value') else regime}."
        )

        result = Q4Portfolio(
            weights=weights,
            cash_ratio=cash_ratio,
            rationale=rationale,
            regime=regime,
            rebalance_freq="DAILY",
            adapter=self.name,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )
        _Q4_CACHE[cache_key] = result
        return result

    # ------------------------------------------------------------------
    # Q5 — Backtest
    # ------------------------------------------------------------------
    def q5_backtest(self, tickers: List[str], start: str, end: str, **kwargs) -> Optional[Q5Backtest]:
        t0 = time.time()
        tickers = list(tickers)
        cache_key = (tuple(sorted(tickers)), start, end)
        if cache_key in _Q5_CACHE:
            cached = _Q5_CACHE[cache_key]
            cached.latency_sec = time.time() - t0
            return cached

        from finrl.agents.stablebaselines3.models import DRLAgent
        from finrl.meta.preprocessor.preprocessors import data_split

        start_ts = pd.Timestamp(start)
        train_start_ts = start_ts - pd.DateOffset(days=HISTORY_DAYS)
        fetch_start = (train_start_ts - pd.DateOffset(days=COV_LOOKBACK_DAYS * 2)).strftime("%Y-%m-%d")

        df = _fetch_and_engineer(tickers, fetch_start, end)
        train_start = train_start_ts.strftime("%Y-%m-%d")

        train_df = data_split(df, train_start, start)
        test_df = data_split(df, start, end)
        if train_df.empty or test_df.empty:
            raise RuntimeError(f"Empty train/test split for {tickers} train=[{train_start},{start}) test=[{start},{end})")

        trained, _ = _train_agent(train_df, tickers)
        test_env_gym = _make_env(test_df, tickers)
        account_df, _ = DRLAgent.DRL_prediction(model=trained, environment=test_env_gym)

        daily_returns = account_df["daily_return"].to_numpy(dtype=float)
        equity_curve = np.cumprod(1.0 + daily_returns)
        total_return = float(equity_curve[-1] - 1.0)

        std = daily_returns.std()
        sharpe = float(np.sqrt(252) * daily_returns.mean() / std) if std > 0 else None

        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (equity_curve - running_max) / running_max
        max_drawdown = float(drawdowns.min())
        calmar = float(total_return / abs(max_drawdown)) if max_drawdown < 0 else None
        win_rate = float((daily_returns > 0).mean())

        bnh_return = _equal_weight_bnh_return(test_df, tickers)
        alpha_vs_benchmark = total_return - bnh_return

        result = Q5Backtest(
            total_return=total_return,
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            alpha_vs_benchmark=alpha_vs_benchmark,
            calmar=calmar,
            win_rate=win_rate,
            equity_curve=[float(x) for x in equity_curve],
            benchmark="equal_weight_bnh",
            train_period=f"{train_start}/{start}",
            test_period=f"{start}/{end}",
            adapter=self.name,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )
        _Q5_CACHE[cache_key] = result
        return result

    # ------------------------------------------------------------------
    # Smoke test — real q4 + q5 calls, not stubs
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        q4 = self.q4_portfolio(["AAPL", "MSFT", "NVDA"], "2024-01-15")
        checks["q4_returns_Q4Portfolio"] = q4 is not None
        if q4 is not None:
            w_sum = sum(q4.weights.values())
            checks["q4_weights_sum_le_1"] = w_sum <= 1.0 + 1e-6
            checks["q4_weights_nonnegative"] = all(v >= 0.0 for v in q4.weights.values())
            checks["q4_cash_ratio_in_range"] = 0.0 <= q4.cash_ratio <= 1.0

        q5 = self.q5_backtest(["AAPL", "MSFT", "NVDA"], "2024-01-01", "2024-03-31")
        checks["q5_returns_Q5Backtest"] = q5 is not None
        if q5 is not None:
            checks["q5_total_return_is_float"] = isinstance(q5.total_return, float)
            checks["q5_max_drawdown_sane"] = q5.max_drawdown is None or q5.max_drawdown <= 1e-9
            checks["q5_sharpe_is_number_or_none"] = q5.sharpe is None or isinstance(q5.sharpe, float)

        return checks
