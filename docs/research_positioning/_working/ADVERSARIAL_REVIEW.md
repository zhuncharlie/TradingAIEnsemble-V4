# Adversarial Review — ICAIF Positioning Report

Produced via genuine `mcp__codex__codex` calls (not simulated), following the
`kill-argument` attack→adjudicate pattern and a `research-review`-style
balanced technical pass. **Adaptation note**: the installed `kill-argument`
skill is built for LaTeX theorem-papers (`main.tex`, compiled PDF,
`\begin{theorem}` obligations) and would formally emit `NOT_APPLICABLE`
(`reason_code: not_theory_or_scope_paper`) against a markdown positioning
report with no theorems. The attack→defense *methodology* was applied
directly via two fresh, independent `mcp__codex__codex` calls (Step 2/Step 3
prompt structure, adapted target), rather than through the skill's literal
LaTeX-file-discovery machinery. This is disclosed per the project's
anti-fabrication rule, not presented as a verbatim skill run.

Target: `docs/research_positioning/ICAIF_POSITIONING_REPORT.md` and its
three sibling deliverables.

---

## Part 1 — Kill-argument (attack → adjudication)

**Attack thread**: `019f7b58-8f5b-7102-9218-6bd4133a447f`
**Adjudication thread**: `019f7b59-68f8-70b3-8ca3-9c234cbac969`
**Reasoning effort**: high (both threads; skill's `ultra` target unavailable
via this account/CLI, consistent with the model-availability constraints
already logged across the novelty-check dossiers).

### Attack memo (verbatim)

> Reject. The proposed combined-paper framing has no defensible core
> contribution; it is an aggregation of marginally novel diagnostics and
> decision heuristics whose viability is explicitly deferred to experiments
> not yet run. The proposal admits that all five sub-claims sit in a narrow
> 5-7/10 novelty band and that "every individual mechanism has a close
> single-paradigm or single-metric analog published in the last 6-12
> months." That is fatal for ICAIF positioning: the claimed novelty rests
> "entirely on the combination and scale," but scale here is only 26
> heterogeneous adapters behind a shared schema, not a new scientific
> principle.
>
> The most serious weakness is that both decision-layer claims are
> derivative of recent, highly relevant prior art. Reliability-weighted
> fusion is already in the "danger zone" relative to TrustTrade, arXiv
> 2603.22567, an LLM-only multi-agent consensus-weighting paper; even the
> novelty check gives it only 6/10 and requires a TrustTrade head-to-head
> plus "correct lone dissenter" ablation before submission. Routing and
> shadow Q4 policy construction fares only slightly better at 7/10 and is
> exposed to FineFT, arXiv 2512.23773, a published ACM SIGKDD self-trained
> RL ensemble with VAE-based routing. Worse, no large-scale results exist
> for this branch.
>
> This is not a paper framing; it is a speculative integration plan.
> Without completed baselines, the central claim is unsubstantiated,
> incremental, and vulnerable to immediate novelty collapse.

### Adjudication (per-point, verbatim)

**P_1 — No defensible core contribution.** Verdict: **partially_answered**
(critical if unresolved). Report §2 defines a coherent research question
(fuse/route/abstain given a measured reliability signal) but does not prove
this rises to a paper-level contribution independent of experimental
success. *Fix*: state one primary scientific claim that survives even if
fusion or routing individually underperforms.

**P_2 — Marginal novelty is fatal.** Verdict: **partially_answered**
(major). Report §4 already admits novelty is "real but genuinely marginal"
— honest disclosure, but doesn't argue why a marginal combination claim
clears ICAIF's bar. *Fix*: add an ICAIF-specific precedent argument for
accepted system-integration papers with marginal mechanism novelty but
strong empirical contribution.

**P_3 — Scale is not a new scientific principle.** Verdict:
**partially_answered** (major). Report §4 claims no prior work unifies
20+ systems into an auditable reliability schema, but concedes this is a
"combination-and-scale" argument — the attack stays live unless the
substrate enables a new measurement or falsifiable decision rule. *Fix*:
reframe the substrate around what new phenomenon/decision rule it enables,
not coverage size.

**P_4 — Fusion is derivative of TrustTrade.** Verdict:
**answered_by_current_text**. Report §2/§5 already call fusion "borderline
... in the danger zone" and make the TrustTrade baseline + lone-dissenter
ablation explicitly non-negotiable. Not overclaimed.

**P_5 — Routing is exposed to FineFT and lacks results.** Verdict:
**partially_answered** (critical). Report acknowledges the score, the
"not obviously preempted" verdict, and the missing baseline ladder, but
**does not name FineFT's specific mechanism delta inline** — the report
text provided to the adjudicator referenced the score/status but not a
direct FineFT differentiation paragraph. *Fix*: inline a direct FineFT
comparison (mechanism, empirical baseline, routing target, what result
establishes non-derivativeness) rather than relying on cross-reference to
`NOVELTY_AUDIT.md`.

