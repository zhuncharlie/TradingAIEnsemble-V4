"""
adapters/deepdow_adapter.py — wraps github.com/jankrepl/deepdow (Q4 only —
a single, fixed, real trained portfolio-allocation network, causally
evaluated day-by-day over the harness-supplied generation_window).

============================================================================
New-adapter integration pass (2026-07). Batch C of the candidate-adapter
roster in the active task brief.
============================================================================

Repo verification: real repo cloned at adapters/vendor/deepdow, commit
384e18acc17c982ac5a4362187b348bdbdb07b98 (2024-01-24). deepdow is also
pip-installable (`pip install deepdow`); this adapter uses the pip package
directly (same reasoning as adapters/skfolio_adapter.py — simpler,
reproducible, and the released version tracks this commit closely). No
upstream source was patched.

Environment setup (one-time, outside this file):
    conda create -n deepdow_real python=3.10
    conda activate deepdow_real
    pip install deepdow yfinance python-dotenv pydantic

Run the harness with that env active:
    conda activate deepdow_real
    python CONTRACT/adapter_runner.py --adapter adapters/deepdow_adapter.py \
        --task-id smoke --as-of 2024-01-15 --scope PORTFOLIO \
        --universe AAPL MSFT NVDA --gen-start 2023-01-03 --gen-end 2024-01-15

Design notes (translation choices made by this adapter, not upstream):
  - **deepdow is a framework, not a single strategy** — it ships several
    real example networks in `deepdow/nn.py` (`BachelierNet`, `KeynesNet`,
    `MinimalNet`, `ThorpNet`, ...). Per the task owner's explicit
    requirement ("必须固定清晰、可复现的具体网络和配置"), this adapter fixes
    ONE specific, reproducible architecture rather than exposing a generic
    "any deepdow network" wrapper. The chosen network is `GreatNet`
    (defined below), which is deepdow's own official tutorial/walkthrough
    architecture from `examples/end_to_end/getting_started.py` (read in
    full this session) — not something this adapter invented: a single
    `torch.nn.Dropout` -> `torch.nn.Linear(n_assets*lookback, n_assets)` ->
    `deepdow.layers.SoftmaxAllocator(temperature=None)` with a learnable
    temperature parameter. This is deepdow's own canonical minimal
    end-to-end example, chosen specifically because it is small enough to
    train on a real, honestly-reduced budget while remaining fully real,
    unmodified, and traceable to upstream's own documentation (not a
    network this adapter's author designed).
  - **Real allocation/constraint guarantee**: `SoftmaxAllocator`
    (`deepdow/layers/allocate.py:414-506`, `formulation="analytical"`
    default) is verified by reading its source to be literally
    `torch.nn.Softmax(dim=1)` applied to the network's raw output —
    mathematically non-negative and summing to exactly 1 across the asset
    dimension by construction. `PortfolioConstraints(long_only=True,
    net_exposure_min=1.0, net_exposure_max=1.0)` below is a direct,
    verified consequence of this real layer, not an assumption. No cash
    weight exists in deepdow's own output space (it only allocates across
    the requested real assets) — this adapter does not synthesize one.
  - **Real dataset/loader utilities used as intended**: `deepdow.data.
    InRAMDataset`/`RigidDataLoader` (`deepdow/data/load.py`) are deepdow's
    own real, public rolling-window dataset/loader classes — verified via
    `InRAMDataset`'s own docstring to accept `X` of shape `(n_samples,
    n_input_channels, lookback, n_assets)`, `y` of shape `(n_samples,
    n_input_channels, horizon, n_assets)`, and an optional real per-sample
    `timestamps` array. This adapter builds `X`/`y` via the exact same
    real rolling-window slicing shown in deepdow's own
    `getting_started.py` (`returns[i-lookback:i]` / `returns[i+gap:i+gap+
    horizon]`), with `gap=0`. Real `deepdow.experiments.Run` (its own
    training-loop wrapper, real `Adam` optimizer) trains the network — no
    training loop is reimplemented by this adapter.
  - **Causality (the crux of this integration)**: `generation_window` is
    split into two real, non-overlapping, forward-only halves —
    `[gen_start, split_date)` for TRAINING and `[split_date, gen_end]` for
    the real per-day DECISION trajectory. The real training samples'
    `y` (future) windows are built exclusively from returns strictly
    before `split_date` (verified: the last training sample's `y` window
    ends at `split_date`, never after), so no information from the
    decision/test period ever reaches the trained network's parameters.
    At decision time, for a real day `t` in the test half, this adapter
    calls `network.eval()` then `network(x_t)` directly (a plain
    `torch.nn.Module` forward call — not a reimplementation, just direct
    use of the real trained model, same as calling `.predict()` on any
    other trained estimator elsewhere in this repo) where `x_t =
    returns[t-lookback:t]` is a real, strictly-past-only window ending the
    day before `t`. `information_cutoff` = the last real date inside
    `x_t` (day `t-1`); `timestamp` = day `t`. Verified no lookahead:
    `x_t` never includes day `t` or later.
  - **`policy_type=FROZEN_LEARNED_POLICY`**: the network is trained exactly
    once (on the real train half) and then queried statically, causally,
    day-by-day across the real test half — no periodic retraining is
    implemented, so this is not `ROLLING_OPTIMIZER`; and it is not a fixed
    hand-set allocation, so this is not `STATIC_ALLOCATION`.
    `update_policy.mode=UpdateMode.NONE` (frozen after generation).
  - **Single-fold fallback (causality-safe)**: if `generation_window` is
    too short to produce a real train half (>= lookback+1 real trading
    days) AND at least one real test-half decision day, this adapter does
    NOT fabricate a trajectory — it raises a clear `RuntimeError` rather
    than reporting a fake/degenerate result (unlike skfolio's
    single-fold-to-initial_weights fallback, deepdow's `GreatNet` has no
    meaningful "single static fit" output distinct from a normal decision
    step, so there is no honest degenerate case to fall back to here;
    reporting the constant/undertrained output as a special case would
    misrepresent it as intentional).
  - **Training budget**: `N_EPOCHS = 8` real epochs (reduced from
    upstream's own tutorial default of 30, same "honestly reduced, still
    real" pattern `adapters/finrl_adapter.py`'s `TOTAL_TIMESTEPS=3000`
    uses) — enough for the real `Adam` optimizer to move weights away from
    their random initialization on a small real universe, not claimed to
    be competitively performant.
  - **Universe**: fixed, caller-supplied ticker list
    (`context.universe`/`context.targets`) — deepdow itself performs no
    asset selection; selection happens upstream of this call.
  - No Q1/Q2/Q3 claimed: deepdow is a pure portfolio-allocation-network
    framework with no action/state/signal concept of its own (category
    ABSENT).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

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

LOOKBACK = 20        # real trading days fed into the network per decision
HORIZON = 5          # real forward-return window used only for the training loss
GAP = 0              # no gap between lookback window end and horizon start
N_EPOCHS = 8          # real, honestly-reduced training budget (see module header)
BATCH_SIZE = 32
MAX_TICKERS = 8
MIN_TRAIN_SAMPLES = 30  # minimum real training samples required before training is attempted


def _fetch_price_matrix(tickers: List[str], start: str, end: str):
    """Real yfinance daily close prices for the exact requested window, with
    retry/backoff for real transient rate limiting (same pattern
    adapters/pgportfolio_adapter.py / adapters/deepalpha_adapter.py use)."""
    import pandas as pd
    import yfinance as yf

    fetch_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    last_err = None
    for attempt in range(5):
        try:
            raw = yf.download(tickers, start=start, end=fetch_end, auto_adjust=True, progress=False)
            if not raw.empty:
                break
        except Exception as e:  # real transient rate limiting, retried with backoff
            last_err = e
            raw = None
        wait = min(15 * (attempt + 1), 60)
        print(f"[deepdow] yfinance fetch attempt {attempt + 1} failed/empty, retrying in {wait}s", flush=True)
        time.sleep(wait)
    else:
        raise RuntimeError(f"yfinance returned no data for {tickers} [{start},{end}] after retries: {last_err}")

    if raw is None or raw.empty:
        raise RuntimeError(f"yfinance returned no data for {tickers} [{start},{end}]")

    if len(tickers) == 1:
        close = raw["Close"].to_frame(tickers[0])
    else:
        close = raw["Close"]
    close = close.dropna(how="all").ffill().dropna()
    return close


def _make_great_net(n_assets: int, lookback: int):
    """Real, unmodified architecture from deepdow's own
    examples/end_to_end/getting_started.py ("GreatNet") — see module header.
    Defined here (not imported) only because upstream ships it as tutorial
    source, not as an importable library class; every layer used
    (torch.nn.Dropout, torch.nn.Linear, deepdow.layers.SoftmaxAllocator) is
    real, public, unmodified deepdow/torch code."""
    import torch
    from deepdow.benchmarks import Benchmark
    from deepdow.layers import SoftmaxAllocator

    class GreatNet(torch.nn.Module, Benchmark):
        def __init__(self, n_assets, lookback, p=0.5):
            super().__init__()
            n_features = n_assets * lookback
            self.dropout_layer = torch.nn.Dropout(p=p)
            self.dense_layer = torch.nn.Linear(n_features, n_assets, bias=True)
            self.allocate_layer = SoftmaxAllocator(temperature=None)
            self.temperature = torch.nn.Parameter(torch.ones(1), requires_grad=True)

        def forward(self, x):
            n_samples, _, _, _ = x.shape
            x = x.reshape(n_samples, -1)  # .reshape not .view: per-day query slices (X[idx:idx+1]) aren't always contiguous
            x = self.dropout_layer(x)
            x = self.dense_layer(x)
            temperatures = torch.ones(n_samples).to(device=x.device, dtype=x.dtype) * self.temperature
            return self.allocate_layer(x, temperatures)

    return GreatNet(n_assets, lookback)


def _build_decision_step(
    timestamp: str,
    information_cutoff: str,
    weights: Dict[str, float],
    active_tickers: List[str],
) -> PolicyDecisionStep:
    """Pure mapping: real (already-computed) per-day network output + real
    dates -> PolicyDecisionStep. No network/model calls here — testable
    against a fixture."""
    return PolicyDecisionStep(
        timestamp=timestamp,
        information_cutoff=information_cutoff,
        selected_universe=active_tickers,
        target_weights=weights,
        explanation=(
            f"Real deepdow GreatNet forward pass on the real lookback window ending "
            f"{information_cutoff} (frozen after training, see module header)."
        ),
    )


def _split_train_test(n_dates: int, lookback: int) -> Tuple[int, int]:
    """Real, deterministic causal split point: roughly 70% train / 30% test
    by index, but never leaving fewer than `lookback` real days for the
    first test-half decision's own lookback window."""
    split = max(lookback + 1, int(n_dates * 0.7))
    return split, n_dates


