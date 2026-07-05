# DECISIONS_finclaw.md — FinClaw adapter (Q3), commit pending, 20/20 harness pass

Written separately from the shared `DECISIONS.md` per this session's
instruction (a parallel Vibe-Trading adapter session is editing that file
concurrently). To be merged in later by whoever integrates both.

Target brief (`SESSION_BRIEFS.md`, Session D): "FinClaw: 484 genetically-
evolved alpha factors, forward-validated. Selects the most predictive
factors for a given stock/period." The brief itself said this name was
**not confirmed** to exist as a real repo and told this session to search
literally for "FinClaw" and "484 alpha factors genetic algorithm trading".

## Repo search process

- **`aifinlab/FinClaw`** (github.com/aifinlab/FinClaw) — real repo (203
  stars, 34 forks, Apache-2.0, confirmed via the GitHub REST API). Reading
  its actual README shows a completely different product: a Chinese
  open-source LLM-agent "Skills" framework for financial institutions
  (banking/securities/insurance/funds/futures/trust — "六只金融龙虾" / "six
  financial lobsters"), 1000+ prompt/tool Skills, Node.js. No genetic
  algorithm, no alpha factors, no forward validation anywhere. Rejected:
  pure name collision, wrong domain.
- **`NeuZhou/finclaw`** (GitHub) — the literal name+number match: its
  cached description says "484 factors, genetic algorithm, walk-forward
  validated, no API keys needed", almost verbatim to the brief. But
  `GET api.github.com/repos/NeuZhou/finclaw` 301-redirects (renamed) to
  `NeuZhou/stratevo`. That repo's commit history has exactly 4 commits, the
  first literally "Initial commit: FinClaw product showcase"
  (2026-04-17) — the public GitHub repo was created as a README-only
  marketing page, not a code repo (confirmed via `GET .../contents/*`:
  just `README.md` + 2 chart PNGs + empty placeholder dirs, **zero Python
  source**). Its own README "Get Access" section says the real engine is
  gated behind a paid "StratEvo Pro" product (email/Discord contact). This
  is the clearest instance this session found of the "buzzwords not
  matching actual code" trap the brief warned about (per `atlas_adapter.py`
  precedent) — here even more extreme, since there's no code at all to
  mismatch, only marketing copy reusing the exact "484 factors / walk-
  forward / Monte Carlo" vocabulary being searched for. Rejected **as a
  GitHub repo**.
- **However**: that same GitHub repo's PyPI project page
  (`pypi.org/project/finclaw-ai/`) still hosts 17 real uploaded releases
  (0.1.0 → 5.6.1, latest 2026-04-10 — a week *before* the GitHub repo was
  pivoted to the marketing page on 2026-04-17). Downloaded and inspected
  the `finclaw_ai-5.6.1.tar.gz` sdist directly: a real, substantial
  (88,606 lines of Python, 500+ files), AGPL-3.0-licensed, CI/codecov-
  badged package with a genuine `finclaw/evolution/auto_evolve.py`
  implementing a real generational genetic algorithm (`AutoEvolver`,
  `StrategyDNA`, Polynomial Mutation per Deb & Goyal 1996) and a real
  `finclaw/evolution/walk_forward.py` (multi-window out-of-sample
  validation with explicit look-ahead-bias guards). **Installed
  `finclaw-ai==5.6.1` in a fresh conda env and ran it for real**
  (`finclaw evolve --market us`, real yfinance data) rather than trusting
  the README — confirmed genuinely functioning (see "Verification" below).
  Conclusion: the *GitHub* repo is now vaporware/marketing, but the
  *PyPI-distributed source* (same author/project, one release earlier) is
  real. This adapter wraps that PyPI-distributed source;
  `upstream_repo = "https://pypi.org/project/finclaw-ai/"` rather than the
  GitHub URL, with the GitHub situation disclosed in the adapter header
  rather than hidden.

