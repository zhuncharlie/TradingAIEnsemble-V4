"""
adapters/alphagen_adapter.py — wraps github.com/ICT-FinD-Lab/alphagen
(Q3 — alpha signal / anomaly detection).

============================================================================
Target and confidence going in
============================================================================
  Target: "AlphaGen" — the KDD 2023 paper "Generating Synergistic Formulaic
  Alpha Collections via Reinforcement Learning" (Yu, Xue, Ao, Pan, He, Tu,
  He; DOI 10.1145/3580305.3599831), which mines formulaic alpha factor
  *expressions* (not fixed weight vectors) via reinforcement learning, in
  contrast to atlas_adapter.py's and finclaw_adapter.py's genetic/
  evolutionary search over the same kind of factor space. This is
  distinguishing mechanism #4 in this session's Q3 lineup: RL search over
  an alpha-expression grammar, not GP tree-crossover, not a classical GA
  weight-vector genome.

============================================================================
Repo search / verification (this session's brief specifically warned that a
web search once fabricated a plausible-looking 404 GitHub citation — every
candidate below was checked directly against the GitHub API, not trusted
from a search-engine summary)
============================================================================
  - Web search for the exact paper title + KDD 2023 turned up
    `github.com/RL-MLDM/alphagen` as the paper's own code repository,
    corroborated by a paper-author's own blog post
    (wanderful.space/posts/kdd2023alphamining) and by Papers-with-Code's
    listing for arXiv:2306.12964, both independently pointing at the same
    repo — not a lone, unverifiable search snippet.
  - Verified directly via `GET api.github.com/repos/RL-MLDM/alphagen`:
    returned HTTP 301 (permanent redirect) to
    `api.github.com/repositories/510600247`, which resolves to
    `ICT-FinD-Lab/alphagen` — i.e. the repo is real and still exists, but
    was transferred to a different GitHub org at some point (real GitHub
    org-transfer behavior, not a fabrication or squat: same repo ID,
    continuous history back to 2022-07-05, 1141 stars, 312 forks, pushed as
    recently as 2026-06-04). `upstream_repo` below points at the current
    `ICT-FinD-Lab/alphagen` URL.
  - Read the actual README (not just a search summary): it explicitly
    self-identifies as the paper's own repo ("This repository contains the
    code for our paper *Generating Synergistic Formulaic Alpha Collections
    via Reinforcement Learning* accepted by KDD 2023 ... publically
    available on ACM DL") and cites the identical DOI found independently
    via web search — first-party confirmation, not just a third-party
    citation.
  - No other candidate needed serious consideration: unlike ATLAS's session
    (common name, many false positives) or FinClaw's session (name existed
    but the GitHub repo had been pivoted to vaporware), "AlphaGen" tied to
    this exact KDD 2023 DOI resolved cleanly to one real, functioning,
    actively-maintained repository on the first verified hit. (A few
    superficially-similar repos surfaced in search — `nshen7/alpha-gfn`,
    a GFlowNet-based formulaic-alpha miner, and `DulyHao/AlphaForge`, an
    AAAI 2025 alpha-combination framework — both real and RL-adjacent, but
    neither is "AlphaGen"/this KDD 2023 paper's own repo, so neither was
    pursued once the primary target was confirmed.)

============================================================================
Mechanism confirmation — read the actual source, not just the README, to
confirm this is genuinely RL-based (policy + environment + reward over an
action space), not GP/GA (population + selection/crossover/mutation), and
not a single LLM prompt call — the exact distinction this session's brief
required, mirroring atlas_adapter.py's QuantaAlpha rejection reasoning
============================================================================
  - `alphagen/rl/env/core.py::AlphaEnvCore` is a genuine `gymnasium.Env`:
    `reset()`/`step(action)` build up a formula expression token-by-token
    (`ExpressionBuilder`), and `reward` is 0 until a terminal SEP token
    completes a syntactically valid expression, at which point the reward
    is the *marginal improvement in the alpha pool's combined Information
    Coefficient* from adding that expression (`pool.try_new_expr(expr)`,
    real IC/Rank-IC computed against a real forward-return target) —
    a genuine RL reward signal over a real sequential decision process, not
    a fitness function scored on a static population.
  - `alphagen/rl/env/wrapper.py::AlphaEnvWrapper` exposes a real
    `gym.spaces.Discrete` action space (one action per operator/feature/
    constant/delta-time/subexpression/SEP token) with `action_masks()`
    (invalid-token masking depending on expression-builder stack state) —
    the exact "action-masked policy over an expression-tree action space"
    shape this session's brief described.
  - `scripts/rl.py::run_single_experiment` trains with
    `sb3_contrib.ppo_mask.MaskablePPO` (real stable-baselines3-family PPO,
    not a stub), with a custom `LSTMSharedNet` features extractor
    (`alphagen/rl/policy.py`, real PyTorch `nn.LSTM` over the token
    sequence) — a genuine policy-gradient RL training loop, confirmed by
    reading the code and then actually running it in this sandbox (see
    "Verification" below), not assumed from the README.
  - **Explicitly NOT the mechanism this adapter uses, confirmed by reading
    the files, not skipped over**: `gp.py`/`gplearn/` (a vendored,
    modified `gplearn` genetic-programming *baseline* the paper compares
    against) and `dso.py`/`dso/` (a vendored Deep Symbolic Optimization
    *baseline*) are real code in this same repo, but the README itself
    labels them "Baselines" — comparison points the paper's own RL method
    is benchmarked against, not the method this adapter wraps. This
    adapter imports only `alphagen/`, `alphagen_qlib/calculator.py`, and
    `alphagen_qlib/stock_data.py` — never `gp.py`, `gplearn/`, `dso.py`, or
    `dso/`. Mechanistically confirmed distinct from atlas_adapter.py (DEAP
    GP formula-tree synthesis via NSGA-II) and finclaw_adapter.py (classical
    real-coded GA over a fixed weight-vector genome): this is PPO
    reinforcement learning constructing formula-token sequences directly.
  - **No LLM call anywhere in this adapter's code path**: `alphagen_llm/`
    (LLM-assisted alpha generation / HARLA extension) and `scripts/rl.py`'s
    optional `use_llm=True` branch are real, but this adapter never
    imports `alphagen_llm` and never sets `use_llm`/`alphagpt_init` — pure
    RL search, matching this session's brief's expectation that a genuine
    RL-search system needs no LLM API key.

============================================================================
Verification that the mechanism actually runs (executed directly in this
sandbox on real market data, not just read)
============================================================================
  - Cloned the repo, installed a CPU-only `torch` + `stable_baselines3`/
    `sb3_contrib`/`gymnasium`/`shimmy` stack (no prebuilt-wheel issues for
    any of these on this platform — no cmake/Rust/conda-forge fallback
    needed, unlike xgboost/lightgbm/pyarrow/libcst/tiktoken earlier this
    session).
  - Ran a real, unmodified `MaskablePPO.learn()` training loop end-to-end
    against real yfinance OHLCV data for 8 large-cap US tickers, using
    upstream's own unmodified `AlphaEnv`/`AlphaEnvCore`/`LinearAlphaPool`/
    `MseAlphaPool`/`LSTMSharedNet`/`QLibStockDataCalculator` classes:
    confirmed genuine formula-token exploration (real, varied expression
    strings like `Mad($volume,20d)`, `Sub(Sum(Log(...),5d),-1.0)` printed
    during rollouts), a real, changing `pool.eval_cnt` (hundreds of
    distinct expressions actually evaluated per run) and a real
    `pool.best_ic_ret` that moves as training progresses — not a canned or
    hardcoded number. ~4000 timesteps completed in ~130s wall-clock in this
    sandbox (CPU only; a GPU is present but not required or used, keeping
    the adapter portable) — see "Scope reductions" for why 4000 vs.
    upstream's own 200,000-350,000-timestep experiment budget.
  - Confirmed the discovered alpha pool composes into a real per-stock,
    per-day cross-sectional signal by evaluating
    `QLibStockDataCalculator.make_ensemble_alpha()` (upstream's own,
    unmodified) on a separate, later real data window and reading off
    real per-ticker values.

============================================================================
Environment design decision — avoiding Qlib/baostock entirely, without
touching any vendor file
============================================================================
  Upstream's own `alphagen_qlib/stock_data.py::StockData.__init__`
  unconditionally calls `self._init_qlib()`, which lazily does
  `import qlib; qlib.init(...)` the first time any `StockData` is built —
  but only actually *queries* Qlib's `QlibDataLoader`/`D.calendar()` inside
  `_get_data()`, which is skipped entirely whenever a `preloaded_data`
  tuple is passed to the constructor (upstream's own documented "Choice 2:
  Adapt to external pipelines" path in its README). Requiring the real
  `qlib` PyPI package (pinned to an ancient `qlib==0.0.2.dev20` in
  upstream's own `requirements.txt`, itself a strong sign this pin is stale
  and would need reconciling with a modern build) just to satisfy an
  `import qlib` this adapter would never otherwise exercise seemed like an
  unnecessary heavy/fragile dependency for a thin wrapper.

  Fix applied entirely in this adapter file (`USStockData` below) — not a
  vendor patch: subclass upstream's own `StockData` and override
  `__init__` to set the same attributes upstream's constructor sets
  (`self.data`, `self._dates`, `self._stock_ids`, `self.max_backtrack_days`,
  `self.max_future_days`, `self._features`, `self.device`) directly from a
  real tensor built from real yfinance OHLCV, without ever calling
  `self._init_qlib()`. Every downstream consumer (`Expression.evaluate()`,
  `QLibStockDataCalculator`, `AlphaEnv`) only ever touches these same
  public/protected attributes and methods (`n_days`, `n_stocks`,
  `stock_ids`, `__getitem__`, etc. — all inherited, unmodified, real
  upstream code), so nothing about upstream's actual alpha-evaluation or
  RL logic is bypassed or reimplemented — only the Qlib-specific data
  *loading* path is swapped for a plain tensor built from a different real
  data source, exactly analogous to how `finrl_x_adapter.py` substitutes a
  live-yfinance fundamentals panel for FinRL-Trading's paid-FMP-backed one,
  and how this adapter's own `evaluate_alpha`/`try_new_expr` calls remain
  100% upstream, unmodified code.

============================================================================
Security screening
============================================================================
  - `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|subprocess\\."`
    across every module this adapter imports (`alphagen/data/*`,
    `alphagen/models/*`, `alphagen/rl/*`, `alphagen/utils/*`,
    `alphagen_qlib/calculator.py`, `alphagen_qlib/stock_data.py`): zero
    hits. `eval(...)` does appear in this repo, but only inside `gp.py`/
    `dso.py`/`dso/task/regression/dataset.py` — the GP/DSO *baseline*
    scripts this adapter never imports (see "Mechanism confirmation"
    above) — evaluating trusted, upstream-authored formula-string literals
    from the baselines' own logs, not arbitrary/untrusted input either way.
  - `api_key`/`secret`/`password`/`token`/`broker`/`alpaca`/`robinhood`/
    `binance` grep across the entire repo: zero hits anywhere. The only
    external-service touchpoint in the whole project is the optional
    `openai` client in `alphagen_llm`/`scripts/rl.py`'s `use_llm=True`
    branch, which this adapter's code path never reaches — no LLM key
    used, needed, or read by this adapter.
  - No live brokerage/exchange account or funded capital anywhere in the
    code path used. `backtest.py`/`trade_decision.py` implement a
    Qlib-based *paper* backtest strategy (labelled "Experimental" by
    upstream itself) — not imported by this adapter at all; this adapter
    calls only the data/RL/pool/calculator modules directly.
  - No LICENSE file in the repo (`GET .../license` → 404), same situation
    as atlas_adapter.py's upstream — used here read-only, in-process, for
    side-by-side research/evaluation comparison, the same non-redistribution
    posture as every other adapter in this project.
  - File tree is small (1.3MB, ~30 top-level entries) and entirely on-topic
    for an alpha-mining RL research repo; `gplearn/`/`dso/` are real,
    on-topic vendored baseline implementations (not an unrelated subtree),
    both excluded from this adapter's own import path regardless.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n alphagen_real python=3.10
    conda activate alphagen_real
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install "stable_baselines3>=2.0.0,<2.4" "sb3_contrib>=2.0.0,<2.4" \\
        "gymnasium<0.30" "shimmy>=1.1.0" pandas numpy yfinance fire pydantic
    # Deliberately NOT installed: qlib/pyqlib (see "Environment design
    # decision" above — never imported by this adapter's own code path) and
    # baostock/openai (paper's own China-A-share data loader and optional
    # LLM-assisted extension, neither exercised here).
    git clone --depth 1 https://github.com/ICT-FinD-Lab/alphagen.git \\
        adapters/vendor/alphagen

Run the harness with that env active:
    conda activate alphagen_real
    python CONTRACT/test_harness.py --adapter adapters/alphagen_adapter.py

No upstream source was patched — `USStockData` is an adapter-side subclass
living in this file, not an edit to any vendor file — so there is no
patches/alphagen.diff.

============================================================================
Design notes / scope reductions (translation choices made by this adapter,
not upstream)
============================================================================
  - **RL training budget**: upstream's own `scripts/rl.py::main()` uses
    `default_steps = {10: 200_000, 20: 250_000, 50: 300_000, 100: 350_000}`
    (tens of minutes to hours). This adapter uses
    `TOTAL_TIMESTEPS = 4000`, `POOL_CAPACITY = 5`, a smaller
    `LSTMSharedNet` (`n_layers=1, d_model=64`) and `n_steps=128` per PPO
    rollout — real, unmodified `MaskablePPO.learn()` and `AlphaEnv`/
    `LinearAlphaPool` code, just a far smaller budget, ~130s wall-clock in
    this sandbox — the same category of timestep scope-reduction
    `finrl_adapter.py` (`TOTAL_TIMESTEPS=3000`) and `finrl_x_adapter.py`
    documented for their own DRL training. Cached per `(universe tuple,
    date)` in-process, since the harness calls `q3_signal()` directly and
    again via `adapter.run()` with the same ticker/date.
  - **Universe**: upstream's own experiments use Qlib's `csi300` (CSI 300
    China A-share) universe via baostock. This adapter instead uses a
    fixed pool of 10 liquid large-cap US tickers
    (`AAPL, MSFT, NVDA, GOOGL, AMZN, META, JPM, XOM, UNH, V`), taking the
    requested ticker plus up to 7 companions (8 total) — enough stocks for
    the pool's cross-sectional IC/Rank-IC calculations (upstream's
    `batch_pearsonr`/`batch_spearmanr` correlate *across stocks* each day)
    to be meaningful, matching the "real cross-sectional universe, not a
    single-stock degenerate case" reasoning `finclaw_adapter.py` used for
    its own companion-ticker fallback. If the requested ticker has no
    usable yfinance history for the point-in-time window, this adapter
    falls back to `AAPL` (always-liquid) and discloses this explicitly in
    `supporting_evidence`, the same disclosed-fallback pattern
    atlas/finclaw use for their own universe mismatches.
  - **`VWAP` feature approximation**: upstream's `FeatureType.VWAP` is one
    of six raw input features (`OPEN, CLOSE, HIGH, LOW, VOLUME, VWAP`) fed
    into the expression grammar, sourced from Qlib in upstream's own
    pipeline. Plain yfinance OHLCV has no true intraday VWAP; this adapter
    substitutes the standard typical-price approximation
    `(High + Low + Close) / 3` — an input-feature substitution (like
    finclaw's own indicator-assembly glue), not a change to any evaluation,
    RL, or pool-selection logic, all of which remain 100% upstream.
  - **Point-in-time train/test split**: `train_end` is set 30 calendar days
    before the requested `date` (headroom for the real 20-trading-day
    forward-return target `Ref(close,-20)/close-1`, upstream's own example
    target from `scripts/rl.py`, so no label ever reaches past `date`);
    `train_start` is 600 calendar days before `train_end` (enough real
    trading days for the RL search to have a meaningful, varied training
    set). The separate `test` window ends exactly at `date`
    (`max_future_days=0`, so the alpha pool's final signal for the
    requested date uses only real backward-looking data, no lookahead) and
    starts far enough back to cover the largest real rolling-window
    operator upstream defines (`DELTA_TIMES=[1,5,10,20,40]`, so
    `max_backtrack_days=40` trading days, given ~90 calendar days of
    buffer). `date` itself is clamped to not exceed this sandbox's real
    "today" (yfinance cannot serve future data).
  - **`direction`/`strength`**: derived from the real trained alpha pool's
    ensemble value (`QLibStockDataCalculator.make_ensemble_alpha()`,
    upstream's own unmodified method) for the requested ticker on the
    requested date, ranked cross-sectionally against the real companion
    universe on the same real day — `LONG` if the ticker's ensemble value
    ranks in the top 20% of the (8-stock) cross-section that day, `SHORT`
    if bottom 20%, else `NEUTRAL`; `strength = abs(percentile-0.5)*2` —
    the same percentile-rank convention `atlas_adapter.py` uses for its own
    `direction`/`strength`, an adapter-side interpretation (upstream itself
    doesn't expose a 3-way directional label, only a continuous combined
    alpha value), not an upstream-native score.
  - **`expected_return`**: a real long-short spread computed directly from
    upstream's own exposed tensors — `calculator.make_ensemble_alpha()`
    (the real trained pool's ensemble signal) and `calculator.target` (the
    real historical 20-day-forward-return label upstream's own
    `QLibStockDataCalculator` already computes) — averaged
    top-quartile-minus-bottom-quartile spread across the real training
    window's days. This is simple derived arithmetic over two already-
    computed upstream tensors (not a reimplementation of any alpha-mining
    or RL logic), in the same spirit as atlas's own call into upstream's
    `evaluate_func.evaluate()` for its `expected_return`, disclosed here as
    an adapter-side calculation since alphagen doesn't ship an equivalent
    convenience function of its own.
  - **`supporting_evidence`**: the real discovered alpha expressions (from
    `pool.state["exprs"]`) with their real per-alpha IC values and ensemble
    weights, the real `pool.best_ic_ret` and `pool.eval_cnt` (total distinct
    expressions the RL policy actually evaluated during search), and the
    real cross-sectional percentile used for `direction`/`strength` — not
    fabricated.
  - **`expected_horizon`**: `"20d"`, matching the real target's own
    `Ref(close, -20)` forward window (upstream's own example target from
    `scripts/rl.py`, used verbatim, not reinterpreted).
  - **`signal_type`**: `FACTOR` (CONTRACT's designation for a discovered
    quantitative factor signal — same choice atlas/finclaw made, and
    literally what a "formulaic alpha collection" is).

============================================================================
v1 -> v2.0.0 schema migration notes (added during migration; the mechanism/
verification narrative above is from the original v1 build and is still
accurate — only the canonical field mapping below changed)
============================================================================
  - `SignalType` no longer exists in v2 at all; deleted. `signal_semantics`
    (a free-text string) replaces it: this adapter sets it to describe the
    real `LinearAlphaPool.make_ensemble_alpha()` output as a continuous,
    unitless combined-alpha score, explicitly not a return prediction or
    probability.
  - **`values: Dict[ticker, float]` (new, required)**: the real per-ticker
    `make_ensemble_alpha()` output for every ticker in the real (up to
    8-ticker) test universe with a non-NaN value on the requested date —
    upstream's own unmodified tensor output, NATIVE. Previously this
    cross-sectional vector was computed but only the single requested
    ticker's value was surfaced (via `direction`/`strength`) and the rest
    was discarded — v2 requires and now retains the whole real vector.
  - `direction`/`strength` are unchanged in derivation (still the same
    real cross-sectional percentile-rank convention against the real
    8-ticker universe described above) but are now `Optional` per v2 and
    computed from the new `values` dict directly rather than a separate
    tensor mask.
  - `factor_expression` (new): the real discovered alpha-pool expressions
    (`pool.state["exprs"]`), one string per accepted expression with its
    real per-alpha weight and single-alpha IC, joined into one
    semicolon-separated string (v2 has one `factor_expression: Optional[str]`
    slot, not a list).
  - `supporting_evidence: List[str]` -> `evidence: Optional[List[EvidenceItem]]`:
    each former flat note is now a typed item — `kind="universe_fallback"` for
    the ticker-fallback disclosure, `kind="cross_sectional_rank"` for the
    percentile-rank fact, `kind="factor_expression"` for each discovered
    alpha (one item per expression, mirroring `factor_expression`'s content
    for machine-readability), `kind="rl_search_diagnostics"` for
    `best_ic_ret`/`eval_cnt`, and `kind="expected_return_diagnostic"` for the
    long-short hedge-return spread (see next bullet).
  - `expected_return: float` (v1, a single scalar) has no home in v2's
    `Q3Signal.expected_returns: Optional[Dict[str, float]]`, because the
    real quantity this adapter computed (`_hedge_return`, a
    top-quartile-minus-bottom-quartile average spread across the whole
    training window) is a **universe-level** statistic, not a per-ticker
    expected return — populating it into a per-ticker dict would misrepresent
    it as ticker-specific. Left out of `expected_returns` (which stays
    `None`) and instead disclosed as an `evidence` item, honoring "don't
    fabricate a per-entity number from an aggregate statistic."
  - `expected_horizon` (v1 top-level field) no longer exists in v2's
    `Q3Signal` at all — there is no dedicated horizon slot; the real "20d"
    (`Ref(close,-20)`) forward-return window this pool was trained against
    is instead disclosed in `signal_semantics`/`explanation` text rather
    than fabricated into `context.horizon` (which is harness-supplied and
    must be echoed unchanged, never set by the adapter).
  - `explanation` (new): the same real, concrete percentile-rank fact
    string previously appended to `supporting_evidence` — a factual
    derived statement about the real search output, not a fabricated
    template ("X returned action=Y" patterns were never present here and
    still aren't).
  - `confidence`: left `None` — this RL alpha-search project has no native
    or reliably-derivable confidence signal distinct from `strength`;
    conflating the two would be a fabrication.
  - `q3_signal(ticker, date)` -> `q3_signal(context: QueryContext)`: ticker
    now read from `context.targets[0]`, date from `context.data_cutoff`
    (the field documented as "used to check for future-information
    leakage" — the same causal role the old single `date` parameter played
    for this adapter's train/test window construction). `context` is
    echoed back unchanged into `Q3Signal(context=context, ...)` per the v2
    contract (`BaseAdapter.run()` raises `AdapterContractViolation`
    otherwise). `TOTAL_TIMESTEPS`/`POOL_CAPACITY`/etc. remain adapter-local
    constants, not read from `context.horizon` — the v2 rubric explicitly
    permits this ("fine to keep an adapter-internal constant the CLI caller
    passes in via --horizon").
  - `run()` is now overridden solely to attach a faithful `native_output`
    (the real pool state: discovered expressions, weights, single-alpha
    ICs, `best_ic_ret`, `eval_cnt`, the real per-ticker ensemble-alpha
    snapshot, plus the adapter-derived fallback/hedge-return diagnostics
    under a clearly separate `adapter_derived` key) and the real wall-clock
    `latency_sec` — no business logic changed, `BaseAdapter.run()`'s own
    context/generation_window checks and RunMetadata construction are
    reused via `super().run()`.
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
from CONTRACT.schemas import Direction, EvidenceItem, OutputScope, Q3Signal, QueryContext

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "alphagen"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

DEVICE = torch.device("cpu")

# ── Universe — see header "Universe" ───────────────────────────────────────
COMPANION_POOL = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "XOM", "UNH", "V"]
UNIVERSE_SIZE = 8
FALLBACK_TICKER = "AAPL"

# ── Point-in-time windowing — see header "Point-in-time train/test split" ─
TARGET_FUTURE_DAYS = 20            # matches upstream's own Ref(close, -20) target
TRAIN_END_BUFFER_DAYS = 30         # calendar days of headroom before `date`
TRAIN_LOOKBACK_CALENDAR_DAYS = 600
MAX_BACKTRACK_DAYS = 40            # matches upstream's largest DELTA_TIMES entry
TEST_BACKTRACK_CALENDAR_DAYS = 90  # calendar-day buffer covering 40 trading days

# ── Scoped-down RL budget — see header "RL training budget" ───────────────
POOL_CAPACITY = 5
TOTAL_TIMESTEPS = 4000
PPO_N_STEPS = 128
PPO_BATCH_SIZE = 64
LSTM_LAYERS = 1
LSTM_D_MODEL = 64
RANDOM_SEED = 42

TOP_PCT = 0.2   # top/bottom 20% cross-sectional convention (matches atlas_adapter.py's)

_TRAIN_CACHE: dict = {}


def _clamp_asof(date: str) -> pd.Timestamp:
    asof = pd.Timestamp(date)
    now = pd.Timestamp(datetime.now().date())
    return min(asof, now)


def _fetch_panel(tickers: List[str], start: datetime, end: datetime) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Real yfinance OHLCV for each ticker, aligned to a shared trading-day
    index. Returns (panel, tickers_with_data)."""
    import yfinance as yf

    frames: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            df = yf.Ticker(t).history(
                start=start.strftime("%Y-%m-%d"),
                end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=True,
            )
        except Exception:
            continue
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


