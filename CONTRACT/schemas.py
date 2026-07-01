"""
CONTRACT/schemas.py — Canonical output schemas for all 5 trading questions.

DO NOT MODIFY THIS FILE. It is the shared contract between all adapters.
Every adapter must import from here and return instances of these classes.
Adding fields requires a version bump and sign-off from the project maintainer.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class Action(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RiskLevel(str, Enum):
    LOW     = "LOW"
    MEDIUM  = "MEDIUM"
    HIGH    = "HIGH"
    EXTREME = "EXTREME"

class SignalType(str, Enum):
    MOMENTUM  = "MOMENTUM"
    REVERSAL  = "REVERSAL"
    BREAKOUT  = "BREAKOUT"
    ANOMALY   = "ANOMALY"
    FACTOR    = "FACTOR"

class Direction(str, Enum):
    LONG    = "LONG"
    SHORT   = "SHORT"
    NEUTRAL = "NEUTRAL"

class Regime(str, Enum):
    BULL     = "BULL"
    BEAR     = "BEAR"
    SIDEWAYS = "SIDEWAYS"


# ---------------------------------------------------------------------------
# Q1 — Single-stock decision: Buy / Sell / Hold?
# ---------------------------------------------------------------------------

class Q1Decision(BaseModel):
    """
    Answer to: "What should I do with this stock right now?"
    Produced by: TradingAgents, ai-hedge-fund, FinRL (direction), DeepAlpha
    """
    action:        Action
    confidence:    float  = Field(..., ge=0.0, le=1.0,
                               description="Model's conviction, 0=random 1=certain")
    reasoning:     str    = Field(..., min_length=10,
                               description="One-paragraph justification")
    bull_case:     Optional[str]   = None
    bear_case:     Optional[str]   = None
    time_horizon:  Optional[str]   = None   # "1d" | "1w" | "1q"

    adapter:       str   = ""
    ticker:        str   = ""
    date:          str   = ""
    cost_usd:      float = 0.0
    latency_sec:   float = 0.0

    model_config = {"use_enum_values": True}


# ---------------------------------------------------------------------------
# Q2 — Market sentiment / risk level
# ---------------------------------------------------------------------------

class Q2Sentiment(BaseModel):
    """
    Answer to: "What is the overall market sentiment and risk right now?"
    Produced by: FinGPT, TradingAgents (sentiment analyst), NoFx, Prediction Arena
    """
    sentiment_score: float     = Field(..., ge=-1.0, le=1.0,
                                       description="-1=extreme fear, 0=neutral, +1=extreme greed")
    risk_level:      RiskLevel
    drivers:         List[str] = Field(..., min_length=1,
                                       description="Top factors driving sentiment, most important first")
    sources:         List[str] = Field(default_factory=list,
                                       description="Data sources used (Reddit, news, etc.)")

    adapter:         str   = ""
    ticker:          str   = ""
    date:            str   = ""
    cost_usd:        float = 0.0
    latency_sec:     float = 0.0

    model_config = {"use_enum_values": True}


# ---------------------------------------------------------------------------
# Q3 — Alpha signal / anomaly detection
# ---------------------------------------------------------------------------

class Q3Signal(BaseModel):
    """
    Answer to: "Are there any unusual opportunities or signals right now?"
    Produced by: ATLAS, FinClaw, Vibe-Trading, FinRL-X
    """
    signal_type:          SignalType
    direction:            Direction
    strength:             float      = Field(..., ge=0.0, le=1.0,
                                            description="0=weak noise, 1=strong conviction")
    supporting_evidence:  List[str]  = Field(..., min_length=1,
                                            description="Factor names or event descriptions")
    expected_horizon:     Optional[str]  = None   # "3d" | "2w" | "1q"
    expected_return:      Optional[float] = None  # point estimate if available

    adapter:              str   = ""
    ticker:               str   = ""
    date:                 str   = ""
    cost_usd:             float = 0.0
    latency_sec:          float = 0.0

    model_config = {"use_enum_values": True}


# ---------------------------------------------------------------------------
# Q4 — Portfolio allocation
# ---------------------------------------------------------------------------

class Q4Portfolio(BaseModel):
    """
    Answer to: "How should I allocate my portfolio?"
    Produced by: FinRL, FinRL-X, TradingAgents (PM stage), Vibe-Trading
    """
    weights:         Dict[str, float] = Field(...,
                         description="ticker → portfolio weight, values must sum ≤ 1.0")
    cash_ratio:      float            = Field(..., ge=0.0, le=1.0)
    rationale:       str
    regime:          Optional[Regime] = None
    rebalance_freq:  Optional[str]    = None   # "DAILY" | "WEEKLY" | "MONTHLY"

    adapter:         str   = ""
    date:            str   = ""
    cost_usd:        float = 0.0
    latency_sec:     float = 0.0

    model_config = {"use_enum_values": True}

    @field_validator("weights")
    @classmethod
    def weights_sum_valid(cls, v: Dict[str, float]) -> Dict[str, float]:
        total = sum(v.values())
        if total > 1.001:
            raise ValueError(f"weights sum {total:.4f} exceeds 1.0")
        if any(w < 0 for w in v.values()):
            raise ValueError("all weights must be non-negative")
        return v


# ---------------------------------------------------------------------------
# Q5 — Backtest / strategy validation
# ---------------------------------------------------------------------------

class Q5Backtest(BaseModel):
    """
    Answer to: "How has this strategy performed historically?"
    Produced by: AgenticTrading, FinRL/FinRL-X, Vibe-Trading, Prediction Arena
    """
    total_return:          float
    sharpe:                Optional[float]  = None
    max_drawdown:          Optional[float]  = None   # negative, e.g. -0.13
    alpha_vs_benchmark:    Optional[float]  = None   # excess return over benchmark
    calmar:                Optional[float]  = None
    win_rate:              Optional[float]  = Field(None, ge=0.0, le=1.0)
    equity_curve:          List[float]      = Field(default_factory=list,
                                                    description="Normalised NAV series (start=1.0)")
    benchmark:             str              = "equal_weight_bnh"
    train_period:          Optional[str]    = None   # "2020-01-01/2022-12-31"
    test_period:           Optional[str]    = None   # "2024-01-01/2024-03-31"

    adapter:               str   = ""
    cost_usd:              float = 0.0
    latency_sec:           float = 0.0

    model_config = {"use_enum_values": True}


# ---------------------------------------------------------------------------
# Envelope — one result file per (adapter, task)
# ---------------------------------------------------------------------------

class AdapterResult(BaseModel):
    """
    The top-level object written to results/{task_id}/{adapter_name}.json.
    At least one of q1/q2/q3/q4/q5 must be non-null.
    """
    adapter:       str
    task_id:       str
    adapter_version: str = "0.1.0"

    q1: Optional[Q1Decision]  = None
    q2: Optional[Q2Sentiment] = None
    q3: Optional[Q3Signal]    = None
    q4: Optional[Q4Portfolio] = None
    q5: Optional[Q5Backtest]  = None

    native_output: dict  = Field(default_factory=dict,
                                 description="Raw upstream output, unmodified")
    adapter_notes: str   = ""

    @field_validator("q1", "q2", "q3", "q4", "q5", mode="before")
    @classmethod
    def at_least_one_answer(cls, v):
        return v

    def model_post_init(self, __context):
        answers = [self.q1, self.q2, self.q3, self.q4, self.q5]
        if all(a is None for a in answers):
            raise ValueError("AdapterResult must populate at least one of q1/q2/q3/q4/q5")
