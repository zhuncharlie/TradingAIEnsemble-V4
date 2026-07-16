"""
CONTRACT/schemas.py — Canonical adapter output schemas for four trading questions.

This is the shared contract between all adapters. Every adapter must import
from here and return instances of these classes. The schema is problem-driven,
not project-driven: it encodes the four research questions (Q1 Action,
Q2 State, Q3 Signal/Alpha, Q4 Policy), not the union of fields any one
upstream project happens to expose. Fields changing requires a version bump
(SCHEMA_VERSION) and sign-off from the project maintainer.

This is a breaking v2.0.0 rewrite of the v1 five-question contract
(Q1 Decision / Q2 Sentiment / Q3 Signal / Q4 Portfolio / Q5 Backtest). Q5 is
removed; Q1/Q2/Q4 are redefined. No v1 aliases are kept — see
milestones/2026-07-16_schema-v1-milestone.md for the v1 rollback point.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

SCHEMA_VERSION = "2.0.0"


# ---------------------------------------------------------------------------
# Shared base model
# ---------------------------------------------------------------------------

class ContractModel(BaseModel):
    """Base class for every schema in this file — shared validation policy."""

    model_config = {
        "use_enum_values": True,
        "extra": "forbid",
        "allow_inf_nan": False,
    }


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class Action(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Direction(str, Enum):
    LONG    = "LONG"
    SHORT   = "SHORT"
    NEUTRAL = "NEUTRAL"


class OutputScope(str, Enum):
    """What the output is about: one asset, the whole market, a cross-section, etc."""
    ASSET         = "ASSET"
    MARKET        = "MARKET"
    CROSS_SECTION = "CROSS_SECTION"
    PORTFOLIO     = "PORTFOLIO"
    MULTI_MARKET  = "MULTI_MARKET"


class ConfidenceKind(str, Enum):
    """What kind of quantity a ConfidenceEstimate.value actually is."""
    PROBABILITY       = "PROBABILITY"
    SELF_REPORTED     = "SELF_REPORTED"
    MODEL_MARGIN      = "MODEL_MARGIN"
    SCORE_NORMALIZED  = "SCORE_NORMALIZED"
    ENTROPY_DERIVED   = "ENTROPY_DERIVED"
    HEURISTIC         = "HEURISTIC"


class FieldSourceType(str, Enum):
    """Provenance of a canonical field, for later coverage/compression analysis."""
    NATIVE           = "NATIVE"
    DERIVED          = "DERIVED"
    HARNESS_SUPPLIED = "HARNESS_SUPPLIED"
    MISSING          = "MISSING"


class PolicyType(str, Enum):
    """The lifecycle shape of a Q4 policy."""
    STATIC_ALLOCATION      = "STATIC_ALLOCATION"
    ROLLING_OPTIMIZER      = "ROLLING_OPTIMIZER"
    FROZEN_LEARNED_POLICY  = "FROZEN_LEARNED_POLICY"
    ONLINE_ADAPTIVE_POLICY = "ONLINE_ADAPTIVE_POLICY"


class UpdateMode(str, Enum):
    """How (if at all) a Q4 policy changes state after generation."""
    NONE             = "NONE"
    STATE_UPDATE     = "STATE_UPDATE"
    ROLLING_REFIT    = "ROLLING_REFIT"
    ONLINE_LEARNING  = "ONLINE_LEARNING"


# ---------------------------------------------------------------------------
# Shared time / target-object context
# ---------------------------------------------------------------------------

class QueryContext(ContractModel):
    """
    Shared temporal and target-object context every Q layer attaches to its
    output. Replaces the old per-Q `ticker`/`date` pair so a single asset,
    a market, a cross-section, or a portfolio can all be described uniformly.
    """
    as_of:       str = Field(..., description="Decision or observation timestamp this output corresponds to.")
    data_cutoff: str = Field(..., description="Latest information timestamp the adapter used; used to check for future-information leakage.")
    scope:       OutputScope = Field(..., description="Whether this output is about a single asset, the market, a cross-section, a portfolio, or multiple markets.")
    targets:     Optional[List[str]] = Field(None, description="Objects this output directly targets.")
    universe:    Optional[List[str]] = Field(None, description="Concrete asset set visible/participating in this decision.")
    universe_id: Optional[str] = Field(None, description="Frozen universe/catalog identifier, used when the asset set is too large to enumerate.")
    horizon:     Optional[str] = Field(None, description="Time horizon the action, state, signal, or holding corresponds to.")

    @field_validator("as_of", "data_cutoff")
    @classmethod
    def _non_empty_timestamp(cls, v: str) -> str:
        if not v:
            raise ValueError("as_of and data_cutoff must be non-empty timestamp strings")
        return v


# ---------------------------------------------------------------------------
# Shared confidence model
# ---------------------------------------------------------------------------

class ConfidenceEstimate(ContractModel):
    """
    A typed confidence value. A bare [0,1] float can't distinguish a model
    probability from an LLM's self-reported conviction from a heuristic
    score normalization — `kind` makes that distinction explicit.
    """
    value:     float = Field(..., ge=0.0, le=1.0, description="Adapter-mapped value on a unified [0,1] scale.")
    kind:      ConfidenceKind = Field(..., description="Semantic source of `value` — required, must not be guessed.")
    raw_value: Optional[float] = Field(None, description="Original value before mapping to [0,1] (e.g. a logit or margin); may fall outside [0,1].")
    method:    Optional[str] = Field(None, description="Brief description of the mapping/derivation method.")


# ---------------------------------------------------------------------------
# Shared evidence model
# ---------------------------------------------------------------------------

class EvidenceItem(ContractModel):
    """A structured piece of evidence, kept separate from free-text explanation."""
    kind:      Optional[str] = Field(None, description="e.g. factor, news, filing, technical_indicator, macro, model_feature.")
    value:     Optional[str] = Field(None, description="Evidence content, factor name, or brief description.")
    source:    Optional[str] = Field(None, description="Data source or upstream module the evidence came from.")
    reference: Optional[str] = Field(None, description="URL, document ID, field path, or other traceable reference.")

    @model_validator(mode="after")
    def _at_least_one_populated(self) -> "EvidenceItem":
        if not any([self.kind, self.value, self.source, self.reference]):
            raise ValueError("EvidenceItem must provide at least one of kind/value/source/reference")
        return self


# ---------------------------------------------------------------------------
# Field-mapping provenance
# ---------------------------------------------------------------------------

class FieldMapping(ContractModel):
    """
    Records where one canonical field's value came from, for later coverage
    and compression-loss analysis. Does not compute coverage itself.
    """
    canonical_field: str = Field(..., description='Dotted path of the canonical field, e.g. "q1.confidence.value".')
    source_type:     FieldSourceType
    native_path:     Optional[str] = Field(None, description="Field path in the raw upstream output, if source_type is NATIVE or DERIVED.")
    transform:       Optional[str] = Field(None, description="Mapping, normalization, or derivation method applied.")
    assumptions:     Optional[List[str]] = Field(None, description="Assumptions the adapter introduced to complete this mapping.")
    loss_notes:      Optional[List[str]] = Field(None, description="Semantics lost in the process of this mapping.")

    @field_validator("canonical_field")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("canonical_field must be a non-empty dotted path")
        return v


# ---------------------------------------------------------------------------
# Run metadata
# ---------------------------------------------------------------------------

class RunMetadata(ContractModel):
    """Adapter/run identity and cost accounting — recorded once per envelope, not once per Q."""
    adapter:          str = Field(..., description="Unique snake_case adapter identifier.")
    adapter_version:  str = "0.1.0"
    schema_version:   str = SCHEMA_VERSION
    run_id:           Optional[str] = None
    upstream_project: Optional[str] = None
    upstream_version: Optional[str] = None
    upstream_commit:  Optional[str] = None
    model_name:       Optional[str] = None
    config_hash:      Optional[str] = None
    cost_usd:         float = Field(default=0.0, ge=0.0)
    latency_sec:      float = Field(default=0.0, ge=0.0)

    @field_validator("adapter")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("adapter identifier must be non-empty")
        return v


# ---------------------------------------------------------------------------
# Q1 — Action: "What should be done right now?"
# ---------------------------------------------------------------------------

class Q1Action(ContractModel):
    """
    Answers Q1: what action should be taken right now. `action` is the only
    required core field — everything else (strength, target position,
    confidence, textual justification, evidence) is optional so that
    non-text-generating projects aren't forced to fabricate explanations.
    """
    context: QueryContext

    action:           Action
    action_semantics: Optional[str] = Field(None, description="What BUY/SELL/HOLD concretely means here, e.g. open position, trim, enter ranked pool, target direction.")
    action_strength:  Optional[float] = Field(None, ge=0.0, le=1.0, description="Strength of the action — distinct from confidence.")
    target_position:  Optional[float] = Field(None, description="Native target position size if the project supports it; may be negative (not forced long-only).")

    confidence:  Optional[ConfidenceEstimate] = None
    explanation: Optional[str] = None
    bull_case:   Optional[str] = None
    bear_case:   Optional[str] = None
    evidence:    Optional[List[EvidenceItem]] = None


# ---------------------------------------------------------------------------
# Q2 — State / Sentiment / Context: "What state is the object/market in?"
# ---------------------------------------------------------------------------

class StateEstimate(ContractModel):
    """
    One state dimension. `dimension` is an open string (sentiment, risk,
    volatility, liquidity, market_regime, macro_condition, event_context,
    uncertainty, positioning, ...) rather than a closed enum, since Q2's
    state space is not fixed in advance. At least one of value_numeric /
    value_category / value_text / value_distribution must be provided.
    """
    dimension: str = Field(..., description="Open-vocabulary state dimension name, e.g. 'sentiment', 'market_regime'.")

    value_numeric:      Optional[float] = None
    value_category:      Optional[str] = None
    value_text:          Optional[str] = None
    value_distribution:  Optional[Dict[str, float]] = Field(None, description="Probability/weight over open-vocabulary category labels. Not required to sum to 1.")

    scale:              Optional[str] = Field(None, description='Value scale, e.g. "[-1,1]" or "probability_distribution".')
    observation_window:  Optional[str] = Field(None, description="How far into the past this state estimate looks, e.g. '7d' or '20_trading_days'. Distinct from context.horizon, which is how far into the future the state is expected to apply.")
    confidence:          Optional[ConfidenceEstimate] = None
    evidence:            Optional[List[EvidenceItem]] = None

    @field_validator("dimension")
    @classmethod
    def _dimension_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("dimension must be a non-empty string")
        return v

    @field_validator("value_distribution")
    @classmethod
    def _distribution_valid(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return v
        if not v:
            raise ValueError("value_distribution, if provided, must not be empty")
        for k, val in v.items():
            if not k:
                raise ValueError("value_distribution keys must not be empty")
            if val < 0:
                raise ValueError(f"value_distribution value for {k!r} must be non-negative")
        return v

    @model_validator(mode="after")
    def _at_least_one_value(self) -> "StateEstimate":
        if all(x is None for x in (self.value_numeric, self.value_category, self.value_text, self.value_distribution)):
            raise ValueError(
                "StateEstimate must provide at least one state value representation "
                "(value_numeric/value_category/value_text/value_distribution)"
            )
        return self


class Q2State(ContractModel):
    """
    Answers Q2: what state is the current object or market in. A list of
    `StateEstimate`s rather than a fixed sentiment_score/risk_level/drivers
    triple, so adapters aren't forced to populate dimensions they don't
    natively support.
    """
    context: QueryContext
    states:  List[StateEstimate] = Field(..., min_length=1)
    explanation: Optional[str] = None


# ---------------------------------------------------------------------------
# Q3 — Signal / Alpha: "What testable predictive signal exists?"
# ---------------------------------------------------------------------------

class Q3Signal(ContractModel):
    """
    Answers Q3: what testable predictive signal or alpha currently exists.
    `values` is a target-id -> numeric-value map so single-asset signals and
    cross-sectional/multi-asset signals share one representation.
    """
    context: QueryContext

    signal_semantics: str = Field(..., description="What the numbers in `values` mean, e.g. predicted_return, return_probability, ranking_score, factor_value, anomaly_score, directional_score.")
    values:           Dict[str, float] = Field(..., description="target_id -> signal value. Must contain at least one entry.")

    score_scale:        Optional[str] = None
    direction:          Optional[Direction] = None
    strength:           Optional[float] = Field(None, ge=0.0, le=1.0)

    expected_returns:   Optional[Dict[str, float]] = None
    factor_expression:  Optional[str] = None
    confidence:         Optional[ConfidenceEstimate] = None
    evidence:           Optional[List[EvidenceItem]] = None
    explanation:        Optional[str] = None

    @field_validator("signal_semantics")
    @classmethod
    def _semantics_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("signal_semantics must be a non-empty string")
        return v

    @field_validator("values")
    @classmethod
    def _values_valid(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("values must contain at least one target_id -> value entry")
        for k in v:
            if not k:
                raise ValueError("values keys (target identifiers) must not be empty")
        return v

    @field_validator("expected_returns")
    @classmethod
    def _expected_returns_valid(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return v
        for k in v:
            if not k:
                raise ValueError("expected_returns keys must not be empty")
        return v


# ---------------------------------------------------------------------------
# Q4 — Policy: "How is the strategy formed and updated over continuous time?"
# ---------------------------------------------------------------------------

class TimeWindow(ContractModel):
    """A start/end time window, e.g. a policy's generation window."""
    start: str
    end:   str

    @field_validator("start", "end")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("TimeWindow start/end must be non-empty")
        return v


