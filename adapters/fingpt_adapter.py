"""
adapters/fingpt_adapter.py — wraps github.com/AI4Finance-Foundation/FinGPT (Q2).

SECURITY NOTE: as of this writing, the upstream repo (cloned into
adapters/vendor/FinGPT/) also contains a subtree at finogrid/ — an unrelated
B2B crypto-payments / KYC-AML platform, merged under a misleadingly-named
branch ("octo-patch/feature/upgrade-minimax-m3"). It even wires itself into
FinGPT's sentiment code at finogrid/fingpt_integration/sentiment/. This was
flagged to and confirmed with the project maintainer. This adapter ONLY
reads from fingpt/FinGPT_Sentiment_Analysis_v3/ (the legitimate sentiment
model docs) and never imports, executes, or otherwise references anything
under finogrid/. Do not add such an import to this file.

Environment setup (one-time, outside this file):
    conda create -n fingpt_real --clone pytorch   # reuses existing CUDA/torch setup
    conda activate fingpt_real
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    pip install "transformers==4.41.2" "tokenizers>=0.19,<0.20" "peft==0.11.1" \
                "accelerate==0.31.0" sentencepiece protobuf huggingface_hub \
                python-dotenv yfinance
    # IMPORTANT: transformers/peft/accelerate are pinned to versions
    # contemporary with upstream's own code (their benchmarks.ipynb comments
    # "# 4.30.2" / "# 0.4.0" next to these imports). Installing latest
    # transformers (tested: 5.12.1) breaks ChatGLM2's custom trust_remote_code
    # model class in multiple ways — see DECISIONS.md for the full chain of
    # incompatibilities found and why pinning (not patching each one) was the
    # right call. torch itself must stay >=2.6 regardless of the transformers
    # pin, because this repo's weights are legacy pickle .bin files and
    # transformers' CVE-2025-32434 guard requires torch>=2.6 to load them
    # (only applies to non-safetensors checkpoints).

    Model download (~12GB, first call only, cached under ~/.cache/huggingface):
        base: THUDM/chatglm2-6b
        lora: oliverwang15/FinGPT_v31_ChatGLM2_Sentiment_Instruction_LoRA_FT
    (Downgraded from FinGPT v3.3 Llama-2-13B mid-session — see DECISIONS.md.
    Loading code taken from upstream's own
    fingpt/FinGPT_Sentiment_Analysis_v3/benchmark/benchmarks.ipynb, "v3.1"
    cell: ChatGLM2 requires AutoModel + trust_remote_code=True, unlike the
    Llama variants which use AutoModelForCausalLM.)
    Both repos are ungated, but anonymous HF Hub downloads are throttled hard
    (~0.35MB/s observed vs ~8.8MB/s raw bandwidth via a single curl request).
    Put a real HF token in adapters/vendor/FinGPT/.env as HF_TOKEN=... to get
    authenticated rate limits. NOTE: huggingface_hub 1.x defaults to the Xet
    transfer backend for Xet-enabled repos (this one), which opens many
    parallel connections — those connections "struggle" and self-throttle
    hard through this sandbox's local egress proxy (127.0.0.1:8080), far
    below the ~8.8MB/s a single plain HTTP connection gets through the same
    proxy. This file sets HF_HUB_DISABLE_XET=1 to force the legacy resumable
    HTTP downloader instead, which matches raw curl throughput.

Run the harness with that env active:
    conda activate fingpt_real
    python CONTRACT/test_harness.py --adapter adapters/fingpt_adapter.py

No upstream source was patched — only environment/dependency setup was
needed, so there is no patches/FinGPT.diff.

Schema v2.0.0 migration notes (this adapter still answers Q2 only, same as
v1 — no new Q layer claimed; see PROJECT_SCHEMA_AUDIT.md §4.1/§7 for prior
findings this migration follows):
  - Model: FinGPT v3.1 (ChatGLM2-6B base), loaded fp16 (no 8-bit
    quantization — see below). Downgraded from v3.3 (Llama-2-13B, best
    reported F1) mid-session purely for download size/time in this sandbox's
    network conditions — v3.1 still scores second-best in upstream's own
    benchmark table (mean F1 0.860 vs 0.886 for v3.3). See DECISIONS.md.
  - No bitsandbytes 8-bit quantization: upstream's own example loads 8-bit,
    but this environment's bitsandbytes (0.49.2, latest) is incompatible with
    peft 0.11.1's 8-bit LoRA injection code (AttributeError on
    MatmulLtState.memory_efficient_backward — another version-skew case).
    Not needed anyway: the GPUs here have 46GB VRAM and the model is only
    ~12GB in fp16.
  - Upstream's model only classifies a single piece of text into
    positive/negative/neutral — it has no notion of "ticker" or "date", and
    does not fetch news itself. This adapter fetches the most recent
    headlines for the ticker via yfinance (free, no API key) and scores each
    one with the real FinGPT model, then aggregates.
  - yfinance's news feed only exposes the *current* latest headlines, not an
    arbitrary historical date's headlines — same kind of real-world API
    limitation ai_hedge_fund_adapter.py documents for its own data source.
    The requested `context.as_of` is recorded on the output but headline
    recency is whatever yfinance has "now".
  - Q2State.states[0] (dimension="sentiment"): value_numeric is the mean of
    per-headline labels (positive=+1, neutral=0, negative=-1) across the
    headlines scored by the real model, clipped to [-1, 1]. This is the same
    aggregation v1 called `sentiment_score`; only the canonical container
    changed.
  - Q2State.states[1] (dimension="sentiment_dispersion", RECOVERED
    presentation — see migration rubric / PROJECT_SCHEMA_AUDIT.md): v1 fed
    this same population-stdev-of-per-headline-labels statistic into a
    hand-tuned `risk_level` enum ladder (LOW/MEDIUM/HIGH/EXTREME) that only
    existed to satisfy v1's forced RiskLevel field. That ladder is deleted
    in this migration — FinGPT has no native risk concept, and forcing a
    real dispersion number through an invented bucket function is exactly
    the kind of derived-heuristic-dressed-as-native-risk pattern the v2
    schema's open-vocabulary StateEstimate is designed to avoid. The real
    number itself is preserved honestly as its own open-vocabulary
    dimension instead of being thrown away or miscategorized.
  - evidence: each StateEstimate carries the individual scored headlines
    (title + real per-headline label) as EvidenceItem(kind="news_headline",
    value=..., source="Yahoo Finance news (yfinance)"), replacing v1's
    `drivers: List[str]` free-text field with the same real per-headline
    information in the schema's structured evidence container. Kept to the
    top 3 by |label| (ties broken by recency), same selection v1 used.
  - No-headlines path (FALLBACK BEHAVIOR DELETED per migration rubric): v1
    fed a fabricated string ("No recent news found for {ticker}.") into the
    real FinGPT model as if it were a real headline, then reported the
    resulting neutral-ish score as if it meant something. That is deleted.
    When yfinance returns zero headlines, this adapter no longer calls the
    model at all — it returns a single honest StateEstimate(value_numeric=
    0.0, confidence=ConfidenceEstimate(value=0.0, kind=HEURISTIC,
    method="no headlines available")) and sets Q2State.explanation to say
    plainly that no headlines were found and sentiment was not evaluated.
  - confidence on the real (headlines-found) sentiment StateEstimate is left
    None: this adapter greedily decodes one label token per headline and
    never captures the model's per-class logits/probabilities, so there is
    no honest numeric confidence to report — reporting one anyway would be
    exactly the "default confidence=0.5" fabrication CLAUDE.md and the
    migration rubric prohibit.
"""

