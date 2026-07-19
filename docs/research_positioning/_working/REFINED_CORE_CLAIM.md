# Refined Core Claim — ICAIF Positioning

Produced via a `research-refine`-adapted anchor→propose→Codex-review loop
(the installed `research-refine` skill's full workflow assumes a
training-recipe-level method proposal and writes to `refine-logs/` with
experiment-planning content — both out of scope for a literature-review/
positioning-only role per this project's CLAUDE.md. The skill's
anchor→propose→external-review→revise *methodology* was applied directly
via real `mcp__codex__codex` calls instead, disclosed per the project's
anti-fabrication rule, consistent with how the adversarial-review pass
adapted `kill-argument` for a non-LaTeX target.) Real call, thread
`019f7b5f-ead0-7da1-b251-42d2ea74597c`, `model_reasoning_effort: xhigh`,
`sandbox: read-only`.

## Problem Anchor

- **Bottom-line problem**: `ICAIF_POSITIONING_REPORT.md` §2's combined main
  line needed one primary scientific claim defensible independent of
  whether the fusion mechanism (vs. TrustTrade) or the routing mechanism
  (vs. FineFT) individually succeed — this was the sharpest unresolved gap
  from the adversarial review (`kill-argument` point P_1, critical) and a
  related objection (P_3, major: "scale is not a new scientific
  principle").
- **Must-solve bottleneck**: the prior attempt at this claim ("the best
  downstream response to [a reliability/contradiction signal] is itself an
  empirical, regime-dependent question") is a research *question*, not a
  falsifiable, pre-experiment-defensible *contribution*.
- **Non-goals**: not designing new adapters, schema fields, or
  infrastructure; not writing the fusion/routing experiment plan itself
  (out of this role's scope); not resolving whether fusion or routing
  ultimately wins.
- **Constraints**: must be measurable using only the existing 26 adapters'
  outputs under the existing shared schema, with no new trainable
  components and no infrastructure beyond what's already built.
- **Success condition**: a claim statement a paper could state in its
  abstract/intro and defend as demonstrated using only the diagnostic
  substrate (calibration, stability, contradiction, regime measurements),
  independent of the two decision-layer mechanisms' outcomes.

## Iteration history

**Round 1 (only round needed — reviewer returned READY, not REVISE)**:
proposed a candidate claim reframing the contribution from "which response
is best" (a question) to "cross-system structural contradiction, detected
purely from the shared schema, is a model-agnostic leading indicator of
degraded forecast/policy quality, falsifiable and measurable without
building fusion or routing at all" (a measurement claim with a named
null hypothesis). The reviewer confirmed this resolves both P_1 (the
contribution no longer depends on downstream mechanism success — it's "a
schema-derived diagnostic variable predicts degradation in model quality,"
analogous to calibration error or disagreement-metric contributions) and
P_3 (scale becomes a statistical-power/external-validity device, not the
claim itself — the reusable diagnostic, cross-system contradiction as a
model-agnostic reliability signal, is the actual contribution). The
reviewer also confirmed implementation simplicity: schema-level
contradiction rules + forward-return/policy-quality labels + confidence
controls + a standard incremental-information statistical test, no new
trainable model or policy required.

**One required tightening, incorporated into the final statement below**:
the reviewer flagged that the contradiction *definition* is the weak point
— e.g. `Action=BUY` co-occurring with `Risk=HIGH` is not inherently
contradictory (high-risk/high-return trades are coherent), and a Q2
sentiment/Q1 action mismatch can be rational (valuation, hedging, mean
reversion). **Fix**: pre-specify a small, economically-defensible
contradiction ontology *before* any measurement is run, separating true
logical/structural incompatibility (e.g., two systems taking literally
opposite directional positions on the same ticker/horizon; an adapter's
own stated action being inconsistent with its own stated logic under its
own documented decision rule) from mere disagreement in conviction
strength, risk appetite, or investment horizon (which is not contradiction
and must not be counted as such).

## Final refined claim

**Full statement**: Schema-level structural contradiction among
heterogeneous financial-AI systems — restricted to a small, pre-registered
ontology of logically incompatible field combinations (not mere
disagreement in risk appetite, conviction strength, or horizon) — is an
out-of-sample, model-agnostic leading indicator of degraded forecast and
policy quality, carrying incremental predictive information beyond each
system's own self-reported confidence. This is falsifiable (null: measured
contradiction rate carries no incremental information about forward
forecast/policy quality once each system's own confidence is controlled
for), measurable directly from the existing 26-adapter diagnostic
substrate without building or evaluating any fusion or routing mechanism,
and therefore survives independently of whether the downstream fusion
(vs. TrustTrade, arXiv 2603.22567) or routing (vs. FineFT, arXiv 2512.23773,
confirmed ACM SIGKDD) mechanisms individually outperform their baselines.
The 26-system, 6+-paradigm scale serves external validity — showing the
signal generalizes across paradigms rather than being an artifact of one —
not the claim itself.

**Sharpest one-sentence (abstract-ready) version, per the reviewer**: "We
show that schema-level structural contradiction among heterogeneous
financial-AI systems is an out-of-sample, model-agnostic leading indicator
of degraded forecast and policy quality, carrying incremental information
beyond self-reported confidence."

**Relationship to the decision-layer claims**: this measurement claim is
now the paper's load-bearing contribution; fusion, routing, and abstention
become three candidate *responses* to a signal whose validity is
established independently of any of them. If fusion or routing
underperforms, the paper still stands on this measurement result. If the
measurement itself is null (contradiction carries no incremental
information), that is a more basic and more informative failure than
either decision-layer mechanism underperforming, and should be treated as
a signal to rethink the whole submission, not just one section — this
sharpens (does not soften) the risk this project's positioning report
already carries in its Candidate-3-related risk-table entry.

**Not yet done, flagged for whoever writes the actual paper**: the
contradiction ontology itself must be pre-registered and written out
explicitly (a short, fixed list of logically-incompatible field
combinations, distinguished from compatible-but-disagreeing combinations)
before any measurement is run, per the reviewer's required tightening
above. This is a design task, not a literature-review task, and is out of
this role's scope to produce.
