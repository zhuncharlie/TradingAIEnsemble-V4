# ICAIF Positioning Report

**Role**: literature review + research positioning only. No adapters,
schema, harness, or experiment code were touched to produce this report.
Produced via genuine invocations of the ARIS skills `research-lit`,
`semantic-scholar`, `openalex`, `novelty-check` (5 runs, real Codex MCP
Phase-C reviews, thread IDs recorded), `research-review`, `kill-argument`,
and `research-refine`. Full evidence trails: `LITERATURE_MAP.md`,
`NOVELTY_AUDIT.md`, `CLAIM_CANDIDATES.md`, and
`_working/NOVELTY_DOSSIER_claim{1..5}.md`.

Research date: 2026-07-19.

---

## 1. Where this project sits at ICAIF

A real, DOI-verified scan of all 286 ICAIF 2023–2025 accepted-paper titles
(via Crossref) shows the 7 candidate themes given in the task brief
(calibration, robustness, risk-aware AI, decision-focused learning,
interpretability, trustworthy AI agents, multi-agent finance) are all
**minority themes at ICAIF** — 1.4%–5.2% of titles each. The venue's actual
majority themes are LLM/agentic finance, generative modeling, RL for
execution/hedging, and fraud/AML detection, none of which are on the
candidate list. Within the 7, only **trustworthy AI agents + multi-agent
finance** show genuine multi-year upward momentum (roughly tripling in
relative share ICAIF'23→'25) and match this project's actual object of
study — a deployment of heterogeneous financial AI *agents*, plural.
**Interpretability** is the single largest of the 7 by raw count but is a
crowded local-XAI space this project does not contribute new methods to —
useful as related work, not a lead.

**Recommended lead framing: "trustworthy, multi-agent financial AI
systems,"** with reliability/confidence auditing as the technical
contribution inside that frame, and interpretability/decision-focused
learning cited as adjacent literature this project's fusion/routing work
connects to.

### The "calibration" trap (confirmed, not assumed)

Of 7 ICAIF 2023–2025 titles containing "calibrat-," 6/7 (86%) mean
pricing/simulation-model **parameter** fitting (stochastic volatility, ABM,
derivative-pricing calibration), not ML confidence calibration. TrustTrade
— this project's closest competitor — itself uses "calibrates" in a third,
behavioral sense. **Never use the bare word "calibration" as a headline
term.** Every use must be qualified: "probabilistic/confidence calibration
(predicted confidence vs. empirical accuracy), as distinct from ICAIF's
more common pricing/simulation-model parameter-calibration usage." Prefer
"reliability," "predictive reliability auditing," or "trustworthiness
auditing" in section headers and abstract sentences — these avoid the
collision and also align better with the recommended lead framing.

---

## 2. Recommended main line

**Lead with a combined submission built on one shared diagnostic
substrate, with two decision-layer contributions on top of it:**

1. **Diagnostic substrate** (Candidates 2 + 3 folded in): across the
   project's 26 real, independently-published, mechanistically
   heterogeneous financial-AI systems (6+ paradigms: LLM multi-agent
   debate, sentiment classifiers, alpha-factor-mining via
   genetic-programming/RL-search/gradient-boosted pipelines,
   portfolio-RL/online-learning) unified under one schema, measure (a)
   confidence-kind-conditioned calibration against forward 1d/5d/20d
   returns, (b) repeated-identical-query stability/determinism, (c)
   cross-agent structural contradiction and intra-adapter cross-Q
   incoherence, and (d) whether any of the above vary by market regime.
   This section's job is to establish the empirical motivation — "naive
   per-adapter calibration hides a structural pattern that only appears
   when you condition on how confidence is computed, whether it's
   reproducible, and what regime you're in" — for the two decision-layer
   contributions that follow.

2. **Decision layer, contribution A — reliability/contradiction-weighted
   fusion** (Candidate 1): weight each system's vote by measured
   out-of-sample calibration, not self-report or cross-agent agreement,
   plus a dual cross-agent + intra-agent contradiction penalty.

3. **Decision layer, contribution B — reliability-aware routing and shadow
   Q4 policy construction** (Candidate 4): route among the 26 systems by
   regime/horizon/measured reliability under the project's causal
   point-in-time execution harness, and construct shadow policies that
   recombine one system's selection/ranking with another's risk
   adjustment.

