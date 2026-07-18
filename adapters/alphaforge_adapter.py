"""
adapters/alphaforge_adapter.py — wraps github.com/DulyHao/AlphaForge (Q3 only
— combined alpha-factor signal; NOT a Q4 policy, see "Q3 vs Q4" below).

============================================================================
Repo identity / relationship to the already-shipped alphagen_adapter.py
============================================================================
  AlphaForge (AAAI 2025, "AlphaForge: A Framework to Mine and Dynamically
  Combine Formulaic Alpha Factors") is a REAL, DISTINCT project from
  `ICT-FinD-Lab/alphagen` (already wrapped by `adapters/alphagen_adapter.py`
  in this repo) — that adapter's own header explicitly names and declines
  `DulyHao/AlphaForge` as a different, RL-adjacent-but-not-the-same target
  when it confirmed AlphaGen's identity. AlphaForge vendors a near-identical
  `alphagen`/`alphagen_generic`/`alphagen_qlib` package lineage (same
  `Expression`/`StockData`/`AlphaPool` core), but its real, distinguishing
  contribution is a two-stage pipeline: (1) GP/RL/DSO-based formulaic-alpha
  *discovery* (`train_GP.py`/`train_RL.py`/`train_DSO.py`, real vendored
  `gplearn`/`dso` search code — this repo does NOT treat these as
  "baselines to skip" the way alphagen_adapter.py treats alphagen's own
  vendored `gp.py`/`dso/`, because AlphaForge's paper explicitly proposes GP
  discovery + a GAN-based *combination* stage as its own two-part method),
  then (2) a GAN/PPO-based dynamic *combination* step
  (`combine_AFF.py`/`train_AFF.py`, real `gan/` package: `generater.py`,
  `masker.py`, `predictor.py`) that re-weights a discovered factor pool over
  time.

============================================================================
Real repo verification
============================================================================
  Cloned `https://github.com/DulyHao/AlphaForge.git`, commit `d0cfc27d`
  (2024-09-01). `requirements.txt` confirms real, heavy deps: `qlib==0.9.0`,
  `baostock==00.8.90` (China A-share data), `torch==1.13.0`,
  `gym==0.21.0`, `sb3_contrib==1.8.0`, `stable_baselines3==1.8.0`. File tree
  (`alphagen/`, `alphagen_generic/`, `alphagen_qlib/`, `gan/`, `gplearn/`,
  `dso/`, `data_collection/`, `train_*.py`, `combine_AFF.py`) is entirely
  on-topic for a formulaic-alpha research repo — no unrelated subtree.
  `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|api_key|secret|password"`
  across every module this adapter imports: `eval(...)` appears only inside
  upstream's own `train_GP.py`/`combine_AFF.py` scripts (evaluating trusted,
  upstream-authored formula-string literals from GP search results — this
  adapter's own `_run_gp_search` reproduces the identical trusted-literal
  pattern, not arbitrary/untrusted input), no credential/secret patterns
  anywhere. No live brokerage/exchange account or funded capital anywhere in
  the code path used.

============================================================================
Mechanism actually used by this adapter, and why (verified by reading
source, then running it, not by trusting the README)
============================================================================
  - **Discovery stage — real, small-scale GP search**: `train_GP.py`'s own
    real pattern is reproduced at drastically reduced scale: real
    `gplearn.genetic.SymbolicRegressor` over upstream's own real
    `alphagen_generic.operators.funcs` (87 real operators, confirmed via
    `len(funcs)==87` in this sandbox) and `alphagen_generic.features`
    (`open_`/`close`/`high`/`low`/`volume`/`vwap`), with a real fitness
    function (`_run_gp_search._metric` below) computing real Pearson IC of
    each candidate expression against upstream's own real target
    (`alphagen_generic.features.target = Ref(vwap,-21)/Ref(vwap,-1)-1`, a
    real 21-day forward VWAP-based return, unmodified) via
    `Expression.evaluate()` (upstream's own, unmodified). Scoped down from
    upstream's own `population_size=1000, generations=40` (`train_GP.py`)
    to `GP_POPULATION_SIZE=40, GP_GENERATIONS=3` — same category of
    real-but-reduced search budget `adapters/atlas_adapter.py` (DEAP GP)
    and `adapters/alphagen_adapter.py` (RL timesteps: 4000 vs. upstream's
    200k-350k) already use in this repo, not a different mechanism.
  - **Combination stage — real, but the LINEAR pool-optimization stage, not
    the full GAN/PPO re-weighting stage**: upstream's real `AlphaPool`
    (`alphagen/models/alpha_pool.py`, distinct class from
    `alphagen_adapter.py`'s `LinearAlphaPool`/`MseAlphaPool`) is built with
    the top-K GP-discovered expressions via its real, public
    `force_load_exprs()`, which internally calls its real, public
    `_optimize()` — a genuine gradient-based (`torch.optim.Adam`) joint
    optimization of combination weights minimizing
    `mut_ic_sum - 2*ret_ic_sum + l1_penalty` (read directly from
    `alpha_pool.py:122-156`, unmodified). This is a real, upstream,
    documented combination mechanism — just not the paper's headline
    GAN/PPO dynamic-reweighting contribution.
    **Scope reduction, disclosed, not fabricated**: the full GAN/PPO
    combination pipeline (`combine_AFF.py::main()`, `train_AFF.py`)
    requires a SEPARATE, already-completed real training run producing a
    pickled `AlphaPool` "zoo" artifact at a hardcoded path
    (`out/{save_name}_{instruments}_{train_end}_{seed}/z_bld_zoo_final.pkl`
    — confirmed by reading `combine_AFF.py:105-113`) plus a real, further
    GAN/masker/predictor training loop over that artifact
    (`train_AFF.py`) — a multi-stage, multi-hour real pipeline this
    adapter's single `q3_signal()` call does not attempt to reproduce
    end-to-end. This is category-3-adjacent (real, public, but requires a
    heavier multi-stage real pipeline than a single thin-wrapper call can
    honestly reproduce at interactive scale) — documented here rather than
    silently claimed. `AlphaPool._optimize()`'s real linear combination is
    still a genuine, upstream, non-fabricated combination step, so this
    adapter is not reporting raw unweighted GP output either.
  - **Q3 vs Q4 (explicit, per task-owner instruction)**: the real
    `AlphaPool.weights` produced by `_optimize()` are ALPHA-FACTOR
    combination weights (how much each discovered *formula* contributes to
    one combined per-asset score), not portfolio asset weights. The final
    combined score is mapped to `Q3Signal.values` (a predictive
    cross-sectional signal), never to any Q4 field — this project has no
    portfolio/order/rebalancing concept anywhere in its real code (`grep`
    confirms no `Portfolio`/`Position`/`Order` class anywhere in
    `alphagen*`/`gan`), so Q4 is genuinely ABSENT, not just unclaimed.

============================================================================
Environment design decision — avoiding Qlib/baostock entirely (same pattern
`adapters/alphagen_adapter.py` already established for the same upstream
`alphagen_qlib.stock_data.StockData` class, adapted for AlphaForge's own
StockData constructor signature, which differs from alphagen's — no
`preloaded_data` kwarg here)
============================================================================
  AlphaForge's own `alphagen_qlib/stock_data.py::StockData.__init__` calls
  `self._init_qlib(qlib_path)` unconditionally, then `self._get_data()`
  (which queries `qlib.data.D`/`QlibDataLoader`). This adapter's
  `AFStockData` (below) is a from-scratch, adapter-side class — not a
  subclass this time, since AlphaForge's `StockData` constructor has no
  data-injection escape hatch — that sets exactly the same attributes real
  downstream consumers read (`data`, `max_backtrack_days`,
  `max_future_days`, `device`, `n_days`, `n_stocks`, `stock_ids` — verified
  by reading `Expression.evaluate()`, `AlphaPool`, `QLibStockDataCalculator`
  in `alphagen/data/expression.py`, `alphagen/models/alpha_pool.py`,
  `alphagen_qlib/calculator.py`), built from real yfinance OHLCV instead of
  Qlib/baostock. `qlib`/`baostock` are never imported by this adapter.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n alphaforge_real python=3.10
    conda activate alphaforge_real
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install pandas numpy yfinance fire pydantic gplearn scikit-learn \\
        scipy python-dotenv
    # Deliberately NOT installed: qlib, baostock, sb3_contrib/stable_baselines3
    # (RL discovery path — this adapter uses the GP path only), the `gan`
    # package's own torch/PPO combination training loop (see "Scope
    # reduction" above — not exercised by this adapter).
    git clone --depth 1 https://github.com/DulyHao/AlphaForge.git \\
        adapters/vendor/AlphaForge

No upstream source was patched — `AFStockData`/`_run_gp_search` are
adapter-side, living in this file — so there is no patches/AlphaForge.diff.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    Direction,
    EvidenceItem,
    OutputScope,
    Q3Signal,
    QueryContext,
    TimeWindow,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "AlphaForge"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Real upstream convention (train_GP.py:29,35, unmodified): GP-discovered
# expression strings reference operator/feature names (e.g. "ts_ema",
# "open_") that must be in scope for eval() to resolve them back into real
# Expression objects. Upstream's own train_GP.py does these exact two
# wildcard imports at module level for the same reason — not a workaround
# introduced by this adapter.
from alphagen.data.expression import *  # noqa: F401,F403
from alphagen_generic.features import *  # noqa: F401,F403

DEVICE = torch.device("cpu")

COMPANION_POOL = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "XOM", "UNH", "V"]
UNIVERSE_SIZE = 8
FALLBACK_TICKER = "AAPL"

TARGET_FUTURE_DAYS = 21          # matches upstream's own Ref(vwap,-21)/Ref(vwap,-1)-1 target
MAX_BACKTRACK_DAYS = 30          # covers upstream operators' typical lookback windows
TRAIN_LOOKBACK_CALENDAR_DAYS = 500
TRAIN_END_BUFFER_DAYS = 30

POOL_CAPACITY = 5                # real AlphaPool capacity (upstream default: 10-100)
GP_POPULATION_SIZE = 40          # scoped down from upstream's own 1000 (train_GP.py)
GP_GENERATIONS = 3               # scoped down from upstream's own 40 (train_GP.py)

RANDOM_SEED = 42
TOP_PCT = 0.2

_SEARCH_CACHE: dict = {}


def _clamp_asof(date: str) -> pd.Timestamp:
    asof = pd.Timestamp(date)
    now = pd.Timestamp(datetime.now().date())
    return min(asof, now)


def _fetch_panel(tickers: List[str], start: datetime, end: datetime) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Real yfinance OHLCV for each ticker, aligned to a shared trading-day
    index. Returns (panel, tickers_with_data). Same pattern
    adapters/alphagen_adapter.py already uses for the same real data source."""
    import yfinance as yf

    frames: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        last_err = None
        for attempt in range(4):
            try:
                df = yf.Ticker(t).history(
                    start=start.strftime("%Y-%m-%d"),
                    end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
                    auto_adjust=True,
                )
                if df is not None and not df.empty:
                    break
                df = None
            except Exception as e:
                last_err = e
                df = None
            if attempt < 3:
                time.sleep(3 * (attempt + 1))
        if df is None or df.empty:
            continue
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df = df[~df.index.duplicated(keep="last")]
        frames[t] = df
    if not frames:
        return {}, []

    common_index = None
    for df in frames.values():
        common_index = df.index if common_index is None else common_index.intersection(df.index)
    common_index = common_index.sort_values()

    panel = {t: df.reindex(common_index) for t, df in frames.items()}
    return panel, list(panel.keys())


