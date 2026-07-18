"""
adapters/atlas_adapter.py — wraps
github.com/Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining
(Q3 — alpha signal / anomaly detection).

============================================================================
Repo search / vetting process (target was "ATLAS: automated research +
Darwinian selection, discovers new alpha factors, multi-queue meta-
weighting" — a description from a project-planning image, NOT a confirmed
repo name going in, and "ATLAS" is an extremely common project name)
============================================================================
  Candidates found and why each was rejected before settling on a match:

  - `chrisworsey55/atlas-gic` ("ATLAS by General Intelligence Capital") —
    this IS a real repo (confirmed via `GET api.github.com/repos/...` -> 200,
    1999 stars, 365 forks, real commit/push history through 2026-07-01 — not
    a fabricated citation like the one this session's brief warned about).
    Its own README describes almost the exact target vocabulary
    ("Darwinian selection", "meta-weighting" via a "JANUS" layer across
    cohorts) closely enough that it looked like a strong hit on first read.
    But reading past the README summary into what it actually *is* (per the
    brief's "verify by reading real source, not just README" instruction):
    its "Darwinian selection" operates on **LLM agent system-prompts**
    (git-commit/git-revert of prompt edits scored by rolling Sharpe), not on
    mathematical alpha-factor formulas — `src/janus.py` and
    `src/mirofish/mirofish_*.py` are prompt/context generators for LLM
    trading agents, there is no formula/expression search anywhere in the
    tree. It also explicitly states it is "now running live with real
    capital" and requires an Alpaca (equities) brokerage account plus FMP/
    Finnhub/Polygon/FRED/Anthropic API keys — this alone is a hard stop per
    this session's brief ("if the repo requires live brokerage/exchange
    account credentials or real money ... STOP and report back"). Rejected
    on BOTH content-mismatch and security grounds.
  - `The-Swarm-Corporation/ATLAS` — real repo, but is a real-time
    volatility/risk-metric monitor (HFT risk analysis), not an alpha-factor
    discovery system. No genetic/evolutionary component at all. Rejected:
    wrong domain.
  - `QuantaAlpha/QuantaAlpha` — real, substantial, actively-maintained
    (1.2k stars) LLM-driven "self-evolving" formulaic-alpha-factor mining
    framework, arXiv-backed (2602.07085), free Qlib/HuggingFace market data,
    no brokerage requirement, DeepSeek-compatible LLM key. The closest
    "automated alpha-factor research" match by far. But its own
    `quantaalpha/core/evolving_framework.py` (read directly, not just the
    README) is a **single-subject, trajectory-based iterative-refinement**
    loop (`EvolvingStrategy.evolve()` over one `EvolvableSubjects` instance
    at a time, RAG-guided) — there is no population, no fitness-based
    selection/discard, no multiple parallel cohorts combined by weight. It
    is evolutionary in the "iteratively improves" sense, not in the
    Darwinian population-selection sense the target description asks for.
    Kept as a strong runner-up but not selected because it doesn't actually
    do population-based selection.
  - AutoAlpha (Zhang et al., Tsinghua, arXiv:2002.08245) — the paper that
    best matches "hierarchical evolutionary alpha-factor mining" by name,
    but Papers-with-Code lists no code implementation; no public repo
    found under any obvious name. Not usable.
  - `Morgansy/Genetic-Alpha` — real, runnable genetic-programming alpha
    factor miner (symbolic regression, single population, standard
    generational GA). No multi-queue/pool structure — evolves one
    population end to end. A legitimate but weaker match than the repo
    finally chosen.
  - `KangOxford/AutoFactor` ("Factor Mining with Evolution Strategies") —
    repo contains only two PDFs (a Huatai Securities research-note
    reproduction target and an unrelated high-frequency-returns paper), no
    code at all. Rejected: not runnable.

  Settled on `Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining`:
  a real, runnable (verified by executing it, not just reading it) DEAP-based
  genetic-programming alpha-factor miner for a 236-token crypto-perpetuals
  panel. It is the closest real match to the target's specific mechanics:
    - **Darwinian selection**: literal `deap.tools.selNSGA2` (multi-objective
      Pareto-front selection — survival of the fittest formula trees across
      generations), `tools.HallOfFame`, and a final `sortNondominated`
      selection across all evolved individuals — genuine population-based
      selection, not prompt-editing or trajectory refinement.
    - **Discovers new alpha factors**: individuals are literal formula trees
      (`gp.PrimitiveTree`) over real technical/statistical columns
      (`mean`, `std`, `skew`, `kurt`, `meanBest5`, `EmaBest5`, ...), compiled
      and evaluated on real data — exactly "new alpha factors", not a
      pre-fixed factor list.
    - **Multi-queue**: upstream's own `GPProcess.run()` literally splits the
      total population into sequential batches (its own print output says
      "Batch 1", "Batch 2", ...) — independent sub-populations (queues) that
      are each evolved for `generation` rounds and then combined via
      `tools.sortNondominated` across all batches into one final accepted
      set. This is a genuine, literal multi-queue-of-evolved-factors-combined
      structure — the closest real analogue to "multi-queue meta-weighting"
      found in this search. It is NOT literally called "meta-weighting" by
      upstream (the combination step is Pareto-front selection + a
      validation-set accept/reject filter, not a weighted average) — this
      difference is documented honestly rather than overclaiming a match.

============================================================================
Verification that the chosen repo is real (not a squat/fabrication) and a
functioning, on-topic implementation (not vaporware) — this session's brief
warned that a web search once fabricated a plausible-looking 404 GitHub
citation, so every candidate above was checked directly against the GitHub
API, and this repo's actual `.py` files were fetched and *executed* here,
not just summarized by a search engine
============================================================================
  - `GET api.github.com/repos/Yitong-Guo/Genetic-Algorithm-for-quantitative-
    alpha-factors-mining` -> 200. Real user account, real single-day commit
    history (2024-09-03, 4 commits — a research-note reproduction rather
    than a long-lived maintained project, which is disclosed here rather
    than hidden), 35 stars.
  - No LICENSE file in the repo (checked: `GET .../license` -> 404). Noted
    for transparency; this adapter wraps the public code read-only for
    side-by-side comparison/evaluation in this project, the same posture
    used for every other adapter here, not redistribution.
  - Ran upstream's own `GPProcess.run()` (unmodified) end to end in this
    sandbox on the repo's own bundled real data (`data/caopre_all_t.csv`,
    236 tokens, 2021-11-06 to 2024-08-14, 145k rows) — real NSGA-II
    evolution across multiple batches, real accept/reject against a
    held-out validation window, real formula trees produced (e.g.
    `ts_kurt_window_7(EmaBest5)`, `ts_delta_window_8(ts_regbeta_window_35(
    ts_argmin_window_20(EmaBest5), meanWrong5))`) with real fitness values —
    confirmed genuinely functioning code, not a stub.

============================================================================
Security screening (same checks used for every adapter this session)
============================================================================
  - `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|subprocess\\.(call|
    run|Popen)|socket\\.|urllib|requests\\.(get|post)"` across every `.py`
    file: zero hits.
  - `pickle.load` appears exactly once (`main.py`, upstream's own optional
    "predict" mode), loading a `.pkl` file that upstream's own "train" mode
    wrote in the same run — not loading untrusted external data, and this
    adapter never calls that code path at all (it calls `GPProcess.run()`
    and `GPProcess.generate_factor()` directly, in-process).
  - `api_key`/`secret`/`password`/`token`/`credential`/`broker`/`alpaca`/
    `robinhood`/`binance` grep: zero hits anywhere in the codebase. This
    project needs **no external data source, no account, and no API key of
    any kind** — its entire input is the repo's own bundled CSV panel of
    236 Binance-perpetual-style token symbols (e.g. `BTCUSDT`), which is
    historical, pre-downloaded, and public-domain-adjacent research data,
    not a live feed or live account. This is the cleanest security profile
    of any adapter built this session (no brokerage risk at all, unlike the
    two real problems found elsewhere this session: FinGPT's unrelated
    `finogrid/` crypto-payments subtree, and a different candidate repo
    needing live brokerage credentials just to fetch data).
  - File tree is small (16 real files) and entirely on-topic for a genetic-
    programming factor miner (`cal/`, `genetic_process.py`,
    `evaluate_func.py`, `data_process.py`, `terminal_process.py`, `main.py`,
    bundled `data/`+`config/`) — no unrelated subtree merged under a
    misleadingly-named branch.
  - No LLM API key is used or needed anywhere in this adapter.

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n atlas_real python=3.11
    conda activate atlas_real
    pip install deap pandas numpy pydantic
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    # torch has a prebuilt CPU wheel for this platform/Python combo — no
    # cmake/Rust/conda-forge fallback was needed for this adapter (unlike
    # xgboost/lightgbm/pyarrow/libcst earlier this session).
    git clone --depth 1 \\
        https://github.com/Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining.git \\
        adapters/vendor/atlas-alpha-mining

Run the harness with that env active:
    conda activate atlas_real
    python CONTRACT/test_harness.py --adapter adapters/atlas_adapter.py

No upstream source was patched — only environment/dependency setup and
adapter-side glue were needed, so there is no patches/atlas-alpha-mining.diff.

============================================================================
Design notes / scope reductions (translation choices made by this adapter,
not upstream)
============================================================================
  - **Population/generation budget**: upstream's own `main.py` example uses
    `population_num=200, batch_size=10, generation=6` (20 batches × 6
    generations — likely tens of minutes). This adapter uses
    `population_num=40, batch_size=10, generation=2` (4 batches/"queues" ×
    2 generations, ~50-60s wall-clock in this sandbox) so a full run fits
    comfortably inside the harness's smoke/adapter.run() timeouts — still
    upstream's own unmodified `GPProcess.run()`, real NSGA-II selection,
    real Hall of Fame, real validation-set accept/reject filter, just a
    smaller, faster budget. Cached per requested `date` in-process (the
    harness calls `q3_signal()` directly and again via `adapter.run()` with
    the same date — same caching rationale as every other adapter this
    session).
  - **Point-in-time train/val/test windows**: derived from the requested
    `date` (not hardcoded), respecting no-lookahead: `train` covers
    [`date`-480d, `date`-120d], `val` covers [`date`-120d, `date`-30d],
    `test` covers [`date`-120d, `date`] (the test window's extra 90-day
    head-room *before* `date` is needed because upstream's own time-series
    operators use rolling windows up to 60 days — without that head-room,
    upstream's own `generate_factor()` returns `NaN` for the first ~60 rows
    of whatever window it's given; confirmed empirically in this sandbox).
    Both `date` and the derived boundaries are clamped into the bundled
    dataset's real coverage (`2021-11-06`..`2024-08-14`) since this is a
    static historical panel, not a live-updating feed — a request for a
    date outside that range is clamped to the nearest valid boundary and
    is therefore not truly point-in-time for that request (documented
    limitation, not silently wrong).
  - **Ticker-universe mismatch (same reinterpretation pattern
    `finrl_x_adapter.py` used for its NASDAQ-only universe)**: upstream's
    real universe is its own bundled 236-name crypto-perpetuals panel
    (e.g. `BTCUSDT`), not equities tickers. This adapter normalizes the
    requested `ticker` (`.upper()`, then also tries `+"USDT"`) and looks it
    up in that real panel. If it matches a real, currently-quoted token,
    the real evolved factor's value for that exact token/date is used. If
    it does not (e.g. the CONTRACT harness's own `"AAPL"` sample ticker),
    this adapter falls back to a fixed representative token (`BTCUSDT` —
    chosen because it is quoted across the entire bundled date range, so
    it never silently returns "no data") and says so explicitly in
    `supporting_evidence`, rather than raising or fabricating an
    equities-specific answer.
  - **`direction`/`strength`**: computed from the real evolved factor's
    cross-sectional percentile rank on the exact requested date, using the
    same top/bottom-20% convention upstream's own
    `evaluate_func.hedge_return_std_cal()` uses for its fitness metric:
    `LONG` if the token's factor value ranks in the top 20% that day,
    `SHORT` if bottom 20%, else `NEUTRAL`; `strength = abs(percentile-0.5)*2`
    (0 at the median, 1 at either extreme) — an adapter-side confidence
    proxy in the same family as `deepalpha_adapter.py`'s dispersion-based
    confidence and `finrl_x_adapter.py`'s rank-based strength, not an
    upstream-native score (upstream doesn't expose one directly).
  - **`expected_return`**: upstream's own unmodified `evaluate_func.evaluate()`
    called with `["Hedge_Return"]` on the real chosen factor's real values
    over the full scoped test window (top-20%-vs-bottom-20% average forward
    return, upstream's own metric, not reimplemented).
  - **`supporting_evidence`**: the real accepted formula strings (top 3 by
    real train-set fitness, drawn from across the multiple evolved
    batches/"queues", not hardcoded), plus an explicit note when the
    ticker-universe fallback above was used.
  - **`expected_horizon`**: set to `"1d"`, inferred from the bundled data's
    daily row cadence. The exact forward-return convention baked into the
    bundled `returns` column is not documented upstream (the data-generation
    script that produced `data/caopre_all_t.csv` is not part of this repo,
    only the resulting panel) — `"1d"` is a reasonable inference from the
    row cadence, not a confirmed upstream spec; disclosed here rather than
    asserted as fact.
  - **`signal_type`**: `FACTOR` (CONTRACT's designation for a discovered
    quantitative factor signal — matches the target description's "alpha
    factors" framing exactly).

============================================================================
v1 -> v2.0.0 schema migration notes (added during migration; the mechanism/
verification narrative above is from the original v1 build and is still
accurate — only the canonical field mapping below changed)
============================================================================
  - `SignalType` no longer exists in v2 at all; deleted. `signal_semantics`
    (free text) replaces it, describing the real `gp.generate_factor()`
    output as a continuous, unitless compiled-formula-tree score.
  - **`values: Dict[ticker, float]` (new, required)**: the real full
    cross-sectional snapshot from `gp.generate_factor(best_ind)` on the
    requested date (`factor_series.xs(asof_str, level="date").dropna()`),
    i.e. every real crypto-perpetual token's real factor value that day —
    upstream's own unmodified per-token output, NATIVE. Previously only the
    single resolved token's value was surfaced; the rest of this same real
    cross-section (up to ~236 tokens) was computed and then discarded.
  - `direction`/`strength` unchanged in derivation (same real percentile
    rank against the same real cross-section, matching upstream's own
    top/bottom-20% `hedge_return_std_cal` convention) but now computed
    directly from the new `values` dict and are `Optional` per v2.
  - `factor_expression` (new): `str(best_ind)`, the real DEAP formula-tree
    string for the best (highest train-fitness) accepted individual — a
    single top-level slot (v2 has no list), so the two runner-up formulas
    that were previously appended to `supporting_evidence` stay as
    `evidence` items (kind="factor_expression") rather than being folded
    into this field.
  - `supporting_evidence: List[str]` -> `evidence: Optional[List[EvidenceItem]]`:
    typed as `kind="universe_fallback"` (ticker/token-universe mismatch
    disclosure), `kind="cross_sectional_rank"` (the percentile-rank fact),
    `kind="factor_expression"` (each runner-up formula), and
    `kind="expected_return_diagnostic"` (the real `Hedge_Return` metric —
    see next bullet).
  - `expected_return: float` (v1) has no home in v2's
    `Q3Signal.expected_returns: Optional[Dict[str, float]]`: the real
    `evaluate_func.evaluate(..., ["Hedge_Return"])` value is a
    **universe/test-window-level** statistic (top-20%-vs-bottom-20% average
    forward return across the whole scoped test window), not a per-token
    expected return — populating a per-token dict with one shared aggregate
    number would misrepresent it as token-specific. Left out of
    `expected_returns` (stays `None`), disclosed instead as an `evidence`
    item.
  - `expected_horizon` (v1 top-level field) no longer exists in v2's
    `Q3Signal` — the "1d" cadence inference is disclosed in
    `signal_semantics`/`explanation` text instead of a dedicated field.
  - `explanation` (new): the same real, concrete percentile-rank fact
    string previously appended to `supporting_evidence` — not a fabricated
    template.
  - `confidence`: left `None` — no native or reliably-derivable confidence
    distinct from `strength` exists for this GP search.
  - `q3_signal(ticker, date)` -> `q3_signal(context: QueryContext)`: ticker
    now read from `context.targets[0]` (fed into the same
    `_resolve_token()` mapping onto the real bundled crypto-token universe),
    date from `context.data_cutoff`. `context` is echoed back unchanged into
    `Q3Signal(context=context, ...)` per the v2 contract.
  - `run()` is now overridden solely to attach a faithful `native_output`
    (the real best/runner-up formula strings, real train fitness values,
    the real factor snapshot, the real `Hedge_Return` metric, plus
    adapter-derived token-resolution diagnostics under a separate
    `adapter_derived` key) and the real wall-clock `latency_sec` — no
    business logic changed.

============================================================================
Capability-recovery pass (this round)
============================================================================
  - **Recovered (category 2 — real, already-public, previously truncated)**:
    `evidence` (kind="factor_expression") and `native_output.upstream.
    accepted_formulas` now report upstream's own COMPLETE validation-accepted
    individual set (`gp.run()`'s real `final_ind` return value, aliased
    `accepted`/`ranked` here) — every formula that passed the real
    Pareto-front selection + real validation-set accept/reject filter for
    this run, not just the top-3 previously kept. This list was already
    fully computed and already returned by the unmodified upstream call;
    only the adapter's own reporting was truncated.
  - **Limitation (category 3 — real, computed, but no public accessor)**:
    upstream's own `GPProcess.run()` (genetic_process.py:332-431) builds a
    real per-generation, per-batch DEAP `Logbook` (`tools.Statistics` over
    both fitness objectives + tree size: avg/std/min/max per generation,
    genetic_process.py:339-355,382-385) and a real per-batch
    `best_individual`/`best_fitness` (genetic_process.py:394-397) — but both
    are local variables inside `run()`, never assigned to `self` and never
    part of `run()`'s return value (`return final_ind`, line 431); they only
    ever reach a `print()` call. There is no documented/public API to
    retrieve the logbook or per-batch best-individual history after
    `run()` returns. Recovering this would require either monkey-patching
    `GPProcess.run()` to stash `logbook`/per-batch bests onto `self` before
    they go out of scope, or reimplementing `run()`'s own batch loop outside
    upstream's method — both excluded by CLAUDE.md's "don't monkey-patch or
    reimplement upstream trading/research logic" rule. Left unrecovered and
    disclosed here rather than reached into via a private-internals hack.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Direction, EvidenceItem, OutputScope, Q3Signal, QueryContext

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "atlas-alpha-mining"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

DATA_MIN = pd.Timestamp("2021-11-06")
DATA_MAX = pd.Timestamp("2024-08-14")

FALLBACK_TOKEN = "BTCUSDT"   # real, quoted across the entire bundled date range

# Scoped-down GA budget — see header "Population/generation budget"
POPULATION_NUM = 40
BATCH_SIZE = 10              # -> 4 batches ("queues") per run
GENERATION = 2
INITIAL_DEPTH = 2
MAX_DEPTH = 3
RANDOM_SEED = 42

TRAIN_LOOKBACK_DAYS = 480     # ~16 months of daily x 236-token history per training window
TRAIN_END_BUFFER_DAYS = 120
VAL_END_BUFFER_DAYS = 30
TEST_LOOKBACK_DAYS = 120      # rolling-window warm-up buffer (see header)

TRAIN_EVALUATIONS = ["Hedge_Return_Std", "Hedge_Return"]
VALID_EVALUATIONS = ["Hedge_Return_Std"]
TOP_PCT = 0.2                 # top/bottom 20% convention (matches upstream's own hedge_return_std_cal)

_GA_CACHE: dict = {}


def _clamp_asof(date: str) -> pd.Timestamp:
    asof = pd.Timestamp(date)
    lo = DATA_MIN + pd.Timedelta(days=TRAIN_LOOKBACK_DAYS + TRAIN_END_BUFFER_DAYS)
    hi = DATA_MAX
    if asof < lo:
        return lo
    if asof > hi:
        return hi
    return asof


def _run_ga(date: str) -> Tuple[object, list, pd.Timestamp]:
    """
    Real, unmodified upstream GPProcess.run() (DEAP-based genetic
    programming: multi-batch/"queue" population evolution, NSGA-II
    Darwinian selection, Hall of Fame, validation-set accept/reject),
    scoped down per header "Population/generation budget". Cached per
    requested date.
    Returns (gp_instance, accepted_individuals, asof_timestamp_used).
    """
    if date in _GA_CACHE:
        return _GA_CACHE[date]

    import warnings
    warnings.filterwarnings("ignore")

    from data_process import DataProcess     # upstream, unmodified
    from genetic_process import GPProcess    # upstream, unmodified

    asof = _clamp_asof(date)
    train_start = max(DATA_MIN, asof - pd.Timedelta(days=TRAIN_LOOKBACK_DAYS))
    train_end = asof - pd.Timedelta(days=TRAIN_END_BUFFER_DAYS)
    val_start = train_end
    val_end = asof - pd.Timedelta(days=VAL_END_BUFFER_DAYS)
    test_start = asof - pd.Timedelta(days=TEST_LOOKBACK_DAYS)
    test_end = asof

    data_pro = DataProcess(path=str(VENDOR_DIR / "data") + "/", data_name="caopre_all_t")
    train_data, val_data, test_data = data_pro.split(
        train_start.strftime("%Y-%m-%d"), train_end.strftime("%Y-%m-%d"),
        val_start.strftime("%Y-%m-%d"), val_end.strftime("%Y-%m-%d"),
        test_start.strftime("%Y-%m-%d"), test_end.strftime("%Y-%m-%d"),
    )

    gp = GPProcess(
        train_data=train_data, val_data=val_data, test_data=test_data,
        train_evaluation=TRAIN_EVALUATIONS, valid_evaluation=VALID_EVALUATIONS,
        population_num=POPULATION_NUM, arity=0, batch_size=BATCH_SIZE,
        generation=GENERATION, initial_depth=INITIAL_DEPTH, max_depth=MAX_DEPTH,
        random_seed=RANDOM_SEED, cals="all",
    )
    accepted = gp.run()
    if not accepted:
        raise RuntimeError(
            "Upstream GPProcess.run() accepted zero factors for this window — "
            "try a different date or a larger population/generation budget."
        )

    result = (gp, list(accepted), asof)
    _GA_CACHE[date] = result
    return result


def _resolve_token(ticker: str, universe: set) -> Tuple[str, bool]:
    """Map a CONTRACT ticker onto upstream's real crypto-token universe.
    Returns (token, was_exact_match) — see header "Ticker-universe mismatch"."""
    normalized = (ticker or "").strip().upper()
    for candidate in (normalized, normalized + "USDT"):
        if candidate in universe:
            return candidate, True
    return FALLBACK_TOKEN, False


class AtlasAdapter(BaseAdapter):
    name = "atlas"
    questions_answered = ["Q3"]
    upstream_repo = "https://github.com/Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining"
    requires_env = "atlas_real"

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        from evaluate_func import evaluate  # upstream, unmodified

        requested_ticker = (context.targets[0] if context.targets else FALLBACK_TOKEN) or FALLBACK_TOKEN
        date = context.data_cutoff or context.as_of

        gp, accepted, asof = _run_ga(date)
        asof_str = asof.strftime("%Y-%m-%d")

        ranked = sorted(accepted, key=lambda ind: ind.fitness.values[0], reverse=True)
        best_ind = ranked[0]

        factor_series = gp.generate_factor(best_ind)  # real upstream inference
        snap = factor_series.xs(asof_str, level="date").dropna()
        universe = set(snap.index)

        token, exact_match = _resolve_token(requested_ticker, universe)

        # `values`: the real full cross-sectional snapshot for the requested
        # date — upstream's own unmodified per-token output, NATIVE.
        values: Dict[str, float] = {t: float(v) for t, v in snap.items()}

        evidence: List[EvidenceItem] = []
        if not exact_match:
            evidence.append(EvidenceItem(
                kind="universe_fallback",
                value=(
                    f"Requested ticker '{requested_ticker}' is not one of the real "
                    f"tokens in this project's own bundled crypto-perpetuals "
                    f"panel; reporting the real evolved factor's signal for "
                    f"'{FALLBACK_TOKEN}' instead (see adapters/atlas_adapter.py "
                    f"header, 'Ticker-universe mismatch')."
                ),
                source="adapter (token universe membership check)",
            ))
        token = token if token in universe else FALLBACK_TOKEN

        if token not in values:
            # Even the fallback has no value for this exact date (thin
            # cross-section day).
            direction = Direction.NEUTRAL
            strength = 0.0
            explanation = (
                f"No valid (non-NaN) cross-sectional factor value for "
                f"'{token}' on {asof_str} in this run — reporting NEUTRAL/0 strength."
            )
            evidence.append(EvidenceItem(kind="missing_value", value=explanation, source="adapter"))
        else:
            n = len(snap)
            rank_position = int(snap.rank(ascending=False, method="min")[token])
            pct = (n - rank_position) / (n - 1) if n > 1 else 0.5
            is_top = pct >= (1 - TOP_PCT)
            is_bottom = pct <= TOP_PCT
            direction = Direction.LONG if is_top else Direction.SHORT if is_bottom else Direction.NEUTRAL
            strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))
            explanation = (
                f"'{token}' real evolved-factor value {snap[token]:.4f} ranks "
                f"{rank_position}/{n} ({pct:.0%} percentile) on {asof_str} "
                f"for formula '{str(best_ind)}' (train fitness="
                f"{best_ind.fitness.values[0]:.4f}). direction/strength are this "
                f"adapter's percentile-rank translation, matching upstream's own "
                f"top/bottom-20% hedge_return_std_cal convention, not an "
                f"upstream-native label."
            )
            evidence.append(EvidenceItem(
                kind="cross_sectional_rank",
                value=explanation,
                source="adapter_derived (percentile rank over gp.generate_factor output)",
            ))

        # Recovered (previously truncated to top-3): `accepted` (aliased here
        # as `ranked`) is the REAL, complete validation-accepted output of
        # upstream's own `GPProcess.run()` -- every formula that passed its
        # real Pareto-front selection + real validation-set accept/reject
        # filter for this run, not just the best one. Reporting only the
        # top 2 runner-ups discarded the rest of this same already-computed,
        # already-public list for no reason -- report the full real
        # per-run accepted-factor set here instead.
        for ind in ranked[1:]:
            evidence.append(EvidenceItem(
                kind="factor_expression",
                value=f"Also accepted: '{str(ind)}' (train fitness={ind.fitness.values[0]:.4f})",
                source="atlas GPProcess accepted individuals (full real validation-accepted set for this run, Pareto front / Hall of Fame)",
            ))

        # Real upstream metric, unmodified, on the full scoped test window.
        new_factor = gp.toolbox_multi.compile_test(expr=best_ind)
        hedge_return = float(evaluate(new_factor, gp.returns_test.clone(), ["Hedge_Return"])[0])
        evidence.append(EvidenceItem(
            kind="expected_return_diagnostic",
            value=(
                f"Real upstream Hedge_Return metric (top-20%-vs-bottom-20% average "
                f"forward return) for the best factor over the full scoped test "
                f"window: {hedge_return:.4f}. Universe-level statistic, not a "
                f"per-token expected return, so not populated into `expected_returns`."
            ),
            source="atlas evaluate_func.evaluate() (upstream, unmodified)",
        ))

        if not values:
            values = {token: 0.0}

        self._last_native_output = {
            "upstream": {
                "best_formula": str(best_ind),
                "best_train_fitness": float(best_ind.fitness.values[0]),
                "accepted_formulas": [
                    {"formula": str(ind), "train_fitness": float(ind.fitness.values[0])} for ind in ranked
                ],
                "asof": asof_str,
                "factor_snapshot": values,
                "hedge_return": hedge_return,
            },
            "adapter_derived": {
                "requested_ticker": requested_ticker,
                "resolved_token": token,
                "was_fallback": not exact_match,
            },
        }
        self._last_latency_sec = time.time() - t0

        return Q3Signal(
            context=context,
            signal_semantics=(
                "factor_value — real GP-evolved formula tree's cross-sectional output "
                "value (atlas GPProcess.generate_factor), a continuous factor score, "
                "not a return prediction or probability."
            ),
            values=values,
            score_scale="continuous, unitless (compiled DEAP formula-tree output over technical/statistical columns)",
            direction=direction,
            strength=strength,
            factor_expression=str(best_ind),
            evidence=evidence or None,
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
        native_output (and real wall-clock latency) captured as a side effect
        of the real q3_signal() call BaseAdapter.run() makes internally."""
        self._last_native_output = None
        self._last_latency_sec = 0.0
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        updates = {}
        if native_output is None and self._last_native_output:
            updates["native_output"] = self._last_native_output
        if self._last_latency_sec:
            updates["run"] = result.run.model_copy(update={"latency_sec": self._last_latency_sec})
        if updates:
            result = result.model_copy(update=updates)
        return result

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.CROSS_SECTION,
            targets=[FALLBACK_TOKEN],
        )
        result = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = result is not None
        if result is not None:
            checks["context_echoed_unchanged"] = result.context == context
            checks["values_nonempty"] = len(result.values) > 0
            checks["direction_is_valid"] = result.direction in ("LONG", "SHORT", "NEUTRAL", None)
            checks["strength_in_range"] = result.strength is None or 0.0 <= result.strength <= 1.0
            checks["evidence_nonempty"] = bool(result.evidence)
            checks["factor_expression_set"] = bool(result.factor_expression)
            # Recovered-capability check: the full accepted-formula set (not
            # just a top-3 truncation) should now be present whenever more
            # than one factor was accepted this run.
            accepted_formulas = (self._last_native_output or {}).get("upstream", {}).get("accepted_formulas", [])
            factor_expr_evidence = [e for e in (result.evidence or []) if e.kind == "factor_expression"]
            checks["accepted_formulas_native_output_present"] = bool(accepted_formulas)
            checks["evidence_covers_full_accepted_set"] = len(factor_expr_evidence) == max(0, len(accepted_formulas) - 1)
        return checks