class UniversePolicy(ContractModel):
    """How the tradable asset set is determined — fixed, adapter-selected, dynamic, or catalog-constrained."""
    mode: str = Field(..., description="e.g. fixed, adapter_selected, dynamic, catalog_constrained.")
    catalog_id:            Optional[str] = None
    fixed_assets:          Optional[List[str]] = None
    allowed_markets:       Optional[List[str]] = None
    allowed_asset_classes: Optional[List[str]] = None
    selection_frequency:   Optional[str] = None
    max_assets:            Optional[int] = Field(None, ge=1)
    selector_description:  Optional[str] = None

    @field_validator("mode")
    @classmethod
    def _mode_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("UniversePolicy.mode must be non-empty")
        return v


class ObservationPolicy(ContractModel):
    """What information the policy observes before deciding."""
    lookback_window:         Optional[str] = None
    features:                Optional[List[str]] = None
    data_sources:            Optional[List[str]] = None
    observation_description: Optional[str] = None


class DecisionPolicy(ContractModel):
    """The rule the policy uses to turn observations into decisions."""
    decision_rule:       Optional[str] = None
    output_semantics:    Optional[str] = None
    rebalance_frequency: Optional[str] = None
    holding_horizon:     Optional[str] = None


class UpdatePolicy(ContractModel):
    """How (if at all) the policy changes after generation — see UpdateMode."""
    mode:               UpdateMode
    update_frequency:   Optional[str] = None
    update_description: Optional[str] = None


