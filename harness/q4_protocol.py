"""
harness/q4_protocol.py — the Q4 stepwise data contract.

Pure data model + structural protocol. No I/O, no subprocess, no adapter
imports (importable from any conda env with only pydantic installed —
matching CONTRACT/test_harness.py's own "stdlib+pydantic only" convention).

This module does NOT modify CONTRACT/schemas.py. It reuses the real, frozen
CONTRACT.schemas classes (QueryContext, TimeWindow, PolicyType, UpdateMode,
UpdatePolicy, UniversePolicy, PortfolioConstraints, PolicyArtifact,
PolicyDecisionStep, Q4Policy) directly and wraps them with harness-side
session/observation/execution types that the schema itself anticipates but
does not define — see Q4Policy's own docstring: "on each legal rebalance
point during sequential execution the harness calls the adapter again and
accumulates one PolicyDecisionStep per call" (CONTRACT/schemas.py:559-562).

Design note on Q4StepAdapter: this is a *structural* typing.Protocol
(PEP 544), not an ABC. An adapter gains STEPWISE capability by defining
q4_initialize/q4_step/q4_finalize directly on its existing BaseAdapter
subclass — zero changes to CONTRACT/base_adapter.py are required.
isinstance(adapter, Q4StepAdapter) (the Protocol is @runtime_checkable) is
how harness/q4_runtime.py's worker decides whether to run the real stepwise
path or fall back to LEGACY_INTERNAL_LOOP replay of the existing
q4_policy() method.
"""

from __future__ import annotations

import sys
from enum import Enum
from typing import Any, Dict, List, Optional

# Literal/Protocol/runtime_checkable are stdlib only from Python 3.8+; some
# real adapter conda envs are pinned to Python 3.7 for a genuine upstream
# reason (e.g. pgportfolio_real needs TF1.15.5, which has no 3.8+ wheel on
# this platform — verified). typing_extensions (already a real dependency of
# several adapters in this repo) backports identical semantics.
if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, runtime_checkable
else:
    from typing_extensions import Literal, Protocol, runtime_checkable

from pydantic import Field, model_validator

from CONTRACT.schemas import (
    ContractModel,
    PolicyArtifact,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q4Policy,
    QueryContext,
    TimeWindow,
    UniversePolicy,
    UpdatePolicy,
)


# ---------------------------------------------------------------------------
# Classification / status vocabularies
# ---------------------------------------------------------------------------

class Q4AdapterClassification(str, Enum):
    """
    An adapter's structural capability under the stepwise protocol — this is
    a property of the adapter's real upstream mechanism, decided once via
    source-code investigation, not a per-run outcome (see RunStatus below
    for that). Used in q4_stepwise_support.csv.
    """
    STEPWISE = "STEPWISE"
    # Adapter has no q4_initialize/q4_step/q4_finalize methods; the harness
    # falls back to calling its existing q4_policy() once and replaying its
    # decisions list one PolicyDecisionStep per harness step.
    LEGACY_INTERNAL_LOOP = "LEGACY_INTERNAL_LOOP"
    # Real upstream mechanism is a single closed-form / one-shot computation
    # with no sequential structure at all — forcing a per-step trajectory
    # would fabricate one the real project does not produce.
    STATIC_ONLY = "STATIC_ONLY"
    # Real, pre-existing external/upstream blocker unrelated to stepwise
    # design (e.g. a dead upstream data API, a missing credential) — carried
    # forward from prior live-verification findings, not re-litigated here.
    BLOCKED = "BLOCKED"


