# DECISIONS_nofx.md — NoFx adapter session log

Written separately from the shared `DECISIONS.md` per instruction (another
adapter session was editing it concurrently). Same fact / **Why** /
**How to apply** style as the shared log.

---

## Target brief and literal-name search

**Fact:** the brief described "NoFx: LLM sentiment + quantitative signal, a
fusion layer that outputs a risk score," name unconfirmed. Searched GitHub
for "NoFx"/"noFX"/"NoFX" variants. Found `NoFxAiOS/nofx`
(github.com/NoFxAiOS/nofx) — confirmed real via the GitHub REST API
(`stargazers_count: 12501`, `forks_count: 3013`, `license: AGPL-3.0`,
`created_at: 2025-10-28`, `pushed_at: 2026-06-30`), not a hallucinated
citation. Description: "Your AI trading terminal assistant for US stocks,
commodities, forex, and crypto."

**Why rejected:** two independent, each-sufficient reasons:
1. Read `docs/architecture/STRATEGY_MODULE.md` and the README directly
   (not just a search summary). Setup step 2 is literally "Connect
   exchange credentials"; the strategy engine's data flow requires
   authenticated account balance/position reads
   (`Account balance -> equity, available, unrealizedPnL`,
   `Current positions -> symbol, side, entry, mark, qty, leverage`). No
   dry-run/paper/analysis-only mode is documented anywhere. This directly
   matches this session's disqualifying condition ("requires live
   brokerage/exchange account credentials... STOP and report back rather
   than wiring it up") — same class of problem as the Robinhood-credential
   rejection already logged for the DeepAlpha adapter in the shared
   `DECISIONS.md`.
2. Its AI layer is hard-routed through a proprietary paid gateway
   ("Claw402") — "Users do not need to configure model providers, manage
   API keys" — meaning the existing `DEEPSEEK_API_KEY` cannot be plugged
   in at all even setting security aside. It is also a Go binary + React
   web terminal, not a callable Python library, so there is no way to
   write a faithful thin single-function wrapper around it regardless.

**How to apply:** when a literal name match is confirmed real but fails
the security/architecture bar, document the concrete evidence (exact
quoted doc lines, not a paraphrase) and move to the closest safe
substitute rather than forcing the wrap or silently picking something
unrelated.

---

## Substitute search and choice

**Fact:** searched for open-source projects that genuinely combine an
LLM-based sentiment signal with a separate quantitative/technical signal
into one fused score. Candidates considered and rejected:
- `Ronitt272/LLM-Enhanced-Trading` — real, but a thin FinGPT + SMA/RSI-
  crossover glue script, not its own fusion architecture; substantively
  already covered by this session's existing `fingpt_adapter.py`.
- `AI4Finance-Foundation/FinGPT` itself — already wrapped by
  `fingpt_adapter.py`; CLAUDE.md's registered-adapters table disallows a
  second adapter for the same upstream project.

**Fact:** settled on `0xemmkty/QuantMuse` (github.com/0xemmkty/QuantMuse).
Confirmed real via the GitHub API: 2,707 stars, 561 forks, MIT license,
Python, `pushed_at: 2025-07-29`, single branch (`main`). Owning account
(`0xemmkty`) created 2022-03-26, 14 varied public repos, 84 followers —
checked specifically because a previous adapter this session
(`prediction_arena_adapter.py`) found a same-shaped candidate repo that
turned out to be a freshly-created content-farm account; this one does
not match that pattern.

**Why:** its `data_service/ai/llm_integration.py` (`LLMIntegration.
assess_risk()`) is a real, working fusion layer — it accepts a
`market_conditions` dict and returns one LLM-fused risk verdict
(`overall_risk`: low/medium/high, plus `risk_factors`). Paired with its
own `data_service/factors/factor_calculator.py` (real RSI/MACD/Bollinger/
momentum from real price history) and `data_service/ai/sentiment_
analyzer.py` (real per-headline LLM sentiment scoring, aggregated via its
own `calculate_market_sentiment()`), this is a genuine, verified-real
match to "LLM sentiment + quant signal -> fusion -> risk score" — closer
than any of the rejected candidates.

**How to apply:** when the literal target is disqualified, prefer a
substitute whose upstream code demonstrably implements the *same
architecture* (verified by reading source, not README prose) over one
that merely uses similar buzzwords.

---

## Security screening

**Fact:** no live brokerage/exchange credentials, real money, or funded
account of any kind appears anywhere in the three upstream modules this
adapter imports (`sentiment_analyzer.py`, `llm_integration.py`,
`factor_calculator.py`) or their package `__init__` import chains.
Upstream's own `setup.py` lists `python-binance` as a core dependency
(used by unrelated live-data fetchers elsewhere in the repo,
`data_service/fetchers/`), but this adapter never imports that path, and
`python-binance` is not even installed in `nofx_real` — the adapter runs
and passes the harness without it, proving the import chain used is
clean. No unrelated merged subtree under a misleadingly-named branch
(repo has exactly one branch). No `eval`/`exec`/`shell=True` in the
modules used.

**Fact (minor, non-disqualifying):** the repo root contains a stray
`test.cpp` (a literal "Hello, C++ is working!" toolchain smoke test) and a
compiled `test.exe` (44KB, valid `MZ`/PE header, size consistent with that
trivial program) — checked because a random top-level binary in a Python
repo warranted a look. Sloppy dev-machine hygiene, not a hidden payload.
This adapter never references either file.

**Why:** matches this session's standing security-screening bar (the
FinGPT unrelated-subtree finding and the DeepAlpha brokerage-credential
finding both set the precedent that every new adapter's upstream gets
checked for these specific patterns before wrapping).

