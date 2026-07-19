"""
harness/execution_engine.py — the transport-agnostic Q4 stepwise driver.

Q4ExecutionEngine works identically whether the adapter passed to it is a
real in-process object (for fast, no-subprocess unit tests) or
harness.q4_runtime.RemoteQ4StepAdapterProxy (a real conda-env subprocess
session) — it only depends on the structural harness.q4_protocol.Q4StepAdapter
interface.

This module is also where CONTRACT/schemas.py::PolicyDecisionStep's
documented-but-unenforced causality rule is actually enforced:
    "information_cutoff must be <= timestamp ... safe ordering comparison is
    left to a layer that can parse a guaranteed datetime format."
    (CONTRACT/schemas.py:464-468)
This module is that layer. Nothing here modifies CONTRACT/schemas.py.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import List, Optional

from CONTRACT.schemas import PolicyDecisionStep, Q4Policy, QueryContext, TimeWindow

from harness.portfolio_state import CASH_KEY, PortfolioLedger, apply_constraints
from harness.q4_protocol import (
    ExecutionResult,
    MarketObservation,
    Q4AdapterClassification,
    Q4CausalityViolation,
    PortfolioState,
    Q4RunConfig,
    Q4RunResult,
    Q4StepAdapter,
)


def _parse_ts(value: str) -> datetime:
    """
    Real datetime parsing for a guaranteed-comparable value — the exact gap
    PolicyDecisionStep's own docstring names ("a layer that can parse a
    guaranteed datetime format"). Tries ISO-8601 first (the convention every
    adapter in this repo already uses for as_of/timestamp/information_cutoff
    strings), falls back to pandas.Timestamp for looser formats if pandas is
    importable, raises Q4CausalityViolation (not a bare parse error) so
    callers get one consistent exception type for every causality failure
    mode.
    """
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    try:
        import pandas as pd  # local import: harness/q4_protocol.py stays pandas-free
        ts = pd.Timestamp(value)
        return ts.to_pydatetime()
    except Exception as e:
        raise Q4CausalityViolation(f"could not parse timestamp {value!r} as a date/time: {e}") from e


def enforce_causality(decision: PolicyDecisionStep, observation: MarketObservation) -> None:
    """
    Raises Q4CausalityViolation if:
      - decision.timestamp != observation.timestamp (decision must answer
        the observation it was actually given, not a different date);
      - information_cutoff > timestamp (the schema's own stated rule);
      - decision.information_cutoff > observation.information_cutoff (a
        strictly STRONGER check than the schema requires: catches an
        adapter that claims to have used information later than what the
        harness itself disclosed to it this step).
    """
    if decision.timestamp != observation.timestamp:
        raise Q4CausalityViolation(
            f"decision.timestamp={decision.timestamp!r} does not match "
            f"observation.timestamp={observation.timestamp!r} for step {observation.step_index}"
        )
    ts = _parse_ts(decision.timestamp)
    cutoff = _parse_ts(decision.information_cutoff)
    if cutoff > ts:
        raise Q4CausalityViolation(
            f"decision.information_cutoff={decision.information_cutoff!r} is after "
            f"decision.timestamp={decision.timestamp!r} at step {observation.step_index}"
        )
    obs_cutoff = _parse_ts(observation.information_cutoff)
    if cutoff > obs_cutoff:
        raise Q4CausalityViolation(
            f"decision.information_cutoff={decision.information_cutoff!r} is after the "
            f"harness-disclosed observation.information_cutoff={observation.information_cutoff!r} "
            f"at step {observation.step_index} — adapter claims to have used information "
            f"the harness never disclosed to it this step"
        )


def audit_trajectory(decisions: List[PolicyDecisionStep]) -> List[str]:
    """
    Static, whole-session re-check over the assembled decisions list:
    non-decreasing timestamps, no duplicate timestamps, every entry
    individually causal. Returns violation description strings (empty list
    = clean). Generalizes the ad hoc per-adapter checks several adapters'
    own smoke_test() methods already hand-write (e.g.
    adapters/universal_portfolios_adapter.py's causal-ordering assertions)
    into one shared, always-on harness function.
    """
    violations: List[str] = []
    prev_ts: Optional[datetime] = None
    prev_raw: Optional[str] = None
    for i, d in enumerate(decisions):
        try:
            ts = _parse_ts(d.timestamp)
            cutoff = _parse_ts(d.information_cutoff)
        except Q4CausalityViolation as e:
            violations.append(f"decisions[{i}]: {e}")
            continue
        if cutoff > ts:
            violations.append(
                f"decisions[{i}]: information_cutoff={d.information_cutoff!r} after timestamp={d.timestamp!r}"
            )
        if prev_ts is not None:
            if ts < prev_ts:
                violations.append(f"decisions[{i}]: timestamp={d.timestamp!r} is before decisions[{i-1}]={prev_raw!r}")
            elif ts == prev_ts:
                violations.append(f"decisions[{i}]: timestamp={d.timestamp!r} duplicates decisions[{i-1}]")
        prev_ts, prev_raw = ts, d.timestamp
    return violations


def _require_unchanged(label: str, supplied, returned) -> None:
    """Same echo-back discipline CONTRACT/base_adapter.py's
    _require_context_unchanged / generation_window check already enforce for
    BaseAdapter.run() — reimplemented here because a stepwise driver bypasses
    run() entirely, so those checks never fire automatically."""
    if supplied != returned:
        raise Q4CausalityViolation(  # reuse the same exception family: this is a harness-invariant violation, not a schema error
            f"{label} was altered by the adapter: supplied={supplied!r} returned={returned!r}"
        )


class Q4ExecutionEngine:
    """The sequential initialize -> N x step -> finalize driver."""

    def __init__(
        self,
        adapter: Q4StepAdapter,
        config: Q4RunConfig,
        observations: List[MarketObservation],
        classification: Q4AdapterClassification = Q4AdapterClassification.STEPWISE,
    ):
        self.adapter = adapter
        self.config = config
        self.observations = observations
        self.classification = classification

    def run(self) -> Q4RunResult:
        t_start = time.time()
        initial_state = PortfolioState(
            as_of=self.config.generation_window.end,
            weights=dict(self.config.initial_weights or {}),
            nav=self.config.initial_cash,
        )

        init_policy = self.adapter.q4_initialize(
            self.config.context, self.config.generation_window, initial_state, self.config,
        )
        _require_unchanged("context", self.config.context, init_policy.context)
        _require_unchanged("generation_window", self.config.generation_window, init_policy.generation_window)

        results: List[ExecutionResult] = []
        state = initial_state
        n_causality_violations = 0
        n_constraint_violations = 0
        n_projections = 0

        for obs in self.observations:
            if self.config.max_steps is not None and obs.step_index >= self.config.max_steps:
                break
            t0 = time.time()
            error: Optional[str] = None
            causality_ok = True
            pre_state = state
            try:
                decision = self.adapter.q4_step(obs.timestamp, obs.information_cutoff, obs, state)
                enforce_causality(decision, obs)
            except Q4CausalityViolation as e:
                n_causality_violations += 1
                causality_ok = False
                if self.config.fail_fast:
                    raise
                error = str(e)
                decision = PolicyDecisionStep(
                    timestamp=obs.timestamp, information_cutoff=obs.information_cutoff,
                    explanation=f"causality violation, step skipped: {e}",
                )

            violations: List[str] = []
            projected = False
            post_state = None
            if decision.target_weights is not None:
                projected_weights, violations, projected = apply_constraints(
                    decision.target_weights, self.config.constraints, state.weights, self.config.projection_mode,
                )
                if violations:
                    n_constraint_violations += 1
                if projected:
                    n_projections += 1
                    decision = decision.model_copy(update={
                        "target_weights": projected_weights,
                        "constraint_violations": (decision.constraint_violations or []) + violations,
                    })
                post_state = PortfolioLedger.advance(state, decision.target_weights or state.weights, obs.timestamp)
                state = post_state

            results.append(ExecutionResult(
                step_index=obs.step_index, decision=decision, pre_trade_state=pre_state,
                post_trade_state=post_state, constraint_violations=violations, projection_applied=projected,
                causality_ok=causality_ok, latency_sec=time.time() - t0, error=error,
            ))

        summary = self.adapter.q4_finalize()

        decisions = [r.decision for r in results]
        traj_violations = audit_trajectory(decisions)
        n_causality_violations += len(traj_violations)

        policy = Q4Policy(
            context=self.config.context,
            policy_type=summary.policy_type,
            generation_window=self.config.generation_window,
            universe_policy=summary.universe_policy,
            update_policy=summary.update_policy,
            constraints=self.config.constraints,
            initial_weights=decisions[0].target_weights if decisions else self.config.initial_weights,
            artifact=summary.artifact,
            decisions=decisions or None,
            explanation=summary.explanation,
        )

        return Q4RunResult(
            session_id=self.config.session_id,
            adapter_name=getattr(self.adapter, "name", type(self.adapter).__name__),
            classification=self.classification,
            policy=policy,
            results=results,
            n_steps=len(results),
            n_causality_violations=n_causality_violations,
            n_constraint_violations=n_constraint_violations,
            n_projections_applied=n_projections,
            total_latency_sec=time.time() - t_start,
        )
