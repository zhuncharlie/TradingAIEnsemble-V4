"""
adapters/finmem_adapter.py — wraps github.com/pipiku915/FinMem-LLM-StockTrading
(Q1 only — see "Q4 investigation" below for why Q4 is NOT claimed).

Repo: cloned at adapters/vendor/FinMem-LLM-StockTrading, commit be814aa4
(2024-08-17). Single LLM agent (`puppy/agent.py::LLMAgent`) + layered
short/mid/long/reflection memory (`puppy/memorydb.py::BrainDB`) + a real
`Portfolio` class (`puppy/portfolio.py`) driven one real trading day at a
time via `LLMAgent.step(market_info, run_mode)`.

============================================================================
Real capability found (Q1)
============================================================================
`LLMAgent.step()` (agent.py:565-608) is a real, causal per-day pipeline:
handle filings -> handle news -> update portfolio market price -> `_reflect()`
(a real LLM call producing `reflection_result_series_dict[cur_date] =
{"investment_decision": "buy"/"sell"/"hold", "summary_reason": "..."}`) ->
construct the real action -> `_portfolio_step()`. This adapter drives exactly
one real `step()` call in `RunMode.Test` and reads the real
`investment_decision`/`summary_reason` for that one day. `Action` maps
buy->BUY, sell->SELL, hold->HOLD (verified against agent.py:530-540, the
values compared are literally the strings "buy"/"hold" — "sell" is the
remaining branch).

============================================================================
Q4 investigation — NOT claimed, real reasons why (both are independent,
either one alone would already rule Q4 out)
============================================================================
1. **Weights are categorically ABSENT, not just hard to reach.** Read
   `puppy/portfolio.py::Portfolio` in full: `__init__` has no cash field at
   all. `record_action()` only does
   `self.holding_shares += action["direction"]` where `direction` is always
   +1/-1/0. There is no price-weighted position value and no cash balance
   anywhere in the class, so a `target_weights` dict can never be honestly
   derived from this project's real state — this is a real, structural
   limitation of the upstream project (PROJECT_SCHEMA_AUDIT.md's own finding,
   re-confirmed here by direct source reading), not an adapter mapping
   choice. A direction-only (weight-less) Q4 trajectory would be schema-legal
   (`Q4Policy.initial_weights`/`PolicyDecisionStep` weights are Optional),
   but was not built — see point 2.
2. **The real LLM-call path this project needs is genuinely BLOCKED with the
   only credential available in this sandbox**, so a multi-day trajectory
   could never actually be run and verified end-to-end, only written
   speculatively. Verified two independent ways:
   - Chat: `puppy/chat.py::ChatOpenAICompatible.parse_response()` (chat.py:
     60-71) hard-dispatches on `self.model.startswith("gpt"/"gemini-pro"/
     "tgi")`, else `raise NotImplementedError`. The real request payload also
     sends `"model": self.model` verbatim to the real endpoint
     (chat.py:123), so a DeepSeek model name (`deepseek-chat`, none of which
     start with any of those three prefixes) cannot be smuggled through by
     relabeling it "gpt-..." either — DeepSeek's real API would reject an
     unrecognized model name in that field, and doing so would misrepresent
     provenance regardless. This project's real, official usage
     (`run_opeai.sh`, `config/tsla_gpt_config.toml`) requires an actual
     OpenAI API key and `model = "gpt-3.5-turbo-0125"` — not available here.
   - Embeddings: `puppy/embedding.py::OpenAILongerThanContextEmb` wraps
     `langchain_community.embeddings.OpenAIEmbeddings` with no `base_url`
     override exposed, so it always targets the real OpenAI embeddings API —
     also unusable with only a DeepSeek key. `BrainDB` (memorydb.py:56)
     constructs this at `__init__` time (lazy — no call yet), but any real
     `add_memory_*`/`query_*` during `_handling_news`/`_reflect()` would hit
     it and fail the same way.
   This project's only real, legitimate LLM credential available in this
   session is `DEEPSEEK_API_KEY` (adapters/vendor/ai-hedge-fund/.env, reused
   by several existing adapters) — no other credential was searched for or
   used. Per CLAUDE.md, this adapter does not monkey-patch
   `ChatOpenAICompatible`/`OpenAILongerThanContextEmb` to route around this;
   it is documented and left BLOCKED.

   **Empirically confirmed live** (2026-07, `finmem_real` env,
   `python CONTRACT/adapter_runner.py --adapter adapters/finmem_adapter.py
   --task-id verify_finmem --as-of 2024-01-15 --scope ASSET --target AAPL
   --universe AAPL`): the embeddings sub-blocker fires FIRST, before the
   chat-completions call is ever reached — `LLMAgent.step()` ->
   `_handling_news()` -> `BrainDB.add_memory_short()` ->
   `OpenAILongerThanContextEmb.__call__()` -> real
   `openai.AuthenticationError: Error code: 401 - Incorrect API key provided:
   sk-9f01f***...` — a real 401 from the REAL `api.openai.com` (not a stub),
   because the DeepSeek key is not a valid OpenAI key. This is the actual
   observed failure, not a hypothetical; the chat-completions
   `parse_response()` prefix gate documented above is a second, independent,
   still-real blocker that this run never even reached.

Given both, this adapter claims **Q1 only**, and Q1 itself is fully wired
with real objects (real `Portfolio`, real `BrainDB`, real `LLMAgent`,
real `MarketEnvironment`-shaped single-day data built from real yfinance
price+news) — but the live LLM call inside `_reflect()` is expected to fail
with a real, honest error (see smoke_test()/run() below), not a fabricated
response. This is the same "BLOCKED, not routed around" pattern already
established for `nofx`/real-nofx in this repo.

============================================================================
Field-by-field classification
============================================================================
- `Q1Action.action`            -> NATIVE (real `investment_decision`, when
                                   the real LLM call succeeds)
- `Q1Action.explanation`       -> NATIVE (real `summary_reason`)
- `Q1Action.confidence`        -> MISSING: no numeric confidence anywhere in
                                   `reflection_result_series_dict`; not
                                   guessed.
- `Q1Action.target_position`   -> MISSING (see Q4 investigation above; same
                                   reason a Q4 trajectory isn't claimed)
- Time semantics: single real trading day per call, driven via
  `RunMode.Test`; `context.as_of` is the day requested; real filings/news
  memory is seeded only from real data this adapter itself fetches (no
  historical replay infrastructure — `data-pipeline/` scripts require SEC
  API / bulk news vendor credentials not available here).
- Asset scope: single-ticker only (`Portfolio(symbol=...)` is scalar).
- Dependencies/runtime limits: conda env `finmem_real`; real yfinance for
  price+news; real DeepSeek key for the LLM call attempt (which is expected
  to fail per the BLOCKED finding above — this is not a bug, it's the
  documented real outcome).

No upstream source was patched — only environment/dependency setup and this
adapter's own thin-wrapper glue.
"""

