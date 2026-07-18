"""
adapters/example_stub_adapter.py — Minimal reference implementation (v2.0.0 schema).

Copy this file, rename it, and fill in the real upstream calls.
Run: python CONTRACT/adapter_runner.py --adapter adapters/example_stub_adapter.py \
    --task-id smoke --as-of 2024-01-15 --scope ASSET --target AAPL --universe AAPL
"""

from typing import Optional

from CONTRACT.base_adapter import BaseAdapter
from CONTRACT.schemas import Action, OutputScope, Q1Action, Q2State, QueryContext, StateEstimate


class ExampleStubAdapter(BaseAdapter):
    # ------------------------------------------------------------------
    # Required class-level metadata
    # ------------------------------------------------------------------
    name               = "example_stub"
    questions_answered = ["Q1", "Q2"]
    upstream_repo      = "https://github.com/FILL_IN/upstream-project"
    requires_env       = ""   # leave empty if no separate conda env needed

    # ------------------------------------------------------------------
    # Q1 — Action
    # ------------------------------------------------------------------
    def q1_action(self, context: QueryContext, **kwargs) -> Optional[Q1Action]:
        # ── Replace the lines below with real upstream API calls ──────
        # from vendor.myproject import analyze
        # result = analyze(context.targets[0], context.as_of)
        # action = Action.BUY if result["signal"] > 0 else Action.SELL
        # confidence = ConfidenceEstimate(value=result["confidence"], kind=ConfidenceKind.SELF_REPORTED)
        # explanation = result["summary"]
        # ─────────────────────────────────────────────────────────────

        # This stub has no real upstream call, so it has nothing to report
        # beyond a placeholder action — do not fabricate confidence or an
        # explanation the (nonexistent) upstream never produced.
        return Q1Action(
            context=context,
            action=Action.HOLD,
        )

    # ------------------------------------------------------------------
    # Q2 — State
    # ------------------------------------------------------------------
    def q2_state(self, context: QueryContext, **kwargs) -> Optional[Q2State]:
        # ── Replace with a real upstream state/sentiment call ─────────
        # StateEstimate(dimension="sentiment", value_numeric=result["score"], ...)
        # ─────────────────────────────────────────────────────────────

        return Q2State(
            context=context,
            states=[
                StateEstimate(dimension="sentiment", value_text="Stub adapter — replace with real upstream call."),
            ],
        )

    # ------------------------------------------------------------------
    # Smoke test (fast, <= 1 real call)
    # ------------------------------------------------------------------
    def smoke_test(self):
        checks = super().smoke_test()  # metadata checks
        context = QueryContext(
            as_of="2024-01-15",
            data_cutoff="2024-01-15",
            scope=OutputScope.ASSET,
            targets=["AAPL"],
            universe=["AAPL"],
        )
        result = self.q1_action(context)
        checks["q1_returns_Q1Action"] = result is not None
        checks["action_is_valid"] = result.action in ("BUY", "SELL", "HOLD")
        return checks
