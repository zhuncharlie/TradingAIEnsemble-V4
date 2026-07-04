# DECISIONS_tradingagents.md — autonomous decisions log for the TradingAgents adapter

Separate file per instruction (DECISIONS.md is being edited by other adapter
sessions in parallel; this avoids a merge collision). Same fact / **Why** /
**How to apply** style as DECISIONS.md.

---

## Repo verification

- **Confirmed `TauricResearch/TradingAgents` is real and matches the brief**,
  via `curl https://api.github.com/repos/TauricResearch/TradingAgents`
  (created 2024-12-28, ~90k stars, Apache-2.0, description "TradingAgents:
  Multi-Agents LLM Financial Trading Framework", homepage links the arXiv
  paper) and by fetching `README.md` directly.
  **Why**: CLAUDE.md's own Registered Adapters table already named this
  exact repo/org for `tradingagents_adapter.py`, Q1+Q2 — but the brief still
  required independent verification before cloning (repos can be renamed,
  deleted, or squatted).
  **How to apply**: the README describes exactly the architecture the brief
  named — analyst team, bull/bear researchers who debate, a risk team
  (aggressive/conservative/neutral) + judge, and a Portfolio Manager that
  approves/rejects the trade. Confirmed the "social" analyst config key is
  literally `tradingagents.agents.create_sentiment_analyst`
  (`tradingagents/graph/setup.py`), which pulls Yahoo Finance news +
  StockTwits + Reddit (r/wallstreetbets, r/stocks, r/investing) —
  matching the brief's "independent sentiment analyst pulling from
  Reddit/StockTwits" line almost verbatim
  (`tradingagents/agents/analysts/sentiment_analyst.py` docstring).

## Security screening

- **No unrelated subtree found.** Walked the full `tradingagents/` package
  tree (`agents/`, `dataflows/`, `graph/`, `llm_clients/`, `reporting.py`)
  via the GitHub API *before* cloning. Every file is on-topic: analyst/
  researcher/risk-team/manager agent modules, data-vendor connectors
  (yfinance, Alpha Vantage, FRED, Polymarket, Reddit, StockTwits), and LLM
  provider clients (OpenAI, Anthropic, Google, Azure, Bedrock, DeepSeek,
  etc.). Also checked `cli/` and `scripts/` — 8 and 1 files respectively, all
  on-topic (CLI wiring, a structured-output smoke test).
  **Why**: this project already found a real unrelated crypto-payments
  subtree merged into FinGPT under a misleadingly-named branch, wired into
  the exact code path being wrapped (see DECISIONS.md, Session B). Every new
  adapter session screens for the same pattern before trusting a clone.
  **How to apply**: no finding to act on here — clean.
- **No brokerage/exchange credentials, no real money.** Data vendors are
  yfinance / Alpha Vantage / FRED / Polymarket (all keyless or free-tier
  public data) plus Reddit's public RSS search feed and StockTwits' public
  symbol-stream endpoint (both explicitly documented upstream as "no API
  key, no OAuth, no registration", and both degrade to a placeholder string
  on failure rather than raising). The only credential this adapter needs
  is an LLM API key.
  **Why**: the brief called out a real prior finding this session (a
  different adapter's candidate repo required live Robinhood
  username/password just to fetch data — see DECISIONS.md Session C) as the
  exact pattern to watch for. TradingAgents does not have this problem.
  **How to apply**: no blocker; proceeded.

## API key / endpoint decision

- **Reused the existing `DEEPSEEK_API_KEY`** at
  `adapters/vendor/ai-hedge-fund/.env` rather than requesting a new key.
  **Why**: TradingAgents has a *native* `"deepseek"` provider entry in its
  LLM-client registry (`tradingagents/llm_clients/openai_client.py`:
  `OPENAI_COMPATIBLE_PROVIDERS["deepseek"] = ProviderSpec(base_url=
  "https://api.deepseek.com", chat_class=DeepSeekChatOpenAI)`), reading
  `DEEPSEEK_API_KEY` directly (`tradingagents/llm_clients/api_key_env.py`) —
  not merely a generic OpenAI-compatible passthrough that would need a
  hand-configured `backend_url`. Same key, same provider semantics upstream
  already built for it.
  **How to apply**: `tradingagents_adapter.py` sets
  `config["llm_provider"] = "deepseek"` and loads the existing `.env` via
  `dotenv`, exactly like `ai_hedge_fund_adapter.py` already does. No new
  secret was created.
