# DECISIONS_qlib.md — standalone decision log for the Qlib adapter

Written standalone (not merged into the shared `DECISIONS.md`) per this
session's brief, for the coordinating session to review before merging.
Same fact / **Why:** / **How to apply:** style as `DECISIONS.md`.

## 2026-07-05 — Q3 methodology expansion, Wave 6 half C (final): Qlib adapter — commit pending, 20/20 harness pass

Fifth and final new Q3 mechanism in this expansion — the deliberate
**non-search** counterpoint to the other four: atlas = DEAP
genetic-programming formula-tree synthesis, finclaw = classical real-coded
GA over a factor-weight genome, alphagen = PPO reinforcement-learning
search over an alpha-expression grammar, rdagent = an LLM-agent
propose/implement/validate/iterate research loop. This adapter wraps a
**curated factor library + ML pipeline**: Qlib's own fixed, pre-defined
Alpha158 factor set (158 real named technical expressions, nothing
invented or evolved) run through Qlib's own real `LGBModel`
(gradient-boosted trees) training/prediction pipeline.

- **Repo confirmed real via GitHub API** (not just README/memory):
  `GET /repos/microsoft/qlib` → `full_name="microsoft/qlib"`, fork=False,
  archived=False, stargazers_count=45700, license=MIT, created_at
  2020-08-14, pushed_at 2026-04-22 (actively maintained through this
  session's real "today"). Latest tag `v0.9.7` (2025-08-15). The repo's own
  description cross-references `microsoft/RD-Agent` — an independent
  corroboration against this session's own already-verified `rdagent`
  upstream, not a coincidence.

- **Deliberately avoided the ancient-qlib-pin trap `alphagen_adapter.py`'s
  session found**: that session found AlphaGen's own `requirements.txt`
  pinned a stale `qlib==0.0.2.dev20` dev-build tag and correctly sidestepped
  installing real qlib at all (qlib was incidental there). Here qlib IS the
  target, so this adapter installs the real, current package: fetched
  qlib's own current README directly from
  `raw.githubusercontent.com/microsoft/qlib/main/README.md` (not memory),
  which recommends `pip install pyqlib` (supports Python 3.8-3.12); used
  `pyqlib==0.9.7`, matching the latest real GitHub tag, via a prebuilt
  `manylinux2014_x86_64` wheel — never the stale tag some *other* project
  happened to depend on.

- **Mechanism confirmed genuinely a curated library + ML pipeline by
  reading the actual source** (fetched `qlib/contrib/data/handler.py` and
  `qlib/contrib/model/gbdt.py` directly from GitHub, then imported and
  exercised the installed package), not assumed from the README or the
  original Alpha158 paper: `Alpha158.get_feature_config()` builds a real
  `kbar`/`price`/`rolling` config expanding to 158 real, named,
  pre-defined technical expressions (`KMID`, `ROC5`...`ROC60`,
  `MA5`...`MA60`, `STD5`...`STD60`, `RSV`, `CORR`, `WVMA`, etc. — confirmed
  by printing real fitted-dataset column names, not the paper's table).
  `LGBModel.fit()`/`.predict()` are a real, thin wrapper around
  `lightgbm.train()`/`Booster.predict()` — no stub, no canned output,
  confirmed by actually running `model.fit()` and observing real,
  changing per-run training-loss numbers and per-ticker prediction values
  across different requested tickers/dates. No genetic population, no RL
  policy/reward, no LLM call anywhere in this adapter's code path —
  mechanistically distinct from all four existing Q3 adapters by
  construction, not just by naming.

- **Security screening**: `grep -rniE "eval\(|exec\(|os\.system|shell=True|
  subprocess\."` across `scripts/dump_bin.py` and the installed
  `qlib/contrib/data/handler.py`/`qlib/contrib/model/gbdt.py`: zero hits.
  `grep -rniE "alpaca|robinhood|binance|coinbase|ccxt|broker_api|api_key|
  secret_key|password"` across the whole cloned repo: only
  `redis_password` (an optional, unused local Redis *cache* config key —
  this adapter never configures Redis caching), no brokerage/exchange
  credential or funded-capital requirement anywhere. No unrelated merged
  subtree (`docs/`, `examples/`, `qlib/`, `scripts/` all on-topic, 13MB
  total). MIT license, Microsoft Corporation copyright confirmed in
  `LICENSE`. This adapter never imports Qlib's own live-trading/execution
  modules (`qlib/backtest/`, `qlib/rl/`) — only data-handler, dataset, and
  GBDT-model modules plus the offline `dump_bin` conversion script.
  Confirms the brief's expectation: Qlib is a research/backtesting
  platform with no live-trading/brokerage exposure, verified rather than
  assumed.

- **Found and fixed a real, deeper-than-usual repo-root scratch-leak bug**
  (same class of issue `rdagent_adapter.py`'s session found, but with a
  root cause that survived a naive fix): Qlib's own default
  `exp_manager.kwargs.uri` is a `Path.cwd()`-based `"file:" + cwd +
  "/mlruns"` default. Overriding it with an explicit absolute path — even
  a properly-formed triple-slash `file:///abs/path` URI — was **not
  sufficient** on this sandbox: the repo is mounted at both
  `/mnt/beegfs/.../trading-ai-ensemble` and a symlinked
  `/home/.../trading-ai-ensemble` (same inode, confirmed via `stat`), and
  something in the mlflow/qlib URI-to-local-path resolution chain
  (triggered inside `LGBModel.fit()`'s first `R.log_metrics()` call) joins
  the already-absolute target path onto `os.getcwd()` again — empirically
  reproduced twice (once with the plain default, once with an explicit
  `file://` override), both times materializing a bogus nested
  `<repo_root>/mnt/beegfs/xqinag/projects/trading-ai-ensemble/mlruns` tree
  at the real repo root (caught via `git status` showing an untracked
  `mnt/` directory; deleted both times during development). Because the
  duplication depends on `os.getcwd()` at call time rather than being a
  single fixed default, no path override alone could be proven safe in
  advance. **Fix**: the real pipeline (`_run_qlib_pipeline` in
  `adapters/qlib_adapter.py`) `os.chdir()`s into this adapter's own
  gitignored scratch directory
  (`adapters/vendor/qlib/git_ignore_folder/work/`) for the duration of the
  qlib-init/train/predict calls, inside a `try/finally` that always
  restores the original working directory — confirmed empirically that
  the same duplicate-path artifact still occurs but is now confined
  entirely inside that already-gitignored scratch tree, never again at
  the real repo root. Also required `MLFLOW_ALLOW_FILE_STORE=true` (a
  separate, real issue: the mlflow version this session's pip resolved
  defaults to refusing Qlib 0.9.7's legacy filesystem tracking backend
  outright with `MlflowException: ... in maintenance mode`).
  **Why**: a `Path.cwd()`-relative default is not fully neutralized by
  overriding it with an absolute path when the filesystem has
  symlink/bind-mount duplication — the safer fix is confinement
  (chdir into a disposable, already-ignored directory) rather than trying
  to out-guess the exact downstream path-join logic.
  **How to apply**: for any future adapter whose upstream uses
  mlflow-based experiment tracking (or any other library with its own
  cwd-relative scratch-path defaults) on a filesystem with symlinked/
  bind-mounted paths, don't assume an absolute-path override is sufficient
  proof against a leak — verify empirically with `git status`/`find
  -newer` after a real run, and if a leak still occurs, confine it via
  `os.chdir()` into an already-gitignored scratch directory rather than
  chasing the exact duplication mechanism.

- **A second, unrelated real dependency-build finding**: PyPI's
  `lightgbm` 4.6.0 ships prebuilt wheels only for `manylinux_2_28_x86_64`
  (glibc ≥2.28); this sandbox's glibc is 2.27 — one minor version too old
  — so `pip install lightgbm` silently fell back to a from-source CMake
  build, which then failed with `Could NOT find OpenMP_C` (no system
  OpenMP). `conda install -c conda-forge lightgbm` (3.3.2) resolved it —
  conda-forge's build bundles its own OpenMP runtime (`libgomp`),
  sidestepping both the wheel-availability gap and the missing-OpenMP
  problem at once. Same "try conda-forge first for build-from-source
  failures" workaround this session used repeatedly (`libcst`/`pyarrow`
  needed the same treatment here too, for the identical
  no-prebuilt-wheel/needs-Rust reason found in earlier adapters this
  session).

- **`scripts/dump_bin.py::DumpDataAll` genuinely needed the repo clone,
  not just the `pyqlib` wheel**: confirmed by listing the installed
  package's files — `scripts/` is not shipped inside the PyPI wheel at
  all, only inside the GitHub source tree. This is real, substantial,
  unmodified upstream code (a CSV → Qlib-binary-format converter, ~300
  lines) genuinely exercised by this adapter, not skipped or
  reimplemented. One real gotcha found while wiring it up: `DumpDataAll`
  by default tries to write every non-excluded CSV column (including a
  literal `symbol` string column) as a float32 binary feature and crashes
  (`ValueError: could not convert string to float: 'AAPL'`) unless
  `exclude_fields="symbol"` is passed explicitly — fixed via that
  documented, first-class constructor kwarg, not a vendor patch.

- **Mechanism verified running end-to-end on real data**, not just read:
  real yfinance OHLCV for an 8-ticker large-cap US universe → real
  `DumpDataAll` conversion → real `qlib.init()` → real `Alpha158` handler
  + `DatasetH` with point-in-time train/valid/test segments → real
  `LGBModel.fit()`/`.predict()` — confirmed real per-run training-loss
  numbers, real changing per-ticker predicted scores across different
  requested tickers/dates, and real non-uniform LightGBM feature
  importances over the real 158 named columns (not a fixture).

- **Scope reductions** (documented in the adapter's own header in more
  detail):
  - **Universe**: upstream's own CSI300 China A-share benchmark universe
    (needing a separate multi-GB baostock/CN data bundle) replaced with a
    fixed pool of 10 liquid large-cap US tickers, requested ticker + up to
    7 companions (8 total) passed directly as a Python list to
    `Alpha158(instruments=[...])` — confirmed via `qlib/data/data.py`'s
    own docstrings that `D.instruments()`/`D.features()` accept a plain
    instrument list natively, no market-name file needed. Disclosed
    fallback to a fixed `AAPL`-anchored universe if the requested ticker
    has no usable real yfinance history, same pattern as
    atlas/finclaw/alphagen/rdagent's own universe-mismatch handling.
  - **Point-in-time window**: ~527 real calendar days ending at the
    (clamped-to-real-"today") requested date — a ~90-day rolling-feature
    warm-up buffer (covers Alpha158's largest default rolling window, 60
    trading days), ~300-day train, ~60-day valid, ~75-day test segment
    ending exactly at the requested date.
  - **LightGBM budget**: `num_boost_round=60`, `num_leaves=8`,
    `early_stopping_rounds=10` vs. upstream's own CSI300-scale benchmark
    config (`qlib.tests.config.CSI300_GBDT_TASK`, fetched directly from
    GitHub) — real, unmodified `LGBModel.fit()`/`.predict()`, just a far
    smaller budget (~1-2s fit time; ~15-20s total pipeline wall-clock,
    confirmed empirically, comfortably inside harness timeouts).
  - **`direction`/`strength`**: cross-sectional percentile rank of the
    real predicted score among the real companion universe on the real
    last test-segment day (top/bottom 20% → LONG/SHORT else NEUTRAL) —
    same convention atlas/alphagen use, an adapter-side translation since
    Qlib's model doesn't natively expose a 3-way directional label.
  - **`expected_return`**: the real predicted score reported verbatim (no
    rescaling) — because upstream's own label
    (`Ref($close,-2)/Ref($close,-1)-1`, an `mse`-loss regression target)
    is already a forward-return ratio, unlike alphagen's/rdagent's own
    necessary adapter-side hedge-return/correlation translations.
  - **`expected_horizon`**: `"2d"`, matching the real label expression's
    own `Ref($close, -2)` shift verbatim.

- **Harness result**: `python CONTRACT/test_harness.py --adapter
  adapters/qlib_adapter.py` → **20/20 checks passed, ALL PASS**
  (smoke_test completed in ~16s, `adapter.run()` in ~0s on cache hit —
  well inside the 300s/600s budgets).

- **Repo root confirmed clean** throughout development and after the
  final harness run (`git status --porcelain` shows only the new
  `adapters/qlib_adapter.py`; no leaked `mlruns/`, `git_ignore_folder/`,
  or `mnt/` at the repo root — all scratch state confined under
  `adapters/vendor/qlib/git_ignore_folder/work/`, already covered by the
  repo's blanket `adapters/vendor/` gitignore rule).

- Thirteenth adapter, fifth and final Q3-methodology-expansion adapter
  this session.
