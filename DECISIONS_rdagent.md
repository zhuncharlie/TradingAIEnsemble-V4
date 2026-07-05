# DECISIONS_rdagent.md — RD-Agent adapter (Q3 expansion, third alpha-signal mechanism)

Target: `microsoft/RD-Agent` — a real LLM-agent-driven "Research and
Development Agent" for automating quant/factor research. Wrapped as
`adapters/rdagent_adapter.py`, `questions_answered = ["Q3"]`.

## Repo verification

- `GET /repos/microsoft/RD-Agent` (GitHub API, not a search snippet) confirmed:
  `full_name="microsoft/RD-Agent"`, `fork=False`, `archived=False`,
  `stargazers_count=13779`, `license=MIT`, `created_at=2024-04-03`,
  `pushed_at=2026-06-15` (actively maintained, real, long-running Microsoft
  Research org). No lookalike-name confusion existed or needed resolving —
  unlike this session's ATLAS/FinClaw searches, the literal name was correct
  on the first try.
- **Why:** GitHub-API existence + activity alone isn't sufficient (this
  session found repurposed/vaporware repos that still pass this check), so
  the next step was reading actual source, not the README.
- **How to apply:** `rdagent/scenarios/qlib/` contains a complete,
  non-trivial factor-mining pipeline (`proposal/factor_proposal.py`,
  `developer/factor_coder.py` + `factor_runner.py`,
  `experiment/factor_experiment.py`, `factor_experiment_loader/`) — read and
  actually executed each stage during development, confirming it is real,
  substantially implemented code, not documentation-only.

## Mechanism check — genuinely LLM-agent-loop-driven