class PortfolioConstraints(ContractModel):
    """
    Explicit portfolio constraints. Nothing here is a default: if a field is
    None, no corresponding check is applied. Q4 does not globally assume
    long-only, no-leverage, or weights-sum-to-1.
    """
    long_only:            Optional[bool] = None
    cash_allowed:         Optional[bool] = None
    max_abs_weight:       Optional[float] = Field(None, ge=0.0)
    gross_exposure_limit: Optional[float] = Field(None, ge=0.0)
    net_exposure_min:     Optional[float] = None
    net_exposure_max:     Optional[float] = None
    leverage_limit:       Optional[float] = Field(None, ge=0.0)
    turnover_limit:       Optional[float] = Field(None, ge=0.0)
    additional_constraints: Optional[List[str]] = None

    @model_validator(mode="after")
    def _net_exposure_order(self) -> "PortfolioConstraints":
        if self.net_exposure_min is not None and self.net_exposure_max is not None:
            if self.net_exposure_min > self.net_exposure_max:
                raise ValueError("net_exposure_min must be <= net_exposure_max")
        return self


class PolicyArtifact(ContractModel):
    """A lightweight reference to a policy artifact — checkpoint, serialized policy, strategy code, etc. Not the artifact itself."""
    artifact_type: str = Field(..., description="e.g. model_checkpoint, serialized_policy, strategy_code, factor_pipeline, optimizer_config.")
    reference:     Optional[str] = None
    hash:          Optional[str] = None
    description:   Optional[str] = None

    @field_validator("artifact_type")
    @classmethod
    def _type_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("artifact_type must be non-empty")
        return v