---

## Environment / dependencies

**Fact:** new dedicated conda env `nofx_real` (python 3.11), not shared
with any other adapter. Installed `pandas numpy requests python-dotenv
yfinance pydantic "openai==0.28.1" matplotlib seaborn scipy`. All from
prebuilt wheels — no cmake/Rust build failures this time.

**Why `openai==0.28.1` specifically:** upstream's `OpenAIProvider` and
`SentimentAnalyzer._analyze_with_openai()` both call the pre-1.0
`openai.ChatCompletion.create(...)` / module-level `openai.api_key` /
`openai.api_base` API. Modern `openai>=1.0` removes `openai.ChatCompletion`
at the top level entirely (raises its own migration error immediately).
Same "pin to the vintage the vendor code was written against" lesson
already logged for `fingpt_adapter.py`'s transformers/peft/accelerate pin.

**Why matplotlib/seaborn/scipy:** importing just `factor_calculator.py`
still executes `data_service/factors/__init__.py`, which eagerly imports
sibling modules (`factor_backtest.py` needs matplotlib+seaborn,
`factor_optimizer.py` needs scipy) even though this adapter never calls
those classes. Installing the real (free, no license/build cost)
dependencies was simpler and more honest than patching upstream's
`__init__.py` just to silence an eager import — unlike the FinRL/FinRL-X
cases where the eager import required a *paid or live-brokerage* SDK,
here it's just ordinary plotting/optimization libraries.

**How to apply:** free/ordinary transitive deps triggered by package
`__init__.py` eager imports → just install them; reserve
patch-to-suppress-an-eager-import for cases where the transitive
dependency itself is disqualifying (paid vendor, live brokerage SDK), as
`finrl_adapter.py`/`finrl_x_adapter.py` did.

---

## Patch applied (`patches/QuantMuse.diff`)

**Fact:** `SentimentAnalyzer._analyze_with_openai()` hardcoded
`model="gpt-3.5-turbo"` with no constructor override, confirmed by a real
failed call against DeepSeek's OpenAI-compatible endpoint: *"The supported
API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed
gpt-3.5-turbo."* (`LLMIntegration`'s own `OpenAIProvider` already accepts
a `model` constructor arg and needed no patch.)

**Why patched instead of worked around:** the alternative to patching
would have been reimplementing the sentiment-analysis prompt in this
adapter's own code to call the LLM directly — which is exactly the
"reimplementing upstream's own logic" anti-pattern CLAUDE.md calls out.
A two-line patch (add an `openai_model` constructor parameter, default
unchanged; use it instead of the hardcoded literal) is smaller and more
honest than that.

**How to apply:** added `openai_model: str = "gpt-3.5-turbo"` to
`SentimentAnalyzer.__init__`, stored as `self.openai_model`, used at the
one `ChatCompletion.create(model=...)` call site. Full diff in
`patches/QuantMuse.diff`. No other upstream file touched.

---

## DeepSeek model name — verified empirically, not from memory

**Fact:** did not assume "deepseek-chat" (the commonly-known DeepSeek
model string) was correct. The first real test call against
`https://api.deepseek.com/v1` with a wrong/placeholder model name failed
with an error that named the two actually-supported strings for this
account: `deepseek-v4-pro` / `deepseek-v4-flash`. Used
`deepseek-v4-flash` (matches the "quick_think" tier choice
`tradingagents_adapter.py` made for its own equivalent calls, per the
shared `DECISIONS.md`).

**Why:** this session's own history includes a web-search summary that
hallucinated a plausible-looking GitHub citation; the same caution
(verify against the live system, don't trust remembered/assumed strings)
applies to model names.

---

## Cost-control / balance-exhaustion handling

**Fact:** upstream's own `_analyze_with_openai()` and `assess_risk()` both
catch every exception internally and silently fall back to a
local/default result rather than raising — which would mask a real
auth/balance failure as an innocuous low-confidence "neutral sentiment"
data point instead of surfacing it. Addressed by attaching a temporary
`logging.Handler` to upstream's own `data_service.ai.sentiment_analyzer`
and `data_service.ai.llm_integration` loggers around each real call and
scanning captured ERROR records for auth/quota-shaped substrings; raises
`RuntimeError("DeepSeek API balance may be exhausted...")` if found,
instead of silently returning degraded output.

**Fact:** no such error was ever triggered in this session — `DEEPSEEK_API_KEY`
loaded correctly (confirmed non-empty in-process via `load_dotenv` before
any upstream call, checked deliberately given this session's earlier
"looked like a balance error, was actually a missing `load_dotenv()` call"
bug logged for a different adapter) and all real DeepSeek calls succeeded.

---

## Harness result

**Fact:** `python CONTRACT/test_harness.py --adapter adapters/nofx_adapter.py`
(env `nofx_real` active) → **19/19 checks passed, ALL PASS.** Smoke test
completes in ~27-29s (3 real per-headline DeepSeek sentiment calls + 1
real DeepSeek fusion `assess_risk()` call + yfinance price/news fetch),
full `run()` in ~21-30s — comfortably inside both budgets.

**Sample real output** (NVDA, not part of the harness, run manually for a
sanity check): real technical factors showed bearish signals (MACD
negative, price below 20/50-day MAs, RSI 40.4) while real headline
sentiment was net positive (0.51) — the fusion layer correctly flagged
`risk_level=HIGH` driven by the technical divergence, with `risk_factors`
naming the specific bearish indicators. This is the kind of
sentiment-vs-technicals disagreement the fusion architecture is meant to
surface, working end-to-end on real data.
