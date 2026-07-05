# DECISIONS_alphagen.md — AlphaGen adapter session log

(Written separately from the shared `DECISIONS.md` per this session's brief,
since a concurrent RD-Agent adapter session was editing that file at the
same time. Same fact/**Why:**/**How to apply:** style as the shared log.)

## 2026-07-05 — AlphaGen adapter — commit pending, 20/20 harness pass

- **Target repo confirmed real via GitHub-API redirect, not a lone search
  snippet.** Web search for "AlphaGen" + the KDD 2023 paper title pointed at
  `github.com/RL-MLDM/alphagen`. `GET api.github.com/repos/RL-MLDM/alphagen`
  returned HTTP 301 → `api.github.com/repositories/510600247` →
  `ICT-FinD-Lab/alphagen` (1141 stars, 312 forks, created 2022-07-05, pushed
  2026-06-04). Corroborated independently by a paper-author's own blog post
  and by Papers-with-Code's listing for arXiv:2306.12964, both pointing at
  the same repo ID under its original name.
  **Why:** this session's brief specifically warned that a prior adapter's
  web search once fabricated a plausible-looking 404 GitHub citation for a
  paper's "code" — a repo transfer (real org rename) can look identical to a
  dead/fabricated link (both 301/404 in a naive check) unless you follow the
  redirect to its actual target and cross-check with a second independent
  source.
  **How to apply:** when `GET api.github.com/repos/<owner>/<repo>` returns
  301, always follow to `api.github.com/repositories/<id>` before concluding
  the repo doesn't exist — a permanent redirect means "moved," a 404 means
  "gone/never existed," and only the latter should trigger a fallback search.

- **Mechanism confirmed genuinely RL, not GP/GA, by reading (and running)
  the actual training script, not the README's marketing language.**
  `scripts/rl.py::run_single_experiment` trains `sb3_contrib.ppo_mask.
  MaskablePPO` (real PPO) against `alphagen/rl/env/wrapper.py::AlphaEnv`, a
  genuine `gymnasium.Env` whose action space is one Discrete action per
  operator/feature/constant/delta-time/SEP token, with `action_masks()`
  enforcing valid-expression-grammar constraints, and whose reward is the
  marginal IC improvement from completing a valid alpha expression
  (`LinearAlphaPool.try_new_expr`). This repo *also* ships `gp.py`/
  `gplearn/` and `dso.py`/`dso/` — real, functioning genetic-programming and
  deep-symbolic-optimization code — but the README itself labels these
  "Baselines" the paper's RL method is compared against, not the method
  itself. This adapter never imports `gp.py`, `gplearn/`, `dso.py`, or
  `dso/`.
  **Why:** this session's brief (echoing atlas_adapter.py's QuantaAlpha
  rejection) required verifying the actual algorithm structure, not
  "evolutionary"/"genetic"/"RL" vocabulary in a README, since projects
  routinely ship multiple mechanisms side by side (here: RL as the paper's
  actual contribution, GP/DSO as comparison baselines in the same repo).
  **How to apply:** when a repo's own README distinguishes a "main method"
  from "baselines," grep which modules the adapter code path actually
  imports and confirm none of the excluded-mechanism files are reachable —
  don't rely on file *presence* alone to judge what a repo "is."