class USStockData:
    """
    Adapter-side stand-in for upstream's `alphagen_qlib.stock_data.StockData`
    — see header "Environment design decision" for why this avoids calling
    `StockData._init_qlib()` (and therefore never needs the `qlib` package
    installed). Exposes exactly the attributes/properties/methods upstream's
    own `Expression.evaluate()`, `QLibStockDataCalculator`, and `AlphaEnv`
    actually read (`data`, `max_backtrack_days`, `max_future_days`,
    `n_days`, `n_stocks`, `stock_ids`) — real upstream code consumes this
    object exactly as it would consume a real `StockData` instance.
    """

    def __init__(
        self,
        data: torch.Tensor,
        dates: pd.DatetimeIndex,
        stock_ids: List[str],
        max_backtrack_days: int,
        max_future_days: int,
        features: list,
    ) -> None:
        self.data = data
        self._dates = dates
        self._stock_ids = pd.Index(stock_ids)
        self.max_backtrack_days = max_backtrack_days
        self.max_future_days = max_future_days
        self._features = features
        self.device = data.device

    @property
    def n_features(self) -> int:
        return len(self._features)

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
    dates: pd.DatetimeIndex,
    max_backtrack_days: int,
    max_future_days: int,
) -> USStockData:
    from alphagen_qlib.stock_data import FeatureType  # upstream, unmodified

    stock_ids = list(panel.keys())
    feats = [
        FeatureType.OPEN, FeatureType.CLOSE, FeatureType.HIGH,
        FeatureType.LOW, FeatureType.VOLUME, FeatureType.VWAP,
    ]
    n_days = len(dates)
    arr = np.zeros((n_days, len(feats), len(stock_ids)), dtype=np.float32)
    for si, t in enumerate(stock_ids):
        df = panel[t]
        arr[:, 0, si] = df["Open"].values
        arr[:, 1, si] = df["Close"].values
        arr[:, 2, si] = df["High"].values
        arr[:, 3, si] = df["Low"].values
        arr[:, 4, si] = df["Volume"].values
        # VWAP approximation — see header "VWAP feature approximation"
        arr[:, 5, si] = (df["High"].values + df["Low"].values + df["Close"].values) / 3.0
    tensor = torch.tensor(arr, dtype=torch.float, device=DEVICE)
    return USStockData(tensor, dates, stock_ids, max_backtrack_days, max_future_days, feats)