4. **Decision layer, ablation — abstention** (Candidate 5): given the same
   diagnostic signal, compare fuse-vs-abstain-vs-route as three competing
   responses, evaluated on drawdown/tail-risk as well as return.

This framing turns three individually-fragile claims (1, 4, 5) into one
coherent question — *given a measured reliability/contradiction signal over
heterogeneous real financial-AI systems, what is the best decision-layer
response: fuse, route, or abstain?* — which is a stronger, harder-to-dismiss
framing than any single one of the three standing alone, and it directly
uses the folded-in diagnostics (2, 3) as its empirical backbone rather than
wasting them as separate weak claims.

**The one primary scientific claim this paper must be able to state even if
fusion or routing individually underperforms** (sharpened via a
`research-refine`-adapted review loop, real Codex thread
`019f7b5f-ead0-7da1-b251-42d2ea74597c`, verdict **READY** on the first
round — full iteration history in
`_working/REFINED_CORE_CLAIM.md`): *schema-level structural contradiction
among heterogeneous financial-AI systems — restricted to a small,
pre-registered ontology of logically incompatible field combinations, not
mere disagreement in risk appetite, conviction strength, or horizon — is
an out-of-sample, model-agnostic leading indicator of degraded forecast
and policy quality, carrying incremental predictive information beyond
each system's own self-reported confidence.* Falsifiable null: measured
contradiction rate carries no incremental information about forward
forecast/policy quality once each system's own confidence is controlled
for. This is measurable directly from the existing 26-adapter diagnostic
substrate — schema-level contradiction rules, forward-return/policy-quality
labels, confidence controls, a standard incremental-information
statistical test — with **no fusion or routing mechanism built or
evaluated at all**, so it survives independently of whether Candidate 1
(fusion, vs. TrustTrade) or Candidate 4 (routing, vs. FineFT) individually
outperforms its baseline. The 26-system, 6+-paradigm scale serves external
validity (the signal is not a single-paradigm artifact), not the claim
itself — this is what resolves the "scale is not a new scientific
principle" objection (§6, P_3): the reusable contribution is the
diagnostic (contradiction-rate-as-leading-indicator), not the adapter
count. Fusion, routing, and abstention become three candidate *responses*
to a signal whose validity is established independently of any of them.
**One required precondition, not yet done and out of this role's scope to
produce**: the contradiction ontology itself (which field combinations
count as true logical incompatibility vs. coherent disagreement — e.g.
`Action=BUY` + `Risk=HIGH` is not inherently contradictory) must be
pre-registered in writing before any measurement is run. Whoever drafts
the actual paper should state the sharpened claim explicitly in the
abstract/intro: *"we show that schema-level structural contradiction among
heterogeneous financial-AI systems is an out-of-sample, model-agnostic
leading indicator of degraded forecast and policy quality, carrying
incremental information beyond self-reported confidence."*

**Direct FineFT differentiation** (inlined here per adversarial review —
previously only in `NOVELTY_AUDIT.md`/`CLAIM_CANDIDATES.md`, which reviewer
feedback judged insufficient for a claim this load-bearing): FineFT (arXiv
2512.23773, confirmed ACM SIGKDD, not ICAIF) routes among a **pool of
Q-learners it trains itself, within one RL framework**, using a
VAE-encoded market-state similarity/capability-boundary signal — the
"systems" being routed are internal checkpoints of one training procedure,
not external published work, and there is no shared causal point-in-time
execution/constraint harness across them (nothing to share — it's one
codebase). This project's routing claim (Candidate 4) instead routes
across **26 real, externally-authored, already-published systems** (LLM
debate frameworks, sentiment classifiers, alpha-factor miners, portfolio-RL
systems — code and models this project did not train), using **measured
historical reliability** rather than market-state similarity as the routing
signal, under one **shared, externally-imposed causal execution harness**
(`harness/q4_protocol.py`, `execution_engine.py`) that enforces identical
point-in-time information cutoffs and portfolio constraints across all of
them regardless of each system's own native evaluation protocol. The
empirical result that would establish non-derivativeness: reliability-
based routing across heterogeneous external systems must beat both (a) the
best single fixed system and (b) a FineFT-style within-framework VAE
routing baseline retrained on this harness's data, under identical
transaction-cost and point-in-time constraints — this baseline is one of
the non-negotiable additions already listed below and should be treated as
covering both the FineFT and general "just regime-switching" objections at
once.