- Traced the real call graph: `rdagent/components/workflow/rd_loop.py::RDLoop`
  (base of `rdagent/app/qlib_rd_loop/factor.py::FactorRDLoop`) is a real
  propose → code → run → feedback loop. `_propose()` calls
  `hypothesis_gen.gen()` (real LLM call #1, proposes an NL hypothesis);
  `_exp_gen()` calls `hypothesis2experiment.convert()` (real LLM call #2,
  turns the hypothesis into concrete `FactorTask`(s): name/description/LaTeX
  formulation/variables); `coding()` calls `coder.develop()`
  (`QlibFactorCoSTEER`), which makes a real LLM call #3
  (`FactorMultiProcessEvolvingStrategy.implement_one_task()`, writes an
  actual `factor.py`), actually executes it locally against real data
  (`FactorFBWorkspace.execute()`, real subprocess), then runs real evaluators
  including LLM call #4 (`FactorCodeEvaluator`, a code critic) and LLM call
  #5 (`FactorFinalDecisionEvaluator`, an LLM-as-judge accept/reject verdict).
  `Trace` carries the hypothesis+feedback history into the next round's
  prompt (confirmed by reading `factor_proposal.py`'s own
  `hypothesis_and_feedback` context construction).
- **Why:** the brief explicitly required genuine propose→implement→
  validate→iterate, not a single LLM call (would duplicate
  `vibe_trading_adapter.py`'s one-shot `SignalEngine` generation) and not
  population-based genetic/evolutionary search (would duplicate
  `atlas_adapter.py`'s DEAP GP or `finclaw_adapter.py`'s real-coded GA).
- **How to apply / confirmed how:** actually ran steps 1–3 end-to-end during
  development (not just read the code) — verified with a real run that
  produced a real hypothesis ("Simple momentum, volatility, and volume
  factors... capture distinct return-predictive signals"), a real factor
  formulation (`Mom_10d`, LaTeX formula, variables), real generated Python
  code, a real execution against real data, and a real LLM-as-judge verdict
  (both an initial real rejection — "index level order is reversed" / "use
  `$close * $factor` for adjusted close" — and a subsequent real acceptance)
  during separate real runs. This is unambiguously a multi-call, multi-stage
  autonomous LLM-agent loop, not a single call and not GP/GA.

## Security screening

- `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.(call|run|Popen)"`
  across every module this adapter's code path imports — the only hit is
  `FactorFBWorkspace.execute()`'s own `subprocess.check_output(...,
  shell=True)` running the LLM-just-generated `factor.py` file, upstream's
  own intended mechanism (same risk class as `vibe_trading_adapter.py`'s
  generated-`SignalEngine`-in-a-subprocess and `atlas_adapter.py`/
  `finclaw_adapter.py`'s compiled-expression `eval()`).
- Zero hits for broker/exchange/credential patterns
  (alpaca/binance/robinhood/coinbase/ccxt/broker/live_trad*) in any module
  this adapter imports. No live brokerage/exchange account or real-money
  path anywhere in the code actually used — the one part of upstream that
  *would* need heavier infrastructure (the Docker-based `QlibFactorRunner`
  backtest, needing a full Qlib install + China-A-share data bundle) is
  never invoked at all (see Scope reductions).
- No unrelated merged subtree: every top-level `rdagent/` package (`app`,
  `components`, `core`, `log`, `oai`, `scenarios`, `utils`) is on-topic for
  an R&D-automation research-agent framework — no FinGPT-session-style
  off-topic subtree found.
- MIT license, Microsoft Corporation copyright confirmed in `LICENSE`.
- **Why:** this session has repeatedly found real repos disqualified by
  live-credential requirements or unrelated merged subtrees; RD-Agent has
  neither.

## Environment / dependency notes

- New dedicated conda env `rdagent_real`, python 3.11 (never shared with
  another adapter, per the Iron Rules).
- `conda install -c conda-forge libcst pyarrow tiktoken` — same recurring
  fix this session has used repeatedly: `libcst` (a transitive build
  dependency) has no prebuilt wheel for this platform/Python combo and
  needs a Rust toolchain to build from source; conda-forge ships
  precompiled binaries.
- `pip install pydantic pydantic-settings loguru fire python-Levenshtein
  scikit-learn filelock fuzzywuzzy openai "litellm>=1.73" azure-identity
  rich tqdm typer numpy pandas jinja2 python-dotenv tables tenacity
  yfinance dill psutil docker` — `dill` and `psutil` are real transitive
  imports (`rdagent/core/knowledge_base.py`, `rdagent/log/logger.py`)
  missing from upstream's own `requirements.txt` top-level pins, found by
  iterating import errors one at a time. `docker` (the Python SDK) is
  imported unconditionally by `rdagent/utils/env.py` even though this
  adapter's code path never constructs a `DockerConf` or calls
  `docker.from_env()` — confirmed empirically that importing it never
  touches an actual Docker socket in this adapter's path.
- **`qlib` itself is deliberately NOT installed.** This adapter's bounded
  code path never imports it — every `import qlib` in the repo lives either
  inside a string literal used to generate a throwaway test script
  (`rdagent/utils/qlib.py::validate_qlib_features`, never called because
  this adapter passes `base_features_path=None`-equivalent by never calling
  `_init_base_features`) or inside upstream's own Docker-run
  `factor_data_template/generate.py` / `read_exp_res.py` scripts (never
  executed, since the Docker backtest runner is skipped). Confirmed via
  `grep -rn "^import qlib\|from qlib" rdagent/` and by successfully running
  the full bounded pipeline with `qlib` absent from the env.
- **Repo-root scratch-directory leak found and fixed mid-session** (flagged
  by the coordinator): upstream has *three* independent `Path.cwd() / ...`
  scratch-output defaults, not one — `RDAgentSettings.workspace_path`
  (`git_ignore_folder/RD-Agent_workspace`), `LogSettings.trace_path`
  (`log/<timestamp>`), and `RDAgentSettings.pickle_cache_folder_path_str`
  (`pickle_cache/`). Early development only overrode the first
  (`WORKSPACE_PATH` env var), so `log/` and `pickle_cache/` still leaked
  into the trading-ai-ensemble repo root. Found all three by grepping for
  `Path.cwd()` across `rdagent/core/conf.py` and `rdagent/log/conf.py`,
  confirmed each one's env-var override empirically
  (`LOG_TRACE_PATH`, `PICKLE_CACHE_FOLDER_PATH_STR`), and now set all three
  (plus `WORKSPACE_PATH`) to paths under this adapter's own gitignored
  `adapters/vendor/RD-Agent/git_ignore_folder/` before any `rdagent.*`
  import (these are pydantic-settings singletons built once at first
  import, so the env vars must be set before that happens). The leaked
  `git_ignore_folder/`, `log/`, and `pickle_cache/` directories that had
  already been created at the repo root during earlier development were
  deleted; the top-level `.gitignore` also gained a safety-net entry for
  all three, in case any other tool run leaks them again.
- **Why:** CLAUDE.md's file layout is explicit that an adapter's vendor
  clone (and anything it produces) stays under `adapters/vendor/`, not the
  repo root.

## LLM wiring

- Upstream's own `rdagent/oai/backend/litellm.py::LiteLLMAPIBackend` is a
  native LiteLLM-based backend (`LLM_SETTINGS.backend =
  "rdagent.oai.backend.LiteLLMAPIBackend"` by default), with a comment of
  its own anticipating DeepSeek specifically ("Deepseek will enter this
  branch"). Reused the existing `DEEPSEEK_API_KEY` from
  `adapters/vendor/ai-hedge-fund/.env` via LiteLLM's native
  `deepseek/<model>` provider string — no separate key, no base-url
  override needed.
- **Model name verified empirically, not assumed from memory** (per this
  session's standing rule): a real test script tried
  `deepseek/deepseek-chat`, `deepseek/deepseek-v4-flash`, and
  `deepseek/deepseek-v4-pro` against real completion calls. All three
  resolved successfully. An initial `max_tokens=5` test made `-flash`/
  `-pro` look broken (empty content) — re-tested with `max_tokens=50` and
  both returned real `"OK"` content with `finish_reason="stop"`, so that
  was a token-budget artifact of the test script, not a real model-name
  failure. Settled on `deepseek/deepseek-v4-flash` for consistency with
  this session's other DeepSeek-using adapters.
- No auth/balance/quota error was ever encountered during development.
  `LITELLM_MAX_RETRY` is nonetheless reduced from upstream's own default of
  10 to 2, so a real auth/balance failure would fail fast rather than
  silently retry for ~10+ seconds. `_run_pipeline()`'s `_classify_llm_error`
  re-raises any auth/insufficient-balance/quota-shaped exception as a clear
  `RuntimeError("DeepSeek API balance may be exhausted")`.
- **A real, unrelated OpenAI dependency was found and avoided**: upstream's
  own knowledge-base self-generation step
  (`CoSTEERRAGStrategyV2.generate_knowledge()`) embeds every
  successful/failed implementation via a hardcoded `text-embedding-3-small`
  OpenAI model regardless of the chat backend — this raised a real
  `litellm.InternalServerError: Missing credentials ... OPENAI_API_KEY`
  the first time the full coder loop was run with default settings. Traced
  the exception back to `vector_base.py::create_embedding()` to confirm it
  was this unrelated embedding feature, not a real DeepSeek balance/auth
  problem, before disabling it (`knowledge_self_gen=False`) — the same
  "double-check before concluding it's a real balance issue" discipline
  this session applied elsewhere (a different adapter's session hit a
  similar false alarm from a missing `load_dotenv()` call, not an actual
  balance problem).

## Scope reductions

- **Bounded to one hypothesis, one factor task, at most two real CoSTEER
  implement/evaluate rounds** (`max_loop=2`), calling the real underlying
  primitives (`hypothesis_gen.gen()`, `hypothesis2experiment.convert()`,
  `QlibFactorCoSTEER(scen, max_loop=2).develop(exp)`) directly instead of
  driving `RDLoop.run()`'s own indefinite loop — the identical pattern
  `vibe_trading_adapter.py`'s session used for its own unbounded upstream
  `AgentLoop`.
  - **Why `max_loop=2`, not 1:** `max_loop=1` was tried first and found,
    during development, to raise upstream's own real `CoderError("All
    tasks are failed")` whenever the single implementation attempt was
    rejected by the real evaluator (a real, legitimate rejection — e.g. the
    evaluator correctly noting the generated code should multiply `$close`
    by `$factor` before computing momentum). `max_loop=2` gives the loop
    one genuine chance to use its own real round-1 feedback to correct
    round 2 — the actual "iterate" step of propose/implement/validate/
    iterate — while staying within this session's "1-2 real
    proposal-and-evaluate cycles" bound.
  - **How non-convergence is handled:** if every attempt within the 2-round
    bound is still rejected, `_run_pipeline()` catches the real
    `CoderError` and reports a disclosed `NEUTRAL`/zero-strength
    `Q3Signal` carrying upstream's own real rejection feedback text as
    `supporting_evidence`, rather than retrying further, forcing a
    fabricated accept, or crashing.
  - `hypothesis2experiment.convert()` may propose 1-3 factor tasks per real
    call; this adapter keeps only the first (`exp.sub_tasks =
    exp.sub_tasks[:1]`) to keep the real call count small (~5-8 real LLM
    calls total, ~60-120s wall-clock measured empirically, comfortably
    inside smoke_test<300s/run()<600s).
- **Upstream's Docker-based `QlibFactorRunner` backtest is never invoked.**
  The full loop's final step normally sends the factor into a dockerized
  Qlib install to train an LGBM model and backtest a portfolio — needs
  Docker plus a multi-GB China-A-share Qlib data bundle, well outside this
  harness's timeout budget and CLAUDE.md's thin-wrapper mandate. This
  adapter stops at the real CoSTEER implement+evaluate step, which already
  produces a real executed factor and a real LLM-as-judge verdict.
- **Real yfinance data substituted for Qlib's own Docker-built China-A-share
  bundle**, reshaped into upstream's own exact expected schema
  (`daily_pv.h5`, key="data", MultiIndex[instrument, datetime],
  `$open/$close/$high/$low/$volume/$factor`, `$factor=1.0` since
  yfinance's `auto_adjust=True` close is already adjusted) — confirmed
  against upstream's own `factor_data_template/generate.py` and
  `README.md`. Same point-in-time real-data-substitution pattern this
  session's `atlas_adapter.py`/`finclaw_adapter.py`/`finrl_x_adapter.py`
  used for their own data-source mismatches.
- **Direction/strength derived via this adapter's own correlation
  statistic**, not upstream's own research logic: Pearson correlation
  between the real generated factor series and the real forward 5-day
  return computed from the same real yfinance closes;
  `sign(correlation) * sign(latest factor value)` for direction,
  `abs(correlation)` for strength. This is schema-translation arithmetic
  (CLAUDE.md's own `Action.BUY if result["signal"] > 0` pattern), not a
  reimplementation of RD-Agent's research method — upstream's own real
  accept/reject verdict is reported separately in `supporting_evidence`.

## Result

- `python CONTRACT/test_harness.py --adapter adapters/rdagent_adapter.py`:
  **21/21 checks passed, ALL PASS** (smoke_test in ~47-77s across separate
  runs depending on whether the real CoSTEER loop converges in round 1 or
  needs round 2; `run()` completes near-instantly on a cache hit for the
  harness's fixed `AAPL`/`2024-01-15` sample).
- No security findings blocked this adapter. No DeepSeek balance/auth
  issue was ever encountered (the one auth-shaped error hit during
  development was the unrelated OpenAI-embedding knowledge-base step,
  traced and disabled, not a DeepSeek problem).