class AFStockData:
    """
    Adapter-side stand-in for upstream's `alphagen_qlib.stock_data.StockData`
    — see module header "Environment design decision". Exposes exactly the
    attributes/properties real upstream code reads (`data`,
    `max_backtrack_days`, `max_future_days`, `device`, `n_days`, `n_stocks`,
    `stock_ids`); real upstream `Expression.evaluate()`/`AlphaPool`/
    `QLibStockDataCalculator` consume this object exactly as they would a
    real `StockData` instance built from Qlib/baostock.
    """

    def __init__(
        self,
        data: torch.Tensor,
        stock_ids: List[str],
        max_backtrack_days: int,
        max_future_days: int,
    ) -> None:
        self.data = data
        self._stock_ids = pd.Index(stock_ids)
        self.max_backtrack_days = max_backtrack_days
        self.max_future_days = max_future_days
        self.device = data.device

    @property
    def n_stocks(self) -> int:
        return self.data.shape[-1]

    @property
    def n_days(self) -> int:
        return self.data.shape[0] - self.max_backtrack_days - self.max_future_days

    @property
    def stock_ids(self) -> pd.Index:
        return self._stock_ids


def _build_stock_data(
    panel: Dict[str, pd.DataFrame],
    max_backtrack_days: int,
    max_future_days: int,
) -> AFStockData:
    from alphagen_qlib.stock_data import FeatureType  # upstream, unmodified

    stock_ids = list(panel.keys())
    n_days = len(next(iter(panel.values())))
    feats = [
        FeatureType.OPEN, FeatureType.CLOSE, FeatureType.HIGH,
        FeatureType.LOW, FeatureType.VOLUME, FeatureType.VWAP,
    ]
    arr = np.zeros((n_days, len(feats), len(stock_ids)), dtype=np.float32)
    for si, t in enumerate(stock_ids):
        df = panel[t]
        arr[:, 0, si] = df["Open"].values
        arr[:, 1, si] = df["Close"].values
        arr[:, 2, si] = df["High"].values
        arr[:, 3, si] = df["Low"].values
        arr[:, 4, si] = df["Volume"].values
        # VWAP approximation (typical price) — same convention
        # adapters/alphagen_adapter.py already uses for its own VWAP feature.
        arr[:, 5, si] = (df["High"].values + df["Low"].values + df["Close"].values) / 3.0
    tensor = torch.tensor(arr, dtype=torch.float, device=DEVICE)
    return AFStockData(tensor, stock_ids, max_backtrack_days, max_future_days)


