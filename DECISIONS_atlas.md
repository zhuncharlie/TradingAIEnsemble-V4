# DECISIONS_atlas.md — autonomous decisions log for the ATLAS adapter

Written separately from the shared `DECISIONS.md` per this session's brief
(a parallel NoFx-adapter session is editing that file concurrently). Same
style/intent as the shared log: decisions made without stopping to ask,
newest at the bottom (single session, so just one dated block).

---

## 2026-07-04 — ATLAS adapter — commit pending, harness pass count below

- **"ATLAS" was not a confirmed repo name** — the target came from a
  project-planning image: "automated research + Darwinian selection,
  discovers new alpha factors, multi-queue meta-weighting", answering Q3.
  "ATLAS" is an extremely common project name, so the search process
  deliberately did not stop at the first repo literally named ATLAS.
  **Why:** the brief explicitly warned this name is a common false-positive
  magnet (physics experiments, cloud infra, unrelated ML frameworks) and
  told this session to verify real source content, not just a name/README
  match, before wrapping anything.
  **How to apply:** for any future "confirm-the-repo" adapter task, budget
  time to read the actual source of every plausible candidate (not just
  its README) before choosing — a README can describe a completely
  different mechanism than the code implements (see QuantaAlpha below).

- **Rejected `chrisworsey55/atlas-gic`** despite it being a *real* repo
  (verified via `GET api.github.com/repos/chrisworsey55/atlas-gic` -> 200,
  1999 stars, real push history) whose README uses almost the exact target
  vocabulary ("Darwinian selection", "meta-weighting" via a "JANUS" layer).
  Reading its actual source (`src/janus.py`, `src/mirofish/*.py`) showed its
  "Darwinian selection" evolves **LLM agent system-prompts** via git-commit/
  git-revert scored by rolling Sharpe — there is no alpha-factor formula
  search anywhere in the tree. It also states it is "now running live with
  real capital" and requires an Alpaca brokerage account plus FMP/Finnhub/
  Polygon/FRED/Anthropic API keys.
  **Why:** this session's brief has two independent stop-conditions this
  repo trips: (1) content doesn't match ("discovers new alpha factors" —
  this project discovers new *prompts*, not factors), and (2) it requires
  live brokerage credentials and real capital, which the brief says to
  stop and report rather than wire up.
  **How to apply:** a repo can be simultaneously "real" (not a fabricated
  citation) and "wrong" (real but off-target, or real but disqualified on
  security grounds) — verifying existence via the GitHub API is necessary
  but not sufficient; both content-match and security screening still have
  to happen even after existence is confirmed.

- **Rejected `The-Swarm-Corporation/ATLAS`** (real-time HFT volatility/risk
  monitor) — no genetic/evolutionary component, wrong domain entirely.

- **Rejected `QuantaAlpha/QuantaAlpha`** — the strongest runner-up: real,
  1.2k-star, arXiv-backed (2602.07085), free-data (Qlib/HuggingFace),
  DeepSeek-compatible LLM-driven formulaic-alpha-factor mining framework.
  Reading `quantaalpha/core/evolving_framework.py` directly showed it is a
  **single-subject, trajectory-based iterative-refinement loop**
  (`EvolvingStrategy.evolve()` over one `EvolvableSubjects` instance,
  RAG-guided), not population-based: no fitness-ranked population, no
  discard/selection step, no multiple cohorts combined by weight.
  **Why:** the target description specifically asks for *Darwinian
  selection* (population + selection pressure), which this project's own
  code does not implement despite "evolutionary" branding in its README/
  paper abstract.
  **How to apply:** "evolutionary" in a project's marketing copy can mean
  either "genetic-algorithm population selection" or "iteratively refines
  itself over trajectories" — these are different algorithms; check the
  actual loop structure (is there a `population`? a `select`/`discard`
  step operating on multiple candidates at once?) before treating them as
  interchangeable.

- **Rejected `Morgansy/Genetic-Alpha`** (real, runnable single-population
  genetic-programming factor miner — no multi-queue/pool structure) and
  **`KangOxford/AutoFactor`** (repo contains only two PDFs, no code) and
  noted **AutoAlpha** (Zhang et al., arXiv:2002.08245, Tsinghua) has no
  public code implementation (confirmed via Papers-with-Code).

