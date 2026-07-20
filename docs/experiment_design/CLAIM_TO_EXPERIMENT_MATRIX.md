# Claim-to-Experiment Matrix

**Role**: pre-registration document. No experiment has been run — every
`Status` cell below is `NOT YET RUN`. This matrix exists so that, once
experiments execute, "what counts as evidence" and "what would falsify the
claim" are already fixed and cannot be adjusted after seeing results.

All hypothesis IDs (H1–H7), experiment-group IDs (L1.x/L2.x/X.x), the
contradiction ontology, and the operational definitions of `C` and `E` are
defined in `docs/experiment_design/EXPERIMENT_PROTOCOL.md` §2 — this file
does not redefine them, only maps them to evidence/falsification standards.

## Evidence-sufficiency cross-check (genuine `result-to-claim`-adapted Codex call)

`result-to-claim`'s literal trigger ("after experiments complete") is
unmet — no experiment has run. Its Codex-judgment methodology was applied
prospectively instead, via a real `mcp__codex__codex` call
(thread `019f7c80-2ff4-7251-ae1f-631a3c583f28`,
`model_reasoning_effort: high`, `sandbox: read-only`) asked a different,
legitimate question: *if this design executed exactly as specified and
produced results matching its own "expected evidence," would that evidence
actually be sufficient to support the claim as stated?* Three real findings
came back and are incorporated into the rows below (not into
`EXPERIMENT_PROTOCOL.md`, which is treated as frozen after this session's
adversarial-review pass — see `SESSION1_INTEGRATION_NOTES.md`):

1. **H1 wording guardrail**: even in the best case, the design supports
   "out-of-sample, incremental, predictive information" — it does **not**
   support causal language ("contradictions *cause* degraded quality").
   The H1 row below is written accordingly, and this constraint should be
   copied verbatim into any future paper draft's phrasing of H1.
2. **H6 has a real attribution gap**: shadow-policy outperformance alone
   does not prove the *Q1/Q3 information* (as opposed to the *borrowed
   Q2/Q4 risk module alone*) was the source of value. Required Evidence
   for H6 below now includes the additional donor-only / recipient-only /
   shuffled-Q1/Q3 / risk-module-only controls the reviewer specified — this
   is a real addition to L2.3's evaluation, not present in
   `EXPERIMENT_PROTOCOL.md`'s original L2.3 entry, and should be treated as
   a required extension to that experiment group's method.
3. **H4 status-claim guardrail**: a null/regime-invariant reliability
   result does **not** support "H4 is true" — it is an informative
   *descriptive* finding (per `EXPERIMENT_PROTOCOL.md`'s own tolerance for
   this outcome) but must not be reported as "H4 confirmed." The row below
   distinguishes "H4 supported" from "H4 null but reported."

---

## Matrix

