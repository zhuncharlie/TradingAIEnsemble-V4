"""
CONTRACT/base_adapter.py — Abstract base class every adapter must inherit.

DO NOT MODIFY THIS FILE.

v2.0.0: migrated to the four-layer Q1 Action / Q2 State / Q3 Signal / Q4
Policy contract (CONTRACT/schemas.py). Q5 is removed. Method signatures now
take a single `context: QueryContext` (the harness-supplied time/target
description) instead of loose ticker/date/tickers/start/end parameters,
matching the v2 schema's unification of that information. Q4 additionally
takes `generation_window` since that interval is harness-supplied, not
chosen by the adapter (see Q4Policy.generation_window docstring).

Implementation rules:
  1. Subclass BaseAdapter in your adapters/{name}_adapter.py file.
  2. Set `name` and `questions_answered` (subset of ["Q1","Q2","Q3","Q4"])
     as class attributes.
  3. Implement only the q* methods your upstream project actually supports.
     Methods you don't implement return None by default — that is correct.
  4. Never import from another adapter file.
  5. Run `python CONTRACT/adapter_runner.py --adapter adapters/your_file.py ...`
     to validate before committing.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar, Dict, List, Optional

from CONTRACT.schemas import (
    AdapterResult,
    FieldMapping,
    Q1Action,
    Q2State,
    Q3Signal,
    Q4Policy,
    QueryContext,
    RunMetadata,
    TimeWindow,
)

VALID_QUESTIONS = {"Q1", "Q2", "Q3", "Q4"}


class AdapterContractViolation(RuntimeError):
    """
    Raised by BaseAdapter.run() when an adapter's returned output violates a
    harness-enforced invariant rather than a structural schema error — i.e.
    the shape was valid Q1Action/.../Q4Policy, but the adapter silently
    altered information the harness supplied to it. Currently checked:

      - each returned q*.context must equal the QueryContext the harness
        passed in (as_of, data_cutoff, scope, targets, universe, horizon)
      - a returned Q4Policy.generation_window must equal the
        generation_window the harness passed in

    An adapter must not narrow or widen its own information cutoff, target
    set, or training window relative to what it was asked to use — that's
    exactly the kind of silent divergence that breaks cross-adapter fairness
    and, for generation_window, causal validity.
    """


def _require_context_unchanged(label: str, returned: QueryContext, supplied: QueryContext) -> None:
    if returned != supplied:
        raise AdapterContractViolation(
            f"{label}.context does not match the harness-supplied QueryContext. "
            "Adapters may read as_of/data_cutoff/scope/targets/universe/horizon "
            "but must not change them before echoing context back. "
            f"supplied={supplied!r} returned={returned!r}"
        )


class BaseAdapter(ABC):
    """
    Wraps one upstream trading-AI project and exposes its outputs
    through the four canonical Q-schema methods.

    Minimum viable implementation: override at least ONE q* method.
    All others default to None (meaning "this project doesn't answer this question").
    """

    # --- class-level metadata (override in your subclass) ---
    name: ClassVar[str] = ""
    """Unique snake_case identifier, e.g. 'ai_hedge_fund'. Used as the JSON filename."""

    questions_answered: ClassVar[List[str]] = []
    """Which questions this adapter answers: subset of ["Q1","Q2","Q3","Q4"]."""

    upstream_repo: ClassVar[str] = ""
    """GitHub URL of the project being wrapped. For documentation only."""

    requires_env: ClassVar[str] = ""
    """conda env name if a separate env is required, else empty string."""

    adapter_version: ClassVar[str] = "0.1.0"
    """Adapter implementation version, recorded in RunMetadata.adapter_version."""

    # ------------------------------------------------------------------ #
    # Q-schema methods — override the ones your project supports          #
    # ------------------------------------------------------------------ #

    def q1_action(
        self,
        context: QueryContext,
        **kwargs,
    ) -> Optional[Q1Action]:
        """What action should be taken right now."""
        return None

    def q2_state(
        self,
        context: QueryContext,
        **kwargs,
    ) -> Optional[Q2State]:
        """What state the current object or market is in."""
        return None

    def q3_signal(
        self,
        context: QueryContext,
        **kwargs,
    ) -> Optional[Q3Signal]:
        """What testable predictive signal or alpha currently exists."""
        return None

    def q4_policy(
        self,
        context: QueryContext,
        generation_window: TimeWindow,
        **kwargs,
    ) -> Optional[Q4Policy]:
        """How the policy is formed and updated over continuous time."""
        return None

    # ------------------------------------------------------------------ #
    # Convenience: build a complete AdapterResult envelope               #
    # ------------------------------------------------------------------ #

    def run(
        self,
        task_id: str,
        context: QueryContext,
        generation_window: Optional[TimeWindow] = None,
        native_output: Optional[dict] = None,
        adapter_notes: Optional[str] = None,
        field_mappings: Optional[List[FieldMapping]] = None,
        **kwargs,
    ) -> AdapterResult:
        """
        Call all implemented q* methods and bundle results into AdapterResult.
        Adapters can override this if they need a different call sequence.
        Q4 is only attempted if `generation_window` is supplied, since
        Q4Policy.generation_window is required and harness-supplied.

        Enforces that every returned q*.context matches the `context` this
        method was called with, and that a returned Q4Policy.generation_window
        matches the `generation_window` this method was called with — an
        adapter may read that information but must not alter it. Raises
        AdapterContractViolation if either check fails.
        """
        q1 = self.q1_action(context, **kwargs) if "Q1" in self.questions_answered else None
        q2 = self.q2_state(context, **kwargs) if "Q2" in self.questions_answered else None
        q3 = self.q3_signal(context, **kwargs) if "Q3" in self.questions_answered else None
        q4 = (
            self.q4_policy(context, generation_window, **kwargs)
            if "Q4" in self.questions_answered and generation_window is not None
            else None
        )

        for label, q in (("q1", q1), ("q2", q2), ("q3", q3), ("q4", q4)):
            if q is not None:
                _require_context_unchanged(label, q.context, context)

        if q4 is not None and generation_window is not None and q4.generation_window != generation_window:
            raise AdapterContractViolation(
                "q4.generation_window does not match the harness-supplied generation_window. "
                "Adapters may record this interval but must not choose, expand, or shorten it. "
                f"supplied={generation_window!r} returned={q4.generation_window!r}"
            )

        return AdapterResult(
            task_id=task_id,
            run=RunMetadata(adapter=self.name, adapter_version=self.adapter_version),
            q1=q1, q2=q2, q3=q3, q4=q4,
            native_output=native_output or {},
            field_mappings=field_mappings,
            adapter_notes=adapter_notes,
        )

    # ------------------------------------------------------------------ #
    # Smoke test — override for adapter-specific quick checks            #
    # ------------------------------------------------------------------ #

    def smoke_test(self) -> Dict[str, bool]:
        """
        Run a minimal self-check. Returns {check_name: passed}.
        Must complete in under 5 minutes and make at most 1 real API call.
        Default implementation just checks the class metadata is set.
        """
        return {
            "name_set":               bool(self.name),
            "questions_answered_set": bool(self.questions_answered),
            "questions_answered_valid": all(q in VALID_QUESTIONS for q in self.questions_answered),
            "upstream_repo_set":      bool(self.upstream_repo),
        }