from __future__ import annotations

import os
import sys
from datetime import date as date_type
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    AdapterResult,
    OutputScope,
    Q1Action,
    QueryContext,
    TimeWindow,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "FinMem-LLM-StockTrading"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Reuse the existing DeepSeek key (adapters/vendor/ai-hedge-fund/.env) rather
# than requiring/searching for a new one — same key several existing
# adapters in this repo already use. FinMem's ChatOpenAICompatible reads
# OPENAI_API_KEY specifically (chat.py:37), so alias it under that name —
# this is the exact same "reuse a real key under upstream's expected env-var
# name" pattern tradingagents_adapter.py already uses for DeepSeek, not a
# fabricated credential.
_AI_HEDGE_FUND_ENV = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"
load_dotenv(dotenv_path=_AI_HEDGE_FUND_ENV)
if os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]

# `LLMAgent.__init__` opens a log file at a path relative to CWD
# (data/04_model_output_log/<symbol>_run.log) — real upstream behavior, not
# modified here; this adapter just ensures the directory exists under the
# vendor checkout so the real constructor doesn't crash on a missing dir.
_LOG_DIR = VENDOR_DIR / "data" / "04_model_output_log"

_ACTION_MAP = {"buy": Action.BUY, "sell": Action.SELL, "hold": Action.HOLD}

DEEPSEEK_CHAT_CONFIG = {
    # Real upstream-shaped chat config (see config/tsla_gpt_config.toml).
    # model/end_point point at DeepSeek's real OpenAI-compatible endpoint —
    # see module docstring "Q4 investigation" point 2 for why the response
    # side of this call is expected to fail regardless (ChatOpenAICompatible
    # .parse_response() only recognizes gpt/gemini-pro/tgi model-name
    # prefixes). This is left pointed at the real endpoint rather than a
    # fake one so the failure mode observed is genuine, not staged.
    "model": "deepseek-chat",
    "end_point": "https://api.deepseek.com/v1/chat/completions",
    "system_message": "You are a helpful assistant.",
}

DEFAULT_CHARACTER_STRING = (
    "You are an expert financial trading agent evaluating a single equity "
    "based on its most recent real price action and news headlines."
)


def _map_reflection_to_action(reflection: dict) -> Action:
    """Pure mapping logic, factored out for fixture-based unit testing
    without needing a real LLMAgent/BrainDB/LLM call. `reflection` is
    shaped exactly like one real `reflection_result_series_dict[date]`
    entry (agent.py:455: `{"investment_decision": ..., "summary_reason":
    ...}`)."""
    raw_decision = str(reflection.get("investment_decision", "hold")).strip().lower()
    return _ACTION_MAP.get(raw_decision, Action.HOLD)


def _ticker_from_context(context: QueryContext) -> str:
    if context.targets:
        return context.targets[0]
    if context.universe:
        return context.universe[0]
    raise ValueError(
        "finmem_adapter requires context.targets or context.universe to "
        "contain at least one ticker (this adapter is single-asset only, "
        "matching upstream Portfolio's scalar symbol design)."
    )