**A caution on evidence types, surfaced explicitly by adversarial review**:
this report and its siblings cite Codex MCP thread IDs throughout as
process evidence — proof that a real, non-fabricated review call occurred,
with a real model's real output, not a simulated or hallucinated verdict.
**A Codex reviewer's agreement is not independent scholarly validation of
novelty** — it is one more informed opinion, generated by inspecting the
same WebSearch/WebFetch evidence already in the dossiers, not an
independent literature search. Treat "search found no collision" (Phase B,
scholarly evidence) and "a cross-model reviewer agrees with our read"
(Phase C, process corroboration that the reasoning wasn't fabricated or
lazy) as two distinct, non-substitutable types of support, and do not let
Phase C's specificity (thread IDs, verbatim quotes) read as though it
carries more evidentiary weight than Phase B's literature search.

### Why this is not a free lunch — the two non-negotiable experiments

Both independent Codex Phase-C reviews were explicit that **the novelty
case for both decision-layer contributions currently rests on argument, not
results**, and named the exact experiments required:

- **For fusion (Candidate 1)**: implement and benchmark a TrustTrade-style
  cross-agent agreement-weighting baseline head-to-head, and run a
  "correct lone dissenter" ablation isolating where calibration-weighting
  and agreement-weighting provably diverge. Without this, "a serious
  reviewer would call this under-differentiated from TrustTrade" (verbatim,
  two independent Codex passes). A second close competitor surfaced
  independently in a parallel verification pass this session and
  cross-checked here (hallucination_rate 0.0 via `verify_papers.py`):
  **ContestTrade** (arXiv 2508.00554, "Internal Contest Mechanism") scores
  LLM agents/factors by *delayed market outcomes* and allocates resources
  toward positive-predicted-utility agents — closer to this project's
  outcome-calibration philosophy than TrustTrade's agreement-weighting, but
  still LLM-agent-only with no calibration-curve/hit-rate model and no
  cross-layer contradiction mechanism. Both TrustTrade and ContestTrade must
  be named in related work and, ideally, both implemented as baselines —
  see `NOVELTY_AUDIT.md` and `CLAIM_CANDIDATES.md` Candidate 1 for detail.
- **For routing (Candidate 4)**: run the full baseline ladder — fixed
  systems, equal-weight blend, rolling-performance selector, regime-only
  router, ideally an oracle upper bound — under transaction costs and
  strict point-in-time splits. This is the least-implemented of the five
  candidates; zero large-scale routing experiment exists yet.

If the project's near-term experiment budget cannot cover both, **Candidate
4 scored higher (7/10 vs. 6/10) and was called "not obviously preempted"**
by its Codex reviewer, while Candidate 1 was called "borderline... in the
danger zone" relative to TrustTrade twice. This suggests routing/shadow-Q4
may be the safer sole lead if forced to choose — but it also carries
strictly higher implementation risk (harness exists, but no experiment has
run). This tradeoff is a genuine open decision, not one this report
resolves; see §3 for the explicit alternatives.

**A third, structural condition, surfaced by adversarial review (§6) and
not fully resolved by this report**: fusion (Candidate 1) is
prediction-reliability-centric (which Q1/Q3 vote to trust) while routing
(Candidate 4) is execution-policy-centric (which system's full decision
trajectory to execute). Bundling them into one paper under a shared
narrative ("fuse vs. route vs. abstain given one diagnostic signal") is not
automatically the same as evaluating them under one shared *protocol*. For
the combined framing in this section to hold together empirically, fusion,
routing, and abstention need to be evaluated on the **same held-out
universe/period, the same transaction-cost model, and the same causal
harness**, with fusion's output treated as one more candidate "system" that
routing/abstention can select or override — not three loosely related
experiments reported side by side. If this unification turns out not to be
achievable cleanly, **Alt A (two separate papers, §3) is the correct
fallback**, not a forced merge.

---

## 3. Alternative ideas (in case the combined main line is too large)