from __future__ import annotations

import os
import statistics
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

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

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "FinGPT"
load_dotenv(dotenv_path=VENDOR_DIR / ".env")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # Xet's high-concurrency transfer
                                                    # degrades badly through this
                                                    # sandbox's local proxy; plain
                                                    # resumable HTTP download is faster.

BASE_MODEL = "THUDM/chatglm2-6b"
LORA_MODEL = "oliverwang15/FinGPT_v31_ChatGLM2_Sentiment_Instruction_LoRA_FT"
MAX_HEADLINES = 5

SENTIMENT_MAP = {"positive": 1, "negative": -1, "neutral": 0}

PROMPT_TEMPLATE = (
    "Instruction: What is the sentiment of this news? "
    "Please choose an answer from {{negative/neutral/positive}}\n"
    "Input: {text}\n"
    "Answer: "
)

_MODEL_CACHE: dict = {}


def _get_model():
    """Lazily load base model + LoRA once per process; reused across calls."""
    if "model" not in _MODEL_CACHE:
        import torch
        from transformers import AutoModel, AutoTokenizer
        from peft import PeftModel

        # ChatGLM2 requires trust_remote_code + the generic AutoModel class
        # (not AutoModelForCausalLM) — per upstream's own benchmarks.ipynb.
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        base = AutoModel.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        model = PeftModel.from_pretrained(base, LORA_MODEL)
        model.eval()
        _MODEL_CACHE["tokenizer"] = tokenizer
        _MODEL_CACHE["model"] = model
    return _MODEL_CACHE["tokenizer"], _MODEL_CACHE["model"]


