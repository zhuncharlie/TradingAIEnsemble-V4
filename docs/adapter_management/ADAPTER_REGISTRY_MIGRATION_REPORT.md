# Adapter Registry Migration Report

**Role**: Session 3 (pre-pilot readiness), Task D. Documents the move from the
original 3-tier system (`extended_all` / `popular_full` / `paper_core`) to the
6-set system required by this session's brief
(`popular_1000_plus` / `controlled_scientific_core` / `pilot_core` /
`methodological_exceptions` / `diagnostic_all`, plus `extended_all` kept
unchanged). No adapter was added or removed from the 26-adapter roster; no
`adapters/`, `CONTRACT/`, or other Python file was touched.

---

## 1. Why this migration happened

The existing `popular_full.yaml` was never actually gated on a star-count
threshold (see its own new deprecation header) — it excluded only `atlas` on
a correctness basis. This session's brief requires a genuinely
popularity-gated set (`stars >= 1000`) as a distinct, explicit filter, plus a
stricter, jointly-gated set for the claim-bearing historical main experiment
that also requires live-readiness and point-in-time replay capability
together — neither of which the old 3-tier system separated out as its own
named artifact.

## 2. Full per-adapter set membership

| Adapter | Old sets | New sets | Reason | Evidence |
|---|---|---|---|---|
| ai_hedge_fund | popular_full, paper_core | popular_1000_plus | Q1-only, `point_in_time_class: L` disqualifies it from `controlled_scientific_core` despite 62,273 stars and `live_status: PASSED` | `configs/adapter_registry.yaml` |
| alphaforge | popular_full, paper_core | (none of the 6 new named sets; remains in `extended_all`/`diagnostic_all`) | 402 stars — below the 1000-star gate; not flagged as a methodological exception because `atlas`/`finclaw` already cover the GA/evolutionary-factor-mining paradigm | `configs/adapter_registry.yaml` |
| alphagen | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core** | 1159 stars (just clears the gate), `live_status: PASSED`, `point_in_time_class: R`, no disqualifying caveat | `configs/adapter_registry.yaml` |
| atlas | extended_all only (already excluded from popular_full) | **methodological_exceptions** | 35 stars; real GA/GP paradigm but self-disclosed crypto-mislabeling caveat on non-crypto tickers — kept as a named "special calibration/mislabeling failure case," not silently dropped | `ADAPTER_SELECTION_REPORT.md` §3.1; `configs/adapter_registry.yaml` notes |
| deepalpha | popular_full, paper_core | **methodological_exceptions**, **pilot_core** (flagged exception) | 10 stars, lowest in roster — kept as the project's own calibration-failure case study; additionally the *only* historically-replayable Q1-capable adapter in the entire registry, making it a flagged, disclosed exception for `pilot_core`'s Q1-coverage requirement specifically | `ADAPTER_SELECTION_REPORT.md` §3.3; `configs/adapter_registry.yaml` |
| deepdow | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core** | 1173 stars, `live_status: PASSED`, `point_in_time_class: R` | `configs/adapter_registry.yaml` |
| earnmore | popular_full, paper_core | (none of the 6 new named sets) | 71 stars — below the gate; `finrl`/`finrl_x`/`trademaster` already cover `rl_deep_rl` more popularly | `configs/adapter_registry.yaml` |
| finagent | popular_full, paper_core (remediation-flagged) | (none of the 6 new named sets) | 75 stars — below the gate regardless of its `live_status: FAILED` remediation status; not elevated to `methodological_exceptions` because `finmem` already represents the memory/reflection paradigm at a closer-to-threshold star count | `configs/adapter_registry.yaml` |
| finbert | popular_full, paper_core | popular_1000_plus | 2187 stars, but `point_in_time_class: L` — yfinance headlines are current-only, not a point-in-time archive; disqualifies it from `controlled_scientific_core` regardless of `live_status: PASSED` | `configs/adapter_registry.yaml` notes; `NEW_ADAPTER_INTEGRATION.md` |
| finclaw | popular_full, paper_core | **methodological_exceptions** | No GitHub star signal exists (PyPI-distributed) — `popularity_gate_1000: not_applicable`, never treated as passing; kept as one of only two remaining GA/evolutionary representatives once `atlas`/`alphaforge` are excluded from claim-bearing use | `configs/adapter_registry.yaml`; `ADAPTER_SELECTION_REPORT.md` §3.3 |
| fingpt | popular_full, paper_core (remediation-flagged) | popular_1000_plus | 20,912 stars, but `live_status: FAILED` (conda env error) **and** `point_in_time_class: L` — double-disqualified from `controlled_scientific_core` | `configs/adapter_registry.yaml` |
| finmem | popular_full only (excluded from paper_core) | **methodological_exceptions** | 927 stars — closest miss on the 1000-star gate; `live_status: BLOCKED` (missing embeddings credential) is itself a named "important failure case" worth diagnostic tracking, per the task brief's own methodological-exception criteria | `configs/adapter_registry.yaml`; `ADAPTER_SELECTION_REPORT.md` §3.2 |
| finrl | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core** | 15,767 stars, `live_status: PASSED`, `point_in_time_class: R` | `configs/adapter_registry.yaml` |
| finrl_x | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core**, **pilot_core** | 3455 stars, `live_status: PASSED`, `point_in_time_class: R`; only adapter answering Q2+Q3+Q4 simultaneously — selected into `pilot_core` for that richness, with a disclosed dynamic-universe-selection risk (see `pilot_core.yaml`) | `configs/adapter_registry.yaml` |
| finrobot | popular_full only (excluded from paper_core) | popular_1000_plus | 7600 stars, but `point_in_time_class: L` disqualifies it from `controlled_scientific_core`; already excluded from the old `paper_core` for thin extractable-field coverage (<15% per Q) | `configs/adapter_registry.yaml`; `PROJECT_SCHEMA_AUDIT.md` §7 |
| pgportfolio | popular_full only (excluded from paper_core) | popular_1000_plus | 1849 stars, but `live_status: BLOCKED` (dead Poloniex API + transient yfinance rate limit) disqualifies it from `controlled_scientific_core` even though `point_in_time_class: R` | `configs/adapter_registry.yaml` |
| prediction_arena | popular_full, paper_core | (none of the 6 new named sets) | 76 stars — below the gate | `configs/adapter_registry.yaml` |
| qlib | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core**, **pilot_core** | 46,410 stars, `live_status: PASSED`, `point_in_time_class: R`; highest information-retention adapter per the original schema audit, MIT-licensed, no API key/GPU dependency — selected into `pilot_core` for reliability and low engineering effort | `configs/adapter_registry.yaml`; `PROJECT_SCHEMA_AUDIT.md` §7-8 |
| quantmuse | popular_full, paper_core | popular_1000_plus | 2793 stars, but `point_in_time_class: L` disqualifies it from `controlled_scientific_core` | `configs/adapter_registry.yaml` |
| rdagent | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core** | 13,944 stars, `live_status: PASSED`, `point_in_time_class: R`; deferred from `pilot_core` specifically for cost control (98.9s latency, real per-call LLM API cost) — reserved for the full claim-bearing experiment | `configs/adapter_registry.yaml` |
| skfolio | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core**, **pilot_core** | 2046 stars, `live_status: PASSED`, `point_in_time_class: R`, LOW cost tier, lowest latency (15.9s) of any Q4-capable adapter in the set — a reliable, cheap `pilot_core` anchor | `configs/adapter_registry.yaml` |
| trademaster | popular_full, paper_core | popular_1000_plus, **controlled_scientific_core**, **pilot_core** | 2933 stars, `live_status: PASSED`, `point_in_time_class: R`; selected into `pilot_core` as a second, independent RL portfolio-management paradigm, with a disclosed universe/window-incompatibility caveat (DJ30 2021, NVDA absent) vs. the rest of the pilot set | `configs/adapter_registry.yaml` |
| tradingagents | popular_full, paper_core (remediation-flagged) | popular_1000_plus | 93,683 stars (highest in the roster), but `live_status: FAILED` (280s timeout) **and** `point_in_time_class: L` — double-disqualified from `controlled_scientific_core` despite being the single most popular adapter in the entire registry | `configs/adapter_registry.yaml` |
| universal_portfolios | popular_full, paper_core | **methodological_exceptions** | 859 stars — closest miss on the 1000-star gate; the only classical *analytical* (closed-form) portfolio baseline in the roster, complementing `skfolio`'s rolling-convex-optimization family | `configs/adapter_registry.yaml`; `ADAPTER_SELECTION_REPORT.md` §3.3 |
| vibe_trading | popular_full, paper_core | popular_1000_plus | 25,256 stars, `live_status: PASSED`, `point_in_time_class: "R (via LEGACY_INTERNAL_LOOP replay only)"`, but `execution_class: STEPWISE_UNSUPPORTED` disqualifies it from `controlled_scientific_core` — its decision matrix is a frozen, pre-computed batch replay, not independently regenerable per causal rolling step, which `Q4_EXPERIMENT_REQUIREMENTS.md` requires | `configs/adapter_registry.yaml` |
| agentictrading | popular_full only (excluded from paper_core) | (none of the 6 new named sets) | 350 stars — below the gate; additionally already excluded from `paper_core` for native field coverage rated "极低" (very low), so no methodological-exception case was made for it either | `configs/adapter_registry.yaml`; `PROJECT_SCHEMA_AUDIT.md` §7 |