Because the literal target name matched real, functioning code once
verified this way, no fallback-to-"closest analogue" search was needed
(unlike ATLAS's session). For completeness, this session did survey the
wider "genetic algorithm alpha factor" GitHub space before finding the
above: `Morgansy/Genetic-Alpha`, `WYFHHH/QuantGplearn`, `IIcodehub/GP-
Alpha-Miner`, `bigsuperFishfish/AutoAlpha`, `weiqingv/DEAP-alpha-learner`,
`jiangtiantu/FactorMining` — all real, but all are tree-based/GP formula
*synthesis* engines (same mechanism family as `atlas_adapter.py`'s
upstream), so none would have qualified as a distinct second adapter
anyway (see "Distinctness from atlas_adapter.py" below).

## The marketed "484 factors" figure does not match the real, executed code

Read past the README into the actual source (same discipline
`atlas_adapter.py` applied to `chrisworsey55/atlas-gic`/`QuantaAlpha`) and
found a real, material inconsistency **within this one package**:

- The README's own category table doesn't even sum to itself
  (14+13+13+12+14+11+11+11+10+2+2 = 113, not the claimed "284 general";
  113+200 = 313, not 484).
- The actual CLI command (`finclaw evolve`) dispatches to
  `finclaw.evolution.auto_evolve.AutoEvolver` (confirmed by reading
  `cli/commands/strategy.py:cmd_evolve` directly). That module's own
  `print()` banner says **"57-dim Factors"**; introspecting its real
  `StrategyDNA` dataclass gives **74 total genome fields, 41 of which are
  `w_*` factor weights** (real technical + fundamental factors: momentum,
  mean-reversion, volume, MACD, Bollinger, KDJ, OBV, ATR, ADX, ROC,
  Williams %R, CCI, MFI, Donchian, Ichimoku, Elder Ray, beta, R², PE, PB,
  ROE, revenue/profit YoY & QoQ, PS, PEG, gross margin, debt ratio,
  cashflow, etc.) — real and rich, but not 484.
- A separate, not-CLI-wired `unified_evolver.py` and a separate, opt-in,
  `OPENAI_API_KEY`-gated `factor_discovery.py` ("LLM-powered factor
  discovery inspired by Microsoft's RD-Agent") also exist in the package
  but are not used by this adapter.

**This adapter's code and documentation use the real, verified number (41
evolved factor weights / 74-field DNA genome), not the marketed 484.**
`supporting_evidence` always reports real top-weighted factors from the
real evolved DNA.

## Distinctness from atlas_adapter.py (already wraps Yitong-Guo/Genetic-
Algorithm-for-quantitative-alpha-factors-mining this session, 20/20 pass)

Mechanistically different, not just a different repo doing the same thing:

- `atlas_adapter.py`: **Genetic Programming** — DEAP `gp.PrimitiveTree`
  expression trees are the individuals; NSGA-II searches over the space of
  *formula structures*, discovering new factor formulas from primitive
  operators.
- `finclaw_adapter.py`: **classical real-coded Genetic Algorithm over a
  fixed-dimension weight vector** — the individual (`StrategyDNA`) is a
  74-field genome (41 factor *weights* over a fixed, pre-computed
  indicator set, plus risk/entry/exit parameters), evolved via Polynomial
  Mutation + elitism. It doesn't invent new formulas; it evolves how much
  to trust and how to combine an existing fixed factor set — matching the
  brief's "selects the most predictive factors" framing by reading the
  evolved DNA's `w_*` magnitudes, not by synthesizing expression trees.

Distinct algorithm family, distinct upstream project/author, distinct
license (AGPL-3.0 vs. none), distinct fitness function (walk-forward
Sharpe×Return/MaxDD with Sortino/consistency/turnover terms vs. atlas's
Hedge_Return/Hedge_Return_Std) — not a duplicate or a trivial reskin.

## Verification the package is real and functioning (executed, not just read)

