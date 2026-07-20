# ADAPTER_SELECTION_REPORT.md

Status: design document for the adapter plug-in management system. No
existing adapter, schema, or harness core logic is modified by this
document. Only `configs/` and `docs/adapter_management/` are touched, per
this task's brief.

Companion artifacts: `configs/adapter_registry.yaml` (full per-adapter
record), `configs/adapter_sets/{paper_core,popular_full,extended_all}.yaml`
(the three tiers this report justifies).

---

## 0. Provenance and one deliberate omission

Every fact in the registry and this report is grounded in one of three
sources, each cited inline where it matters:

1. Direct `grep` of `adapters/*.py` source for `upstream_repo`,
   `requires_env`, `questions_answered` (exact, unambiguous — line numbers
   verified, not paraphrased).
2. A live GitHub REST API snapshot taken during this design pass
   (2026-07-19) for stars/forks/license/last-pushed-date.
3. Explicit statements inside each adapter's own module docstring (paper
   citations, upstream-verification notes, category description).

**One deliberate omission, stated plainly**: a research pass over all 26
adapter docstrings (used to extract paper/category/cost signals) initially
reported that `trademaster` is "NeurIPS 2023, arXiv:2310.08144." This claim
was checked directly against `adapters/trademaster_adapter.py` and **no
such citation exists anywhere in that file** — the research pass appears
to have supplied outside/general knowledge rather than reporting only what
the file states, despite being explicitly instructed not to. TradeMaster
may well have a real NeurIPS 2023 paper in the broader literature, but
since the adapter's own verification docstring does not state it, it is
excluded from `adapter_registry.yaml`'s `paper` field for `trademaster` —
consistent with this project's fabrication-avoidance rule (CLAUDE.md §2:
populate a field only from direct upstream output, a documented
derivation, or information explicitly supplied by the harness/task — not
from an agent's general knowledge). The same research pass also reported
two incorrect `upstream_repo` URLs (for `tradingagents` and
`vibe_trading`); both were caught against direct `grep` output and
corrected in the registry. **Lesson for future adapter-management work**:
verify any subagent's citation-level claims against direct source
inspection before writing them into a permanent registry — a "read the
docstring and report only what's there" instruction is not sufficient on
its own to prevent fabrication.

---

## 1. What the registry records

`configs/adapter_registry.yaml` — one entry per adapter, 26 total
(`adapters/example_stub_adapter.py` excluded as the non-deliverable
reference stub). Fields, per the task brief:

| Field | Source | Notes |
|---|---|---|
| `name`, `github`, `requires_env`, `q_coverage` | direct source grep | exact, line-verified |
| `stars_snapshot`, `forks`, `license`, `last_pushed` | live GitHub API, 2026-07-19 | `finclaw` has none — PyPI-distributed, not GitHub |
| `commit` | adapter docstring where a vendor commit is pinned; else "HEAD of default branch as of snapshot_date" | only `trademaster` pins an exact commit in-file |
| `paper` | adapter docstring only (§0's rule) | populated for 3/26: `alphaforge`, `alphagen`, `prediction_arena` (with a caveat on the last) |
| `category` | adapter docstring's own description of what it wraps | 11 categories used, see §2 |
| `cost_tier` | derived from `requires_env` + docstring compute/API description | LOW / MEDIUM / HIGH, see §2 |
| `live_status` | `results/unified_harness/unified_harness_summary.json` (run `unified_harness_2026_07_18`) | PASSED / FAILED / BLOCKED |
| `point_in_time_class` | `docs/experiment_design/DATA_SPLIT_PROTOCOL.md` §1 (reused, not re-derived) | R (replay-capable) / L (live-context-bound) |
| `latency_sec_observed` | same unified_harness run | one observation, not a distribution — see §5 caveat |
| `execution_class` | `q4_stepwise_support.csv` (Q4 adapters only) | STEPWISE / STATIC_ONLY / STEPWISE_UNSUPPORTED |
| `notes` | synthesis of the above + specific data-quality caveats | e.g. `atlas`'s crypto-mislabeling |

---

## 2. Landscape summary

**Q-coverage** (26 adapters): Q1=6, Q2=7, Q3=10, Q4=13 — `qlib` answers
Q3+Q4, easy to miss in a quick scan (confirmed via direct grep of
`adapters/qlib_adapter.py`).

**Category distribution** (11 categories, methodological diversity is
real, not superficial):

| Category | Adapters |
|---|---|
| `llm_agent_*` (5 sub-flavors) | `ai_hedge_fund` (hybrid rule-based), `finagent` (online-adaptive), `finmem` (memory/reflection), `finrobot` (multi-agent debate, AutoGen), `tradingagents` (multi-agent debate, Bull/Bear), `vibe_trading` (code generation) — 6 total |
| `ga_evolutionary_factor_mining` | `alphaforge`, `atlas`, `finclaw` (3) |
| `rl_deep_rl` (+ 1 regime-switching variant) | `alphagen`, `earnmore`, `finrl`, `finrl_x`, `trademaster` (5) |
| `gradient_boosted_ml` | `deepalpha`, `qlib` (2) |
| `deep_learning_portfolio_allocation` | `deepdow`, `pgportfolio` (2) |
| `classical_optimization` | `agentictrading`, `skfolio`, `universal_portfolios` (3) |
| `sentiment_nlp` | `finbert`, `fingpt` (2) |
| `llm_fusion_quant` | `quantmuse` (1) |
| `forecasting_prediction_market` | `prediction_arena` (1) |
| `research_loop_automated_hypothesis` | `rdagent` (1) |

**Cost tiers**: LOW (CPU-only, no paid API, no heavy training) = 4
(`agentictrading`, `finbert`, `skfolio`, `universal_portfolios`); MEDIUM
(local compute-heavy, no recurring API cost) = 13; HIGH (requires a paid
external LLM API call per invocation) = 9. A paper budgeting compute
should read `cost_tier` alongside `latency_sec_observed` — HIGH-cost
adapters are not necessarily the slowest (`ai_hedge_fund`: 14.2s, HIGH;
`alphagen`: 115.1s, MEDIUM) since API latency and local-compute latency
are different bottlenecks.

**Live status** (from the most recent full harness run): 21 PASSED, 3
FAILED (`fingpt` — conda env error; `tradingagents`, `finagent` — 280s
timeout, LLM-latency-bound), 2 BLOCKED (`finmem` — missing embeddings
credential; `pgportfolio` — dead upstream API + transient rate limit).
None of the 3 FAILED cases look like a methodology defect — all three are
plausibly fixable infra issues (raise timeout budget, fix conda env) —
see paper_core's remediation flags in §3.

**Star range**: 10 (`deepalpha`) to 93,683 (`tradingagents`) — a
~9,400x spread. This alone is why popularity cannot be the sole selection
axis: `deepalpha`'s 10 stars would trivially fail any star-count
threshold, yet it is the pilot study's own calibration-failure case study
and the adapter D2/M2 in `EXPERIMENT_PROTOCOL.md` are explicitly built
around re-verifying (see its registry entry).

---

## 3. Selection rule and per-adapter reasoning

Four principles, applied in this priority order when they conflict
(stated explicitly so the ordering itself is auditable, not implicit):

1. **Reproducibility** — can this adapter's result be trusted and
   regenerated? (real, verified upstream code; live status; data-quality
   caveats like `atlas`'s mislabeling; pinned commit where available.)
   This is checked first because a result that can't be trusted shouldn't
   be in a headline table regardless of how popular or diverse it is.
2. **Methodological diversity** — does this adapter represent a category
   not otherwise covered, or is it redundant with a stronger same-category
   pick? Diversity can *override* a popularity/star-count concern (see
   `deepalpha`, `finclaw`, `universal_portfolios` below) — this is the
   direct answer to the brief's "不要简单删除低star项目" instruction.
3. **Paper relevance** — is this adapter the verified official code for a
   real paper, or closely paper-adjacent? Only 3 adapters qualify under
   the strict in-file-citation rule (§0); this principle is a tie-breaker,
   not a primary filter, given how few adapters have a verifiable citation.
4. **Popularity** — GitHub stars, as a secondary signal of community
   trust and long-term maintenance likelihood, used only to choose between
   otherwise-comparable candidates within the same category (e.g. `qlib`
   at 46,410 stars over a same-category alternative), never to disqualify
   a low-star adapter that passes 1-3.

### 3.1 Tier definitions (strictly nested: paper_core ⊂ popular_full ⊂ extended_all)

- **extended_all** (26): everything. Used for Layer 1 diagnostic/audit
  experiments (D1-D7) where characterizing the *whole* landscape —
  including broken, blocked, or narrow-scope adapters — is the point.
- **popular_full** (25 = extended_all − 1): excludes only `atlas`.
  `atlas`'s exclusion is a **correctness** decision, not a popularity
  filter: its bundled dataset is crypto-perpetuals-only, and for any
  non-crypto ticker it silently repeats the same BTCUSDT signal under a
  different label. Including it in a broad *comparison* (not just an
  audit) would inflate sample size with duplicate, mislabeled
  observations — a data-integrity bug, not a fair "this adapter performs
  worse" result. `atlas` remains fully eligible for any crypto-scoped
  study and for `extended_all`'s diagnostic use (where the mislabeling
  itself is exactly what D1/D4 are designed to catch).
- **paper_core** (21 = popular_full − 4): the recommended set for the
  paper's main experiment table (Layer 1 headline diagnostics D1-D5,
  Layer 2 fusion methods M1-M4 in `EXPERIMENT_PROTOCOL.md`).