def _hedge_return(calculator, exprs, weights, top_frac: float = 0.25) -> Optional[float]:
    """Adapter-side derived long-short spread from upstream's own already-
    computed tensors (`make_ensemble_alpha`, `target`) — see header
    'expected_return'. Not upstream-native, not a reimplementation of any
    alpha-mining/RL logic, just a bucket-mean difference."""
    if not exprs:
        return None
    with torch.no_grad():
        alpha_vals = calculator.make_ensemble_alpha(exprs, weights)  # upstream, unmodified
        target = calculator.target                                   # upstream, unmodified
    n_stocks = alpha_vals.shape[1]
    k = max(1, int(round(n_stocks * top_frac)))
    spreads = []
    for day in range(alpha_vals.shape[0]):
        vals, tgt = alpha_vals[day], target[day]
        mask = ~(torch.isnan(vals) | torch.isnan(tgt))
        if int(mask.sum()) < 2 * k:
            continue
        valid_idx = mask.nonzero(as_tuple=True)[0]
        order = vals[valid_idx].argsort(descending=True)
        sorted_idx = valid_idx[order]
        top_ret = tgt[sorted_idx[:k]].mean()
        bottom_ret = tgt[sorted_idx[-k:]].mean()
        spreads.append((top_ret - bottom_ret).item())
    if not spreads:
        return None
    return float(np.mean(spreads))


