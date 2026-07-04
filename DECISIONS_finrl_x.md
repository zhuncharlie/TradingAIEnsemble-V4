# DECISIONS_finrl_x.md — FinRL-X adapter decision log

Per CLAUDE.md, this is a separate file (not the shared `DECISIONS.md`) to
avoid concurrent-edit collisions with other adapter sessions running in
parallel. Same fact/**Why:**/**How to apply:** style as the shared log.

---

## Repo identification

**Fact:** The target description ("FinRL-X: adaptive DRL that switches
between growth/defensive/neutral regimes; selects the top 25% of NASDAQ
stocks using ML factors, then allocates via DRL") was not confirmed to map
to any specific repo going in — "FinRL-X" was a project/paper name from a
planning image, not a verified GitHub identifier.

**Why:** Repo names get squatted, abandoned, or reused for unrelated
projects; CLAUDE.md and this session's own precedent (`deepalpha_adapter.py`)
require verifying a name match actually corresponds to real, on-topic code
before wrapping it.

**How to apply / what was found:**
- WebSearch for "FinRL-X github regime switching DRL portfolio" surfaced
  `AI4Finance-Foundation/FinRL-Trading`. Its own README opens with "FinRL-X:
  An AI-Native Modular Infrastructure for Quantitative Trading" — FinRL-X is
  the paper/project name; `FinRL-Trading` is the actual repo it shipped
  under. An arXiv-style PDF for the same paper also turned up in search
  results but was not relied on for anything — the GitHub repo's own README
  and source code were verified directly instead.
- Also checked the rest of the AI4Finance-Foundation family per the
  session brief's hint (FinRL-Meta, FinRL_Podracer, ElegantRL, FinRL_Crypto,
  FinRL-Tutorials) — none of those implement "top-25%-NASDAQ ML factor
  selection + regime-switching DRL allocation"; FinRL-Trading is the one
  that does, and does so almost verbatim to the target description.
- Verified it's not a squat/homonym/abandoned repo: confirmed via
  `WebFetch` of `github.com/orgs/AI4Finance-Foundation/repositories` that it
  is genuinely under the real AI4Finance-Foundation org (alongside
  FinRL/FinRL-Meta/FinGPT), v1.0.0 released 2026-03-25, 3.4k stars, 1k
  forks, 317 commits, Apache-2.0 license — active and real, not vaporware.
- Cloned it (`adapters/vendor/FinRL-Trading`) and read the actual source,
  not just the README: `src/strategies/ml_bucket_selection.py` is a real,
  complete ML ensemble pipeline (RandomForest/XGBoost/LightGBM/
  HistGradientBoosting/ExtraTrees/Ridge/Stacking competition via
  `run_bucket()`); `src/strategies/adaptive_rotation/market_regime.py` is a
  real slow/fast regime detector (26-week trend + VIX, 3-day shock);
  `src/strategies/fundamental_portfolio_drl.py` / `rl_model.py` call real
  upstream FinRL DRL classes (`DRLAgent`, `StockPortfolioEnv`). This is
  genuine, runnable code — not a notebook-only or paper-only repo.
- Nothing was rejected in favor of this repo — it was the first and only
  strong candidate found, and it matched the target description closely
  enough (including the literal "top-25% NASDAQ-100" and "regime-switching"
  language) that no further candidates were pursued.

---

## Security screening

**Fact:** Two real problems were already found in upstream repos elsewhere
this session (FinGPT's unrelated `finogrid/` crypto-payments subtree; a
different adapter's candidate repo needing live brokerage credentials), so
every new adapter's upstream gets the same screening before being wrapped.

**Why:** CLAUDE.md's security stop-condition: no live brokerage/exchange
credentials, real money, or anything beyond public market data.

**How to apply / findings:**
- `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.(call|run|Popen)"`
  across `src/`, `examples/`, `deploy.sh` — zero hits.
- File tree (`src/data`, `src/strategies`, `src/backtest`, `src/trading`,
  `src/web`, `src/config`, `src/tools`, `src/utils`, `examples`, `docs`,
  `figs`) is entirely on-topic — no unrelated merged subtree.
- `api_key`/`secret`/`password`/`token`/`credential` hits are confined to
  (a) `.env.example`'s template vars (Alpaca, WRDS, FMP, OpenAI — read via
  `os.environ`/pydantic `SecretStr`, never hardcoded), (b) FMP data-fetch
  code, (c) `src/trading/`'s live Alpaca execution code. **This adapter
  never imports (c)** — no brokerage account, no real money, anywhere.
