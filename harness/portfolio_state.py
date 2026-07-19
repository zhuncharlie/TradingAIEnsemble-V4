"""
harness/portfolio_state.py — real constraint enforcement + portfolio ledger.

CONTRACT/schemas.py::PortfolioConstraints declares long_only, cash_allowed,
max_abs_weight, gross_exposure_limit, net_exposure_min/max, leverage_limit,
turnover_limit, additional_constraints — but its own validator,
_check_weights_against_constraints (CONTRACT/schemas.py:502-536), only
*checks* (raises on violation) long_only / max_abs_weight /
gross_exposure_limit / net_exposure_min/max. leverage_limit, turnover_limit,
and cash_allowed are declared fields with no corresponding enforcement
anywhere in the schema. This module is the concrete, additive enforcement
of the full set — real projection (clip-then-log) or real rejection,
depending on Q4RunConfig.projection_mode, never a silent no-op.

Nothing here modifies CONTRACT/schemas.py; PortfolioConstraints/
PolicyDecisionStep/Q4Policy are reused as-is.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from CONTRACT.schemas import PortfolioConstraints
from harness.q4_protocol import PortfolioState, Q4ConstraintViolation

_TOLERANCE = 1e-6
CASH_KEY = "CASH"


def apply_constraints(
    weights: Dict[str, float],
    constraints: Optional[PortfolioConstraints],
    prior_weights: Dict[str, float],
    mode: str = "clip",
) -> Tuple[Dict[str, float], List[str], bool]:
    """
    Real projection/enforcement of PortfolioConstraints against one real
    decision's target_weights. Returns (possibly-projected weights,
    violation description strings, whether any projection was applied).

    mode="clip": violations are corrected via the documented rule below and
        recorded (never silent).
    mode="reject": any violation raises Q4ConstraintViolation instead of
        being corrected — used when the caller wants the raw adapter
        decision to fail loudly rather than be silently altered.

    Every rule below states its own projection method explicitly so a
    downstream report can distinguish "adapter's own weights were already
    compliant" (violations=[], projection_applied=False) from "harness
    altered the stated decision" (projection_applied=True) — required for
    honest reporting per this project's no-fabrication rules.
    """
    if constraints is None:
        return dict(weights), [], False

    w = dict(weights)
    violations: List[str] = []
    projected = False

    def _reject_or_note(msg: str) -> None:
        if mode == "reject":
            raise Q4ConstraintViolation(msg)
        violations.append(msg)

    # 1. long_only: real rule = no negative weights. Projection: clip to 0.0.
    if constraints.long_only:
        for asset, val in list(w.items()):
            if val < -_TOLERANCE:
                _reject_or_note(f"long_only violated: {asset}={val} < 0")
                if mode == "clip":
                    w[asset] = 0.0
                    projected = True

    # 2. max_abs_weight: clip magnitude, preserving sign.
    if constraints.max_abs_weight is not None:
        limit = constraints.max_abs_weight
        for asset, val in list(w.items()):
            if abs(val) > limit + _TOLERANCE:
                _reject_or_note(f"max_abs_weight violated: |{asset}|={abs(val)} > {limit}")
                if mode == "clip":
                    w[asset] = limit if val > 0 else -limit
                    projected = True

    # 3. gross_exposure_limit: uniformly scale all non-cash weights down.
    if constraints.gross_exposure_limit is not None:
        gross = sum(abs(v) for v in w.values())
        limit = constraints.gross_exposure_limit
        if gross > limit + _TOLERANCE:
            _reject_or_note(f"gross_exposure_limit violated: {gross} > {limit}")
            if mode == "clip" and gross > 0:
                scale = limit / gross
                w = {a: v * scale for a, v in w.items()}
                projected = True

    # 4. leverage_limit: a stricter-if-lower secondary cap on the same real
    #    gross-exposure quantity (PortfolioConstraints does not separately
    #    define margin/borrowing mechanics, so this is interpreted as an
    #    additional ceiling on total gross exposure — documented here since
    #    the schema itself leaves this field's exact semantics
    #    implementation-defined by not enforcing it at all).
    if constraints.leverage_limit is not None:
        gross = sum(abs(v) for v in w.values())
        limit = constraints.leverage_limit
        if gross > limit + _TOLERANCE:
            _reject_or_note(f"leverage_limit violated: {gross} > {limit}")
            if mode == "clip" and gross > 0:
                scale = limit / gross
                w = {a: v * scale for a, v in w.items()}
                projected = True

    # 5. net_exposure_min/max: absorb any shortfall/excess into CASH when
    #    cash_allowed is not explicitly False; otherwise scale non-cash
    #    weights uniformly (real, documented heuristic — PortfolioConstraints
    #    does not specify a projection method, only a check).
    net = sum(w.values())
    if constraints.net_exposure_max is not None and net > constraints.net_exposure_max + _TOLERANCE:
        _reject_or_note(f"net_exposure_max violated: {net} > {constraints.net_exposure_max}")
        if mode == "clip":
            excess = net - constraints.net_exposure_max
            if constraints.cash_allowed is not False:
                w[CASH_KEY] = w.get(CASH_KEY, 0.0) - excess
            else:
                non_cash_sum = sum(v for a, v in w.items() if a != CASH_KEY)
                if non_cash_sum > 0:
                    scale = (non_cash_sum - excess) / non_cash_sum
                    w = {a: (v * scale if a != CASH_KEY else v) for a, v in w.items()}
            projected = True
    if constraints.net_exposure_min is not None and net < constraints.net_exposure_min - _TOLERANCE:
        _reject_or_note(f"net_exposure_min violated: {net} < {constraints.net_exposure_min}")
        if mode == "clip":
            shortfall = constraints.net_exposure_min - net
            if constraints.cash_allowed is not False:
                w[CASH_KEY] = w.get(CASH_KEY, 0.0) + shortfall
            projected = True

    # 6. turnover_limit: partial-fill toward the target proportional to the
    #    available turnover budget (real, documented heuristic).
    if constraints.turnover_limit is not None:
        assets = set(w) | set(prior_weights)
        turnover = sum(abs(w.get(a, 0.0) - prior_weights.get(a, 0.0)) for a in assets) / 2.0
        limit = constraints.turnover_limit
        if turnover > limit + _TOLERANCE:
            _reject_or_note(f"turnover_limit violated: {turnover} > {limit}")
            if mode == "clip" and turnover > 0:
                frac = limit / turnover
                w = {a: prior_weights.get(a, 0.0) + frac * (w.get(a, 0.0) - prior_weights.get(a, 0.0)) for a in assets}
                projected = True

    # 7. cash_allowed=False: any residual CASH weight is redistributed
    #    proportionally to non-cash holdings (real, documented heuristic).
    if constraints.cash_allowed is False and abs(w.get(CASH_KEY, 0.0)) > _TOLERANCE:
        cash = w.pop(CASH_KEY, 0.0)
        _reject_or_note(f"cash_allowed=False violated: residual CASH={cash}")
        if mode == "clip":
            non_cash_sum = sum(w.values())
            if non_cash_sum > 0:
                scale = (non_cash_sum + cash) / non_cash_sum
                w = {a: v * scale for a, v in w.items()}
            projected = True

    return w, violations, projected


class PortfolioLedger:
    """Real weight -> PortfolioState transition. The harness — not any
    individual adapter — is the single source of truth for portfolio state
    across a stepwise session, so cross-adapter comparisons are auditable
    against one consistent accounting method."""

    @staticmethod
    def advance(prior: PortfolioState, target_weights: Dict[str, float], timestamp: str) -> PortfolioState:
        return PortfolioState(
            as_of=timestamp,
            weights=dict(target_weights),
            nav=prior.nav,
            step_index=prior.step_index + 1,
            last_rebalance_timestamp=timestamp,
        )

    @staticmethod
    def turnover(prior: PortfolioState, target_weights: Dict[str, float]) -> float:
        assets = set(prior.weights) | set(target_weights)
        return sum(abs(target_weights.get(a, 0.0) - prior.weights.get(a, 0.0)) for a in assets) / 2.0
