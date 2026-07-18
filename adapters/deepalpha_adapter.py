"""
adapters/deepalpha_adapter.py — wraps
github.com/LeoRigasaki/stock-market-prediction-engine (Q1, Q3).

Repo choice (per SESSION_BRIEFS.md Session C: no public "DeepAlpha" repo
exists, find the closest open-source gradient-boosted trading model):
searched GitHub for XGBoost+LightGBM(+CatBoost) ensembles on technical
factors predicting forward stock returns. The closest exact-keyword match
(irissees/EnsembleTrading) was rejected — it requires live Robinhood
account credentials via an unofficial reverse-engineered broker API just to
fetch data, which this adapter will not wire up without explicit
authorization (see DECISIONS.md). Settled on
LeoRigasaki/stock-market-prediction-engine: a proper `src/` package (not a
notebook-only repo), XGBoost + LightGBM ensemble (no CatBoost, but closest
available match), 73 technical/statistical features, walk-forward
validation, real yfinance data, no brokerage credentials required, MIT-style
transparent methodology docs, clean security scan (no eval/exec/shell=True/
credential-harvesting patterns, coherent single-purpose file tree).

Environment setup (one-time, outside this file):
    conda create -n deepalpha_real python=3.11
    conda activate deepalpha_real
    conda install -c conda-forge xgboost lightgbm scikit-learn pandas numpy joblib
    pip install yfinance ta loguru optuna matplotlib plotly aiohttp seaborn python-dotenv pydantic
    # xgboost/lightgbm via conda-forge, not pip: no prebuilt pip wheel for
    # this platform/Python combo, and building from source needs cmake
    # (not installed here). conda-forge ships precompiled binaries.

Run the harness with that env active:
    conda activate deepalpha_real
    python CONTRACT/test_harness.py --adapter adapters/deepalpha_adapter.py

No upstream source was patched — only environment/dependency setup was
needed, so there is no patches/stock-market-prediction-engine.diff.

Design notes (translation choices made by this adapter, not upstream):
  - Upstream's real pipeline trains on a bulk historical dataset pulled from
    Kaggle (requires KAGGLE_USERNAME/KAGGLE_KEY) across many tickers over
    ~15 "Day N" pipeline stages, then serves predictions from saved
    `models/*.joblib` artifacts — none of which are checked into the repo
    (gitignored) or reproducible without Kaggle credentials this sandbox
    doesn't have. Minimum viable substitution: this adapter calls upstream's
    own `RealTimePredictionEngine.engineer_realtime_features()` on ~3 years
    of real yfinance OHLCV history for the single requested ticker, then
    trains upstream's own `AdvancedMLFramework.create_xgboost_model()` /
    `.create_lightgbm_model()` (their pre-configured hyperparameters, not
    reimplemented — Optuna hyperparameter search is skipped for speed) on
    that ticker's own history, and combines them with upstream's own
    `SimpleEnsemble` averaging class. This is real training + real
    inference on real data, just scoped to one ticker on the fly instead of
    upstream's full multi-ticker Kaggle-sourced production pipeline.
  - Feature selection: `engineer_realtime_features()` returns the full
    engineered frame including raw OHLCV columns. Upstream's real feature
    list (73 columns) came from a separate Kaggle-pipeline stage not present
    in this repo's checked-in code (`data/features/selected_features.csv`,
    gitignored/generated). This adapter excludes raw price/volume columns
    itself before training (Open/High/Low/Close/Volume/Dividends/Stock
    Splits) — training on the engineered indicators only, not on raw Close
    (which would leak directly into a Close-derived target). This is a data
    hygiene choice this adapter makes when reconstructing the feature list,
    not a modification of `engineer_realtime_features()` itself.
  - Target: 5-day forward return (`Close.shift(-5)/Close - 1`), matching
    upstream's own `Config.FORECAST_HORIZON_DAYS = 5` and `return_5d`/
    `target_5d` naming convention used throughout their code.
  - Q1 action / signal threshold: reuses upstream's own
    `Config.signal_threshold_ratio()` (transaction-cost-based threshold)
    rather than an arbitrary cutoff.
  - Q1 confidence / Q3 strength: derived from ensemble dispersion between
    the two models' predictions, using the same formula upstream's own
    `RealTimePredictionEngine.generate_predictions()` uses for
    `model_agreement` (`max(0, 1 - dispersion/0.1)`).
  - Q3 supporting_evidence: real per-run XGBoost `feature_importances_`,
    top 3 by importance — not hardcoded.
  - Per-ticker caching: Q1 and Q3 (and `run()`, which calls both) would
    otherwise retrain the ensemble redundantly for the same ticker within
    one process; cached in memory per ticker.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    Action,
    ConfidenceEstimate,
    ConfidenceKind,
    Direction,
    EvidenceItem,
    OutputScope,
    Q1Action,
    Q3Signal,
    QueryContext,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "stock-market-prediction-engine"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

RAW_COLS = {
    "Date", "Ticker", "Open", "High", "Low", "Close", "Volume",
    "Dividends", "Stock Splits", "Stock_Splits",
}
TARGET_RELATED = {"target_1d", "target_5d", "return_1d", "return_5d", "sharpe_5d"}
EXCLUDE_COLS = RAW_COLS | TARGET_RELATED
FORECAST_HORIZON_DAYS = 5  # upstream Config.FORECAST_HORIZON_DAYS default; overridable via context.horizon (see _horizon_days_from_context)

_TRAIN_CACHE: dict = {}


def _ticker_from_context(context: QueryContext) -> str:
    """This adapter is single-asset only (one ticker per call). Read it from
    the harness-supplied QueryContext instead of a bespoke ticker param."""
    if context.targets:
        return context.targets[0]
    if context.universe:
        return context.universe[0]
    raise ValueError(
        "deepalpha_adapter requires context.targets or context.universe to "
        "contain at least one ticker (this adapter is single-asset only)."
    )


def _horizon_days_from_context(context: QueryContext) -> int:
    """v2: replace the old hardcoded FORECAST_HORIZON_DAYS constant with
    context.horizon when the harness supplies a parseable '<N>d' horizon;
    otherwise fall back to upstream's own Config.FORECAST_HORIZON_DAYS
    default (5) as a documented adapter-internal constant (per migration
    rubric: "it's fine to keep an adapter-internal constant... that the CLI
    caller is expected to pass in via --horizon")."""
    if context.horizon:
        h = context.horizon.strip().lower()
        if h.endswith("d"):
            try:
                return int(h[:-1])
            except ValueError:
                pass
    return FORECAST_HORIZON_DAYS


def _train_ensemble(ticker: str, horizon_days: int) -> Tuple[object, List[str], float, float]:
    """
    Fetch real yfinance history, engineer features via upstream's own
    method, train upstream's own XGBoost+LightGBM models on this ticker's
    history, combine with upstream's own SimpleEnsemble.
    Returns (xgb_model, feature_cols, latest_prediction, model_agreement).

    NOTE (pre-existing limitation, not introduced by this migration): this
    fetches "3y" of yfinance history ending at real wall-clock "now", not
    windowed to end at the requested QueryContext.as_of/data_cutoff — same
    behavior as the v1 adapter. Left unchanged per the migration rubric's
    scope rule (preserve existing data-fetching/business logic; only the
    canonical field mapping is being migrated here). Disclosed honestly in
    Q1Action.explanation / Q3Signal.explanation below rather than silently
    passed through.
    """
    cache_key = (ticker, horizon_days)
    if cache_key in _TRAIN_CACHE:
        return _TRAIN_CACHE[cache_key]

    import pandas as pd
    import yfinance as yf

    from src.advanced_models import AdvancedMLFramework
    from src.ensemble_models import SimpleEnsemble
    from src.realtime_prediction import RealTimePredictionEngine

    hist = yf.Ticker(ticker).history(period="3y", interval="1d")
    if hist.empty:
        raise RuntimeError(f"yfinance returned no history for {ticker}")

    hist = hist.reset_index()
    hist["Ticker"] = ticker
    if "Date" not in hist.columns and "Datetime" in hist.columns:
        hist["Date"] = hist["Datetime"]
    hist["Stock_Splits"] = hist["Stock Splits"] if "Stock Splits" in hist.columns else 0

    engine = RealTimePredictionEngine()
    df_feat = engine.engineer_realtime_features(hist, ticker)
    if df_feat.empty:
        raise RuntimeError(f"upstream engineer_realtime_features() returned empty frame for {ticker}")

    target_col = f"target_{horizon_days}d"
    df_feat[target_col] = df_feat["Close"].shift(-horizon_days) / df_feat["Close"] - 1

    exclude = EXCLUDE_COLS | {target_col}
    feature_cols = [
        c for c in df_feat.columns
        if c not in exclude and pd.api.types.is_numeric_dtype(df_feat[c])
    ]

    df_train = df_feat.iloc[:-horizon_days]
    X_train = df_train[feature_cols]
    y_train = df_train[target_col]
    X_latest = df_feat[feature_cols].iloc[[-1]]

    adv = AdvancedMLFramework()
    xgb_model = adv.create_xgboost_model("regression")
    lgb_model = adv.create_lightgbm_model("regression")
    xgb_model.fit(X_train, y_train)
    lgb_model.fit(X_train, y_train)

    ensemble = SimpleEnsemble({"XGBoost": xgb_model, "LightGBM": lgb_model})
    ensemble.fit(X_train, y_train)

    xgb_pred = float(xgb_model.predict(X_latest)[0])
    lgb_pred = float(lgb_model.predict(X_latest)[0])
    prediction = float(ensemble.predict(X_latest)[0])

    import numpy as np
    dispersion = float(np.std([xgb_pred, lgb_pred]))
    agreement = max(0.0, 1.0 - min(dispersion / 0.1, 1.0))

    result = (xgb_model, feature_cols, prediction, agreement)
    _TRAIN_CACHE[cache_key] = result
    return result


class DeepAlphaAdapter(BaseAdapter):
    name = "deepalpha"
    questions_answered = ["Q1", "Q3"]
    upstream_repo = "https://github.com/LeoRigasaki/stock-market-prediction-engine"
    requires_env = "deepalpha_real"

    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        t0 = time.time()
        from src.config import Config

        ticker = _ticker_from_context(context)
        horizon_days = _horizon_days_from_context(context)

        xgb_model, feature_cols, prediction, agreement = _train_ensemble(ticker, horizon_days)
        threshold = Config.signal_threshold_ratio()

        if prediction > threshold:
            action = Action.BUY
        elif prediction < -threshold:
            action = Action.SELL
        else:
            action = Action.HOLD

        # Real upstream model_agreement measure (1 - normalised cross-model
        # prediction dispersion) — this is NOT a calibrated probability, so
        # it is tagged MODEL_MARGIN, not PROBABILITY (see migration rubric).
        confidence = ConfidenceEstimate(
            value=max(0.0, min(1.0, agreement)),
            kind=ConfidenceKind.MODEL_MARGIN,
            raw_value=agreement,
            method=(
                "Upstream's own model_agreement formula: max(0, 1 - dispersion/0.1), "
                "dispersion = std(xgboost_pred, lightgbm_pred), matching "
                "RealTimePredictionEngine.generate_predictions()'s own convention. "
                "Measures cross-model prediction agreement, not a calibrated probability."
            ),
        )

        explanation = (
            f"XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on "
            f"{ticker}'s own 3y trailing yfinance history ending at real run time — "
            f"not windowed to context.as_of={context.as_of!r}, see adapter header/"
            f"_train_ensemble docstring for this pre-existing limitation — no "
            f"pretrained Kaggle-sourced artifacts were available) predicts a "
            f"{horizon_days}-day forward return of {prediction:+.4%}, against a "
            f"transaction-cost-based signal threshold of {threshold:.4%}. Model "
            f"agreement (1 - normalised prediction dispersion) is {agreement:.2f}."
        )

        return Q1Action(
            context=context,
            action=action,
            confidence=confidence,
            explanation=explanation,
        )

    def q3_signal(self, context: QueryContext, **kwargs) -> Optional[Q3Signal]:
        t0 = time.time()

        ticker = _ticker_from_context(context)
        horizon_days = _horizon_days_from_context(context)

        xgb_model, feature_cols, prediction, agreement = _train_ensemble(ticker, horizon_days)

        direction = Direction.LONG if prediction > 0 else Direction.SHORT if prediction < 0 else Direction.NEUTRAL
        strength = max(0.0, min(1.0, abs(prediction) / 0.05))

        evidence: List[EvidenceItem] = []
        importances = getattr(xgb_model, "feature_importances_", None)
        if importances is not None:
            ranked = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)[:3]
            for fname, fval in ranked:
                evidence.append(EvidenceItem(
                    kind="model_feature",
                    value=f"{fname} (importance={fval:.4f})",
                    source="XGBoost feature_importances_ (upstream AdvancedMLFramework.create_xgboost_model(), freshly trained this run)",
                ))
        else:
            evidence.append(EvidenceItem(kind="model_feature", value="XGBoost feature_importances_ unavailable"))

        confidence = ConfidenceEstimate(
            value=max(0.0, min(1.0, agreement)),
            kind=ConfidenceKind.MODEL_MARGIN,
            raw_value=agreement,
            method=(
                "Same model_agreement measure as Q1Action.confidence (1 - normalised "
                "XGBoost/LightGBM prediction dispersion) — reused here since it "
                "applies to the same ensemble prediction underlying this signal."
            ),
        )

        explanation = (
            f"Ensemble predicts a {horizon_days}-day forward return of {prediction:+.4%} "
            f"for {ticker} (model agreement {agreement:.2f}); same 3y-trailing, "
            f"real-run-time-windowed training data as Q1Action (see that method's "
            f"docstring for the point-in-time limitation)."
        )

        return Q3Signal(
            context=context,
            signal_semantics="predicted_return",
            values={ticker: prediction},
            score_scale="fractional forward return (e.g. 0.01 = +1%)",
            direction=direction,
            strength=strength,
            expected_returns={ticker: prediction},
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
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
            checks["confidence_in_range"] = (
                result.confidence is not None and 0.0 <= result.confidence.value <= 1.0
            )

        q3 = self.q3_signal(context)
        checks["q3_returns_Q3Signal"] = q3 is not None
        if q3 is not None:
            checks["q3_direction_is_valid"] = q3.direction in ("LONG", "SHORT", "NEUTRAL")
            checks["q3_strength_in_range"] = q3.strength is not None and 0.0 <= q3.strength <= 1.0
        return checks