## 3. Summary counts

- **Moved out of the main claim-bearing set due to Star < 1000**:
  `agentictrading`, `alphaforge`, `atlas`, `deepalpha`, `earnmore`,
  `finagent`, `finclaw` (n/a — no star signal), `prediction_arena`,
  `universal_portfolios`, `finmem` — 10 adapters. Of these, 5
  (`deepalpha`, `atlas`, `finclaw`, `universal_portfolios`, `finmem`) are
  retained as named `methodological_exceptions`; the other 5 have no
  standalone diagnostic-value case beyond `extended_all`/`diagnostic_all`.
- **Excluded from `controlled_scientific_core` due to live failure**
  (despite passing the popularity gate): `fingpt` (conda env error),
  `pgportfolio` (dead upstream API + transient rate limit), `tradingagents`
  (280s LLM-latency timeout) — 3 adapters. All three remain in
  `popular_1000_plus`; none are silently dropped from the registry.
- **Excluded from `controlled_scientific_core` due to point-in-time
  failure** (despite passing the popularity gate and being live-PASSED):
  `ai_hedge_fund`, `finbert`, `finrobot`, `quantmuse` — 4 adapters, all
  `point_in_time_class: L` (current-context-bound, cannot be honestly
  backfilled to a historical decision date).
- **Excluded from `controlled_scientific_core` due to universe/execution
  incompatibility**: `vibe_trading` — `execution_class:
  STEPWISE_UNSUPPORTED` (batch-replay only, not independently regenerable
  per causal step).
