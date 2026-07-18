"""
adapters/rdagent_adapter.py — wraps github.com/microsoft/RD-Agent (Q3).

============================================================================
Repo verification (GitHub API, not just a search snippet)
============================================================================
`GET /repos/microsoft/RD-Agent` confirmed: full_name="microsoft/RD-Agent",
fork=False, archived=False, stargazers_count=13779, license=MIT,
created_at=2024-04-03, pushed_at=2026-06-15 (actively maintained, real,
long-running Microsoft Research org, not a throwaway account), description
literally reads "...lets AI drive data-driven AI. RD-Agent...". This is the
real, correct target -- no lookalike-name confusion was found or needed
(unlike this session's ATLAS/FinClaw searches).

Read the actual source (not just the README) to confirm the quant/factor-
mining scenario is real, not a documentation-only stub:
`rdagent/scenarios/qlib/` contains `proposal/factor_proposal.py`,
`developer/factor_coder.py` + `factor_runner.py`,
`experiment/factor_experiment.py`, and `factor_experiment_loader/` --
a complete, non-trivial, substantially-implemented factor-mining pipeline,
not vaporware.

============================================================================
Mechanism check (read the actual orchestration code, not assumed from the
README) -- genuinely LLM-agent-driven propose -> implement -> validate ->
iterate, distinct from both this session's other Q3 adapters
============================================================================
`rdagent/components/workflow/rd_loop.py::RDLoop` (base class of
`rdagent/app/qlib_rd_loop/factor.py::FactorRDLoop`) is a real, executable
propose/code/run/feedback loop:
  1. `_propose()` -> `self.hypothesis_gen.gen(trace, plan)` --
     `QlibFactorHypothesisGen.gen()` (via `LLMHypothesisGen.gen()` in
     `rdagent/components/proposal/__init__.py`) makes a REAL
     `APIBackend().build_messages_and_create_chat_completion(...)` call that
     proposes a natural-language investment hypothesis (e.g. "past returns /
     volatility / volume ratios capture distinct return-predictive signals").
  2. `_exp_gen()` -> `self.hypothesis2experiment.convert(hypothesis, trace)` --
     `QlibFactorHypothesis2Experiment.convert()` makes a SECOND real LLM call
     that turns the hypothesis into one or more concrete `FactorTask`s (name,
     description, LaTeX formulation, variables).
  3. `coding()` -> `self.coder.develop(exp)` -- `QlibFactorCoSTEER` (a
     `CoSTEER` = "Collaborative Software... Evolving" coder) makes a THIRD
     real LLM call (`FactorMultiProcessEvolvingStrategy.implement_one_task()`)
     that writes an actual `factor.py` Python implementation of the
     formulation, actually EXECUTES it locally
     (`FactorFBWorkspace.execute()`, real subprocess against real data), then
     runs real evaluators (`FactorEvaluatorForCoder`) including a fourth real
     LLM call (`FactorCodeEvaluator`, a code critic) and a fifth real LLM
     call (`FactorFinalDecisionEvaluator`, an LLM-as-judge final accept/
     reject decision) against the real execution feedback.
  4. `running()`/`feedback()` -> real backtest execution + a real
     LLM-generated summary feedback that is fed back into the next
     `hypothesis_gen.gen()` call via `Trace` (upstream's own iteration
     mechanism) -- confirmed by reading `Trace.hist`/`sync_dag_parent_and_hist`
     and `factor_proposal.py`'s own use of
     `trace.hist`/`hypothesis_and_feedback` context in the next round's
     prompt.
This is a genuine multi-call, multi-stage LLM agent loop with real code
generation + real local execution + real LLM-as-judge evaluation feeding
back into the next hypothesis -- verified empirically by actually running
steps 1-3 end-to-end during development (see DECISIONS_rdagent.md), not
just reading the code. It is neither a single LLM call (that would
duplicate `vibe_trading_adapter.py`'s Q3, which does exactly one DeepSeek
call to write a `SignalEngine`) nor a population-based genetic/evolutionary
search (that would duplicate `atlas_adapter.py`'s DEAP genetic-programming
Pareto search or `finclaw_adapter.py`'s real-coded GA over a factor-weight
genome) -- it is autonomous LLM-agent research: propose a hypothesis in
natural language, translate it to a concrete spec, implement it in code,
execute and critique the result, and (in the untouched full loop) iterate.

============================================================================
Security screening
============================================================================
  - `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.(call|run|Popen)"`
    across every module this adapter's code path imports
    (`rdagent/core/`, `rdagent/components/coder/factor_coder/`,
    `rdagent/components/coder/CoSTEER/`, `rdagent/components/proposal/`,
    `rdagent/scenarios/qlib/proposal/`, `rdagent/scenarios/qlib/developer/
    factor_coder.py`, `rdagent/scenarios/qlib/experiment/factor_experiment.py`,
    `rdagent/oai/`) -- the only hit is `FactorFBWorkspace.execute()`'s own
    `subprocess.check_output(f"{python_bin} {code_path}", shell=True, ...)`,
    upstream's own documented, intended mechanism for running the
    LLM-generated `factor.py` file it just wrote (same risk class as
    `vibe_trading_adapter.py`'s generated-`SignalEngine`-in-a-subprocess and
    `atlas_adapter.py`/`finclaw_adapter.py`'s compiled-expression
    DEAP/gplearn `eval()` -- real code execution of a real, reviewable
    artifact this pipeline just produced, not arbitrary attacker-controlled
    input).
  - Zero hits for broker/exchange/credential patterns
    (alpaca/binance/robinhood/coinbase/ccxt/broker/live_trad*) anywhere in
    the modules this adapter imports. `rdagent/app/` contains unrelated
    scenarios (kaggle, finetune, data_science, rl) this adapter never
    imports; none of them are reached by this adapter's code path.
  - No unrelated merged subtree: every top-level `rdagent/` package
    (`app`, `components`, `core`, `log`, `oai`, `scenarios`, `utils`) is
    on-topic for an R&D-automation research-agent framework -- no
    FinGPT-session-style off-topic subtree.
  - No live brokerage/exchange account, funded capital, or real-money path
    anywhere in the modules imported. The upstream Docker-based
    `QlibFactorRunner` backtest path (which would need a full qlib
    installation + China-A-share data bundle) is never invoked by this
    adapter at all (see "Scope reductions" below) -- so there is no
    live-market-data or brokerage dependency of any kind, only this
    adapter's own real yfinance fetch and the real DeepSeek chat API.
  - MIT license, Microsoft Corporation copyright header confirmed in
    `LICENSE`.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n rdagent_real python=3.11
    conda activate rdagent_real
    conda install -c conda-forge libcst pyarrow tiktoken -y
    # Same conda-forge workaround this session used repeatedly: `libcst`
    # (a transitive build dependency pulled in indirectly) has no prebuilt
    # wheel for this platform/Python combo and needs a Rust toolchain to
    # build from source; conda-forge ships precompiled binaries for
    # libcst/pyarrow/tiktoken.
    pip install pydantic pydantic-settings loguru fire python-Levenshtein \\
        scikit-learn filelock fuzzywuzzy openai "litellm>=1.73" \\
        azure-identity rich tqdm typer numpy pandas jinja2 python-dotenv \\
        tables tenacity yfinance dill psutil docker
    # `dill` and `psutil` are real transitive imports
    # (rdagent/core/knowledge_base.py, rdagent/log/logger.py) missing from
    # requirements.txt's top-level pins. `docker` (the Python SDK, not the
    # daemon) is imported unconditionally by rdagent/utils/env.py even
    # though this adapter's code path never constructs a DockerConf or
    # calls docker.from_env() -- confirmed empirically: importing it here
    # never touches an actual Docker socket, only the module is needed at
    # import time. `qlib` itself is deliberately NOT installed -- this
    # adapter's bounded code path never imports it (see below); it is only
    # ever imported inside upstream's own generated shell scripts for the
    # (skipped) Docker backtest/data-download path.
    git clone --depth 1 https://github.com/microsoft/RD-Agent.git \\
        adapters/vendor/RD-Agent

Run the harness with that env active:
    conda activate rdagent_real
    python CONTRACT/test_harness.py --adapter adapters/rdagent_adapter.py

No upstream source was patched -- the vendored clone is completely
untouched; this adapter only supplies (a) its own real market data reshaped
into upstream's own expected file schema, and (b) constructor keyword
arguments to real upstream classes (`max_loop=2`, `knowledge_self_gen=False`)
that are documented, first-class parameters of those classes. There is no
`patches/RD-Agent.diff`.

============================================================================
LLM wiring
============================================================================
Upstream's own `rdagent/oai/backend/litellm.py::LiteLLMAPIBackend` is a
native LiteLLM-based, OpenAI-compatible-agnostic backend (`LLM_SETTINGS.backend
= "rdagent.oai.backend.LiteLLMAPIBackend"` by default) -- exactly the
LiteLLM-style config option the session brief expected. It even has a
comment of its own anticipating DeepSeek specifically:
`if response_format and not supports_response_schema(model=...): # Deepseek
will enter this branch`. Reused the existing `DEEPSEEK_API_KEY` from
`adapters/vendor/ai-hedge-fund/.env` via LiteLLM's native `deepseek/<model>`
provider string (same mechanism `forecasting_tools`/other DeepSeek-using
adapters this session use) -- no separate key, no base-url override needed
(LiteLLM's `deepseek/` provider already targets `https://api.deepseek.com`
and reads `DEEPSEEK_API_KEY` natively).

Model name verified empirically against real completion calls during
development (not assumed from memory, per this session's standing rule
after the hallucinated-GitHub-URL and false-alarm-balance-error lessons):
`deepseek/deepseek-chat`, `deepseek/deepseek-v4-flash`, and
`deepseek/deepseek-v4-pro` all resolved to real, working completions on
this deployment (an initial `max_tokens=5` test made `-flash`/`-pro` look
like they were returning empty content -- re-tested with `max_tokens=50`
and both returned real `"OK"` content with `finish_reason="stop"`, so that
was a token-budget artifact, not a real model-name failure). Settled on
`deepseek/deepseek-v4-flash` for consistency with this session's other
DeepSeek-using adapters. No auth/balance/quota error was ever encountered
during development; `LITELLM_MAX_RETRY` is nonetheless reduced from
upstream's own default of 10 to 2 so that a real auth/balance failure would
fail fast rather than silently retrying for ~10+ seconds, per this
session's cost-control convention -- if a real call still raises an
auth/insufficient-balance/quota-shaped exception, `_run_pipeline()` below
re-raises it as a clear `RuntimeError("DeepSeek API balance may be
exhausted")` instead of masking or looping on it.

============================================================================
Scope reductions (translation choices made by this adapter, not upstream)
============================================================================
  - **Bounded to one hypothesis, one factor task, at most two real CoSTEER
    implement/evaluate rounds** -- upstream's own full `FactorRDLoop.run()`
    is an unbounded multi-round propose/code/run/feedback loop (by design:
    RD-Agent is meant to run for many hours/rounds refining a factor
    library), the same class of unbounded-turn-count problem
    `vibe_trading_adapter.py`'s session already solved for its own upstream
    `AgentLoop` -- this adapter applies the identical pattern: call the same
    real underlying primitives (`hypothesis_gen.gen()`,
    `hypothesis2experiment.convert()`, `QlibFactorCoSTEER(scen,
    max_loop=2).develop(exp)`) directly instead of driving `RDLoop.run()`'s
    own indefinite `while True` orchestration. `max_loop=2` (not 1) was
    chosen after `max_loop=1` was found, during development, to raise
    upstream's own real `CoderError("All tasks are failed")` whenever the
    single real implementation attempt happened to be rejected by the real
    evaluator (e.g. a real critique that the generated code should multiply
    `$close` by `$factor` before computing momentum) -- `max_loop=2` gives
    the real loop one genuine chance to use its own real round-1
    execution/code/value feedback to correct round 2's implementation,
    which is the actual "iterate" step of propose/implement/validate/
    iterate, still just 1-2 real proposal-and-evaluate cycles per this
    session's own bound. If every attempt within the 2-round bound is still
    rejected, `_run_pipeline()` catches the real `CoderError` and reports a
    disclosed NEUTRAL/zero-strength signal carrying upstream's own real
    rejection feedback as evidence, rather than retrying further, forcing a
    fabricated success, or crashing.
    `hypothesis2experiment.convert()` may propose 1-3 factor tasks in one
    JSON response; this adapter keeps only the first (`exp.sub_tasks =
    exp.sub_tasks[:1]`) before handing it to the coder, to keep the real
    call count small and predictable (~5-8 real LLM calls total, ~60-120s
    wall-clock, confirmed empirically, comfortably inside the harness's
    smoke_test<300s/run()<600s budgets) -- this is the adapter selecting a
    subset of upstream's own real output, not reimplementing upstream's
    formulation logic.
  - **Upstream's Docker-based `QlibFactorRunner` backtest is never invoked.**
    The full research loop's final step normally sends the implemented
    factor into a dockerized Qlib installation to train an LGBM model and
    backtest a portfolio -- this needs Docker plus a multi-GB China-A-share
    Qlib data bundle (`generate_data_folder_from_qlib()`), well outside this
    harness's timeout budget and CLAUDE.md's "thin wrapper" mandate. This
    adapter stops at the real CoSTEER implement+evaluate step (which already
    executes the real generated code against real data and produces a real
    LLM-as-judge accept/reject verdict) -- a materially real "implement +
    validate" outcome without the heavyweight backtest infrastructure.
  - **Real yfinance data substituted for Qlib's own Docker-built China-A-share
    bundle**, reshaped into upstream's own exact expected schema
    (`daily_pv.h5`, key="data", MultiIndex[instrument, datetime],
    `$open/$close/$high/$low/$volume/$factor` columns, `$factor=1.0` since
    yfinance's `auto_adjust=True` close is already split/dividend-adjusted)
    -- confirmed by reading upstream's own
    `factor_data_template/generate.py` and `factor_data_template/README.md`
    for the exact contract. Same "point-in-time real-data substitution"
    pattern this session's `atlas_adapter.py`/`finclaw_adapter.py`/
    `finrl_x_adapter.py` used for their own data-source mismatches. Because
    `rdagent/scenarios/qlib/experiment/utils.py::get_data_folder_intro()`
    only calls the (skipped) Docker data-generation path when
    `FACTOR_COSTEER_DATA_FOLDER(_DEBUG)` doesn't already exist, pre-populating
    both directories with real data before constructing `QlibFactorScenario()`
    causes upstream's own code to skip that path entirely and read this
    adapter's real data instead -- verified this happens correctly (no
    Docker/network calls attempted) during development.
  - **Knowledge-base self-generation disabled**
    (`knowledge_self_gen=False`, `with_knowledge=True` -- the latter is
    required by `MultiProcessEvolvingStrategy.evolve_iter()`, confirmed by a
    real `ValueError` when first tried with it off). Discovered empirically:
    upstream's own `CoSTEERRAGStrategyV2.generate_knowledge()` step (which
    persists successful/failed implementations into a cross-run knowledge
    graph) embeds each implementation via a hardcoded
    `text-embedding-3-small` OpenAI embedding model regardless of the chat
    backend -- this raised a real `litellm.InternalServerError: Missing
    credentials ... OPENAI_API_KEY` during development. This is unrelated to
    the real DeepSeek chat call (which always succeeded) and is not a
    balance/auth problem with this adapter's actual target call --
    confirmed by reading the traceback back to
    `vector_base.py::create_embedding()` rather than assumed. Since this
    adapter makes one bounded, ephemeral call per (ticker, date) with no
    persisted `knowledge_base_path` anyway, disabling self-generation loses
    nothing this adapter would have used, and avoids provisioning a second,
    unrelated OpenAI key for a feature outside this session's scope.
  - **Direction/strength translated via this adapter's own correlation
    statistic**, not upstream's own evaluation logic: upstream's real
    evaluators already judge code/format/execution correctness (a real
    accept/reject verdict, included in `supporting_evidence`); to map the
    real factor *values* onto CONTRACT's LONG/SHORT/NEUTRAL + strength
    fields, this adapter computes the Pearson correlation between the real
    generated factor series and the real forward N-day return computed from
    the same real yfinance closes (`FORWARD_RETURN_DAYS=5`), then combines
    `sign(correlation) * sign(latest factor value)` for direction and
    `abs(correlation)` (already bounded in [0,1]) for strength. This is the
    adapter's own schema-translation arithmetic (same class of step as
    CLAUDE.md's own `Action.BUY if result["signal"] > 0` example), not a
    reimplementation of RD-Agent's research method itself.
  - **`WORKSPACE_PATH` / `FACTOR_COSTEER_DATA_FOLDER(_DEBUG)` env vars set**
    to real paths under this adapter's own gitignored `adapters/vendor/
    RD-Agent/git_ignore_folder/` before any `rdagent.*` import, so upstream's
    own pydantic-settings singletons (built once at first import) never
    default to creating a stray `git_ignore_folder/` at the trading-ai-
    ensemble repo root (upstream's own literal default is `Path.cwd() /
    "git_ignore_folder" / ...`).

============================================================================
v1 -> v2.0.0 schema migration notes (added during migration; the mechanism/
verification/scope-reduction narrative above is from the original v1 build
and is still accurate — only the canonical field mapping below changed)
============================================================================
  - `SignalType` no longer exists in v2 at all; deleted. `signal_semantics`
    (free text) replaces it: describes the real executed value of the
    RD-Agent-implemented `factor.py` for this ticker as a continuous score,
    not a return prediction or probability.
  - **`values: Dict[ticker, float]` (new, required)**: the real executed
    factor value — `workspace.execute()`'s own real local subprocess run of
    the real LLM-generated `factor.py`, the latest non-null value of the
    resulting real per-date `factor_series` for the one real ticker this
    pipeline fetched data for. This pipeline only ever builds data for a
    single ticker (`_build_debug_data(ticker, date)`), so `values` is a
    single-entry dict here, not a cross-section — a genuine difference from
    alphagen/atlas (whose pools are evaluated over a real multi-ticker
    universe), disclosed rather than papered over with a fabricated
    cross-section.
  - **If the real pipeline produces no valid executed factor value this
    call** (a genuine `CoderError` — the real CoSTEER evaluator rejected
    every attempt within the bounded 2-round loop — or a real execution
    that returns an empty/all-NaN series), `q3_signal` returns `None`
    rather than fabricating a `values` entry: `Q3Signal.values` is
    required and non-empty in v2, and CLAUDE.md forbids fabricating a
    field with no real source. This did not happen during the real smoke
    run for this migration but is a real, disclosed possible outcome of
    the bounded LLM loop; see "测试结果" in the migration report for
    whether it was observed.
  - `factor_expression` (new): `task.factor_formulation`, the real LLM-
    formulated LaTeX/formula-string produced by
    `QlibFactorHypothesis2Experiment.convert()` — NATIVE (upstream's own
    field, not adapter-derived).
  - `supporting_evidence: List[str]` -> `evidence: Optional[List[EvidenceItem]]`,
    typed per this migration's brief: `kind="hypothesis"` for
    `Hypothesis.hypothesis`, `kind="hypothesis_reason"` for
    `Hypothesis.reason`, `kind="factor_formulation"` for the real
    `FactorTask.factor_name`/`.factor_description`/`.factor_formulation`,
    `kind="coder_feedback"` for the real `HypothesisFeedback.final_decision`/
    `.final_feedback` (or the real `CoderError` text when the bounded loop
    never converged), and `kind="correlation_diagnostic"` for this
    adapter's own Pearson-correlation direction/strength translation.
  - `explanation` (new): `Hypothesis.hypothesis` — the real LLM-proposed
    hypothesis text, used verbatim (per this migration's brief), not
    wrapped in adapter-authored template prose.
  - `expected_return` (v1 field, always `None` here already) has no v2
    equivalent populated for the same reason as alphagen/atlas: no
    reliable per-ticker expected-return number exists in this adapter
    beyond the direction/strength translation itself.
  - `expected_horizon` (v1 top-level field) no longer exists in v2's
    `Q3Signal` — the real `FORWARD_RETURN_DAYS=5` window used for this
    adapter's own correlation statistic is disclosed in `explanation`/
    `evidence` text instead of a dedicated field, and remains an
    adapter-internal constant (not read from `context.horizon`), per this
    migration rubric's explicit allowance.
  - `direction`/`strength`: unchanged in derivation (same real Pearson
    correlation between the real executed factor series and the real
    forward-return series, `sign(corr) * sign(latest_value)` for direction,
    `abs(corr)` for strength) but now `Optional` per v2.
  - `confidence`: left `None` — no native or reliably-derivable confidence
    exists distinct from the correlation-based `strength`; the real
    CoSTEER accept/reject verdict is a code-quality judgment, not a
    signal-confidence estimate, so it stays in `evidence`
    (`kind="coder_feedback"`) rather than being repurposed as `confidence`.
  - `q3_signal(ticker, date)` -> `q3_signal(context: QueryContext)`: ticker
    read from `context.targets[0]` (required — this adapter has no
    universe-fallback concept, unlike alphagen/atlas, since it fetches data
    for exactly the one requested ticker), date from `context.data_cutoff`.
    `context` is echoed back unchanged into `Q3Signal(context=context, ...)`
    per the v2 contract.
  - `run()` is now overridden to attach a faithful `native_output` (the
    real hypothesis/reason/factor-task/feedback text, the real generated
    `factor.py` source, the real correlation statistic, under a separate
    `adapter_derived` key for the direction/strength translation) and —
    since this is the one adapter of this migration's three that spends
    real money on a real LLM API — the real observed `cost_usd`
    (`_litellm_backend.ACC_COST` delta) and wall-clock `latency_sec`,
    patched onto `RunMetadata` after `super().run()` builds it (that method
    itself never threads q3_signal's cost/latency into `RunMetadata`, so
    this is the only place those real, already-tracked numbers can be
    attached without modifying `CONTRACT/base_adapter.py`).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Direction, EvidenceItem, OutputScope, Q3Signal, QueryContext

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "RD-Agent"
DEEPSEEK_ENV_PATH = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"
DATA_ROOT = VENDOR_DIR / "git_ignore_folder"
DATA_FOLDER = DATA_ROOT / "factor_implementation_source_data"
DATA_FOLDER_DEBUG = DATA_ROOT / "factor_implementation_source_data_debug"
WORKSPACE_ROOT = DATA_ROOT / "RD-Agent_workspace"
LOG_ROOT = DATA_ROOT / "log"
PICKLE_CACHE_ROOT = DATA_ROOT / "pickle_cache"

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from dotenv import load_dotenv  # noqa: E402  (vendor path must be on sys.path first)

load_dotenv(dotenv_path=DEEPSEEK_ENV_PATH)

# All of these must be set *before* any `rdagent.*` import: the pydantic-settings
# singletons that read them (FACTOR_COSTEER_SETTINGS, LITELLM_SETTINGS,
# RD_AGENT_SETTINGS) are constructed once at first import and never re-read.
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
DATA_FOLDER_DEBUG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("FACTOR_COSTEER_DATA_FOLDER", str(DATA_FOLDER))
os.environ.setdefault("FACTOR_COSTEER_DATA_FOLDER_DEBUG", str(DATA_FOLDER_DEBUG))
os.environ.setdefault("WORKSPACE_PATH", str(WORKSPACE_ROOT))
# Two more of upstream's own `Path.cwd() / ...` scratch-output defaults
# (rdagent/log/conf.py::LogSettings.trace_path, rdagent/core/conf.py::
# RDAgentSettings.pickle_cache_folder_path_str) that would otherwise leak a
# `log/` and `pickle_cache/` directory into the trading-ai-ensemble repo root
# when this adapter is imported/run -- redirected under the same gitignored
# vendor-local scratch root as WORKSPACE_PATH above, discovered empirically
# during development (see DECISIONS_rdagent.md).
os.environ.setdefault(
    "LOG_TRACE_PATH", str(LOG_ROOT / time.strftime("%Y-%m-%d_%H-%M-%S"))
)
os.environ.setdefault("PICKLE_CACHE_FOLDER_PATH_STR", str(PICKLE_CACHE_ROOT))
# DeepSeek model name verified empirically against a real call during development
# (see module docstring / DECISIONS_rdagent.md).
os.environ.setdefault("LITELLM_CHAT_MODEL", "deepseek/deepseek-v4-flash")
os.environ.setdefault("LITELLM_CHAT_STREAM", "False")
# Cost control: fail fast on a real auth/balance error instead of upstream's own
# default 10-retry backoff loop.
os.environ.setdefault("LITELLM_MAX_RETRY", "2")

from rdagent.core.exception import CoderError  # noqa: E402
from rdagent.core.proposal import Trace  # noqa: E402
from rdagent.scenarios.qlib.developer.factor_coder import QlibFactorCoSTEER  # noqa: E402
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorScenario  # noqa: E402
from rdagent.scenarios.qlib.proposal.factor_proposal import (  # noqa: E402
    QlibFactorHypothesis2Experiment,
    QlibFactorHypothesisGen,
)
import rdagent.oai.backend.litellm as _litellm_backend  # noqa: E402

LOOKBACK_DAYS = 550
FORWARD_RETURN_DAYS = 5
_README_PATH = (
    VENDOR_DIR / "rdagent" / "scenarios" / "qlib" / "experiment" / "factor_data_template" / "README.md"
)
_README_TEXT = _README_PATH.read_text(encoding="utf-8")

_PIPELINE_CACHE: Dict[Tuple[str, str], dict] = {}


def _classify_llm_error(exc: Exception) -> None:
    """Re-raise a clear balance/auth error, or the original exception otherwise.

    Upstream's own retry loop (`_try_create_chat_completion_or_embedding`) wraps
    the underlying litellm exception into a generic `RuntimeError("Failed to
    create chat completion after N retries.")`, losing the original message --
    this is a best-effort classification on whatever text is available, same
    convention every other DeepSeek-using adapter this session applies.
    """
    msg = str(exc).lower()
    if any(
        s in msg
        for s in ("insufficient", "balance", "quota", "401", "unauthorized", "authentication", "api key", "credentials")
    ):
        raise RuntimeError("DeepSeek API balance may be exhausted") from exc
    raise exc


def _build_debug_data(ticker: str, date: str) -> pd.Series:
    """Real yfinance OHLCV, point-in-time windowed to end at `date`, reshaped into
    upstream's own qlib-schema `daily_pv.h5` ($open/$close/$high/$low/$volume/
    $factor, MultiIndex[instrument, datetime]). Returns the real close-price
    series (kept in-process for this adapter's own forward-return direction
    scoring, see module docstring "Scope reductions").
    """
    end = pd.Timestamp(date)
    start = end - pd.Timedelta(days=LOOKBACK_DAYS)
    df = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker} in {start.date()}/{end.date()}")

    df = df.copy()
    df.columns = [c[0] for c in df.columns]  # drop yfinance's per-ticker column level
    close = df["Close"].copy()
    close.index.name = "datetime"

    qdf = df.rename(
        columns={"Open": "$open", "Close": "$close", "High": "$high", "Low": "$low", "Volume": "$volume"}
    )
    qdf["$factor"] = 1.0
    qdf.index.name = "datetime"
    qdf["instrument"] = ticker
    qdf = qdf.reset_index().set_index(["instrument", "datetime"]).sort_index()
    qdf = qdf[["$open", "$close", "$high", "$low", "$volume", "$factor"]]

    for out_dir in (DATA_FOLDER, DATA_FOLDER_DEBUG):
        qdf.to_hdf(out_dir / "daily_pv.h5", key="data", mode="w")
        (out_dir / "README.md").write_text(_README_TEXT, encoding="utf-8")

    return close


def _direction_and_strength(factor_series: pd.Series, close: pd.Series) -> Tuple[Direction, float, Optional[float]]:
    """Translate the real upstream-generated factor values into direction/
    strength via a real, disclosed statistic -- see module docstring, "Scope
    reductions".
    """
    if factor_series.empty:
        return Direction.NEUTRAL, 0.0, None

    fwd_ret = close.shift(-FORWARD_RETURN_DAYS) / close - 1.0
    aligned = pd.concat([factor_series.rename("factor"), fwd_ret.rename("fwd_ret")], axis=1, join="inner").dropna()
    if len(aligned) < 10:
        return Direction.NEUTRAL, 0.0, None

    corr = aligned["factor"].corr(aligned["fwd_ret"])
    if pd.isna(corr):
        return Direction.NEUTRAL, 0.0, None

    latest_nonnull = factor_series.dropna()
    if latest_nonnull.empty:
        return Direction.NEUTRAL, 0.0, float(corr)

    latest_value = float(latest_nonnull.iloc[-1])
    score = corr * latest_value
    if score > 1e-9:
        direction = Direction.LONG
    elif score < -1e-9:
        direction = Direction.SHORT
    else:
        direction = Direction.NEUTRAL
    strength = float(min(1.0, abs(corr)))
    return direction, strength, float(corr)


def _extract_factor_series(factor_df: Optional[pd.DataFrame], ticker: str) -> pd.Series:
    if factor_df is None or factor_df.shape[1] == 0:
        return pd.Series(dtype=float)
    s = factor_df.iloc[:, 0]
    if isinstance(s.index, pd.MultiIndex) and "instrument" in s.index.names:
        try:
            s = s.xs(ticker, level="instrument")
        except KeyError:
            s = s.droplevel("instrument")
    return s.sort_index()


def _run_pipeline(ticker: str, date: str) -> dict:
    """Real, bounded RD-Agent factor-mining pipeline: propose (1 real LLM call)
    -> formulate (1 real LLM call) -> implement + execute + evaluate (a real,
    unmodified `QlibFactorCoSTEER` round: 1 real LLM call to write factor.py,
    a real local execution, and 2 real LLM evaluator calls). See module
    docstring for the full mechanism/scope-reduction narrative.
    """
    key = (ticker, date)
    if key in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[key]

    cost_before = _litellm_backend.ACC_COST
    try:
        close = _build_debug_data(ticker, date)

        scen = QlibFactorScenario()
        trace = Trace(scen=scen)
        plan = {"features": {}, "feature_codes": {}}

        hg = QlibFactorHypothesisGen(scen)
        hypothesis = hg.gen(trace, plan)

        h2e = QlibFactorHypothesis2Experiment()
        exp = h2e.convert(hypothesis, trace)
        exp.base_features = {}
        exp.base_feature_codes = {}
        # Bounded scope: keep only the first real factor task the LLM proposed
        # (see module docstring "Scope reductions").
        exp.sub_tasks = exp.sub_tasks[:1]
        task = exp.sub_tasks[0]

        # Bounded to 2 real rounds (not upstream's own unbounded default): gives
        # the real CoSTEER loop one genuine chance to use its own real
        # execution/code/value feedback from round 1 to correct round 2's
        # implementation if the first attempt is rejected -- exercising the
        # actual "iterate" step of propose/implement/validate/iterate, still
        # well inside this session's "1-2 real proposal-and-evaluate cycles"
        # bound (see module docstring "Scope reductions").
        coder = QlibFactorCoSTEER(scen, max_loop=2, with_knowledge=True, knowledge_self_gen=False)
        try:
            exp2 = coder.develop(exp)
        except CoderError as coder_exc:
            # A genuine, disclosed non-convergence: the real evaluator rejected
            # every attempt within the bounded loop. Reported honestly as a
            # weak/neutral signal with upstream's own real rejection feedback
            # as evidence, rather than retried further or forced to "success".
            result = {
                "hypothesis": hypothesis,
                "task": task,
                "feedback": None,
                "coder_error": str(coder_exc),
                "factor_code": "",
                "factor_series": pd.Series(dtype=float),
                "direction": Direction.NEUTRAL,
                "strength": 0.0,
                "corr": None,
                "cost_usd": max(0.0, _litellm_backend.ACC_COST - cost_before),
            }
            _PIPELINE_CACHE[key] = result
            return result

        workspace = exp2.sub_workspace_list[0] if exp2.sub_workspace_list else None
        prop_fb = getattr(exp2, "prop_dev_feedback", None)
        feedback = prop_fb[0] if (prop_fb is not None and len(prop_fb) > 0) else None

        factor_code = ""
        factor_series = pd.Series(dtype=float)
        if workspace is not None:
            factor_code = workspace.file_dict.get("factor.py", "")
            _exec_feedback_text, factor_df = workspace.execute()
            factor_series = _extract_factor_series(factor_df, ticker)

        direction, strength, corr = _direction_and_strength(factor_series, close)

        result = {
            "hypothesis": hypothesis,
            "task": task,
            "feedback": feedback,
            "coder_error": None,
            "factor_code": factor_code,
            "factor_series": factor_series,
            "direction": direction,
            "strength": strength,
            "corr": corr,
            "cost_usd": max(0.0, _litellm_backend.ACC_COST - cost_before),
        }
        _PIPELINE_CACHE[key] = result
        return result
    except Exception as exc:  # noqa: BLE001 - classify below, don't swallow
        _classify_llm_error(exc)
        raise


class RDAgentAdapter(BaseAdapter):
    name = "rdagent"
    questions_answered = ["Q3"]
    upstream_repo = "https://github.com/microsoft/RD-Agent"
    requires_env = "rdagent_real"

    # ------------------------------------------------------------------
    # Q3 — Alpha signal via a real, bounded LLM-agent research round
    # ------------------------------------------------------------------
    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        if not context.targets:
            raise ValueError(
                "rdagent q3_signal requires context.targets[0] — this adapter fetches "
                "real data for exactly one requested ticker, it has no universe-fallback "
                "concept like alphagen/atlas."
            )
        ticker = context.targets[0]
        date = context.data_cutoff or context.as_of

        result = _run_pipeline(ticker, date)

        hyp = result["hypothesis"]
        task = result["task"]
        fb = result["feedback"]

        # `values`: the real executed factor value (workspace.execute()'s real
        # local subprocess run of the real LLM-generated factor.py) — a
        # single-ticker dict since this pipeline only ever fetches data for
        # the one requested ticker (see header migration notes).
        factor_series = result.get("factor_series")
        latest_value: Optional[float] = None
        if factor_series is not None and not factor_series.empty:
            nonnull = factor_series.dropna()
            if not nonnull.empty:
                latest_value = float(nonnull.iloc[-1])

        if latest_value is None:
            # No real executed factor value this call (CoderError non-convergence,
            # or a real execution that produced an empty/all-NaN series).
            # Q3Signal.values is required and non-empty in v2 — never fabricate
            # an entry, so this adapter has nothing honest to return this call.
            self._last_native_output = {
                "upstream": {
                    "hypothesis": hyp.hypothesis,
                    "hypothesis_reason": hyp.reason,
                    "factor_name": task.factor_name,
                    "factor_description": task.factor_description,
                    "factor_formulation": task.factor_formulation,
                    "coder_error": result.get("coder_error"),
                    "factor_code": result.get("factor_code", ""),
                },
                "adapter_derived": {"ticker": ticker, "no_real_value_reason": "empty/non-convergent factor_series"},
            }
            self._last_cost_usd = result["cost_usd"]
            self._last_latency_sec = time.time() - t0
            return None

        values: Dict[str, float] = {ticker: latest_value}

        evidence: List[EvidenceItem] = [
            EvidenceItem(
                kind="hypothesis",
                value=hyp.hypothesis,
                source="RD-Agent QlibFactorHypothesisGen.gen() (real LLM call)",
            ),
            EvidenceItem(
                kind="hypothesis_reason",
                value=hyp.reason,
                source="RD-Agent QlibFactorHypothesisGen.gen() (real LLM call)",
            ),
            EvidenceItem(
                kind="factor_formulation",
                value=f"'{task.factor_name}': {task.factor_description} [formulation: {task.factor_formulation}]",
                source="RD-Agent QlibFactorHypothesis2Experiment.convert() (real LLM call)",
            ),
        ]
        if fb is not None:
            evidence.append(EvidenceItem(
                kind="coder_feedback",
                value=f"final_decision={fb.final_decision} -- {fb.final_feedback}",
                source="RD-Agent QlibFactorCoSTEER real CoSTEERSingleFeedback (real LLM-as-judge call)",
            ))
            # Recovered (previously discarded): upstream's real per-stage
            # feedback fields on FactorSingleFeedback (= CoSTEERSingleFeedbackDeprecated)
            # — execution_feedback (real local-execution stdout summary),
            # value_feedback (real FactorValueEvaluator verdict on the
            # generated factor's numeric output), and code_feedback (real
            # FactorCodeEvaluator LLM code critique) — distinct from, and
            # richer than, the single final_decision/final_feedback pair
            # already captured above.
            if getattr(fb, "execution_feedback", None):
                evidence.append(EvidenceItem(
                    kind="execution_feedback",
                    value=fb.execution_feedback,
                    source="RD-Agent FactorEvaluatorForCoder (real local subprocess execution of factor.py)",
                ))
            if getattr(fb, "value_feedback", None):
                evidence.append(EvidenceItem(
                    kind="value_feedback",
                    value=fb.value_feedback,
                    source="RD-Agent FactorValueEvaluator (real evaluator over the executed factor values)",
                ))
            if getattr(fb, "code_feedback", None):
                evidence.append(EvidenceItem(
                    kind="code_feedback",
                    value=fb.code_feedback,
                    source="RD-Agent FactorCodeEvaluator (real LLM code critique)",
                ))
        if result.get("coder_error"):
            evidence.append(EvidenceItem(
                kind="coder_feedback",
                value=(
                    "Real CoSTEER round did not converge on an accepted implementation within "
                    f"the bounded 2-round loop -- upstream's own real rejection feedback: "
                    f"{result['coder_error']}"
                ),
                source="RD-Agent QlibFactorCoSTEER (real local execution + evaluator)",
            ))
        explanation = hyp.hypothesis
        if result["corr"] is not None:
            evidence.append(EvidenceItem(
                kind="correlation_diagnostic",
                value=(
                    f"This adapter's own translation: correlation of the real executed factor "
                    f"values with {ticker}'s real {FORWARD_RETURN_DAYS}-day forward return = "
                    f"{result['corr']:.4f} (used to derive direction/strength, not upstream's "
                    "own evaluation)."
                ),
                source="adapter_derived (Pearson correlation, factor_series vs forward return)",
            ))

        self._last_native_output = {
            "upstream": {
                "hypothesis": hyp.hypothesis,
                "hypothesis_reason": hyp.reason,
                "factor_name": task.factor_name,
                "factor_description": task.factor_description,
                "factor_formulation": task.factor_formulation,
                "coder_feedback": (
                    {
                        "final_decision": fb.final_decision,
                        "final_feedback": fb.final_feedback,
                        "execution_feedback": getattr(fb, "execution_feedback", None),
                        "value_feedback": getattr(fb, "value_feedback", None),
                        "code_feedback": getattr(fb, "code_feedback", None),
                        "value_generated_flag": getattr(fb, "value_generated_flag", None),
                        "final_decision_based_on_gt": getattr(fb, "final_decision_based_on_gt", None),
                    }
                    if fb is not None else None
                ),
                "coder_error": result.get("coder_error"),
                "factor_code": result.get("factor_code", ""),
                "executed_factor_value": latest_value,
            },
            "adapter_derived": {
                "ticker": ticker,
                "correlation": result["corr"],
            },
        }
        self._last_cost_usd = result["cost_usd"]
        self._last_latency_sec = time.time() - t0

        return Q3Signal(
            context=context,
            signal_semantics=(
                "factor_value — the real executed value of the RD-Agent-implemented factor.py "
                "for this ticker (LLM-proposed hypothesis -> formulated factor -> generated + "
                "locally-executed code), not a return prediction or probability."
            ),
            values=values,
            score_scale="continuous, unitless (real locally-executed generated-code output)",
            direction=result["direction"],
            strength=result["strength"],
            factor_expression=task.factor_formulation,
            evidence=evidence,
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
        native_output plus the real observed cost_usd/latency_sec (this
        adapter is the one of the three migrated in this batch that spends
        real money on a real DeepSeek LLM call; BaseAdapter.run() itself
        never threads a q*_method's cost/latency into RunMetadata, so this
        is the only place those already-tracked real numbers can be
        attached without touching CONTRACT/base_adapter.py)."""
        self._last_native_output = None
        self._last_cost_usd = 0.0
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native_output:
            updates["native_output"] = self._last_native_output
        if self._last_cost_usd or self._last_latency_sec:
            updates["run"] = result.run.model_copy(update={
                "cost_usd": self._last_cost_usd,
                "latency_sec": self._last_latency_sec,
            })
        if updates:
            result = result.model_copy(update=updates)
        return result

    # ------------------------------------------------------------------
    # Smoke test — one real call through the full bounded pipeline
    # ------------------------------------------------------------------
    def smoke_test(self) -> Dict[str, bool]:
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        try:
            q3 = self.q3_signal(context)
            checks["q3_returns_Q3Signal"] = q3 is not None
            if q3 is not None:
                checks["context_echoed_unchanged"] = q3.context == context
                checks["q3_values_nonempty"] = len(q3.values) > 0
                checks["q3_direction_valid"] = q3.direction in ("LONG", "SHORT", "NEUTRAL", None)
                checks["q3_strength_in_range"] = q3.strength is None or 0.0 <= q3.strength <= 1.0
                checks["q3_evidence_nonempty"] = bool(q3.evidence)
                checks["q3_evidence_includes_real_hypothesis"] = any(
                    (e.kind == "hypothesis" and e.value) for e in (q3.evidence or [])
                )
                # Recovered fields: if a real coder_feedback round happened (not a
                # CoderError non-convergence), at least one of the richer per-stage
                # feedback kinds (execution_feedback/value_feedback/code_feedback)
                # should now be present alongside the pre-existing coder_feedback.
                evidence_kinds = {e.kind for e in (q3.evidence or [])}
                if "coder_feedback" in evidence_kinds:
                    checks["q3_evidence_includes_richer_coder_feedback"] = bool(
                        evidence_kinds & {"execution_feedback", "value_feedback", "code_feedback"}
                    )
        except Exception:
            checks["q3_smoke_call_succeeds"] = False
        return checks