**P_6 — Framing is speculative because viability is deferred.** Verdict:
**partially_answered** (critical). Report explicitly states the novelty
case "rests on argument, not results" — this is honest self-diagnosis but
supports the reviewer's concern more than it refutes it. *Fix*: separate
"submission-ready claim" from "experiment-contingent claim" explicitly,
demoting unvalidated branches to fallback/future-work status until results
exist.

**Summary**: 6 points; 1 `answered_by_current_text`, 5
`partially_answered` (3 at critical severity: P_1, P_5, P_6), 0
`still_unresolved`.

**Computed verdict (per the skill's mapping table, applied manually since
no `still_unresolved` points exist but ≥1 `partially_answered` is
critical)**: **WARN** — `reason_code: partial_critical_or_repeated_major`.

**Net assessment (verbatim from adjudicator)**: "The report would not
fully survive a senior ICAIF area chair reading the attack memo as a
defense of a submission-ready paper. It is candid and technically
disciplined, but mostly by validating the reviewer's central concern: the
novelty case is marginal, the decision-layer claims are experiment-
contingent, and the combined framing is not yet proven to be more than
integration. The TrustTrade risk is well handled as a known blocker. The
FineFT/routing issue and the 'scale is not science' objection need
sharper direct answers. As a positioning report, it is credible; as a
rebuttal to rejection, it is not yet sufficient."

---

## Part 2 — Research-review pass (balanced technical review)

**Thread**: `019f7b5a-829c-7ef0-8d3f-9a67332e3eee`

- **CRITICAL — Combined-paper framing may overload the contribution.**
  Fusion is "danger zone," routing has zero completed experiments, yet the
  main line still combines both. Fusion is Q1/Q3-centric (prediction
  reliability); routing/shadow-Q4 is execution-policy-centric (portfolio
  construction). Risk: the paper fractures across prediction reliability,
  portfolio construction, and execution unless all three (fuse/route/
  abstain) are evaluated under one genuinely shared decision protocol, not
  just a shared narrative frame.
- **MAJOR — Risk table (§5) is novelty-complete but empirical-hygiene-thin.**
  Missing: survivorship bias, look-ahead leakage beyond the Q4 harness's
  own claim, transaction costs/slippage consistently across all three
  decision layers, regime-label arbitrariness, multiple-testing/p-hacking
  exposure across 26 systems × horizons × regimes, statistical power, and
  — most load-bearing — whether the 26 adapters are *actually* independent
  or share datasets/pretrained backbones/market signals underneath. A real
  ICAIF reviewer would press on adapter independence before accepting
  "heterogeneous systems" as a clean experimental substrate.
- **MAJOR — Candidate 3's risk is rated too low relative to its blast
  radius.** `NOVELTY_AUDIT.md`/`CLAIM_CANDIDATES.md` call it the "highest
  thin-result risk" of the five, but the positioning report's own risk
  table rates it only Medium/"containable." Since regime-conditioning
  feeds *both* fusion and routing, a null or unstable regime finding
  degrades the combined framing itself, not just one ablation.
- **MAJOR — Process evidence (Codex thread IDs) is being used as if it
  were scholarly evidence.** Thread IDs are legitimate *process* audit
  trail (proof a real, non-fabricated review occurred) but are not
  independent novelty validation — a Codex reviewer's opinion is one more
  informed opinion, not a literature fact. The four deliverables should
  more consistently distinguish "search found no collision" (scholarly
  evidence) from "a cross-model reviewer agrees with our read" (process
  corroboration).
- **MAJOR — "26 real, independently-published, heterogeneous systems" is
  asserted, not exhibited.** Every deliverable treats this as a settled
  premise. A compact adapter-provenance table (source, paradigm, output
  type, confidence-kind, train/eval date boundaries, externally-authored
  y/n) is the natural artifact to substantiate it and does not exist yet
  in this deliverable set.
- **MINOR — terminology handling (the "calibration" trap) is consistently
  and correctly applied across all four files** — flagged as a genuine
  strength, not a gap.

**Overall**: close to handoff quality, but not fully hardened. Main fixes
are not more literature breadth — they are (1) tightening the
combined-paper structure so fusion/routing/abstention share one real
evaluation protocol, not just a narrative frame, (2) expanding the risk
table to cover financial-evaluation hygiene and adapter-independence, not
just novelty collisions, and (3) inlining a direct FineFT differentiation
paragraph in the positioning report itself rather than only in
`NOVELTY_AUDIT.md`.

---

## Consolidated verdict for the parent task

**The recommended main line (§2 of `ICAIF_POSITIONING_REPORT.md`) is
credible as a *positioning* document — it does not overclaim novelty and
already discloses its own conditionality honestly — but it would not yet
survive a hostile ICAIF area-chair read if treated as a near-final paper
framing.** 0 of 6 kill-argument points were left fully unresolved, but 3 of
6 were `partially_answered` at critical severity, and the balanced review
independently surfaced one structural risk (fusion/routing/abstention not
yet sharing one real evaluation protocol) and one evidentiary gap
(adapter-independence / provenance table) that the report does not
currently address at all. These are genuine, actionable gaps for whoever
turns this positioning into an actual paper draft — not blocking issues for
the positioning report itself, which was scoped as "recommend a direction,"
not "write a submission-ready paper."