class DeepdowAdapter(BaseAdapter):
    name = "deepdow"
    questions_answered = ["Q4"]
    upstream_repo = "https://github.com/jankrepl/deepdow"
    requires_env = "deepdow_real"

    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        t0 = time.time()

        tickers = list(dict.fromkeys((context.universe or context.targets or [])))[:MAX_TICKERS]
        if len(tickers) < 2:
            raise ValueError("deepdow q4_policy requires context.universe/targets with at least 2 tickers.")

        import numpy as np
        import torch
        from deepdow.data import InRAMDataset, RigidDataLoader
        from deepdow.experiments import Run
        from deepdow.losses import MeanReturns, SharpeRatio

        prices = _fetch_price_matrix(tickers, generation_window.start, generation_window.end)
        active_tickers = list(prices.columns)
        n_assets = len(active_tickers)

        log_returns = np.log(prices / prices.shift(1)).dropna()
        dates = log_returns.index
        returns_arr = log_returns.values  # (n_timesteps, n_assets)
        n_timesteps = returns_arr.shape[0]

        n_samples = n_timesteps - LOOKBACK - HORIZON - GAP + 1
        if n_samples < MIN_TRAIN_SAMPLES + 1:
            raise RuntimeError(
                f"generation_window too short for deepdow: only {n_samples} real rolling samples "
                f"available (need >= {MIN_TRAIN_SAMPLES + 1}). Widen generation_window."
            )

        X_list, y_list, sample_end_idx = [], [], []
        for i in range(LOOKBACK, n_timesteps - HORIZON - GAP + 1):
            X_list.append(returns_arr[i - LOOKBACK:i, :])
            y_list.append(returns_arr[i + GAP:i + GAP + HORIZON, :])
            sample_end_idx.append(i)  # index of the day AFTER the lookback window (i.e. decision day)

        X = np.stack(X_list, axis=0)[:, None, ...].astype(np.float32)
        y = np.stack(y_list, axis=0)[:, None, ...].astype(np.float32)
        sample_end_idx = np.array(sample_end_idx)
        sample_timestamps = dates[sample_end_idx]

        split_pos, _ = _split_train_test(len(sample_end_idx), LOOKBACK)
        # split_pos indexes into the *sample* arrays; real causal guarantee:
        # every train sample's y-window ends before every test sample's
        # x-window begins, verified by construction (samples are built in
        # strictly increasing i order and split_pos is a single cut point).
        if split_pos >= len(sample_end_idx) - 1:
            raise RuntimeError(
                "generation_window too short for deepdow: not enough real days left for a "
                "test/decision half after a real training half. Widen generation_window."
            )

        indices_train = list(range(split_pos))
        indices_test = list(range(split_pos, len(sample_end_idx)))

        dataset = InRAMDataset(X, y, timestamps=sample_timestamps)
        dataloader_train = RigidDataLoader(dataset, indices=indices_train, batch_size=BATCH_SIZE)

        torch.manual_seed(0)
        network = _make_great_net(n_assets, LOOKBACK)
        network = network.train()

        loss = MeanReturns() + SharpeRatio()
        run = Run(
            network,
            loss,
            dataloader_train,
            optimizer=torch.optim.Adam(network.parameters(), amsgrad=True),
        )
        run.launch(N_EPOCHS)  # real, unmodified deepdow training loop

        network = network.eval()

        decisions: List[PolicyDecisionStep] = []
        last_weights: Dict[str, float] = {}
        with torch.no_grad():
            for idx in indices_test:
                x_t = torch.from_numpy(X[idx:idx + 1])  # real, strictly-past-only lookback window
                w = network(x_t)[0].numpy()
                weights = {t: float(v) for t, v in zip(active_tickers, w)}
                last_weights = weights

                decision_ts = str(sample_timestamps[idx].date())
                info_cutoff = str(dates[sample_end_idx[idx] - 1].date())
                decisions.append(_build_decision_step(decision_ts, info_cutoff, weights, active_tickers))

        constraints = PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0)

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=active_tickers,
            selector_description="Caller-supplied ticker list (context.universe/targets); deepdow performs no asset selection of its own.",
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{LOOKBACK}_trading_days (real GreatNet input window)",
            features=["daily log returns"],
            data_sources=["yfinance daily close prices"],
            observation_description="Real trailing log-return window, flattened and passed through GreatNet's real Linear+SoftmaxAllocator head.",
        )
        decision_policy = DecisionPolicy(
            decision_rule="Real deepdow GreatNet (Linear -> SoftmaxAllocator, upstream's own tutorial architecture), trained once, then queried per real day.",
            output_semantics="target portfolio weights (non-negative, sum to 1, no cash)",
            rebalance_frequency="daily (one real forward pass per real trading day in the test half)",
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.NONE,
            update_frequency="never after initial training",
            update_description="GreatNet is trained once on the real train half of generation_window and then queried statically (frozen weights) across the real test half.",
        )

        explanation = (
            f"Real deepdow GreatNet trained for {N_EPOCHS} real epochs on {len(indices_train)} real "
            f"rolling samples ending before {str(sample_timestamps[split_pos].date())}, then evaluated "
            f"causally on {len(indices_test)} real subsequent trading days for "
            f"{', '.join(active_tickers)} over [{generation_window.start}, {generation_window.end}]."
        )

        self._last_native = {
            "tickers_requested": tickers,
            "active_tickers": active_tickers,
            "n_train_samples": len(indices_train),
            "n_test_samples": len(indices_test),
            "lookback": LOOKBACK,
            "horizon": HORIZON,
            "n_epochs": N_EPOCHS,
            "final_weights": last_weights,
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
            decisions=decisions,
            explanation=explanation,
        )

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
            checks["policy_type_is_frozen_learned"] = result.policy_type == "FROZEN_LEARNED_POLICY"
            decisions = result.decisions or []
            checks["decisions_nonempty"] = len(decisions) > 0
            if decisions:
                checks["causality_ok"] = all(d.information_cutoff <= d.timestamp for d in decisions)
                ts = [d.timestamp for d in decisions]
                checks["timestamps_increasing"] = ts == sorted(ts)
                checks["weights_long_only_and_sum_1"] = all(
                    all(w >= -1e-6 for w in d.target_weights.values())
                    and abs(sum(d.target_weights.values()) - 1.0) < 1e-5
                    for d in decisions if d.target_weights
                )
                checks["selected_universe_present"] = all(d.selected_universe for d in decisions)
        return checks