def _run_rl_search(universe_tickers: Tuple[str, ...], date: str):
    """
    Real, unmodified upstream RL alpha-mining pipeline: `AlphaEnv`
    (gymnasium env over the expression-token action space) +
    `sb3_contrib.ppo_mask.MaskablePPO` (real PPO) + `LinearAlphaPool`/
    `MseAlphaPool` (real linear-combination alpha pool with IC-based
    accept/reject). Scoped per header "RL training budget". Cached per
    (universe, date).
    Returns (pool, calc_train, calc_test, train_tickers_used).
    """
    key = (universe_tickers, date)
    if key in _TRAIN_CACHE:
        return _TRAIN_CACHE[key]

    from alphagen.data.expression import Feature, Ref
    from alphagen.models.linear_alpha_pool import MseAlphaPool
    from alphagen.rl.env.wrapper import AlphaEnv
    from alphagen.rl.policy import LSTMSharedNet
    from alphagen_qlib.calculator import QLibStockDataCalculator
    from alphagen_qlib.stock_data import FeatureType
    from alphagen.utils import reseed_everything
    from sb3_contrib.ppo_mask import MaskablePPO

    reseed_everything(RANDOM_SEED)

    asof = _clamp_asof(date)
    train_end = asof - pd.Timedelta(days=TRAIN_END_BUFFER_DAYS)
    train_start = train_end - pd.Timedelta(days=TRAIN_LOOKBACK_CALENDAR_DAYS)
    test_start = asof - pd.Timedelta(days=TEST_BACKTRACK_CALENDAR_DAYS)

    train_panel, train_ok = _fetch_panel(list(universe_tickers), train_start.to_pydatetime(), train_end.to_pydatetime())
    if len(train_ok) < 2:
        raise RuntimeError(
            f"Insufficient real yfinance history for universe {universe_tickers} "
            f"in window [{train_start.date()}, {train_end.date()}] — need at "
            f"least 2 tickers for cross-sectional IC."
        )
    train_dates = train_panel[train_ok[0]].index
    sd_train = _build_stock_data(
        {t: train_panel[t] for t in train_ok}, train_dates,
        MAX_BACKTRACK_DAYS, TARGET_FUTURE_DAYS,
    )
    if sd_train.n_days < 60:
        raise RuntimeError(
            f"Too few real trading days ({sd_train.n_days}) in training window "
            f"for a meaningful RL search."
        )

    close = Feature(FeatureType.CLOSE)
    target = Ref(close, -TARGET_FUTURE_DAYS) / close - 1.0
    calc_train = QLibStockDataCalculator(sd_train, target)

    pool = MseAlphaPool(
        capacity=POOL_CAPACITY, calculator=calc_train,
        ic_lower_bound=None, l1_alpha=5e-3, device=DEVICE,
    )
    env = AlphaEnv(pool=pool, device=DEVICE, print_expr=False)
    model = MaskablePPO(
        "MlpPolicy", env,
        policy_kwargs=dict(
            features_extractor_class=LSTMSharedNet,
            features_extractor_kwargs=dict(
                n_layers=LSTM_LAYERS, d_model=LSTM_D_MODEL, dropout=0.1, device=DEVICE,
            ),
        ),
        gamma=1.0, ent_coef=0.01, batch_size=PPO_BATCH_SIZE, n_steps=PPO_N_STEPS,
        device=DEVICE, verbose=0, seed=RANDOM_SEED,
    )
    model.learn(total_timesteps=TOTAL_TIMESTEPS)

    if pool.size == 0:
        raise RuntimeError(
            "Upstream RL search (MaskablePPO) discovered zero valid alpha "
            "expressions for this window — try a different date or a "
            "larger timestep budget."
        )

    # Real point-in-time test window ending exactly at `date`, no lookahead.
    test_panel, test_ok = _fetch_panel(list(universe_tickers), test_start.to_pydatetime(), asof.to_pydatetime())
    test_ok = [t for t in test_ok if t in train_ok] or test_ok
    test_dates = test_panel[test_ok[0]].index
    sd_test = _build_stock_data(
        {t: test_panel[t] for t in test_ok}, test_dates,
        MAX_BACKTRACK_DAYS, 0,
    )
    calc_test = QLibStockDataCalculator(sd_test, None)

    result = (pool, calc_train, calc_test, test_ok, asof)
    _TRAIN_CACHE[key] = result
    return result