class RunStatus(str, Enum):
    """Per-run-attempt outcome vocabulary (harness/tools layer, not schema)."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    NOT_RUN = "NOT_RUN"
    STEPWISE_UNSUPPORTED = "STEPWISE_UNSUPPORTED"


# ---------------------------------------------------------------------------
# Harness-side exceptions (parallel to, but outside, CONTRACT/base_adapter.py)
# ---------------------------------------------------------------------------

class Q4CausalityViolation(RuntimeError):
    """
    Raised when a real PolicyDecisionStep from a real q4_step() call violates
    a causality invariant the schema documents but does not itself enforce:
    CONTRACT/schemas.py's PolicyDecisionStep docstring states "information_
    cutoff must be <= timestamp... safe ordering comparison is left to a
    layer that can parse a guaranteed datetime format" (schemas.py:464-468)
    — this harness is that layer. A causality violation invalidates the
    whole session's evaluability and is a hard stop by default
    (Q4RunConfig.fail_fast), not a soft warning.
    """


class Q4ConstraintViolation(RuntimeError):
    """
    Raised (in "reject" projection_mode) when a real decision's weights
    violate PortfolioConstraints and the harness is configured to refuse
    rather than project them into compliance. In "clip" mode, violations are
    projected and logged into ExecutionResult.constraint_violations instead
    of raised.
    """


# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

class MarketObservation(ContractModel):
    """
    What the harness discloses to an adapter at one decision timestep.
    Deliberately does not carry a full lookback panel per step (would
    re-serialize e.g. a 250-day window on every call) — adapters needing a
    lookback window either maintain their own state across q4_step() calls
    (the normal case — see per-adapter migration notes) or read it from
    their own already-loaded dataset, using `timestamp` purely as an index.
    """
    step_index:        int = Field(..., ge=0)
    timestamp:         str = Field(..., description="The date/time this observation is disclosed for.")
    information_cutoff: str = Field(..., description="Latest information timestamp this observation may legally reflect.")
    universe:          List[str] = Field(default_factory=list)
    is_rebalance_point: bool = True

    bar:      Optional[Dict[str, dict]] = Field(None, description="Optional per-asset OHLCV for this one timestamp, keyed by ticker.")
    features: Optional[Dict[str, Any]] = Field(None, description="Optional adapter-specific precomputed features for this timestamp.")

    @model_validator(mode="after")
    def _cutoff_not_after_timestamp(self) -> "MarketObservation":
        # String comparison is a deliberate, documented limitation here (ISO
        # 8601 'YYYY-MM-DD'-shaped strings sort correctly lexicographically);
        # execution_engine.py's _parse_ts does real datetime parsing for the
        # authoritative check against adapter-returned decisions. This is a
        # cheap early sanity check on harness-constructed observations only.
        if self.information_cutoff > self.timestamp:
            raise ValueError(
                f"MarketObservation.information_cutoff ({self.information_cutoff!r}) "
                f"must not be after timestamp ({self.timestamp!r})"
            )
        return self


class PortfolioState(ContractModel):
    """
    The real, harness-maintained portfolio ledger passed to q4_step() and
    updated by harness/portfolio_state.py::PortfolioLedger.advance() after
    each decision — adapters read this, they do not maintain their own
    parallel unverifiable ledger.
    """
    as_of:       str
    weights:     Dict[str, float] = Field(default_factory=dict, description='Asset -> weight, "CASH" for cash, same convention as PolicyDecisionStep.target_weights.')
    nav:         float = Field(1.0, description="Portfolio net asset value, normalized to 1.0 at session start unless overridden by Q4RunConfig.initial_cash.")
    step_index:  int = Field(0, ge=0)
    last_rebalance_timestamp: Optional[str] = None


class Q4RunConfig(ContractModel):
    """
    Everything the harness decides and discloses to a session up front —
    the adapter may read this but, per the same echo-back discipline
    CONTRACT/base_adapter.py already enforces for generation_window, must
    not alter context/generation_window/rebalance_schedule.
    """
    task_id:            str
    session_id:          str
    context:             QueryContext
    generation_window:   TimeWindow
    rebalance_schedule:  List[str] = Field(default_factory=list, description="Harness-decided legal decision dates. The adapter does not choose rebalance timing.")
    constraints:          Optional[PortfolioConstraints] = None
    initial_weights:      Optional[Dict[str, float]] = None
    initial_cash:         float = 1.0
    projection_mode:      Literal["clip", "reject"] = "clip"
    fail_fast:            bool = True
    max_steps:            Optional[int] = None
    adapter_kwargs:        Dict[str, str] = Field(default_factory=dict)
    audit_mode:           bool = False


class Q4AdapterSession(ContractModel):
    """
    Worker-side (in-process, inside the adapter's own conda env) session
    handle. Only the JSON-safe bookkeeping fields cross a process boundary
    (via harness/q4_runtime.py's RemoteQ4StepAdapterProxy); the real opaque
    adapter state (a trained model, a live upstream Account/env object, an
    algorithm's running A/b matrices) never leaves the worker process and is
    therefore intentionally NOT a field here — it lives only in the worker's
    local Python memory, keyed by session_id.
    """
    session_id:  str
    adapter_name: str
    step_count:  int = 0
    initialized: bool = False
    finalized:   bool = False


class ExecutionResult(ContractModel):
    """One real q4_step() call's full outcome, including harness-side
    causality/constraint bookkeeping the adapter itself does not compute."""
    step_index:        int
    decision:           PolicyDecisionStep
    pre_trade_state:    PortfolioState
    post_trade_state:   Optional[PortfolioState] = None
    constraint_violations: List[str] = Field(default_factory=list)
    projection_applied:  bool = False
    causality_ok:        bool = True
    latency_sec:         float = Field(0.0, ge=0.0)
    raw_native_output:   Optional[dict] = None
    error:               Optional[str] = None


class Q4FinalizeSummary(ContractModel):
    """The parts of a Q4Policy that are naturally only known at session end."""
    policy_type:      PolicyType
    update_policy:     Optional[UpdatePolicy] = None
    universe_policy:   Optional[UniversePolicy] = None
    artifact:          Optional[PolicyArtifact] = None
    explanation:       Optional[str] = None


class Q4RunResult(ContractModel):
    """The full assembled outcome of one Q4ExecutionEngine.run() call."""
    session_id:   str
    adapter_name:  str
    classification: Q4AdapterClassification
    policy:        Q4Policy
    results:       List[ExecutionResult]
    n_steps:       int
    n_causality_violations: int
    n_constraint_violations: int
    n_projections_applied: int
    total_latency_sec: float


# ---------------------------------------------------------------------------
# Structural protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class Q4StepAdapter(Protocol):
    """
    Structural interface a real adapter opts into by defining these three
    methods directly (no base-class change required). See per-adapter
    migration notes in Q4_STEPWISE_MIGRATION.md for which real upstream
    calls populate each method for each of the 13 currently Q4-capable
    adapters.
    """

    def q4_initialize(
        self,
        context: QueryContext,
        generation_window: TimeWindow,
        initial_portfolio: PortfolioState,
        run_config: Q4RunConfig,
    ) -> Q4Policy:
        """
        Called exactly once per session. May: use generation_window data
        only, train/load/freeze a model, construct a policy artifact,
        initialize internal state, return real policy metadata (policy_type
        at minimum). Must NOT read test-window/future data.
        """
        ...

    def q4_step(
        self,
        timestamp: str,
        information_cutoff: str,
        observation: MarketObservation,
        portfolio_state: PortfolioState,
    ) -> PolicyDecisionStep:
        """
        Called once per legal rebalance point. Must return exactly one
        PolicyDecisionStep satisfying information_cutoff <= timestamp. Must
        not read data beyond information_cutoff or precompute the whole
        window's decisions in one call.
        """
        ...

    def q4_finalize(self) -> Q4Policy:
        """
        Called exactly once at session end. Returns final policy metadata
        (artifact, update_policy, explanation) — the accumulated `decisions`
        trajectory itself is assembled by harness/execution_engine.py from
        the harness's own accumulated ExecutionResults, not returned here
        (matching Q4Policy's own docstring: "the full decision trajectory is
        normally accumulated by the harness across those calls").
        """
        ...
