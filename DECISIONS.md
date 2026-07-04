# DECISIONS.md — autonomous decisions log

Decisions made without stopping to ask, per user instruction to proceed
autonomously. Newest entries at the bottom.

---

## 2026-07-01/02 — Session B (FinGPT adapter)

- **finogrid/ security finding**: upstream `AI4Finance-Foundation/FinGPT`
  contains an unrelated crypto-payments subtree (`finogrid/`), merged under
  a misleadingly-named branch, wiring into FinGPT's sentiment code. User
  confirmed (earlier in session): ignore it, wrap only `fingpt/`. Documented
  in `adapters/fingpt_adapter.py` header. No further action needed.
- **Model choice**: FinGPT v3.3 (Llama-2-13B + LoRA), per user's earlier
  choice (best reported F1 in upstream's own benchmark).
- **News source**: upstream FinGPT model only classifies text, doesn't fetch
  news. Adapter uses `yfinance` (free, no API key) for headlines rather than
  the `massive` MCP tool, because the MCP tool's API key is server-side to
  this agent session and would not be callable from a standalone Python
  script run by someone else later (violates "adapter must be independently
  runnable").
- **HF download throttling**: anonymous HF Hub downloads were ~0.35MB/s vs
  ~8.8MB/s raw bandwidth (est. 19+ hours for the 26GB model). User provided
  an `HF_TOKEN`, stored at `adapters/vendor/FinGPT/.env` (gitignored,
  consistent with the existing `ai-hedge-fund/.env` pattern). Also enabled
  `HF_XET_HIGH_PERFORMANCE=1` (the current fast-transfer backend —
  `HF_HUB_ENABLE_HF_TRANSFER` is deprecated in huggingface_hub 1.x).
- **Detached download process**: background shell tasks did not survive a
  session boundary (confirmed — a `run_in_background` download died with no
  completion record when the harness process was torn down). Restarted the
  warm-up download via `setsid nohup ... & disown` writing to
  `/tmp/.../scratchpad/warm_fingpt.log` so it survives session teardown
  during the unattended window. This is the download all later checks in
  this session poll against.
- **Xet transfer backend disabled**: huggingface_hub 1.x defaults to the Xet
  high-concurrency transfer backend for this Xet-enabled repo. Its transfer
  log showed constant "connection struggling" backoffs through this
  sandbox's local egress proxy (127.0.0.1:8080) — effective throughput
  ~20-140KB/s (would have taken 100+ hours for 26GB). A single plain `curl`
  through the same proxy got ~8.8MB/s. Set `HF_HUB_DISABLE_XET=1` to force
  the legacy resumable HTTP downloader, which matches that ~5-9MB/s.
- **Downgraded to FinGPT v3.1 (ChatGLM2-6B) from v3.3 (Llama-2-13B)**: at
  the direct request of the user, mid-download, to cut the download size
  (~12GB vs ~26GB) and reduce risk of not finishing in the user's 2-hour
  unattended window — not because v3.3 was infeasible, just slower than
  desired. v3.1 has the second-best F1 in upstream's own benchmark table
  (mean 0.860 vs 0.886 for v3.3), so quality impact is small. ChatGLM2
  requires a different loading path than the Llama variants (`AutoModel` +
  `trust_remote_code=True` instead of `AutoModelForCausalLM`) — copied
  verbatim from upstream's own `benchmark/benchmarks.ipynb` "v3.1" cell to
  avoid guessing at undocumented API details. Also switched answer-parsing
  from slicing by `len(prompt)` to `.split("Answer:")[-1]` (matches
  upstream's own README approach) since decode() isn't guaranteed to
  reproduce the prompt byte-for-byte across tokenizers.
- **`trust_remote_code=True` note**: THUDM/chatglm2-6b ships custom modeling
  code (`modeling_chatglm.py`, `configuration_chatglm.py`,
  `tokenization_chatglm.py`, `quantization.py`) that gets executed locally —
  standard/expected for ChatGLM2 (it predates full native `transformers`
  support), from a reputable source (Tsinghua's THUDM), and explicitly
  required by upstream FinGPT's own documented usage. Not treating this as a
  new security concern distinct from the finogrid/ finding above, but noting
  it for the record since it does execute remote code.
- **Version-skew debugging chain, resolved by pinning instead of patching**:
  after the ChatGLM2-6B model finished downloading, loading it against this
  environment's originally-installed bleeding-edge `transformers` (5.12.1)
  hit a chain of six distinct incompatibilities between that very-new
  library and THUDM's 2023-era custom `trust_remote_code=True` modeling
  code: (1) `load_in_8bit=True` kwarg removed (needs `BitsAndBytesConfig`),
  (2) `config.max_length` no longer auto-populated on `PretrainedConfig`,
  (3) `bitsandbytes` 8-bit quantizer's tied-weights preprocessing raising
  `AttributeError` on `all_tied_weights_keys` (missing because the custom
  class's `__init__` never calls the modern `post_init()` that sets it —
  same error recurred in 3 different internal call sites even after
  switching away from 8-bit to fp16), (4) `torch.load` of the repo's legacy
  `.bin` (non-safetensors) weights blocked by transformers' CVE-2025-32434
  guard, requiring torch>=2.6, (5) upgrading torch alone broke
  `torchvision`/`torchaudio` ABI compatibility, cascading into peft's import
  chain, (6) after fixing all of the above under transformers 5.12.1, the
  custom `ChatGLMTokenizer._pad()` didn't accept the new `padding_side`
  kwarg tokenizer.pad() now passes. Patched (1)-(4)+(6) individually one at
  a time; by the time the 6th distinct break surfaced, decided that chasing
  transformers-5.x-vs-2023-code incompatibilities one at a time wasn't
  converging — each fix revealed a new one. **Pivoted to pinning
  `transformers==4.41.2`, `peft==0.11.1`, `accelerate==0.31.0`** (matching
  the versions upstream's own benchmark notebook comments reference: "#
  4.30.2" / "# 0.4.0"), keeping torch at 2.6.0+cu124 (still needed for the
  CVE guard, works fine with the older driver via NVIDIA's CUDA minor-version
  compatibility) and torchvision/torchaudio matched to it. Also dropped
  8-bit quantization entirely (not just as a workaround — bitsandbytes
  0.49.2 is *also* incompatible with peft 0.11.1's 8-bit LoRA injection,
  `AttributeError` on `MatmulLtState.memory_efficient_backward`); loads fp16
  instead, which the 46GB-VRAM GPUs here handle easily for a ~12GB model.
  End-to-end test (real headline -> real model -> "positive") passed after
  this pin. `adapters/fingpt_adapter.py`'s `_get_model()` now matches
  upstream's original documented loading code almost verbatim, no
  monkeypatches — the environment being version-pinned correctly made the
  adapter code itself simple again. **Lesson for future adapters wrapping
  old `trust_remote_code` research code**: pin the dependency versions the
  original code was written against from the start, rather than installing
  latest-and-patching.
- **Harness run #1 failed on a real adapter bug**: `PROMPT_TEMPLATE.format()`
  choked on the literal `{negative/neutral/positive}` text in the prompt
  (Python's `.format()` reads unescaped `{...}` as a substitution field) —
  `KeyError: 'negative/neutral/positive'`. Not a version-skew issue, just a
  bug in this adapter's own code (never exercised by earlier standalone
  script tests, which called `.generate()` directly on a hardcoded prompt
  string rather than going through `.format()`). Fixed by escaping to
  `{{negative/neutral/positive}}`. Harness run #2: **19/19 checks passed,
  ALL PASS.**
- **Confirmed no download resume across process restarts**: each kill+retry
  created brand-new `*.incomplete` blob files with random suffixes rather
  than resuming previous partial progress (seen both under Xet and the
  legacy downloader, across multiple restarts today). Practical implication:
  every restart of a model download effectively starts from 0 bytes in this
  environment — avoid restarting once a stable download is underway.

## 2026-07-02 — Session C (DeepAlpha adapter)

- **Repo candidate rejected**: `irissees/EnsembleTrading` matched the
  brief's description closest (XGBoost+LightGBM+CatBoost ensemble, overnight
  stock return prediction) but requires live Robinhood account credentials
  (`r.login(username=..., password=...)`) via an unofficial reverse-
  engineered brokerage API just to fetch training data. Not wiring real
  brokerage login credentials into an automated adapter without explicit
  user authorization — real-money account exposure, ToS risk for an
  unofficial API. Moved to a different candidate using a standard public
  data source instead.
- **Repo choice**: no real "DeepAlpha" repo exists (as the brief expected).
  Searched GitHub for XGBoost/LightGBM/CatBoost ensembles on technical
  factors for forward stock-return prediction. Best exact-keyword match
  (`irissees/EnsembleTrading`) rejected — requires live Robinhood account
  credentials via an unofficial API just to fetch data (see entry above).
  Settled on `LeoRigasaki/stock-market-prediction-engine`: proper `src/`
  package (not notebook-only), XGBoost+LightGBM ensemble, 73 engineered
  technical features, walk-forward validation, yfinance-only data (no
  brokerage creds), transparent/honest methodology docs, clean security
  scan. Full rationale in the adapter's own header docstring.
- **Pretrained models not available**: upstream's real production pipeline
  trains on a bulk Kaggle-sourced dataset (needs `KAGGLE_USERNAME`/
  `KAGGLE_KEY`, not available here) across ~15 "Day N" stages, then serves
  from saved `.joblib` artifacts that are gitignored (not in the repo).
  Minimum viable substitution: adapter calls upstream's own
  `RealTimePredictionEngine.engineer_realtime_features()` on real yfinance
  history for the single requested ticker, then trains upstream's own
  `AdvancedMLFramework.create_xgboost_model()`/`create_lightgbm_model()`
  (their hyperparameters, Optuna search skipped for speed) on that ticker's
  own 3-year history, combined via upstream's own `SimpleEnsemble`. Real
  training + real inference on real data, just scoped per-ticker instead of
  upstream's full multi-ticker batch pipeline.
- **xgboost/lightgbm install**: no prebuilt pip wheel for this platform/
  Python 3.11 combo; source build needs `cmake` (not installed). Installed
  both via `conda-forge` instead (precompiled binaries) — no dependency
  drama this time, unlike FinGPT's saga.
- **Harness result**: 21/21 checks passed on the first real run (no
  compatibility issues, unlike FinGPT) — this stack (xgboost/lightgbm/
  sklearn/pandas) doesn't have the same "old trust_remote_code vs bleeding
  edge transformers" problem since none of it depends on a custom dynamic
  model class. Smoke test completes in ~10s (no LLM, no GPU needed).

## 2026-07-02 — Comparison visualization layer (analysis/ + ui/)

User confirmed via AskUserQuestion (after I flagged an intervening message
as having injection-like characteristics — nonexistent `analysis/` module
reference, "all 3 adapters are green" phrased like a status report back to
me, "do not ask me questions" stacked under an external "IMPORTANT...you
MUST" wrapper) that the expanded task list was genuinely theirs. Proceeded
on that basis.

- **`analysis/` is not an adapter, so Iron Rule #4 doesn't apply to it**:
  "Do not read or import other adapters" (CLAUDE.md) restricts adapter
  files from importing each other. `analysis/` is the cross-adapter
  comparison layer the whole project exists to enable ("see how different
  frameworks answer it — consensus vs. divergence, side by side" — project
  description). It's the one place in the repo meant to know about all
  adapters at once. It does not import adapter *code* directly either way —
  see next point.
- **Adapters run as subprocesses, one per conda env, not imported**: the
  three adapters have mutually incompatible pinned dependencies (FinGPT
  needs transformers==4.41.2 exactly; ai-hedge-fund needs a Rust-built
  tiktoken via poetry; DeepAlpha needs conda-forge xgboost/lightgbm) and
  cannot coexist in one Python process. `analysis/_run_one.py` is a thin
  CLI (reuses `CONTRACT.test_harness.load_adapter`, not custom loading
  logic) invoked via `conda run` from `analysis/collect_results.py`, one
  subprocess per (adapter, ticker) pair, writing
  `results/{task_id}/{adapter}__{ticker}.json`.
- **Ticker set / date**: AAPL, NVDA, TSLA, BTC-USD, SPY as specified. Used
  "today" (2026-07-02) as the query date for all adapters, and a real
  3-month yfinance price history (`analysis/fetch_price_history.py`) for
  the same 5 tickers as the returns-chart backdrop.
- **ai_hedge_fund has no crypto or ETF coverage**: `ai_hedge_fund__BTC-USD`
  and `ai_hedge_fund__SPY` both returned a degenerate fallback (Q1 HOLD,
  confidence=1.0, reasoning="No valid trade available", ~2s latency vs
  ~14s for a real LLM-backed decision) — its data source
  (financialdatasets.ai) apparently only covers individual equities, not
  BTC-USD or the SPY ETF. `load_results()` in `build_visualizations.py`
  detects this generically (matches on the exact reasoning string + fast
  latency, not a hardcoded ticker list) and treats those cells as N/A
  rather than plotting a fake confidence=1.0 signal.
- **fingpt has no native Q1**: it only answers Q2 (sentiment). For the
  divergence heatmap and the returns-chart position sizing, its action is
  *derived* from `sentiment_score` (>0.2 → BUY, <-0.2 → SELL, else HOLD)
  and `|sentiment_score|` stands in for a confidence proxy. Both charts
  label this explicitly (subtitle + hover text) so it isn't mistaken for a
  native decision.
- **Cumulative returns chart is a simplified, NOT walk-forward, backtest**:
  each adapter's single point-in-time Q1 action (from the one collection
  run above) is held as a *static* position (+1 long / -1 short / 0 flat)
  across the entire 3-month price window, equal-weighted across the 5
  tickers, and compared to SPY buy-and-hold. This is NOT "what the adapter
  would have told you each day for 3 months" — it's "what if you'd taken
  today's signal and held it for 3 months." A true walk-forward backtest
  would need ~90 daily re-queries per adapter per ticker; ai_hedge_fund
  makes a real paid LLM call per query and fingpt reloads a 6B-parameter
  model per call, so that was not practical here. Stated explicitly in the
  chart title/subtitle and in `build_cumulative_returns()`'s docstring, not
  just here, so the paper doesn't need to be the only place this caveat
  lives.
- **Chart output location and `.gitignore`**: the repo's `.gitignore` had
  blanket `*.png` and `*.csv` rules (for adapter scratch output), which
  would have silently dropped the paper-ready chart PNGs. Added a scoped
  exception (`!plots/*.png`, `!plots/*.html`) rather than removing the
  blanket rule, so adapter-generated CSV/PNG scratch files elsewhere stay
  ignored. `results/` (raw JSON + price_history.csv) stays fully
  gitignored and is not committed — regenerable via `collect_results.py` +
  `fetch_price_history.py`.
- **kaleido/Chrome for static PNG export**: `plotly`'s `write_image()`
  needs a headless Chrome (kaleido v1+). `plotly_get_chrome` downloaded one,
  but it crashed on start with `error while loading shared libraries:
  libnspr4.so: cannot open shared object file` — this sandbox's system
  Chrome dependencies (NSS/NSPR) aren't installed and there's no
  passwordless sudo/apt access. Fixed by installing `nss`/`nspr` via
  conda-forge into the same env and exporting
  `LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"` before running the
  chart builder, so the dynamic linker finds them. This env var must be set
  whenever `analysis/build_visualizations.py` is run for real (not just
  imported for its functions, e.g. from `ui/app.py`, which only calls
  `fig.write_html`-equivalent via `st.plotly_chart` and never touches
  kaleido, so it doesn't need this).
- **Bug found and fixed**: `analysis/_run_one.py`'s
  `Path.write_text(result.model_dump_json(...))` used the platform default
  encoding, which resolved to ASCII in the conda-run subprocess environment
  — crashed with `UnicodeEncodeError` the moment a real yfinance headline
  contained a Unicode smart quote (’, U+2019), affecting fingpt/AAPL and
  fingpt/BTC-USD on the first collection pass. Fixed by passing
  `encoding="utf-8"` explicitly to both `write_text()` calls (success and
  error-payload paths), then re-ran just the two affected (adapter,
  ticker) pairs rather than the whole 15-run batch.
- **Streamlit dependency build issue**: same root cause as xgboost/lightgbm
  earlier — `streamlit`'s `pyarrow` dependency has no prebuilt pip wheel for
  this platform/Python 3.11 combo and needs Rust (`libcst`) to build from
  source. Installed `pyarrow` via conda-forge first (prebuilt binary), then
  `pip install streamlit` succeeded using that.
- **`ui/app.py` verification**: `streamlit run` served an apparent HTTP 500
  on first test — turned out to be an artifact of my own test harness, not
  the app: this sandbox sets `HTTP_PROXY`/`HTTPS_PROXY=127.0.0.1:8080`
  globally with no `NO_PROXY`, so my `urllib` health-check requests to
  `127.0.0.1:<streamlit-port>` were being routed through that proxy, which
  couldn't reach the ephemeral port and returned its own "Connection error"
  body dressed up as a 500. Setting `NO_PROXY=127.0.0.1,localhost` for the
  test request confirmed a real `HTTP 200`. `ui/app.py` imports its chart
  functions from `analysis/build_visualizations.py` rather than duplicating
  the chart logic, per instruction.

## 2026-07-03/04 — Wave 1: TradingAgents + FinRL adapters (parallel subagents)

Built by two parallel subagents (per user request to fan out adapter work
in pairs, verified against the blueprint image's resource-profile pairing:
LLM-API-bound + local-training-bound). Each wrote its own
`DECISIONS_<name>.md` to avoid concurrent-edit collisions on this file;
merged here after both completed and committed independently.

### TradingAgents (Q1, Q2) — commit `d751630`, 24/24 harness pass

- **Repo confirmed real**: `TauricResearch/TradingAgents` (~90k stars,
  created 2024-12-28) — matches CLAUDE.md's registered target exactly.
  README/code confirmed the bull/bear debate + risk team + Portfolio
  Manager architecture the blueprint described, and that its "social"
  analyst literally pulls Yahoo Finance news + StockTwits + Reddit.
- **Security screening clean**: no unrelated subtree (the finogrid/-style
  pattern this project now checks every new adapter for), no brokerage
  credentials, no real money — only an LLM API key needed.
- **Reused `DEEPSEEK_API_KEY`**: TradingAgents has a *native* `"deepseek"`
  provider (not a generic OpenAI-compatible passthrough), so no new secret
  was needed. `deep_think_llm="deepseek-v4-pro"` for Research
  Manager/Portfolio Manager, `quick_think_llm="deepseek-v4-flash"` for
  analysts/researchers/trader/risk debators.
- **First adapter to populate `bull_case`/`bear_case`** — every other
  adapter leaves these `None`; sourced directly from the real bull/bear
  researcher debate transcripts in graph state.
- **Cost control**: one real `TradingAgentsGraph.propagate()` run (~9-10
  real LLM calls, ~250s) is cached per `(ticker, date)` and serves both
  `q1_decision()` and `q2_sentiment()` — confirmed empirically that the
  harness's later Q1/Q2/`run()` calls all logged 0.0s, i.e. the expensive
  debate only ran once per harness pass, not up to 4 times.
- **Field mapping notes**: 5-tier `PortfolioRating` collapses to CONTRACT's
  3-way `Action`; confidence has no native numeric field so it's bucketed
  by rating-tier distance from Hold (0.85/0.65/0.5); `sentiment_score` is
  regex-parsed from a rendered markdown report (the raw Pydantic object
  isn't retained in graph state) and linearly rescaled from upstream's 0-10
  scale to CONTRACT's -1..+1; `risk_level` and `sources` are similarly
  derived from real upstream fields/behavior, not reimplemented analysis.

### FinRL (Q4, Q5) — commit `085b6fb`, 23/23 harness pass

- **Repo confirmed real**: `AI4Finance-Foundation/FinRL` — CLAUDE.md's own
  registered target, no selection ambiguity. Confirmed via WebSearch/
  WebFetch (no `gh` CLI in this sandbox) that it's a real DRL framework
  (PPO/A2C/DDPG/TD3/SAC via Stable-Baselines3) with a portfolio-allocation
  environment and free Yahoo Finance data support.
- **Security screening**: credential-requiring code exists only in
  alternate, unused data processors (JoinQuant, Sinopac/Shioaji, Alpaca,
  WRDS) — this adapter's only data path is `YahooDownloader`/yfinance,
  free and public. No brokerage account, no real money.
- **Patch required — `patches/FinRL.diff`**: `finrl/__init__.py` eagerly
  imports `finrl.trade`/`finrl.train`/`finrl.test` at package-import time,
  which transitively requires live-brokerage `alpaca`/`alpaca_trade_api`
  SDKs and the paid-subscription `wrds` package just to `import finrl` at
  all — never mind use them. Wrapped those three imports in
  `try/except ImportError`, verified (via a temporary import-blocker) that
  every module this adapter actually uses (`FeatureEngineer`,
  `YahooDownloader`, `StockPortfolioEnv`, `DRLAgent`) still imports cleanly
  without any live-brokerage/paid-vendor SDKs. Same "dead-weight eager
  import in an otherwise-fine upstream repo" pattern as a legitimate patch
  target, not upstream logic being changed.
- **`yfinance` pinned to `0.2.66`** (not left at latest 1.x): FinRL's own
  `YahooDownloader.fetch_data()` calls `yf.download(..., proxy=proxy)` — a
  kwarg `yfinance>=1.0` removed entirely. Same "pin to the vintage the
  vendor code was written against" lesson as FinGPT's transformers/peft/
  accelerate pin.
- **No pretrained weights, by design**: FinRL's own repo/tutorials ship no
  checkpoints — training is always expected to be done by the user. Trains
  **live**, real `stable_baselines3.A2C` via upstream's own `DRLAgent`,
  `TOTAL_TIMESTEPS=3000` (vs. tens/hundreds of thousands at paper scale),
  `COV_LOOKBACK_DAYS=60` (vs. tutorial's 252) — whole Q4+Q5 pipeline for 3
  tickers runs in ~50.6s inside `smoke_test()`, comfortably inside budget.
  Same "train live, scoped down" pattern as `deepalpha_adapter.py`.
- **Two real training bugs found and fixed**: (1) `pd.DateOffset(years=1.5)`
  raises `ValueError` (pandas doesn't support fractional-year offsets) —
  switched to whole-day lookback (`HISTORY_DAYS=550`); (2)
  `StockPortfolioEnv` expects upstream's own `data_split()` date-factorized
  indexing convention (one shared integer index per date across all
  tickers) — a plain `reset_index()` broke `self.data["cov_list"].values[0]`
  (ndarray has no `.values`); fixed by routing the Q4 training frame through
  upstream's own `data_split()` instead, matching what the Q5 path already
  did correctly.