class PolicyDecisionStep(ContractModel):
    """
    A single causal decision output at one point in time — not a
    pre-generated future trajectory. A rolling or online policy is expected
    to be called once per legal rebalance point during sequential execution
    and to return one PolicyDecisionStep each time; the full decision
    trajectory is normally accumulated by the harness across those calls,
    not predicted and filled in upfront by the adapter during policy
    generation. Carries no return/NAV/Sharpe/drawdown/benchmark information
    — those belong to the evaluation layer.

    Causality: `information_cutoff` must be <= `timestamp` (the decision may
    not use information from after its own cutoff). Only non-empty checks
    are enforced here since these are free-form timestamp strings; safe
    ordering comparison is left to a layer that can parse a guaranteed
    datetime format.
    """
    timestamp:           str = Field(..., description="When this decision applies.")
    information_cutoff:  str = Field(..., description="Latest information timestamp used to produce this decision. Must be <= timestamp.")

    selected_universe:   Optional[List[str]] = None
    target_weights:      Optional[Dict[str, float]] = Field(None, description='Asset -> weight. Use "CASH" as the cash asset key; weights may be negative (no long-only default).')
    orders:              Optional[List[dict]] = None

    turnover:              Optional[float] = Field(None, ge=0.0)
    constraint_violations: Optional[List[str]] = None
    explanation:           Optional[str] = None

    @field_validator("timestamp", "information_cutoff")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("timestamp and information_cutoff must be non-empty")
        return v

    @field_validator("target_weights")
    @classmethod
    def _weights_keys_valid(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return v
        for k in v:
            if not k:
                raise ValueError("target_weights keys must not be empty")
        return v


_WEIGHT_TOLERANCE = 1e-6


def _check_weights_against_constraints(
    label: str,
    weights: Dict[str, float],
    constraints: Optional[PortfolioConstraints],
) -> None:
    """Shared weight-constraint check for Q4Policy.initial_weights and each PolicyDecisionStep.target_weights."""
    if constraints is None:
        return

    if constraints.long_only:
        for asset, w in weights.items():
            if w < -_WEIGHT_TOLERANCE:
                raise ValueError(f"{label}: negative weight {w} for {asset!r} violates long_only constraint")

    if constraints.max_abs_weight is not None:
        for asset, w in weights.items():
            if abs(w) > constraints.max_abs_weight + _WEIGHT_TOLERANCE:
                raise ValueError(
                    f"{label}: abs(weight)={abs(w)} for {asset!r} exceeds "
                    f"max_abs_weight={constraints.max_abs_weight}"
                )

    if constraints.gross_exposure_limit is not None:
        gross = sum(abs(w) for w in weights.values())
        if gross > constraints.gross_exposure_limit + _WEIGHT_TOLERANCE:
            raise ValueError(
                f"{label}: gross exposure {gross} exceeds "
                f"gross_exposure_limit={constraints.gross_exposure_limit}"
            )

    net = sum(weights.values())
    if constraints.net_exposure_min is not None and net < constraints.net_exposure_min - _WEIGHT_TOLERANCE:
        raise ValueError(f"{label}: net exposure {net} below net_exposure_min={constraints.net_exposure_min}")
    if constraints.net_exposure_max is not None and net > constraints.net_exposure_max + _WEIGHT_TOLERANCE:
        raise ValueError(f"{label}: net exposure {net} exceeds net_exposure_max={constraints.net_exposure_max}")


class Q4Policy(ContractModel):
    """
    Answers Q4: how the system forms and updates an investment policy over
    continuous time. Covers single-point allocations, rolling optimizers,
    frozen learned policies, and online adaptive policies through one shape:
    a policy_type, optional universe/observation/decision/update sub-policies,
    optional constraints, and at least one of initial_weights / artifact /
    decisions / decision_policy.decision_rule as an executable representation.

    By convention only (not enforced by a validator, to avoid rejecting
    legitimate upstream projects that don't fit the common case):
    ROLLING_OPTIMIZER policies typically carry update_policy.mode=
    ROLLING_REFIT; ONLINE_ADAPTIVE_POLICY policies typically carry
    ONLINE_LEARNING or STATE_UPDATE.

    Market regime is deliberately not a field here — it lives on Q2 as an
    open StateEstimate.dimension ("market_regime"), since regime is a state
    of the world, not a property of a policy. A policy may reference it by
    name in observation_policy.features.

    `decisions` is optional and does not need to be populated upfront for a
    rolling or online policy: on each legal rebalance point during
    sequential execution the harness calls the adapter again and
    accumulates one PolicyDecisionStep per call. `decisions` here exists to
    carry decisions a project has already produced (historical replay,
    single-run projects that return several already-realized decisions,
    static policies), not to require predicting the future at generation
    time.
    """
    context:           QueryContext
    policy_type:       PolicyType
    generation_window: TimeWindow = Field(
        ...,
        description=(
            "Harness-supplied strategy generation interval. The adapter "
            "records this interval but must not choose, expand, shorten, "
            "or otherwise alter it. Validation/test windows are not part "
            "of this contract — they belong to the harness/experiment "
            "execution layer, not to the adapter's policy output."
        ),
    )

    universe_policy:     Optional[UniversePolicy] = None
    observation_policy:  Optional[ObservationPolicy] = None
    decision_policy:     Optional[DecisionPolicy] = None
    update_policy:       Optional[UpdatePolicy] = None
    constraints:         Optional[PortfolioConstraints] = None

    initial_weights: Optional[Dict[str, float]] = None
    artifact:        Optional[PolicyArtifact] = None
    decisions:       Optional[List[PolicyDecisionStep]] = None

    explanation: Optional[str] = None

    @field_validator("initial_weights")
    @classmethod
    def _initial_weights_keys_valid(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return v
        for k in v:
            if not k:
                raise ValueError("initial_weights keys must not be empty")
        return v

    @model_validator(mode="after")
    def _has_executable_representation(self) -> "Q4Policy":
        has_initial_weights = bool(self.initial_weights)
        has_artifact = self.artifact is not None
        has_decisions = bool(self.decisions)
        has_decision_rule = bool(self.decision_policy and self.decision_policy.decision_rule)
        if not (has_initial_weights or has_artifact or has_decisions or has_decision_rule):
            raise ValueError(
                "Q4Policy must provide at least one executable policy representation "
                "(initial_weights, artifact, decisions, or decision_policy.decision_rule)"
            )
        return self

    @model_validator(mode="after")
    def _weights_respect_constraints(self) -> "Q4Policy":
        if self.initial_weights:
            _check_weights_against_constraints("initial_weights", self.initial_weights, self.constraints)
        if self.decisions:
            for i, step in enumerate(self.decisions):
                if step.target_weights:
                    _check_weights_against_constraints(
                        f"decisions[{i}].target_weights", step.target_weights, self.constraints
                    )
        return self


# ---------------------------------------------------------------------------
# Envelope — one result file per (adapter, task)
# ---------------------------------------------------------------------------

class AdapterResult(ContractModel):
    """
    The top-level object written to results/{task_id}/{adapter_name}.json.
    At least one of q1/q2/q3/q4 must be non-null. Adapter identity, version,
    and cost/latency live only in `run` — not duplicated per-question.
    """
    task_id: str
    run:     RunMetadata

    q1: Optional[Q1Action] = None
    q2: Optional[Q2State]  = None
    q3: Optional[Q3Signal] = None
    q4: Optional[Q4Policy] = None

    native_output:  dict = Field(default_factory=dict, description="Raw upstream output, unmodified.")
    field_mappings: Optional[List[FieldMapping]] = None
    adapter_notes:  Optional[str] = None

    @field_validator("task_id")
    @classmethod
    def _task_id_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("task_id must be non-empty")
        return v

    @model_validator(mode="after")
    def _at_least_one_answer(self) -> "AdapterResult":
        if all(a is None for a in (self.q1, self.q2, self.q3, self.q4)):
            raise ValueError("AdapterResult must populate at least one of q1/q2/q3/q4")
        return self
