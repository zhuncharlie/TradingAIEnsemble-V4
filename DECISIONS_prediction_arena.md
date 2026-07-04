# DECISIONS_prediction_arena.md — autonomous decisions log (prediction_arena adapter)

Session scope: build `adapters/prediction_arena_adapter.py` for the target
brief "Prediction Arena: LLMs tested on real prediction markets, live
implied-probability signal (Q2); real-money live testing, a 57-day LLM
comparison experiment on Kalshi/Polymarket (Q5)". Per instructions, this file
is separate from the shared `DECISIONS.md` to avoid concurrent-edit
collisions with other sessions.

---

## Repo search — what was tried, what was rejected, and why

**1. The literal "Prediction Arena" project — real, but not usable.**
It exists: arXiv 2604.07355, "Prediction Arena: Benchmarking AI Models on
Real-World Prediction Markets" (Zhang, Liu, Johansson, Yitayew, Ohly, Li),
plus a live site at `predictionarena.ai/methodology`. The paper describes
exactly this brief — six frontier models trading real capital on Kalshi and
Polymarket, 57 days (Jan 12–Mar 9 2026), $10k starting capital per agent,
autonomous decisions every 15–45 minutes.

- Directly fetched the arXiv HTML (not just a search snippet) and checked
  specifically for a code-availability statement / GitHub link / "Appendix
  C" pointer the paper's own abstract-summary implied existed. **None is
  present anywhere in the paper.**
