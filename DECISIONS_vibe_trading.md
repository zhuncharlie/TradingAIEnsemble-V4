# DECISIONS_vibe_trading.md — autonomous decisions log (Vibe-Trading adapter)

Written separately from the shared `DECISIONS.md` per this session's
instructions (a concurrent FinClaw-adapter session is editing the shared
file right now; merge later). Same fact / **Why:** / **How to apply:** style.

---

## 2026-07-04 — Vibe-Trading adapter (Q3 + Q4 + Q5) — 25/25 harness pass

**All three questions in the brief (Q3, Q4, Q5) were implemented** —
`questions_answered = ["Q3", "Q4", "Q5"]`.

### Repo search process (target NOT confirmed to exist going in)

The session brief explicitly flagged "Vibe-Trading" as unconfirmed — "search
for 'Vibe-Trading' ... natural-language strategy generation + multi-market
backtesting system with a CompositeEngine". WebSearch for "Vibe-Trading
github natural language strategy generation CompositeEngine" and "Vibe
Trading github LLM strategy generation multi-market backtest composite
engine" surfaced several repos literally named `vibe-trading`/`Vibe-Trading`.
Every candidate was checked via the GitHub REST API directly (not just
trusted from the search snippet), per this session's standing rule that a
web search once fabricated a plausible-looking GitHub citation:

| Repo | Stars/forks | Created / pushed | Verdict |
|---|---|---|---|
| `HKUDS/Vibe-Trading` | 17,724 / 2,924 | 2026-04-01 / 2026-07-04 (actively maintained) | **Chosen** |
| `vibe-trading-agent/vibe-trading` | 1 / 0 | 2026-06-15 | Rejected — tagline "Download Vibe-Trading: Your Personal Trading Agent." matches the classic fake-repo/malware-distribution phrasing pattern; near-zero stars, no independent content, rides the real project's name |
| `kkwangRocks/vibe-trading` | 0 / 0 | 2026-06-16 | Rejected — GitHub API confirms `"fork": true` of `HKUDS/Vibe-Trading` itself, not an independent implementation |
| `VibeTradingLabs/vibetrading` | 55 / 10 | 2026-02-20 / 2026-03-23 (stale) | Real, on-topic, but far smaller/earlier and not where the brief's exact "CompositeEngine" phrase traces to; not needed once HKUDS's repo was confirmed |
| `spyderweb47/Vibe-Trade` | 9 / 1 | 2026-04-01 | Real but a much smaller single-author Next.js/pattern-detection tool, not a strategy-generation + multi-market-backtest platform |
| `Markjinli/Vibe-Trading-Chinese` | 0 / 0 | 2026-05-11 | Chinese-localized fork/mirror, not independent |

`HKUDS` ("✨Data Intelligence Lab@HKU✨") is a long-running real research org
(created 2022, 91 public repos, several other high-star projects —
`OpenHarness` 14.5k stars, `OpenSpace` 6.6k, `ClawTeam` 5.3k) — not a fresh
throwaway account minted to squat on a trending name.

**Verified by reading actual source, not just the README** (this session's
standing rule, after finding README-vs-code mismatches in other adapters):
- `agent/backtest/engines/composite.py` — `CompositeEngine` is a real,
  executable cross-market engine with a shared capital pool and per-market
  "rule-provider" sub-engines (`ChinaAEngine`, `GlobalEquityEngine`,
  `CryptoEngine`, `ForexEngine`, `ChinaFuturesEngine`, `GlobalFuturesEngine`).
- `agent/backtest/runner.py`'s `_create_market_engine()` auto-routes to
  `CompositeEngine` whenever `len({_detect_market(c) for c in codes}) > 1` —
  confirmed by actually running it with `["AAPL.US", "BTC-USDT"]` and
  observing the composite run (positions.csv correctly splits weight
  0.535/0.465 between the two real markets).