- **Model choice**: `deep_think_llm = "deepseek-v4-pro"` (Research Manager +
  Portfolio Manager — the framework's two "deep thinking" roles),
  `quick_think_llm = "deepseek-v4-flash"` (analysts, bull/bear researchers,
  trader, risk debators — the "quick thinking" roles), per
  `tradingagents/llm_clients/model_catalog.py`'s own DeepSeek entry list.
  **Why**: matches upstream's own quick/deep split intent at the cheaper end
  of its DeepSeek lineup.

## Dependency / environment notes

- **Conda env `tradingagents_real` (Python 3.12) already existed** with
  `tradingagents==0.3.0` pre-installed in site-packages before this session
  touched it. Diffed the installed package tree against a fresh
  `git clone` of the upstream repo (`diff -rq`) — identical except for
  `__pycache__` directories.
  **Why**: confirms the pre-existing install is the genuine upstream 0.3.0,
  not a stale or tampered copy, before trusting it.
  **How to apply**: cloned upstream into `adapters/vendor/TradingAgents`
  anyway (per this project's convention of keeping a vendor/ checkout for
  every adapter) and reinstalled via `pip install --no-deps .` from that
  clone, so the installed package is now traceably built from the vendor/
  checkout in this repo rather than an untraceable prior install.
- **No dependency build failures this session** — `langgraph`,
  `langchain-openai`, `stockstats`, `yfinance`, `backtrader`, etc. all had
  prebuilt wheels for Python 3.12 on this platform. No cmake/Rust/
  conda-forge workaround was needed (unlike FinGPT's transformers pin saga
  or DeepAlpha's xgboost/lightgbm build).

## Translation / design choices (adapter-internal, not upstream changes)

- **One real graph run serves both Q1 and Q2.** `_run()` caches
  `TradingAgentsGraph.propagate()`'s `(final_state, decision)` result keyed
  by `(ticker, date)`. `BaseAdapter.run()` and the test harness both call
  `q1_decision()` then `q2_sentiment()` for the same ticker/date, so without
  this cache the (expensive, ~9-10-real-LLM-call) graph would run twice per
  harness pass. Confirmed empirically: the full harness run took the ~250s
  graph-execution cost exactly once (during `smoke_test()`), and every
  later Q1/Q2/`adapter.run()` check in the harness output logged "0.0s".
  **Why**: cost control — TradingAgents' debate architecture (bull/bear
  researchers, 3-way risk debate, Research Manager, Trader, Portfolio
  Manager) always runs regardless of which analysts are selected, unlike
  ai-hedge-fund where most stages are optional non-LLM nodes. The one
  available cost lever is `selected_analysts`, restricted here to
  `["social"]` (sentiment analyst only — cheapest, and the one Q2 needs
  anyway). Even so, a single run makes on the order of 9-10 real LLM calls;
  there's no way to get this specific framework down to "1 real call"
  without disabling its core debate mechanism.
- **Action mapping**: upstream's 5-tier `PortfolioRating` (Buy / Overweight /
  Hold / Underweight / Sell) collapses onto CONTRACT's 3-way `Action`:
  Buy+Overweight -> BUY, Sell+Underweight -> SELL, Hold -> HOLD.
- **Confidence**: TradingAgents' `PortfolioDecision` has no numeric
  confidence field at all. Bucketed by rating-tier distance from Hold:
  Buy/Sell -> 0.85, Overweight/Underweight -> 0.65, Hold -> 0.5.
- **`bull_case`/`bear_case` populated for the first time across this
  project's adapters** — sourced directly from
  `final_state["investment_debate_state"]["bull_history"]` /
  `["bear_history"]`, the real bull/bear researcher debate transcripts.
- **`sentiment_score`**: the Sentiment Analyst's structured output
  (`SentimentReport.overall_score`, 0-10 scale) is only available in graph
  state as a rendered markdown string
  (`final_state["sentiment_report"]`, via `render_sentiment_report`) — the
  raw Pydantic object isn't retained. Regex-parsed the deterministic header
  line back out and linearly rescaled `(score - 5) / 5` to CONTRACT's
  -1..+1 range. Arithmetic rescaling of a real upstream number, not a
  re-derivation of sentiment from raw text.
- **`risk_level`**: TradingAgents has no generic "market risk level" concept
  anywhere in its output. Rather than building a separate risk-scoring model
  in the adapter (which would cross into "reimplementing upstream logic"),
  bucketed directly off the Sentiment Analyst's own `overall_score`
  extremity (distance from neutral 5.0): >=4 -> EXTREME, >=2.5 -> HIGH,
  >=1.0 -> MEDIUM, else LOW. Documented in the adapter header as an
  adapter-level choice to fill a field upstream doesn't expose, using only
  upstream's own real number as input.
- **`drivers`**: mechanically extracted (newline-split, drop markdown table
  rows/short lines, keep first 5 substantive lines) from the sentiment
  narrative — plain text splitting, not a re-analysis.
- **`sources`**: reported as the fixed list `["Yahoo Finance news",
  "StockTwits", "Reddit"]` — code-verified from
  `sentiment_analyst.py` (these three are pre-fetched unconditionally every
  run), not parsed from prose.

## Harness result

`python CONTRACT/test_harness.py --adapter adapters/tradingagents_adapter.py`
(env `tradingagents_real` active): **24/24 checks passed, ALL PASS.** Smoke
test (real DeepSeek calls, ~250s) confirmed `bull_case`/`bear_case`
non-empty and both Q1/Q2 outputs schema-valid.