- **Settled on `Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining`**:
  real DEAP-based genetic programming over a bundled 236-token crypto-
  perpetuals panel (2021-11-06 to 2024-08-14, 145k rows, real historical
  data). Confirmed real (GitHub API 200; single-day commit history,
  disclosed rather than hidden) and confirmed *functioning* by actually
  executing `GPProcess.run()` in this sandbox, not just reading it — it
  produced real evolved formula trees with real fitness values.
  **Why this is the closest real match**: `deap.tools.selNSGA2` (Pareto-
  front multi-objective selection) + `tools.HallOfFame` is genuine
  Darwinian population selection over literal alpha-factor formula trees
  (not prompts, not a fixed factor list); upstream's own `GPProcess.run()`
  literally splits the population into sequential "Batch 1", "Batch 2", ...
  sub-populations (its own print output uses that word) that are evolved
  independently and then combined via `sortNondominated` across all
  batches — the closest literal analogue to "multi-queue" combination of
  evolved-factor pools found across every candidate checked. It is *not*
  literally "meta-weighting" (the combination is Pareto-front selection +
  a validation-set accept/reject filter, not a weighted average) — this
  gap is documented in the adapter header rather than overclaimed.
  **How to apply:** when no candidate is a perfect terminology match,
  prefer the one whose actual *mechanism* (not vocabulary) is closest to
  every clause of the target description, and say exactly which clause
  isn't a literal match rather than rounding up.

- **Security screening clean, and the cleanest of any adapter this
  session**: no eval/exec/os.system/shell=True/subprocess anywhere; the one
  `pickle.load` call is upstream's own optional "predict" mode loading a
  `.pkl` it wrote itself in the same run (never called by this adapter);
  zero hits for any credential/broker/api_key/secret/token pattern anywhere
  in the codebase. This project needs **no external data source, no
  account, and no API key of any kind** — its entire input is the repo's
  own bundled historical CSV panel.
  **Why:** the brief flagged two real problems found elsewhere this session
  (FinGPT's unrelated `finogrid/` subtree; a different candidate needing
  live brokerage credentials) as the exact pattern to screen for — this
  repo has neither, and needing zero live data/accounts at all is a
  meaningfully lower-risk profile than every other adapter built this
  session.

- **No LICENSE file in the upstream repo** (`GET .../license` -> 404).
  Documented for transparency; this adapter wraps the public code
  read-only for side-by-side comparison in this project, same posture as
  every other adapter here, not redistribution.

- **Environment**: dedicated `atlas_real` conda env (python 3.11), never
  shared with another adapter. `pip install deap pandas numpy pydantic`
  plus `pip install torch --index-url https://download.pytorch.org/whl/cpu`
  — torch has a prebuilt CPU wheel for this platform/Python combination, so
  no cmake/Rust build-from-source issue and no conda-forge fallback was
  needed here (unlike xgboost/lightgbm/pyarrow/libcst earlier this
  session). No LLM API key needed anywhere — this adapter is pure
  genetic-programming/statistics, no LLM calls at all.

- **Scope reduction — GA budget**: upstream's own `main.py` example uses
  `population_num=200, batch_size=10, generation=6` (20 batches × 6
  generations). This adapter uses `population_num=40, batch_size=10,
  generation=2` (4 batches/"queues" × 2 generations, ~20-80s wall-clock in
  this sandbox depending on which cross-sectional operators get sampled)
  so the harness's smoke_test (<300s) and adapter.run() (<600s) timeouts
  are comfortably met — still upstream's own unmodified `GPProcess.run()`,
  real NSGA-II selection, real Hall of Fame, real validation-set accept/
  reject filter, just a smaller/faster budget. Cached per requested `date`
  in-process so the harness's repeated calls with the same date (direct
  Q3 call + `adapter.run()`) don't retrain.

- **Scope reduction — ticker universe**: upstream's real universe is its
  own bundled 236-name crypto-perpetuals panel (e.g. `BTCUSDT`), not
  equities tickers. This adapter normalizes the requested `ticker`
  (`.upper()`, then also tries `+"USDT"`) against that real panel; when it
  doesn't match (e.g. the CONTRACT harness's own `"AAPL"` sample ticker),
  it falls back to a fixed representative token (`BTCUSDT`, quoted across
  the entire bundled date range) and says so explicitly in
  `supporting_evidence` — same reinterpretation pattern `finrl_x_adapter.py`
  used for its NASDAQ-only universe mismatch.

- **Scope reduction — point-in-time windows**: train/val/test windows are
  derived from the requested `date` (train: [date-480d, date-120d]; val:
  [date-120d, date-30d]; test: [date-120d, date], the extra 120-day
  head-room before `date` needed because upstream's own time-series
  operators use rolling windows up to 60 days and otherwise return `NaN`
  for the first ~60 rows — confirmed empirically). Both `date` and the
  derived boundaries are clamped into the bundled dataset's real coverage
  (2021-11-06 to 2024-08-14) since it's a static historical panel, not a
  live feed; a request for a date outside that range would be clamped and
  therefore not truly point-in-time (documented limitation). At the
  harness's own sample date (`2024-01-15`), with the 480-day training
  lookback chosen, no clamping occurs.

============================================================================
Result
============================================================================
Repo used: https://github.com/Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining
Adapter: adapters/atlas_adapter.py (Q3 only)
Harness: `python CONTRACT/test_harness.py --adapter adapters/atlas_adapter.py`
  → 20/20 checks passed, ALL PASS (smoke_test ~25-80s depending on which
  operators get sampled each run; full harness well under the 600s
  adapter.run() budget since Q3 results are cached per date).
