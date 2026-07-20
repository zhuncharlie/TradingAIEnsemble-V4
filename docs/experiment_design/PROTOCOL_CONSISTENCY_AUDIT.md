# Protocol Consistency Audit

**Role**: Session 3 (pre-pilot readiness), Task B. Audits the 10 Session 2
deliverables for the 8 named conflict classes (B1–B8) plus any additional
conflicts surfaced during the fresh blind H1 review (Task A, see
`H1_FRESH_REVIEW.md`). No experiment code was written, no experiment was
run, no adapter/schema/harness file was touched.

**Skills used**: `experiment-audit`'s adversarial checklist methodology
(applied prospectively — see `RISK_AND_FAILURE_PLAN.md` §1's existing
Session 2 pass, extended here to consistency rather than integrity
specifically), `result-to-claim`'s evidence-sufficiency framing (used to
judge whether each fix actually closes the gap it targets, not just
changes wording), `research-refine`'s "smallest adequate fix" discipline
(applied throughout — every fix below is the minimal edit that removes the
contradiction, not a rewrite). The fresh blind Codex review that surfaced
most of B1/B2/B3/B6's concrete instances is documented in full in
`H1_FRESH_REVIEW.md` (thread `019f7e01-0fe6-7092-ad68-1b1f1f7e3e94`) and is
not re-quoted here in full — this file focuses on the fix ledger.

---

## Fix ledger