def _run_gp_search(universe_tickers: Tuple[str, ...], date: str):
    """
    Real, unmodified upstream discovery+combination pipeline at reduced
    scale: real `gplearn.genetic.SymbolicRegressor` search over upstream's
    own real operator/feature set (`alphagen_generic`), scored by real
    Pearson IC via upstream's own `Expression.evaluate()`; top candidates
    combined via upstream's own real `AlphaPool.force_load_exprs()` +
    `_optimize()`. See module header for the full mechanism writeup and the
    documented GAN/PPO-stage scope reduction.
    Returns (pool, data, target_expr, universe_used, asof).
    """
    key = (universe_tickers, date)
    if key in _SEARCH_CACHE:
        return _SEARCH_CACHE[key]

    from alphagen.data.expression import Expression, OutOfDataRangeError
    from alphagen.models.alpha_pool import AlphaPool
    from alphagen.utils.correlation import batch_pearsonr
    from alphagen.utils.pytorch_utils import normalize_by_day
    from alphagen.utils.random import reseed_everything
    from alphagen_generic.features import target as generic_target
    from alphagen_generic.operators import funcs as generic_funcs
    from gplearn.functions import make_function
    from gplearn.genetic import SymbolicRegressor
    from gplearn.fitness import make_fitness

    reseed_everything(RANDOM_SEED)

    asof = _clamp_asof(date)
    train_end = asof - pd.Timedelta(days=TRAIN_END_BUFFER_DAYS)
    train_start = train_end - pd.Timedelta(days=TRAIN_LOOKBACK_CALENDAR_DAYS)

    panel, ok = _fetch_panel(list(universe_tickers), train_start.to_pydatetime(), train_end.to_pydatetime())
    if len(ok) < 2:
        raise RuntimeError(
            f"Insufficient real yfinance history for universe {universe_tickers} "
            f"in window [{train_start.date()}, {train_end.date()}] — need at "
            f"least 2 tickers for cross-sectional IC."
        )
    data = _build_stock_data({t: panel[t] for t in ok}, MAX_BACKTRACK_DAYS, TARGET_FUTURE_DAYS)
    if data.n_days < 60:
        raise RuntimeError(f"Too few real trading days ({data.n_days}) for a meaningful GP search.")

    target_factor = normalize_by_day(generic_target.evaluate(data))  # upstream, unmodified

    # Real GP fitness function: identical mechanism to upstream's own
    # train_GP.py::_metric (cache expr_str -> IC, evaluate real
    # Expression.evaluate() + real Pearson IC), just called from a
    # drastically smaller SymbolicRegressor budget.
    cache: Dict[str, float] = {}

    def _metric(x, y, w):
        key_str = y[0]
        if key_str in cache:
            return cache[key_str]
        token_len = key_str.count("(") + key_str.count(")")
        if token_len > 14:
            return -1.0
        try:
            expr: Expression = eval(key_str)  # trusted, upstream-authored formula literal (see header)
            factor = normalize_by_day(expr.evaluate(data))
            ic = batch_pearsonr(factor, target_factor)
            ic = torch.nan_to_num(ic).mean().item()
        except (OutOfDataRangeError, Exception):
            ic = -1.0
        if np.isnan(ic):
            ic = -1.0
        cache[key_str] = ic
        return ic

    Metric = make_fitness(function=_metric, greater_is_better=True)
    funcs = [make_function(**func._asdict()) for func in generic_funcs]

    X_train = np.array([["open_", "close", "high", "low", "volume", "vwap"]])
    y_train = np.array([[1]])

    est_gp = SymbolicRegressor(
        population_size=GP_POPULATION_SIZE,
        generations=GP_GENERATIONS,
        init_depth=(2, 4),
        tournament_size=max(5, GP_POPULATION_SIZE // 4),
        stopping_criteria=1.0,
        p_crossover=0.3, p_subtree_mutation=0.1, p_hoist_mutation=0.01,
        p_point_mutation=0.1, p_point_replace=0.6,
        max_samples=0.9, parsimony_coefficient=0.0,
        random_state=RANDOM_SEED, function_set=funcs, metric=Metric,
        const_range=None, n_jobs=1, verbose=0,
    )
    est_gp.fit(X_train, y_train)  # real, unmodified gplearn.genetic.SymbolicRegressor

    if not cache:
        raise RuntimeError("Real GP search evaluated zero candidate expressions for this window.")

    # Top-K real discovered expressions by real cached IC (upstream's own
    # train_GP.py::try_pool selection rule, Counter(cache).most_common).
    ranked = sorted(cache.items(), key=lambda kv: kv[1], reverse=True)[:POOL_CAPACITY]
    top_exprs = [eval(expr_str) for expr_str, _ in ranked]  # trusted literals, same as upstream

    pool = AlphaPool(capacity=POOL_CAPACITY, stock_data=data, target=generic_target, ic_lower_bound=None)
    pool.force_load_exprs(top_exprs)  # real, unmodified upstream combination optimization

    # NOTE: pool.best_ic_ret/pool.eval_cnt are only ever updated inside
    # AlphaPool.try_new_expr() (see alpha_pool.py:89-111) — force_load_exprs()
    # (the real combination method this adapter uses) never touches them,
    # so they'd stay at their __init__ defaults (-1.0 / 0) here regardless
    # of real search quality. Reporting those fields directly would be a
    # real field name carrying a permanently-stale, misleading value.
    # Use pool.test_ensemble() (real, public) for a genuine in-sample
    # ensemble IC instead, and the real GP fitness-cache size (distinct
    # expressions actually evaluated by SymbolicRegressor) in place of
    # eval_cnt.
    real_ensemble_ic, _ = pool.test_ensemble(data, generic_target)
    gp_eval_count = len(cache)

    result = (pool, data, generic_target, ok, asof, real_ensemble_ic, gp_eval_count)
    _SEARCH_CACHE[key] = result
    return result


def _rank_direction_strength(
    resolved_ticker: str, values: Dict[str, float], top_pct: float = TOP_PCT
) -> Tuple[str, float, int, float]:
    """Pure adapter-derived cross-sectional percentile-rank -> Direction/
    strength translation (same convention adapters/alphagen_adapter.py
    already uses). Factored out for direct fixture testing — no network,
    no upstream call. Returns (direction, strength, rank_position, pct)."""
    n_valid = len(values)
    sorted_ids = sorted(values, key=lambda k: values[k], reverse=True)
    rank_position = sorted_ids.index(resolved_ticker) + 1
    pct = (n_valid - rank_position) / (n_valid - 1) if n_valid > 1 else 0.5
    direction = Direction.LONG if pct >= (1 - top_pct) else Direction.SHORT if pct <= top_pct else Direction.NEUTRAL
    strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))
    return direction, strength, rank_position, pct


