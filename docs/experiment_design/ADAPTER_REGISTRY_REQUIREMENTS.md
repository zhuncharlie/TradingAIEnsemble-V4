# Adapter Registry Requirements — Handoff to Session 3

**This is a read-only requirements list, not a design or implementation.**
Session 2 does not modify Session 3's registry files, does not decide the
final adapter list, and does not touch `adapters/`, `CONTRACT/`, or any
Python file. This document exists so Session 3's registry can be built to
satisfy exactly what `EXPERIMENT_PROTOCOL.md` and `DATA_SPLIT_PROTOCOL.md`
need, without Session 2 guessing at Session 3's implementation.

---

## 1. Why this handoff exists

`EXPERIMENT_PROTOCOL.md`'s experiment groups (especially L1.1–L1.5's
diagnostics and L2.1–L2.6's methods) and `DATA_SPLIT_PROTOCOL.md`'s §5
eligibility tiers both need machine-readable per-adapter facts to select
the correct sample at each experiment stage. Today those facts live
scattered across three read-only prose documents
(`PROJECT_SCHEMA_AUDIT.md`, `ADAPTER_CAPABILITY_RECOVERY.md`,
`NEW_ADAPTER_INTEGRATION.md`) — this is a request for Session 3 to
formalize them into a queryable registry, not a claim that they don't
already exist in some form.

## 2. Required registry fields

| Field | Why the experiment protocol needs it | Source precedent (read-only, already observed) |
|---|---|---|
| `popularity_tier` | Main-paper experiments (`EXPERIMENT_PROTOCOL.md` §5/§6) use only "popular, reproducible, and method-diverse" adapters per the task brief's own instruction — this session cannot decide which subset that is without a tier field to filter on | `PROJECT_SCHEMA_AUDIT.md` §8's `P0/P1/P2/REJECT` priority tiers are a usable starting taxonomy |
| `paper_status` | Novelty/citation framing (Session 1) and reproducibility claims both need to know which adapters are official paper implementations vs. unofficial/demo-level | `PROJECT_SCHEMA_AUDIT.md` §3's per-project "官方实现?" (official implementation?) column, including the explicitly-flagged uncertain cases (FinAgent's probabilistic attribution, TradeMaster's unverified PDF code-availability claim) |
| `q_coverage` | L1.1 (Representation) and every L2 group need to know which of Q1/Q2/Q3/Q4 an adapter genuinely (not partially/derived) supports before it can be used as an input to that layer | `PROJECT_SCHEMA_AUDIT.md` §5's NATIVE/PARTIAL/UNSUPPORTED coverage matrix (27 rows) |
| `native_vs_derived` per field | L1.1's field-value ablation needs per-field, not just per-adapter, provenance | `CONTRACT/schemas.py`'s own `FieldSourceType` enum (NATIVE/DERIVED/HARNESS_SUPPLIED/MISSING) — already schema-native, the registry should expose it queryably rather than requiring a fresh read of each `field_mappings` output per query |
| `live_readiness` | `DATA_SPLIT_PROTOCOL.md` §5's TIER-1/2/3 eligibility gate is exactly this field, formalized | `ADAPTER_CAPABILITY_RECOVERY.md`/`NEW_ADAPTER_INTEGRATION.md`'s per-adapter PASSED/BLOCKED live-test results — e.g. FinMem BLOCKED (credential), PGPortfolio BLOCKED (dead API + transient rate limit) |
| `point_in_time_readiness` | Distinct from `live_readiness` — an adapter can be live-PASSED but PIT-unusable for a historical experiment (the FinBERT case: yfinance headlines are current-only, not historical-as-of) — conflating these two fields would silently make FinBERT look eligible for the historical main experiment when it is not | `NEW_ADAPTER_INTEGRATION.md`'s explicit FinBERT limitation note — this project already knows the distinction matters, it just isn't a first-class registry field yet |
| `stochasticity_class` | L1.2 (Calibration and Stability)'s K-repeat budget and X.3's seed/repeated-run analysis both branch on whether an adapter is deterministic / stochastic-ML-RL / LLM-based | Implicit in `ADAPTER_CAPABILITY_RECOVERY.md`'s adapter descriptions (e.g. LLM-based cost-per-call adapters vs. deterministic rule-based ones) but not a queryable field today |
| `expected_cost` (per-call `cost_usd`/`latency_sec` estimate) | `EXPERIMENT_DEPENDENCY_MAP.md`'s compute-budget gates need a per-adapter cost estimate before committing to a K-repeat or multi-baseline experiment, not just the `RunMetadata.cost_usd` value observed after the fact | Real observed costs already exist per adapter (e.g. tradingagents ~9-10 real LLM calls/run) but are scattered in run logs, not a registry-queryable prior estimate |
| `supported_horizon` | L1.2/L1.3/H1's horizon-stratified test needs to know which horizons {1d, 5d, 20d} each adapter can even produce a decision for | Not explicitly tabulated in the audit docs today — a genuine new field this registry should add, derivable from each adapter's `Q1Action.context.horizon`/`Q3Signal.context.horizon` support |
| `supported_universe` | `DATA_SPLIT_PROTOCOL.md` §4's universe-mapping table needs this per adapter (e.g. TradeMaster = DJ30-only, EarnMore = sector-grouped subsets) | `NEW_ADAPTER_INTEGRATION.md`'s per-adapter "Remaining Limitations" column already states several of these in prose |
| `q4_policy_type` | L1.5/L2.2/L2.3/L2.5 need `PolicyType` (STATIC_ALLOCATION / ROLLING_OPTIMIZER / FROZEN_LEARNED_POLICY / ONLINE_ADAPTIVE_POLICY, per `CONTRACT/schemas.py`) queryable per adapter to select the right baseline/comparison class | Already schema-native per adapter's own `Q4Policy.policy_type` output — registry should index it, not re-derive it |
| `current_limitations` (free text or structured) | `RISK_AND_FAILURE_PLAN.md` and every experiment group's "failure interpretation" field need a queryable link back to known, already-documented limitations, so a future result anomaly can be checked against a known cause first (e.g. is this outlier explained by the already-known Qlib calendar-boundary bug, or is it a genuine new finding?) | `ADAPTER_CAPABILITY_RECOVERY.md`'s "剩余损失"/"Remaining Limitations" column, `NEW_ADAPTER_INTEGRATION.md`'s "Remaining Limitations" column |

## 3. Fields this session explicitly does NOT request

Per CLAUDE.md §2/§5 and this session's own scope: no field for
backtest/return/Sharpe/drawdown metrics computed *by the adapter itself*
(those belong to the evaluation layer per `PROJECT_SCHEMA_AUDIT.md` §10's
explicit, already-correct exclusion — this session reuses that exclusion,
does not relitigate it). No field that would require Session 3 to fabricate
a value an adapter doesn't genuinely produce.

## 4. What this session does NOT decide

- The final adapter subset used in the historical main experiment — that
  is a query *against* the registry once built (`DATA_SPLIT_PROTOCOL.md`
  §5's tiers are eligibility *criteria*, not a hardcoded list, per the
  task brief's explicit instruction).
- The registry's storage format, schema, or implementation — out of this
  session's file-isolation scope (`docs/adapter_management/` is
  explicitly off-limits).
- Any change to `CONTRACT/schemas.py` or any adapter file.
