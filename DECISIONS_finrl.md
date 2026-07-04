# DECISIONS_finrl.md — autonomous decisions log for the FinRL adapter (Q4/Q5)

Self-contained log for `adapters/finrl_adapter.py`, kept separate from the
shared `DECISIONS.md` per instruction (other adapters are being built in
parallel this session and concurrent edits to the shared file would
collide). Same fact → **Why:** → **How to apply:** style as the shared log.

---

## Repo verification

- **Repo is real and matches the brief exactly**: confirmed
  `AI4Finance-Foundation/FinRL` exists via WebSearch (no `gh` CLI available
  in this sandbox — used WebSearch + WebFetch of the raw README/setup.py
  instead). README confirms: DRL framework for algorithmic stock trading,
  "train-test-trade" pipeline, PPO/A2C/DDPG/TD3/SAC via Stable-Baselines3
  (+ElegantRL/RLlib), 14+ data providers including free Yahoo Finance,
  a dedicated portfolio-allocation application/environment, DOW-30-style
  benchmarking. `setup.py`: `python_requires=">=3.7"`, classifiers through
  3.12. This is CLAUDE.md's own registered target for `finrl_adapter.py` —
  no repo-selection ambiguity like DeepAlpha's session had.
  **Why**: brief required verification before cloning, not just trusting
  the URL. **How to apply**: none needed going forward — repo confirmed.

## Security screening

- **File tree scan**: `finrl/agents`, `finrl/applications`,
  `finrl/meta/env_*`, `finrl/meta/data_processors`,
  `finrl/meta/preprocessor`, `unit_tests`, `examples`, `docs` — entirely
  on-topic for a DRL trading framework. No unrelated subtree like FinGPT's
  `finogrid/` crypto-payments merge found this time.
- **`eval`/`exec`/`shell=True`/`os.system` grep**: only hit is
  `os.system("rm -f " + path)` in `finrl/meta/data_processors/func.py` —
  a scratch-file cleanup helper, not a credential/injection risk.
- **`username`/`password`/`login`/`api_key`/`secret_key` grep**: only in
  *alternative, optional* data-source processors this adapter never
  imports: `processor_joinquant.py` (Chinese JoinQuant account),
  `processor_sinopac.py` / `shioajidownloader.py` (Taiwan Sinopac/Shioaji
  brokerage login), `processor_alpaca.py` (Alpaca paper-trading keys),
  `processor_wrds.py` (paid WRDS academic subscription). This adapter's
  only data path is `YahooDownloader` → `yfinance` — free, public OHLCV,
  no credentials, no real money, no brokerage account anywhere.
  **Why**: brief's explicit stop-condition (no live brokerage creds / real
  money / anything beyond public market data). **How to apply**: if this
  adapter is ever extended to use a different FinRL data processor,
  re-screen that specific processor file for credential requirements
  before wiring it in.

## Patch: `patches/FinRL.diff`

- **Problem**: unpatched `finrl/__init__.py` eagerly does
  `from finrl.trade import trade` / `from finrl.train import train` /
  `from finrl.test import test` at package-import time (i.e. on plain
  `import finrl`). That chain pulls in `AlpacaPaperTrading` (needs
  `alpaca`/`alpaca_trade_api` live-brokerage SDKs) and
  `finrl.meta.data_processor.DataProcessor`, which unconditionally imports
  `WrdsProcessor` — requiring the **paid WRDS academic database package**
  just to import, never mind use.
- **Chased the cascade first, then stopped**: installed
  `exchange_calendars` and `pandas_market_calendars` while diagnosing (two
  of the several missing transitive deps in that chain) before recognizing
  the chain would keep growing (next: `alpaca`, `alpaca_trade_api`, then
  potentially `wrds`, `ccxt`, `jqdatasdk`, `shioaji` if `DataProcessor` were
  ever touched) purely to satisfy imports of live-brokerage/paid-data-vendor
  code this adapter never calls.
- **Resolution**: patched `finrl/__init__.py` to wrap those three imports
  in `try/except ImportError: pass`. Verified (via a temporary
  `sys.meta_path` import-blocker for `exchange_calendars`,
  `pandas_market_calendars`, `alpaca`, `alpaca_trade_api`, `wrds`, `ccxt`,
  `jqdatasdk`, `shioaji`) that `import finrl` and every submodule this
  adapter actually uses (`FeatureEngineer`, `YahooDownloader`,
  `StockPortfolioEnv`, `DRLAgent`, `config`) import cleanly without any of
  them once the patch is applied — i.e. `exchange_calendars` and
  `pandas_market_calendars` turned out to be unnecessary in the end, just
  harmless to leave installed since they were already in before the patch
  landed.
  **Why**: CLAUDE.md's patch escape hatch ("if you must patch the upstream
  project to make it work, document it") — this is a dead-weight eager
  import, not the DRL/portfolio logic itself, and the alternative was an
  unbounded chain of unrelated broker/vendor SDK installs.
  **How to apply**: a fresh clone of `AI4Finance-Foundation/FinRL` needs
  `patches/FinRL.diff` applied to `finrl/__init__.py` before use; no other
  vendor file is modified. Skip installing `exchange_calendars` /
  `pandas_market_calendars` on a fresh setup — not needed once patched.

## Dependency install issues