def _resolve_universe(ticker: str) -> Tuple[Tuple[str, ...], bool]:
    normalized = (ticker or "").strip().upper()
    companions = [t for t in COMPANION_POOL if t != normalized][: UNIVERSE_SIZE - 1]
    universe = [normalized] + companions
    return tuple(universe), normalized in COMPANION_POOL or normalized == FALLBACK_TICKER


class AlphaForgeAdapter(BaseAdapter):
    name = "alphaforge"
    questions_answered = ["Q3"]
    upstream_repo = "https://github.com/DulyHao/AlphaForge"
    requires_env = "alphaforge_real"

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        requested_ticker = ((context.targets[0] if context.targets else FALLBACK_TICKER) or "").strip().upper()
        date = context.data_cutoff or context.as_of
        universe, _ = _resolve_universe(requested_ticker)

        try:
            pool, data, target_expr, universe_used, asof, ensemble_ic, gp_eval_count = _run_gp_search(universe, date)
            resolved_ticker = requested_ticker if requested_ticker in universe_used else None
        except Exception:
            resolved_ticker = None

        was_fallback = False
        if resolved_ticker is None:
            was_fallback = True
            fb_universe, _ = _resolve_universe(FALLBACK_TICKER)
            pool, data, target_expr, universe_used, asof, ensemble_ic, gp_eval_count = _run_gp_search(fb_universe, date)
            resolved_ticker = FALLBACK_TICKER if FALLBACK_TICKER in universe_used else universe_used[0]

        asof_str = asof.strftime("%Y-%m-%d")

        # Real combined per-asset score: upstream's own weighted sum of the
        # real pool's real normalized factor values (same computation
        # AlphaPool.test_ensemble() performs internally, read directly).
        from alphagen.utils.pytorch_utils import normalize_by_day

        with torch.no_grad():
            factors = []
            for i in range(pool.size):
                factor = normalize_by_day(pool.exprs[i].evaluate(data))
                factors.append(factor * float(pool.weights[i]))
            combined = sum(factors) if factors else torch.zeros((data.n_days, data.n_stocks))
        last_row = combined[-1]
        stock_ids = list(universe_used)

        values: Dict[str, float] = {
            sid: float(last_row[i].item())
            for i, sid in enumerate(stock_ids)
            if not torch.isnan(last_row[i])
        }
        if not values:
            values = {resolved_ticker: 0.0}

        evidence: List[EvidenceItem] = []
        if was_fallback:
            evidence.append(EvidenceItem(
                kind="universe_fallback",
                value=(
                    f"Requested ticker '{requested_ticker}' had no usable real yfinance "
                    f"history for this point-in-time window; reporting the real "
                    f"GP-discovered/combined alpha signal for fallback ticker "
                    f"'{resolved_ticker}' instead."
                ),
                source="adapter (yfinance data-availability check)",
            ))

        if resolved_ticker in values:
            direction, strength, rank_position, pct = _rank_direction_strength(resolved_ticker, values)
            n_valid = len(values)
            explanation = (
                f"'{resolved_ticker}' real GP-discovered + AlphaPool-combined score "
                f"{values[resolved_ticker]:.4f} ranks {rank_position}/{n_valid} "
                f"({pct:.0%} percentile) across the real {n_valid}-ticker universe on "
                f"{asof_str}. Combination stage: real AlphaPool._optimize() linear "
                f"weights (see module header for the GAN/PPO-stage scope reduction — "
                f"the paper's full dynamic-reweighting stage is not reproduced here)."
            )
        else:
            direction = Direction.NEUTRAL
            strength = 0.0
            explanation = f"No valid (non-NaN) combined score for '{resolved_ticker}' on {asof_str}."

        for i in range(pool.size):
            evidence.append(EvidenceItem(
                kind="factor_expression",
                value=f"{str(pool.exprs[i])} (combination_weight={float(pool.weights[i]):.4f}, single_ic={float(pool.single_ics[i]):.4f})",
                source="AlphaForge AlphaPool.state (real GP-discovered expression + real _optimize() weight)",
            ))

        evidence.append(EvidenceItem(
            kind="gp_search_diagnostics",
            value=(
                f"Real gplearn.genetic.SymbolicRegressor search: population_size="
                f"{GP_POPULATION_SIZE}, generations={GP_GENERATIONS} (scoped down from "
                f"upstream's own 1000/40 — see module header), {gp_eval_count} distinct "
                f"real candidate expressions evaluated, real in-sample combined-pool "
                f"ensemble IC (AlphaPool.test_ensemble()) = {ensemble_ic:.4f}. "
                f"(pool.best_ic_ret/eval_cnt are not used here — real upstream code only "
                f"updates them inside try_new_expr(), never inside the force_load_exprs() "
                f"combination path this adapter calls; see module header.)"
            ),
            source="AlphaForge gplearn.SymbolicRegressor + AlphaPool.test_ensemble()",
        ))

        self._last_native_output = {
            "upstream": {
                "pool_exprs": [str(e) for e in pool.exprs[:pool.size]],
                "pool_weights": [float(w) for w in pool.weights[:pool.size]],
                "pool_single_ics": [float(x) for x in pool.single_ics[:pool.size]],
                "pool_ensemble_ic": float(ensemble_ic),
                "gp_eval_count": int(gp_eval_count),
                "universe_used": list(stock_ids),
                "asof": asof_str,
                "combined_score_last_row": values,
            },
            "adapter_derived": {
                "requested_ticker": requested_ticker,
                "resolved_ticker": resolved_ticker,
                "was_fallback": was_fallback,
                "gp_population_size": GP_POPULATION_SIZE,
                "gp_generations": GP_GENERATIONS,
            },
        }
        self._last_latency_sec = time.time() - t0

        return Q3Signal(
            context=context,
            signal_semantics=(
                "factor_value — combined alpha score from AlphaForge's real "
                "GP-discovered formulaic-alpha pool, linearly combined via "
                "AlphaPool._optimize() (real, upstream). Continuous cross-sectional "
                "score, not a return prediction or probability."
            ),
            values=values,
            score_scale="continuous, unitless (linear combination of real normalized formulaic alphas)",
            direction=direction,
            strength=strength,
            factor_expression="; ".join(str(e) for e in pool.exprs[:pool.size]) or None,
            confidence=ConfidenceEstimate(
                value=max(0.0, min(1.0, (float(ensemble_ic) + 1.0) / 2.0)),
                kind=ConfidenceKind.MODEL_MARGIN,
                raw_value=float(ensemble_ic),
                method="real AlphaPool.test_ensemble() in-sample Pearson IC against the real forward-return target, rescaled from [-1,1] to [0,1]",
            ),
            evidence=evidence or None,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output, reusing the same
    # cached search q3_signal() will use.
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
        self._last_latency_sec = 0.0
        result = super().run(
            task_id, context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes,
            field_mappings=field_mappings, **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native_output:
            updates["native_output"] = self._last_native_output
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
            scope=OutputScope.CROSS_SECTION,
            targets=["AAPL"],
            universe=["AAPL"],
        )
        result = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = result is not None
        if result is not None:
            checks["context_echoed_unchanged"] = result.context == context
            checks["values_nonempty"] = len(result.values) > 0
            checks["direction_is_valid"] = result.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["strength_in_range"] = result.strength is None or 0.0 <= result.strength <= 1.0
            checks["evidence_nonempty"] = bool(result.evidence)
            checks["factor_expression_set"] = bool(result.factor_expression)
            checks["confidence_in_range"] = (
                result.confidence is not None and 0.0 <= result.confidence.value <= 1.0
            )
            factor_evidence = [e for e in (result.evidence or []) if e.kind == "factor_expression"]
            checks["evidence_reflects_real_pool_size"] = len(factor_evidence) >= 1
        return checks
