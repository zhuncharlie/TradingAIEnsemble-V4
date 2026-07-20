# GO / NO-GO for Pilot

**Role**: Session 3 (pre-pilot readiness), Task F — final synthesis of
Tasks A-E. This document makes no new claims; every judgment below cites a
specific finding already recorded in `H1_FRESH_REVIEW.md`,
`PROTOCOL_CONSISTENCY_AUDIT.md`, `docs/adapter_management/
REGISTRY_GAP_ANALYSIS.md`/`ADAPTER_REGISTRY_MIGRATION_REPORT.md`, or
`PILOT_PROTOCOL_DRAFT.md`.

---

## Ready to write experiment code?

### `CONDITIONAL`

- **YES, specifically, for**: the H1 pre-pilot's own minimal dry-run
  pipeline as specified in `PILOT_PROTOCOL_DRAFT.md` (alignment table
  construction, 1d/5d label computation, minimal calibration features,
  binary `C` per the current ontology draft, the no-random-effect pooled
  model, block bootstrap/leave-one-out mechanics) — this pipeline is fully
  specified, uses only already-existing adapters via
  `CONTRACT/adapter_runner.py` (no retraining, no adapter modification),
  and its own explicit purpose (§12 of `PILOT_PROTOCOL_DRAFT.md`) is to
  surface implementation ambiguities empirically, which requires code to
  exist. Writing this specific, scoped code is itself the recommended
  next step — **contingent on the human approval `PILOT_PROTOCOL_DRAFT.md`
  and `h1_pre_pilot_draft.yaml` both explicitly require before any of it
  runs**.