def _fetch_real_price_and_news(ticker: str) -> tuple[float, list[str]]:
    """Real yfinance data — same data source/pattern as fingpt_adapter.py's
    own real headline fetch. No historical replay: yfinance's news feed and
    `.history()` only expose current data, same real-world limitation
    fingpt_adapter.py/ai_hedge_fund_adapter.py already document."""
    import yfinance as yf

    tk = yf.Ticker(ticker)
    hist = tk.history(period="5d", interval="1d")
    if hist.empty:
        raise RuntimeError(f"yfinance returned no price history for {ticker}")
    price = float(hist["Close"].iloc[-1])

    items = tk.news or []
    headlines = []
    for item in items[:5]:
        title = (item.get("content") or {}).get("title")
        if title:
            headlines.append(title)
    return price, headlines


def _build_agent(ticker: str):
    """Construct the real upstream LLMAgent via its own from_config()
    classmethod — no upstream logic reimplemented, only a config dict
    assembled from real values this adapter controls (agent name, symbol,
    character string, chat config)."""
    from puppy.agent import LLMAgent

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    try:
        os.chdir(VENDOR_DIR)  # LLMAgent's log path is relative to CWD (real upstream behavior)
        config = {
            "general": {
                "agent_name": f"adapter_agent_{ticker}",
                "trading_symbol": ticker,
                "character_string": DEFAULT_CHARACTER_STRING,
                "top_k": 3,
                "look_back_window_size": 7,
            },
            "chat": dict(DEEPSEEK_CHAT_CONFIG),
            "short": {
                "importance_score_initialization": "sample",
                "decay_params": {"recency_factor": 3.0, "importance_factor": 0.92},
                "clean_up_threshold_dict": {"recency_threshold": 0.05, "importance_threshold": 5},
                "jump_threshold_upper": 60,
            },
            "mid": {
                "jump_threshold_lower": 60,
                "jump_threshold_upper": 80,
                "importance_score_initialization": "sample",
                "decay_params": {"recency_factor": 90.0, "importance_factor": 0.967},
                "clean_up_threshold_dict": {"recency_threshold": 0.05, "importance_threshold": 5},
            },
            "long": {
                "jump_threshold_lower": 80,
                "importance_score_initialization": "sample",
                "decay_params": {"recency_factor": 365.0, "importance_factor": 0.988},
                "clean_up_threshold_dict": {"recency_threshold": 0.05, "importance_threshold": 5},
            },
            "reflection": {
                "importance_score_initialization": "sample",
                "decay_params": {"recency_factor": 365.0, "importance_factor": 0.988},
                "clean_up_threshold_dict": {"recency_threshold": 0.05, "importance_threshold": 5},
            },
            "agent": {
                "agent_1": {
                    "embedding": {
                        "detail": {
                            "embedding_model": "text-embedding-ada-002",
                            "chunk_size": 5000,
                            "verbose": False,
                        }
                    }
                }
            },
        }
        return LLMAgent.from_config(config)
    finally:
        os.chdir(cwd)


class FinMemAdapter(BaseAdapter):
    name = "finmem"
    questions_answered = ["Q1"]
    upstream_repo = "https://github.com/pipiku915/FinMem-LLM-StockTrading"
    requires_env = "finmem_real"

    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        from puppy.run_type import RunMode

        ticker = _ticker_from_context(context)
        price, news = _fetch_real_price_and_news(ticker)

        try:
            cur_date = date_type.fromisoformat(context.as_of[:10])
        except ValueError:
            cur_date = date_type.today()

        agent = _build_agent(ticker)
        # market_info_type = (date, price, filing_k, filing_q, news, record, terminated)
        # No SEC filing text: this adapter has no SEC API credential (real
        # limitation, disclosed rather than fabricating filing text fed to
        # the real LLM). record=None since this is RunMode.Test (agent.py's
        # own step() only reads cur_record in Train mode).
        market_info = (cur_date, price, None, None, news, None, False)
        agent.step(market_info=market_info, run_mode=RunMode.Test)

        reflection = agent.reflection_result_series_dict.get(cur_date)
        if not reflection or "investment_decision" not in reflection:
            raise RuntimeError(
                f"FinMem LLMAgent.step() completed but produced no real "
                f"investment_decision for {cur_date} — cannot report a "
                f"fabricated action."
            )

        action = _map_reflection_to_action(reflection)
        explanation = reflection.get("summary_reason")

        return Q1Action(
            context=context,
            action=action,
            explanation=explanation,
        )

    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window: Optional[TimeWindow] = None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ) -> AdapterResult:
        return super().run(
            task_id,
            context,
            generation_window=generation_window,
            native_output=native_output,
            adapter_notes=adapter_notes,
            field_mappings=field_mappings,
            **kwargs,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        result = self.q1_action(context)
        checks["q1_returns_Q1Action"] = result is not None
        if result is not None:
            checks["action_is_valid"] = result.action in ("BUY", "SELL", "HOLD")
        return checks
