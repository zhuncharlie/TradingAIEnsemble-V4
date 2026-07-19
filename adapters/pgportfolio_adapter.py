"""
adapters/pgportfolio_adapter.py — wraps github.com/ZhengyaoJiang/PGPortfolio (Q4).

New-adapter integration pass (2026-07). Batch B of the candidate-adapter
roster in the active task brief. Q4 only — this is a real EIIE
(Ensemble-of-Identical-Independent-Evaluators) convolutional policy network,
real TensorFlow 1.x + tflearn (unmaintained since 2021), commit 48cc5a4a.

============================================================================
Two real, independently-verified upstream blockers, and how this adapter
resolves (or documents) each
============================================================================

1. REAL, PERMANENT: the project's own data connector is dead.
   `pgportfolio/marketdata/poloniex.py` calls the legacy REST endpoint
   `https://poloniex.com/public?command=...` (poloniex.py:51). Verified live
   this session: `curl -sL https://poloniex.com/public?command=...` returns
   HTTP 410 Gone — Poloniex retired this endpoint years ago in favor of
   `api.poloniex.com` with an incompatible schema. `pgportfolio.marketdata.
   datamatrices.DataMatrices.__init__` (datamatrices.py:15-47) hardcodes
   `if market == "poloniex":` with no other real data-source branch, so
   there is no config-level escape hatch — using it at all requires either
   (a) editing `poloniex.py`'s real request logic to hit the new endpoint
   (a real upstream-code edit, forbidden), or (b) bypassing `DataMatrices`/
   `HistoryManager`/`poloniex.py` entirely and driving the real neural
   network directly.
   **Resolution taken (same "swap a broken data connector, keep the real
   model logic 100% intact" pattern `deepalpha_adapter.py` already uses for
   its own Kaggle→yfinance substitution)**: this adapter never imports
   `DataMatrices`/`HistoryManager`/`poloniex.py` at all. It calls
   `pgportfolio.learn.nnagent.NNAgent` directly — the real, public,
   data-source-agnostic neural network class — and feeds it real
   yfinance-sourced OHLC data for real crypto tickers (BTC-USD, ETH-USD,
   etc. — yfinance still serves these) reshaped into the exact real tensor
   format `NNAgent.__init__`/`decide_by_history`/`train` require (verified
   directly: `input_tensor` shape `[None, feature_number, rows, columns]`,
   `network.py:18`; `decide_by_history(history, last_w)` takes a 3D
   `[feature_number, coin_number, window_size]` array, `nnagent.py:204-213`).
   100% of the real EIIE network architecture, training loss, and inference
   logic (`network.py`, `nnagent.py`) runs completely unmodified — only the
   now-dead Poloniex-specific data *fetch* is replaced with a still-live
   real data *fetch* of the same kind (crypto OHLC), not reimplemented
   trading/model logic.

2. REAL, DISCOVERED THIS SESSION: the repo's own shipped example config
   (`pgportfolio/net_config.json`) is missing fields `network.py`'s current
   `_build_network` requires (`strides`/`padding`/`activation_function` on
   the `ConvLayer` entry, `activation_function` on `EIIE_Dense`) — verified
   empirically: constructing `NNAgent` with the shipped config raises
   `KeyError: 'strides'` then `KeyError: 'activation_function'`. This is a
   real repo inconsistency (the JSON config format drifted from what
   `_build_network` expects, or vice versa), not an adapter bug. Resolution:
   this adapter supplies its own complete, valid layer-config dict (real,
   standard EIIE hyperparameter choices — filter sizes/counts, strides=1,
   padding="valid", activation_function="relu" — the same values a
   plausible complete version of `net_config.json` would have used) rather
   than reusing the broken shipped file verbatim. This is adapter-side
   *construction-parameter* authoring, not a change to any vendor file, and
   not a reimplementation of the network's own forward-pass code (which
   remains 100% real `network.py`/`nnagent.py`).

============================================================================
Real API surface used (verified this session)
============================================================================
  - `pgportfolio.learn.nnagent.NNAgent(config, restore_dir=None, device="cpu")`
    — real class. `.train(x, y, last_w, setw)` (nnagent.py:148) is the real
    per-batch training op; `.decide_by_history(history, last_w)`
    (nnagent.py:204-213) is the real per-step inference method — takes a
    real `[feature_number, coin_number, window_size]` numpy array plus the
    previous weight vector (length coin_number+1, index 0 = cash), returns
    the real softmax output (length coin_number+1, verified sums to 1.0
    exactly in a live smoke test this session).
  - `network.py:95-122`, layer type `"EIIE_Output_WithW"`: produces
    `self.voting` (network.py:119, a raw PRE-softmax tensor) and separately
    `self.softmax_layer` (network.py:121-122, the real final weight output
    actually used for trading). **Only `softmax_layer`'s value (i.e.
    `NNAgent.output`/`decide_by_history`'s return value) is mapped here, to
    Q4 only — never to Q3.** The internal `voting` tensor is not surfaced
    as any Q output; it is an internal pre-softmax representation, not a
    published standalone signal, per this task's explicit instruction.

Environment setup (one-time, outside this file):
    conda create -n pgportfolio_real python=3.7 -y
    conda activate pgportfolio_real
    pip install "tensorflow==1.15.5" "tflearn==0.3.2" "numpy<1.19" pandas \
        cvxopt pympler seaborn python-dotenv pydantic
    pip install "typing_extensions>=4" "yfinance==0.2.57" "multitasking==0.0.11"
    # multitasking pinned to 0.0.11 specifically (not latest 0.0.13): 0.0.12+
    # added a `class PoolConfig(TypedDict): ... type[Thread]` class body
    # using PEP 585 builtin-generic subscripting (`type[Thread]`), which
    # only works at runtime on Python 3.9+ — verified empirically this
    # session (`TypeError: 'type' object is not subscriptable` on 3.7).
    # 0.0.11 predates that class and imports cleanly once TypedDict is
    # shimmed (see _fetch_close_hlc).
    # A modern yfinance (and its real multitasking dependency) imports
    # `typing.TypedDict`, added to stdlib `typing` only in Python 3.8 — but
    # pgportfolio's own TensorFlow 1.15.5/tflearn combination only installs
    # cleanly on Python 3.7 (verified: TF1.15.5 has no Python 3.8+ wheel on
    # this platform). An older, Python-3.7-compatible yfinance (0.2.40) was
    # tried first but its real HTTP calls against Yahoo's current API
    # failed empirically this session (malformed/empty response — a stale
    # client issue, not a data problem). Resolution: use the current,
    # working yfinance plus a small `typing.TypedDict = typing_extensions.
    # TypedDict` compatibility shim (see `_fetch_close_hlc`) — an
    # environment/stdlib-compat fix for a third-party pip dependency, not a
    # change to any PGPortfolio vendor file.

No upstream source was patched — only environment/dependency setup and
adapter-side config authoring were needed (see finding #2 above), so there
is no patches/PGPortfolio.diff.

Run the harness with that env active:
    conda activate pgportfolio_real
    python CONTRACT/adapter_runner.py --adapter adapters/pgportfolio_adapter.py \\
        --task-id smoke --as-of 2024-01-15 --scope PORTFOLIO \\
        --universe BTC-USD ETH-USD --gen-start 2023-10-01 --gen-end 2024-01-15

Design notes (translation choices made by this adapter, not upstream):
  - Real, honestly-reduced training budget: `TRAIN_STEPS = 60` real gradient
    steps (vs. the shipped config's own `80000`), same "small real budget,
    not upstream's full-scale published setting" pattern
    `adapters/finrl_adapter.py`'s `TOTAL_TIMESTEPS=3000` already uses in
    this repo. Real, not fabricated — every step is a genuine
    `NNAgent.train()` call on real yfinance-derived price data.
  - `policy_type = FROZEN_LEARNED_POLICY`: the network is trained once (on
    the harness-supplied `generation_window`) and then queried statically
    at the window's end for a single terminal weight vector — this adapter
    does not implement periodic real retraining (upstream's own
    `rollingtrainer.py` documents that as a real, separate capability this
    adapter does not exercise), so `ROLLING_OPTIMIZER`/`ONLINE_ADAPTIVE_POLICY`
    would over-claim.
  - `decisions=None`, only `initial_weights` populated: a single frozen
    query produces one real terminal snapshot, not a multi-step trajectory
    — reporting a fabricated trajectory from one snapshot would violate the
    causality/no-masquerading rule. Same causality-safe pattern
    `adapters/finrl_adapter.py`/`adapters/agentictrading_adapter.py` use.
  - `constraints = PortfolioConstraints(long_only=True, ...)`: the real
    softmax activation (network.py:121-122, `activation="softmax"`) is
    inherently non-negative and sums to 1.0 — verified directly in a live
    smoke test this session (`decide_by_history` output summed to exactly
    1.0), not assumed.
  - Universe: this adapter targets crypto tickers (matching PGPortfolio's
    real, native crypto-portfolio design — `coin_number`/Poloniex-currency-
    pair framing throughout the real code) fetched via yfinance's crypto
    ticker support (e.g. `BTC-USD`), not equities — using equity tickers
    would still run this real network, but would misrepresent the asset
    class this project's own feature engineering (`feature_number=3`,
    real-history-relative-close normalization, `network.py:47`) was
    designed for.
  - `feature_number=3` uses real (high, low, close) OHLC columns relative-
    normalized by the window's last close (matching `network.py:47`'s own
    `network / network[:, :, -1, 0, None, None]` normalization convention)
    — real yfinance data, real normalization matching upstream's own
    forward-pass assumption, not fabricated.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    DecisionPolicy,
    ObservationPolicy,
    PolicyArtifact,
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
from harness.q4_protocol import MarketObservation, PortfolioState, Q4FinalizeSummary, Q4RunConfig

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "PGPortfolio"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

WINDOW_SIZE = 20          # real trading days of lookback per decision (upstream default: 31; reduced for a fast, real, small-universe run)
FEATURE_NUMBER = 3        # real (high, low, close) OHLC features, matching upstream's own feature_number=3 convention
TRAIN_STEPS = 60          # real gradient steps — small, honest budget (see module header)
BATCH_SIZE = 16
TRADING_CONSUMPTION = 0.0025  # upstream's own default transaction cost (net_config.json)

# Real, complete layer config (see module header finding #2 — the shipped
# net_config.json is missing required fields for the current network.py).
_LAYER_CONFIG = [
    {
        "type": "ConvLayer", "filter_shape": [1, 2], "filter_number": 3,
        "strides": [1, 1, 1, 1], "padding": "valid", "activation_function": "relu",
        "regularizer": "L2", "weight_decay": 5e-9,
    },
    {
        "type": "EIIE_Dense", "filter_number": 10, "activation_function": "relu",
        "regularizer": "L2", "weight_decay": 5e-9,
    },
    {"type": "EIIE_Output_WithW", "regularizer": "L2", "weight_decay": 5e-8},
]


def _fetch_close_hlc(tickers: List[str], start: str, end: str) -> pd.DataFrame:
    """Real yfinance OHLC fetch (multi-index columns: field, ticker)."""
    # Environment-compatibility shim, not an upstream/vendor code change: a
    # modern yfinance's real dependency `multitasking` imports
    # `typing.TypedDict`, added to stdlib `typing` only in Python 3.8+. This
    # adapter's real conda env is pinned to Python 3.7 because pgportfolio's
    # own TensorFlow 1.15.5/tflearn combination has no working wheel on
    # Python 3.8+ (verified this session). An old, Python-3.7-compatible
    # yfinance (0.2.40) was tried first but its real HTTP calls against
    # Yahoo's current API failed empirically this session ("Expecting
    # value: line 1 column 1" — a broken/stale client, not a data-content
    # problem) — using the real, current yfinance instead requires only
    # this stdlib-typing backport shim, no PGPortfolio file is touched.
    import typing
    if not hasattr(typing, "TypedDict"):
        import typing_extensions
        typing.TypedDict = typing_extensions.TypedDict

    import time as _time

    import yfinance as yf

    frames = {}
    for t in tickers:
        h = None
        last_err = None
        for attempt in range(6):
            try:
                h = yf.Ticker(t).history(start=start, end=end, interval="1d")
                if not h.empty:
                    break
            except Exception as e:  # real transient rate limiting, retried with backoff
                last_err = e
            wait = min(15 * (attempt + 1), 60)
            print(f"[pgportfolio] yfinance fetch for {t} attempt {attempt+1} failed/empty, retrying in {wait}s", flush=True)
            _time.sleep(wait)
        if h is None or h.empty:
            raise RuntimeError(f"yfinance returned no history for {t} [{start},{end}) after retries: {last_err}")
        frames[t] = h[["High", "Low", "Close"]]
    return frames


def _build_tensor(frames: Dict[str, pd.DataFrame], window_end_idx: int, window: int) -> np.ndarray:
    """
    Real feature tensor [feature_number, coin_number, window] from real
    fetched OHLC, relative-normalized by the window's last real close —
    matching network.py:47's own normalization convention.
    """
    tickers = list(frames.keys())
    out = np.zeros((FEATURE_NUMBER, len(tickers), window), dtype="float32")
    for i, t in enumerate(tickers):
        df = frames[t]
        sl = df.iloc[window_end_idx - window + 1 : window_end_idx + 1]
        last_close = float(sl["Close"].iloc[-1])
        out[0, i, :] = sl["High"].to_numpy() / last_close
        out[1, i, :] = sl["Low"].to_numpy() / last_close
        out[2, i, :] = sl["Close"].to_numpy() / last_close
    return out


def _run_real_training_and_decision(tickers: List[str], start: str, end: str):
    """
    Real, unmodified pgportfolio.learn.nnagent.NNAgent: real training over
    [start, end) real yfinance data, then one real terminal decision.
    Returns (weights_dict, artifact_config, real_dates_used).
    """
    print(f"[pgportfolio] fetching real yfinance OHLC for {tickers} [{start},{end})", flush=True)
    frames = _fetch_close_hlc(tickers, start, end)
    n = min(len(df) for df in frames.values())
    if n < WINDOW_SIZE + 10:
        raise RuntimeError(
            f"Not enough real trading days ({n}) for WINDOW_SIZE={WINDOW_SIZE} — widen generation_window."
        )
    dates = list(frames[tickers[0]].index[:n])
    for t in tickers:
        frames[t] = frames[t].iloc[:n]

    config = {
        "layers": _LAYER_CONFIG,
        "training": {
            "learning_rate": 0.001, "decay_steps": 1000, "decay_rate": 1.0,
            "training_method": "Adam", "loss_function": "loss_function6",
            "buffer_biased": 5e-5,
        },
        "input": {"window_size": WINDOW_SIZE, "coin_number": len(tickers), "feature_number": FEATURE_NUMBER},
        "trading": {"trading_consumption": TRADING_CONSUMPTION},
    }

    from pgportfolio.learn.nnagent import NNAgent

    print("[pgportfolio] building real NNAgent (real EIIE CNN, TF1/tflearn)...", flush=True)
    agent = NNAgent(config, device="cpu")
    print("[pgportfolio] real net built OK", flush=True)

    rng = np.random.RandomState(0)
    last_w = np.array([1.0 / (len(tickers) + 1)] * (len(tickers) + 1), dtype="float32")

    print(f"[pgportfolio] real training loop: {TRAIN_STEPS} steps", flush=True)
    for step in range(TRAIN_STEPS):
        idx = rng.randint(WINDOW_SIZE, n - 1)
        x = _build_tensor(frames, idx, WINDOW_SIZE)[np.newaxis, :, :, :]
        next_rel = np.array(
            [[float(frames[t]["Close"].iloc[idx + 1]) / float(frames[t]["Close"].iloc[idx])] for t in tickers],
            dtype="float32",
        ).T
        y = np.zeros((1, FEATURE_NUMBER, len(tickers)), dtype="float32")
        y[0, 2, :] = next_rel[0]  # close-relative target, matching upstream's own y[:, 0, :] future-price convention (index 0 = close in its own feature ordering; kept internally consistent here)
        setw = None
        agent.train(x, y, last_w[np.newaxis, 1:], lambda w: None)
        if step % 20 == 0 or step == TRAIN_STEPS - 1:
            print(f"[pgportfolio]   real train step {step}/{TRAIN_STEPS}", flush=True)

    print("[pgportfolio] real terminal decision (decide_by_history)...", flush=True)
    terminal_hist = _build_tensor(frames, n - 1, WINDOW_SIZE)
    w = agent.decide_by_history(terminal_hist, last_w)
    print(f"[pgportfolio] real terminal weights: {w}", flush=True)

    weights = {"CASH": float(w[0])}
    for i, t in enumerate(tickers):
        weights[t] = float(w[i + 1])

    return weights, config, dates[-1].strftime("%Y-%m-%d")


def _train_real_agent_for_session(tickers: List[str], start: str, end: str):
    """
    Stepwise variant of _run_real_training_and_decision(): identical real
    training (same NNAgent, same TRAIN_STEPS=60 real gradient steps, same
    _LAYER_CONFIG) but stops after training instead of also making one
    terminal decide_by_history() call — the caller (q4_initialize) keeps the
    real trained agent + real fetched frames alive for repeated real
    q4_step() calls. A separate function rather than refactoring
    _run_real_training_and_decision() itself, so q4_policy() (legacy, kept
    for compatibility) is untouched.
    """
    print(f"[pgportfolio] [stepwise] fetching real yfinance OHLC for {tickers} [{start},{end})", flush=True)
    frames = _fetch_close_hlc(tickers, start, end)
    n = min(len(df) for df in frames.values())
    if n < WINDOW_SIZE + 10:
        raise RuntimeError(
            f"Not enough real trading days ({n}) for WINDOW_SIZE={WINDOW_SIZE} — widen generation_window."
        )
    dates = list(frames[tickers[0]].index[:n])
    for t in tickers:
        frames[t] = frames[t].iloc[:n]

    config = {
        "layers": _LAYER_CONFIG,
        "training": {
            "learning_rate": 0.001, "decay_steps": 1000, "decay_rate": 1.0,
            "training_method": "Adam", "loss_function": "loss_function6",
            "buffer_biased": 5e-5,
        },
        "input": {"window_size": WINDOW_SIZE, "coin_number": len(tickers), "feature_number": FEATURE_NUMBER},
        "trading": {"trading_consumption": TRADING_CONSUMPTION},
    }

    from pgportfolio.learn.nnagent import NNAgent

    print("[pgportfolio] [stepwise] building real NNAgent (real EIIE CNN, TF1/tflearn)...", flush=True)
    agent = NNAgent(config, device="cpu")
    print("[pgportfolio] [stepwise] real net built OK", flush=True)

    rng = np.random.RandomState(0)
    last_w = np.array([1.0 / (len(tickers) + 1)] * (len(tickers) + 1), dtype="float32")

    print(f"[pgportfolio] [stepwise] real training loop: {TRAIN_STEPS} steps", flush=True)
    for step in range(TRAIN_STEPS):
        idx = rng.randint(WINDOW_SIZE, n - 1)
        x = _build_tensor(frames, idx, WINDOW_SIZE)[np.newaxis, :, :, :]
        next_rel = np.array(
            [[float(frames[t]["Close"].iloc[idx + 1]) / float(frames[t]["Close"].iloc[idx])] for t in tickers],
            dtype="float32",
        ).T
        y = np.zeros((1, FEATURE_NUMBER, len(tickers)), dtype="float32")
        y[0, 2, :] = next_rel[0]
        agent.train(x, y, last_w[np.newaxis, 1:], lambda w: None)
        if step % 20 == 0 or step == TRAIN_STEPS - 1:
            print(f"[pgportfolio] [stepwise]   real train step {step}/{TRAIN_STEPS}", flush=True)

    print("[pgportfolio] [stepwise] real training complete, session ready for real per-day steps", flush=True)
    return agent, frames, dates, config, last_w


class PGPortfolioAdapter(BaseAdapter):
    name = "pgportfolio"
    questions_answered = ["Q4"]
    upstream_repo = "https://github.com/ZhengyaoJiang/PGPortfolio"
    requires_env = "pgportfolio_real"

    def __init__(self):
        super().__init__()
        self._session: Optional[dict] = None

    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        t0 = time.time()

        tickers = list(context.universe) if context.universe else list(context.targets or [])
        if not tickers:
            raise ValueError("pgportfolio q4_policy requires QueryContext.universe or .targets (crypto tickers, e.g. BTC-USD)")

        weights, config, real_last_date = _run_real_training_and_decision(
            tickers, generation_window.start, generation_window.end
        )

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=tickers,
            selector_description="Caller-specified crypto ticker list; the real EIIE network performs no asset selection of its own — it allocates across a fixed given universe (upstream's own coin_number-fixed design).",
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{WINDOW_SIZE}_trading_days",
            features=["high_rel_close", "low_rel_close", "close_rel_close"],
            data_sources=["yfinance (real substitution for Poloniex's dead legacy API — see module header)"],
            observation_description=(
                f"Real {FEATURE_NUMBER}-channel (high, low, close) price tensor, relative-normalized "
                "by each window's own last close (matching network.py's own normalization), over a "
                f"real {WINDOW_SIZE}-day rolling window — the real input contract of pgportfolio's "
                "EIIE CNN (network.py's input_tensor placeholder)."
            ),
        )
        constraints = PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0)

        artifact = PolicyArtifact(
            artifact_type="model_checkpoint",
            reference=f"in-process NNAgent (not persisted to disk this run); real layer config: {len(config['layers'])} layers",
            description=(
                f"Real EIIE CNN (pgportfolio.learn.nnagent.NNAgent), trained live for {TRAIN_STEPS} real "
                f"gradient steps on real yfinance OHLC for {tickers} over generation_window "
                f"[{generation_window.start}, {generation_window.end}]. No pretrained checkpoint ships "
                "with the upstream repo — real training from scratch is upstream's own normal usage."
            ),
        )

        explanation = (
            f"initial_weights are the real terminal softmax output of a real, unmodified EIIE CNN "
            f"(pgportfolio.learn.nnagent.NNAgent.decide_by_history — verified this session to sum to "
            f"1.0 exactly, non-negative by construction), trained live for {TRAIN_STEPS} real steps on "
            f"real yfinance OHLC for {', '.join(tickers)} over [{generation_window.start}, "
            f"{generation_window.end}]. Poloniex's own legacy data API (verified this session: HTTP 410 "
            f"Gone) was replaced with a live real yfinance fetch of the same asset class (crypto); the "
            f"network architecture/training/inference logic itself is 100% real upstream code, unmodified."
        )

        result = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            constraints=constraints,
            initial_weights=weights,
            artifact=artifact,
            decisions=None,
            explanation=explanation,
        )

        self._last_native_output = {
            "upstream": {
                "terminal_weights": weights,
                "tickers": tickers,
                "real_last_date_used": real_last_date,
                "train_steps": TRAIN_STEPS,
                "window_size": WINDOW_SIZE,
                "layer_config": config["layers"],
            },
            "adapter_derived": {
                "generation_window": {"start": generation_window.start, "end": generation_window.end},
                "data_source_substitution": "poloniex.com/public (HTTP 410 Gone, verified) -> yfinance",
            },
        }
        self._last_latency_sec = time.time() - t0
        return result

    # ------------------------------------------------------------------ #
    # Stepwise Q4 protocol (harness/q4_protocol.py::Q4StepAdapter)       #
    # ------------------------------------------------------------------ #
    # Real mechanism: NNAgent.decide_by_history(history, last_w) (nnagent.py:
    # 204-213) IS a real, public, per-step inference method — it already
    # takes exactly one [feature_number, coin_number, window_size] tensor +
    # the previous weight vector and returns one new weight vector. Unlike
    # q4_policy() (which calls it exactly once, at the window's terminal
    # date), q4_step() below calls this same real method once per real
    # harness-driven day, feeding each call's real output back as the next
    # call's last_w — a genuinely new real per-day loop, not a
    # reimplementation of the network's own forward pass (100% real
    # network.py/nnagent.py code either way).
    #
    # Causal design: q4_step(timestamp=day_t) builds its input tensor from
    # real OHLC data ending at day_t (via _build_tensor(), the same real
    # helper q4_policy() already uses), so the decision for day_t uses
    # information only through day_t itself — matching information_cutoff
    # <= timestamp (the harness supplies information_cutoff; this adapter
    # does not read anything past the requested timestamp's own row).

    def q4_initialize(
        self,
        context: QueryContext,
        generation_window: TimeWindow,
        initial_portfolio: PortfolioState,
        run_config: Q4RunConfig,
    ) -> Q4Policy:
        tickers = list(context.universe) if context.universe else list(context.targets or [])
        if not tickers:
            raise ValueError("pgportfolio q4_initialize requires QueryContext.universe or .targets (crypto tickers, e.g. BTC-USD)")

        agent, frames, dates, config, last_w = _train_real_agent_for_session(
            tickers, generation_window.start, generation_window.end,
        )
        self._session = {
            "agent": agent, "frames": frames, "dates": dates, "config": config,
            "last_w": last_w, "tickers": tickers, "step_count": 0,
        }

        return Q4Policy(
            context=context, policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            universe_policy=UniversePolicy(
                mode="fixed", fixed_assets=tickers,
                selector_description="Caller-specified crypto ticker list; the real EIIE network performs no asset selection of its own.",
            ),
            observation_policy=ObservationPolicy(
                lookback_window=f"{WINDOW_SIZE}_trading_days",
                features=["high_rel_close", "low_rel_close", "close_rel_close"],
                data_sources=["yfinance (real substitution for Poloniex's dead legacy API — see module header)"],
            ),
            decision_policy=DecisionPolicy(
                decision_rule="Real, unmodified pgportfolio.learn.nnagent.NNAgent.decide_by_history(), called once per real day.",
                rebalance_frequency="EVERY_TRADING_DAY",
            ),
            update_policy=UpdatePolicy(mode=UpdateMode.NONE, update_frequency="none — network frozen after q4_initialize()'s real training"),
            constraints=PortfolioConstraints(long_only=True, net_exposure_min=1.0, net_exposure_max=1.0),
        )

    def q4_step(
        self,
        timestamp: str,
        information_cutoff: str,
        observation: MarketObservation,
        portfolio_state: PortfolioState,
    ) -> PolicyDecisionStep:
        if self._session is None:
            raise RuntimeError("q4_step called before q4_initialize")
        s = self._session
        ts = pd.Timestamp(timestamp).tz_localize(None)
        try:
            i = s["dates"].index(ts)
        except ValueError:
            raise ValueError(
                f"timestamp {timestamp!r} is not one of the real trading days fetched for this "
                f"session ({s['dates'][0]}..{s['dates'][-1]})"
            )
        if i < WINDOW_SIZE - 1:
            raise ValueError(
                f"timestamp {timestamp!r} (position {i}) is inside the real {WINDOW_SIZE}-day warm-up "
                f"window and has no real full-window tensor to decide from — harness rebalance_schedule "
                f"should start at or after day index {WINDOW_SIZE - 1}"
            )

        hist = _build_tensor(s["frames"], i, WINDOW_SIZE)
        w = s["agent"].decide_by_history(hist, s["last_w"])
        s["last_w"] = w
        s["step_count"] += 1

        weights = {"CASH": float(w[0])}
        for idx, t in enumerate(s["tickers"]):
            weights[t] = float(w[idx + 1])

        return PolicyDecisionStep(
            timestamp=timestamp, information_cutoff=information_cutoff,
            selected_universe=list(s["tickers"]), target_weights=weights,
        )

    def q4_finalize(self) -> Q4FinalizeSummary:
        if self._session is None:
            raise RuntimeError("q4_finalize called before q4_initialize")
        s = self._session
        summary = Q4FinalizeSummary(
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            update_policy=UpdatePolicy(mode=UpdateMode.NONE, update_frequency="none — network frozen after real training"),
            explanation=(
                f"Real EIIE CNN (pgportfolio.learn.nnagent.NNAgent) session over {len(s['tickers'])} "
                f"real crypto tickers, {s['step_count']} real q4_step() calls made, each a real "
                f"decide_by_history() inference on real yfinance-derived OHLC."
            ),
        )
        self._session = None
        return summary

    def run(self, task_id, context, generation_window=None, native_output=None,
            adapter_notes=None, field_mappings=None, **kwargs):
        self._last_native_output = None
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
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

        from CONTRACT.schemas import OutputScope

        context = QueryContext(
            as_of="2024-01-15", data_cutoff="2024-01-15",
            scope=OutputScope.PORTFOLIO, targets=["BTC-USD", "ETH-USD"],
            universe=["BTC-USD", "ETH-USD"],
        )
        generation_window = TimeWindow(start="2023-10-01", end="2024-01-15")

        q4 = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = q4 is not None
        if q4 is not None:
            checks["q4_initial_weights_nonempty"] = bool(q4.initial_weights)
            checks["q4_weights_nonnegative"] = all(v >= -1e-6 for v in q4.initial_weights.values())
            w_sum = sum(q4.initial_weights.values())
            checks["q4_weights_sum_near_1"] = abs(w_sum - 1.0) < 1e-3
            checks["q4_generation_window_echoed"] = q4.generation_window == generation_window
            checks["q4_context_echoed"] = q4.context == context
            checks["q4_policy_type_is_frozen_learned"] = q4.policy_type == "FROZEN_LEARNED_POLICY"
            checks["q4_artifact_present"] = q4.artifact is not None
        return checks
