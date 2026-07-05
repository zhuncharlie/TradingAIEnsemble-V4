# DECISIONS_agentictrading.md — standalone log for the AgenticTrading adapter

Written standalone (per this session's brief) rather than editing the shared
`DECISIONS.md` directly, since no other session is concurrently editing it
right now but the merge should still happen deliberately. Same fact /
**Why:** / **How to apply:** style as `DECISIONS.md`.

---

## 2026-07-04/05 — Wave 5: AgenticTrading adapter — 19/19 harness pass, Q5

- **Target was explicitly unconfirmed going in**: the brief described
  "AgenticTrading: standardized leaderboard, history-to-paper-trading full
  pipeline, multi-agent comparison" from a project-planning image, not a
  confirmed repo name, and flagged the risk of this being a duplicate of an
  existing single-strategy Q5 backtester (`finrl_adapter.py`,
  `deepalpha_adapter.py`, `atlas_adapter.py`, `finclaw_adapter.py`,
  `vibe_trading_adapter.py`).
  **Why:** the brief's real concern wasn't naming — it was making sure this
  6th Q5 adapter added a genuinely different *shape* of evidence
  (standardized multi-strategy ranking) rather than a 6th independent
  backtest engine.
  **How to apply:** always check the "is this actually different" question
  before the "does the name match" question when a target repo is unconfirmed.

- **Found `Open-Finance-Lab/AgenticTrading` on the first web search**, and
  it happens to share the target's literal name. Verified directly via
  `GET api.github.com/repos/Open-Finance-Lab/AgenticTrading` (not the search
  snippet) before trusting it, per this session's fabricated-citation
  precedent: 200, real non-fork repo, 315 stars, created 2025-05-21, last
  pushed 2026-07-05 (actively maintained through the literal present).
  Two credible runner-ups (`ulab-uiuc/live-trade-bench`, real, 160 stars;
  `HKUSTDial/DeepFund`, real, 283 stars, NeurIPS'25 workshop, MIT) were also
  checked the same way and are both genuine multi-agent trading benchmarks
  — but `Open-Finance-Lab/AgenticTrading` was chosen because it matches the
  target name exactly and, per the deeper source read below, is the closest
  real implementation of all three feature legs the brief named at once.
  **Why:** the GitHub-API-verification step is necessary but not
  sufficient — the same lesson ATLAS's session drew from
  `chrisworsey55/atlas-gic` (real repo, wrong content) applied here too, so
  content-reading came next regardless of the name match.
  **How to apply:** verify existence via the API, then verify content by
  reading source, every time, even when the name match feels conclusive.

- **README raised its own "buzzwords vs. code" yellow flag, and it turned
  out to be narrower than it looked.** The README's "Future Roadmap"
  section says "Leaderboard backed by real multi-agent runs (replace mock
  data)" — read at face value this could mean the whole leaderboard is
  canned. Reading `dashboard/backend/domain/leaderboard/service.py` and
  `strategies/*.py` directly (not just the README) showed this caveat only
  applies to the *LLM-model* leaderboard entries: `dashboard/config/
  leaderboard.json` marks every `llm_agent`-strategy entry `"auto_compute":
  false` — they're precomputed offline by `scripts/deploy_leaderboard_
  model.py` (expensive real LLM calls, cached rather than recomputed per
  request) and are guarded by a real integrity check
  (`_reject_if_llm_fallback` / `LeaderboardFallbackError` in `service.py`)
  that refuses to publish an LLM entry that silently degraded to
  rule-based trading. The four *deterministic* baseline strategies this
  adapter actually wraps (`buy_hold`, `equal_weight_index`,
  `mean_variance`, `market_index`) are genuinely computed live every time
  via `ensure_leaderboard_runs()` → `get_strategy(cfg).run()` →
  `calc_metrics()` → real `_rank_entries()` — confirmed by actually
  executing this exact call chain against real, live-fetched market data in
  this sandbox, not by trusting the README.
  **Why:** "mock data" in a roadmap note can describe one slice of a
  feature, not the whole feature — the fix is always to trace which code
  path the caveat is actually attached to.
  **How to apply:** when a README admits a limitation, go find the exact
  function/config flag it's talking about before deciding whether it
  disqualifies the whole repo or just narrows what you wrap.

- **Confirmed genuinely non-duplicate**: all four strategies this adapter
  runs share one registry (`strategies/registry.py`), one fixed contest
  window/initial-capital, and one ranking function
  (`service.py::_rank_entries`, a combined return-rank/Sharpe-rank average)
  — a real "standardized leaderboard, multiple strategies compared under
  one protocol" shape. None of the five existing Q5 adapters have this:
  finrl/finrl_x train a single RL policy, atlas is DEAP genetic-programming
  factor mining, finclaw is a classical real-coded GA over a factor-weight
  genome, vibe_trading drives one LLM `SignalEngine`. Nothing else wrapped
  this session runs a *fixed roster of independent strategies through one
  shared ranking harness*.
  **Why:** CLAUDE.md disallows a duplicate-upstream adapter, but the more
  important test is whether the new adapter demonstrates a materially
  different *evaluation methodology*, which this one does.
  **How to apply:** compare mechanism, not just README vocabulary, against
  every existing adapter's upstream before committing to a new one.

- **Security screening**: no live brokerage/exchange credentials or real
  money anywhere in the path this adapter calls. Upstream's *default* data
  source for the leaderboard baselines is Alpaca's **paper**-trading API
  (`ALPACA_BASE_URL=https://paper-api.alpaca.markets` per `.env.example`) —
  never live/funded, but still requires a free account/API key signup. This
  adapter avoids that entirely: every `BaselineStrategy.run(bars_by_symbol,
  ...)` in upstream's own code takes already-fetched bars as a plain
  dependency-injected argument (`strategies/base.py`), so this adapter
  supplies that argument itself via `yfinance` (public, no-signup, already
  an upstream dependency in `requirements.txt`) instead of importing
  upstream's `AlpacaDataLoader` at all — the same "swap the data source,
  keep the real strategy class" pattern upstream's own `market_index.py`
  already uses internally for `^DJI`/`^GSPC` (Yahoo direct, since "Alpaca
  only serves tradeable ETFs, not the underlying index"). This satisfies
  CLAUDE.md's "beyond public/historical market data" prohibition without
  touching upstream source.
  **Why:** a repo defaulting to a paper-trading broker isn't automatically
  disqualifying (unlike NoFx's live-funded-credential requirement), but it
  still shouldn't force an account signup on every later re-run of this
  adapter if a public substitute for the *injected* dependency exists.
  **How to apply:** check whether the credentialed data source is a hard
  requirement of the algorithm itself, or just the default value of a
  dependency-injected parameter — the latter can often be substituted
  cleanly with public data.

- **Two upstream import-time footguns found and worked around without
  touching vendor source**:
  1. `BaselineGenerator.__init__` (used internally by the real
     `buy_hold`/`equal_weight_index` strategy classes) unconditionally
     calls `sys.exit(1)` if neither `ALPACA_API_KEY`/`ALPACA_SECRET_KEY` env
     vars nor `credentials/alpaca.json` are present — even though the two
     methods this adapter actually calls
     (`generate_buyhold_baseline`/`generate_index_baseline`) never touch
     the network, only the injected `bars_by_symbol` argument (confirmed by
     reading `baseline_generator.py`: the only network method,
     `_fetch_bars_for_symbol`, is never invoked by either). Worked around
     with `os.environ.setdefault("ALPACA_API_KEY", "unused-placeholder-...")`
     — inert placeholders, never used for any real network/account call.
  2. `dashboard/backend/domain/leaderboard/service.py` (needed only for its
     real `_rank_entries` function) transitively imports
     `dashboard/backend/database.py`, which runs SQLite schema migrations
     against `DATABASE_PATH` at import time — left at its default this
     would mutate the upstream repo's own committed
     `dashboard/storage/data/backtest.db` (confirmed by accident during
     manual testing before the fix). Worked around by setting
     `DATABASE_PATH` (via `os.environ.setdefault`, before the import) to a
     private scratch file inside the gitignored `adapters/vendor/` clone —
     the same "point it at a scratch file" convention the upstream repo's
     own `tests/conftest.py` already documents for its own test suite.
  **Why:** both are real preconditions upstream's own code enforces at
  import/construction time that have nothing to do with this adapter's
  actual (network-free / DB-free) call path — satisfying them with inert
  placeholders is not the same as patching or reimplementing logic.
  **How to apply:** when a constructor/import raises on a missing
  precondition your actual call path never needs, prefer an inert
  environment shim over either skipping the import or patching the source.

- **Scope reduction — `llm_agent` leaderboard strategy excluded.** Upstream's
  real `llm_agent.py` strategy makes real per-hour LLM trading-decision
  calls, but `make_llm_client()`
  (`infrastructure/llm/backtest_harness.py`) only builds an
  `anthropic.Anthropic(...)`-shaped client — native Anthropic, or the
  CommonStack gateway (which re-exposes DeepSeek behind an
  *Anthropic-response-shaped* endpoint: `content[0].text` +
  `usage.input_tokens`/`output_tokens`). This session's only available key
  is `DEEPSEEK_API_KEY` (confirmed present at `adapters/vendor/ai-hedge-
  fund/.env`; confirmed absent: `ANTHROPIC_API_KEY`/`COMMONSTACK_API_KEY`),
  which is OpenAI-compatible in both request and response shape — not
  Anthropic-shaped. Wiring it in safely would require either an invasive
  patch reimplementing `request_trading_decision`/`extract_response_text`/
  `extract_token_usage` for a different response schema (crosses into
  "reimplementing upstream logic", disallowed by CLAUDE.md), or
  monkeypatching `make_llm_client` at runtime (the same class of
  "modifying upstream internals" CLAUDE.md's own bad-example explicitly
  disallows). Rather than force either, this adapter reports Q5 using only
  the four deterministic strategies (`buy_hold`, `equal_weight_index`,
  `mean_variance`, `market_index`), which already fully exercises the
  "standardized leaderboard / multi-strategy comparison" feature the brief
  called out, and honestly excludes the model-agent leaderboard slice
  instead of faking it. No LLM calls occur anywhere in this adapter — no
  API key needed, no balance/cost-control concerns (same "no LLM at all"
  scope class as `atlas_adapter.py`).
  **Why:** CLAUDE.md's cost-control instructions exist to prevent silent
  degraded/fabricated LLM results as much as to prevent wasted spend; since
  upstream's own client factory can't honestly serve DeepSeek's shape
  without a disallowed level of patching, the honest choice is exclusion,
  not a best-effort fake.
  **How to apply:** when a genuinely different LLM provider requires
  reimplementing request/response parsing to fit a upstream client factory
  built for a different provider's SDK shape, that crosses from "wrap" into
  "reimplement" — scope it out and document why, rather than force it.

- **Scope reduction — point-in-time window clamping.** `yfinance` only
  serves 60-minute bars for the trailing ~730 days from the real
  wall-clock present (confirmed via `date -u` in this sandbox: real system
  clock is in July 2026). CONTRACT's own sample window
  (`2024-01-01`/`2024-03-31`) is outside that horizon — confirmed by an
  actual failed fetch returning yfinance's own explicit "must be within the
  last 730 days" error, not assumed. `_clamp_window()` in the adapter
  detects this and substitutes the closest real, currently-available
  intraday window of the same (capped, 5–30 day) length, surfaced in
  `Q5Backtest.test_period` whenever the substitution fires.
  **Why:** same "point-in-time clamp to real available coverage, disclose
  it" pattern `atlas_adapter.py` (bundled-dataset date range) and
  `finclaw_adapter.py` (yfinance history windowed to the requested date)
  already established this session, generalized to a rolling real-time data
  horizon instead of a fixed bundled dataset's range.
  **How to apply:** whenever a real data source has a hard historical
  horizon and a schema's sample dates might fall outside it, verify with a
  real failing call first, then clamp deterministically and disclose the
  substituted window in the schema's own period field.

- **Scope reduction — universe/window caps.** Ticker universe capped to 5
  symbols, backtest window capped to 30 days (still >2 real trading weeks
  of hourly bars) to keep `adapter.run()` comfortably inside the harness's
  600s budget. This is a real, unmodified, live-data backtest end to end —
  just shorter than upstream's own full one-month contest window
  (`dashboard/config/leaderboard.json`'s real contest is `2026-04-15` to
  `2026-05-15`).
  **Why:** every adapter this session needed at least one scope reduction
  to fit harness timeouts; this one is purely a size/time cap, not a
  behavior change.

- **Environment**: dedicated conda env `agentictrading_real`, Python 3.12.
  `pandas-ta==0.4.71b0` (transitively required at import time by
  `llm_agent.py`, which `strategies/registry.py` imports unconditionally
  even though this adapter never calls it) declares
  `Requires-Python >=3.12` with no prebuilt wheel for 3.11 — the env was
  bumped to 3.12 rather than patched/pinned around. `pip install numpy
  pandas pydantic yfinance pytz requests pandas-ta` all installed cleanly
  from PyPI; no cmake/Rust/conda-forge fallback was needed for this
  adapter. The `anthropic` SDK is intentionally not installed (see the
  `llm_agent` scope reduction above) — upstream's own optional-dependency
  guard handles `HAS_ANTHROPIC=False` gracefully (confirmed: a harmless
  "Anthropic SDK not installed" print, never an exception).

- **Verification, not just reading**: actually executed, in this sandbox,
  the real call chain a live leaderboard refresh uses —
  `get_strategy(cfg).run(bars, start, end, capital)` for `buy_hold`,
  `equal_weight_index`, and `mean_variance` against real live-fetched
  `yfinance` hourly bars for AAPL/MSFT/NVDA, and `market_index` against
  real live-fetched Yahoo `^GSPC` data via upstream's own
  `_yahoo.fetch_index_hourly` — all four produced real, distinct,
  non-degenerate equity curves and metrics. Then ran the real
  `calc_metrics()` and `_rank_entries()` on the resulting entries and
  confirmed the ranking executes correctly end to end, before writing the
  adapter around that confirmed-working call chain.

- **Result**: `python CONTRACT/test_harness.py --adapter
  adapters/agentictrading_adapter.py` → **19/19 checks passed, ALL PASS**
  (smoke_test in ~8.5s, `adapter.run()` in ~1.3s — both comfortably inside
  the 300s/600s budgets).