| Issue | Files affected | Old conflict | Resolution | Files changed |
|---|---|---|---|---|
| **B1 — Calibration vs. validation interval** | `DATA_SPLIT_PROTOCOL.md`, `RISK_AND_FAILURE_PLAN.md` | `DATA_SPLIT_PROTOCOL.md`'s own table (§1) correctly assigned calibrator/threshold fitting to the **Calibration** interval, but the very next paragraph ("Hard rule") said "calibrator fit... happen on validation only" — a direct self-contradiction. `RISK_AND_FAILURE_PLAN.md` §2 repeated the same "fitting happens on validation only" error. Additionally, the relationship between the *process* "pilot stage" (`EXPERIMENT_DEPENDENCY_MAP.md`) and the *data* intervals (this file) was never specified, which is what made `EXPERIMENT_PROTOCOL.md` §2.4's "threshold fixed at the pilot stage, before validation begins" read as if it conflicted with `DATA_SPLIT_PROTOCOL.md`'s "threshold fixed... before test" (inside the Validation row) | Rewrote the Hard-rule paragraph to state the single correct rule (calibrators/thresholds → Calibration interval; Layer 2 method params → Validation interval; nothing → Test) matching the table. Added new §1.1 explicitly reconciling "pilot stage" (a small-scale rehearsal on a *subset of Calibration-interval data*, never Validation/Test) with the four data intervals. Reworded the Validation row to say H1's threshold is *applied*, not *fixed*, there. Fixed the matching sentence in `RISK_AND_FAILURE_PLAN.md` §2 | `DATA_SPLIT_PROTOCOL.md` (§1 table row, Hard-rule paragraph, new §1.1), `RISK_AND_FAILURE_PLAN.md` (§2 leakage table) |
| **B2 — H1 pooled test vs. per-stratum acceptance** | `EXPERIMENT_PROTOCOL.md`, `CLAIM_TO_EXPERIMENT_MATRIX.md` | §2.3.2 already said the pooled test is the sole primary acceptance criterion, but §2.4's "Robustness requirement for H1 to be reported as supported" bullet still said the effect must "survive FDR correction in at least one horizon and one regime stratum" — an independent, contradictory acceptance path. `CLAIM_TO_EXPERIMENT_MATRIX.md`'s Fallback (c) row explicitly called single-stratum significance "already H1's own acceptance criterion." Independently surfaced by the fresh blind review (question 4) as the single most damaging inconsistency | Rewrote §2.4's bullet into one unambiguous sentence: "H1 is supported if, and only if, the pooled test... is significant"; per-stratum results reclassified as robustness/interpretability detail on an *already-significant* pooled result, never a substitute. Rewrote §2.6's fallback-table row and `CLAIM_TO_EXPERIMENT_MATRIX.md`'s Fallback (c) row to match, and added a new explicit non-fallback row for "pooled null, one stratum significant uncorrected" (a null result, not a pass) | `EXPERIMENT_PROTOCOL.md` (§2.4, §2.6), `CLAIM_TO_EXPERIMENT_MATRIX.md` (H1 row, Fallback (c) row) |
| **B3 — Adapter-pair effect specified twice, inconsistently** | `EXPERIMENT_PROTOCOL.md` | §2.3.1 (added in the Session 2 adversarial-review pass) already specified one adapter-pair term defaulting to random effect/partial pooling. §2.3.2 (the pooled-test description) still said "adapter-pair... as fixed or random effects" without stating the default, reading as a second, independently-decided term | Reworded §2.3.2 to explicitly point back to §2.3.1's single term and its random-effect-by-default rule, leaving only regime/horizon's fixed-vs-random choice open to the pilot stage | `EXPERIMENT_PROTOCOL.md` (§2.3.2) |
| **B4 — H6 attribution controls not synced to main protocol** | `EXPERIMENT_PROTOCOL.md` | `CLAIM_TO_EXPERIMENT_MATRIX.md`'s H6 row already required four attribution controls (donor-only, recipient-only, shuffled placebo, risk-module-only) plus a hard "cannot claim Q1/Q3 value without beating risk-module-only" rule (added by a Session 2 sub-pass), but `EXPERIMENT_PROTOCOL.md` §6's L2.3 (Shadow Q4) section — the main protocol's own description of the same experiment group — never mentioned them | Added the four controls and the hard attribution rule directly into L2.3's Baseline and Expected-evidence fields, so the main protocol document is self-sufficient and does not silently depend on a reader also checking the claim matrix | `EXPERIMENT_PROTOCOL.md` (§6, L2.3) |
| **B5 — "26 adapters" vs. evaluated N** | `BASELINE_DESIGN.md` | One baseline-fairness note described a competitor baseline as implemented "against the same 26-adapter/6+-paradigm pool as L2.1" — using the aspirational catalog count in a claim-adjacent (fairness-of-comparison) sentence, contrary to the rule already stated correctly elsewhere (`RISK_AND_FAILURE_PLAN.md` §12, `EXPERIMENT_PROTOCOL.md` §2.6) | Reworded to "the same TIER-1-eligible adapter pool (N adapters, M paradigms, per `ADAPTER_REGISTRY_REQUIREMENTS.md`)" | `BASELINE_DESIGN.md` (§1) |
| **B6 — Practical-significance/power procedure** | `EXPERIMENT_PROTOCOL.md` | Already fixed in the Session 2 adversarial-review pass (§2.4): 0.02 incremental AUC/pseudo-R² is explicitly labeled "a placeholder judgment call, not a data-driven one"; may be revised **at most once**, only if the eligible sample is under-powered, only at the pilot stage, recorded before any validation-stage result is seen, never adjusted based on validation or test results (the "final test touched once" rule already forecloses test-based adjustment). Re-verified this session — no further edit needed, already meets all 5 of Task B6's required disclosures | Re-verified only, no change | none |
| **B7 — Contradiction threshold** | `EXPERIMENT_PROTOCOL.md` | Already fixed in the Session 2 adversarial-review pass (§2.2): the adapter-relative risk threshold is a fixed 90th percentile, computed once at the pilot stage on pilot-window data, then locked for validation and test. This session additionally closed two related precision gaps the fresh blind review found (§2.2's "equivalent open-vocabulary risk/volatility dimension" and "machine-checkable rule exists" phrases) — see the new row below | Re-verified core threshold rule (no change); added deterministic whitelist/parser-template fixes for the two adjacent vague phrases (see next row) | `EXPERIMENT_PROTOCOL.md` (§2.2, new sub-list) |
| **B7-adjacent — Ontology cell precision** (surfaced by the fresh blind review, question 2/8, not separately numbered in the task brief but load-bearing for B7's spirit) | `EXPERIMENT_PROTOCOL.md` | Three ontology-table cells left implementer discretion: "or equivalent open-vocabulary risk/volatility dimension" (no fixed list), "no offsetting `explanation`" (required semantic judgment of free text, which a neighboring row explicitly forbids as a contradiction-detection input — internally inconsistent), "machine-checkable rule exists" (no definition of what counts) | Fixed a closed 5-item dimension-name whitelist (exact-match only); removed the free-text-offsetting-explanation criterion entirely (row is now purely structural, consistent with the neighboring row's own rule); defined "machine-checkable" as matching one of a fixed set of parseable rule templates, registered at the pilot stage | `EXPERIMENT_PROTOCOL.md` (§2.2) |
| **B8 — Final test access consistency** | `EXPERIMENT_PROTOCOL.md`, `EXPERIMENT_DEPENDENCY_MAP.md` | Four separate places (`EXPERIMENT_PROTOCOL.md` §2.3.1/§2.3/L2.1/L2.2's sample-construction bullets, `EXPERIMENT_DEPENDENCY_MAP.md`'s dependency-chain diagram and stage table) cited a nonexistent "§9" of `EXPERIMENT_PROTOCOL.md` as the source of the "touched once" rule — a stale cross-reference from an earlier draft structure, not a substantive disagreement, but exactly the kind of drift B8 is meant to catch | Replaced every phantom "§9" citation with the correct pointer (`DATA_SPLIT_PROTOCOL.md` §1's "Untouched final test" row, the actual source of the rule); the underlying rule itself (test touched once, single evaluation pass, no re-tuning) was never actually inconsistent in substance, only in citation | `EXPERIMENT_PROTOCOL.md` (4 locations), `EXPERIMENT_DEPENDENCY_MAP.md` (3 locations) |

---

## Additional issue surfaced by the fresh blind review, not in the B1–B8 list, fixed anyway

- **Primary outcome family for `E` was unlocked**: `EXPERIMENT_PROTOCOL.md`
  §2.3 defined both a Q1/Q3 sign-mismatch variant and a Q4 policy-return
  variant of `E` without declaring which one H1's pooled test actually
  uses — a genuine gap (mixing outcome types with different units and
  different eligible samples into one pooled coefficient would itself be a
  design flaw). **Fixed**: Q1/Q3 sign-mismatch is now the sole primary `E`
  for H1's pooled test (computable for every TIER-1 adapter regardless of
  Q4 capability); the Q4 variant is a secondary robustness check on the
  Q4-capable subset only, never pooled into the same headline coefficient.
- **HOLD/NEUTRAL decisions were unhandled in `E`**: fixed — decisions with
  no genuine directional call are excluded from the Q1/Q3 `E` computation
  entirely (not scored either way), symmetric with §2.2's existing
  HOLD-is-not-an-opposite-of-BUY exclusion.
- **Unit of analysis / pseudo-replication**: the ontology and the pooled
  test previously left ambiguous whether the unit was one row per
  adapter-pair or one row per market-outcome tuple — the former risks
  inflating effective sample size when multiple correlated pairs share the
  same underlying outcome. **Fixed**: the primary unit is now explicitly
  one row per `(ticker, as_of, horizon)` tuple, with `C` and the
  disagreement covariate aggregated across all eligible adapters/pairs at
  that tuple; pair-level detail is reclassified as secondary, tuple-
  conditional analysis.
- **Generic disagreement-magnitude covariate was underspecified**: "e.g.
  entropy/dispersion" gave no single computable formula. **Fixed**: defined
  as the normalized Shannon entropy (base-2, divided by log2(3)) of the
  {-1, 0, +1}-mapped directional-vote distribution across eligible
  adapters at a tuple — one formula, reused identically by L2.4's baseline.

## Issues considered and explicitly NOT fixed (with reason)

- The fresh blind review's overall verdict is **REVISE**, not **PASS** —
  per the task brief's explicit two-round limit, this fix pass is the one
  permitted "minimal necessary revision." A second, final fresh-reviewer
  round is documented in `H1_FRESH_REVIEW.md`; if that round still does not
  return PASS, the honest verdict is carried into `GO_NO_GO_FOR_PILOT.md`
  as `NO-GO FOR CLAIM-BEARING PILOT` per the task brief's explicit
  instruction not to iterate indefinitely toward a PASS.
- No fix in this pass **silently changed H1's core definition** (the
  five-class ontology, the binary-`C`-as-primary-exposure rule, the
  pooled-test-as-sole-acceptance-path rule) — every change either removed
  a genuine internal contradiction, replaced a vague criterion with a
  deterministic one, or added a control/robustness check the fresh review
  found missing. This is stated explicitly because the task brief
  separately prohibits "为了通过 review 静默改变 H1 的核心定义" (silently
  changing H1's core definition just to pass review) — none of the edits
  above change what H1 *claims*; they change how precisely and
  consistently it is *specified*.