- **Pre-existing `finrl_real` conda env had `pip install finrl` (PyPI
  0.3.7) instead of a git clone**: found this env already created (Python
  3.10) with `FinRL==0.3.7` installed via pip, hitting the exact
  `ModuleNotFoundError: No module named 'exchange_calendars'` version of
  the same eager-import problem above. Per this project's established
  convention (`adapters/vendor/` git clones, see `deepalpha_adapter.py`),
  uninstalled the pip package (`pip uninstall -y finrl`) and cloned
  `AI4Finance-Foundation/FinRL` into `adapters/vendor/FinRL` instead, so
  the exact patched version is visible/pinned in this repo's own vendor
  tree rather than depending on whatever PyPI happens to ship.
- **`yfinance` pinned to `0.2.66`, not left at latest (`1.4.1`/`1.5.1`)**:
  FinRL's own `YahooDownloader.fetch_data()` unconditionally calls
  `yf.download(tic, start=..., end=..., proxy=proxy, auto_adjust=...)`
  with `proxy=None` by default. `yfinance>=1.0` removed the `proxy` kwarg
  from `download()` entirely (moved to `yf.set_config(proxy=...)`),
  raising `TypeError: download() got an unexpected keyword argument
  'proxy'` on every single call. No vendor source was patched for this —
  pinned `yfinance==0.2.66` (last 0.2.x release) instead, which still
  accepts the kwarg. Same "pin to match the vintage the vendor code was
  written against" lesson as FinGPT's transformers/peft/accelerate pin
  this session.
- **`pydantic` was missing from the env**: `CONTRACT/schemas.py` imports
  it and the env had never had it installed (env was set up for FinRL's
  own deps, not the CONTRACT layer). `pip install pydantic` — no version
  conflicts.
  **Why/How to apply**: a from-scratch `finrl_real` setup should install,
  in this order: `stable-baselines3[extra] gymnasium stockstats
  scikit-learn pandas numpy matplotlib torch`, then
  `pip install "yfinance==0.2.66"` (pinned, installed last so nothing else
  upgrades it back), then `pydantic` for the harness itself. No
  conda-forge detour was needed for this stack (unlike xgboost/lightgbm/
  pyarrow earlier this session) — plain pip wheels installed fine for
  everything here.

## Adapter design / scope-reduction choices

(Full rationale lives in `adapters/finrl_adapter.py`'s own header
docstring, matching `deepalpha_adapter.py`'s style. Summary:)

- **No pretrained weights used, by design, not by necessity**: FinRL's own
  repo/tutorials never ship trained checkpoints — you're expected to train
  yourself against whatever universe/date range you want. This adapter
  trains **live**, real `stable_baselines3.A2C` (via upstream's own
  `DRLAgent`), `TOTAL_TIMESTEPS = 3000` (vs. tens/hundreds of thousands in
  upstream's published benchmarks) using upstream's own default
  `A2C_PARAMS`. Whole pipeline (fetch + engineer + train + rollout) for 3
  tickers measured **~15–25s** standalone, **~50.6s** inside `smoke_test()`
  (two independent Q4+Q5 runs) — comfortably inside the 300s/600s harness
  budgets.
- **`cov_list` construction is adapter-side data-prep glue, not
  reimplemented decision logic**: `StockPortfolioEnv` requires a rolling-
  covariance column that upstream's own `FeatureEngineer` doesn't produce
  (it's shown in FinRL's separate `FinRL-Tutorials` notebooks, not this
  repo's checked-in library code). Reproduced with `COV_LOOKBACK_DAYS = 60`
  (reduced from the tutorial's 252) purely to bound the required history
  fetch size within the time budget — documented as a scope reduction.
- **Two real training bugs found and fixed while building this**:
  1. `pd.DateOffset(years=1.5)` raises `ValueError: Non-integer years and
     months are ambiguous` — pandas doesn't support fractional-year
     offsets. Fixed by expressing the ~1.5y lookback as
     `HISTORY_DAYS = 550` (whole days) instead.
  2. `StockPortfolioEnv.__init__` does `self.data = self.df.loc[self.day,
     :]` then `self.data["cov_list"].values[0]`, which assumes upstream's
     own `data_split()` indexing convention (date factorized into an
     integer index *shared by every ticker row on that date*, so
     `.loc[day]` returns a multi-row slice and `["cov_list"]` is a Series).
     This adapter's own `_fetch_and_engineer()` used a plain
     `reset_index(drop=True)` (one unique index per row) for the Q4 path,
     so `.loc[self.day]` returned a single row and `self.data["cov_list"]`
     was already the raw covariance `ndarray`, not a Series — `.values[0]`
     then failed with `AttributeError: 'numpy.ndarray' object has no
     attribute 'values'`. Fixed by routing the Q4 training frame through
     upstream's own `data_split()` (already used correctly on the Q5 path)
     instead of a plain `reset_index`, matching the indexing convention
     upstream's own environment expects.
- **Harness result**: 23/23 checks passed (16 smoke-test sub-checks + 4
  metadata + 2 Q-method schema validations + 1 envelope/serialization
  check), all green on the fully-green run. `adapter.run()` completed in
  0.0s because it reused the harness's own Q4/Q5 in-memory cache (same
  ticker/date arguments as the direct calls in section [3]) — see the
  per-(tickers,date)/(tickers,start,end) caching note in the adapter's
  header.
