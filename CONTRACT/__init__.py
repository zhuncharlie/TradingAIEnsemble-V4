# CONTRACT package — re-exports the current schema contract + base adapter.
from CONTRACT.schemas import (
    SCHEMA_VERSION,
    Action, Direction, OutputScope, ConfidenceKind, FieldSourceType,
    PolicyType, UpdateMode,
    ContractModel, QueryContext, ConfidenceEstimate, EvidenceItem,
    FieldMapping, RunMetadata,
    Q1Action, StateEstimate, Q2State, Q3Signal,
    TimeWindow, UniversePolicy, ObservationPolicy, DecisionPolicy,
    UpdatePolicy, PortfolioConstraints, PolicyArtifact, PolicyDecisionStep,
    Q4Policy, AdapterResult,
)
from CONTRACT.base_adapter import AdapterContractViolation, BaseAdapter

__all__ = [
    "SCHEMA_VERSION",
    "Action", "Direction", "OutputScope", "ConfidenceKind", "FieldSourceType",
    "PolicyType", "UpdateMode",
    "ContractModel", "QueryContext", "ConfidenceEstimate", "EvidenceItem",
    "FieldMapping", "RunMetadata",
    "Q1Action", "StateEstimate", "Q2State", "Q3Signal",
    "TimeWindow", "UniversePolicy", "ObservationPolicy", "DecisionPolicy",
    "UpdatePolicy", "PortfolioConstraints", "PolicyArtifact", "PolicyDecisionStep",
    "Q4Policy", "AdapterResult", "BaseAdapter", "AdapterContractViolation",
]