- **NOT YET, for**: code implementing H1's *full, claim-bearing* pooled
  statistical model (the version with a genuine adapter-pair random-effect
  structure, full power-analysis procedure, and minimum-coverage gating at
  real scale) — `H1_FRESH_REVIEW.md` Round 2 found this specification
  genuinely incomplete (confidence aggregation and the adapter-pair effect
  term's tuple-level representation are not fully defined), and writing
  code against an incomplete spec risks encoding an undocumented judgment
  call as if it were a decided design choice. The pre-pilot dry run is
  explicitly meant to inform this gap before it is closed, not to be
  built in parallel with a guess at the answer.
- **NOT YET, for**: any Layer 2 method code (L2.1-L2.6) — none of these
  depend only on already-resolved specification; several (L2.2 routing,
  L2.6 meta-fusion) are explicitly lower-priority than L1/H1 per
  `EXPERIMENT_DEPENDENCY_MAP.md`'s own sequencing and have not been
  through any adversarial-review-and-fix cycle this session (only H1 has).

## Ready to run H1 pre-pilot?

### `CONDITIONAL` — protocol-ready, pending human approval

The protocol itself (`PILOT_PROTOCOL_DRAFT.md`,
`configs/experiments/h1_pre_pilot_draft.yaml`) is fully specified: pilot
adapters and selection basis, ticker/universe (with the `finrl_x`
alignment risk disclosed, not hidden), calibration/embargo/validation
windows, horizons, data source, ontology version tag, generic-disagreement
formula, missingness control, pooled model specification (deliberately
simplified, with the simplification's reasoning stated), block-bootstrap
length, leave-one-out checks, expected sample size (explicitly
non-power-analyzed), cost/timeout/failure handling, and output manifest
schema. **Every field the task brief required is present and traceable to
either existing evidence or an explicitly-disclosed simplification —
nothing is silently assumed.**

This is marked `CONDITIONAL`, not `YES`, for one reason only: per the task
brief's own explicit instruction ("这只是draft。未经人工批准不得运行"), no
draft — however complete — authorizes its own execution. **A human must
approve `h1_pre_pilot_draft.yaml` (currently `status: DRAFT_NOT_APPROVED`)
before any adapter call under this config is made.**

## Ready to run full Layer 1 pilot?

### `NO`

Four concrete blockers, each already documented elsewhere in this
deliverable set:

1. **H1's own specification is not frozen.** `H1_FRESH_REVIEW.md`: two
   independent fresh reviews both returned `REVISE`, and the task brief's
   own two-round limit means no third round was run this session. Running
   a full-scale Layer 1 pilot before H1's tuple-level model gap is closed
   risks generating a large volume of results against a specification that
   will need to change.
2. **The H1 pre-pilot dry run (above) has not actually executed yet** —
   only its protocol is drafted. `EXPERIMENT_DEPENDENCY_MAP.md`'s own
   stage sequence (pilot → screening → full validation → final test)
   places a completed pilot stage strictly before screening (= "full
   Layer 1 pilot" in this question's terms); skipping straight to
   screening would violate the sequencing this project's own protocol
   already committed to.
3. **Session 4's Q4 rolling execution protocol does not exist yet** —
   `Q4_EXPERIMENT_REQUIREMENTS.md` is a *handoff specification* to Session
   4, not an implementation. `L1.5` (Q4 Performance and Risk Audit)
   explicitly depends on it (`EXPERIMENT_PROTOCOL.md` §5), and several
   `controlled_scientific_core` adapters' Q4 capability (e.g. `finrl_x`,
   `trademaster`, `skfolio`) can only be evaluated at rolling, multi-step
   scale, not the single-shot calls the existing harness has verified so
   far.
4. **Several `controlled_scientific_core`/`popular_1000_plus` adapters
   need remediation before they can contribute real data at pilot scale**:
   `finagent`/`tradingagents` (280s timeout), `fingpt` (conda env error) —
   all three flagged `remediation_status: KNOWN_FIX_AVAILABLE` in the
   upgraded registry, i.e. plausibly fixable but not yet fixed;
   `finmem`/`pgportfolio` (`remediation_status: BLOCKED_EXTERNAL` —
   credential/dead-API issues outside this session's control to resolve).
   None of `controlled_scientific_core`'s own 8 members are currently
   blocked (all `live_status: PASSED`), so this specific blocker mainly
   affects `popular_1000_plus`-scale diagnostic work, not the narrower
   `controlled_scientific_core` set — but it does affect completeness of
   any `diagnostic_all`/`popular_1000_plus`-scope Layer 1 run.

**Recommended path to `YES`** (not a commitment, an observation): (a) get
human approval and run the H1 pre-pilot dry run; (b) use its findings
(§12 of `PILOT_PROTOCOL_DRAFT.md`) to close the tuple-level model-
specification gap in `EXPERIMENT_PROTOCOL.md` §2.3.1/§2.3.2; (c) run a
third, genuinely fresh H1 review round *after* that revision (not
constrained by this session's two-round limit, since it would be a new
review cycle, not a continuation of this one); (d) in parallel, remediate
the three `KNOWN_FIX_AVAILABLE` adapters and confirm Session 4's rolling
protocol is ready for at least `controlled_scientific_core`'s Q4-bearing
members.

## Ready to access final test?

### `NO`

Categorical, per the task brief's explicit instruction, and not close to
being satisfied by anything in this session's scope: **zero** of Session
2's `EXPERIMENT_DEPENDENCY_MAP.md` §3's three human checkpoints have been
reached (Checkpoint 1 requires an actual L1.3/H1 result to review — none
exists yet, only a design; Checkpoint 2 requires actual L2.1/L2.2 results;
Checkpoint 3 requires all of the above plus explicit human sign-off). No
Layer 1 diagnostic has been run even once. This session's own scope
explicitly excludes running anything (§1 of the task brief: "本阶段不得...
运行pilot，不得读取最终测试集") — this answer will remain `NO` until
several full stages of actual experimentation (not just design) have
completed and a human has explicitly granted each checkpoint in sequence.

---

## Basis for these four judgments (cross-reference)

| Judgment | Primary evidence |
|---|---|
| Experiment code: CONDITIONAL | `H1_FRESH_REVIEW.md` (tuple-level gap), `PILOT_PROTOCOL_DRAFT.md` §8 (deliberate simplification for the dry run specifically) |
| H1 pre-pilot: CONDITIONAL (protocol-ready, approval-pending) | `PILOT_PROTOCOL_DRAFT.md` (full spec), `configs/experiments/h1_pre_pilot_draft.yaml` (`status: DRAFT_NOT_APPROVED`) |
| Full Layer 1 pilot: NO | `H1_FRESH_REVIEW.md` (REVISE ×2), `Q4_EXPERIMENT_REQUIREMENTS.md` (handoff only, not implemented), `configs/adapter_registry.yaml` (`remediation_status` fields for `finagent`/`tradingagents`/`fingpt`/`finmem`/`pgportfolio`) |
| Final test: NO | `EXPERIMENT_DEPENDENCY_MAP.md` §3 (zero of three checkpoints reached); this session's own explicit scope prohibition |

## What would need to be true for each `NO`/`CONDITIONAL` to become `YES`

- **Experiment code (full H1 model)** → the tuple-level model-specification
  gap closed, informed by the pre-pilot's actual results (not guessed).
- **H1 pre-pilot** → a human reads `PILOT_PROTOCOL_DRAFT.md` and
  `h1_pre_pilot_draft.yaml`, and explicitly sets `status: APPROVED` with
  `approved_by`/`approved_date` populated.
- **Full Layer 1 pilot** → the H1 pre-pilot has run, a third (fresh-cycle)
  H1 review has returned PASS or an explicitly human-accepted qualified
  REVISE, Session 4's Q4 rolling protocol exists and covers at least
  `controlled_scientific_core`'s Q4-bearing members, and the three
  `KNOWN_FIX_AVAILABLE` adapters are remediated (or their absence is
  explicitly accepted and scoped around).
- **Final test** → all three `EXPERIMENT_DEPENDENCY_MAP.md` checkpoints
  passed in sequence, informed by real (not merely designed) Layer 1 and
  Layer 2 results.
