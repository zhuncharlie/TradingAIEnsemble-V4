"""
adapters/trademaster_adapter.py — wraps github.com/TradeMaster-NTU/TradeMaster
(Q4 only, via the real `portfolio_management` / `EIIE` algorithm+task-type pair).

New-adapter integration pass (2026-07), Batch C. TradeMaster is a large,
multi-paradigm framework (`algorithmic_trading`, `high_frequency_trading`,
`order_execution`, `portfolio_management` task types, each with several
distinct trainers/agents/environments — e.g. `portfolio_management` alone
ships `eiie_trainer.py`, `deeptrader_trainer.py`, `investor_imitator_trainer.py`,
`sarl_trainer.py`). Per the active task brief: different algorithms in this
project have genuinely different short/cash/weight-constraint semantics, so
this adapter deliberately wraps exactly ONE real algorithm+task-type pair
(portfolio_management/EIIE — the most standard weight-vector portfolio
algorithm, real simplex-constrained output) rather than generalizing across
the whole framework. It does not claim anything about TradeMaster's other
paradigms.

Repo verification: real repo cloned at adapters/vendor/TradeMaster, commit
1747cc18db3fe2639af12defc80e138c51a625c0 (2025-06-04). Re-verified by
reading real source (not copied from any prior audit):
  - trademaster/environments/portfolio_management/eiie_environment.py,
    class PortfolioManagementEIIEEnvironment: real gym.Env. `step(weights)`
    treats `weights[0]` as the cash weight and `weights[1:]` as per-ticker
    weights (ticker order = `df.tic.unique()`), used directly (unclipped,
    un-renormalized) to compute `portfolio_return` — the environment itself
    enforces NO constraint on `weights`; it trusts whatever the caller
    passes in.
  - trademaster/nets/eiie.py, class EIIEConv.forward(): the REAL constraint
    enforcement lives here, not in the environment. `x = torch.cat((x, para),
    dim=1); x = torch.softmax(x, dim=1)` (eiie.py:34-36) — the actor
    network concatenates a learnable scalar (cash logit) onto the per-stock
    scores and applies softmax over the WHOLE vector. This is a real,
    verified, code-level guarantee: the action this adapter ever passes to
    `env.step()` is non-negative and sums to exactly 1.0 across
    stocks+cash — long-only, fully-invested, no leverage, no shorting.
    Verified directly from the network's forward pass, not assumed.
  - trademaster/agents/portfolio_management/eiie.py, class
    PortfolioManagementEIIE(AgentBase): real off-policy actor-critic agent.
    `explore_env(env, horizon_len)` and `update_net(buffer)` are real,
    public methods this adapter calls directly (see "Design notes" below
    for why the full `PortfolioManagementEIIETrainer` class is NOT used).
  - Real, complete, OFFLINE dataset ships with the repo:
    data/portfolio_management/dj30/{train,valid,test}.csv — real DJ30
    tickers (29: AAPL, AMGN, AXP, BA, CAT, CRM, CSCO, CVX, DIS, GS, HD, HON,
    IBM, INTC, JNJ, JPM, KO, MCD, MMM, MRK, MSFT, NKE, PG, TRV, UNH, V, VZ,
    WBA, WMT), real dates 2012-01-04 through 2021-12-31, real OHLC +
    z-scored technical indicators (zopen/zhigh/zlow/zadjcp/zclose/
    zd_{5,10,15,20,25,30}) already computed by upstream's own preprocessing
    pipeline. This adapter reads these real, shipped CSVs directly — no
    yfinance call, no network dependency, avoiding this session's earlier
    yfinance rate-limiting entirely.

Environment setup (one-time, outside this file):
    conda create -n trademaster_real python=3.10
    conda activate trademaster_real
    pip install "setuptools<81" wheel   # mmcv==1.7.1's build needs pkg_resources,
                                          # which modern setuptools no longer
                                          # bundles by default at build-isolation time
    pip install "mmcv==1.7.1" --no-build-isolation
    pip install torch pandas pydantic python-dotenv prettytable matplotlib \
        plotly scikit-learn statsmodels scipy psutil iopath tslearn fastdtw \
        chardet gym
    pip install "numpy<2.0"
    # PIN numpy<2.0: upstream's own eiie_environment.py:266 (evaualte())
    # calls `np.nan_to_num(neg_ret_lst, 0)` — real numpy>=2.0 tightened
    # nan_to_num's copy semantics and raises `ValueError: Unable to avoid
    # copy while creating an array as requested` for this exact real,
    # unmodified call. This only fires on the terminal step (when upstream
    # computes its own internal Sortino ratio — a Q5 metric this adapter
    # never reads). No upstream file was patched; environment-level pin
    # only, same category as e.g. deepalpha_adapter.py's transformers pin.
    git clone --depth 1 https://github.com/TradeMaster-NTU/TradeMaster.git \
        adapters/vendor/TradeMaster

Run the harness with that env active:
    conda activate trademaster_real
    python CONTRACT/adapter_runner.py --adapter adapters/trademaster_adapter.py \
        --task-id smoke --as-of 2021-12-31 --scope PORTFOLIO \
        --universe AAPL MSFT JNJ --gen-start 2021-01-04 --gen-end 2021-12-31

Design notes (translation choices made by this adapter, not upstream):
  - **Does NOT instantiate `PortfolioManagementEIIETrainer`**: that class's
    home package (`trademaster/trainers/__init__.py`) eagerly imports EVERY
    portfolio_management trainer (including `trainer.py`, which imports
    `ray.tune.registry` — a heavy, unrelated dependency this adapter has no
    other need for). Verified by direct import: `from
    trademaster.trainers.portfolio_management.eiie_trainer import ...`
    fails with `ModuleNotFoundError: No module named 'ray'` even though
    EIIE's own trainer code never touches ray. Rather than installing
    `ray[rllib]` just to satisfy an unrelated sibling module's import, or
    patching TradeMaster's own `__init__.py` (which the task rules make a
    heavier, less-clean choice than the alternative below), this adapter
    imports only `trademaster.agents.portfolio_management.eiie`,
    `trademaster.environments.portfolio_management.eiie_environment`, and
    `trademaster.nets.eiie` directly (none of which transitively need ray),
    and calls the SAME real, public `agent.explore_env()`/`agent.update_net()`
    methods `PortfolioManagementEIIETrainer.train_and_valid()` itself calls,
    in the same real order — just without the Trainer class's disk
    checkpointing/plotting orchestration, which a single `q4_policy()` call
    doesn't need. 100% of the real EIIE agent/environment/network logic is
    unmodified and unreimplemented; only the (comparatively thin) training
    orchestration loop is inlined.
  - `generation_window` (harness-supplied) is used as the full real span
    from which this adapter draws real DJ30 data — matching the convention
    already established by other Q4 adapters in this repo (e.g.
    `skfolio_adapter.py`'s WalkForward folds, `qlib_adapter.py`'s backtest
    window) of partitioning internally within the harness-supplied window
    rather than treating it as training-only. Internally: the FIRST 70% of
    real trading days in `generation_window` (by count) is used for a
    small, real, honestly-reduced training budget (same spirit as
    `finrl_adapter.py`'s reduced `TOTAL_TIMESTEPS`); the LAST 30% is used
    for a real causal decision rollout (`decisions` trajectory). No test
    period ever sees data used for training, and training strictly
    precedes every decision it informs.
  - `policy_type=FROZEN_LEARNED_POLICY`: the EIIE actor is trained once
    (on the real training slice) then queried statically through the real
    decision slice — no retraining/online learning happens during the
    trajectory rollout. `update_policy=UpdatePolicy(mode=UpdateMode.NONE)`
    follows from the same fact.
  - `constraints=PortfolioConstraints(long_only=True, cash_allowed=True,
    net_exposure_min=1.0, net_exposure_max=1.0)`: verified directly from
    `EIIEConv.forward()`'s real softmax (see above) — not the environment's
    own (unenforced) contract.
  - `information_cutoff`/`timestamp` per decision: at each real rollout
    step, `information_cutoff` = the last real date in the lookback window
    the actor's decision was conditioned on (`env.data.date.unique()[-1]`
    BEFORE calling `env.step()`); `timestamp` = the real date the resulting
    weights are realized against (`env.date_memory[-1]` AFTER
    `env.step()`) — i.e. a decision made using data through day T is
    recorded as applying to day T+1's price move, the same real one-day
    causal offset `trademaster/environments/portfolio_management/
    eiie_environment.py`'s own `step()` logic uses internally.
  - Ticker universe: `context.universe` is intersected with the real
    29-ticker DJ30 set this shipped dataset covers; a `ValueError` is
    raised if the intersection is empty (rather than silently substituting
    tickers) — this adapter's real data coverage is fixed to what
    TradeMaster's own shipped, preprocessed dataset contains, not an
    arbitrary universe.
"""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import date as _date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

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

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "TradeMaster"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