- `pip install finclaw-ai==5.6.1` in a fresh `finclaw_real` conda env;
  `finclaw --help` / `finclaw demo` / `finclaw evolve --market us` all ran.
- Ran a real, non-demo evolution end-to-end: real yfinance OHLCV for AAPL +
  8 large-cap companions, real `AutoEvolver.evolve(generations=30)`
  (population=24) — genuine generational progress (fitness climbed from
  -0.95 at gen 0 to 144.70 in one run / 87.0 in the harness's actual run,
  with visible stagnation-escape re-injections along the way — not a
  canned number), producing a real winning `StrategyDNA` with real
  walk-forward OOS annual_return in the 20-80% range across runs, real
  Sharpe, real win rate, real simulated trade counts, and real top evolved
  factor weights that differ run to run (`w_r_squared`, `w_mean_reversion`,
  `w_bollinger`, `w_support`, `w_ps`, `w_quantile_lower`, etc. across
  different test runs) — confirms the GA is really exploring, not
  returning a fixed answer.
- Confirmed the real `score_stock(idx, indicators, dna)` function produces
  a real live per-day/per-ticker [0,10] score when fed a real per-ticker
  indicator dict built from upstream's own real `compute_rsi`/
  `compute_macd`/`compute_bollinger_bands`/`compute_kdj`/
  `compute_obv_trend`/`compute_ma_alignment`/`compute_atr`/`compute_roc`/
  `compute_williams_r`/`compute_cci`/`compute_mfi`/
  `compute_donchian_position`/`compute_aroon`/`compute_price_volume_corr`/
  `compute_linear_regression`/`compute_volume_ratio` functions (all real,
  unmodified, individually imported from `finclaw.evolution.auto_evolve`).

## Security screening

- `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.|socket\.|
  api_key|secret|password|broker|alpaca|robinhood"` restricted to every
  module this adapter actually imports (`auto_evolve.py`,
  `auto_download.py`, `data_loader.py`, `walk_forward.py`, `models.py`,
  `invariants.py`): **zero hits**.
- `evolve()` internally seeds a handful of extra dynamic factors via
  `factor_discovery.create_seed_factors()`/`FactorRegistry`. Read
  `factor_discovery.py` directly: seed factors are fixed, hardcoded
  formula strings (no network/LLM call), evaluated via
  `eval(formula, sandbox)` where `sandbox` is a **restricted globals
  dict** (numpy/math functions + the OHLCV arrays only — no `__builtins__`,
  no `os`, no filesystem/network access) — same risk class as DEAP/
  gplearn's own compiled-expression evaluation used elsewhere this
  session, not arbitrary code execution. The separate LLM-powered
  `discover-factors` CLI path (`OPENAI_API_KEY`-gated) is never called by
  this adapter.
- No live brokerage/exchange account or funded capital anywhere in the
  path used: `AutoEvolver` reads local CSVs only; this adapter populates
  them from free, keyless Yahoo Finance data via `yfinance` (same source
  `finrl_adapter.py`/`deepalpha_adapter.py` already use). Upstream's real
  live-trading/brokerage modules (`exchanges/`, `crypto/live_runner.py`,
  `trading/live_engine.py` — real Alpaca/Binance/Kraken/etc. credential
  code) exist in the package but are never imported by this adapter.
