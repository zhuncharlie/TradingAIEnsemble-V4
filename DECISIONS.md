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

## 2026-07-04 — Wave 2, half A: Prediction Arena adapter — commit `22de7ef`, 22/22 harness pass

- **The literal "Prediction Arena" is a real project with no public code.**
  It's arXiv 2604.07355 + a live site (predictionarena.ai) — six frontier
  models trading real capital on Kalshi/Polymarket over 57 days. Fetched the
  arXiv HTML directly and confirmed no code-availability statement or GitHub
  link exists anywhere in the paper.
- **A web-search summary hallucinated a specific GitHub citation**
  (`github.com/foresight-arena/analysis`) for this paper's "released"
  code. Checked directly via the GitHub REST API: that repo returns 404. The
  `foresight-arena` org is real but is a different, unrelated project
  (on-chain prediction competition on Polygon). Concrete example of why a
  prose web-search summary must be checked against a primary source
  (GitHub/arXiv API) before being trusted, not just this project's own
  memory-of-training-data risk.
- **A second candidate, `spfunctions/prediction-market-model-benchmark`,
  was rejected as a likely content-farm placeholder**: real repo (not
  hallucinated), description matches the brief almost verbatim, but the
  owning account was created 2026-03-14 and already owns 35 repos, this
  specific repo has 0 stars, and every source directory is empty
  (skeleton-only). Even a real, confirmed-to-exist repo can still be an
  unreliable source — GitHub-API existence alone isn't sufficient
  verification, actual implementation content matters too.
- **Settled on `Metaculus/forecasting-tools`** (73 stars, MIT, actively
  maintained) as the closest real, safe substitute — uses its own
  unmodified LLM-forecasting-bot engine (prompts/parsing) paired with real,
  public Kalshi market data fetched directly by the adapter. Metaculus's own
  API now requires a token even for reads (403 without one) and is never
  contacted at all by this adapter; only Kalshi's genuinely keyless public
  market-data endpoints are used.
- **Real-money security screening (the extra-caution item this brief
  called out)**: confirmed live that Kalshi's and Polymarket's public
  market-data endpoints return real data with zero authentication — no API
  key, no account, no funded wallet. Only `GET` requests are issued
  anywhere in the adapter; no order-placement, portfolio, or account
  endpoint is ever called. No funded brokerage/exchange account, private
  key, or wallet credential of any kind is used, read, or required.
- **Environment**: same compiled-dependency-needs-conda-forge pattern as
  DeepAlpha (`tiktoken`/`libcst`/`pyarrow` had no glibc-2.27-compatible
  prebuilt wheel here) — fixed via `conda install -c conda-forge libcst
  pyarrow` + `pip install "tiktoken<0.12"`. Also vendor-cloned the repo
  because PyPI's latest release (0.2.92) lacks a bot class that exists on
  GitHub's `main` branch, and inserted the vendor path ahead of
  site-packages — a version-selection shim, not a patch (no upstream file
  modified), so no `patches/forecasting-tools.diff` was needed.
- **Reused `DEEPSEEK_API_KEY`** via litellm's native `deepseek/` provider
  string. One real `AuthenticationError` was hit during validation and
  initially looked exactly like "balance may be exhausted" — turned out to
  be a real bug in the adapter itself (missing `load_dotenv()` call), not
  an account/balance problem; confirmed via `env | grep DEEPSEEK` showing
  the key genuinely absent from the process before the fix. No actual
  balance/quota issue was ever encountered.