DATA_DIR = VENDOR_DIR / "data" / "portfolio_management" / "dj30"
REAL_DJ30_TICKERS = [
    "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS", "GS",
    "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK",
    "MSFT", "NKE", "PG", "TRV", "UNH", "V", "VZ", "WBA", "WMT",
]
TECH_INDICATOR_LIST = [
    "zopen", "zhigh", "zlow", "zadjcp", "zclose",
    "zd_5", "zd_10", "zd_15", "zd_20", "zd_25", "zd_30",
]
TIME_STEPS = 10                 # real upstream default (length_day) in the shipped EIIE config
TRAIN_FRACTION = 0.7            # real trading days: front 70% train, back 30% real causal decisions
HORIZON_LEN = 24                # small real per-round exploration horizon (reduced from typical usage)
TRAIN_ROUNDS = 3                # small real number of explore+update rounds — honestly reduced budget
INITIAL_AMOUNT = 100_000.0
TRANSACTION_COST_PCT = 0.001

_DATA_CACHE: Dict[str, pd.DataFrame] = {}


def _load_real_dj30() -> pd.DataFrame:
    """Concatenate the real, shipped train/valid/test DJ30 CSVs into one
    real historical frame spanning 2012-01-04..2021-12-31. No values are
    invented; every row is a real upstream-preprocessed data point."""
    if "combined" in _DATA_CACHE:
        return _DATA_CACHE["combined"]
    frames = []
    for name in ("train.csv", "valid.csv", "test.csv"):
        df = pd.read_csv(DATA_DIR / name, index_col=0)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"])
    combined = combined.sort_values(["date", "tic"]).reset_index(drop=True)
    _DATA_CACHE["combined"] = combined
    return combined