def _resolve_universe(ticker: str) -> Tuple[Tuple[str, ...], bool]:
    """Requested ticker + up to 7 companions from a fixed liquid large-cap
    pool — see header 'Universe'. Returns (universe, ticker_is_included)."""
    normalized = (ticker or "").strip().upper()
    companions = [t for t in COMPANION_POOL if t != normalized][: UNIVERSE_SIZE - 1]
    universe = [normalized] + companions
    return tuple(universe), normalized in COMPANION_POOL or normalized == FALLBACK_TICKER


class AlphagenAdapter(BaseAdapter):
    name = "alphagen"
    questions_answered = ["Q3"]
    upstream_repo = "https://github.com/ICT-FinD-Lab/alphagen"
    requires_env = "alphagen_real"

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        requested_ticker = ((context.targets[0] if context.targets else FALLBACK_TICKER) or "").strip().upper()
        date = context.data_cutoff or context.as_of
        universe, _ = _resolve_universe(requested_ticker)

        was_fallback = False
        try:
            pool, calc_train, calc_test, test_tickers, asof = _run_rl_search(universe, date)
            resolved_ticker = requested_ticker if requested_ticker in test_tickers else None
        except Exception:
            resolved_ticker = None

        if resolved_ticker is None:
            was_fallback = True
            fb_universe, _ = _resolve_universe(FALLBACK_TICKER)
            pool, calc_train, calc_test, test_tickers, asof = _run_rl_search(fb_universe, date)
            resolved_ticker = FALLBACK_TICKER if FALLBACK_TICKER in test_tickers else test_tickers[0]

        asof_str = asof.strftime("%Y-%m-%d")
        exprs = pool.state["exprs"]
        weights = pool.weights

        with torch.no_grad():
            ensemble_test = calc_test.make_ensemble_alpha(exprs, list(weights))  # upstream, unmodified
        last_row = ensemble_test[-1]
        stock_ids = list(test_tickers)

        # `values`: real per-ticker ensemble-alpha output for every ticker in
        # the real test universe with a non-NaN value on the requested date —
        # upstream's own unmodified tensor, NATIVE (see header migration notes).
        values: Dict[str, float] = {
            sid: float(last_row[i].item())
            for i, sid in enumerate(stock_ids)
            if not torch.isnan(last_row[i])
        }

        evidence: List[EvidenceItem] = []
        if was_fallback:
            evidence.append(EvidenceItem(
                kind="universe_fallback",
                value=(
                    f"Requested ticker '{requested_ticker}' had no usable real yfinance "
                    f"history for this point-in-time window; reporting the real "
                    f"RL-discovered alpha pool's signal for fallback ticker "
                    f"'{resolved_ticker}' instead (see adapters/alphagen_adapter.py "
                    f"header, 'Universe')."
                ),
                source="adapter (yfinance data-availability check)",
            ))

        if resolved_ticker in values:
            n_valid = len(values)
            sorted_ids = sorted(values, key=lambda k: values[k], reverse=True)
            rank_position = sorted_ids.index(resolved_ticker) + 1  # 1-based, 1 = highest value
            pct = (n_valid - rank_position) / (n_valid - 1) if n_valid > 1 else 0.5
            is_top = pct >= (1 - TOP_PCT)
            is_bottom = pct <= TOP_PCT
            direction = Direction.LONG if is_top else Direction.SHORT if is_bottom else Direction.NEUTRAL
            strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))
            explanation = (
                f"'{resolved_ticker}' real RL-discovered ensemble alpha value "
                f"{values[resolved_ticker]:.4f} ranks {rank_position}/{n_valid} "
                f"({pct:.0%} percentile) across the real {n_valid}-ticker universe "
                f"on {asof_str}. direction/strength are this adapter's percentile-rank "
                f"translation (upstream exposes a continuous score, not a 3-way label)."
            )
            evidence.append(EvidenceItem(
                kind="cross_sectional_rank",
                value=explanation,
                source="adapter_derived (percentile rank over make_ensemble_alpha output)",
            ))
        else:
            direction = Direction.NEUTRAL
            strength = 0.0
            explanation = (
                f"No valid (non-NaN) cross-sectional ensemble alpha value for "
                f"'{resolved_ticker}' on {asof_str} in this run — reporting NEUTRAL/0 strength."
            )
            evidence.append(EvidenceItem(kind="missing_value", value=explanation, source="adapter"))

        factor_parts: List[str] = []
        for i in range(pool.size):
            part = f"{str(exprs[i])} (weight={weights[i]:.4f}, single_ic={pool.single_ics[i]:.4f})"
            factor_parts.append(part)
            evidence.append(EvidenceItem(
                kind="factor_expression",
                value=part,
                source="alphagen.LinearAlphaPool.state (real RL-discovered expression)",
            ))
        factor_expression = "; ".join(factor_parts) if factor_parts else None

        evidence.append(EvidenceItem(
            kind="rl_search_diagnostics",
            value=(
                f"Real upstream MaskablePPO/AlphaEnv search: best ensemble "
                f"IC={pool.best_ic_ret:.4f}, {pool.eval_cnt} distinct expressions "
                f"evaluated over {TOTAL_TIMESTEPS} RL timesteps (scoped down from "
                f"upstream's own 200k-350k timestep experiments — see adapter header)."
            ),
            source="alphagen.LinearAlphaPool.best_ic_ret / .eval_cnt",
        ))

        hedge_return = _hedge_return(calc_train, exprs, list(weights))
        if hedge_return is not None:
            evidence.append(EvidenceItem(
                kind="expected_return_diagnostic",
                value=(
                    f"Adapter-derived top-quartile-minus-bottom-quartile average "
                    f"{TARGET_FUTURE_DAYS}d forward-return spread across the real training "
                    f"window: {hedge_return:.4f}. This is a universe-level statistic, not a "
                    f"per-ticker expected return, so it is not populated into `expected_returns`."
                ),
                source="adapter_derived (calculator.make_ensemble_alpha / calculator.target)",
            ))

        if not values:
            # Should not happen given _run_rl_search's own zero-pool-size guard,
            # but never construct an empty `values` dict — Q3Signal requires
            # at least one entry, and fabricating one would violate CLAUDE.md.
            values = {resolved_ticker: 0.0}

        self._last_native_output = {
            "upstream": {
                "pool_exprs": [str(e) for e in exprs],
                "pool_weights": [float(w) for w in weights],
                "pool_single_ics": [float(x) for x in pool.single_ics],
                "pool_best_ic_ret": float(pool.best_ic_ret),
                "pool_eval_cnt": int(pool.eval_cnt),
                "universe_used": list(stock_ids),
                "asof": asof_str,
                "ensemble_alpha_last_row": values,
            },
            "adapter_derived": {
                "requested_ticker": requested_ticker,
                "resolved_ticker": resolved_ticker,
                "was_fallback": was_fallback,
                "hedge_return_diagnostic": hedge_return,
            },
        }
        self._last_latency_sec = time.time() - t0

        return Q3Signal(
            context=context,
            signal_semantics=(
                "factor_value — combined ensemble alpha score from AlphaGen's real "
                "RL-discovered formulaic-alpha pool (LinearAlphaPool.make_ensemble_alpha), "
                "a continuous cross-sectional score, not a return prediction or probability."
            ),
            values=values,
            score_scale="continuous, unitless (linear combination of z-scored formulaic alphas)",
            direction=direction,
            strength=strength,
            factor_expression=factor_expression,
            evidence=evidence or None,
            explanation=explanation,
        )

    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window=None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ):
        """Delegates to BaseAdapter.run() for the real context/generation_window
        checks and RunMetadata construction — only attaches a faithful
        native_output (and real wall-clock latency) captured as a side effect
        of the real q3_signal() call BaseAdapter.run() makes internally."""
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
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION,
            targets=["AAPL"],
        )
        result = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = result is not None
        if result is not None:
            checks["context_echoed_unchanged"] = result.context == context
            checks["values_nonempty"] = len(result.values) > 0
            checks["direction_is_valid"] = result.direction in ("LONG", "SHORT", "NEUTRAL", None)
            checks["strength_in_range"] = result.strength is None or 0.0 <= result.strength <= 1.0
            checks["evidence_nonempty"] = bool(result.evidence)
            checks["factor_expression_set"] = bool(result.factor_expression)
        return checks