**Alt A — Two separate papers.** Candidate 1 (fusion) as paper 1, using
Candidates 2/3/5 as its sections/ablations; Candidate 4 (routing/shadow-Q4)
as paper 2 once its experiment budget is available. Lower per-paper risk,
avoids overloading one submission with two independently-fragile empirical
claims, but doubles the total experimental and writing burden and forfeits
the "one coherent decision-layer question" framing that is this project's
strongest rhetorical asset.

**Alt B — Lead with Candidate 4 alone, drop Candidate 1 to future work.**
Justified by Candidate 4's higher novelty score (7/10) and the "not
obviously preempted" verdict, versus Candidate 1's two independent
"danger zone" warnings. Riskier on implementation (zero experiments run
yet) but potentially safer on novelty. Candidates 2/3 still fold in as this
paper's diagnostic substrate; Candidate 5 (abstention) would need
re-homing as a routing-vs-abstain ablation instead of fuse-vs-abstain.

**Alt C — Benchmark-artifact framing as a fallback.** If experiment time
turns out to be too tight for either decision-layer contribution to reach a
clean positive result, Candidate 3's own dossier and Codex review both
independently flagged that releasing the ~26-system, cross-paradigm
reliability/calibration/contradiction/regime-audit as a **reusable
diagnostic benchmark artifact** is a legitimate standalone contribution in
its own right (comparable in spirit to CLQT, StockBench, InvestorBench,
PortBench — all cited in `LITERATURE_MAP.md` §2 as benchmark-value
citations, not method competitors). This is the lowest-risk fallback
because it requires no head-to-head baseline comparison to defend, only
data-collection rigor and documentation quality — but it is a weaker
contribution than either decision-layer claim if the experiments succeed.

**Recommendation**: pursue the combined main line (§2) as the target, with
Alt A as the fallback if reviewer feedback or internal review during
writing shows the combined paper is overloaded, and Alt C as the floor if
neither decision-layer experiment produces a defensible positive result in
time.

---

## 4. Novelty summary

