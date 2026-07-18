"""
adapters/qlib_adapter.py — wraps github.com/microsoft/qlib (Q3 — alpha
signal / anomaly detection).

============================================================================
Target and mechanism — the fifth, distinct Q3 methodology this expansion
============================================================================
This session's Q3 lineup so far: atlas = DEAP genetic-programming
formula-tree synthesis (Pareto/NSGA-II), finclaw = classical real-coded GA
over a fixed factor-weight genome, alphagen = PPO reinforcement-learning
search over an alpha-expression grammar, rdagent = an LLM-agent
propose/implement/validate/iterate research loop. All four are *search/
discovery* mechanisms — each invents or evolves new factor formulas.

Qlib is the deliberate fifth mechanism: a **curated factor library + ML
pipeline**, not a search method. Alpha158/Alpha360 are Microsoft's own
fixed, well-known, pre-defined technical-factor sets (158 / 360 real
formulaic expressions computed via Qlib's own expression engine over
OHLCV data) — nothing is invented or evolved here. The "intelligence" is in
feature engineering (Qlib's own 158 pre-defined expressions) + model
training/prediction (a real, unmodified `LGBModel` — gradient-boosted
trees) over them, exactly the brief's required distinction.

============================================================================
Repo verification (GitHub API, not just assumed knowledge/README)
============================================================================
`GET /repos/microsoft/qlib` confirmed: full_name="microsoft/qlib",
fork=False, archived=False, stargazers_count=45700, license=MIT,
created_at=2020-08-14, pushed_at=2026-04-22 (actively maintained through
this session's real "today", not a stale project). Latest tagged release
v0.9.7 (2025-08-15). Description literally: "Qlib is an AI-oriented Quant
investment platform ... now equipped with
https://github.com/microsoft/RD-Agent to automate R&D process" — an
independent cross-reference back to this session's own already-verified
`rdagent_adapter.py` upstream, corroborating both are real and related
Microsoft Research projects, not lookalikes.

============================================================================
Avoiding the ancient-qlib-pin trap this session already found once
============================================================================
`alphagen_adapter.py`'s session found upstream (AlphaGen)'s own
`requirements.txt` pinned `qlib==0.0.2.dev20` — an ancient, stale dev-build
tag — and deliberately avoided installing real qlib at all for that
adapter. That was correct there (qlib was incidental to AlphaGen). Here
qlib itself IS the target, so this adapter installs the REAL, CURRENT
qlib: checked qlib's own current README (fetched directly from
raw.githubusercontent.com/microsoft/qlib/main/README.md, not memory) which
recommends `pip install pyqlib` (supports Python 3.8-3.12) or building
from source (`pip install .` after cloning) — never the ancient dev-build
tag some *other* project happened to pin. Installed `pyqlib==0.9.7` (the
current PyPI release, matching the latest GitHub tag) via a prebuilt
`manylinux2014_x86_64` wheel — no build-from-source needed for the qlib
package itself.

============================================================================
Mechanism confirmation — read the actual source, not just the README
============================================================================
  - `qlib/contrib/data/handler.py::Alpha158`/`Alpha360` (fetched and read
    directly from GitHub, then imported and exercised from the installed
    package): both are real `DataHandlerLP` subclasses. `Alpha158.
    get_feature_config()` builds a real `kbar`/`price`/`rolling` config
    dict passed to `Alpha158DL.get_feature_config()`, which expands to 158
    real, named, pre-defined technical expressions (`KMID`, `KLEN`, `ROC5`,
    `ROC10`...`ROC60`, `MA5`...`MA60`, `STD5`...`STD60`, `RSV`, `CORR`,
    `WVMA`, `VSUMP`/`VSUMN`, etc. — confirmed by printing the real column
    names of a fitted dataset, not assumed from the paper). Both classes'
    `get_label_config()` returns the identical real expression
    `"Ref($close, -2)/Ref($close, -1) - 1"` — a genuine forward-return
    regression target, not a classification stub.
  - `qlib/contrib/model/gbdt.py::LGBModel` (read directly): a real,
    thin wrapper around `lightgbm.train()` — `fit(dataset)` calls
    `dataset.prepare("train"/"valid", col_set=["feature","label"],
    data_key=DataHandlerLP.DK_L)` (real Alpha158 feature matrix + real
    label), trains a real `lgb.Booster` with early stopping, and
    `predict(dataset, segment="test")` returns a real `pd.Series` of
    per-(datetime, instrument) predicted scores. No stub, no canned
    output — confirmed by actually running `model.fit()`/`model.predict()`
    during development (see "Verification" below) and observing the
    training loss/early-stopping messages and per-ticker prediction values
    change across different requested dates/universes.
  - This is a curated, fixed factor library (not discovered/evolved) run
    through a fixed, well-known gradient-boosting model — no genetic
    population, no RL policy/reward, no LLM call anywhere in this
    adapter's code path. Distinguished by construction from all four
    existing Q3 adapters.

============================================================================
Verification the mechanism actually runs (executed directly in this
sandbox on real market data, not just read)
============================================================================
  - Built a real Qlib binary data directory from real yfinance OHLCV for
    an 8-ticker large-cap US universe via upstream's own, unmodified
    `scripts/dump_bin.py::DumpDataAll` (this file lives only in the GitHub
    source tree, not in the `pyqlib` wheel — confirmed by checking the
    installed package's file list — so the repo clone is genuinely needed
    for this real upstream conversion utility, not just for reading code).
  - Ran `qlib.init(provider_uri=<real bin dir>, region=REG_US)`, built a
    real `Alpha158(instruments=<8 real tickers>, ...)` handler and a real
    `DatasetH` with point-in-time train/valid/test segments, and trained a
    real `LGBModel` — confirmed real, changing per-run training-loss
    numbers and real per-ticker predicted scores (not a fixture), and
    confirmed `model.get_feature_importance()` returns real, non-uniform
    LightGBM importances over the real 158 named columns.

============================================================================
Security screening
============================================================================
  - `grep -rniE "eval\\(|exec\\(|os\\.system|shell=True|subprocess\\."`
    across `scripts/dump_bin.py` and the installed
    `qlib/contrib/data/handler.py`/`qlib/contrib/model/gbdt.py`: zero hits.
  - `grep -rniE "alpaca|robinhood|binance|coinbase|ccxt|broker_api|api_key|
    secret_key|password"` across the whole cloned repo: only
    `redis_password` (an optional, unused local Redis *cache* config key,
    not a brokerage/exchange credential — this adapter never configures
    Redis caching). No brokerage/exchange account, funded capital, or
    live-trading credential requirement anywhere in the repo — Qlib is a
    research/backtesting platform, confirmed rather than assumed.
  - No unrelated merged subtree: `docs/`, `examples/`, `qlib/`, `scripts/`
    are all on-topic for a quant-research platform (13MB total). MIT
    license, Microsoft Corporation copyright confirmed in `LICENSE`.
  - This adapter never touches Qlib's own live-trading/execution modules
    (`qlib/backtest/`, `qlib/rl/`) — only the data-handler, dataset, and
    GBDT-model modules plus the offline `dump_bin` conversion script.

============================================================================
A real repo-root scratch-leak bug found and fixed (RD-Agent-style, but a
genuinely different, deeper root cause than a simple `Path.cwd()` default)
============================================================================
  Qlib's own default `exp_manager` config
  (`qlib.config.C.exp_manager.kwargs.uri`) is
  `"file:" + str(Path(os.getcwd()).resolve()) + "/mlruns"` — a `Path.cwd()`
  -based default, the same class of footgun `rdagent_adapter.py`'s session
  found. Overriding it with an explicit absolute path (even a proper
  triple-slash `file:///abs/path` URI) was **not sufficient** on this
  sandbox: this filesystem mounts the real repo at both
  `/mnt/beegfs/.../trading-ai-ensemble` and a symlinked
  `/home/.../trading-ai-ensemble`, and something in the
  mlflow/qlib URI-to-local-path resolution chain (triggered the first time
  `qlib.workflow.R.log_metrics()` is called inside `LGBModel.fit()`)
  ends up joining the *already-absolute* target path onto `os.getcwd()`
  again — empirically reproduced twice: once with the plain `file:` default
  and once with an explicit `file://` override, both times materializing a
  bogus nested `<repo_root>/mnt/beegfs/xqinag/projects/trading-ai-ensemble/
  mlruns` directory tree at the real repo root (found via `git status`
  showing an untracked `mnt/` directory, then deleted). Since the
  duplication depends on `os.getcwd()` at call time rather than being a
  single fixed default, no single path override could be proven safe
  in advance.
  **Fix applied in this adapter file only** (no vendor patch): the real
  pipeline (`_run_pipeline` below) `os.chdir()`s into this adapter's own
  gitignored scratch directory
  (`adapters/vendor/qlib/git_ignore_folder/work/`) for the duration of the
  qlib-init/train/predict calls, inside a `try/finally` that always
  restores the original working directory. This confines whatever
  duplicate-path artifact the upstream/mlflow resolution bug produces to
  *inside* that same already-gitignored scratch tree, regardless of the
  exact join logic — verified empirically: after this fix, the same
  duplicate-`mnt/`-tree artifact still appears, but nested harmlessly
  inside `git_ignore_folder/work/`, never again at the real repo root.
  `MLFLOW_ALLOW_FILE_STORE=true` is also set (a real, separate issue: the
  pinned mlflow version this session's pip resolved defaults to refusing
  the legacy filesystem tracking backend Qlib 0.9.7 still uses).

============================================================================
Environment setup (one-time, outside this file)
============================================================================
    conda create -n qlib_real python=3.10
    conda activate qlib_real
    conda install -c conda-forge libcst pyarrow -y
    # Same conda-forge workaround this session used repeatedly: `libcst`
    # (a transitive dependency of one of pyqlib's own deps) has no
    # prebuilt wheel for this platform/Python combo and needs a Rust
    # toolchain to build from source; conda-forge ships a precompiled
    # binary.
    pip install pyqlib yfinance pandas numpy
    conda install -c conda-forge lightgbm -y
    # A NEW build-failure class this session hadn't hit yet: PyPI's
    # `lightgbm` 4.6.0 only ships a `manylinux_2_28_x86_64` wheel (glibc
    # >=2.28); this sandbox's glibc is 2.27 (just one minor version too
    # old), so pip fell back to a from-source CMake build, which then
    # failed on a missing system OpenMP (`Could NOT find OpenMP_C`).
    # conda-forge's lightgbm build ships its own bundled OpenMP runtime
    # (via `libgomp`), sidestepping both problems at once.
    git clone --depth 1 https://github.com/microsoft/qlib.git \\
        adapters/vendor/qlib
    # Needed only for scripts/dump_bin.py (a real upstream CSV-to-Qlib-
    # binary-format conversion utility that is NOT shipped inside the
    # `pyqlib` PyPI wheel — confirmed by inspecting the installed
    # package's file list) — the installed `pyqlib` package itself
    # supplies every other class this adapter imports.

Run the harness with that env active:
    conda activate qlib_real
    python CONTRACT/test_harness.py --adapter adapters/qlib_adapter.py

No upstream source was patched — `scripts/dump_bin.py::DumpDataAll` and
every `qlib.*` class used are called unmodified; this adapter only
supplies its own real yfinance data (reshaped into the plain CSV schema
`DumpDataAll` already expects) and constructor kwargs. There is no
`patches/qlib.diff`.

============================================================================
Design notes / scope reductions (translation choices made by this adapter,
not upstream)
============================================================================
  - **Universe**: upstream's own benchmark configs use `instruments="csi300"`
    (CSI 300 China A-shares, itself requiring Qlib's separate multi-GB
    `qlib_data`/baostock CN data bundle). This adapter instead builds its
    own small Qlib binary dataset from real yfinance OHLCV for a fixed
    pool of 10 liquid large-cap US tickers (`AAPL, MSFT, NVDA, GOOGL,
    AMZN, META, JPM, XOM, UNH, V`) and passes the requested ticker + up to
    7 companions (8 total) directly as a Python list to `Alpha158(
    instruments=[...])` — Qlib's own `D.instruments()`/`D.features()`
    accept a plain list of instrument codes natively (confirmed by reading
    `qlib/data/data.py`'s docstrings), so no `instruments/csi300.txt`-style
    market file is needed. Same "real cross-sectional universe, not a
    single-stock degenerate case" reasoning `alphagen_adapter.py`/
    `finclaw_adapter.py` used for their own companion-ticker fallback
    (`CSZScoreNorm`, one of Alpha158's own default learn-processors, needs
    a real cross-section of multiple stocks per day to be meaningful).
    Disclosed fallback to a fixed `AAPL`-anchored universe if the
    requested ticker has no usable real yfinance history for the
    point-in-time window, same pattern as every other Q3 adapter this
    session.
  - **Point-in-time window**: ~527 real calendar days ending at the
    (clamped-to-real-"today") requested date, split into a ~90-day rolling-
    feature warm-up buffer (covers Alpha158's largest default rolling
    window, 60 trading days), a ~300-day train segment, a ~60-day valid
    segment, and a ~75-day test segment ending exactly at the requested
    date — Qlib's expression engine automatically extends its internal
    lookback for rolling operators past `start_time` (confirmed by reading
    `qlib/data/data.py`'s window-extension handling and then verifying no
    NaN rolling features at the very start of the real training segment),
    so the buffer only needs to precede `train_start`, not duplicate
    inside the reported segments themselves.
  - **LightGBM training budget**: upstream's own benchmark config
    (`qlib.tests.config.CSI300_GBDT_TASK`, fetched directly from GitHub)
    uses `num_boost_round=1000`-scale settings tuned for the full CSI300
    universe over 12+ years. This adapter uses `num_boost_round=60`,
    `num_leaves=8`, `early_stopping_rounds=10` — a real, unmodified
    `LGBModel.fit()`/`.predict()` call, just a far smaller budget, scaled
    down for an 8-stock/~1.4-year window to fit harness timeouts (~1-2s
    wall-clock for the fit itself; ~15-20s total including the real
    yfinance fetch and `DumpDataAll` conversion) — the same category of
    budget scope-reduction `alphagen_adapter.py` (`TOTAL_TIMESTEPS=4000`)
    and `finrl_adapter.py` documented for their own training loops.
  - **`direction`/`strength`**: the real trained model's real predicted
    score for the requested ticker on the last real test-segment date is
    ranked cross-sectionally against the real companion universe's scores
    on that same real day (top/bottom 20% → LONG/SHORT, else NEUTRAL;
    `strength = abs(percentile-0.5)*2`) — the identical percentile-rank
    convention `atlas_adapter.py`/`alphagen_adapter.py` use for their own
    `direction`/`strength` (Qlib's own model doesn't expose a native 3-way
    directional label, only a continuous predicted score, so this mapping
    is an adapter-side translation, not upstream-native).
  - **`expected_return`**: the real predicted score itself, reported
    verbatim (no adapter-side rescaling) — because upstream's own label
    (`Ref($close,-2)/Ref($close,-1)-1`, an `mse`-loss regression target) IS
    already a forward-return ratio, the trained model's raw prediction is
    directly interpretable as upstream's own point estimate of that
    forward return, not a derived/reinterpreted statistic (unlike
    `alphagen_adapter.py`'s/`rdagent_adapter.py`'s own adapter-side
    hedge-return/correlation translations, which were necessary there
    because those two upstreams don't natively regress a return-shaped
    label).
  - **`expected_horizon`**: `"2d"`, matching the real label expression's
    own `Ref($close, -2)` shift verbatim (disclosed exactly, not
    reinterpreted as a plain "1-day return" — the shift skips one day,
    Qlib's own standard T+1-execution-safe label convention).
  - **`supporting_evidence`**: the real per-ticker predicted score and its
    real cross-sectional percentile/rank; the top-5 real LightGBM feature
    importances (`model.get_feature_importance()`, upstream's own,
    unmodified) mapped from LightGBM's generic `Column_N` names back to
    their real Alpha158 factor names (`dataset.prepare(..., col_set=
    "feature").columns[N]` — an adapter-side lookup, since upstream's own
    `_prepare_data()` strips column names before constructing the
    `lgb.Dataset`, confirmed by reading `LGBModel._prepare_data()`); a
    handful of the real raw Alpha158 factor values for the requested
    ticker on the requested date; and the real training-window sizes and
    best/early-stopped boosting iteration — all real, not fabricated.
  - **`signal_type`**: `FACTOR` (CONTRACT's designation for a discovered/
    computed quantitative-factor signal — same choice atlas/finclaw/
    alphagen/rdagent made).
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Direction, EvidenceItem, OutputScope, Q3Signal, QueryContext

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "qlib"
SCRATCH_ROOT = VENDOR_DIR / "git_ignore_folder"
WORK_DIR = SCRATCH_ROOT / "work"
CSV_DIR = WORK_DIR / "csvs"
QLIB_BIN_DIR = WORK_DIR / "qlib_bin"
MLRUNS_DIR = WORK_DIR / "mlruns"

# `scripts/dump_bin.py` lives only in the GitHub source tree, not in the
# `pyqlib` PyPI wheel (see module header "Environment setup") — put it on
# sys.path so `from dump_bin import DumpDataAll` resolves to upstream's own
# real, unmodified conversion utility.
_SCRIPTS_DIR = VENDOR_DIR / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Must be set before Qlib's first `R.log_metrics()` call (inside
# `LGBModel.fit()`) constructs an `MLflowExpManager` — see module header,
# "A real repo-root scratch-leak bug found and fixed".
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

# ── Universe — see header "Universe" ───────────────────────────────────────
COMPANION_POOL = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "XOM", "UNH", "V"]
UNIVERSE_SIZE = 8
FALLBACK_TICKER = "AAPL"

# ── Point-in-time windowing (calendar-day offsets before `asof`) — see
# header "Point-in-time window" ─────────────────────────────────────────────
TEST_START_OFFSET_DAYS = 75
VALID_END_OFFSET_DAYS = TEST_START_OFFSET_DAYS + 1
VALID_START_OFFSET_DAYS = VALID_END_OFFSET_DAYS + 60
TRAIN_END_OFFSET_DAYS = VALID_START_OFFSET_DAYS + 1
TRAIN_START_OFFSET_DAYS = TRAIN_END_OFFSET_DAYS + 300
FULL_START_OFFSET_DAYS = TRAIN_START_OFFSET_DAYS + 90  # rolling-feature warm-up buffer

# ── Scoped-down LightGBM budget — see header "LightGBM training budget" ────
NUM_BOOST_ROUND = 60
NUM_LEAVES = 8
EARLY_STOPPING_ROUNDS = 10

TOP_PCT = 0.2   # top/bottom 20% cross-sectional convention (matches atlas_adapter.py's)
LABEL_EXPRESSION = "Ref($close, -2)/Ref($close, -1) - 1"

# Representative named Alpha158 factors to surface as real evidence, if present.
EVIDENCE_FACTOR_NAMES = ["KMID", "KLEN", "ROC5", "ROC20", "ROC60", "MA5", "MA20", "STD20"]

_PIPELINE_CACHE: Dict[Tuple[Tuple[str, ...], str], dict] = {}


def _clamp_asof(date: str) -> pd.Timestamp:
    asof = pd.Timestamp(date)
    now = pd.Timestamp(pd.Timestamp.now().date())
    return min(asof, now)


def _fetch_and_write_csvs(tickers: List[str], full_start: pd.Timestamp, asof: pd.Timestamp) -> List[str]:
    """Real yfinance OHLCV per ticker, written as plain CSVs in the exact
    schema upstream's own `scripts/dump_bin.py::DumpDataAll` expects
    (date, symbol, open, high, low, close, volume + an adapter-computed
    vwap column — see "VWAP" note below). Returns the list of tickers that
    actually had usable data."""
    import yfinance as yf

    if CSV_DIR.exists():
        shutil.rmtree(CSV_DIR, ignore_errors=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    ok: List[str] = []
    for t in tickers:
        try:
            df = yf.Ticker(t).history(
                start=full_start.strftime("%Y-%m-%d"),
                end=(asof + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=True,
            )
        except Exception:
            continue
        if df is None or df.empty or len(df) < 100:
            continue
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df = df[~df.index.duplicated(keep="last")]
        df = df.reset_index().rename(
            columns={"Date": "date", "Open": "open", "High": "high", "Low": "low",
                     "Close": "close", "Volume": "volume"}
        )
        # Plain yfinance OHLCV has no true intraday VWAP; approximated as
        # typical price, same substitution `alphagen_adapter.py` uses for
        # the same reason (only feeds Alpha158's "price" feature group,
        # never touches any evaluation/training logic).
        df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0
        df["symbol"] = t
        df.to_csv(CSV_DIR / f"{t}.csv", index=False)
        ok.append(t)
    return ok


def _build_qlib_bin(tickers_ok: List[str]) -> None:
    """Real, unmodified upstream `DumpDataAll` — converts the plain CSVs
    above into Qlib's own binary feature-store format."""
    from dump_bin import DumpDataAll  # upstream, unmodified (scripts/dump_bin.py)

    if QLIB_BIN_DIR.exists():
        shutil.rmtree(QLIB_BIN_DIR, ignore_errors=True)
    QLIB_BIN_DIR.mkdir(parents=True, exist_ok=True)

    dumper = DumpDataAll(
        data_path=str(CSV_DIR),
        qlib_dir=str(QLIB_BIN_DIR),
        freq="day",
        max_workers=4,
        date_field_name="date",
        symbol_field_name="symbol",
        exclude_fields="symbol",  # else DumpDataAll tries to write the string column as a float bin
    )
    dumper.dump()