- No LLM API key needed anywhere in this adapter.
- AGPL-3.0 license (unlike atlas's unlicensed upstream): used read-only,
  in-process, for side-by-side research comparison — same
  non-redistribution posture as every other adapter here.

## Dependency / environment notes

- `conda create -n finclaw_real python=3.11`, then
  `pip install "finclaw-ai==5.6.1" "yfinance>=0.2.0" pydantic` — plain pip
  wheels throughout, no cmake/Rust/conda-forge fallback needed (unlike
  xgboost/lightgbm/pyarrow/libcst earlier this session).
- No `adapters/vendor/` git clone: `finclaw-ai` is consumed as a normal
  installed PyPI dependency (like DEAP for `atlas_adapter.py`), not a
  git-cloned tree, since PyPI (not the current GitHub repo) is its real
  source-distribution channel right now.
- A stale editable install from an earlier interrupted session (pointing
  at a since-wiped scratch directory) had to be uninstalled and replaced
  with a real `pip install finclaw-ai==5.6.1` (non-editable) — resolved by
  `pip uninstall -y finclaw-ai` + removing the leftover
  `__editable__.finclaw_ai*` shim files, then a clean reinstall.

## Design / scope choices

- **GA budget**: upstream's own CLI defaults are `population=30,
  generations=100, max_stocks=500`. This adapter uses `population=24,
  generations=30, max_stocks=9` (requested ticker + up to 8 large-cap
  companions from upstream's own `DEFAULT_US_SYMBOLS`, giving `AutoEvolver`
  a genuine cross-sectional universe rather than a single-stock
  degenerate case) — real, unmodified `AutoEvolver.evolve()`, ~75-100s
  wall-clock in this sandbox, comfortably inside harness timeouts (smoke
  <300s, `run()` <600s). Cached per `(ticker, date)` in-process — confirmed
  in the harness run that the second/third calls to the same
  `(ticker, date)` reused the cache (`adapter.run()` completed in 0.0s).
- **Point-in-time data**: upstream's own `download_us_data()` always ends
  at `datetime.now()`, which would leak future data relative to a
  historical requested `date`. This adapter fetches yfinance history
  itself windowed to end at the requested `date` (420 calendar days of
  lookback, clamped to not exceed real "today"), saved via upstream's own
  real `_save_ohlcv_csv()` helper (not reimplemented) in the exact CSV
  schema `AutoEvolver.load_data()` expects.
- **`factors/` CWD side effect**: upstream's `evolve()` hardcodes
  `create_seed_factors("factors")` — a literal relative path. This adapter
  runs the real `evolve()` call inside `contextlib.chdir()` into its own
  per-request temp directory so upstream's real behavior is preserved
  without littering the trading-ai-ensemble repo tree with a stray
  `factors/` directory.
- **Ticker/universe**: US equities via yfinance only (free, keyless,
  consistent with other US-equities adapters this session). If the
  requested ticker has no usable yfinance history for the point-in-time
  window, falls back to `AAPL` with an explicit note in
  `supporting_evidence` (same disclosure pattern as `atlas_adapter.py`'s
  own ticker-universe fallback).
- **`direction`/`strength`**: derived from the real `score_stock()` [0,10]
  output — `LONG` if score ≥ 6.0, `SHORT` if score ≤ 4.0, else `NEUTRAL`;
  `strength = min(1.0, abs(score-5.0)/5.0)`. An adapter-side 3-way mapping
  of upstream's continuous score (upstream's own trading logic uses a
  per-DNA evolved `min_score` entry threshold rather than a fixed label).
- **`supporting_evidence`**: real top-3 `w_*` factor weights by magnitude
  from the real winning DNA, the real `score_stock()` value, and the real
  walk-forward OOS profitable-window count.
- **`expected_return`**: the real winning strategy's walk-forward
  `annual_return` (upstream's own metric, unmodified).
- **`expected_horizon`**: derived from the real evolved DNA's own
  `hold_days` field.
- **`signal_type`**: `FACTOR` (same choice as `atlas_adapter.py`, matches
  CONTRACT's designation for a discovered/weighted quantitative factor
  signal).

## Harness result

`python CONTRACT/test_harness.py --adapter adapters/finclaw_adapter.py`
(env `finclaw_real` active): **20/20 checks passed, ALL PASS**. Smoke test
completes in ~85-100s (population=24, generations=30, 9-stock universe);
full `adapter.run()` call reuses the cached evolution result and completes
in 0.0s.
