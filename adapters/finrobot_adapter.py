"""
adapters/finrobot_adapter.py — wraps github.com/AI4Finance-Foundation/FinRobot (Q2, best-effort Q1).

New-adapter integration pass (2026-07). Batch C of the candidate-adapter
roster in the active task brief.

============================================================================
Central finding this adapter is built around
============================================================================
FinRobot is an AutoGen (`pyautogen`) multi-agent tool-calling framework, not
a single pipeline. Its own `SingleAssistant.chat()` wrapper
(finrobot/agents/workflow.py:125-165, read directly) calls
`self.user_proxy.initiate_chat(self.assistant, message=message, ...)` and
returns nothing (implicit `None`) — the real `autogen.ChatResult` that
`initiate_chat()` returns is discarded by FinRobot's own wrapper code.

This looked, at first read, like it would make the model's real output
entirely uncapturable through any public interface. **Verified empirically
(this session, in two rounds) that it is not, but the first fix attempt was
itself wrong and had to be corrected via a live-run failure:**

  - Round 1 (wrong): confirmed `ConversableAgent.initiate_chat()` populates
    `self.chat_messages[recipient]` as a side effect, independent of the
    caller's use of the return value — true, and demonstrated with an
    isolated 2-message "Say OK" test. The draft adapter then called the
    real, unmodified `SingleAssistant.chat()` wrapper and read
    `chat_messages` *afterward*. A live CLI run then produced an empty
    `full_reply`/`messages` despite real, visible conversation output on
    screen — a real bug, not a flake.
  - Root cause (confirmed by reading `finrobot/agents/workflow.py:158-164`
    and `autogen.ConversableAgent.reset()`'s source directly):
    `SingleAssistant.chat()` itself calls `self.reset()` right before
    returning (`print("Current chat finished. Resetting agents ...");
    self.reset()` — real, unmodified upstream code), and `reset()` calls
    `self.clear_history()`, which empties `chat_messages`. The isolated
    "Say OK" test never called `SingleAssistant.chat()`'s wrapper, only the
    raw `initiate_chat()`, so it never hit this reset and looked correct in
    isolation — a real gap between an isolated unit check and the actual
    integrated call path, only surfaced by the live CLI run.
  - Round 2 (fix, verified working): call
    `single.user_proxy.initiate_chat(single.assistant, message=message,
    max_turns=6, silent=False)` **directly**, using the exact same real
    `user_proxy`/`assistant` objects `SingleAssistant.__init__` already
    built (same LLM config, same registered toolkits, same profile) —
    still 100% real, public, unmodified autogen API, just skipping the one
    wrapper method that self-resets before returning. Extract from the
    real, public `ChatResult.chat_history` (confirmed via
    `inspect.signature(ConversableAgent.initiate_chat) -> ChatResult`),
    falling back to `chat_messages` (both real at this point, since
    extraction now happens before any reset). `single.reset()` is still
    called afterward, for hygiene, but only after extraction. Re-verified
    live: a real MSFT run's `native_output.full_reply`/`messages` now
    contain the full real multi-paragraph analysis and the model's own
    real "bullish" conclusion, matching the visible console transcript.

No bypass of real chat logic, no monkey-patch, no fabrication — only a
correction of which real, public method to call, driven by an actual
observed live-run failure rather than assumed to work from an isolated
check.

============================================================================
Environment / dependency note
============================================================================
The `pyautogen` PyPI package was renamed: the current release (0.10.0 as of
this writing) is a thin proxy over the newer `autogen-agentchat`/
`autogen-core` packages and does NOT provide the classic `import autogen`
namespace this repo's code (`from autogen import ...`) requires. Pin
`pyautogen==0.2.35` (still in the classic-namespace era, compatible with
this repo's own `requirements.txt: pyautogen>=0.2.19`) instead of latest.
That version's own `tiktoken` pin has no prebuilt wheel for this platform
without a Rust compiler (not installed here); pinning `tiktoken<0.12`
first (same fix `prediction_arena_adapter.py` already uses in this repo)
resolves it before installing pyautogen.

Environment setup (one-time, outside this file):
    conda create -n finrobot_real python=3.11
    conda activate finrobot_real
    pip install "tiktoken<0.12"
    pip install "pyautogen==0.2.35" yfinance python-dotenv pandas numpy pydantic
    pip install finnhub-python sec_api praw mplfinance backtrader reportlab \
        ipython matplotlib chromadb
    # Real, unmodified upstream import-time coupling, discovered empirically
    # this session: importing finrobot.agents.workflow (needed for the real
    # SingleAssistant class) triggers `finrobot.agents.agent_library` ->
    # `from finrobot.data_source import *` (real, eagerly imports
    # FinnHubUtils/YFinanceUtils/FMPUtils/SECUtils/RedditUtils regardless of
    # which one you actually use) AND `from finrobot.functional import *`
    # (real, eagerly imports mplfinance/backtrader-based/reportlab-based/
    # IPython-based/RAG(chromadb-based) utility classes the same way). This
    # adapter only ever calls 3 real YFinanceUtils methods — everything
    # else above is required purely to satisfy real, unmodified upstream
    # import statements, not because this adapter uses those capabilities.
    # None of the extra packages need an API key or network call just to be
    # importable; none of their real API-calling methods are ever invoked
    # by this adapter.

Run the harness with that env active:
    conda activate finrobot_real
    python CONTRACT/adapter_runner.py --adapter adapters/finrobot_adapter.py \
        --task-id smoke --as-of 2024-01-15 --scope ASSET --target AAPL --universe AAPL

No upstream source was patched.

============================================================================
Scope choice (deliberate, disclosed)
============================================================================
FinRobot ships several persona configs in `finrobot/agents/agent_library.py`
(`library` dict). Two candidates were considered for a single, well-scoped,
honestly-achievable use case (per the task brief's explicit instruction not
to try to cover the whole framework's many possible configs):
  - `Expert_Investor`: needs `FMPUtils.get_sec_report` (a Financial
    Modeling Prep API key not provisioned in this project) plus heavy
    ReportLab PDF-building tooling — rejected as out of scope for a thin,
    keyless-data adapter.
  - `Market_Analyst` (agent_library.py, real, unmodified profile text):
    ships with `[FinnHubUtils.get_company_profile, FinnHubUtils.
    get_company_news, FinnHubUtils.get_basic_financials, YFinanceUtils.
    get_stock_data]` — the first three need a FinnHub API key (also not
    provisioned). **This adapter passes its own trimmed toolkit list**
    (`YFinanceUtils.get_stock_data`, `.get_stock_info`, `.get_company_info`
    — all real, confirmed keyless, `finrobot/data_source/yfinance_utils.py`)
    when constructing the `SingleAssistant`. This is a legitimate
    adapter-side configuration choice (which real, already-defined toolkit
    functions to hand the real, unmodified `SingleAssistant`/`FinRobot`
    class), not a modification of `agent_library.py` or the persona's own
    profile text (which is used completely verbatim).

Q1-vs-Q2 honesty: `Market_Analyst`'s own real profile text
(agent_library.py) asks it to "collect necessary financial information and
aggregate them" — an analysis/state task, not a request for a BUY/SELL/HOLD
call. This adapter's own user-turn message (not a persona/profile edit —
the same kind of real, task-specific query every other LLM-driving adapter
in this repo constructs, e.g. `tradingagents_adapter.py`'s real prompts)
explicitly asks for a bullish/bearish/neutral outlook so the real answer is
extractable, but the resulting BUY/SELL/HOLD mapping is inherently a
**DERIVED**, disclosed, best-effort keyword extraction over free-form LLM
prose (FinRobot has no deterministic structured-output header format the
way e.g. TradingAgents' real Pydantic schemas do) — never claimed NATIVE.
If no clear keyword is found, Q1 is left `None` rather than defaulting to
HOLD (defaulting would fabricate a decision the model didn't actually make).
Q2 (`StateEstimate(dimension="market_outlook", value_text=<the real full
reply>)`) is the honestly-NATIVE capability — the model's real analysis
text, verbatim, is always captured when the call succeeds.

Not integrated this pass (disclosed, not a gap): the "Trade_Strategist"
demo elsewhere in this repo generates and writes a real BackTrader
strategy-code file to disk — a real, separate, `PolicyArtifact`-shaped
capability, but a different real use case from the single-ticker analysis
flow this adapter focuses on; left as a documented, not-yet-integrated
capability rather than bolted on to keep this adapter narrowly scoped and
fully tested, per the task brief's explicit instruction.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    EvidenceItem,
    OutputScope,
    Q1Action,
    Q2State,
    QueryContext,
    StateEstimate,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "FinRobot"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Reuse the existing DeepSeek key (adapters/vendor/ai-hedge-fund/.env) rather
# than requiring a new one — same key ai_hedge_fund_adapter.py/
# tradingagents_adapter.py/finagent_adapter.py already use.
_AI_HEDGE_FUND_ENV = Path(__file__).resolve().parent / "vendor" / "ai-hedge-fund" / ".env"
load_dotenv(dotenv_path=_AI_HEDGE_FUND_ENV)

COMP_MODEL = "deepseek-chat"

# Real, unmodified Market_Analyst profile text, copied verbatim from
# finrobot/agents/agent_library.py at import time (not hand-retyped) so any
# real upstream wording change is picked up automatically.
_MARKET_ANALYST_PROFILE: Optional[str] = None


def _market_analyst_profile() -> str:
    global _MARKET_ANALYST_PROFILE
    if _MARKET_ANALYST_PROFILE is None:
        from finrobot.agents.agent_library import library

        _MARKET_ANALYST_PROFILE = library["Market_Analyst"]["profile"]
    return _MARKET_ANALYST_PROFILE


_OUTLOOK_RE = re.compile(r"\b(bullish|bearish|neutral)\b", re.IGNORECASE)


def _run_market_analyst(ticker: str, as_of: str) -> dict:
    """
    Real, unmodified finrobot.agents.workflow.SingleAssistant call, driving
    the real Market_Analyst persona with a real, keyless yfinance-only
    toolkit subset (see module header for why FinnHub-dependent tools are
    dropped). Returns the real captured chat_messages exchange.
    """
    import autogen

    from finrobot.agents.workflow import SingleAssistant
    from finrobot.data_source.yfinance_utils import YFinanceUtils

    llm_config = {
        "config_list": [
            {
                "model": COMP_MODEL,
                "api_key": _deepseek_key(),
                "base_url": "https://api.deepseek.com",
            }
        ],
        "temperature": 0.2,
        "timeout": 120,
    }

    agent_config = {
        "name": "Market_Analyst",
        "profile": _market_analyst_profile(),
        # Real, keyless yfinance-only toolkit subset — see module header.
        "toolkits": [
            YFinanceUtils.get_stock_data,
            YFinanceUtils.get_stock_info,
            YFinanceUtils.get_company_info,
        ],
    }

    single = SingleAssistant(
        agent_config,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config={"use_docker": False, "work_dir": "coding"},
    )

    # This adapter's own task-specific user-turn message — a real query, not
    # a persona/profile edit (see module header, "Q1-vs-Q2 honesty").
    message = (
        f"Using the get_stock_data / get_stock_info / get_company_info "
        f"tools, analyze {ticker} as of {as_of}. Summarize the recent price "
        f"action and company fundamentals, then state your outlook using "
        f"exactly one of the words bullish, bearish, or neutral. "
        f"Reply TERMINATE when done."
    )

    # IMPORTANT, discovered empirically this session (corrected from an
    # earlier draft): `SingleAssistant.chat()` itself calls `self.reset()`
    # right before returning (finrobot/agents/workflow.py:158-164, real,
    # unmodified upstream code — confirmed via a live run printing "Current
    # chat finished. Resetting agents ..."), and `ConversableAgent.reset()`
    # calls `self.clear_history()`, which empties `chat_messages`. So
    # calling `single.chat(message)` and THEN reading `chat_messages`
    # reads state that upstream's own wrapper already wiped — verified by
    # a live run where this returned 0 messages despite real, visible
    # conversation output on screen. Fix: call the same real, public,
    # unmodified `user_proxy.initiate_chat(assistant, ...)` method
    # `SingleAssistant.chat()` itself calls internally, directly — this
    # skips only the wrapper's own post-hoc reset, not any real chat logic.
    # Still the exact same real agents `SingleAssistant.__init__` built
    # (same LLM config, same registered toolkits, same profile).
    chat_result = single.user_proxy.initiate_chat(
        single.assistant,
        message=message,
        max_turns=6,
        silent=False,
    )

    # Real, public ChatResult.chat_history (confirmed via
    # inspect.signature(ConversableAgent.initiate_chat) -> "-> ChatResult"),
    # captured before any reset. chat_messages (still real, still populated
    # at this point since reset() hasn't run) is read too as a
    # cross-check/fallback.
    messages = list(getattr(chat_result, "chat_history", None) or [])
    if not messages:
        messages = single.user_proxy.chat_messages.get(single.assistant, [])
    real_texts = [
        m.get("content", "") for m in messages if m.get("role") == "user" and m.get("content")
    ]
    full_reply = "\n\n".join(t for t in real_texts if t.strip() and t.strip() != "TERMINATE")

    # Real cleanup, now safe since extraction already happened.
    single.reset()

    return {
        "ticker": ticker,
        "as_of": as_of,
        "messages": messages,
        "full_reply": full_reply,
    }


def _deepseek_key() -> str:
    import os

    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. It should already exist at "
            "adapters/vendor/ai-hedge-fund/.env (shared with several other "
            "adapters in this repo) — never hardcode it here."
        )
    return key


class FinRobotAdapter(BaseAdapter):
    name = "finrobot"
    questions_answered = ["Q1", "Q2"]
    upstream_repo = "https://github.com/AI4Finance-Foundation/FinRobot"
    requires_env = "finrobot_real"

    def __init__(self):
        super().__init__()
        self._cache: dict[tuple[str, str], dict] = {}

    def _run(self, ticker: str, as_of: str) -> dict:
        key = (ticker, as_of)
        if key in self._cache:
            return self._cache[key]
        result = _run_market_analyst(ticker, as_of)
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Q2 — market_outlook state (NATIVE: the model's own real reply text)
    # ------------------------------------------------------------------
    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        if not context.targets:
            raise ValueError("finrobot q2_state requires context.targets == [ticker]")
        ticker = context.targets[0]
        raw = self._run(ticker, context.as_of)

        if not raw["full_reply"]:
            return Q2State(
                context=context,
                states=[
                    StateEstimate(
                        dimension="market_outlook",
                        value_category="no_reply_captured",
                        confidence=ConfidenceEstimate(
                            value=0.0,
                            kind=ConfidenceKind.HEURISTIC,
                            method="no real reply captured from chat_messages this call",
                        ),
                    )
                ],
                explanation="Market_Analyst produced no capturable reply this call.",
            )

        state = StateEstimate(
            dimension="market_outlook",
            value_text=raw["full_reply"],
            scale="free-form real Market_Analyst analysis text",
            evidence=[
                EvidenceItem(
                    kind="llm_conversation",
                    value=f"{len(raw['messages'])} real messages captured via chat_messages",
                    source="finrobot.agents.workflow.SingleAssistant + real DeepSeek call (deepseek-chat)",
                )
            ],
        )

        return Q2State(
            context=context,
            states=[state],
            explanation=raw["full_reply"][:2000],
        )

    # ------------------------------------------------------------------
    # Q1 — best-effort DERIVED bullish/bearish/neutral -> BUY/SELL/HOLD
    # ------------------------------------------------------------------
    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        if not context.targets:
            raise ValueError("finrobot q1_action requires context.targets == [ticker]")
        ticker = context.targets[0]
        raw = self._run(ticker, context.as_of)

        if not raw["full_reply"]:
            return None

        m = _OUTLOOK_RE.search(raw["full_reply"])
        if not m:
            # Real reply captured, but no extractable directional keyword —
            # leave Q1 unclaimed rather than defaulting to HOLD (that would
            # fabricate a decision the model didn't actually state).
            return None

        outlook = m.group(1).lower()
        action = {"bullish": Action.BUY, "bearish": Action.SELL, "neutral": Action.HOLD}[outlook]

        return Q1Action(
            context=context,
            action=action,
            action_semantics=(
                f"DERIVED via keyword extraction over Market_Analyst's real free-form reply "
                f"(matched '{outlook}') — FinRobot has no deterministic structured-output format "
                f"for this persona, unlike e.g. TradingAgents' real Pydantic schemas."
            ),
            confidence=None,  # no honest numeric confidence available from free-form prose
            explanation=raw["full_reply"][:2000],
            evidence=[
                EvidenceItem(
                    kind="keyword_extraction",
                    value=f"matched outlook keyword: {outlook}",
                    source="adapter-side regex over real Market_Analyst reply (DERIVED, not native)",
                )
            ],
        )

    # ------------------------------------------------------------------
    # run() override — attach faithful native_output, reusing the same
    # cached real chat exchange q1_action()/q2_state() will use.
    # ------------------------------------------------------------------
    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window=None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ) -> AdapterResult:
        if native_output is None and context.targets:
            ticker = context.targets[0]
            raw = self._run(ticker, context.as_of)
            native_output = {
                "ticker": raw["ticker"],
                "as_of": raw["as_of"],
                "full_reply": raw["full_reply"],
                "messages": raw["messages"],
            }
        return super().run(
            task_id,
            context,
            generation_window=generation_window,
            native_output=native_output,
            adapter_notes=adapter_notes,
            field_mappings=field_mappings,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Smoke test (real call — one real DeepSeek-driven Market_Analyst run)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()

        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )

        q2 = self.q2_state(context)
        checks["q2_returns_Q2State"] = q2 is not None
        checks["q2_states_nonempty"] = q2 is not None and len(q2.states) >= 1
        outlook_state = next((s for s in q2.states if s.dimension == "market_outlook"), None) if q2 else None
        checks["q2_market_outlook_present"] = outlook_state is not None
        checks["q2_context_echoed"] = q2 is not None and q2.context == context

        # Same cached call — no second real LLM invocation.
        q1 = self.q1_action(context)
        checks["q1_action_none_or_valid"] = q1 is None or q1.action in ("BUY", "SELL", "HOLD")

        return checks