### 3.2 The 4 exclusions from paper_core (beyond `atlas`), each adapter-specific

| Adapter | Reason excluded | Why not "just low popularity" |
|---|---|---|
| `agentictrading` | Native field coverage rated 极低 (very low) in `PROJECT_SCHEMA_AUDIT.md` §7 — contributes mostly noise to a headline table despite PASSED live status and 350 real stars. | Popularity is fine (350★, real repo); the problem is almost nothing recoverable is actually exposed as Q4 signal. A coverage defect, not a popularity one. |
| `finmem` | Live path structurally BLOCKED (401 on the embeddings endpoint its real memory/reflection subsystem needs) — cannot currently produce a live result at all. | 927★, real MIT-licensed project, legitimate `llm_agent_memory_reflection` category — excluded purely because it cannot run today, not because it's unpopular or low-quality. Revisit once an embeddings-capable credential is available. |
| `finrobot` | <15% field coverage per Q (`PROJECT_SCHEMA_AUDIT.md` §7); Q1 is DERIVED best-effort keyword extraction from AutoGen chat prose, not a native structured output. `tradingagents` already covers the multi-agent-debate LLM category with a stronger, more direct signal (once its timeout is fixed). | 7,600★, from the well-known AI4Finance-Foundation ecosystem — genuinely popular. Excluded for thin *extractable* signal despite the popular upstream, and because the category is already represented. |
| `pgportfolio` | Crypto-only upstream domain (BTC-USD/ETH-USD substituted for the real Poloniex-only design) plus currently BLOCKED (dead upstream API + transient yfinance rate limit). `deepdow` already covers `deep_learning_portfolio_allocation` on the standard equity/ETF universe. | 1,849★, real and historically significant EIIE-CNN architecture, offline unit tests pass 11/11 — excluded for scope-mismatch with the paper's standard universe and current live blockage, not popularity. |

### 3.3 Three deliberate low-popularity *inclusions* (the "don't just delete" cases)

| Adapter | Stars | Why included despite low/no popularity signal |
|---|---|---|
| `deepalpha` | 10 (lowest in the roster) | It is the pilot study's own running example of a calibration failure (`EXPERIMENT_REPORT.md` §8: naive confidence-weighted fusion underperformed majority vote, traced to this adapter dominating the weighted average). `EXPERIMENT_PROTOCOL.md`'s D2/M2 experiments are explicitly written around re-verifying this exact case. Excluding it from paper_core would remove the experiment design's own headline illustrative example. |
| `finclaw` | none (PyPI-distributed, not GitHub — no star signal exists) | Once `atlas` is excluded (§3.1), `finclaw` is one of only two remaining `ga_evolutionary_factor_mining` representatives (with `alphaforge`). Its real, substantial (88,606-line) source was directly inspected despite the nominal GitHub repo having been pivoted to a marketing page — reproducibility was verified by reading actual code, not by trusting a star count that doesn't exist for this distribution channel. |
| `universal_portfolios` | 859 (modest) | The only classical *analytical* (closed-form, no optimization solver) portfolio baseline in the roster, complementing `skfolio`'s rolling-convex-optimization approach. A "classical baseline" category needs at least one representative regardless of star count, and this is the only real candidate. |

### 3.4 Remediation-flagged inclusions (in paper_core, but need an infra fix first)

`finagent`, `tradingagents`, and `fingpt` are all included in
`paper_core` despite currently FAILING in the live harness — in all three
cases the failure is an infrastructure issue (280s timeout for the first
two, both LLM-latency-bound; a conda environment error for the third), not
a sign the underlying methodology is unsound. `tradingagents` in
particular has the highest star count in the entire roster (93,683) and
represents the multi-agent-debate category at its most well-known and
carefully engineered — excluding it purely because the current timeout
budget is too tight would be a self-inflicted loss for the paper's
methodological-diversity story. **Before running any paper_core
experiment**, confirm these three are unblocked (raise the harness timeout
for the first two; fix the conda environment for the third) — do not
silently report paper_core results with 18/21 adapters and call it 21.

---

## 4. Cross-reference to the experiment protocol

This registry and its tiers are designed to slot directly into
`docs/experiment_design/EXPERIMENT_PROTOCOL.md` without requiring changes
to that document:

- **D1-D7 (Layer 1 diagnostics)**: use `extended_all` — the point is
  characterizing the whole landscape, including `atlas`'s mislabeling
  (itself a D1/D4 finding) and the 5 adapters excluded from `paper_core`.
- **M1-M4 (Layer 2 fusion methods)**: use `paper_core` once the 3
  remediation flags in §3.4 are cleared; fall back to `popular_full` if a
  broader, less-curated comparison is specifically wanted (e.g. to show a
  result is robust to including `agentictrading`/`finmem`/`finrobot`/
  `pgportfolio`).