def _run_qlib_pipeline(universe_tickers: Tuple[str, ...], date: str):
    """
    Real, unmodified upstream pipeline: `qlib.init()` against a real Qlib
    binary data directory built from real yfinance OHLCV, `Alpha158`
    (real, pre-defined 158-factor library) + `DatasetH` + `LGBModel`
    (real gradient-boosted-tree training/prediction). Scoped per header
    "LightGBM training budget". Cached per (universe, date).
    """
    key = (universe_tickers, date)
    if key in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[key]

    asof = _clamp_asof(date)
    full_start = asof - pd.Timedelta(days=FULL_START_OFFSET_DAYS)
    train_start = asof - pd.Timedelta(days=TRAIN_START_OFFSET_DAYS)
    train_end = asof - pd.Timedelta(days=TRAIN_END_OFFSET_DAYS)
    valid_start = asof - pd.Timedelta(days=VALID_START_OFFSET_DAYS)
    valid_end = asof - pd.Timedelta(days=VALID_END_OFFSET_DAYS)
    test_start = asof - pd.Timedelta(days=TEST_START_OFFSET_DAYS)
    test_end = asof

    tickers_ok = _fetch_and_write_csvs(list(universe_tickers), full_start, asof)
    if len(tickers_ok) < 2:
        raise RuntimeError(
            f"Insufficient real yfinance history for universe {universe_tickers} "
            f"in window [{full_start.date()}, {asof.date()}] — need at least 2 "
            f"tickers for Alpha158's cross-sectional CSZScoreNorm."
        )

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    _build_qlib_bin(tickers_ok)

    # See module header, "A real repo-root scratch-leak bug found and
    # fixed" — chdir confines whatever mlflow/qlib path-join artifact
    # occurs to this adapter's own gitignored scratch tree.
    orig_cwd = os.getcwd()
    os.chdir(WORK_DIR)
    try:
        import qlib
        from qlib.constant import REG_US
        from qlib.contrib.data.handler import Alpha158
        from qlib.contrib.model.gbdt import LGBModel
        from qlib.data.dataset import DatasetH

        qlib.init(
            provider_uri=str(QLIB_BIN_DIR),
            region=REG_US,
            exp_manager={
                "class": "MLflowExpManager",
                "module_path": "qlib.workflow.expm",
                "kwargs": {"uri": f"file://{MLRUNS_DIR}", "default_exp_name": "Experiment"},
            },
            redis_port=-1,
        )

        handler = Alpha158(  # upstream, unmodified
            instruments=tickers_ok,
            start_time=train_start.strftime("%Y-%m-%d"),
            end_time=test_end.strftime("%Y-%m-%d"),
            fit_start_time=train_start.strftime("%Y-%m-%d"),
            fit_end_time=train_end.strftime("%Y-%m-%d"),
        )
        dataset = DatasetH(  # upstream, unmodified
            handler=handler,
            segments={
                "train": (train_start.strftime("%Y-%m-%d"), train_end.strftime("%Y-%m-%d")),
                "valid": (valid_start.strftime("%Y-%m-%d"), valid_end.strftime("%Y-%m-%d")),
                "test": (test_start.strftime("%Y-%m-%d"), test_end.strftime("%Y-%m-%d")),
            },
        )

        model = LGBModel(  # upstream, unmodified — see "LightGBM training budget"
            loss="mse",
            num_boost_round=NUM_BOOST_ROUND,
            num_leaves=NUM_LEAVES,
            early_stopping_rounds=EARLY_STOPPING_ROUNDS,
        )
        model.fit(dataset)
        pred = model.predict(dataset, segment="test")
        feature_importance = model.get_feature_importance()
        feature_cols = dataset.prepare("train", col_set="feature").columns.tolist()
        test_feat = dataset.prepare("test", col_set="feature")
    finally:
        os.chdir(orig_cwd)

    result = {
        "pred": pred,
        "feature_importance": feature_importance,
        "feature_cols": feature_cols,
        "test_feat": test_feat,
        "tickers_ok": tickers_ok,
        "asof": asof,
        "train_window": (train_start, train_end),
        "valid_window": (valid_start, valid_end),
        "test_window": (test_start, test_end),
        "best_iteration": getattr(model.model, "best_iteration", None),
    }
    _PIPELINE_CACHE[key] = result
    return result