- **Avoided the `qlib`/`baostock` dependency chain entirely, without
  touching any vendor file.** Upstream's `alphagen_qlib/stock_data.py::
  StockData.__init__` unconditionally calls `self._init_qlib()`
  (`import qlib; qlib.init(...)`), but only actually *queries* Qlib
  (`QlibDataLoader`/`D.calendar()`) inside `_get_data()`, which is skipped
  whenever a `preloaded_data` tuple is passed to the constructor — upstream's
  own documented "Choice 2: Adapt to external pipelines" path. This adapter
  defines `USStockData` (in `adapters/alphagen_adapter.py`, not a vendor
  file) — a plain subclass whose `__init__` sets the same attributes
  (`data`, `_dates`, `_stock_ids`, `max_backtrack_days`, `max_future_days`,
  `_features`, `device`) directly from a tensor built from real yfinance
  OHLCV, and never calls `_init_qlib()`. Every downstream consumer
  (`Expression.evaluate()`, `QLibStockDataCalculator`, `AlphaEnv`) only
  touches these same attributes/properties, all inherited unmodified from
  upstream.
  **Why:** upstream's own `requirements.txt` pins `qlib==0.0.2.dev20` — an
  ancient dev-build tag — and `baostock` for its default China A-share data
  source; getting a real, current `qlib` installed just to satisfy a lazy
  `import qlib` this adapter would never otherwise exercise (no
  `QlibDataLoader` call ever happens once `preloaded_data` is supplied)
  would have meant either fighting a stale pin or a heavy, fragile
  dependency purely for an unused code path.
  **How to apply:** when a project's own `__init__` does lazy, optional
  heavy-dependency setup gated by a code path your adapter will never
  reach (here: the *only* consumer of `qlib` inside `StockData` is the
  branch skipped by `preloaded_data`), a documented adapter-side subclass
  that supplies the same public attributes is a legitimate "wrap, don't
  patch" solution — confirm by reading exactly which methods use the
  lazy-loaded import before assuming you need the dependency installed.

- **Security screening**: `eval()`/`exec()` grep hits exist in this repo
  but only inside `gp.py`/`dso.py`/`dso/task/regression/dataset.py` — the
  GP/DSO baseline scripts this adapter never imports (see mechanism
  confirmation above) — evaluating upstream-authored formula-string
  literals, not untrusted input. Zero `api_key`/`secret`/`broker`/`alpaca`/
  `binance` hits anywhere in the repo. The only external-service touchpoint
  in the whole project is an optional `openai` client
  (`alphagen_llm`/`scripts/rl.py`'s `use_llm=True` branch) this adapter's
  code path never reaches — no LLM key used or needed, matching this
  session's brief's expectation that a pure RL-search system needs none.
  No live brokerage/exchange account or real money anywhere in the code
  path used (`backtest.py`/`trade_decision.py`, upstream's own
  "Experimental" paper-backtest modules, are never imported). No LICENSE
  file in the repo (confirmed via `GET .../license` → 404), same situation
  as atlas_adapter.py's upstream — used here read-only, in-process, for
  side-by-side research comparison only.

- **Environment**: CPU-only `torch` + `stable_baselines3`/`sb3_contrib`/
  `gymnasium`/`shimmy` all had prebuilt wheels for this platform — no
  cmake/Rust/conda-forge fallback needed (unlike xgboost/lightgbm/pyarrow/
  libcst/tiktoken earlier this session). `qlib`/`baostock`/`openai`
  deliberately not installed (see dependency-avoidance note above — none
  are on this adapter's actual import path).

- **Scope reductions**:
  - **RL training budget**: upstream's own `scripts/rl.py::main()` uses
    200,000-350,000 PPO timesteps per experiment (tens of minutes to
    hours). This adapter uses `TOTAL_TIMESTEPS=4000`, `POOL_CAPACITY=5`, a
    smaller `LSTMSharedNet` (`n_layers=1, d_model=64`), `n_steps=128` — real,
    unmodified `MaskablePPO.learn()`/`AlphaEnv`/`LinearAlphaPool` code, ~60s
    wall-clock per fresh training run in this sandbox (CPU only) — the same
    category of timestep scope-reduction `finrl_adapter.py`
    (`TOTAL_TIMESTEPS=3000`) and `finrl_x_adapter.py` documented for their
    own DRL training. Cached per `(universe, date)` in-process since the
    harness calls `q3_signal()` directly and again via `adapter.run()` with
    the same ticker/date (confirmed: full harness `adapter.run()` completed
    in 0.0s on cache hit).
  - **Universe**: upstream's own experiments use Qlib's CSI300 (China
    A-share) universe via baostock. This adapter uses a fixed pool of 10
    liquid US large-caps (`AAPL, MSFT, NVDA, GOOGL, AMZN, META, JPM, XOM,
    UNH, V`), taking the requested ticker + up to 7 companions (8 total) —
    enough stocks for upstream's own cross-sectional IC/Rank-IC calculations
    to be meaningful. Verified the disclosed-fallback path directly: an
    invalid ticker (`ZZZZINVALIDTICKER`) correctly triggers a second,
    disclosed training run against a fallback universe (`AAPL` +
    companions), completing in ~122s total (two training runs) — still
    comfortably inside the 600s `adapter.run()` budget.
  - **`VWAP` feature approximation**: upstream's expression grammar takes
    `VWAP` as one of six raw input features, sourced from Qlib in upstream's
    own pipeline. Plain yfinance OHLCV has no true intraday VWAP; this
    adapter substitutes the standard typical-price approximation
    `(High + Low + Close) / 3` as the input feature value — an input-data
    substitution, not a change to any evaluation, RL, or pool-selection
    logic (all unmodified upstream).
  - **Point-in-time train/test split**: `train_end` = requested `date` minus
    30 calendar days (headroom for the real 20-trading-day forward-return
    target `Ref(close,-20)/close-1`, upstream's own example target); 600
    calendar days of training history before that. The separate test window
    ends exactly at the requested `date` (`max_future_days=0`, no
    lookahead), with ~90 calendar days of backtrack buffer covering
    upstream's largest real rolling-window operator (`DELTA_TIMES` up to
    40 trading days).
  - **`expected_return`**: a real long-short spread computed from upstream's
    own already-exposed tensors (`QLibStockDataCalculator.
    make_ensemble_alpha()` and `.target`) — simple top-quartile-minus-
    bottom-quartile bucket-mean arithmetic over real data, not a
    reimplementation of any alpha-mining/RL logic, disclosed as an
    adapter-side derived metric (alphagen doesn't ship an equivalent
    convenience function of its own, unlike atlas's upstream
    `evaluate_func.evaluate()`).

- **Result**: `python CONTRACT/test_harness.py --adapter
  adapters/alphagen_adapter.py` → **20/20 checks passed**. `smoke_test()`
  in 62.8s (well under the 300s budget); full `adapter.run()` in 0.0s on
  cache hit (both `q3_signal()` calls in the harness use the same
  `(ticker="AAPL", date="2024-01-15")` pair). Real discovered alpha
  expressions and IC values are printed verbatim in `supporting_evidence`
  (e.g. `Var(Sum(Add(30.0,$vwap),5d),20d)` with `single IC=0.0766`), not
  fabricated.

- Thirteenth adapter, fourth Q3 (alpha-signal) adapter this expansion
  (after atlas: DEAP genetic-programming formula-tree synthesis; finclaw:
  classical real-coded GA over a fixed weight-vector genome) — this one is
  reinforcement learning (PPO) directly constructing formula-token
  sequences, a distinct algorithm family from both prior Q3 adapters.