- `agent/src/skills/strategy-generate/SKILL.md` (the real natural-language
  strategy authoring guide the framework's own agent loop uses) +
  `agent/src/providers/llm.py`'s real `build_llm()` factory are the real
  NL-strategy-generation machinery — an LLM is prompted with this exact
  skill guide to write a `SignalEngine` class matching the runner's
  contract.

No case arose here of needing to assemble the three Q's from more than one
repo — one real, verified project covered all three.

### Security screening

- `grep -rniE "eval\(|exec\(|os\.system|shell=True|subprocess\.(call|run|Popen)"`
  across `agent/backtest/`, `agent/src/providers/`, `agent/src/shadow_account/`,
  `agent/src/skills/strategy-generate/`, `agent/src/skills/cross-market-strategy/`
  — zero hits (the one `ast.literal_eval` hit in `shadow_account/codegen.py`
  is upstream's own safe-literal renderer).
- File tree (`agent/backtest`, `agent/src/{agent,api,channels,config,core,
  factors,goal,hypotheses,live,providers,shadow_account,skills,swarm,tools}`,
  top-level `frontend/`, `wiki/`, `tools/`, `scripts/`) is entirely on-topic
  for a finance research agent + web UI + docs. No unrelated subtree merged
  under a misleading name (the FinGPT-session pattern this project
  explicitly checks for every time).
- `agent/src/live/` (mandate/enforcement/order_guard — real live-order
  execution governance) exists in the repo but this adapter's code path
  never imports it. Only `backtest.*` (paper/historical simulation) and
  `src.providers.llm` (LLM factory) are used. **No brokerage/exchange
  account, live order routing, or real money anywhere in this adapter's
  code path** — the same disqualifying pattern DeepAlpha/NoFx/ATLAS hit and
  rejected elsewhere in this session simply doesn't apply here; Vibe-Trading
  the *upstream project* has a live-trading layer, but it's fully separable
  from the backtest/research layer this adapter wraps, and the adapter never
  touches it.
- Data sources: only `agent/backtest/loaders/yfinance_loader.py` (US/HK
  equities, free, no key) and `agent/backtest/loaders/okx.py` ("OKX V5
  public REST API (no auth)", `requires_auth = False`) are reached by this
  adapter's `source="auto"` routing. China A-shares (`tushare`, needs a free
  token) and premium loaders (`fmp`/`finnhub`/`alphavantage`/`tiingo`) and
  the broker-login `futu` loader are never used.
- The one credential this adapter reads is `DEEPSEEK_API_KEY` (Q3's single
  real LLM call), from the already-existing `adapters/vendor/ai-hedge-fund/.env`
  — no separate or fabricated key requested, per this session's convention.

### Real bug found in upstream's own bundled example

`agent/src/skills/cross-market-strategy/example_signal_engine.py` — the
exact reference implementation upstream ships for the CompositeEngine use
case this adapter needs — **fails upstream's own runtime security
validator**. Found by actually *running* it (not just reading it):

```
{"error": "SignalEngine source error: Executable top-level statement Assign is not allowed"}
```

Root cause: `backtest/runner.py`'s `_validate_signal_engine_source()` walks
the AST and only allows top-level assignments whose value is a pure literal
(`_is_literal_node`: constants, and lists/dicts/tuples/sets built only from
constants). The example's `_MARKET_PATTERNS = [(re.compile(r"..."), "a_share"), ...]`
list contains `re.compile()` `Call` nodes, which are not literal — so
upstream's own shipped reference file cannot pass upstream's own gate.

**Why:** this looks like upstream added the AST-based import-time-execution
guard after (or without re-testing against) this particular example file —
a real, reproducible inconsistency between two parts of the same upstream
repo, not a environment/sandbox artifact.

**How to apply:** `CROSS_MARKET_SIGNAL_ENGINE_SOURCE` in
`adapters/vibe_trading_adapter.py` is upstream's own example, byte-for-byte
identical in strategy logic (same `MARKET_PARAMS` table, same
inverse-volatility weighting formula in `_vol_adjust`), with only the
market-detection step changed to call upstream's own already-imported
`backtest.engines._market_hooks._detect_market` (the same single source of
truth `CompositeEngine` itself uses internally) instead of re-deriving a
second, import-time-unsafe regex table. This is **not a patch to vendor
source** — the vendored clone is completely untouched; it is this adapter's
own `code/signal_engine.py` input file, adapted from upstream's broken
example so it actually passes upstream's own real validator. No
`patches/Vibe-Trading.diff` was needed as a result.

A second, related real bug was hit during development: DeepSeek's
LLM-generated `SignalEngine` (Q3) occasionally adds an
`__init__(self, config)` with no default value, which fails upstream's own
`_validate_signal_engine_class()` ("SignalEngine.__init__() has required
arguments ['config']"). This is expected LLM nondeterminism, not an upstream
bug — the skill guide doesn't loudly enough state the no-required-args
constraint. **Fix applied:** the adapter now (1) states the constraint
explicitly in the system prompt, (2) runs upstream's own
`_validate_signal_engine_source` *and* `_validate_signal_engine_class`
in-process (dynamically importing the generated module) before ever
spending a real subprocess/backtest call, and (3) retries the DeepSeek call
exactly once, feeding the real validator's own error message back to the
model, before giving up for real. Confirmed stable across two consecutive
full harness runs after the fix (25/25 both times).

### Dependency / environment notes

- New env: `conda create -n vibe_trading_real python=3.11` (dedicated, not
  shared with any other adapter).
- `tiktoken` (a `langchain-openai` transitive dependency) has no prebuilt
  wheel for this platform/Python combo and needs a Rust toolchain to build
  from source (same class of failure `ai_hedge_fund_adapter.py` hit
  earlier this session). Fixed the same way: `conda install -c conda-forge
  tiktoken` (precompiled binary) instead of fighting the source build.
- `fastmcp>=2.14.0` is required even though this adapter never touches the
  multi-agent swarm feature: `backtest/runner.py`'s own `safe_run_dir()`
  unconditionally imports `src.swarm.store` (for its default run-root list),
  which imports `src.tools.mcp`, which imports `fastmcp`. A real, if
  slightly surprising, transitive-import chain in upstream's own code — not
  worked around, just installed.
- Full package list: `pandas numpy scipy pydantic requests yfinance
  defusedxml pyyaml python-dotenv fastmcp langchain(<2) langchain-core(<2)
  langchain-openai(<2)`. Notably NOT installed: `tushare`, `akshare`,
  `ccxt`, `weasyprint`, `matplotlib`, `duckdb`, `smartmoneyconcepts`,
  `python-pptx`/`python-docx`/`pypdfium2` — none of upstream's own
  `agent/requirements.txt` entries for China-A-share data, PDF/report
  generation, or document-reading tools are reached by this adapter's three
  q*() methods, so none were installed (smaller, faster env; harness green
  without them, proof the import path used is clean).
- `git clone --depth 1 https://github.com/HKUDS/Vibe-Trading.git
  adapters/vendor/Vibe-Trading` — first clone attempt was killed by the
  bash tool's 2-minute timeout mid-transfer and left a corrupted git index
  (`git status` showed every tracked file staged as deleted). Re-cloned
  clean into the same path as a backgrounded process instead of foreground;
  second clone completed successfully (1649 files, 255 dirs, clean
  `git status`).

### Design / scope-reduction choices

- **Q5 built first, then Q4, then Q3**, per the brief's own sequencing.
- **Deterministic strategy for Q4/Q5; exactly one real LLM call site for
  Q3.** Q4/Q5 always run the fixed, adapted `CROSS_MARKET_SIGNAL_ENGINE_SOURCE`
  (no LLM) — fast, free, and it exercises the real `CompositeEngine`/backtest
  pipeline end-to-end every time. Q3 is the only place a real DeepSeek call
  happens, via upstream's own `build_llm()` + `strategy-generate` skill
  guide, producing a fresh `SignalEngine` validated by upstream's own AST
  gate and then executed through the same real backtest pipeline.
- **Why not drive the full autonomous `AgentLoop`**: upstream's real
  multi-turn ReAct loop (`agent/src/agent/loop.py`, 1500+ lines — heartbeats,
  goal/memory management, tool-call orchestration across `write_file`,
  `backtest`, `edit_file`, etc.) is real, working code, and is the "true"
  end-to-end natural-language-to-strategy experience. It was deliberately
  not driven end-to-end here: it has an unbounded LLM turn count (the model
  decides how many tool calls/iterations to take), which doesn't fit
  cleanly into the harness's fixed `smoke_test()` (<300s) / `run()` (<600s)
  budgets or this session's cost-control convention of a small, bounded
  number of real LLM calls per adapter invocation. Calling `build_llm()` +
  the real skill-guide prompt + the real AST validator + the real backtest
  runner directly reaches the same underlying primitives the loop uses,
  without the open-ended orchestration risk — the same class of scope
  reduction every other adapter this session applied to its own upstream's
  heaviest pipeline (reduced GA populations, reduced DRL timesteps, single
  point-in-time instead of continuous, etc).
- **Cross-market anchor**: CONTRACT's own sample tickers (`AAPL`, `MSFT`,
  `NVDA`) are all single-market (US equities) and would route to upstream's
  single-market `GlobalEquityEngine`, never exercising `CompositeEngine` —
  the exact feature the brief singles out for Q4. The adapter appends a
  fixed `BTC-USDT` anchor code whenever the requested tickers don't already
  span more than one real upstream-detected market (checked via upstream's
  own `_detect_market`), so `CompositeEngine` is genuinely exercised on
  every call. This is disclosed in `Q4Portfolio.rationale` whenever it
  fires, not hidden.
- **Q4 weight translation**: upstream's own `positions.csv` records each
  symbol's *standalone* target signal in `[-1, 1]` (per upstream's own skill
  guide: "1.0 = fully long ... 0.0 = flat"), which is not CONTRACT's
  `Q4Portfolio.weights` convention (non-negative, sum ≤ 1.0 across the whole
  book). The adapter clips negative/short targets to 0 (long-only), and
  renormalizes down to sum ≤ 1.0 only if raw long exposure exceeds 1.0,
  reporting the remainder as `cash_ratio`. This is a translation of real
  upstream output, not a reimplementation of upstream's signal or allocation
  logic.
- **Lookback windows**: Q4's single `date` argument is expanded into a
  200-calendar-day lookback ending at `date` (enough bars for the strategy's
  longest 50-day moving average on daily equity data); Q5 uses the caller's
  own `start`/`end` directly.
- **Subprocess execution for all real backtests**: `python -m
  backtest.runner <run_dir>` is invoked as a subprocess (`sys.executable`),
  exactly the same way upstream's own `agent/src/tools/backtest_tool.py`
  invokes it internally (`Runner.execute(..., cli_args=[str(run_path)])`),
  because `backtest/runner.py`'s own `main()` calls `sys.exit()` on error,
  which would kill this adapter's process if called in-process. Only the Q3
  code-generation step (a plain LangChain chat call) and its validation
  happen in-process.
- **Caching**: both the backtest results (keyed by codes/start/end/strategy
  source) and the Q3 LLM-generated code (keyed by ticker/description) are
  cached in-process, so the harness's two passes over each q*() method
  (once individually in section [3], once inside `adapter.run()` in section
  [4]) only pay the real network/LLM cost once. Confirmed by the harness's
  own timing: `adapter.run()` completed in 0.0s on the second pass.
- **Cost control**: the one real DeepSeek call is wrapped so any
  auth/insufficient-balance/quota-shaped exception raises a clear
  `"DeepSeek API balance may be exhausted"` error instead of retrying in a
  loop or being silently swallowed. No such error actually occurred this
  session (real calls succeeded both times, confirmed against the model
  name/base URL other adapters this session already verified empirically:
  `deepseek-v4-flash` / `https://api.deepseek.com`).

### Harness result

```
python CONTRACT/test_harness.py --adapter adapters/vibe_trading_adapter.py
Summary: 25/25 checks passed — ALL PASS
```

Confirmed stable across two consecutive full runs (smoke_test ~38-43s both
times, well under the 300s budget; `adapter.run()` <1s on the cache-hit
second pass, comfortably under the 600s budget).