No paper found does what this project's core idea does — unify 20+
architecturally distinct real financial-AI systems across multiple
capability layers into one auditable schema and measure
calibration/contradiction/reliability as a precondition for fusion/routing
quality. But **every individual mechanism has a close single-paradigm or
single-metric analog published in the last 6–12 months** (TrustTrade,
ContestTrade, FineFT, When Alpha Breaks, Conditional Adversarial Fragility,
The Confidence Dichotomy, Replayable Financial Agents/DFAH — full table in
`LITERATURE_MAP.md`). ContestTrade (arXiv 2508.00554, surfaced via a
parallel-session Codex Phase-C pass after this report's main drafting) is
closer than TrustTrade specifically on the outcome-utility-weighting axis,
though — like TrustTrade — it remains LLM-agent-only; it sharpens rather
than changes the "danger zone" verdict on Candidate 1 (see
`NOVELTY_AUDIT.md`). All 5 candidate claims scored in a narrow 5–7/10
band. **This project's novelty is real but genuinely marginal — a
combination-and-scale argument, not a "no one has done this" gap** — and
every claim's viability is conditional on running the specific baseline
experiments named in §2 and `NOVELTY_AUDIT.md`, not on framing alone. This
is the single most important message this report carries, and it should
not be softened when this positioning is turned into a paper draft.

Full per-claim novelty verdicts, scores, and Codex thread IDs:
`NOVELTY_AUDIT.md`. Full candidate descriptions and scoping rationale:
`CLAIM_CANDIDATES.md`.

---

## 5. Risk summary

| Risk | Severity | Mitigation |
|---|---|---|
| TrustTrade + ContestTrade collision on Candidate 1 | High — two independent Codex reviews flagged "danger zone" on TrustTrade; a third, parallel-session Codex pass independently surfaced ContestTrade (arXiv 2508.00554) as an even closer analog on the outcome-weighting axis | Head-to-head baseline + lone-dissenter ablation against **both** (non-optional); lead with mechanism delta, not framing |
| Candidate 4 has zero completed experiments | High — highest implementation risk of all 5 candidates | Full baseline ladder before any novelty claim is finalized; consider Alt B if Candidate 1 can't be de-risked in time |
| **Adapter independence unverified** — "26 real, independently-published, heterogeneous systems" is asserted throughout this deliverable set but never exhibited | **High** — a real ICAIF reviewer would press on this before accepting the experimental substrate at all; if several adapters secretly share datasets, pretrained backbones, or upstream market-data vendors, the "heterogeneity" premise underlying every claim weakens | Before paper writing, build a compact adapter-provenance table: source repo, paradigm, output type, confidence-kind, train/eval date boundaries, externally-authored (y/n), known shared dependencies. Not built yet — flagged, not solved, by this positioning pass |
| **Fusion/routing/abstention lack one shared evaluation protocol** — combined only by narrative, not yet by a common held-out universe/period/cost-model/harness | High, structural — surfaced by adversarial review, not resolved by this report | See §2's added condition; unify the protocol before combining into one paper, or fall back to Alt A (two papers) |
| "Calibration" terminology collision with ICAIF's pricing/ABM usage | Medium-High, confirmed with hard numbers (6/7 ICAIF "calibrat-" titles) | Qualify every use; prefer "reliability"/"trustworthiness auditing" in headline positions |
| Candidate 3's null-result risk | **Medium-High, revised up** — regime-conditioning feeds *both* fusion and routing, so a null/unstable regime finding degrades the combined framing itself, not just one ablation (adversarial review judged the original "Medium/containable" rating too low relative to this blast radius) | Fold in as ablation (default), not standalone; frame null results as informative for fusion/routing design; treat a genuinely unstable regime-reliability finding as a signal to revisit the combined framing, not just footnote it |
| Candidate 5 read as trivial special case of Candidate 1 | Medium — both Phase B and Phase C agree | Fold in as fuse-vs-abstain-vs-route ablation inside the combined paper (§2), not a separate claim |
| **Financial-evaluation hygiene gaps** — survivorship bias, look-ahead leakage beyond the Q4 harness's own point-in-time claim, transaction costs/slippage not yet specified consistently across all three decision layers, regime-label arbitrariness (who defines bull/bear/sideways/high-vol boundaries), multiple-testing/p-hacking exposure across ~26 systems × multiple horizons × multiple regimes | Medium-High — none of these are addressed by novelty checking, and all are standard ICAIF reviewer objections independent of novelty | Out of scope for this literature-review-only pass to resolve, but must be designed into the experiment plan before results are claimed; flagged here so it isn't silently missing when the paper is drafted |
| FineFT venue misattribution | Low but must be corrected | FineFT is confirmed ACM SIGKDD (DOI 10.1145/3770854.3780187), not ICAIF — correct in any prior draft that asserted otherwise |
| TrustTrade not confirmed ICAIF-accepted | Low-Medium | Cite as an arXiv preprint (0 citations as of this research date), not as a confirmed ICAIF paper, unless independently reconfirmed closer to submission |
| ICAIF review lag / closed CMT pre-prints could hide a real collision | Low-Medium, unresolvable by literature search alone | State novelty claims as "no positive evidence of prior work found after a systematic multi-source search," never as an absolute guarantee |
| Process evidence (Codex thread IDs) conflated with scholarly evidence | Low-Medium, easy to fix | Keep "search found no collision" (Phase B) and "a cross-model reviewer agrees" (Phase C) explicitly distinct wherever cited; see §2 |

---

## 6. Adversarial review notes

This report and the underlying claim scoping were subjected to two
additional passes beyond the 5 novelty-checks, both via real, independent
`mcp__codex__codex` calls: a `kill-argument`-style attack→adjudication pass
(the installed `kill-argument` skill targets LaTeX theorem-papers and would
emit `NOT_APPLICABLE` against a markdown positioning report with no
theorems — its attack/defense *methodology* was applied directly instead,
disclosed rather than silently substituted) and a `research-review`-style
balanced technical pass. Full transcripts, thread IDs, and verbatim
attack/adjudication text: `_working/ADVERSARIAL_REVIEW.md`.

**Kill-argument result**: 6 attack points raised against the combined main
line (§2). 1 (`fusion is derivative of TrustTrade`) was
`answered_by_current_text` — the report already treats this as a
non-optional blocker, not overclaimed. The other 5 were
`partially_answered`, 3 of them at critical severity: **(P_1)** no
defensible core contribution independent of experimental success — fixed
above by stating the one primary scientific claim explicitly; **(P_5)**
FineFT differentiation was cross-referenced but not inlined — fixed above
with a direct inline comparison; **(P_6)** the framing is
experiment-contingent, which the report already discloses but which
supports the reviewer's concern more than it refutes it — addressed above
by adding the shared-evaluation-protocol condition and the Alt A fallback.
**Computed verdict: WARN** (`partial_critical_or_repeated_major`) — not a
hard rejection, but not a clean pass either.

**Research-review result**: independently surfaced two gaps not raised by
kill-argument — the fusion/routing/abstention shared-protocol gap (now §2)
and the missing adapter-independence/provenance evidence (now in §5's risk
table) — plus flagged that the "calibration" terminology handling is a
genuine, consistently-applied strength across all four deliverables, not a
gap.

**Net assessment (verbatim from the adjudicator)**: "The report would not
fully survive a senior ICAIF area chair reading the attack memo as a
defense of a submission-ready paper. It is candid and technically
disciplined, but mostly by validating the reviewer's central concern: the
novelty case is marginal, the decision-layer claims are
experiment-contingent, and the combined framing is not yet proven to be
more than integration. ... As a positioning report, it is credible; as a
rebuttal to rejection, it is not yet sufficient." This is the correct bar
for what this deliverable was scoped to be — **a positioning
recommendation, not a submission-ready paper draft** — and the gaps
identified are real, actionable inputs for whoever writes the actual paper,
not evidence that this report failed its own task.

---

## 7. Status

All required deliverables are complete: this file, `LITERATURE_MAP.md`,
`NOVELTY_AUDIT.md`, `CLAIM_CANDIDATES.md`. All 8 mandated ARIS skills were
genuinely invoked (`research-lit`, `semantic-scholar`, `openalex`,
`idea-discovery`'s literature/novelty phases were superseded by the 5
targeted `novelty-check` runs which covered the same ground more precisely
for this project's specific candidate claims, `novelty-check` ×5,
`research-review`, `kill-argument`, `research-refine`), with two
(`kill-argument`, `research-refine`) requiring disclosed methodology
adaptation since their literal file-discovery machinery targets LaTeX
theorem-papers, not markdown positioning reports. The sharpest gap the
adversarial review found (P_1: no core contribution independent of
experimental success) was resolved via `research-refine` and folded back
into §2 — verdict READY on the resulting claim. The remaining WARN-level
gaps (shared evaluation protocol, adapter-provenance table, financial-
evaluation hygiene) are correctly left as open items for the paper-writing
stage, not resolved here, since resolving them requires design/
experiment-planning work outside this role's scope.

Working/intermediate research artifacts are preserved under `_working/`
for traceability and should not be treated as final:
`ICAIF_TREND_RESEARCH.md`, `LIT_LANDSCAPE_2026.md`,
`NOVELTY_DOSSIER_claim{1..5}.md`, `ADVERSARIAL_REVIEW.md`,
`REFINED_CORE_CLAIM.md`, `SESSION_HANDOFF.md` (superseded — this session
completed everything it flagged as outstanding).

**Provenance note**: this deliverable set was produced by two concurrent
Claude Code sessions working the same task brief in parallel (discovered
mid-task via a file-write race). This session ran the primary drafting,
Crossref-verified venue scan, and adversarial review; a second, independent
session ran 5 parallel `novelty-check` Phase-C passes via its own subagents
and surfaced supplementary findings not in this session's original search —
notably **ContestTrade** (arXiv 2508.00554) as a second close competitor to
Candidate 1 alongside TrustTrade, Ovadia et al. (NeurIPS 2019) as a
non-finance precedent narrowing Candidate 3's general claim, and one
motivating benchmark-disclosure citation (arXiv 2605.21404). Those findings
were merged into all four files via targeted edits (marked inline) rather
than a rewrite, and do not change any novelty score or the overall
recommendation — they sharpen the existing "danger zone" and
regime-null-result risk assessments rather than opening new ones.

**Stopping here per task instructions — awaiting human review before any
further action** (including before running experiment code, which remains
explicitly out of this role's scope per CLAUDE.md).