- **A1-A2 (ablations), Ro1-Ro3 (robustness)**: inherit whichever adapter
  set the underlying M-method was evaluated on (per
  `EXPERIMENT_PROTOCOL.md` §5's cross-reference table) — do not
  re-litigate the adapter-set choice per ablation arm.

---

## 5. Known limitations of this registry (stated, not hidden)

- **`latency_sec_observed` is a single observation per adapter**, from one
  harness run (`unified_harness_2026_07_18`), not a distribution. D3
  (stability audit) in `EXPERIMENT_PROTOCOL.md` will produce N≥5 repeat
  measurements for Class-R adapters — this registry's latency field should
  be treated as a rough triage signal only, not a benchmark result.
- **`stars_snapshot` is a point-in-time value** (2026-07-19). Re-fetch
  before using this registry to make a claim about "current" popularity
  in any paper written more than a few months after this snapshot date.
- **`cost_tier` is a coarse 3-bucket estimate**, not a metered dollar
  figure — no adapter in this roster was actually run to completion
  during this design pass to measure real token/API spend (that would
  require executing 21+ adapters across their pinned conda environments,
  outside this task's configs/docs-only scope). A `system-profile` pass
  per adapter (see §6) is the natural follow-up if metered cost figures
  are needed for the paper's compute-budget section.
- **`paper` is populated for only 3/26 adapters** under the strict
  in-file-citation rule (§0). This undercounts real-world paper
  associations (e.g. `pgportfolio`, `trademaster`, and `finbert` likely do
  have real associated papers) but was a deliberate choice to avoid
  propagating an unverified citation into a document other researchers
  may cite from directly. Fixing this properly means going back to each
  adapter file and adding a verified citation to the docstring itself —
  out of scope for this configs/docs-only task (adapter files may not be
  modified per this task's brief).

---

## 6. ARIS skill usage

- **`system-profile`**: not run as a live per-adapter profiling pass in
  this design phase — doing so would require executing 21+ adapters
  across their pinned conda environments, which is compute-/time-heavy
  and outside a configs/docs-only task's scope. Instead, `cost_tier` and
  `latency_sec_observed` reuse the existing harness telemetry
  (`results/unified_harness/unified_harness_summary.json`) as a
  lower-fidelity but zero-additional-cost proxy. Recommended next step:
  run `system-profile` per `paper_core` adapter once the 3 remediation
  flags (§3.4) are cleared, to get real metered latency/compute
  distributions rather than single-run snapshots.
- **`experiment-audit`**: run against this report and the registry.
  Codex MCP (the skill's external-reviewer backend) failed twice with the
  same network-layer error already logged for `EXPERIMENT_PROTOCOL.md`'s
  review (`stream disconnected ... error sending request for url
  https://chatgpt.com/backend-api/codex/responses`) — the skill's default
  fraud-pattern checklist (ground-truth provenance, score normalization,
  dead metric code) also doesn't literally apply to a design document with
  no evaluation metrics, so the audit prompt was adapted to the skill's
  stated spirit (adversarial, verify-everything, file:line evidence)
  before either attempt. Fell back to a self-critique — see
  `docs/research_reports/2026-07-19_adapter_registry_self_audit.md` for
  what it checked (traceability, internal consistency, set-nesting
  correctness, honesty of §0's disclosed fabrication incident) and found
  (4/4 PASS, 2 minor follow-ups noted, no FAIL/WARN).
- **`research-wiki`**: **not run.** This project's `research-wiki/`
  directory does not exist yet, and the skill's write path
  (`papers/<slug>.md`, `graph/edges.jsonl`, `index.md`, etc.) would create
  a new top-level directory outside this task's explicit scope
  (`configs/` and `docs/adapter_management/` only). Rather than silently
  expand scope to accommodate the skill, the three verified paper
  citations are left recorded here and in `adapter_registry.yaml`'s
  `paper` fields only. If/when `research-wiki/` is initialized under a
  task that authorizes it, `alphaforge` (AAAI 2025), `alphagen` (KDD 2023,
  arXiv:2306.12964), and `prediction_arena` (arXiv:2604.07355, with the
  non-official-code caveat from §3) are the three candidates to ingest
  first — this repo's own adapter docstrings are already the verified
  source, no new literature search needed for these three.

---

## 7. Summary table

| Tier | Count | File |
|---|---|---|
| `extended_all` | 26 | `configs/adapter_sets/extended_all.yaml` |
| `popular_full` | 25 | `configs/adapter_sets/popular_full.yaml` |
| `paper_core` | 21 | `configs/adapter_sets/paper_core.yaml` |

No adapter, `CONTRACT/`, `harness/`, or other Python code was written or
modified to produce this report or its companion YAML files.
