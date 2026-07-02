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