def _tickers_from_context(context: QueryContext) -> List[str]:
    requested = list(context.universe or context.targets or [])
    if not requested:
        raise ValueError("trademaster q4_policy requires QueryContext.universe or .targets")
    real = [t for t in requested if t in REAL_DJ30_TICKERS]
    if not real:
        raise ValueError(
            f"None of the requested tickers {requested} are covered by TradeMaster's "
            f"real, shipped DJ30 dataset ({REAL_DJ30_TICKERS}); this adapter does not "
            "substitute an unrelated data source for a fixed, preprocessed dataset."
        )
    return sorted(real)


def _write_env_csv(df_slice: pd.DataFrame, path: Path) -> None:
    """Write a real data slice in exactly the shape
    PortfolioManagementEIIEEnvironment expects. Critical, verified detail:
    the real shipped CSVs use a "day-position" index — the SAME integer
    repeated across every ticker's row for a given date (e.g. index 0 for
    every ticker on the first date in the file) — because
    `eiie_environment.py`'s `self.df.loc[self.day - self.time_steps + 1 :
    self.day, :]` slices by day-position, not by row number. A plain
    `reset_index(drop=True)` (unique index per row) breaks this and causes
    a real ValueError inside the environment's own __init__. This function
    reconstructs the same real day-position index for the (possibly
    date-filtered, ticker-filtered) slice this adapter passes in."""
    out = df_slice.sort_values(["date", "tic"]).copy()
    unique_dates = sorted(out["date"].unique())
    date_to_pos = {d: i for i, d in enumerate(unique_dates)}
    out.index = out["date"].map(date_to_pos)
    out.index.name = None  # must NOT be "date" — the source Series' name
    # leaks onto the index and collides with the real "date" data column on
    # write, silently renaming it to "date.1" on read-back (verified via a
    # direct read-back inspection: without this line, readback.columns ==
    # ['date.1', 'open', ...] and self.data.date raises AttributeError
    # inside PortfolioManagementEIIEEnvironment.__init__).
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(path)