- An initial `WebSearch` summary claimed "the full simulation pipeline ...
  released open-source at `github.com/foresight-arena/analysis`". Checked
  this directly against the GitHub REST API: **that repo returns 404 — it
  does not exist.** The `foresight-arena` GitHub org is real, but is an
  unrelated project ("on-chain prediction competition for AI agents on
  Polygon", per its own org description) — a different concept entirely,
  not this paper's code. This is a concrete example of why a prose web
  summary must be checked against a primary source (GitHub/arXiv API)
  before being trusted — it fabricated a specific, plausible-looking
  citation.
- **Rejected** regardless of code availability: even if real code existed,
  the paper's methodology is inherently live-money trading on Kalshi and
  Polymarket with funded accounts, which this session's security policy
  prohibits wiring up under any circumstances.

**2. `spfunctions/prediction-market-model-benchmark`** — confirmed real via
GitHub API (not a hallucination), with a description matching the brief
almost verbatim ("Open benchmark harness for latest major AI models on
prediction-market forecasting, calibration, microstructure, and
trading-risk tasks"). **Rejected** as an unreliable/likely-placeholder
source: the owning account (`spfunctions`) was created 2026-03-14 and
already owns 35 repositories; this specific repo has 0 stars; and its file
tree is skeleton-only — empty `docs/`, `examples/`, `schemas/`, `src/`,
`tasks/`, `tests/` directories alongside just a README, `pyproject.toml`,
and a `model_roster.json`. No actual implementation to wrap. The same
account's `prediction-markets-reading` repo (also cited by search results)
shows the same recent-creation, content-farm-like pattern. Not a
community-vetted open-source project in the sense the other adapters in
this repo wrap.

**3. Settled on `Metaculus/forecasting-tools`**
(github.com/Metaculus/forecasting-tools) — the official repository of the
Metaculus organization. Confirmed real and actively maintained: 73 stars,
pushed the same calendar day as this session, MIT-licensed, single coherent
Python package with no foreign subtrees. It is a genuine, actively-used
framework for building LLM-based forecasting bots — the closest verified-real
match to "LLMs tested on real prediction markets" available, even though its
native target platform is Metaculus (a free forecasting community) rather
than Kalshi/Polymarket by default.

Why this is still a faithful match to the brief and not a stretch: this
adapter uses only forecasting-tools' bot-forecasting *engine* (its own exact
prompt templates and JSON-parsing code, called unmodified) and pairs it with
**real, public Kalshi market data fetched directly by this adapter** — so
the end result genuinely is "a real LLM forecast vs. a real Kalshi-implied
probability," just assembled from two real, independently-verified real
components instead of one project that does both end-to-end (which doesn't
exist in public, safely-wrappable form).

---

## Security screening (real-money angle — the extra-caution item)

- **Metaculus itself involves no money** (a free forecasting community, not
  an exchange), so it's not the real-money concern — but it turned out to
  have its own access issue: as of this writing, Metaculus's REST API
  requires a `METACULUS_TOKEN` even to *read* a question (confirmed live:
  `GET https://www.metaculus.com/api/posts/28841/` → `403 "The API is only
  available to authenticated users. Please create an account and use your
  API token to access the API."` with no token set). No token was
  available or requested for this adapter, so **the Metaculus platform/API
  is never contacted at all** by `prediction_arena_adapter.py`. (Upstream's
  `ForecastBot.__init__` still constructs a `MetaculusClient()` internally
  — it just logs a warning when unconfigured — but nothing in this adapter
  calls any of that client's network methods.)
- **Kalshi**: confirmed live that `https://api.elections.kalshi.com/trade-api/v2/{markets,events,candlesticks}`
  return real market data with **zero authentication** — no API key, no
  account, no funded wallet. Only `GET` requests are issued anywhere in this
  file; no order-placement, portfolio, or account endpoint is ever called.
- **Polymarket**: also confirmed live and public/keyless
  (`gamma-api.polymarket.com/markets`, `clob.polymarket.com/markets` both
  return real 200s with no auth) — not used in the final implementation
  (Kalshi's Companies/Financials/Economics event categories gave cleaner,
  more per-company-relevant real markets than Polymarket's inventory, which
  skews sports/crypto/politics), but confirmed available as a safe,
  read-only alternative/fallback source if needed later.
- **No funded brokerage/exchange account, private key, or wallet credential
  of any kind is used, read, or required anywhere in this adapter.** No
  live order can ever be placed by this code — it only issues `GET`s
  against public market-data endpoints and real (but harmless, read-only)
  LLM completion calls.
- Screened `Metaculus/forecasting-tools` for the FinGPT-style
  unrelated-merged-subtree pattern: none found. Single coherent package,
  matches its stated single purpose.

---

## Dependency / environment notes

- New dedicated env `prediction_arena_real` (python 3.11), not shared with
  any other adapter.
- `pip install forecasting-tools` initially failed: `tiktoken`, `libcst`,
  and `pyarrow` are Rust-backed transitive dependencies, and their current
  releases ship only `manylinux_2_28` wheels (require glibc ≥ 2.28); this
  sandbox's glibc is 2.27, so pip fell back to source dists, which need a
  Rust compiler — not installed here, and installing one was avoided in
  favor of the same fix pattern `deepalpha_adapter.py` used for its own
  compiled-dependency mismatch:
  - `conda install -c conda-forge libcst pyarrow` (precompiled binaries)
  - `pip install "tiktoken<0.12" forecasting-tools requests python-dotenv`
    (tiktoken releases below 0.12 still ship `manylinux2014`/glibc-2.17
    wheels, which this system's glibc satisfies)
- Also `git clone --depth 1 https://github.com/Metaculus/forecasting-tools.git`
  into `adapters/vendor/forecasting-tools/`, and the adapter inserts that
  path at the front of `sys.path` **ahead of** the pip-installed copy. Why:
  the pip-installed release (0.2.92, latest on PyPI at time of writing) does
  not yet contain `forecast_bots/official_bots/no_research_one_shot_bot.py`,
  which exists on the GitHub `main` branch (published ahead of the last PyPI
  cut). The vendored source is used for the bot classes/data models; its
  already-pip-installed dependencies (litellm, pydantic, etc.) are reused
  unchanged from site-packages. No upstream file was modified — this is a
  version-selection shim, not a patch, so there is no
  `patches/forecasting-tools.diff`.
- LLM: DeepSeek via litellm's native `deepseek/` provider string (confirmed
  supported by reading `forecasting_tools/ai_models/general_llm.py`'s
  `_defaults` dict, which has a dedicated `"deepseek/"` timeout entry).
  Reuses the existing `DEEPSEEK_API_KEY` at
  `adapters/vendor/ai-hedge-fund/.env` (same key `ai_hedge_fund_adapter.py`
  uses) — no new key was requested or created. litellm reads
  `DEEPSEEK_API_KEY` from the environment natively for this provider; no
  OpenAI-compatible `base_url` shim was needed.
  - Caught one real bug during validation: the adapter initially never
    called `load_dotenv()` on `adapters/vendor/ai-hedge-fund/.env`, so the
    first harness run failed with a real `litellm.AuthenticationError` from
    DeepSeek ("Authentication Fails"). This looked exactly like the
    "balance may be exhausted" failure mode the brief warns about, but
    turned out to be a missing-env-var bug in this adapter, not an account
    problem — confirmed via `env | grep DEEPSEEK` showing the key genuinely
    absent from the process environment before the fix. Fixed by adding the
    same `load_dotenv(dotenv_path=...)` pattern `fingpt_adapter.py` uses.
    After the fix, a real DeepSeek call succeeded end-to-end (see harness
    output). No balance/quota issue was ever encountered with the real key.

---

## Design / scope choices

- **Q2 (live implied-probability signal)**: Kalshi doesn't sell literal
  per-equity price-threshold contracts — its inventory is real-world
  corporate/macro event markets (e.g. "DOJ wins their anti-trust case
  against Apple?", ticker `APPLEUS-29DEC31`). The adapter keyword-matches
  the requested ticker against a small built-in company-name map, searched
  live across Kalshi's public `Companies`/`Financials`/`Economics` event
  categories; if no real match is found it falls back to the verified-real,
  actively-traded Apple antitrust market and says so explicitly in Q2's
  `drivers` list (never silently substitutes).
  - `sentiment_score` = the real LLM's own `P(yes)` conviction on the
    tracked real-world question, rescaled linearly to `[-1, 1]`. Explicitly
    **not** a bullish/bearish valence judgment — Kalshi's event markets vary
    in valence per question (a "DOJ wins" market resolving YES is bad news
    for the company; an "IPO" market resolving YES is neutral-to-good), and
    automatically inferring valence would require additional analysis
    neither upstream project performs nor this adapter attempts.
  - `risk_level` is derived from the real divergence between the LLM's
    forecast and the real Kalshi market-implied probability (mid of
    yes_bid/yes_ask) — bigger model/market disagreement is treated as
    higher uncertainty, the same "dispersion implies risk" pattern
    `fingpt_adapter.py` uses for its own risk_level derivation.
- **Q5 (57-day live comparison) — scope reduction**: a genuine 57-day live,
  real-money, multi-model Kalshi/Polymarket comparison cannot be reproduced
  here — it requires funded exchange accounts (disallowed by security
  policy) and 57 real days of wall-clock time (incompatible with a single
  harness call, `adapter.run()` budget is 600s). Implemented instead as a
  real backtest of "buy-and-hold the YES side" on one real Kalshi market,
  using its full available public daily-candlestick price history (Kalshi's
  candlestick and trade-history endpoints are also public/keyless, confirmed
  live) — typically ~1+ year of real daily closes for the default market.
  `total_return`/`sharpe`/`max_drawdown`/`win_rate`/`equity_curve` are
  computed directly from that real price path with standard, undisguised
  arithmetic (no synthetic or fabricated prices at any point). This is the
  same style of scope reduction `deepalpha_adapter.py` and
  `ai_hedge_fund_adapter.py` document for their own unreproducible full
  upstream methodologies.
- Per-ticker in-process caching of both the Kalshi market lookup and the
  real DeepSeek forecast, so `run()` (which can call q2 and q5 for the same
  ticker) and repeated harness invocations don't redundantly re-query Kalshi
  or re-call the LLM.

---

## Validation

```
conda activate prediction_arena_real
python CONTRACT/test_harness.py --adapter adapters/prediction_arena_adapter.py
```
Result: **22/22 checks passed — ALL PASS** (smoke_test in ~33s, well under
the 300s budget; `adapter.run()` in ~2.5s, well under the 600s budget — the
run() timing is fast because it reuses the in-process caches warmed by the
smoke test / Q-method checks that preceded it in the same harness process).