- **Retained as `methodological_exceptions`**: `deepalpha`, `atlas`,
  `finclaw`, `universal_portfolios`, `finmem` — 5 adapters, each with a
  named, specific diagnostic-value reason (§2 above), consistent with the
  task brief's explicit instruction not to silently delete low-star
  projects.

## 4. The Q1-coverage gap (the most important finding of this migration)

`controlled_scientific_core` (8 adapters, all popular + live-PASSED +
historically-replayable) has **zero Q1 (Action) coverage**. Every
popular, live-PASSED, `point_in_time_class: R` adapter answers only
Q2/Q3/Q4 — no exception. The adapters that *do* answer Q1
(`ai_hedge_fund`, `finagent`, `finrobot`, `tradingagents`) are either
`point_in_time_class: L` (current-context-bound) or currently
`live_status: FAILED`/`BLOCKED`. The only historically-replayable,
live-PASSED Q1-capable adapter anywhere in the 26-adapter registry is
`deepalpha`, at 10 stars — far below the popularity gate.

**This is a real, load-bearing limitation for `EXPERIMENT_PROTOCOL.md`
§2.2's ontology**, specifically the "Cross-adapter directional conflict"
and "Intra-adapter Q1/Q3 direction mismatch" classes, which depend on Q1
`action` values. On `controlled_scientific_core` alone, at claim-bearing
historical scale, these two classes would have to be evaluated using only
`Q3Signal.direction` as a Q1 proxy across the 8-adapter set — a real,
disclosed scope narrowing, not a silent one. This finding is carried
forward into `docs/experiment_design/PILOT_PROTOCOL_DRAFT.md` (which
handles it via a flagged `deepalpha` exception, since the pre-pilot is
explicitly non-claim-bearing) and must be re-examined before any
claim-bearing historical experiment runs on `controlled_scientific_core`
— either by expanding the registry with a new, popular, historically-
replayable Q1 adapter (out of this session's scope to find/integrate), or
by explicitly scoping H1's headline result to the Q3-direction-only
reading of the ontology's directional-conflict classes and disclosing
that scoping prominently.

## 5. Legacy sets

`paper_core.yaml` and `popular_full.yaml` are **kept, not deleted**, each
with a new deprecation header explaining (a) why the name no longer
precisely describes the file's actual selection rule, and (b) which new
file to use instead for which purpose. Neither file's adapter list was
changed. See each file's own header for the full disclosure.
