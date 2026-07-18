"""
adapters/finbert_adapter.py — wraps github.com/ProsusAI/finBERT (Q2).

New-adapter integration pass (2026-07). Batch A of the candidate-adapter
roster in the active task brief. Q2 only — this is a pure supervised
sentiment classifier with no ticker/date/portfolio concept of its own.

Repo verification: real repo cloned at adapters/vendor/finBERT, commit
44995e0c5870c4ab37a189d756550654ae87cdf0 (2022-02-01), matching the commit
already recorded in PROJECT_SCHEMA_AUDIT.md line 55. Re-verified against
real source in this pass (not copied from the audit blindly):
  - finbert/finbert.py:581-640 `predict(text, model, write_to_csv=False,
    path=None, use_gpu=False, gpu_name='cuda:0', batch_size=5)` is the real,
    public inference entrypoint. It splits `text` into sentences via
    `nltk.sent_tokenize`, batches them, runs the real classifier, and
    returns a pandas.DataFrame with columns:
      - sentence: str
      - logit: the real full 3-class softmax array [P(positive),
        P(negative), P(neutral)] (finbert.py:624, `softmax(np.array(logits))`)
      - prediction: one of "positive"/"negative"/"neutral"
        (argmax over the softmax array)
      - sentiment_score: logit[0] - logit[1] i.e. P(positive) - P(negative),
        upstream's own real scalar summary, roughly in [-1, 1]
  - Real official pretrained weights: HuggingFace `ProsusAI/finbert`
    (confirmed via README.md — "FinBERT sentiment analysis model is now
    available on Hugging Face model hub"). Loaded via
    `AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert",
    num_labels=3, cache_dir=None)`, matching scripts/predict.py's own usage.
  - No upstream source was patched.

Environment setup (one-time, outside this file):
    conda create -n finbert_real python=3.10
    conda activate finbert_real
    pip install torch "transformers==4.41.2" pandas numpy nltk yfinance python-dotenv
    python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
    # PIN transformers==4.41.2, NOT latest: finbert/finbert.py does
    # `from transformers.optimization import AdamW,
    # get_linear_schedule_with_warmup` at module import time (used only by
    # this repo's own *training* code, never by `predict()`), but modern
    # transformers (tested: 5.14.1) removed `AdamW` from
    # transformers.optimization entirely, so the import fails before
    # `predict()` is ever reached. 4.41.2 is the same pin
    # `fingpt_adapter.py` already uses for an unrelated but similarly-aged
    # compatibility reason — verified empirically to still export AdamW and
    # to load ProsusAI/finbert (a standard BertForSequenceClassification
    # checkpoint) cleanly. This is an import-time dependency fix, not a
    # change to any upstream file.
    # `from tqdm import tqdm_notebook as tqdm` (finbert.py:1) was also
    # checked: tqdm 4.69.0 (this env's version) still ships the deprecated
    # `tqdm_notebook` alias, so no additional pin was needed there.

Run the harness with that env active:
    conda activate finbert_real
    python CONTRACT/adapter_runner.py --adapter adapters/finbert_adapter.py \
        --task-id smoke --as-of 2024-01-15 --scope ASSET --target AAPL --universe AAPL

Design notes (translation choices made by this adapter, not upstream):
  - No ticker/date concept natively, and this project does not fetch news
    itself. Same pattern as fingpt_adapter.py (its closest sibling in this
    repo): fetch real recent headlines for the requested ticker via
    yfinance (free, no API key), run each real headline through the real
    `predict()` function, aggregate.
  - Same real-world data limitation fingpt_adapter.py documents: yfinance's
    news feed only exposes the *current* latest headlines, not an arbitrary
    historical date's headlines. `context.as_of` is recorded on the output;
    headline recency is whatever yfinance has "now".
  - Q2State.states[0] (dimension="sentiment"): value_numeric is the mean of
    the real per-headline `sentiment_score` values (already in [-1,1] per
    headline, so the mean needs no further clipping beyond defensive
    min/max), matching fingpt_adapter.py's own aggregation shape.
  - Q2State.states[0] ALSO carries `value_distribution` — the mean of the
    real per-headline 3-class softmax arrays,
    {"positive": ..., "negative": ..., "neutral": ...}. This is a genuine
    capability FinBERT has that fingpt_adapter.py's model does not: FinGPT's
    adapter only ever captures a greedy-decoded label (no logits), so it
    can't honestly report a distribution or a real confidence value.
    FinBERT's `predict()` returns the full softmax every call — recovering
    this is a straightforward, real, low-risk capability gain, not
    derivable-but-forced.
  - confidence on the sentiment StateEstimate: also unlike fingpt_adapter.py
    (which must leave confidence=None), FinBERT genuinely gives a
    per-headline max-class probability. This adapter averages
    max(logit) across headlines and reports it as ConfidenceKind.PROBABILITY
    (a real softmax probability, not self-reported or heuristic).
  - evidence: one EvidenceItem per real scored headline (title + real
    per-headline prediction label + real sentiment_score), kind=
    "news_headline". ALL scored headlines are kept (MAX_HEADLINES=5 already
    bounds this to a small, safe number — matching fingpt_adapter.py's own
    already-corrected behavior of not truncating a small bounded set).
  - No-headlines path: same honest-fallback pattern as fingpt_adapter.py —
    do not feed a fabricated string into the real model. Return an honest
    zero-value state with confidence=0.0/HEURISTIC and an explanation that
    plainly says sentiment could not be evaluated.
  - Q1/Q3/Q4: genuinely ABSENT. FinBERT is a single-purpose text classifier
    with no action/signal/policy concept anywhere in its real code — this
    is not a missed mapping, there is nothing there to map.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import (
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    EvidenceItem,
    OutputScope,
    Q2State,
    QueryContext,
    StateEstimate,
    TimeWindow,
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "finBERT"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

FINBERT_MODEL = "ProsusAI/finbert"
MAX_HEADLINES = 5

_MODEL_CACHE: dict = {}


def _get_model():
    """Lazily load the real pretrained ProsusAI/finbert classifier once per process."""
    if "model" not in _MODEL_CACHE:
        from transformers import AutoModelForSequenceClassification

        model = AutoModelForSequenceClassification.from_pretrained(
            FINBERT_MODEL, num_labels=3, cache_dir=None
        )
        _MODEL_CACHE["model"] = model
    return _MODEL_CACHE["model"]


def _score_headlines(headlines: List[str]) -> List[Dict]:
    """
    Run real headlines through upstream's own real finbert.finbert.predict(),
    one real predict() call per headline (not all headlines joined into one
    text blob). News headlines routinely lack terminal punctuation, and
    predict()'s own real nltk.sent_tokenize() sentence-boundary detection can
    then merge several unrelated headlines into a single "sentence" when
    given a joined blob (verified empirically: 3 real AAPL headlines with no
    periods between them were tokenized as one sentence, corrupting the
    per-headline correspondence this adapter's evidence/aggregation
    depends on). Scoring one headline per call is real, upstream-unmodified
    behavior — just invoked in a way that guarantees a clean 1:1
    headline<->score mapping, matching fingpt_adapter.py's own per-headline
    granularity.
    """
    from finbert.finbert import predict

    model = _get_model()
    scored = []
    for headline in headlines:
        df = predict(headline, model, write_to_csv=False)
        if df.empty:
            continue
        row = df.iloc[0]
        logit = list(row["logit"])  # [P(positive), P(negative), P(neutral)]
        scored.append(
            {
                "sentence": str(row["sentence"]),
                "prediction": str(row["prediction"]),
                "sentiment_score": float(row["sentiment_score"]),
                "logit": {
                    "positive": float(logit[0]),
                    "negative": float(logit[1]),
                    "neutral": float(logit[2]),
                },
            }
        )
    return scored


def _fetch_headlines(ticker: str, limit: int = MAX_HEADLINES) -> List[str]:
    import yfinance as yf

    items = yf.Ticker(ticker).news or []
    titles = []
    for item in items[:limit]:
        title = (item.get("content") or {}).get("title")
        if title:
            titles.append(title)
    return titles


class FinBERTAdapter(BaseAdapter):
    name = "finbert"
    questions_answered = ["Q2"]
    upstream_repo = "https://github.com/ProsusAI/finBERT"
    requires_env = "finbert_real"

    def __init__(self):
        super().__init__()
        # Cache keyed by (ticker, as_of): run()'s native_output capture
        # reuses the same real scoring pass q2_state() performs, instead of
        # re-running the real model a second time.
        self._cache: Dict[Tuple[str, str], dict] = {}

    def _run(self, ticker: str, date: str) -> dict:
        key = (ticker, date)
        if key in self._cache:
            return self._cache[key]

        headlines = _fetch_headlines(ticker)
        if not headlines:
            raw = {"ticker": ticker, "date": date, "headlines": [], "scored": []}
            self._cache[key] = raw
            return raw

        scored = _score_headlines(headlines)
        raw = {"ticker": ticker, "date": date, "headlines": headlines, "scored": scored}
        self._cache[key] = raw
        return raw

    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        if not context.targets:
            raise ValueError("finbert q2_state requires context.targets == [ticker]")
        ticker = context.targets[0]
        date = context.as_of

        raw = self._run(ticker, date)
        scored = raw["scored"]

        if not scored:
            no_headline_state = StateEstimate(
                dimension="sentiment",
                value_numeric=0.0,
                scale="[-1,1]",
                confidence=ConfidenceEstimate(
                    value=0.0,
                    kind=ConfidenceKind.HEURISTIC,
                    method="no headlines available",
                ),
            )
            return Q2State(
                context=context,
                states=[no_headline_state],
                explanation=(
                    f"No recent Yahoo Finance headlines were available for {ticker} "
                    "via yfinance; the real FinBERT model was not run on fabricated "
                    "input, so sentiment could not be evaluated."
                ),
            )

        scores = [s["sentiment_score"] for s in scored]
        avg = max(-1.0, min(1.0, sum(scores) / len(scores)))

        pos = statistics.fmean(s["logit"]["positive"] for s in scored)
        neg = statistics.fmean(s["logit"]["negative"] for s in scored)
        neu = statistics.fmean(s["logit"]["neutral"] for s in scored)

        mean_max_prob = statistics.fmean(max(s["logit"].values()) for s in scored)

        evidence = [
            EvidenceItem(
                kind="news_headline",
                value=f"{s['sentence']} ({s['prediction']}, score={s['sentiment_score']:.3f})",
                source="Yahoo Finance news (yfinance) + real ProsusAI/finbert prediction",
            )
            for s in scored
        ]

        sentiment_state = StateEstimate(
            dimension="sentiment",
            value_numeric=avg,
            value_distribution={"positive": pos, "negative": neg, "neutral": neu},
            scale="[-1,1]; value_distribution is the mean real 3-class softmax [positive,negative,neutral] across scored headlines",
            confidence=ConfidenceEstimate(
                value=mean_max_prob,
                kind=ConfidenceKind.PROBABILITY,
                raw_value=mean_max_prob,
                method=(
                    "Mean, across scored headlines, of the real per-headline "
                    "max-class softmax probability from ProsusAI/finbert's own "
                    "prediction — a genuine model probability, not self-reported "
                    "or heuristic."
                ),
            ),
            evidence=evidence,
        )

        return Q2State(
            context=context,
            states=[sentiment_state],
            explanation=(
                f"Aggregated real FinBERT (ProsusAI/finbert) sentiment across "
                f"{len(scored)} Yahoo Finance headline(s) for {ticker}: mean "
                f"sentiment_score {avg:.3f} (range [-1,1]); mean class distribution "
                f"positive={pos:.3f} negative={neg:.3f} neutral={neu:.3f}."
            ),
        )

    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window: Optional[TimeWindow] = None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings=None,
        **kwargs,
    ) -> AdapterResult:
        """
        Overridden solely to attach a faithful native_output (the real
        per-headline FinBERT predictions this run produced, or an empty
        scored list if yfinance had no headlines) — same pattern
        fingpt_adapter.py uses. Pre-populating self._cache here means the
        subsequent q2_state() call super().run() makes internally reuses
        this same real result instead of invoking the model a second time.
        """
        if native_output is None and context.targets:
            native_output = self._run(context.targets[0], context.as_of)
        return super().run(
            task_id,
            context,
            generation_window=generation_window,
            native_output=native_output,
            adapter_notes=adapter_notes,
            field_mappings=field_mappings,
            **kwargs,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
        )
        result = self.q2_state(context)
        checks["q2_returns_Q2State"] = result is not None
        checks["states_non_empty"] = len(result.states) >= 1
        sentiment = next((s for s in result.states if s.dimension == "sentiment"), None)
        checks["sentiment_state_present"] = sentiment is not None
        if sentiment is not None and sentiment.value_numeric is not None:
            checks["sentiment_value_in_range"] = -1.0 <= sentiment.value_numeric <= 1.0
            raw = self._cache.get((context.targets[0], context.as_of), {})
            n_scored = len(raw.get("scored", []))
            checks["evidence_covers_all_scored_headlines"] = (
                n_scored == 0 or len(sentiment.evidence or []) == n_scored
            )
            if n_scored > 0:
                checks["value_distribution_present"] = bool(sentiment.value_distribution)
                checks["value_distribution_sums_near_1"] = (
                    sentiment.value_distribution is not None
                    and 0.9 <= sum(sentiment.value_distribution.values()) <= 1.1
                )
                checks["confidence_present"] = sentiment.confidence is not None
                checks["confidence_in_range"] = (
                    sentiment.confidence is not None
                    and 0.0 <= sentiment.confidence.value <= 1.0
                )
        return checks