- **Q5 scope reduction**: a genuine 57-day live real-money comparison is
  infeasible (funded accounts disallowed by security policy; 57 real days
  vs. a single harness call's 600s budget). Reduced to a real
  buy-and-hold-YES backtest over one real Kalshi market's full public daily
  candlestick history — real prices, standard arithmetic, no fabrication.

## 2026-07-04 — Wave 2, half B: FinRL-X adapter — commit `cf3dc9f`, 22/22 harness pass

- **"FinRL-X" is a paper/project name, not a repo name** — it ships under
  `AI4Finance-Foundation/FinRL-Trading` (README literally opens "FinRL-X: An
  AI-Native Modular Infrastructure for Quantitative Trading"). Confirmed via
  the AI4Finance-Foundation org listing (3.4k stars, v1.0.0, 317 commits,
  Apache-2.0 — real, active, not vaporware) and by reading the actual source
  (not just the README): `ml_bucket_selection.py`'s `run_bucket()` is a real
  6-model ensemble competition; `market_regime.py` is a real regime
  detector; both call real upstream FinRL `DRLAgent`/`StockPortfolioEnv`.
  Also checked the rest of the AI4Finance family (FinRL-Meta, FinRL_Podracer,
  ElegantRL, FinRL_Crypto) per the brief's hint — none of those matched;
  FinRL-Trading was the first and only strong candidate and matched closely
  enough that no further search was needed.
- **Security screening clean**: no eval/exec/shell=True, no unrelated
  subtree. Credential-requiring code (Alpaca live-trading, WRDS, FMP)
  exists but is confined to modules this adapter never imports — no
  brokerage account or real money anywhere in the code path actually used.
- **Avoided a paid data dependency entirely**: upstream's own ML
  stock-selection pipeline expects a pre-populated SQLite database of
  22,909 quarterly fundamental records that upstream's own tooling builds
  via FMP's paid-tier API — not checked into the repo, not reproducible
  without a paid key. Substituted a live-yfinance-computed fundamentals
  panel (9 of upstream's 28 feature columns, same names/semantics) passed
  through upstream's own unmodified `run_bucket()` — the ranking logic
  itself is 100% real upstream code.
- **Real, sandbox-specific SIGSEGV found and root-caused**: upstream's
  `build_models()` hardcodes `n_jobs=-1` on several sklearn ensembles. In
  this sandbox (52 visible cores), that makes `StackingRegressor.fit()`'s
  nested cross-validation fork worker processes that each try to run an
  OpenMP-parallel estimator — every worker segfaults, reproduced under both
  `loky` and `threading` joblib backends, independent of
  `OMP_NUM_THREADS`/`LOKY_START_METHOD` tuning. Root-caused by fitting each
  estimator individually and bisecting; `loky.cpu_count()` (what `-1`
  resolves against) tracks `os.sched_getaffinity(0)` on Linux. Fixed by
  temporarily restricting CPU affinity to one core for the duration of the
  `run_bucket()` call only (making `n_jobs=-1` resolve to 1, taking joblib's
  sequential in-process fast path) — an environment-level workaround inside
  the adapter's own process, not a vendor patch. Confirmed identical
  modeling results, ~3s, zero crashes after the fix.
- **`lightgbm` deliberately not installed**: upstream's own `build_models()`
  already wraps that import in `try/except ImportError` and drops it from
  the model roster gracefully — omitting it exercises a supported upstream
  code path rather than working around a missing dependency.
- **Reused this session's existing `adapters/vendor/FinRL` clone +
  `patches/FinRL.diff`**: FinRL-Trading's own DRL code imports the separate
  `finrl` package (not declared in its own requirements.txt) and hits the
  identical eager-import problem `finrl_adapter.py` already patched earlier
  this session — same public repo cloned to the same local path, not a new
  patch and not cross-adapter code coupling (vendor/ stays gitignored
  either way).
- **Q4 DRL training reuses `finrl_adapter.py`'s already-validated reduced
  budget** (`TOTAL_TIMESTEPS=3000`, `COV_LOOKBACK_DAYS=60`) rather than
  upstream's own `rl_model.py` helpers, whose hardcoded timestep counts
  (50000-80000, no override) would blow past harness timeouts several times
  over.
- **Q4 regime**: real upstream `detect_slow_regime()` fed real weekly
  `^GSPC`/`^VIX` closes; its `RISK_ON/NEUTRAL/RISK_OFF` states map to
  CONTRACT's `Regime.BULL/SIDEWAYS/BEAR`, and its own `effective_cash_floor`
  output is blended with the DRL policy's cash allocation so the regime
  genuinely modulates the final weights, not just a label.

## 2026-07-04 — Wave 3, half A: NoFx adapter — commit `3d8f0f3`, 19/19 harness pass

- **Literal "NoFx" (`NoFxAiOS/nofx`) is real (12.5k stars) but disqualified
  on two independent grounds**: (1) its setup requires connecting live
  funded exchange credentials (Binance/Bybit/OKX/etc.) with no documented
  paper-trading/analysis-only mode — same disqualifying pattern as
  DeepAlpha's Robinhood-credential rejection; (2) its AI layer is
  hard-routed through a proprietary paid gateway with no way to plug in the
  existing DeepSeek key, and it's a Go binary + web terminal, not a
  callable Python library — no faithful thin wrapper is possible regardless
  of the credentials issue.
- **Substituted `0xemmkty/QuantMuse`** (2,707 stars, MIT, verified real
  and not a content-farm account — checked specifically because Prediction
  Arena's session found exactly that pattern once already) after also
  rejecting a too-thin candidate (`Ronitt272/LLM-Enhanced-Trading`, just a
  FinGPT+SMA-crossover glue script) and ruling out re-wrapping FinGPT
  itself (already has an adapter; CLAUDE.md disallows a duplicate).
  QuantMuse's own `LLMIntegration.assess_risk()` genuinely fuses real LLM
  sentiment scoring with real RSI/MACD/Bollinger/momentum factors into one
  risk verdict — verified by reading the source, not just README claims.
- **Security screening**: no live brokerage credentials or real money in
  any of the three modules imported; upstream's `python-binance` dependency
  (used only by unrelated live-data fetchers elsewhere in the repo) isn't
  even installed in this adapter's env, and the harness still passes —
  proof the import path used is clean. A stray `test.exe`/`test.cpp` in the
  repo root was checked and confirmed to be a trivial, harmless compiler
  smoke-test artifact, not a hidden payload.
- **Patch (`patches/QuantMuse.diff`)**: a two-line change making
  `SentimentAnalyzer`'s hardcoded `model="gpt-3.5-turbo"` configurable, so
  DeepSeek could be plugged in — smaller and more honest than reimplementing
  the sentiment prompt in adapter code to avoid touching upstream.
- **DeepSeek model name verified empirically, not assumed from memory**:
  a real failed test call against a wrong model name returned an error
  naming the two actually-supported strings (`deepseek-v4-pro`/
  `deepseek-v4-flash`) — same "don't trust a remembered/assumed string,
  verify against the live system" caution as the hallucinated-GitHub-URL
  lesson from Prediction Arena's session, generalized to model names too.
- **Cost-control finding**: upstream's own sentiment/fusion calls catch
  every exception internally and silently fall back to a degraded default
  rather than raising — which would have masked a real auth/balance
  failure as an innocuous "neutral sentiment" data point. Worked around by
  attaching a temporary logging handler around the real calls and scanning
  for auth/quota-shaped error substrings, raising a clear
  "DeepSeek API balance may be exhausted" error if found instead of
  silently degrading. No such error actually occurred this session —
  `load_dotenv()` was deliberately double-checked given the earlier
  false-alarm bug in a different adapter's session.

## 2026-07-04 — Wave 3, half B: ATLAS adapter — commit `105dfcb`, 20/20 harness pass

- **"ATLAS" is an extremely common project name** (physics experiments,
  cloud infra, unrelated ML frameworks) — the search deliberately did not
  stop at the first repo literally named ATLAS.
- **Rejected `chrisworsey55/atlas-gic`** despite being real (1999 stars)
  and using near-identical target vocabulary ("Darwinian selection",
  "meta-weighting" via a "JANUS" layer) — reading its actual source showed
  it evolves **LLM agent system-prompts** via git-commit/revert, not
  alpha-factor formulas, and it's "now running live with real capital"
  requiring an Alpaca brokerage account. Two independent disqualifiers at
  once: wrong content *and* live-money/brokerage exposure. Demonstrates
  that GitHub-API existence verification is necessary but not sufficient —
  content-match and security screening both still have to happen even
  after a repo is confirmed real.
- **Rejected `QuantaAlpha/QuantaAlpha`** (the strongest runner-up: real,
  1.2k stars, arXiv-backed, DeepSeek-compatible) after reading
  `evolving_framework.py` directly and finding it's a single-subject,
  trajectory-based iterative-refinement loop, not population-based —
  no fitness-ranked population, no selection/discard step. "Evolutionary"
  in marketing copy can mean either real genetic-algorithm population
  selection or "iteratively refines itself," and these are different
  algorithms — check for an actual `population` + `select`/`discard` step
  before treating them as interchangeable.
- Also rejected `The-Swarm-Corporation/ATLAS` (real-time risk monitor,
  wrong domain), `Morgansy/Genetic-Alpha` (real single-population GP, no
  multi-queue structure), `KangOxford/AutoFactor` (PDFs only, no code), and
  noted AutoAlpha (Tsinghua paper) has no public implementation.
- **Settled on `Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining`**:
  real DEAP-based genetic programming (`selNSGA2` Pareto selection +
  `HallOfFame`) over a bundled 236-token crypto-perpetuals historical panel.
  Confirmed not just real but *functioning* by actually executing
  `GPProcess.run()`, not just reading it. Its own code splits the
  population into sequential "Batch 1/2/3/4" sub-populations evolved
  independently then combined via non-dominated sorting — the closest
  literal analogue to "multi-queue" found across every candidate, though
  honestly documented as not literally "meta-weighting" (it's Pareto-front
  selection + a validation-set filter, not a weighted average) rather than
  rounded up to a perfect match.
- **Cleanest security profile of any adapter this session**: no eval/exec/
  shell=True/subprocess, zero credential/broker/API-key patterns anywhere,
  and needs no external data source, account, or API key of any kind — its
  entire input is the repo's own bundled historical CSV panel, no live feed.
- **No LLM calls at all** (pure genetic-programming/statistics) — no API
  key needed, no cost-control concerns.
- **Scope reductions**: GA budget scaled from upstream's own example
  (200/10/6 population/batch/generation) down to 40/10/2 to fit harness
  timeouts, still running upstream's real unmodified `GPProcess.run()`;
  ticker universe mismatch (equities vs. the project's real crypto-token
  panel) handled by falling back to a fixed representative token with an
  explicit note in `supporting_evidence`, same reinterpretation pattern
  `finrl_x_adapter.py` used for its own universe mismatch; point-in-time
  train/val/test windows derived from the requested date, clamped to the
  bundled dataset's real historical coverage.

## 2026-07-04 — Wave 4, half A: Vibe-Trading adapter — commit `a3a8f2a`, 25/25 harness pass, all 3 questions (Q3+Q4+Q5)

- **Confirmed `HKUDS/Vibe-Trading`** (17.7k stars, actively maintained,
  real long-running research org) as the correct real repo after checking
  five lookalike candidates via the GitHub API directly (not trusting
  search snippets): two were fork/malware-tagline squats on the real
  project's name, one was a genuine fork (not independent), two were real
  but smaller/unrelated single-author tools. Verified by reading and
  actually *running* the source (not just the README): `CompositeEngine`
  is real and genuinely auto-routes multi-market ticker lists to a shared
  capital pool across per-market sub-engines; the NL-strategy-generation
  machinery is a real skill-guide-driven LLM call, not marketing copy.
- **Security screening**: repo has a real live-order-execution layer
  (`agent/src/live/`) but this adapter's code path never imports it — only
  the backtest/paper-simulation layer and the LLM factory are used. No
  brokerage account, no real money, anywhere this adapter's code actually
  runs. Data sources used are yfinance and OKX's public no-auth REST API
  only; premium/broker-login loaders in the same repo are never reached.
- **Found a real bug in upstream's own shipped reference example**:
  `cross-market-strategy/example_signal_engine.py` — the exact file
  upstream ships as the CompositeEngine usage example — fails upstream's
  own runtime AST security validator (a top-level `re.compile()` call
  isn't literal-safe by the validator's own rules). Confirmed by actually
  running it, not just reading it. Fixed by adapting the example to call
  upstream's own already-imported market-detection function instead of
  re-deriving a second, unsafe regex table — this is the adapter's own
  input file, not a vendor patch (the vendored clone is untouched).
- **Handled real LLM nondeterminism**: DeepSeek's generated `SignalEngine`
  code occasionally violates upstream's own class-validation rule (a
  required constructor arg with no default). Fixed with an explicit
  constraint in the prompt + in-process pre-validation before spending a
  real backtest call + exactly one retry feeding the real validator's error
  back to the model — confirmed stable (25/25) across two consecutive full
  harness runs after the fix.
- **Deliberately did not drive the full autonomous `AgentLoop`**: upstream's
  real multi-turn ReAct loop is genuine working code but has an unbounded
  LLM turn count that doesn't fit the harness's fixed timeouts or this
  session's bounded-real-LLM-calls convention. Calls the same underlying
  primitives (`build_llm()`, the skill guide, the AST validator, the
  backtest runner) directly instead — same class of scope reduction every
  other adapter this session applied to its own upstream's heaviest path.
- **Cross-market anchor for Q4**: CONTRACT's own sample tickers are all
  single-market US equities, which would never actually exercise
  `CompositeEngine` (the exact Q4 feature the brief calls out). The adapter
  appends a fixed `BTC-USDT` anchor whenever the requested tickers don't
  already span multiple real upstream-detected markets, disclosed in
  `Q4Portfolio.rationale` whenever it fires.
- **Environment**: `tiktoken` had the same no-prebuilt-wheel problem
  `ai_hedge_fund_adapter.py` hit earlier this session — fixed the same way
  via `conda install -c conda-forge tiktoken`. A first `git clone` attempt
  was killed by a tool timeout mid-transfer and left a corrupted git index;
  re-cloned as a backgrounded process instead of foreground.

## 2026-07-04 — Wave 4, half B: FinClaw adapter — commit `a70cd77`, 20/20 harness pass

- **The literal GitHub repo (`NeuZhou/finclaw`) had been repurposed into a
  zero-code marketing page** for a paid "StratEvo Pro" product — confirmed
  via the GitHub API (redirects to `NeuZhou/stratevo`, exactly 4 commits,
  first one literally "Initial commit: FinClaw product showcase," contents
  are just a README + 2 PNGs, zero Python source). The most extreme version
  of the "buzzwords not matching actual code" trap found this session —
  here there's no code at all to mismatch, only marketing copy reusing the
  exact search-target vocabulary.
- **However, the same project's PyPI page still hosts real, functioning
  source** one release earlier (`finclaw-ai==5.6.1`, uploaded a week before
  the GitHub pivot) — a real, substantial (88,606 lines, AGPL-3.0,
  CI/codecov-badged) package with a genuine generational genetic algorithm
  (`AutoEvolver`/`StrategyDNA`, Polynomial Mutation) and real walk-forward
  out-of-sample validation. Installed and actually *ran* it (`finclaw evolve
  --market us`, real yfinance data) rather than trusting the README —
  confirmed genuine generational fitness progress across runs, not a canned
  number. `upstream_repo` points to the PyPI page, not the now-vaporware
  GitHub repo, with the GitHub situation disclosed rather than hidden.
- **The package's own marketed "484 factors" figure doesn't match its own
  executed code**: the README's category table doesn't even sum to itself,
  and the actual CLI-wired engine has 41 real factor weights (confirmed by
  introspecting the real `StrategyDNA` dataclass), not 484. Documented this
  honestly and used the verified real number rather than parroting the
  marketing claim.
- **Confirmed mechanistically distinct from `atlas_adapter.py`** (not a
  duplicate-upstream problem): atlas wraps tree-based Genetic
  Programming (DEAP formula-tree synthesis via NSGA-II, discovering new
  factor *formulas*); this wraps a classical real-coded Genetic Algorithm
  over a fixed 74-field weight-vector genome (evolving how much to trust
  and combine an existing fixed factor set, not inventing new formulas) —
  different algorithm family, different author/license/fitness function.
  Surveyed the wider GA-alpha-factor GitHub space too (6 other real repos)
  and confirmed all of those are tree-based/GP synthesis like atlas's
  upstream, not a distinct second candidate.
- **Security**: zero eval/exec/os.system/credential/broker hits in any
  module this adapter imports. Upstream's `evolve()` does internally call
  `eval(formula, sandbox)` for a handful of fixed, hardcoded seed-factor
  formula strings, but `sandbox` is a restricted globals dict (numpy/math
  functions + OHLCV arrays only, no `__builtins__`/`os`/network) — same
  risk class as DEAP's/gplearn's own compiled-expression evaluation used
  elsewhere this session, not arbitrary code execution. A separate,
  `OPENAI_API_KEY`-gated LLM factor-discovery path exists in the package
  but is never called by this adapter. No live brokerage/exchange
  credentials or funded capital anywhere in the path used — real
  live-trading modules exist in the package but aren't imported here.
- **Scope reduction**: GA budget scaled from upstream's own CLI defaults
  (population=30, generations=100, max_stocks=500) to population=24,
  generations=30, 9-stock universe — real, unmodified `AutoEvolver.evolve()`,
  ~75-100s wall-clock, comfortably inside harness timeouts.
- **Point-in-time fix**: upstream's own data downloader always ends at
  "now," which would leak future data relative to a historical requested
  `date`. This adapter fetches yfinance history itself windowed to end at
  the requested date, saved via upstream's own real CSV-writing helper
  (not reimplemented) in the schema upstream's loader expects.
