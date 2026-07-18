"""
adapters/universal_portfolios_adapter.py — wraps
github.com/Marigold/universal-portfolios (Q4 — real online portfolio
selection algorithms).

New-adapter integration pass (2026-07). Batch B of the candidate-adapter
roster in the active task brief.

Repo verification: real repo cloned at adapters/vendor/universal-portfolios,
commit deb797be16cb33f1fc9b92db54a2ce5d2f11e2ec (2026-04-15), pip-installable
package `universal-portfolios` 0.4.16 (pyproject.toml). No upstream source
was patched.

============================================================================
What this project real is, verified by reading source (not the README)
============================================================================
`universal.algo.Algo` (universal/algo.py) is the real base class every
online-portfolio-selection algorithm subclasses. Two methods matter:
  - `step(self, x, last_b, history=None)` — the real per-period update rule.
    `x` is the current period's price relative, `last_b` the previous
    weight vector, `history` all data up to and including the current
    period.
  - `weights(self, X, min_history=None, ...)` (algo.py:66-104) — the real
    driver loop. Read in full and confirmed causal:
      `history = X.iloc[: t + 1]` (algo.py:92) — only past+current data is
      ever passed to `step()`, never future rows.
      `B.iloc[t] = last_b` (algo.py:82) — the weight recorded for period t
      was decided using data through t-1 and is held DURING period t (the
      new weight computed from period t's return is only assigned to
      period t+1's row on the next loop iteration).
  - `Algo.run(S)` (algo.py:117-170) is the real, public, intended
    entrypoint: `S` is a DataFrame of absolute prices, and `run()` itself
    converts prices to whatever `PRICE_TYPE` (ratio/log/raw) the specific
    algorithm needs before calling `weights()`. This adapter calls `run()`
    directly — the real, unmodified, documented public API — rather than
    reimplementing the price-conversion/step-loop wiring itself.
  - `AlgoResult.B` (universal/result.py) is the real weights DataFrame
    (index=dates, columns=tickers) `run()` returns.

============================================================================
Hindsight-optimal algorithms explicitly EXCLUDED (per active task brief)
============================================================================
`universal/algos/bcrp.py` (Best Constant Rebalanced Portfolio) computes the
theoretically optimal FIXED weights using the entire known price history at
once — a literal look-ahead/hindsight computation, not an executable
sequential policy. `universal/algos/best_markowitz.py` does the analogous
thing via full-sample mean/covariance. Neither is wrapped as `q4_policy`
output anywhere in this file, and neither is imported. They are real,
legitimate baselines upstream ships for *evaluating* other algorithms
against a theoretical optimum after the fact — exactly the kind of
retrospective-only object this project's Q4 contract forbids presenting as
an executable policy.

============================================================================
Algorithms wrapped (2 of ~14 real online algorithms; chosen deliberately)
============================================================================
  - ONS (universal/algos/ons.py) — Online Newton Step (Agarwal, Hazan, Kale,
    Schapire 2006). Verified real, causal, adaptive: maintains its own
    running `A`/`b` state updated only from the current period's realized
    return (`step(self, r, p, history)`), projects the resulting point onto
    the probability simplex via real quadratic programming
    (`projection_in_norm`, cvxopt `solvers.qp` with `G=-eye(m)` enforcing
    non-negativity and `A=ones/b=1` enforcing sum-to-1 — i.e. long-only,
    fully-invested by construction, confirmed by reading the QP setup, not
    assumed). `policy_type=ONLINE_ADAPTIVE_POLICY`.
  - OLMAR (universal/algos/olmar.py) — On-Line Moving Average Reversion (Li
    & Hoi 2012). Verified real, causal: `step()` only reads
    `history.iloc[-self.window:]` (a bounded PAST lookback window, no
    future rows), projects onto the simplex via `tools.simplex_proj`
    (long-only, sum-to-1). `policy_type=ONLINE_ADAPTIVE_POLICY`.
Both are real, unmodified upstream classes — this adapter's own code only
does: fetch real prices, instantiate the chosen `Algo` subclass, call its
real `.run()`, and map `AlgoResult.B` into the schema. No algorithm math is
reimplemented.

Algorithm selection: `algo_name` kwarg to `q4_policy`/`__init__`, one of
"ons" (default) or "olmar". Any other value raises `ValueError` rather than
silently falling back — this adapter does not claim the whole project's
~14-algorithm surface, only these two, verified ones.

============================================================================
Design notes (translation choices made by this adapter, not upstream)
============================================================================
  - `generation_window` (harness-supplied) is the exact price-history window
    fetched and run through the algorithm — never expanded/shortened. Real
    yfinance `Close` prices for `context.universe`/`context.targets`.
  - `decisions`: one `PolicyDecisionStep` per real row of `AlgoResult.B`
    strictly after the algorithm's own `min_history` warm-up (the warm-up
    rows all hold the fixed initial 1/N weights per `init_weights()` and
    would misrepresent the algorithm's real adaptive behavior if reported
    as "decisions" — they are dropped from `decisions` and the first
    genuine post-warm-up row becomes `initial_weights` instead, matching
    this schema's "single point vs trajectory" distinction). `timestamp` =
    that row's real date; `information_cutoff` = the previous real trading
    date in the fetched series (the date whose return `step()` consumed to
    produce this row's weights, per the `weights()` loop structure above) —
    always strictly less than `timestamp`, never equal, since the decision
    is made before that day's own price is known.
  - If the real fetched window is too short to produce more than the
    warm-up rows (no genuine post-warm-up decision), `decisions=None` and
    only `initial_weights` (the warm-up weights) is populated — a
    single-point result is never padded out to look like a trajectory.
  - `constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0,
    net_exposure_max=1.0)` — both chosen algorithms' real simplex
    projections guarantee this (see per-algorithm citations above); this is
    a verified property of the real code, not an assumed default (the
    schema itself does not assume long-only/sum-to-1 for Q4 in general).
  - No `artifact`: neither algorithm produces a persisted model file —
    their entire state is the in-memory `A`/`b` (ONS) or `x_pred` (OLMAR)
    running variables, which do not outlive one `q4_policy()` call in this
    adapter's design (matching `update_policy.mode=ONLINE_LEARNING`, state
    reset each call — a real, disclosed simplification: a genuine
    production deployment would persist this state across calls, but nothing
    in the harness contract requires or exposes an adapter-side persistence
    mechanism, so each call is honestly reported as a fresh cold-start run
    over the full `generation_window`).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    AdapterResult,
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

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "universal-portfolios"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

ALGO_REGISTRY = {
    "ons": ("universal.algos.ons", "ONS"),
    "olmar": ("universal.algos.olmar", "OLMAR"),
}
DEFAULT_ALGO = "ons"


def _load_algo_class(algo_name: str):
    if algo_name not in ALGO_REGISTRY:
        raise ValueError(
            f"universal_portfolios_adapter only wraps {sorted(ALGO_REGISTRY)} "
            f"(verified real, causal, non-hindsight algorithms) — got {algo_name!r}. "
            f"Hindsight-optimal algorithms (bcrp, best_markowitz) are intentionally "
            f"not wrapped by this adapter."
        )
    module_name, class_name = ALGO_REGISTRY[algo_name]
    import importlib

    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _build_decisions(B: pd.DataFrame, min_history: int, tickers: List[str]) -> List[PolicyDecisionStep]:
    """Pure mapping: real AlgoResult.B (weights DataFrame, index=dates) ->
    a real, causal PolicyDecisionStep list. Rows before min_history are the
    algorithm's own fixed warm-up weights (init_weights()), not a genuine
    decision, and are excluded — see module header. Kept as a standalone
    function so it can be unit-tested with a synthetic B DataFrame, without
    a real yfinance fetch or a real Algo.run() call."""
    decisions: List[PolicyDecisionStep] = []
    dates = list(B.index)
    for i in range(min_history, len(B)):
        if i == 0:
            continue  # no prior date to serve as information_cutoff
        ts = dates[i]
        cutoff = dates[i - 1]
        row = B.iloc[i]
        weights = {str(t): float(row[t]) for t in tickers}
        decisions.append(
            PolicyDecisionStep(
                timestamp=str(ts.date() if hasattr(ts, "date") else ts),
                information_cutoff=str(cutoff.date() if hasattr(cutoff, "date") else cutoff),
                selected_universe=list(tickers),
                target_weights=weights,
            )
        )
    return decisions


def _fetch_prices(tickers: List[str], start: str, end: str) -> pd.DataFrame:
    """Real yfinance absolute close prices, exactly the harness-supplied window
    (+1 day on `end` since yfinance's `end` is exclusive).

    Uses per-ticker `yf.Ticker(t).history(start=, end=)` rather than the
    batch `yf.download()` API — verified empirically in this sandbox that
    `yf.download()` returns an empty frame ("possibly delisted") for the
    same real, valid date range that `Ticker.history()` serves correctly.
    Same real per-ticker fetch pattern already used by
    `adapters/deepalpha_adapter.py` in this repo."""
    import yfinance as yf

    end_inclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    series = {}
    for t in tickers:
        hist = yf.Ticker(t).history(start=start, end=end_inclusive, interval="1d")
        if hist.empty:
            raise RuntimeError(f"yfinance returned no data for {t} [{start},{end}]")
        s = hist["Close"]
        s.index = s.index.tz_localize(None)
        series[t] = s
    prices = pd.DataFrame(series)
    prices = prices.dropna(how="all").ffill().dropna()
    if prices.empty:
        raise RuntimeError(f"No overlapping real trading days for {tickers} in [{start},{end}]")
    return prices


class UniversalPortfoliosAdapter(BaseAdapter):
    name = "universal_portfolios"
    questions_answered = ["Q4"]
    upstream_repo = "https://github.com/Marigold/universal-portfolios"
    requires_env = "universal_portfolios_real"

    def __init__(self):
        super().__init__()
        self._last_native: dict = {}

    # ------------------------------------------------------------------ #
    # Q4 — real online portfolio selection (ONS / OLMAR)                 #
    # ------------------------------------------------------------------ #
    def q4_policy(
        self,
        context: QueryContext,
        generation_window: TimeWindow,
        algo_name: str = DEFAULT_ALGO,
        **kwargs,
    ) -> Optional[Q4Policy]:
        tickers = list(dict.fromkeys(context.universe or context.targets or []))
        if not tickers:
            return None

        algo_cls = _load_algo_class(algo_name)
        algo = algo_cls()

        prices = _fetch_prices(tickers, generation_window.start, generation_window.end)

        # Real, unmodified public entrypoint — see module header.
        result = algo.run(prices)
        B = result.B  # real weights DataFrame, index=dates, columns=tickers

        min_history = getattr(algo, "min_history", 0) or 0
        decisions = _build_decisions(B, min_history, list(prices.columns))

        initial_weights: Optional[Dict[str, float]] = None
        if not decisions:
            # Real fetched window too short for a genuine post-warm-up decision
            # — only the fixed warm-up weights exist. Single point, not a
            # trajectory (see module header).
            last_row = B.iloc[-1]
            initial_weights = {str(t): float(last_row[t]) for t in prices.columns}
            decisions = None
        else:
            initial_weights = decisions[0].target_weights

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=list(tickers),
            selector_description=(
                "Caller-specified ticker list; universal-portfolios performs no "
                "asset selection of its own — every real algorithm in this "
                "project allocates only across the assets it is given."
            ),
        )
        observation_policy = ObservationPolicy(
            lookback_window=(
                f"full generation_window ({len(prices)} real trading days); "
                f"algorithm-internal state ({algo_name.upper()}) further bounds "
                f"how much of that history influences each decision"
            ),
            features=["real daily close price relatives (Algo.PRICE_TYPE conversion)"],
            data_sources=["yfinance (real historical close prices)"],
            observation_description=(
                f"Real {algo_cls.__name__}.step() update using only past+current "
                f"price relatives (verified causal via universal/algo.py:92, "
                f"history = X.iloc[: t + 1])."
            ),
        )
        decision_policy = DecisionPolicy(
            decision_rule=(
                f"Real, unmodified {algo_cls.__module__}.{algo_cls.__name__}.step() — "
                f"see module header for the per-algorithm real update rule and its "
                f"real simplex-projection constraint enforcement."
            ),
            output_semantics="target_weights: real simplex-projected allocation across tickers (non-negative, sums to 1.0).",
            rebalance_frequency="EVERY_TRADING_DAY" if getattr(algo, "frequency", 1) == 1 else f"every_{algo.frequency}_periods",
            holding_horizon=None,
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.ONLINE_LEARNING,
            update_frequency="every real trading day within generation_window",
            update_description=(
                f"Real {algo_cls.__name__} running state (see module header) updates "
                f"from each real day's realized price relative; state is not persisted "
                f"across separate q4_policy() calls (disclosed simplification, see header)."
            ),
        )
        constraints = PortfolioConstraints(
            long_only=True,
            net_exposure_min=1.0,
            net_exposure_max=1.0,
            additional_constraints=[
                f"Real simplex projection in {algo_cls.__name__}.step() (see module header) "
                f"guarantees non-negative weights summing to 1.0 every period."
            ],
        )

        explanation = (
            f"Real {algo_cls.__name__} ({algo_cls.__module__}) run over {len(tickers)} tickers "
            f"({', '.join(tickers)}) across {len(prices)} real trading days in "
            f"[{generation_window.start}, {generation_window.end}]. "
            f"{'Produced ' + str(len(decisions)) + ' real causal decisions.' if decisions else 'Window too short for a post-warm-up decision; only warm-up weights reported.'}"
        )

        self._last_native = {
            "algo_name": algo_name,
            "algo_class": f"{algo_cls.__module__}.{algo_cls.__name__}",
            "tickers": tickers,
            "n_trading_days": len(prices),
            "min_history": min_history,
            "weights_last_row": {str(t): float(B.iloc[-1][t]) for t in prices.columns},
            "generation_window": {"start": generation_window.start, "end": generation_window.end},
        }

        return Q4Policy(
            context=context,
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            initial_weights=initial_weights,
            artifact=None,
            decisions=decisions,
            explanation=explanation,
        )

    # ------------------------------------------------------------------ #
    # run() override — attach faithful native_output                    #
    # ------------------------------------------------------------------ #
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
        self._last_native = {}
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        if native_output is None and self._last_native:
            result = result.model_copy(update={"native_output": self._last_native})
        return result

    # ------------------------------------------------------------------ #
    # Smoke test — real call, small real universe/window                #
    # ------------------------------------------------------------------ #
    def smoke_test(self) -> Dict[str, bool]:
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-03-01",
            data_cutoff="2024-03-01",
            scope=OutputScope.PORTFOLIO,
            universe=["AAPL", "MSFT", "NVDA"],
        )
        generation_window = TimeWindow(start="2024-01-02", end="2024-03-01")

        result = self.q4_policy(context, generation_window, algo_name="ons")
        checks["q4_returns_Q4Policy"] = result is not None
        if result is not None:
            checks["context_echoed_unchanged"] = result.context == context
            checks["generation_window_echoed_unchanged"] = result.generation_window == generation_window
            checks["policy_type_is_online_adaptive"] = result.policy_type == "ONLINE_ADAPTIVE_POLICY"
            checks["initial_weights_present"] = bool(result.initial_weights)
            if result.initial_weights:
                w = result.initial_weights
                checks["weights_nonnegative"] = all(v >= -1e-9 for v in w.values())
                checks["weights_sum_to_1"] = abs(sum(w.values()) - 1.0) < 1e-6
            checks["decisions_present"] = bool(result.decisions)
            if result.decisions:
                checks["decisions_length_gt_1"] = len(result.decisions) > 1
                ok_causal = all(d.information_cutoff <= d.timestamp for d in result.decisions)
                checks["all_decisions_causal"] = ok_causal
                ts = [d.timestamp for d in result.decisions]
                checks["timestamps_strictly_increasing"] = all(a < b for a, b in zip(ts, ts[1:]))
                checks["all_decisions_have_selected_universe"] = all(
                    d.selected_universe == context.universe for d in result.decisions
                )
                checks["all_weights_sum_to_1"] = all(
                    abs(sum(d.target_weights.values()) - 1.0) < 1e-6 for d in result.decisions
                )
                checks["all_weights_nonnegative"] = all(
                    v >= -1e-9 for d in result.decisions for v in d.target_weights.values()
                )
        # Also verify a second real algorithm (OLMAR) constructs correctly.
        result2 = self.q4_policy(context, generation_window, algo_name="olmar")
        checks["olmar_returns_Q4Policy"] = result2 is not None
        return checks
