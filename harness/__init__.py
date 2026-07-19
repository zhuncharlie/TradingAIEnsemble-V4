"""
harness/ — the Q4 stepwise execution runtime.

Lives entirely outside CONTRACT/ (which is frozen — see CLAUDE.md §3). This
package never modifies CONTRACT/schemas.py; it only reuses the real,
frozen Q4Policy/PolicyDecisionStep/TimeWindow/PortfolioConstraints/
QueryContext classes and adds harness-side enforcement and orchestration
around them (causality checking, constraint projection, multi-step session
management) that the schema itself explicitly defers to "a layer that can
parse a guaranteed datetime format" (see PolicyDecisionStep's docstring).

Modules:
    q4_protocol.py    — pure data contract: Q4StepAdapter Protocol,
                         MarketObservation, PortfolioState, Q4RunConfig,
                         Q4AdapterSession, ExecutionResult, Q4FinalizeSummary.
                         No I/O, no subprocess, no adapter imports.
    portfolio_state.py — PortfolioLedger (weight -> PortfolioState transition)
                         and apply_constraints (real projection/enforcement
                         of PortfolioConstraints, including leverage_limit/
                         turnover_limit/cash_allowed, which CONTRACT/schemas.py
                         declares but never itself enforces).
    observations.py   — real market data acquisition + rebalance-schedule
                         resolution for adapters that want harness-driven data.
    execution_engine.py — Q4ExecutionEngine: the transport-agnostic sequential
                         driver (initialize -> N x step -> finalize), causality
                         enforcement, trajectory assembly into a real Q4Policy.
    q4_runtime.py      — conda-env subprocess orchestration: spawns one
                         persistent per-adapter session subprocess, speaks a
                         line-delimited-JSON protocol to it, and provides the
                         LEGACY_INTERNAL_LOOP replay fallback for adapters that
                         don't implement the stepwise protocol.
"""