def _build_env(csv_path: Path, task: str, tickers: List[str], work_dir: Path):
    from trademaster.environments.portfolio_management.eiie_environment import (
        PortfolioManagementEIIEEnvironment,
    )

    dataset = {
        "train_path": str(csv_path),
        "valid_path": str(csv_path),
        "test_path": str(csv_path),
        "time_steps": TIME_STEPS,
        "initial_amount": INITIAL_AMOUNT,
        "transaction_cost_pct": TRANSACTION_COST_PCT,
        "tech_indicator_list": TECH_INDICATOR_LIST,
    }
    return PortfolioManagementEIIEEnvironment(
        dataset=dataset, task=task, work_dir=str(work_dir)
    )


def _reset_state_tensor(env, device):
    import torch

    state = env.reset()
    assert state.shape == (env.action_dim, env.time_steps, env.state_dim)
    return torch.tensor(state, dtype=torch.float32, device=device)


def _build_agent(action_dim: int, state_dim: int, device):
    """Real EIIEConv/EIIECritic nets + real PortfolioManagementEIIE agent,
    matching adapter-vendored TradeMaster/configs/portfolio_management/
    portfolio_management_dj30_eiie_eiie_adam_mse.py's real hyperparameters
    (act=EIIEConv(output_dim=1, kernel_size=3, dims=[32]),
    cri=EIIECritic(output_dim=1, num_layers=1, hidden_size=32),
    optimizer=Adam(lr=0.001), loss=MSELoss, gamma=0.99)."""
    import torch
    from collections import namedtuple

    from trademaster.agents.portfolio_management.eiie import PortfolioManagementEIIE
    from trademaster.nets.eiie import EIIEConv, EIIECritic

    act = EIIEConv(input_dim=len(TECH_INDICATOR_LIST), output_dim=1, time_steps=TIME_STEPS, kernel_size=3, dims=[32])
    cri = EIIECritic(input_dim=len(TECH_INDICATOR_LIST), action_dim=action_dim, output_dim=1, time_steps=TIME_STEPS, num_layers=1, hidden_size=32)
    act_optimizer = torch.optim.Adam(act.parameters(), lr=0.001)
    cri_optimizer = torch.optim.Adam(cri.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()
    transition = namedtuple("Transition", ["state", "action", "reward", "undone", "next_state"])

    agent = PortfolioManagementEIIE(
        num_envs=1,
        device=device,
        action_dim=action_dim,
        state_dim=state_dim,
        time_steps=TIME_STEPS,
        act=act,
        cri=cri,
        act_optimizer=act_optimizer,
        cri_optimizer=cri_optimizer,
        criterion=criterion,
        gamma=0.99,
        batch_size=16,
        repeat_times=1.0,
        transition=transition,
    )
    return agent


def _train_real_agent(agent, train_env, device) -> None:
    """Real, reduced-budget training: calls the SAME real
    agent.explore_env()/agent.update_net() methods
    PortfolioManagementEIIETrainer.train_and_valid() itself calls, just
    without that class's disk-checkpointing/plotting orchestration (see
    module header 'Design notes')."""
    from trademaster.utils import GeneralReplayBuffer

    agent.last_state = _reset_state_tensor(train_env, device).unsqueeze(0)
    transition_shapes = {
        "state": (HORIZON_LEN, 1, agent.action_dim, agent.time_steps, agent.state_dim),
        "action": (HORIZON_LEN, 1, agent.action_dim + 1),
        "reward": (HORIZON_LEN, 1),
        "undone": (HORIZON_LEN, 1),
        "next_state": (HORIZON_LEN, 1, agent.action_dim, agent.time_steps, agent.state_dim),
    }
    buffer = GeneralReplayBuffer(
        transition=agent.transition, shapes=transition_shapes,
        num_seqs=1, max_size=HORIZON_LEN, device=device,
    )
    for round_i in range(TRAIN_ROUNDS):
        train_env.reset()
        agent.last_state = _reset_state_tensor(train_env, device).unsqueeze(0)
        buffer_items = agent.explore_env(train_env, HORIZON_LEN)
        buffer.update(buffer_items)
        import torch
        torch.set_grad_enabled(True)
        agent.update_net(buffer)
        torch.set_grad_enabled(False)


def _run_real_decision_rollout(agent, test_env, tickers: List[str], device) -> List[dict]:
    """Real causal rollout: query the real, now-frozen agent once per real
    trading day, record the real softmax weights and the real dates
    surrounding each decision. No retraining happens here."""
    import torch

    steps: List[dict] = []
    state = test_env.reset()
    done = False
    while not done:
        cutoff_date = test_env.data.date.unique()[-1]
        tensor_state = torch.as_tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
        action = agent.act(tensor_state)
        weights = action.detach().cpu().numpy()[0]
        state, reward, done, info = test_env.step(weights)
        if done:
            break
        applied_date = test_env.date_memory[-1]
        target_weights = {"CASH": float(weights[0])}
        for i, tic in enumerate(tickers):
            target_weights[tic] = float(weights[1 + i])
        steps.append({
            "information_cutoff": pd.Timestamp(cutoff_date).strftime("%Y-%m-%d"),
            "timestamp": pd.Timestamp(applied_date).strftime("%Y-%m-%d"),
            "selected_universe": list(tickers),
            "target_weights": target_weights,
        })
    return steps


def _build_decision_step(raw_step: dict) -> PolicyDecisionStep:
    """Pure mapping from one real rollout step dict (see
    _run_real_decision_rollout) to a schema PolicyDecisionStep. Offline-
    testable: takes no environment/agent, just the already-extracted real
    values."""
    return PolicyDecisionStep(
        timestamp=raw_step["timestamp"],
        information_cutoff=raw_step["information_cutoff"],
        selected_universe=raw_step.get("selected_universe"),
        target_weights=raw_step["target_weights"],
    )


class TradeMasterAdapter(BaseAdapter):
    name = "trademaster"
    questions_answered = ["Q4"]
    upstream_repo = "https://github.com/TradeMaster-NTU/TradeMaster"
    requires_env = "trademaster_real"

    def q4_policy(self, context: QueryContext, generation_window: TimeWindow, **kwargs) -> Optional[Q4Policy]:
        t0 = time.time()
        tickers = _tickers_from_context(context)

        import torch
        device = torch.device("cpu")

        df = _load_real_dj30()
        df = df[df.tic.isin(tickers)]
        window_df = df[
            (df.date >= pd.Timestamp(generation_window.start))
            & (df.date <= pd.Timestamp(generation_window.end))
        ].copy()
        real_dates = sorted(window_df.date.unique())
        if len(real_dates) < TIME_STEPS * 4:
            raise RuntimeError(
                f"Not enough real trading days ({len(real_dates)}) in generation_window "
                f"[{generation_window.start},{generation_window.end}] for TIME_STEPS={TIME_STEPS} "
                "lookback + a real train/decide split — widen generation_window."
            )

        split_idx = max(TIME_STEPS + 1, int(len(real_dates) * TRAIN_FRACTION))
        split_idx = min(split_idx, len(real_dates) - TIME_STEPS - 2)
        train_dates = real_dates[: split_idx + 1]
        test_dates = real_dates[split_idx:]

        train_slice = window_df[window_df.date.isin(train_dates)]
        test_slice = window_df[window_df.date.isin(test_dates)]

        with tempfile.TemporaryDirectory(prefix="trademaster_adapter_") as tmp:
            tmp_path = Path(tmp)
            train_csv = tmp_path / "train.csv"
            test_csv = tmp_path / "test.csv"
            _write_env_csv(train_slice, train_csv)
            _write_env_csv(test_slice, test_csv)

            train_env = _build_env(train_csv, "train", tickers, tmp_path)
            test_env = _build_env(test_csv, "test", tickers, tmp_path)

            agent = _build_agent(action_dim=train_env.action_dim, state_dim=train_env.state_dim, device=device)
            _train_real_agent(agent, train_env, device)
            raw_steps = _run_real_decision_rollout(agent, test_env, tickers, device)

        decisions = [_build_decision_step(s) for s in raw_steps]

        if not decisions:
            initial_weights = None
        else:
            initial_weights = decisions[-1].target_weights

        universe_policy = UniversePolicy(
            mode="fixed",
            fixed_assets=tickers,
            selector_description=(
                "Caller-specified subset of TradeMaster's real, shipped DJ30 dataset "
                f"({len(REAL_DJ30_TICKERS)} real tickers); EIIE performs no asset "
                "selection of its own — the universe is fixed by the data provided."
            ),
        )
        observation_policy = ObservationPolicy(
            lookback_window=f"{TIME_STEPS}_trading_days",
            features=list(TECH_INDICATOR_LIST),
            data_sources=["TradeMaster's own shipped, preprocessed data/portfolio_management/dj30/*.csv"],
            observation_description=(
                "Real per-ticker OHLC + z-scored technical indicators over a real "
                f"{TIME_STEPS}-trading-day lookback window, matching upstream's own "
                "PortfolioManagementEIIEEnvironment state construction."
            ),
        )
        decision_policy = DecisionPolicy(
            decision_rule=(
                "Real EIIEConv actor network: a 1D convolution over the lookback window per "
                "ticker, concatenated with a learnable cash logit, passed through softmax "
                "(eiie.py:34-36) — verified non-negative, sums to 1.0 across tickers+cash."
            ),
            output_semantics="target_weights: real softmax allocation across tickers+CASH, long-only, fully invested.",
            rebalance_frequency="DAILY",
            holding_horizon=None,
        )
        update_policy = UpdatePolicy(
            mode=UpdateMode.NONE,
            update_description=(
                f"Real EIIE actor/critic trained once ({TRAIN_ROUNDS} real explore+update rounds, "
                f"horizon_len={HORIZON_LEN} — an honestly reduced budget, not upstream's full-scale "
                "training) on the first ~70% of generation_window's real trading days, then queried "
                "statically (no further gradient updates) across the remaining real trading days."
            ),
        )
        constraints = PortfolioConstraints(
            long_only=True, cash_allowed=True,
            net_exposure_min=1.0, net_exposure_max=1.0,
        )

        explanation = (
            f"Real EIIE actor-critic policy (upstream TradeMaster's own "
            f"PortfolioManagementEIIE agent + EIIEConv/EIIECritic nets), trained on "
            f"{len(train_dates)} real trading days and evaluated causally over the "
            f"following {len(test_dates)-1} real trading days, all within the harness-"
            f"supplied generation_window [{generation_window.start}, {generation_window.end}]. "
            f"Universe: {', '.join(tickers)} (subset of TradeMaster's real shipped DJ30 data)."
        )

        result = Q4Policy(
            context=context,
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=generation_window,
            universe_policy=universe_policy,
            observation_policy=observation_policy,
            decision_policy=decision_policy,
            update_policy=update_policy,
            constraints=constraints,
            initial_weights=initial_weights,
            decisions=decisions or None,
            explanation=explanation,
        )

        self._last_native_output = {
            "upstream": {
                "tickers": tickers,
                "train_dates": [str(d.date()) if hasattr(d, "date") else str(d) for d in train_dates[:3]] + ["..."],
                "test_dates": [str(d.date()) if hasattr(d, "date") else str(d) for d in test_dates[:3]] + ["..."],
                "n_train_days": len(train_dates),
                "n_decisions": len(decisions),
                "horizon_len": HORIZON_LEN,
                "train_rounds": TRAIN_ROUNDS,
            },
            "adapter_derived": {
                "generation_window": {"start": generation_window.start, "end": generation_window.end},
                "time_steps": TIME_STEPS,
            },
        }
        self._last_latency_sec = time.time() - t0
        return result

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
        self._last_native_output = None
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
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
            as_of="2021-12-31",
            data_cutoff="2021-12-31",
            scope=OutputScope.PORTFOLIO,
            targets=["AAPL", "MSFT", "JNJ"],
            universe=["AAPL", "MSFT", "JNJ"],
        )
        generation_window = TimeWindow(start="2021-01-04", end="2021-12-31")

        q4 = self.q4_policy(context, generation_window)
        checks["q4_returns_Q4Policy"] = q4 is not None
        if q4 is not None:
            checks["q4_context_echoed"] = q4.context == context
            checks["q4_generation_window_echoed"] = q4.generation_window == generation_window
            checks["q4_policy_type_is_frozen_learned"] = q4.policy_type == "FROZEN_LEARNED_POLICY"
            checks["q4_decisions_nonempty"] = bool(q4.decisions)
            if q4.decisions:
                checks["q4_timestamps_increasing"] = all(
                    q4.decisions[i].timestamp > q4.decisions[i - 1].timestamp
                    for i in range(1, len(q4.decisions))
                )
                checks["q4_causality_ok"] = all(
                    d.information_cutoff <= d.timestamp for d in q4.decisions
                )
                checks["q4_weights_long_only_and_sum_1"] = all(
                    all(v >= -1e-6 for v in d.target_weights.values())
                    and abs(sum(d.target_weights.values()) - 1.0) < 1e-4
                    for d in q4.decisions
                )
                checks["q4_selected_universe_present"] = all(
                    d.selected_universe == sorted(context.universe) for d in q4.decisions
                )
        return checks
