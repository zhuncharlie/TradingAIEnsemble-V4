# Registry Gap Analysis

**Role**: Session 3 (pre-pilot readiness), Task C. Compares the existing
`configs/adapter_registry.yaml` (26 entries, built by a concurrent
"research/literature" session, already spot-verified honest and internally
consistent per its own self-audit at `docs/research_reports/
2026-07-19_adapter_registry_self_audit.md`) against `docs/experiment_
design/ADAPTER_REGISTRY_REQUIREMENTS.md` (Session 2's handoff spec) and
`docs/experiment_design/DATA_SPLIT_PROTOCOL.md` §5 (eligibility tiers).
**The existing registry is not assumed wrong and is not rewritten from
scratch** — every field below is classified `KEEP AS-IS`, `RENAME/
RESTRUCTURE`, or `ADD`, with the upgrade in `configs/adapter_registry.yaml`
implementing exactly this ledger, minimally.

---

## 1. Fields to KEEP AS-IS (already satisfy the requirement)

| Existing field | Requirement it satisfies | Why no change needed |
|---|---|---|
| `name`, `github`, `requires_env`, `q_coverage` | Identity, `q_coverage` | Direct source grep, line-verified, exactly what's needed |
| `stars_snapshot`, `forks`, `license`, `last_pushed` | Popularity raw data | Live GitHub API snapshot, dated; feeds the new `popularity_gate_1000`/`popularity_tier` fields (§2) without needing re-fetch |
| `commit` | Reproducibility (partial) | Already honestly discloses "HEAD of default branch" vs. a real pinned SHA (`trademaster` only) — see §2 for the structured upgrade that doesn't discard this text |
| `paper` | Paper provenance (partial) | Already populated only from in-file docstring citations, with one explicitly-disclosed self-caught fabrication incident excluded (`trademaster`) — this is exactly `ADAPTER_REGISTRY_REQUIREMENTS.md`'s "not by an agent's general knowledge" rule already followed; kept verbatim, structured `paper_status`/`paper_verification_source` added alongside (§2), not replacing it |
| `category` | Methodological-diversity input | Already the basis for the existing report's 11-category diversity table; reused as-is for `q_coverage`/paradigm-diversity gates in the new adapter sets (Task D) |
| `live_status` | `live_readiness` requirement | Already exactly PASSED/FAILED/BLOCKED, sourced from `results/unified_harness/unified_harness_summary.json` — this **is** `live_readiness`, just needs the name confirmed, not re-derived |
| `point_in_time_class` | `point_in_time_readiness` requirement | Already exactly the R/L distinction `DATA_SPLIT_PROTOCOL.md` §5 needs, and already correctly separates `live_status` from PIT status (e.g. `finbert`: `live_status: PASSED`, `point_in_time_class: L` — this is precisely the "must be separated, not conflated" requirement already met) |
| `latency_sec_observed` | `expected_cost` (latency half) | Real, already-observed single-run value; the registry's own §5 limitation note ("a single observation... not a distribution") is honestly disclosed already — `latency_observation_count` is added (§2) to make that disclosure machine-queryable, not to fix an error |
| `notes` | `current_limitations`, misc | Rich, adapter-specific, evidence-grounded prose already covers most of what `limitations`/`remediation_required` need — structured fields are added (§2) to make the *existing* prose machine-queryable, not to replace it |

## 2. Fields to ADD (genuine gaps against `ADAPTER_REGISTRY_REQUIREMENTS.md`)

| New field | Gap it closes | Derivation rule (evidence-only, no fabrication) |
|---|---|---|
| `commit_status: PINNED \| SNAPSHOT_ONLY \| UNKNOWN` | Structured reproducibility field `ADAPTER_REGISTRY_REQUIREMENTS.md` §2 asked for, currently only implicit in `commit`'s free text | `PINNED` only for `trademaster` (the one adapter with a real SHA in-file); `SNAPSHOT_ONLY` for the other 25 (a real GitHub HEAD was recorded at snapshot time, just not a pinned SHA); `finclaw` gets `SNAPSHOT_ONLY` too (PyPI version pin `5.6.1` is itself a real, if non-Git, snapshot identifier) |
| `snapshot_date` (per-adapter) | The existing top-level `snapshot_date: "2026-07-19"` applies globally, but `finclaw`'s own entry already documents a *different* PyPI-release date in its `last_pushed` field — worth a per-adapter field so this doesn't require reading prose to notice | Copy the top-level date for 25 adapters; for `finclaw`, record both (registry snapshot date = 2026-07-19, matching the rest; PyPI artifact date stays in `last_pushed` as already written, unchanged) |
| `popularity_gate_1000: true \| false \| not_applicable` | User's stated main-experiment popularity preference (stars ≥ 1000), not previously gated as a boolean | Mechanical: `true` if `stars_snapshot >= 1000`, `false` if `stars_snapshot` is a real number `< 1000`, `not_applicable` only for `finclaw` (no GitHub stars exist — PyPI-distributed; **never** interpreted as `>= 1000` per the task brief's explicit warning not to treat missing stars as passing the gate) |
| `popularity_tier` | Coarser bucketing for reporting/sampling | Derived mechanically from `stars_snapshot`: `VIRAL` (>=10000), `ESTABLISHED` (1000-9999), `NICHE` (100-999), `OBSCURE` (<100), `NOT_APPLICABLE` (finclaw) — thresholds are a simple, disclosed convention, not a claim about real-world significance |
| `paper_status: OFFICIAL_IMPLEMENTATION \| PROBABLE_IMPLEMENTATION \| SOFTWARE_NO_PAPER \| UNOFFICIAL \| UNKNOWN` | Structured version of the existing free-text `paper` field | `OFFICIAL_IMPLEMENTATION` where the adapter's own docstring both cites a paper **and** self-identifies as that paper's code (`alphagen`: repo self-identifies as the KDD 2023 paper's own code); `UNOFFICIAL` where a paper is cited but the adapter is an explicitly-disclosed substitute, not the paper's own code (`prediction_arena`: wraps Metaculus/forecasting-tools + Kalshi, not arXiv:2604.07355's own unreleased code); `PROBABLE_IMPLEMENTATION` for `alphaforge` (AAAI 2025 citation in-file, no explicit "this is the official repo" self-statement found); `SOFTWARE_NO_PAPER` for adapters whose category is a software tool/framework with no claimed paper (e.g. `deepdow`, `universal_portfolios`, `quantmuse`); `UNKNOWN` for the remaining `paper: null` entries where no in-file signal exists either way — **never** upgraded to a positive status from outside knowledge |
| `paper_verification_source` | Where the `paper_status` judgment came from | For the 3 populated cases: the exact adapter file/docstring passage already quoted in `ADAPTER_SELECTION_REPORT.md` §1; for `UNKNOWN`/`SOFTWARE_NO_PAPER`, states `"no in-file citation found, not independently searched"` — honest about the boundary of what was checked |
| `field_provenance` (per-Q pointer, not full copy) | `ADAPTER_REGISTRY_REQUIREMENTS.md`'s "native/derived per field, machine-queryable" requirement | A structured pointer object per adapter: `{source: "PROJECT_SCHEMA_AUDIT.csv", filter: "project == '<name>'"}` plus a compact per-Q summary count already derivable from that CSV (e.g. `{q1: "NATIVE", q3: "DERIVED(weak)"}` using the audit's own NATIVE/DERIVED/PARTIAL/UNSUPPORTED vocabulary) — **not** a 474-row copy into YAML, exactly as the task brief allows |
| `historical_replay_ready` | Distinct from both `live_status` and `point_in_time_class` — whether the adapter can actually be driven through a **rolling historical window**, not just answer one point-in-time query | `true` only for adapters that are both `point_in_time_class: R` **and** `live_status: PASSED` **and** have no adapter-specific replay-breaking caveat recorded in `notes` (excludes `atlas`, whose crypto-mislabeling caveat makes non-crypto historical replay unsafe even though it's nominally `R`+`PASSED`); `false` for all `point_in_time_class: L` adapters (current-context-bound by construction) and any `R`+non-PASSED adapter; a third value `CAVEAT` for `atlas` specifically, since blanket `false` would understate its real crypto-scoped replay capability |
| `controlled_track_eligible` | Direct implementation of `DATA_SPLIT_PROTOCOL.md` §4's Controlled Scientific Track gate | `true` only if `historical_replay_ready` is `true` (or `CAVEAT` with the caveat scope respected) **and** `popularity_gate_1000` is `true` **and** no unresolved `live_status: BLOCKED`/`FAILED` — see §3's worked eligibility table |
| `eligibility_tier: TIER_1 \| TIER_2 \| TIER_3` | Direct implementation of `DATA_SPLIT_PROTOCOL.md` §5's tiers | Mechanical function of `controlled_track_eligible` + `live_status` + `point_in_time_class`, see §3 |
| `eligibility_reasons` (list) | Auditability of the tier assignment | Free-text list, each entry citing the specific registry field that drove the classification (e.g. `"live_status=BLOCKED (embeddings credential missing)"`) — not a new judgment, a structured echo of already-recorded facts |
| `supported_horizons` | Missing entirely — no adapter previously recorded which of {1d, 5d, 20d} it can natively answer | Derived only where directly evidenced: adapters with an explicit `context.horizon` field observed in `results/unified_harness/` output, or a documented rebalance/holding-period in `notes` (e.g. `skfolio`'s `REBALANCE_PERIOD_DAYS`); marked `unknown` (not defaulted to "all three") everywhere the evidence doesn't exist — a genuine, disclosed gap this pass cannot close without re-running adapters, which is out of this task's configs/docs-only scope |
| `supported_universe` | Currently only in prose (`atlas`: crypto-only; `trademaster`: DJ30 2021; `earnmore`: 2008-09 crisis window) | Structured from the *same* already-documented prose, not new research — a direct copy of already-verified facts into a queryable field |
| `supported_asset_classes` | Not previously recorded | Derived from `supported_universe` + `category` (e.g. `atlas`/`pgportfolio` → `[crypto]`; the equity-universe majority → `[equity]`) — mechanical, not a new claim |
| `stochasticity_class: DETERMINISTIC \| STOCHASTIC_ML_RL \| LLM_BASED` | `ADAPTER_REGISTRY_REQUIREMENTS.md`'s explicit ask, needed for L1.2's K-repeat budget | Derived from `category`: `llm_agent_*`/`llm_fusion_quant`/`forecasting_prediction_market` categories → `LLM_BASED`; `rl_deep_rl*`/`ga_evolutionary_*`/`deep_learning_portfolio_allocation`/`gradient_boosted_ml` → `STOCHASTIC_ML_RL`; `classical_optimization`/`sentiment_nlp` (pretrained-inference-only, no training/search) → `DETERMINISTIC` — one boundary case (`sentiment_nlp`'s `finbert`, pure inference, no stochastic decoding observed) resolved to `DETERMINISTIC`; `fingpt` (same category but decodes via a language model) resolved to `LLM_BASED` despite the shared category, since the *mechanism* (LLM generation), not the category label, is the correct classification basis |
| `q4_policy_type` (Q4 adapters only, from `CONTRACT.PolicyType` enum) | **Explicitly required to be separated from `execution_class`** — the existing registry's `execution_class` field currently mixes two taxonomies (see §3 of this document for the detailed finding) | Split out of the existing `execution_class` values that are actually `PolicyType` enum members (`STATIC_ALLOCATION`, `ROLLING_OPTIMIZER`, `FROZEN_LEARNED_POLICY`, `ONLINE_ADAPTIVE_POLICY`) — read directly from each adapter's own `Q4Policy.policy_type` output already captured in the existing registry's `execution_class` cell, just re-homed to the correctly-named field |
| `execution_class` (redefined, Q4 adapters only, rolling-execution-support taxonomy) | Same conflation fix, other half | Keeps the existing registry's genuinely-distinct rolling-support values (`STEPWISE`, `STATIC_ONLY`, `STEPWISE_UNSUPPORTED`) as this field's actual domain; the `PolicyType`-flavored values move to the new `q4_policy_type` field instead |
| `state_persistence_required` | Not previously recorded | `true` only for adapters whose `execution_class` (new sense) is `STEPWISE` **and** `q4_policy_type` is `ONLINE_ADAPTIVE_POLICY` (state must carry across steps); `false` otherwise — mechanical from the two fields just split apart |
| `requires_paid_api` (bool) | `cost_tier: HIGH` conflates "needs a paid API" and "needs heavy local compute" per the existing registry's own §5/self-audit N2 disclosure | `true` for the 9 adapters already marked `cost_tier: HIGH` in the current registry (their `notes` already state the specific paid LLM API used, e.g. DeepSeek) — a direct, already-evidenced split, not new research |
| `api_cost_class` / `local_compute_class` | Same conflation fix, two independent axes replacing the one `cost_tier` ordinal | `api_cost_class ∈ {NONE, PER_CALL_LLM}`; `local_compute_class ∈ {CPU_LIGHT, CPU_OR_GPU_TRAINING}` — derived from the same evidence already in each adapter's `notes` (e.g. `fingpt`: `api_cost_class=NONE`, `local_compute_class=CPU_OR_GPU_TRAINING`, already stated in its notes as "local GPU inference... no paid API") |
| `latency_observation_count` | Registry's own §5 already discloses `latency_sec_observed` is "a single observation... not a distribution" | `1` for all 26 entries (honest, matches the disclosed limitation exactly — not upgraded without new profiling, consistent with this task's explicit permission to use `estimated, not freshly profiled` telemetry) |
| `credential_requirements` (structured list) | Currently only in `requires_env`/`notes` prose | Direct structuring of already-stated facts (e.g. `finmem`: `["OpenAI-compatible embeddings endpoint (currently unavailable — 401)"]`) |
| `estimated_pilot_cost` | Not previously recorded (registry's own §5 explicitly flags this as needing a follow-up `system-profile` pass, not done in the original design pass either) | `unknown` for every adapter — **not fabricated as a number**; this task's own instructions allow `estimated, not freshly profiled` only where *some* telemetry exists (`latency_sec_observed` does), but a dollar-cost estimate requires a metered run that has never happened for any of the 26 adapters, so `unknown` is the honest value throughout, explicitly not a placeholder number |
| `limitations` (structured list, replacing free-text-only) | `ADAPTER_REGISTRY_REQUIREMENTS.md`'s explicit ask to structure, not just narrate | One list entry per distinct limitation already named in `notes` (e.g. `finmem`: `["Live path BLOCKED — 401 on embeddings endpoint", "No Q4 (upstream Portfolio has no cash field)"]`) — a direct restructuring of existing prose, adding no new claims |
| `remediation_required` (bool) | Was previously prose-only (`ADAPTER_SELECTION_REPORT.md` §3.4's remediation-flag table) | `true` for exactly the 3 adapters already named in that table (`finagent`, `tradingagents`, `fingpt`) plus the 2 `BLOCKED` adapters (`finmem`, `pgportfolio`) — a direct structuring of an already-existing, already-evidenced list |
| `remediation_status` | Same | `KNOWN_FIX_AVAILABLE` for the 3 timeout/env-error cases (already described as "plausibly fixable infra issues" in the existing report); `BLOCKED_EXTERNAL` for `finmem` (needs a credential this project doesn't control) and `pgportfolio` (needs a dead upstream API or a stable data substitute) |

## 3. Corrections, not just additions

- **`execution_class` conflates two taxonomies — a real, structural gap, not
  a naming quibble.** Direct evidence: the existing registry's own values
  for this field include both rolling-execution-support labels
  (`STEPWISE`, `STATIC_ONLY`, `STEPWISE_UNSUPPORTED` — e.g. `qlib`,
  `finclaw`, `vibe_trading`) **and** `CONTRACT.PolicyType` enum members
  (`FROZEN_LEARNED_POLICY`, `ONLINE_ADAPTIVE_POLICY` — e.g. `deepdow`,
  `finrl`, `finagent`), sometimes in the same cell with a parenthetical
  ("FROZEN_LEARNED_POLICY (reclassified for stepwise path...)" for
  `finrl`/`finrl_x`) that itself shows the two concepts were being
  manually reconciled ad hoc, field-by-field, rather than represented as
  two separate fields. This is exactly the gap `Q4_EXPERIMENT_
  REQUIREMENTS.md`'s "execution_class=STEPWISE 不等于 q4_policy_type"
  instruction anticipates. **Fix**: split into `q4_policy_type` (the
  `PolicyType` enum value) and `execution_class` (redefined to only ever
  take the three rolling-support values) — see §2's two rows above. No
  adapter's underlying fact changes; only the field structure does.

## 4. Fields NOT added, with reasons (avoiding scope creep)

- **No per-adapter dollar cost figure** — would require a real metered run
  of 21+ adapters, outside this configs/docs-only task's scope (already
  correctly declined once in the original design pass, §5's own
  limitation note; re-declined here, not silently re-attempted).
- **No new `supported_horizons` values invented where no evidence exists**
  — recorded `unknown` rather than guessed; a real, disclosed gap, not
  hidden by defaulting to "supports everything."
- **No rewrite of `notes`** — the free-text field is preserved verbatim for
  every adapter; new structured fields are additive, not a replacement of
  the existing (already-audited, already-trustworthy) narrative record.
- **No change to the 26-adapter roster** — no adapter added or removed;
  `Alpha-GFN`/`real NoFx` remain correctly excluded (`excluded_from_roster`
  block, unchanged).

## 5. Summary of the upgrade's shape

- **9 existing top-level fields**: unchanged.
- **1 existing field split into 2** (`execution_class` → `q4_policy_type` +
  redefined `execution_class`): a genuine structural fix, not a rename.
- **~19 new fields added** per adapter, every one traced above to either
  direct evidence already in the registry/reports/audit files, or an
  honest `null`/`unknown`/`not_applicable` where no evidence exists.
- **Zero new adapters, zero removed adapters, zero changed `live_status`/
  `point_in_time_class`/`stars_snapshot`/`category` values** — this is a
  minimal-modification upgrade, not a rewrite, per the task brief's
  explicit instruction.
