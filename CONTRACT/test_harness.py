"""
CONTRACT/test_harness.py — Validates the v2.0.0 adapter contract itself.

This is a pure schema-contract test suite for CONTRACT/schemas.py. It does
NOT load, run, or validate real adapters — the v1 -> v2.0.0 schema rewrite is
a breaking change and existing adapters (all built against the removed v1
five-question contract) are expected to be temporarily incompatible until a
separate adapter-migration task updates them. See
milestones/2026-07-16_schema-v1-milestone.md for the v1 rollback point, and
CONTRACT/base_adapter.py for the (currently import-broken) adapter base class.

No network calls, no adapter imports, no external dependencies beyond
pydantic — stdlib unittest only, matching this repo's existing test
convention (see analysis/test_icaif_experiments.py).

Usage:
    python CONTRACT/test_harness.py
    python -m unittest CONTRACT.test_harness -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from CONTRACT.schemas import (
    SCHEMA_VERSION,
    Action,
    AdapterResult,
    ConfidenceEstimate,
    ConfidenceKind,
    ContractModel,
    DecisionPolicy,
    Direction,
    EvidenceItem,
    FieldMapping,
    FieldSourceType,
    ObservationPolicy,
    OutputScope,
    PolicyArtifact,
    PolicyDecisionStep,
    PolicyType,
    PortfolioConstraints,
    Q1Action,
    Q2State,
    Q3Signal,
    Q4Policy,
    QueryContext,
    RunMetadata,
    StateEstimate,
    TimeWindow,
    UniversePolicy,
    UpdateMode,
    UpdatePolicy,
)

from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_context(
    *,
    scope=OutputScope.ASSET,
    targets=None,
    universe=None,
    universe_id=None,
    horizon="1d",
):
    return QueryContext(
        as_of="2026-01-31T16:00:00Z",
        data_cutoff="2026-01-31T16:00:00Z",
        scope=scope,
        targets=targets,
        universe=universe,
        universe_id=universe_id,
        horizon=horizon,
    )


def make_run_metadata():
    return RunMetadata(
        adapter="test_adapter",
        adapter_version="0.1.0",
        run_id="test-run-001",
    )


def make_minimal_q1():
    return Q1Action(
        context=make_context(targets=["NVDA"], universe=["NVDA"]),
        action=Action.BUY,
    )


def make_minimal_q2():
    return Q2State(
        context=make_context(scope=OutputScope.MARKET, targets=["US_EQUITY_MARKET"]),
        states=[StateEstimate(dimension="market_regime", value_category="RISK_OFF")],
    )


def make_minimal_q3():
    return Q3Signal(
        context=make_context(targets=["NVDA"], universe=["NVDA"]),
        signal_semantics="predicted_return",
        values={"NVDA": 0.03},
    )


def make_minimal_q4():
    return Q4Policy(
        context=make_context(scope=OutputScope.PORTFOLIO, universe_id="GLOBAL_LIQUID_ASSETS_V1", targets=None, universe=None),
        policy_type=PolicyType.STATIC_ALLOCATION,
        generation_window=TimeWindow(start="2020-01-01", end="2023-12-31"),
        initial_weights={"SPY": 0.6, "GLD": 0.2, "CASH": 0.2},
    )


# ---------------------------------------------------------------------------
# ContractModel common behavior
# ---------------------------------------------------------------------------

class TestContractModelBehavior(unittest.TestCase):
    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            Q1Action(context=make_context(), action=Action.BUY, not_a_real_field=123)

    def test_float_rejects_nan(self):
        with self.assertRaises(ValidationError):
            ConfidenceEstimate(value=float("nan"), kind=ConfidenceKind.HEURISTIC)

    def test_float_rejects_infinity(self):
        with self.assertRaises(ValidationError):
            Q3Signal(
                context=make_context(targets=["NVDA"], universe=["NVDA"]),
                signal_semantics="predicted_return",
                values={"NVDA": float("inf")},
            )

    def test_enum_serializes_as_string_value(self):
        q1 = make_minimal_q1()
        payload = q1.model_dump(mode="json")
        self.assertEqual(payload["action"], "BUY")

    def test_json_schema_generation(self):
        for model in (Q1Action, Q2State, Q3Signal, Q4Policy, AdapterResult):
            schema = model.model_json_schema()
            self.assertIsInstance(schema, dict)


class TestSchemaVersionAndDeletions(unittest.TestCase):
    def test_schema_version(self):
        self.assertEqual(SCHEMA_VERSION, "2.0.0")

    def test_q5_removed_from_envelope(self):
        self.assertNotIn("q5", AdapterResult.model_fields)

    def test_update_policy_uses_update_mode_not_old_flags(self):
        self.assertIn("mode", UpdatePolicy.model_fields)
        for old_field in ("stateful", "online_update", "retraining_allowed"):
            self.assertNotIn(old_field, UpdatePolicy.model_fields)

    def test_q4_has_no_evaluation_windows(self):
        for banned in ("validation_window", "test_window", "evaluation_window"):
            self.assertNotIn(banned, Q4Policy.model_fields)


# ---------------------------------------------------------------------------
# QueryContext
# ---------------------------------------------------------------------------

class TestQueryContext(unittest.TestCase):
    def test_single_asset(self):
        ctx = QueryContext(
            as_of="2026-01-31",
            data_cutoff="2026-01-31",
            scope=OutputScope.ASSET,
            targets=["NVDA"],
            universe=["NVDA"],
            horizon="1d",
        )
        self.assertEqual(ctx.targets, ["NVDA"])

    def test_whole_market(self):
        ctx = QueryContext(
            as_of="2026-01-31",
            data_cutoff="2026-01-31",
            scope=OutputScope.MARKET,
            targets=["US_EQUITY_MARKET"],
            universe_id="SP500",
        )
        self.assertEqual(ctx.universe_id, "SP500")

    def test_multi_market_no_targets_or_universe_required(self):
        ctx = QueryContext(
            as_of="2026-01-31",
            data_cutoff="2026-01-31",
            scope=OutputScope.MULTI_MARKET,
            universe_id="GLOBAL_CATALOG_V1",
        )
        self.assertIsNone(ctx.targets)
        self.assertIsNone(ctx.universe)

    def test_empty_as_of_rejected(self):
        with self.assertRaises(ValidationError):
            QueryContext(as_of="", data_cutoff="2026-01-31", scope=OutputScope.ASSET)


# ---------------------------------------------------------------------------
# ConfidenceEstimate
# ---------------------------------------------------------------------------

class TestConfidenceEstimate(unittest.TestCase):
    def test_value_zero_legal(self):
        ConfidenceEstimate(value=0.0, kind=ConfidenceKind.PROBABILITY)

    def test_value_one_legal(self):
        ConfidenceEstimate(value=1.0, kind=ConfidenceKind.PROBABILITY)

    def test_value_below_zero_rejected(self):
        with self.assertRaises(ValidationError):
            ConfidenceEstimate(value=-0.1, kind=ConfidenceKind.PROBABILITY)

    def test_value_above_one_rejected(self):
        with self.assertRaises(ValidationError):
            ConfidenceEstimate(value=1.1, kind=ConfidenceKind.PROBABILITY)

    def test_all_confidence_kinds_usable(self):
        for kind in ConfidenceKind:
            ConfidenceEstimate(value=0.5, kind=kind)

    def test_raw_value_may_exceed_unit_interval(self):
        est = ConfidenceEstimate(value=0.9, kind=ConfidenceKind.MODEL_MARGIN, raw_value=37.4)
        self.assertEqual(est.raw_value, 37.4)

    def test_q1_q2_q3_legal_without_confidence(self):
        make_minimal_q1()
        make_minimal_q2()
        make_minimal_q3()


# ---------------------------------------------------------------------------
# EvidenceItem
# ---------------------------------------------------------------------------

class TestEvidenceItem(unittest.TestCase):
    def test_kind_only(self):
        EvidenceItem(kind="factor")

    def test_value_only(self):
        EvidenceItem(value="momentum_12m")

    def test_source_or_reference_only(self):
        EvidenceItem(source="finviz")
        EvidenceItem(reference="https://example.com/filing")

    def test_all_empty_rejected(self):
        with self.assertRaises(ValidationError):
            EvidenceItem()


# ---------------------------------------------------------------------------
# FieldMapping
# ---------------------------------------------------------------------------

class TestFieldMapping(unittest.TestCase):
    def test_native(self):
        FieldMapping(
            canonical_field="q1.action",
            source_type=FieldSourceType.NATIVE,
            native_path="decision.action",
        )

    def test_derived(self):
        FieldMapping(
            canonical_field="q1.confidence.value",
            source_type=FieldSourceType.DERIVED,
            native_path="prediction.logits",
            transform="softmax_margin",
        )

    def test_harness_supplied(self):
        FieldMapping(
            canonical_field="q4.generation_window",
            source_type=FieldSourceType.HARNESS_SUPPLIED,
        )

    def test_missing(self):
        FieldMapping(
            canonical_field="q1.explanation",
            source_type=FieldSourceType.MISSING,
            loss_notes=["Upstream project does not generate explanations"],
        )


# ---------------------------------------------------------------------------
# Q1Action
# ---------------------------------------------------------------------------

class TestQ1Action(unittest.TestCase):
    def test_minimal_legal(self):
        q1 = make_minimal_q1()
        self.assertEqual(q1.action, "BUY")

    def test_secondary_fields_optional(self):
        q1 = make_minimal_q1()
        for field in (
            "action_semantics", "action_strength", "target_position",
            "confidence", "explanation", "bull_case", "bear_case", "evidence",
        ):
            self.assertIsNone(getattr(q1, field))

    def test_action_strength_below_zero_rejected(self):
        with self.assertRaises(ValidationError):
            Q1Action(context=make_context(), action=Action.BUY, action_strength=-0.1)

    def test_action_strength_above_one_rejected(self):
        with self.assertRaises(ValidationError):
            Q1Action(context=make_context(), action=Action.BUY, action_strength=1.1)

    def test_target_position_may_be_negative(self):
        q1 = Q1Action(context=make_context(), action=Action.SELL, target_position=-500.0)
        self.assertEqual(q1.target_position, -500.0)

    def test_no_reasoning_field_required(self):
        self.assertNotIn("reasoning", Q1Action.model_fields)

    def test_no_run_metadata_fields_on_q1(self):
        for banned in ("adapter", "ticker", "date", "cost_usd", "latency_sec"):
            self.assertNotIn(banned, Q1Action.model_fields)


# ---------------------------------------------------------------------------
# Q2State
# ---------------------------------------------------------------------------

class TestStateEstimate(unittest.TestCase):
    def test_numeric_state(self):
        StateEstimate(dimension="sentiment", value_numeric=-0.4, scale="[-1,1]", observation_window="7d")

    def test_category_state(self):
        StateEstimate(dimension="market_regime", value_category="RISK_OFF")

    def test_text_state(self):
        StateEstimate(dimension="event_context", value_text="Earnings uncertainty is elevated.")

    def test_distribution_state(self):
        StateEstimate(
            dimension="market_regime",
            value_distribution={"RISK_ON": 0.2, "RISK_OFF": 0.7, "TRANSITION": 0.1},
            scale="probability_distribution",
        )

    def test_all_values_empty_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(dimension="sentiment")

    def test_empty_dimension_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(dimension="", value_numeric=0.1)

    def test_distribution_empty_key_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(dimension="market_regime", value_distribution={"": 0.5})

    def test_distribution_negative_value_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(dimension="market_regime", value_distribution={"RISK_ON": -0.1})

    def test_distribution_nan_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(dimension="market_regime", value_distribution={"RISK_ON": float("nan")})

    def test_distribution_need_not_sum_to_one(self):
        est = StateEstimate(dimension="market_regime", value_distribution={"RISK_ON": 0.3, "RISK_OFF": 0.3})
        self.assertAlmostEqual(sum(est.value_distribution.values()), 0.6)


class TestQ2State(unittest.TestCase):
    def test_minimal_legal(self):
        q2 = make_minimal_q2()
        self.assertEqual(len(q2.states), 1)

    def test_empty_states_rejected(self):
        with self.assertRaises(ValidationError):
            Q2State(context=make_context(scope=OutputScope.MARKET), states=[])

    def test_open_vocabulary_regime_dimension(self):
        Q2State(
            context=make_context(scope=OutputScope.MARKET),
            states=[StateEstimate(dimension="anything_the_adapter_wants", value_category="X")],
        )

    def test_no_regime_enum_exists(self):
        import CONTRACT.schemas as schemas
        self.assertFalse(hasattr(schemas, "Regime"))

    def test_explanation_optional(self):
        q2 = make_minimal_q2()
        self.assertIsNone(q2.explanation)


# ---------------------------------------------------------------------------
# Q3Signal
# ---------------------------------------------------------------------------

class TestQ3Signal(unittest.TestCase):
    def test_single_asset_minimal(self):
        q3 = make_minimal_q3()
        self.assertEqual(q3.values, {"NVDA": 0.03})

    def test_cross_section(self):
        q3 = Q3Signal(
            context=make_context(scope=OutputScope.CROSS_SECTION, universe=["AAPL", "MSFT", "NVDA"], horizon="5d"),
            signal_semantics="ranking_score",
            values={"AAPL": 0.2, "MSFT": 0.7, "NVDA": 0.9},
            score_scale="cross_sectional_rank",
        )
        self.assertEqual(len(q3.values), 3)

    def test_empty_values_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(context=make_context(), signal_semantics="predicted_return", values={})

    def test_empty_key_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(context=make_context(), signal_semantics="predicted_return", values={"": 0.1})

    def test_nan_value_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(context=make_context(), signal_semantics="predicted_return", values={"NVDA": float("nan")})

    def test_infinity_value_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(context=make_context(), signal_semantics="predicted_return", values={"NVDA": float("inf")})

    def test_expected_returns_invalid_key_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(
                context=make_context(),
                signal_semantics="predicted_return",
                values={"NVDA": 0.1},
                expected_returns={"": 0.05},
            )

    def test_strength_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            Q3Signal(context=make_context(), signal_semantics="predicted_return", values={"NVDA": 0.1}, strength=1.5)

    def test_direction_confidence_evidence_optional(self):
        q3 = make_minimal_q3()
        self.assertIsNone(q3.direction)
        self.assertIsNone(q3.confidence)
        self.assertIsNone(q3.evidence)
        self.assertIsNone(q3.factor_expression)

    def test_no_signal_type_enum_exists(self):
        import CONTRACT.schemas as schemas
        self.assertFalse(hasattr(schemas, "SignalType"))


# ---------------------------------------------------------------------------
# TimeWindow / generation window
# ---------------------------------------------------------------------------

class TestTimeWindow(unittest.TestCase):
    def test_legal_window(self):
        TimeWindow(start="2020-01-01", end="2023-12-31")

    def test_empty_start_rejected(self):
        with self.assertRaises(ValidationError):
            TimeWindow(start="", end="2023-12-31")

    def test_empty_end_rejected(self):
        with self.assertRaises(ValidationError):
            TimeWindow(start="2020-01-01", end="")


# ---------------------------------------------------------------------------
# UpdateMode / UpdatePolicy
# ---------------------------------------------------------------------------

class TestUpdatePolicy(unittest.TestCase):
    def test_all_modes_constructible(self):
        for mode in (UpdateMode.NONE, UpdateMode.STATE_UPDATE, UpdateMode.ROLLING_REFIT, UpdateMode.ONLINE_LEARNING):
            UpdatePolicy(mode=mode)

    def test_old_boolean_fields_absent(self):
        self.assertNotIn("stateful", UpdatePolicy.model_fields)
        self.assertNotIn("online_update", UpdatePolicy.model_fields)
        self.assertNotIn("retraining_allowed", UpdatePolicy.model_fields)


# ---------------------------------------------------------------------------
# Q4Policy — four policy shapes
# ---------------------------------------------------------------------------

class TestQ4PolicyShapes(unittest.TestCase):
    def _portfolio_context(self):
        return make_context(scope=OutputScope.PORTFOLIO, universe_id="GLOBAL_LIQUID_ASSETS_V1", targets=None, universe=None)

    def _window(self):
        return TimeWindow(start="2020-01-01", end="2023-12-31")

    def test_static_allocation(self):
        Q4Policy(
            context=self._portfolio_context(),
            policy_type=PolicyType.STATIC_ALLOCATION,
            generation_window=self._window(),
            initial_weights={"SPY": 0.6, "GLD": 0.2, "CASH": 0.2},
        )

    def test_rolling_optimizer_without_pregenerated_decisions(self):
        # Must be constructible on decision_rule alone, with no `decisions` yet.
        Q4Policy(
            context=self._portfolio_context(),
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=self._window(),
            observation_policy=ObservationPolicy(lookback_window="252d", features=["returns"]),
            decision_policy=DecisionPolicy(
                decision_rule="hierarchical_risk_parity",
                output_semantics="target_weights",
                rebalance_frequency="MONTHLY",
            ),
            update_policy=UpdatePolicy(mode=UpdateMode.ROLLING_REFIT, update_frequency="MONTHLY"),
        )

    def test_frozen_learned_policy(self):
        Q4Policy(
            context=self._portfolio_context(),
            policy_type=PolicyType.FROZEN_LEARNED_POLICY,
            generation_window=self._window(),
            artifact=PolicyArtifact(artifact_type="model_checkpoint", reference="artifacts/policy.pt"),
            update_policy=UpdatePolicy(mode=UpdateMode.STATE_UPDATE),
        )

    def test_online_adaptive_policy(self):
        Q4Policy(
            context=self._portfolio_context(),
            policy_type=PolicyType.ONLINE_ADAPTIVE_POLICY,
            generation_window=self._window(),
            artifact=PolicyArtifact(artifact_type="serialized_policy", reference="artifacts/online_policy.pkl"),
            update_policy=UpdatePolicy(mode=UpdateMode.ONLINE_LEARNING, update_frequency="DAILY"),
        )


class TestQ4PolicyMinimumViability(unittest.TestCase):
    def _base_kwargs(self):
        return dict(
            context=make_context(scope=OutputScope.PORTFOLIO, universe_id="X", targets=None, universe=None),
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=TimeWindow(start="2020-01-01", end="2023-12-31"),
        )

    def test_no_representation_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            Q4Policy(**self._base_kwargs())
        self.assertIn("executable policy representation", str(ctx.exception))

    def test_decision_rule_alone_is_sufficient(self):
        Q4Policy(**self._base_kwargs(), decision_policy=DecisionPolicy(decision_rule="momentum_rank"))

    def test_artifact_alone_is_sufficient(self):
        Q4Policy(**self._base_kwargs(), artifact=PolicyArtifact(artifact_type="model_checkpoint", reference="x.pt"))

    def test_initial_weights_alone_is_sufficient(self):
        Q4Policy(**self._base_kwargs(), initial_weights={"SPY": 1.0})


# ---------------------------------------------------------------------------
# PolicyDecisionStep
# ---------------------------------------------------------------------------

class TestPolicyDecisionStep(unittest.TestCase):
    def test_minimal_legal(self):
        PolicyDecisionStep(
            timestamp="2024-01-31T16:00:00Z",
            information_cutoff="2024-01-31T16:00:00Z",
            selected_universe=["SPY", "GLD"],
            target_weights={"SPY": 0.7, "GLD": 0.2, "CASH": 0.1},
        )

    def test_target_weights_optional_orders_may_replace(self):
        PolicyDecisionStep(
            timestamp="2024-01-31T16:00:00Z",
            information_cutoff="2024-01-31T16:00:00Z",
            orders=[{"ticker": "SPY", "side": "BUY", "qty": 10}],
        )

    def test_negative_turnover_rejected(self):
        with self.assertRaises(ValidationError):
            PolicyDecisionStep(timestamp="t", information_cutoff="t", turnover=-0.1)

    def test_empty_weight_key_rejected(self):
        with self.assertRaises(ValidationError):
            PolicyDecisionStep(timestamp="t", information_cutoff="t", target_weights={"": 0.5})

    def test_nan_weight_rejected(self):
        with self.assertRaises(ValidationError):
            PolicyDecisionStep(timestamp="t", information_cutoff="t", target_weights={"SPY": float("nan")})

    def test_cash_is_an_ordinary_weight_key(self):
        step = PolicyDecisionStep(timestamp="t", information_cutoff="t", target_weights={"CASH": 1.0})
        self.assertEqual(step.target_weights["CASH"], 1.0)
        self.assertNotIn("cash_ratio", PolicyDecisionStep.model_fields)


# ---------------------------------------------------------------------------
# Q4 weight constraints (long-only / short / gross / net / max-weight)
# ---------------------------------------------------------------------------

class TestQ4WeightConstraints(unittest.TestCase):
    def _q4(self, weights, constraints=None, via_decision_step=False):
        ctx = make_context(scope=OutputScope.PORTFOLIO, universe_id="X", targets=None, universe=None)
        window = TimeWindow(start="2020-01-01", end="2023-12-31")
        if via_decision_step:
            return Q4Policy(
                context=ctx,
                policy_type=PolicyType.ROLLING_OPTIMIZER,
                generation_window=window,
                constraints=constraints,
                decisions=[
                    PolicyDecisionStep(timestamp="t", information_cutoff="t", target_weights=weights)
                ],
            )
        return Q4Policy(
            context=ctx,
            policy_type=PolicyType.STATIC_ALLOCATION,
            generation_window=window,
            constraints=constraints,
            initial_weights=weights,
        )

    def test_long_only_rejects_negative_weight(self):
        with self.assertRaises(ValidationError):
            self._q4({"SPY": -0.1, "CASH": 1.1}, PortfolioConstraints(long_only=True))

    def test_long_only_rejects_negative_weight_in_decision_step(self):
        with self.assertRaises(ValidationError):
            self._q4({"SPY": -0.1, "CASH": 1.1}, PortfolioConstraints(long_only=True), via_decision_step=True)

    def test_short_allowed_when_long_only_false(self):
        self._q4({"SPY": -0.1, "CASH": 1.1}, PortfolioConstraints(long_only=False))

    def test_max_abs_weight_enforced(self):
        with self.assertRaises(ValidationError):
            self._q4({"SPY": 0.5}, PortfolioConstraints(max_abs_weight=0.4))
        self._q4({"SPY": 0.35}, PortfolioConstraints(max_abs_weight=0.4))

    def test_gross_exposure_enforced(self):
        with self.assertRaises(ValidationError):
            self._q4({"SPY": 1.0, "SHORT_QQQ": -1.0}, PortfolioConstraints(gross_exposure_limit=1.5))
        self._q4({"SPY": 0.7, "SHORT_QQQ": -0.5}, PortfolioConstraints(gross_exposure_limit=1.5))

    def test_net_exposure_bounds_enforced(self):
        constraints = PortfolioConstraints(net_exposure_min=0.5, net_exposure_max=1.0)
        with self.assertRaises(ValidationError):
            self._q4({"SPY": 0.2}, constraints)
        self._q4({"SPY": 0.7}, constraints)

    def test_no_constraints_means_no_defaults(self):
        # No long-only, no sum<=1, no leverage/short prohibition unless stated.
        self._q4({"SPY": -2.0, "QQQ": 3.5}, constraints=None)


# ---------------------------------------------------------------------------
# UniversePolicy / PolicyArtifact sanity
# ---------------------------------------------------------------------------

class TestUniversePolicyAndArtifact(unittest.TestCase):
    def test_universe_policy_mode_required(self):
        with self.assertRaises(ValidationError):
            UniversePolicy(mode="")
        UniversePolicy(mode="adapter_selected", max_assets=25)

    def test_policy_artifact_type_required(self):
        with self.assertRaises(ValidationError):
            PolicyArtifact(artifact_type="")
        PolicyArtifact(artifact_type="strategy_code", reference="strategies/momentum.py")


# ---------------------------------------------------------------------------
# AdapterResult
# ---------------------------------------------------------------------------

class TestAdapterResult(unittest.TestCase):
    def test_only_q1(self):
        AdapterResult(task_id="task-q1-001", run=make_run_metadata(), q1=make_minimal_q1(), native_output={"action": "BUY"})

    def test_only_q2(self):
        AdapterResult(task_id="task-q2-001", run=make_run_metadata(), q2=make_minimal_q2())

    def test_only_q3(self):
        AdapterResult(task_id="task-q3-001", run=make_run_metadata(), q3=make_minimal_q3())

    def test_only_q4(self):
        AdapterResult(task_id="task-q4-001", run=make_run_metadata(), q4=make_minimal_q4())

    def test_all_q_none_rejected(self):
        with self.assertRaises(ValidationError):
            AdapterResult(task_id="empty-result", run=make_run_metadata())

    def test_q5_field_absent(self):
        self.assertNotIn("q5", AdapterResult.model_fields)

    def test_adapter_identity_only_in_run(self):
        self.assertNotIn("adapter", Q1Action.model_fields)
        self.assertNotIn("adapter", Q2State.model_fields)
        self.assertNotIn("adapter", Q3Signal.model_fields)
        self.assertNotIn("adapter", Q4Policy.model_fields)
        self.assertIn("adapter", RunMetadata.model_fields)

    def test_cost_and_latency_only_in_run(self):
        for model in (Q1Action, Q2State, Q3Signal, Q4Policy):
            self.assertNotIn("cost_usd", model.model_fields)
            self.assertNotIn("latency_sec", model.model_fields)
        self.assertIn("cost_usd", RunMetadata.model_fields)
        self.assertIn("latency_sec", RunMetadata.model_fields)

    def test_field_mappings_and_notes_optional(self):
        result = AdapterResult(task_id="t", run=make_run_metadata(), q1=make_minimal_q1())
        self.assertIsNone(result.field_mappings)
        self.assertIsNone(result.adapter_notes)

    def test_native_output_defaults_empty_dict(self):
        result = AdapterResult(task_id="t", run=make_run_metadata(), q1=make_minimal_q1())
        self.assertEqual(result.native_output, {})

    def test_schema_version_defaults_correctly(self):
        result = AdapterResult(task_id="t", run=make_run_metadata(), q1=make_minimal_q1())
        self.assertEqual(result.run.schema_version, SCHEMA_VERSION)


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------

class TestRoundTripSerialization(unittest.TestCase):
    def test_full_envelope_round_trips(self):
        q2 = Q2State(
            context=make_context(scope=OutputScope.MARKET, targets=["US_EQUITY_MARKET"]),
            states=[
                StateEstimate(
                    dimension="market_regime",
                    value_distribution={"RISK_ON": 0.2, "RISK_OFF": 0.7, "TRANSITION": 0.1},
                    scale="probability_distribution",
                )
            ],
        )
        q3 = Q3Signal(
            context=make_context(scope=OutputScope.CROSS_SECTION, universe=["AAPL", "MSFT", "NVDA"], horizon="5d"),
            signal_semantics="ranking_score",
            values={"AAPL": 0.2, "MSFT": 0.7, "NVDA": 0.9},
            direction=Direction.LONG,
            confidence=ConfidenceEstimate(value=0.6, kind=ConfidenceKind.SCORE_NORMALIZED),
        )
        q4 = Q4Policy(
            context=make_context(scope=OutputScope.PORTFOLIO, universe_id="X", targets=None, universe=None),
            policy_type=PolicyType.ROLLING_OPTIMIZER,
            generation_window=TimeWindow(start="2020-01-01", end="2023-12-31"),
            observation_policy=ObservationPolicy(lookback_window="252d", features=["returns", "volatility"]),
            decision_policy=DecisionPolicy(decision_rule="hierarchical_risk_parity", rebalance_frequency="MONTHLY"),
            update_policy=UpdatePolicy(mode=UpdateMode.ROLLING_REFIT),
            decisions=[
                PolicyDecisionStep(
                    timestamp="2024-01-31T16:00:00Z",
                    information_cutoff="2024-01-31T16:00:00Z",
                    target_weights={"SPY": 0.7, "GLD": 0.2, "CASH": 0.1},
                )
            ],
        )
        result = AdapterResult(
            task_id="round-trip-001",
            run=make_run_metadata(),
            q2=q2,
            q3=q3,
            q4=q4,
            field_mappings=[
                FieldMapping(canonical_field="q3.values", source_type=FieldSourceType.NATIVE, native_path="factor.score"),
            ],
            native_output={"raw": {"nested": [1, 2, 3]}},
        )

        payload = result.model_dump(mode="json")
        restored = AdapterResult.model_validate(payload)
        self.assertEqual(restored, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