def _score_text(text: str) -> Tuple[str, int]:
    """Run one headline through the real FinGPT model. Returns (label, score)."""
    import torch

    tokenizer, model = _get_model()
    prompt = PROMPT_TEMPLATE.format(text=text[:512])
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=10,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id or tokenizer.pad_token_id,
        )

    decoded = tokenizer.decode(out[0], skip_special_tokens=True)
    # Split on the marker rather than slicing by len(prompt): upstream's own
    # README uses this approach because decode() isn't guaranteed to
    # reproduce the prompt byte-for-byte across tokenizers (e.g. ChatGLM2).
    answer = decoded.split("Answer:")[-1].strip().lower()

    label = "neutral"
    for key in SENTIMENT_MAP:
        if key in answer:
            label = key
            break
    return label, SENTIMENT_MAP[label]


def _fetch_headlines(ticker: str, limit: int = MAX_HEADLINES) -> List[str]:
    import yfinance as yf

    items = yf.Ticker(ticker).news or []
    titles = []
    for item in items[:limit]:
        title = (item.get("content") or {}).get("title")
        if title:
            titles.append(title)
    return titles


class FinGPTAdapter(BaseAdapter):
    name = "fingpt"
    questions_answered = ["Q2"]
    upstream_repo = "https://github.com/AI4Finance-Foundation/FinGPT"
    requires_env = "fingpt_real"

    def __init__(self):
        super().__init__()
        # Cache keyed by (ticker, as_of): the run() override's native_output
        # capture reuses the same real scoring pass q2_state() performs,
        # instead of re-running the GPU model a second time.
        self._cache: dict[tuple[str, str], dict] = {}

    def _run(self, ticker: str, date: str) -> dict:
        key = (ticker, date)
        if key in self._cache:
            return self._cache[key]

        headlines = _fetch_headlines(ticker)

        if not headlines:
            raw = {"ticker": ticker, "date": date, "headlines": [], "scored": []}
            self._cache[key] = raw
            return raw

        scored = [(title, *_score_text(title)) for title in headlines]  # (title, label, value)
        raw = {
            "ticker": ticker,
            "date": date,
            "headlines": headlines,
            "scored": [{"title": t, "label": l, "value": v} for t, l, v in scored],
        }
        self._cache[key] = raw
        return raw

    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        if not context.targets:
            raise ValueError("fingpt q2_state requires context.targets == [ticker]")
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
                    "via yfinance; the real FinGPT model was not run on fabricated "
                    "input, so sentiment could not be evaluated."
                ),
            )

        values = [s["value"] for s in scored]
        avg = max(-1.0, min(1.0, sum(values) / len(values)))
        dispersion = statistics.pstdev(values) if len(values) > 1 else 0.0

        top_evidence = sorted(scored, key=lambda s: abs(s["value"]), reverse=True)[:3]
        evidence = [
            EvidenceItem(
                kind="news_headline",
                value=f"{item['title']} ({item['label']})",
                source="Yahoo Finance news (yfinance)",
            )
            for item in top_evidence
        ]

        sentiment_state = StateEstimate(
            dimension="sentiment",
            value_numeric=avg,
            scale="[-1,1]",
            evidence=evidence,
        )
        dispersion_state = StateEstimate(
            dimension="sentiment_dispersion",
            value_numeric=dispersion,
            scale="population_stdev_of_per_headline_labels_in_{-1,0,1}",
        )

        return Q2State(
            context=context,
            states=[sentiment_state, dispersion_state],
            explanation=(
                f"Aggregated real FinGPT v3.1 (ChatGLM2-6B) sentiment across "
                f"{len(scored)} Yahoo Finance headline(s) for {ticker}: mean "
                f"per-headline label {avg:.3f} (range [-1,1]), dispersion "
                f"(population stdev of per-headline labels) {dispersion:.3f}."
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
        Overridden solely to attach a faithful `native_output` (the real
        per-headline FinGPT labels/scores this run produced, or an empty
        scored list if yfinance had no headlines). No business logic
        changes; context checks and RunMetadata construction are still done
        by super().run(). Pre-populating self._cache here means the
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
        return checks