- **FMP requirement specifically avoided**: upstream's own ML
  stock-selection pipeline is designed around a pre-populated SQLite
  database (22,909 quarterly fundamental records, 2015-2026) that upstream's
  own `fetch_and_store_fundamentals.py` builds via FMP's paid-tier
  endpoints. That database isn't checked into the repo and isn't
  reproducible without an FMP key + a huge number of API calls. This
  adapter substitutes a live-yfinance-computed fundamentals panel instead
  (see "Design choices" below) — no FMP, WRDS, or Alpaca credential is
  read, required, or referenced anywhere in `finrl_x_adapter.py`.
- No LLM API key is used anywhere (`openai` is in upstream's
  `requirements.txt` for an unrelated news-sentiment feature this adapter
  never imports) — consistent with this being an ML/DRL system, not
  LLM-based, per the session brief.

---

## Environment / dependency notes

**Fact:** A dedicated `finrl_x_real` conda env was created (never shared
with another adapter's env), plus three real environment issues were hit
and resolved.

**Why / how to apply:**
- `xgboost` installed via `conda-forge` (prebuilt binary; no cmake/Rust
  build-from-source needed). `lightgbm` was deliberately **not** installed
  — see the SIGSEGV finding below; upstream's own `build_models()` already
  wraps the lightgbm import in `try/except ImportError` and just drops it
  from the model roster, so omitting it exercises a supported upstream code
  path, not a hack.
- `pandas-market-calendars` (needed transitively by
  `adaptive_rotation.utils.calendar_utils`) pulled in `numpy>=1.26` via its
  own `exchange-calendars` dependency, upgrading numpy to 2.2.6 and breaking
  scipy/sklearn/xgboost (built against numpy<1.25 in this env). Fixed by
  re-pinning `numpy==1.24.4` after installing pandas-market-calendars —
  leaves a pip dependency-conflict *warning* but everything (scipy, sklearn,
  xgboost, pandas_market_calendars) imports and runs correctly together at
  that pin. Same "pin to the vintage the rest of the stack needs" lesson as
  FinGPT's transformers pin and FinRL's yfinance pin earlier this session.
- `yfinance` pinned to `0.2.66` for the same reason `finrl_adapter.py`
  pinned it: upstream FinRL's own `YahooDownloader.fetch_data()` calls
  `yf.download(..., proxy=proxy)`, a kwarg removed in yfinance>=1.0.
- **Real, sandbox-specific SIGSEGV found and worked around (not a vendor
  patch)**: `ml_bucket_selection.py`'s `build_models()` hardcodes
  `n_jobs=-1` on `RandomForestRegressor`/`ExtraTreesRegressor`/
  `StackingRegressor`. In this sandbox (52 visible cores), letting joblib
  resolve `-1` to "all cores" makes `StackingRegressor.fit()`'s nested
  `cross_val_predict()` fork/spawn worker processes that each fit an
  OpenMP-parallel estimator (`HistGradientBoostingRegressor`, and
  originally `LGBMRegressor`) — every worker segfaults
  (`TerminatedWorkerError`, `SIGSEGV`/`SIGABRT`), reproduced under both the
  default `loky` backend and a `threading` backend, independent of
  `OMP_NUM_THREADS`/`LOKY_START_METHOD` tuning. Root-caused by fitting each
  estimator individually and bisecting; confirmed `loky.cpu_count()`
  (what `n_jobs=-1` resolves against) tracks `os.sched_getaffinity(0)` on
  Linux. Fixed entirely inside the adapter's own process: temporarily
  restrict CPU affinity to one core (`os.sched_setaffinity(0, {core})`)
  for the duration of the `run_bucket()` call only, then restore it — this
  makes joblib's `n_jobs=-1` resolve to 1, which takes the "run
  sequentially in-process, never fork" fast path. Confirmed this produces
  identical modeling results (same 6-model competition, same Stacking
  ensemble, same feature importances) in ~3s with zero crashes. This is an
  environment-level workaround around upstream's own hardcoded parallelism
  setting, not a modification to any vendor file — no `patches/*.diff` was
  needed for it.
- This adapter also depends on the separate `AI4Finance-Foundation/FinRL`
  package (FinRL-Trading's own DRL scripts import
  `finrl.agents.stablebaselines3.models.DRLAgent` etc., but `finrl` is not
  declared in FinRL-Trading's own `requirements.txt`/`setup.py`). Reused
  the identical `adapters/vendor/FinRL` clone + `patches/FinRL.diff` that
  `adapters/finrl_adapter.py` already set up this session for the exact
  same upstream repo and the exact same eager-import problem — not
  re-authored, not a new patch file, and no Python import of
  `adapters/finrl_adapter.py` itself occurs anywhere (vendor/ is gitignored
  either way; this is "clone the same public repo to the same local path",
  not cross-adapter coupling).

---

## Design choices / scope reductions

**Fact:** Several places where this adapter substitutes live yfinance data
or a reduced scope for upstream's paid-data/paper-scale pipeline.

**Why:** Per the session brief, when upstream ships no pretrained
artifacts or needs data this session doesn't have access to (here: FMP's
paid quarterly-fundamentals history), prefer training/fitting live on real
yfinance data, scoped down to fit the harness's timeouts — documented, not
silent.

**How to apply:**
- **Universe**: a static 30-ticker NASDAQ-100-style snapshot
  (`NASDAQ_UNIVERSE` in the adapter) substitutes upstream's live FMP-based
  NASDAQ-100 constituent fetch. The ranking *logic* is 100% upstream's own
  `run_bucket()`, untouched.
- **Fundamentals**: computed live from `yfinance`'s
  `quarterly_financials`/`quarterly_balance_sheet` for 9 of upstream's 28
  `FEATURE_COLS` (pe, ps, pb, roe, gross_margin, operating_margin,
  debt_to_equity, cur_ratio, EPS — same names/semantics, smaller subset),
  passed as the real `feature_cols` parameter `run_bucket()` already
  accepts. PE/PS/PB use a crude quarterly×4 annualization rather than
  upstream's true TTM/annual figures.
- **Fiscal-quarter alignment**: yfinance reports each company's own fiscal
  quarter-end (e.g. NVDA's Jan/Apr/Jul/Oct cycle) rather than a shared
  calendar grid; this adapter snaps each date to the nearest standard
  calendar quarter-end before calling `run_bucket()`, otherwise its
  date-based train/val/infer split fragments the universe across dozens of
  near-but-not-identical dates. Pure date-bucketing glue, not a change to
  the selection logic.
- **`date` parameter caveat for Q3/Q4's stock-selection stage**: yfinance's
  quarterly statements always reflect the *latest available* quarters as of
  when the adapter runs, not "as of the requested `date`" — unlike
  upstream's own point-in-time FMP database. `date` is passed through for
  labeling only; DRL training windows (which use price history, not
  quarterly fundamentals) ARE correctly point-in-time.
- **Q4 DRL training**: reuses the exact real-upstream-FinRL building blocks
  and reduced budget (`TOTAL_TIMESTEPS=3000`, `COV_LOOKBACK_DAYS=60`,
  `HISTORY_DAYS=550`, A2C via `DRLAgent`/`StockPortfolioEnv`)
  `adapters/finrl_adapter.py` already validated this session, rather than
  `rl_model.py`'s own `train_a2c`/`train_ppo`/`train_ddpg` helpers (whose
  `total_timesteps` — 50000/80000/50000 — are hardcoded literals with no
  override, and would blow past the harness's timeouts three times over if
  run as upstream wrote them).
- **Q4 universe**: the DRL allocator always trades upstream's own
  ML-selected top-25% subset (reflecting the target's fixed "select, then
  allocate" pipeline), not an arbitrary caller-supplied ticker basket. The
  harness's `tickers` argument is intersected with the selected set only
  for an informational note in `rationale`.
- **Q4 `regime`**: from upstream's own
  `adaptive_rotation.market_regime.detect_slow_regime()`, fed real weekly
  `^GSPC`/`^VIX` closes and upstream's own shipped
  `AdaptiveRotationConf_v1.2.2.yaml`. `SlowRegimeState.RISK_ON/NEUTRAL/
  RISK_OFF` mapped to CONTRACT's `Regime.BULL/SIDEWAYS/BEAR`. Upstream's own
  `effective_cash_floor` output is blended with the DRL policy's own cash
  allocation (`cash_ratio = max(drl_cash, regime_cash_floor)`, rescaling
  weights proportionally) so the regime genuinely modulates the final
  allocation.
- **Caching**: the ML panel/ranking is built once per process (doesn't vary
  with `date`, per the caveat above); DRL training is cached per
  (selected-ticker-set, date) — same rationale as `finrl_adapter.py`'s own
  cache (the harness calls each Q method directly and again via
  `adapter.run()` with identical arguments).

---

## Validation result

`python CONTRACT/test_harness.py --adapter adapters/finrl_x_adapter.py`
(env `finrl_x_real` active): **22/22 checks passed — ALL PASS**.
`smoke_test()` completed in ~114s (budget 300s); `adapter.run()` completed
in 0.0s on the second call (cache hit — first cold run, inside
`smoke_test()`, took the ~114s above).
