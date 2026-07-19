"""
adapters/skfolio_adapter.py — wraps github.com/skfolio/skfolio (Q4 only —
rolling long-only mean-variance portfolio optimization via real WalkForward
cross-validation).

============================================================================
New-adapter integration pass (2026-07). Batch B of the candidate-adapter
roster in the active task brief.
============================================================================

Repo verification: real repo cloned at adapters/vendor/skfolio, commit
109ed13fee0125ff9b001b8be33643b17e791578 (2026-07-15). skfolio is also
pip-installable (`pip install skfolio`); this adapter uses the pip package
directly (not the vendor checkout) since the cloned commit is the current
`main` and the released package tracks it closely — simpler, more
reproducible for anyone re-running this adapter than pinning a vendor
sys.path shim. No upstream source was patched either way.

Environment setup (one-time, outside this file):
    conda create -n skfolio_real python=3.11
    conda activate skfolio_real
    pip install skfolio yfinance python-dotenv

Run the harness with that env active:
    conda activate skfolio_real
    python CONTRACT/adapter_runner.py --adapter adapters/skfolio_adapter.py \
        --task-id smoke --as-of 2024-01-15 --scope PORTFOLIO \
        --universe AAPL MSFT NVDA --gen-start 2023-01-03 --gen-end 2024-01-15

Design notes (translation choices made by this adapter, not upstream):
  - **Real `WalkForward` rolling refit, not a single `.fit()`** (per the
    task owner's explicit requirement): `skfolio.model_selection.WalkForward`
    (src/skfolio/model_selection/_walk_forward.py) is a real, public,
    sklearn-compatible cross-validator. Verified directly from its own
    docstring/`split()` implementation: yielded `(train_idx, test_idx)`
    pairs always have every test index strictly after every train index
    for that fold (non-overlapping, forward-only) — genuinely causal, not
    a convenience wrapper around a single in-sample fit. This adapter
    drives it with `test_size=REBALANCE_PERIOD_DAYS` (observation-count
    based, `freq=None` — simpler and avoids DatetimeIndex-frequency edge
    cases for a first integration) and `train_size=TRAIN_WINDOW_DAYS`,
    producing one real re-optimized weight vector per fold.
  - **Real optimizer**: `skfolio.optimization.MeanRisk` (its own default
    constructor args, verified by reading
    src/skfolio/optimization/convex/_mean_risk.py:695-705: `min_weights=0.0`
    → long-only, no shorting; `budget=1.0` → fully invested, weights sum to
    1). These are real, upstream-documented DEFAULTS, not values this
    adapter invented — `PortfolioConstraints` below cites them directly.
    `.fit(X_train).weights_` is the real fitted weight vector; nothing is
    reimplemented.
  - **Real returns computation**: `skfolio.preprocessing.prices_to_returns`
    (its own public function) converts real yfinance daily close prices to
    linear returns — the same function skfolio's own docs recommend for
    portfolio optimization (linear, not log, returns — see the function's
    own docstring on why).
  - **`generation_window` is harness-supplied and read-only**: real daily
    prices are fetched over exactly `[generation_window.start,
    generation_window.end]` (± 1 day padding for yfinance's exclusive
    `end`), never expanded/shrunk, and the same `generation_window` object
    is echoed back unchanged on `Q4Policy.generation_window`
    (`CONTRACT/base_adapter.py`'s `AdapterContractViolation` check enforces
    this).
  - **`policy_type=ROLLING_OPTIMIZER`**: each `WalkForward` fold re-fits
    `MeanRisk` from scratch on that fold's real train slice — a genuine
    periodic refit, not a single static allocation and not a per-observation
    online update. `update_policy.mode=UpdateMode.ROLLING_REFIT` follows.
  - **Causal `information_cutoff`**: for fold `i`, `information_cutoff` is
    the last real date in that fold's train slice (`X.index[train_idx[-1]]`)
    — strictly before the fold's own test dates, verified via `WalkForward`'s
    own non-overlapping-index guarantee cited above. `timestamp` for each
    `PolicyDecisionStep` is the first real date of that fold's test slice
    (the date the newly-fit weights first apply).
  - **Single-fold fallback (causality-safe)**: if the harness-supplied
    `generation_window` is too short to produce more than one real
    `WalkForward` split, this adapter does NOT report a fabricated
    one-step "trajectory" — it falls back to `initial_weights` only (the
    single real fit) with `decisions=None`, same pattern
    `adapters/finrl_adapter.py`/`adapters/agentictrading_adapter.py` use
    for their own single-point cases.
  - **Universe**: fixed, caller-supplied ticker list
    (`context.universe`/`context.targets`) — skfolio itself performs no
    asset selection; selection happens upstream of this call.
  - No Q1/Q2/Q3 claimed: skfolio is a pure portfolio-construction/
    cross-validation library with no action/state/signal concept of its
    own (category ABSENT).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    DecisionPolicy,
    ObservationPolicy,
    OutputScope,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    TimeWindow,
    UniversePolicy,
    UpdateMode,
    UpdatePolicy,
)

# Stepwise protocol types (harness/, outside CONTRACT/ — see
# Q4_STEPWISE_MIGRATION.md). Only used by q4_initialize/q4_step/q4_finalize
# below; q4_policy() (legacy, kept for compatibility) does not depend on them.
from harness.q4_protocol import PortfolioState, Q4FinalizeSummary, Q4RunConfig

TRAIN_WINDOW_DAYS = 60      # real observations per train fold
REBALANCE_PERIOD_DAYS = 10  # real observations per test fold (rebalance cadence)
MAX_TICKERS = 8


def _fetch_price_matrix(tickers: List[str], start: str, end: str):
    """Real yfinance daily close prices for the exact requested window."""
    import pandas as pd
    import yfinance as yf

    fetch_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw = yf.download(tickers, start=start, end=fetch_end, auto_adjust=True, progress=False)
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {tickers} [{start},{end}]")

    if len(tickers) == 1:
        close = raw["Close"].to_frame(tickers[0])
    else:
        close = raw["Close"]
    close = close.dropna(how="all").ffill().dropna()
    return close


def _build_decision_step(
    train_end_date: str,
    test_start_date: str,
    weights: Dict[str, float],
    active_tickers: List[str],
    train_size: int,
) -> PolicyDecisionStep:
    """Pure mapping: real (already-fitted) fold weights + real dates ->
    PolicyDecisionStep. No network/model calls — testable against a fixture."""
    return PolicyDecisionStep(
        timestamp=test_start_date,
        information_cutoff=train_end_date,
        selected_universe=active_tickers,
        target_weights=weights,
        explanation=(
            f"Real skfolio MeanRisk().fit() on train fold ending {train_end_date} "
            f"({train_size} real observations), applied for test fold starting {test_start_date}."
        ),
    )


class SkfolioAdapter(BaseAdapter):
    name = "skfolio"
    questions_answered = ["Q4"]
    upstream_repo = "https://github.com/skfolio/skfolio"
    requires_env = "skfolio_real"

    def __init__(self):
        super().__init__()
        self._session: Optional[dict] = None

    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        t0 = time.time()

        tickers = list(dict.fromkeys((context.universe or context.targets or [])))[:MAX_TICKERS]
        if not tickers:
            raise ValueError("skfolio q4_policy requires context.universe or context.targets with at least one ticker.")

        from skfolio.model_selection import WalkForward
        from skfolio.optimization import MeanRisk
        from skfolio.preprocessing import prices_to_returns

        prices = _fetch_price_matrix(tickers, generation_window.start, generation_window.end)
        active_tickers = list(prices.columns)
        X = prices_to_returns(prices)

        cv = WalkForward(test_size=REBALANCE_PERIOD_DAYS, train_size=TRAIN_WINDOW_DAYS, freq=None)
        n_splits = cv.get_n_splits(X)

        decisions: List[PolicyDecisionStep] = []
        last_weights: Dict[str, float] = {}
        fold_log = []

        for train_idx, test_idx in cv.split(X):
            X_train = X.iloc[train_idx]
            model = MeanRisk()  # real upstream defaults: min_weights=0.0 (long-only), budget=1.0 (fully invested)
            model.fit(X_train)
            weights = {asset: float(w) for asset, w in zip(X.columns, model.weights_)}
            last_weights = weights

            info_cutoff = str(X.index[train_idx[-1]].date())
            decision_ts = str(X.index[test_idx[0]].date())
            decisions.append(_build_decision_step(info_cutoff, decision_ts, weights, active_tickers, len(train_idx)))
            fold_log.append({"train_end": info_cutoff, "test_start": decision_ts, "weights": weights})

        constraints = PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0)

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=active_tickers,
            selector_description="Caller-supplied ticker list (context.universe/targets); skfolio performs no asset selection of its own.",
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{TRAIN_WINDOW_DAYS}_trading_days (real WalkForward train fold)",
            features=["daily linear returns (skfolio.preprocessing.prices_to_returns)"],
            data_sources=["yfinance daily close prices"],
            observation_description="Real historical return covariance/mean over each rolling real train fold.",
        )
        decision_policy = DecisionPolicy(
            decision_rule="Real skfolio MeanRisk (mean-variance, long-only, fully invested — upstream's own defaults) refit each WalkForward fold.",
            output_semantics="target portfolio weights (non-negative, sum to 1)",
            rebalance_frequency=f"every {REBALANCE_PERIOD_DAYS} trading days (WalkForward test_size)",
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.ROLLING_REFIT,
            update_frequency=f"every {REBALANCE_PERIOD_DAYS} trading days",
            update_description="Each WalkForward fold refits skfolio's real MeanRisk optimizer from scratch on that fold's real train slice.",
        )

        explanation = (
            f"Real skfolio.model_selection.WalkForward({TRAIN_WINDOW_DAYS}-day train, "
            f"{REBALANCE_PERIOD_DAYS}-day test) drove {n_splits} real MeanRisk refits over "
            f"{', '.join(active_tickers)}'s real yfinance daily prices in "
            f"[{generation_window.start}, {generation_window.end}]."
        )

        self._last_native = {
            "tickers_requested": tickers,
            "active_tickers": active_tickers,
            "n_splits": n_splits,
            "folds": fold_log,
        }

        if n_splits <= 1:
            # Causality-safe single-fold fallback: don't report a
            # one-element list as if it were a genuine trajectory.
            return Q4Policy(
                context=context,
                policy_type=PolicyType.ROLLING_OPTIMIZER,
                generation_window=generation_window,
                universe_policy=universe_policy,
                observation_policy=observation_policy,
                decision_policy=decision_policy,
                update_policy=update_policy,
                constraints=constraints,
                initial_weights=last_weights or None,
                decisions=None,
                explanation=explanation + " (generation_window too short for >1 real WalkForward split; reporting single fit only.)",
            )

        return Q4Policy(
            context=context,
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            decisions=decisions,
            explanation=explanation,
        )

    # ------------------------------------------------------------------ #
    # Stepwise Q4 protocol (harness/q4_protocol.py::Q4StepAdapter)       #
    # ------------------------------------------------------------------ #
    # Real mechanism: same real skfolio.model_selection.WalkForward +
    # skfolio.optimization.MeanRisk calls q4_policy() already makes — the
    # ONLY change is WHEN they run: q4_initialize() computes the real fold
    # boundaries once (WalkForward.split(X), a real, cheap, already-causal
    # generator per skfolio's own docstring — no actual optimization happens
    # yet), and q4_step() performs the real MeanRisk().fit(X_train) refit
    # for whichever fold's real test-start date matches the timestamp it is
    # asked about. Step granularity here is FOLD, not daily (unlike
    # adapters/universal_portfolios_adapter.py's per-day design) — one
    # q4_step() call answers for one real WalkForward fold.
    #
    # Off-schedule defensive behavior: if q4_step() is asked about a
    # timestamp that is not a real fold-start date (shouldn't happen if the
    # harness's rebalance schedule was built from this adapter's own real
    # fold boundaries, but handled defensively), it returns the
    # most-recently-fit REAL weights unchanged rather than performing a
    # spurious extra refit or fabricating new ones — a legitimate
    # "hold current weights" real behavior for a non-rebalance day.

    def q4_initialize(self, context: QueryContext, generation_window: TimeWindow,
                       initial_portfolio: PortfolioState, run_config: Q4RunConfig) -> Q4Policy:
        tickers = list(dict.fromkeys((context.universe or context.targets or [])))[:MAX_TICKERS]
        if not tickers:
            raise ValueError("skfolio q4_initialize requires context.universe or context.targets with at least one ticker.")

        from skfolio.model_selection import WalkForward
        from skfolio.preprocessing import prices_to_returns

        prices = _fetch_price_matrix(tickers, generation_window.start, generation_window.end)
        active_tickers = list(prices.columns)
        X = prices_to_returns(prices)

        cv = WalkForward(test_size=REBALANCE_PERIOD_DAYS, train_size=TRAIN_WINDOW_DAYS, freq=None)
        folds = list(cv.split(X))  # real, cheap: just yields (train_idx, test_idx) index arrays, no fitting yet

        folds_by_ts = {}
        for train_idx, test_idx in folds:
            info_cutoff = str(X.index[train_idx[-1]].date())
            decision_ts = str(X.index[test_idx[0]].date())
            folds_by_ts[decision_ts] = {"train_idx": train_idx, "info_cutoff": info_cutoff}

        self._session = {
            "X": X, "active_tickers": active_tickers, "folds_by_ts": folds_by_ts,
            "n_splits": len(folds), "last_weights": None, "step_count": 0,
        }

        return Q4Policy(
            context=context, policy_type=PolicyType.ROLLING_OPTIMIZER, generation_window=generation_window,
            universe_policy=UniversePolicy(mode="fixed", fixed_assets=active_tickers,
                                            selector_description="Caller-supplied ticker list; skfolio performs no asset selection of its own."),
            observation_policy=ObservationPolicy(
                lookback_window=f"{TRAIN_WINDOW_DAYS}_trading_days (real WalkForward train fold)",
                features=["daily linear returns (skfolio.preprocessing.prices_to_returns)"],
                data_sources=["yfinance daily close prices"],
            ),
            decision_policy=DecisionPolicy(
                decision_rule="Real skfolio MeanRisk (mean-variance, long-only, fully invested) refit each WalkForward fold.",
                rebalance_frequency=f"every {REBALANCE_PERIOD_DAYS} trading days (WalkForward test_size)",
            ),
            update_policy=UpdatePolicy(mode=UpdateMode.ROLLING_REFIT, update_frequency=f"every {REBALANCE_PERIOD_DAYS} trading days"),
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
        )

    def q4_step(self, timestamp: str, information_cutoff: str, observation, portfolio_state: PortfolioState) -> PolicyDecisionStep:
        if self._session is None:
            raise RuntimeError("q4_step called before q4_initialize")
        s = self._session
        s["step_count"] += 1

        fold = s["folds_by_ts"].get(timestamp)
        if fold is None:
            # Off-schedule day: hold the most recent real weights unchanged.
            if s["last_weights"] is None:
                raise ValueError(
                    f"timestamp {timestamp!r} is not a real WalkForward fold-start date and no prior "
                    f"real fit exists yet to hold — this session's real fold-start dates are "
                    f"{sorted(s['folds_by_ts'])[:3]}..."
                )
            return PolicyDecisionStep(
                timestamp=timestamp, information_cutoff=information_cutoff,
                selected_universe=s["active_tickers"], target_weights=s["last_weights"],
                explanation="Off-schedule day (not a real WalkForward fold-start date) — holding most recent real fit unchanged.",
            )

        from skfolio.optimization import MeanRisk

        X_train = s["X"].iloc[fold["train_idx"]]
        model = MeanRisk()  # real upstream defaults: min_weights=0.0 (long-only), budget=1.0 (fully invested)
        model.fit(X_train)
        weights = {asset: float(w) for asset, w in zip(s["X"].columns, model.weights_)}
        s["last_weights"] = weights

        return _build_decision_step(fold["info_cutoff"], timestamp, weights, s["active_tickers"], len(fold["train_idx"]))

    def q4_finalize(self) -> Q4FinalizeSummary:
        if self._session is None:
            raise RuntimeError("q4_finalize called before q4_initialize")
        s = self._session
        summary = Q4FinalizeSummary(
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            update_policy=UpdatePolicy(mode=UpdateMode.ROLLING_REFIT, update_frequency=f"every {REBALANCE_PERIOD_DAYS} trading days"),
            explanation=(
                f"Real skfolio WalkForward session over {len(s['active_tickers'])} tickers, "
                f"{s['n_splits']} real folds available, {s['step_count']} real q4_step() calls made."
            ),
        )
        self._session = None
        return summary

    def run(self, task_id, context, generation_window=None, native_output=None,
            adapter_notes=None, field_mappings=None, **kwargs):
        self._last_native = {}
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        if native_output is None and self._last_native:
            result = result.model_copy(update={"native_output": self._last_native})
        return result

    def smoke_test(self) -> Dict[str, bool]:
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO,
            universe=["AAPL", "MSFT", "NVDA"],
        )
        generation_window = TimeWindow(start="2023-06-01", end="2024-01-15")

        result = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = result is not None
        if result is not None:
            checks["context_echoed_unchanged"] = result.context == context
            checks["generation_window_echoed_unchanged"] = result.generation_window == generation_window
            checks["policy_type_is_rolling_optimizer"] = result.policy_type == "ROLLING_OPTIMIZER"
            decisions = result.decisions or []
            checks["decisions_nonempty"] = len(decisions) > 0
            if decisions:
                ok_causal = all(d.information_cutoff <= d.timestamp for d in decisions)
                checks["causality_ok"] = ok_causal
                ts = [d.timestamp for d in decisions]
                checks["timestamps_increasing"] = ts == sorted(ts)
                checks["weights_long_only_and_sum_1"] = all(
                    all(w >= -1e-9 for w in d.target_weights.values())
                    and abs(sum(d.target_weights.values()) - 1.0) < 1e-6
                    for d in decisions if d.target_weights
                )
        return checks