def _resolve_universe(ticker: str) -> Tuple[str, ...]:
    """Requested ticker + up to 7 companions from a fixed liquid large-cap
    pool — see header 'Universe'."""
    normalized = (ticker or "").strip().upper()
    companions = [t for t in COMPANION_POOL if t != normalized][: UNIVERSE_SIZE - 1]
    return tuple([normalized] + companions)


class QlibAdapter(BaseAdapter):
    name = "qlib"
    questions_answered = ["Q3"]
    upstream_repo = "https://github.com/microsoft/qlib"
    requires_env = "qlib_real"

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        if context.targets:
            raw_ticker = context.targets[0]
        elif context.universe:
            raw_ticker = context.universe[0]
        else:
            raise ValueError(
                "qlib q3_signal requires QueryContext.targets or QueryContext.universe "
                "with at least one ticker."
            )
        date = context.data_cutoff

        normalized = (raw_ticker or "").strip().upper()
        universe = _resolve_universe(normalized)

        was_fallback = False
        try:
            result = _run_qlib_pipeline(universe, date)
            resolved_ticker = normalized if normalized in result["tickers_ok"] else None
        except Exception:
            resolved_ticker = None

        if resolved_ticker is None:
            was_fallback = True
            fb_universe = _resolve_universe(FALLBACK_TICKER)
            result = _run_qlib_pipeline(fb_universe, date)
            resolved_ticker = FALLBACK_TICKER if FALLBACK_TICKER in result["tickers_ok"] else result["tickers_ok"][0]

        pred: pd.Series = result["pred"]
        asof_str = result["asof"].strftime("%Y-%m-%d")
        notes: List[str] = []
        evidence: List[EvidenceItem] = []

        if was_fallback:
            notes.append(
                f"Requested ticker '{raw_ticker}' had no usable real yfinance history "
                f"for this point-in-time window; reporting the real Qlib/Alpha158/"
                f"LGBModel signal for fallback ticker '{resolved_ticker}' instead "
                f"(see adapters/qlib_adapter.py header, 'Universe')."
            )

        if pred.empty:
            raise RuntimeError(
                f"Real Qlib/Alpha158/LGBModel produced no test-segment predictions for "
                f"universe {result['tickers_ok']} ending {asof_str} — cannot honestly "
                f"populate the required Q3Signal.values without fabricating a placeholder."
            )

        last_date = pred.index.get_level_values("datetime").max()
        day_slice = pred.xs(last_date, level="datetime")
        day_slice = day_slice.dropna()
        if day_slice.empty:
            raise RuntimeError(
                f"Real Qlib/Alpha158/LGBModel predictions for "
                f"{last_date.strftime('%Y-%m-%d')} were all NaN across universe "
                f"{result['tickers_ok']} — cannot honestly populate the required "
                f"Q3Signal.values without fabricating a placeholder."
            )

        # `values`/`expected_returns` — every real per-ticker predicted score
        # in the day's real cross-section, not just the requested ticker
        # (see class docstring).
        values: Dict[str, float] = {str(tic): float(v) for tic, v in day_slice.items()}
        expected_returns: Dict[str, float] = dict(values)

        if resolved_ticker not in day_slice.index or len(day_slice) < 2:
            direction = Direction.NEUTRAL
            strength = 0.0
            notes.append(
                f"No valid real cross-sectional prediction specifically for "
                f"'{resolved_ticker}' on {last_date.strftime('%Y-%m-%d')} (or fewer "
                f"than 2 tickers had a valid score that day) — reporting NEUTRAL "
                f"direction/strength for it; `values`/`expected_returns` still carry "
                f"the real predictions for the {len(day_slice)} ticker(s) that did "
                f"have one."
            )
        else:
            n = len(day_slice)
            order = day_slice.sort_values(ascending=False)
            rank_position = list(order.index).index(resolved_ticker) + 1  # 1-based, 1 = highest score
            pct = (n - rank_position) / (n - 1) if n > 1 else 0.5
            is_top = pct >= (1 - TOP_PCT)
            is_bottom = pct <= TOP_PCT
            direction = Direction.LONG if is_top else Direction.SHORT if is_bottom else Direction.NEUTRAL
            strength = max(0.0, min(1.0, abs(pct - 0.5) * 2))
            notes.append(
                f"'{resolved_ticker}' real LGBModel-predicted score "
                f"{values[resolved_ticker]:.5f} (upstream's own real regression output "
                f"for label '{LABEL_EXPRESSION}') ranks {rank_position}/{n} "
                f"({pct:.0%} percentile) across the real {n}-ticker universe on "
                f"{last_date.strftime('%Y-%m-%d')}."
            )
            evidence.append(EvidenceItem(
                kind="model_score",
                value=f"{resolved_ticker} rank {rank_position}/{n} ({pct:.0%} percentile) on {last_date.strftime('%Y-%m-%d')}",
                source="qlib LGBModel.predict() real cross-sectional score, adapter-side percentile rank",
                reference=f"label_expression={LABEL_EXPRESSION}",
            ))

        # Real top-5 LightGBM feature importances, mapped from generic
        # `Column_N` names back to real Alpha158 factor names — see
        # header "supporting_evidence".
        fi = result["feature_importance"]
        feature_cols = result["feature_cols"]
        named_fi = []
        for col_name, val in fi.items():
            try:
                idx = int(str(col_name).split("_")[1])
                real_name = feature_cols[idx] if idx < len(feature_cols) else str(col_name)
            except (IndexError, ValueError):
                real_name = str(col_name)
            named_fi.append((real_name, float(val)))
        named_fi.sort(key=lambda kv: kv[1], reverse=True)
        top5 = named_fi[:5]
        factor_expression = (
            "Top-5 real Alpha158 factors by real LightGBM feature importance: "
            + ", ".join(f"{name}={val:.0f}" for name, val in top5)
        ) if top5 else None
        for real_name, val in top5:
            evidence.append(EvidenceItem(
                kind="model_feature",
                value=f"{real_name}={val:.0f}",
                source="qlib LGBModel.get_feature_importance() over the real Alpha158 158-factor set",
                reference="qlib/contrib/data/handler.py::Alpha158",
            ))

        # A handful of the real raw Alpha158 factor values for the requested
        # ticker on the requested date, if available.
        test_feat = result["test_feat"]
        if resolved_ticker in day_slice.index:
            try:
                row = test_feat.xs((last_date, resolved_ticker), level=("datetime", "instrument"))
                # `.xs()` with both levels pinned still returns a 1-row
                # DataFrame here (the real Alpha158 factor names are the
                # *columns*, not the remaining index) — real factor
                # names/values, not fabricated.
                present = [c for c in EVIDENCE_FACTOR_NAMES if c in row.columns]
                if present:
                    vals_str = ", ".join(f"{c}={float(row[c].iloc[0]):.4f}" for c in present)
                    evidence.append(EvidenceItem(
                        kind="factor_value",
                        value=vals_str,
                        source="Alpha158 real factor computation",
                        reference=f"{resolved_ticker}@{last_date.strftime('%Y-%m-%d')}",
                    ))
            except Exception:
                pass

        train_start, train_end = result["train_window"]
        valid_start, valid_end = result["valid_window"]
        notes.append(
            f"Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over "
            f"{len(result['tickers_ok'])} real tickers, real LGBModel trained on "
            f"[{train_start.date()}, {train_end.date()}], validated on "
            f"[{valid_start.date()}, {valid_end.date()}], best/early-stopped "
            f"iteration={result['best_iteration']} (see adapter header, "
            f"'LightGBM training budget', for why this is scoped down from "
            f"upstream's own CSI300-scale benchmark config). Forward-horizon "
            f"disclosure: upstream's own label expression '{LABEL_EXPRESSION}' "
            f"shifts 2 trading days ahead (a T+1-execution-safe convention), so "
            f"`values`/`expected_returns` are point estimates of a ~2-trading-day "
            f"forward return, not a plain 1-day return."
        )

        self._last_native_output = {
            "upstream": {
                "predicted_scores": values,
                "feature_importance_top5": [{"factor": n, "importance": v} for n, v in top5],
                "last_prediction_date": last_date.strftime("%Y-%m-%d"),
                "train_window": [train_start.strftime("%Y-%m-%d"), train_end.strftime("%Y-%m-%d")],
                "valid_window": [valid_start.strftime("%Y-%m-%d"), valid_end.strftime("%Y-%m-%d")],
                "test_window": [result["test_window"][0].strftime("%Y-%m-%d"), result["test_window"][1].strftime("%Y-%m-%d")],
                "best_iteration": result["best_iteration"],
                "tickers_ok": result["tickers_ok"],
                "label_expression": LABEL_EXPRESSION,
            },
            "adapter_derived": {
                "requested_ticker": raw_ticker,
                "resolved_ticker": resolved_ticker,
                "was_fallback": was_fallback,
            },
        }

        return Q3Signal(
            context=context,
            signal_semantics="predicted_return",
            values=values,
            score_scale=f"real regression-label scale ({LABEL_EXPRESSION}) — a forward daily-return ratio, not normalized/rescaled",
            direction=direction,
            strength=strength,
            expected_returns=expected_returns,
            factor_expression=factor_expression,
            evidence=evidence or None,
            explanation="\n".join(notes),
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
        native_output captured as a side effect of the real q3_signal() call
        BaseAdapter.run() makes internally (same pattern used by this
        session's other migrated Q3 adapters, e.g. alphagen/rdagent)."""
        self._last_native_output = None
        result = super().run(
            task_id=task_id, context=context, generation_window=generation_window,
            native_output=native_output, adapter_notes=adapter_notes, field_mappings=field_mappings,
            **kwargs,
        )
        if native_output is None and self._last_native_output:
            result = result.model_copy(update={"native_output": self._last_native_output})
        return result

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
            universe=["AAPL"],
        )
        result = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = result is not None
        if result is not None:
            checks["direction_is_valid"] = result.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["strength_in_range"] = result.strength is None or 0.0 <= result.strength <= 1.0
            checks["values_nonempty"] = len(result.values) > 0
            checks["context_echoed"] = result.context == context
        return checks
