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

Design notes (translation choices made by this adapter, not upstream):
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
    The requested `date` is recorded on the output but headline recency is
    whatever yfinance has "now".
  - sentiment_score: mean of per-headline labels (positive=+1, neutral=0,
    negative=-1) across the headlines scored, clipped to [-1, 1].
  - risk_level: FinGPT has no native risk concept, so this adapter derives a
    bucket from the aggregate score and cross-headline disagreement (a
    population stdev of the per-headline labels): consistently very negative
    -> EXTREME, negative-or-highly-disagreeing -> HIGH, near-neutral ->
    MEDIUM, net positive -> LOW.
  - drivers: the top 3 headlines ranked by |individual label|, ties broken by
    recency, formatted as "<title> (<label>)".
"""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Q2Sentiment, RiskLevel

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

    def q2_sentiment(self, ticker: str, date: str, **kwargs) -> Optional[Q2Sentiment]:
        t0 = time.time()

        headlines = _fetch_headlines(ticker)
        if not headlines:
            headlines = [f"No recent news found for {ticker}."]

        scored = [(title, *_score_text(title)) for title in headlines]
        # scored: List[(title, label, value)]

        values = [v for _, _, v in scored]
        avg = sum(values) / len(values)
        avg = max(-1.0, min(1.0, avg))
        dispersion = statistics.pstdev(values) if len(values) > 1 else 0.0

        if avg <= -0.66 and dispersion < 0.5:
            risk = RiskLevel.EXTREME
        elif avg <= -0.2 or dispersion >= 0.8:
            risk = RiskLevel.HIGH
        elif avg <= 0.2:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW

        top_drivers = sorted(scored, key=lambda s: abs(s[2]), reverse=True)[:3]
        drivers = [f"{title} ({label})" for title, label, _ in top_drivers]

        return Q2Sentiment(
            sentiment_score=avg,
            risk_level=risk,
            drivers=drivers,
            sources=["Yahoo Finance news (yfinance)"],
            adapter=self.name,
            ticker=ticker,
            date=date,
            cost_usd=0.0,
            latency_sec=time.time() - t0,
        )

    def smoke_test(self):
        checks = super().smoke_test()
        result = self.q2_sentiment("AAPL", "2024-01-15")
        checks["q2_returns_Q2Sentiment"] = result is not None
        checks["sentiment_score_in_range"] = -1.0 <= result.sentiment_score <= 1.0
        checks["risk_level_is_valid"] = result.risk_level in ("LOW", "MEDIUM", "HIGH", "EXTREME")
        checks["drivers_non_empty"] = len(result.drivers) > 0
        return checks