| Claim | Primary/Secondary/Fallback | Required Experiment | Required Evidence | Falsification Condition | Status |
|---|---|---|---|---|---|
| **H1** — schema-level structural contradiction (§2.2 ontology, **binary `C` only** — see `EXPERIMENT_PROTOCOL.md` §2.2's post-adversarial-review tightening) is an out-of-sample, model-agnostic **incremental predictive signal** (not a causal claim — see guardrail above), independent of generic cross-adapter disagreement, for degraded forecast/policy quality, beyond self-reported confidence | **Primary** | L1.3 | **Revised after `EXPERIMENT_PROTOCOL.md` §8's adversarial review (FAIL on the original design; fixes applied but not yet re-adjudicated by a fresh reviewer — treat this row as provisional until that re-check happens)**: a **pooled** nested-model test (adapter-pair and regime/horizon as fixed/random effects, §2.3.2) — confidence-only vs. confidence+`C`, with `C`'s coefficient required to remain significant after controlling for generic disagreement magnitude, a missingness/coverage indicator, and adapter-pair fixed effects (§2.3.1) — significant at the pilot-stage-computed power-analysis threshold (§2.4); block-bootstrap CI excludes 0; leave-one-adapter-out AND leave-one-ticker-out robust; minimum coverage met (a majority of Session 1's 6+ catalogued paradigms plus a pilot-computed sample-size floor, per §2.4.1's simplified, pilot-stage-computed rule — not a hand-picked count); per-stratum BH-FDR-corrected breakdown reported as secondary/exploratory only, never substituted for the pooled result | Pooled H0 not rejected, OR the effect disappears once generic-disagreement/missingness/adapter-pair controls are added (i.e. H1 is really just "any disagreement predicts errors"), OR the pilot-computed minimum coverage (§2.4.1) is not met and no honestly-narrowed-scope alternative claim is substituted, OR leave-one-out shows the pooled effect is carried by a single adapter/ticker | NOT YET RUN |
| H2 — reliability-/contradiction-weighted fusion beats naive aggregation AND TrustTrade-style AND ContestTrade-style baselines | Secondary | L2.1 | L2.1 beats majority vote, equal-weight, self-reported-confidence weighting, TrustTrade-style agreement weighting, and ContestTrade-style outcome-utility weighting on the Controlled Scientific Track's held-out test, on at least directional-accuracy or risk-adjusted portfolio metrics; the "correct lone dissenter" case-study slice shows the mechanism divergence concretely | L2.1 does not beat the TrustTrade-style and/or ContestTrade-style baseline on the primary metric | NOT YET RUN |
| H3 — contradiction-aware intervention lowers downside risk vs. always-fuse/random-intervention, independent of return | Secondary | L2.4 | Intervention beats no-intervention, random intervention, fixed-cash-buffer, AND the entropy/dispersion-rule baseline specifically on drawdown/tail-risk metrics (not just vs. weak baselines) | Intervention performs no better than the generic entropy/dispersion baseline on drawdown/tail-risk | NOT YET RUN |
| H4 — reliability is regime- and horizon-dependent | Secondary | L1.4 | A regime-by-metric interaction test is significant for ≥1 reliability metric, with rank stability of adapters differing meaningfully across regimes | **Guardrail**: a non-significant interaction test does **not** falsify the project — it is reported as "H4 null, regime-invariant reliability observed" (an accepted, pre-registered descriptive outcome per Fallback row below), distinct from "H4 supported." Only a significant-but-uninterpretable or non-reproducible result counts as a genuine failure here | NOT YET RUN |
| H5 — Layer 1 diagnostic features add incremental decision value beyond raw Q1–Q4 alone | Secondary | Cross-cutting X.2 feeding L2.1/L2.2 | The 3-point ablation (raw-only vs. raw+Layer1-minus-contradiction vs. raw+full-Layer1, per `EXPERIMENT_PROTOCOL.md` §6's ablation-planner-adapted revision) shows a monotonic or at-least-directional improvement from raw-only to raw+full-Layer1 on L2.1/L2.2's primary metric | raw+Layer1 performs no better than raw-only on any primary metric | NOT YET RUN |
| H6 — shadow Q4 policies convert Q4-weak systems' Q1/Q3 information into competitive portfolio value | Secondary | L2.3 | **Extended per the Codex cross-check above**: shadow policy beats both source systems' native policies risk-adjusted, **and** an attribution control set (donor-Q1/Q3-only policy, recipient-native-policy-only, shuffled-Q1/Q3-placebo, risk-module-only-with-neutral-selection) confirms the gain traces to the *combination*, not to the risk module alone; "Q4-weak" status for candidate donor systems must be defined ex ante (e.g. via L1.5's audit) before pairs are chosen, not post-hoc | Shadow policy gain is statistically indistinguishable from the risk-module-only control (i.e. the donor's Q1/Q3 information contributed nothing) | NOT YET RUN |
| H7 — reliability-aware routing beats one-size-fits-all fusion under regime/horizon conditioning, incl. a FineFT-style baseline | Secondary | L2.2 vs. L2.1 | L2.2 beats the full baseline ladder (random, static-global-best, round-robin, regime-blind learned, recent-performance/L2.5, FineFT-style VAE-routing-retrained) on L1.5's performance+risk metrics, and beats L2.1 head-to-head under the same track | L2.2 does not clear the FineFT-style baseline, or performs no better than L2.5 (rolling-performance selector) alone | NOT YET RUN |
| **Fallback (a)**: fusion/routing fail on raw return but H1 holds | Fallback | L1.3 (H1) independent of L2.1/L2.2 outcome | H1's own evidence bar (row 1) is met on its own | H1 itself also fails — no fallback available in this branch, see Fallback (e)/(f) framing instead | NOT YET RUN |
| **Fallback (b)**: only downside-risk reduction (H3) holds, not return improvement | Fallback | L2.4 (H3) | H3's evidence bar is met even though H2/H7 are not | H3 also fails — genuinely no positive decision-layer result; report as a negative decision-layer finding, not disguised as a risk-management contribution | NOT YET RUN |
| **Fallback (c)**: H1 holds only in some regimes | Fallback | L1.3 + L1.4 | H1's row-1 bar is met in ≥1 regime stratum but not universally (this is explicitly **already** H1's own acceptance criterion, not a downgrade — listed here only for completeness) | N/A — this is not a separate falsification path, it is H1's designed tolerance | NOT YET RUN |
| **Fallback (d)**: calibration (L1.2) poor project-wide but contradiction (L1.3) still diagnostic | Fallback | L1.2 + L1.3 | **Per Codex cross-check**: report requires showing contradiction adds incremental value *despite* poor calibration (i.e. H1's row-1 bar is independently met even when L1.2's calibration metrics are uniformly weak) — a bare assertion that "they are different axes" without this joint result is not sufficient to report as a finding | Contradiction's incremental value (H1) also fails when calibration is poor — then this is not a usable fallback, only a plain negative result | NOT YET RUN |
| **Fallback (e)**: eligible (TIER-1) adapter subset smaller than 26 | Fallback | Applies to all groups | Every claim is explicitly rescoped to "N adapters, M paradigms actually used" (`ADAPTER_REGISTRY_REQUIREMENTS.md` eligibility gate) | N/A — this is a scoping rule, not itself falsifiable; the failure mode it prevents is silently overclaiming the full 26 | NOT YET RUN |
| **Fallback (f)**: Q4 projects not fully comparable under the Controlled Scientific Track | Fallback | L1.5, L2.2, L2.3 | Non-comparable adapter pairs are excluded from controlled comparison and reported only on the Native Capability Track with an explicit non-comparability caveat | N/A — a data-handling rule, not itself falsifiable | NOT YET RUN |

---

## Notes on rows deliberately left without a "Falsification Condition" (the three N/A rows)

Fallback (c), (e), and (f) are **scoping/handling rules**, not empirical
claims — they describe what to *do* under a given condition, not a
proposition that could itself be true or false. Giving them a fabricated
falsification condition would misrepresent them as claims; they are marked
`N/A` deliberately rather than populated with an invented condition, per
`CLAUDE.md`'s no-fabrication rule.
