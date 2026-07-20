# Adversarial Review — Experiment Protocol (Session 2)

Produced via genuine `mcp__codex__codex` calls (not simulated), following
the `kill-argument` attack→adjudicate pattern, adapted for a markdown
experiment-protocol target rather than a LaTeX theorem-paper (the skill's
literal file-discovery machinery targets `.tex`/`.bib`/compiled PDF; the
attack/defense methodology was applied directly instead, disclosed here
per this project's anti-fabrication rule — the same adaptation pattern
Session 1 used).

Target: `docs/experiment_design/EXPERIMENT_PROTOCOL.md` and its six
sibling deliverables.

---

## Attack (Thread 1, fresh, `019f7c86-3730-7823-bb0a-5a8a2a367376`)

> Reject. The protocol's primary contribution is not genuinely
> pre-registered or falsifiable. H1 is framed as a clean incremental-
> information test in `EXPERIMENT_PROTOCOL.md` §2.1, but the actual
> acceptance surface is left movable: contradiction thresholds are
> adapter-relative and fit later (`DATA_SPLIT_PROTOCOL.md` §1), severity
> can be "optionally scaled" (`EXPERIMENT_PROTOCOL.md` §2.2), the
> practical effect-size threshold is deferred to pilot/validation
> (`EXPERIMENT_PROTOCOL.md` §2.4; `EXPERIMENT_DEPENDENCY_MAP.md` §6), and
> H1 support requires significance in only "at least one horizon and one
> regime stratum with adequate power" (`EXPERIMENT_PROTOCOL.md` §2.4;
> `CLAIM_TO_EXPERIMENT_MATRIX.md` H1). "Adequate power" is never
> numerically defined, while adapter eligibility, universe coverage,
> horizon availability, and failed strata can all be narrowed through
> later manifests and exclusions (`DATA_SPLIT_PROTOCOL.md` §§4-5;
> `RISK_AND_FAILURE_PLAN.md` §1C). Thus the design can execute "as
> specified" yet still let investigators discover which adapters,
> universes, regimes, horizons, thresholds, and severity encodings survive
> contact with data before the final claim is made.
>
> This is not merely a leakage concern; it changes the estimand. The
> final paper could report a corrected positive result in one surviving
> stratum and call H1 supported, while the reader cannot distinguish a
> real, model-agnostic contradiction signal from validation-stage ontology
> selection plus scope attrition. That is not a defensible scientific
> contribution.

## Adjudication (Thread 2, fresh, `019f7c88-0e7b-7f40-809b-2b7a92753ce4`)

| Point | Attack claim | Verdict | Severity if unresolved |
|---|---|---|---|
| P1 | Contradiction thresholds/severity remain movable post-hoc | partially_answered | major |
| P2 | Practical significance / power not numerically pre-registered | partially_answered | critical |
| P3 | "≥1 significant stratum" acceptance invites stratum cherry-picking | partially_answered | major |
| P4 | Adapter/universe/horizon/failure attrition can narrow claim-bearing scope after the fact | partially_answered | major |
| P5 | H1 not shown distinguishable from generic cross-adapter disagreement | **still_unresolved** | **critical** |

**Counts**: 0 `answered_by_current_text`, 4 `partially_answered`, 1
`still_unresolved` (critical).

**Computed verdict** (per the skill's mapping table — any
`still_unresolved` at critical severity → FAIL, regardless of the other
counts): **FAIL**, `reason_code: unresolved_critical`.

**Net assessment (verbatim from the adjudicator)**: "As currently written,
this protocol would likely not survive a hostile pre-registration review
on the primary H1 claim. It has serious anti-leakage machinery: final-test
isolation, embargoes, FDR correction, manifesting, leave-one robustness,
and scope-language discipline. But the central acceptance surface is still
not fully frozen... The rejection memo is overstated in places, but its
core concern stands."

**Top action items (verbatim)**:
1. Freeze H1's primary estimand and acceptance rule numerically: effect
   threshold, power, minimum sample/events, and whether global or
   stratum-specific support is primary.
2. Lock claim-bearing scope before pilot: adapter roster, universe,
   horizons, minimum coverage, and exclusion handling.
3. Make binary `C` the primary exposure and add H1-specific controls
   against generic disagreement, missingness, adapter-pair effects, and
   ontology-class selection.

---

## Fixes applied (all three action items, directly in `EXPERIMENT_PROTOCOL.md`)

1. **§2.3.2** (new): primary acceptance criterion changed from "significant
   in ≥1 stratum" to a **pooled** whole-deployment test (adapter-pair and
   regime/horizon as fixed/random effects); per-stratum BH-FDR results
   demoted to secondary/exploratory, never substitutable for the pooled
   result.
2. **§2.4** (revised): the practical-significance threshold is no longer a
   bare deferral — a concrete power-analysis *procedure* is pre-registered
   (pilot-stage variance/incidence estimate → 80%-power target at a
   provisional 0.02 incremental-AUC/pseudo-R² threshold → sample-size
   check against the actual TIER-1-eligible roster → at most one recorded
   revision, before validation, never after).
3. **§2.4.1** (new): a minimum-coverage floor (≥4 paradigms, ≥8 adapters,
   ≥2 horizons, ≥2 regime strata) for H1 to remain the paper's primary,
   full-scope claim; an explicit honestly-narrowed-scope fallback if not
   met.
4. **§2.2** (revised): binary `C` is now H1's sole primary exposure;
   severity scoring demoted to a secondary, fixed-formula-only measure
   (no more "optionally scaled"); the adapter-relative risk threshold is
   pinned to a fixed 90th-percentile rule, computed once at the pilot
   stage and then frozen.
5. **§2.3.1** (new): H1's own nested model must now control for generic
   cross-adapter disagreement magnitude, a missingness/coverage indicator,
   and adapter-pair fixed effects, plus report a per-ontology-class
   breakdown — directly closing P5 (the critical, still-unresolved point).

`CLAIM_TO_EXPERIMENT_MATRIX.md`'s H1 row was updated to match.

## What this session does not claim

These fixes were authored by the same session that received the critique —
per `kill-argument`'s own rule that the verdict must never be computed by
a self-grading defender, **this is not a confirmed PASS**. It should be
read as: *FAIL identified honestly, concrete fixes applied, re-adjudication
by a fresh reviewer thread not yet performed*. This is flagged as an open
item in the final terminal summary rather than silently upgraded.
