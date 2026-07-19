# Claim Candidates — ICAIF Positioning

Five candidate contributions were drafted from a non-mechanical evaluation
of the project's Exp1–Exp18 reference list (several items were merged or
dropped rather than adopted 1:1), then each independently novelty-checked
(Phase B literature search + Phase C real Codex MCP cross-model review; see
`NOVELTY_AUDIT.md` for the synthesized verdicts and
`_working/NOVELTY_DOSSIER_claim{1..5}.md` for full reasoning trails, thread
IDs, and verbatim reviewer responses). Two survive as standalone-paper-
worthy; three fold in as sections/ablations. This file presents all five
with their evidence-backed scoping recommendation, since the task asked for
4–5 candidate contributions, not just the winners.

**All scores and citations below trace to a specific dossier file and a
specific tool call (WebFetch, arXiv API, or a Codex MCP thread ID); nothing
here is asserted without that backing.**

---

## Candidate 1 — Reliability- and Contradiction-Aware Multi-View Fusion

**Status: PROCEED WITH CAUTION — standalone-worthy, conditionally.**
Novelty: MEDIUM (6/10).

**What it is.** Fuse Q1/Q3 outputs across the project's 26 real,
independently-published, mechanistically heterogeneous adapters (LLM
multi-agent debate, sentiment classifiers, alpha-factor-mining across
genetic-programming/RL-search/LLM-agent/gradient-boosted paradigms,
portfolio-RL/online-learning systems), weighting each source's vote by (a)
its *measured, out-of-sample* calibration reliability — realized hit rate
vs. self-reported confidence, tracked causally — not the self-reported
confidence itself, plus (b) a penalty when a cross-agent contradiction rule
fires or the same adapter's own Q1–Q4 outputs are internally incoherent.

**Why it's real.** No paper found fuses genuinely heterogeneous, real,
independently-published systems this way. The closest work, TrustTrade
(arXiv 2603.22567, confirmed via direct WebFetch of its abstract), fuses
multiple LLM *instances* by cross-agent *agreement* — a structurally
different reliability signal that mathematically penalizes a correct lone
dissenter, which calibration-based weighting need not. A second close
competitor, **ContestTrade** (arXiv 2508.00554, "Internal Contest
Mechanism," found via an independent Codex Phase-C pass in a parallel
verification run), scores LLM agents/factors by *delayed market outcomes*
and allocates resources toward positive-predicted-utility agents — closer
than TrustTrade on the outcome-weighting axis specifically, but still
LLM-agent-only, with no calibration-curve/hit-rate model and no cross-layer
contradiction-severity mechanism. Both must be cited and differentiated,
not just one.

**Non-negotiable conditions before this is paper-worthy** (two independent
Codex Phase-C reviews agreed, thread IDs `019f7b46-5195-7f42-add1-5f1076b76c56`
and `019f7b4a-1461-71f2-9d00-33edd98ebe85`): implement and benchmark a
TrustTrade-style agreement-weighting baseline head-to-head, and run a
"correct lone dissenter" ablation that isolates where the two weighting
philosophies provably diverge. Lead with that mechanism delta, not with the
"confidence means incompatible things across mechanism types" framing
(flagged twice as likely to read as obvious/motivational, not a novelty
anchor).

**Recommended absorption**: Candidates 2 and 5 fold in here as diagnostic
section and ablation arm, respectively (see below).

---

## Candidate 2 — Calibration and Stability Evaluation of Heterogeneous Financial Agents

**Status: FOLD INTO CANDIDATE 1 — not standalone.** Novelty: MEDIUM (5/10).

**What it is.** (a) Confidence-kind-conditioned calibration — does Q1
confidence / Q3 strength predict forward 1d/5d/20d returns, broken out by
*which mechanism* produces the confidence value (self-report, model-margin,
heuristic normalization, entropy-derived, static IC, etc. — using the
project's own CONTRACT confidence-kind taxonomy)? (b) A repeated-identical-
query stability diagnostic — call each adapter K times on frozen (ticker,
date) inputs, separating "miscalibrated but deterministic" from
"non-deterministic," motivated by a real defect already found in one
adapter (unseeded per-call retraining causing the same query to return
different outputs on different calls).

**Why it's not standalone.** Each half has a close single-paradigm analog:
The Confidence Dichotomy (arXiv 2601.07264, mechanism-conditioned
calibration, non-finance) and Replayable Financial Agents/DFAH (arXiv
2601.15322, finance-domain determinism testing, LLM-only). A reviewer would
reasonably ask "what's new besides the dataset?"

**How it earns its place.** As the empirical motivation section for
Candidate 1: the specific cross-paradigm interaction pattern (which
mechanism-kind × which paradigm × miscalibrated-vs-nondeterministic) is
what justifies calibration-aware, stability-aware fusion weights instead of
a naive confidence-weighted ensemble — a full section, not a footnote.

---

## Candidate 3 — Regime-Conditioned Reliability Audit

**Status: FOLD INTO CANDIDATES 1 & 4 (default) — standalone only as a
released benchmark artifact.** Novelty: MEDIUM-HIGH (6/10), the second-
highest score of the five, but with the highest "thin result" risk.

**What it is.** An open empirical question (explicitly tolerating a null
result): does measured *reliability* — calibration error, hit-rate
stability, cross-adapter contradiction rate, not accuracy or returns — vary
systematically by market regime (bull/bear/sideways/high-vol), across a
~26-system, 6+-paradigm real deployment?

**Why it scores well.** Genuinely unoccupied as a specific question — no
paper audits *reliability* (as opposed to accuracy, returns, or adversarial
robustness) by regime across a multi-system deployment. Closest, Conditional
Adversarial Fragility (arXiv 2512.19935), studies regime-conditioned
*adversarial* fragility for one architecture and explicitly finds ordinary
calibration is regime-*stable* — a fact a reviewer could misuse to claim
this question is already answered.

**Why it doesn't stand alone.** Both Phase B and Phase C (Codex thread
`019f7b49-7338-79b0-93ac-22f7d0fafa27`) independently concluded a null or
weakly-powered result reads as "a useful robustness check," not a
contribution, at a finance-AI venue — unless the ~26-system evaluation
surface itself is packaged and released as a reusable heterogeneous-system
reliability benchmark, which is a separate (Candidate-1/2-adjacent)
contribution in its own right, not this claim's job to carry alone.

**Recommended framing**: a regime-stratified ablation feeding both
Candidate 1 (does fusion weighting need regime-conditioning?) and Candidate
4 (does routing need regime-conditioning?) — report a null result as
informative for fusion/routing policy design ("reliability degradation is
regime-invariant across paradigms"), not as a failed experiment.

---

## Candidate 4 — Reliability-Aware Routing and Shadow Q4 Policy Construction

**Status: PROCEED WITH CAUTION — standalone-worthy, conditionally, highest
implementation risk.** Novelty: MEDIUM-HIGH (7/10), the highest score of
the five.

**What it is.** Built on the project's newly-finished causal, point-in-time
Q4 stepwise execution harness (`harness/q4_protocol.py`,
`execution_engine.py`, confirmed present in the repo). Two mechanisms: (a)
route among the 26 heterogeneous real systems by regime/horizon/historical
measured reliability at each causal decision step; (b) construct "shadow"
Q4 policies by combining one system's Q1/Q3 selection-and-ranking with
another system's Q4 risk adjustment into a synthetic, causally-evaluated
decision trajectory — evaluated against each fixed underlying system and a
naive equal-weight blend.

**Why it's real.** FineFT (arXiv 2512.23773 — confirmed **ACM SIGKDD, not
ICAIF**, via Semantic Scholar's `publicationVenue` field) is the closest
paper and routes across a self-trained pool of Q-learners within one RL
framework via VAE market-state similarity, with no causal point-in-time
execution/constraint harness and no independently-authored external
systems. Codex Phase C (thread `019f7b4a-1d93-7333-bb05-8c836c5c23e5`):
"not obviously preempted by FineFT, MM-DREX, or Look-Ahead-Freedom."

**Why it's risky.** Zero large-scale multi-regime routing experiment exists
yet for this claim — the enabling harness is built and tested, but the
novelty case currently rests on argument, not results. A skeptical reviewer
can dismiss the routing half as "standard dynamic ensemble selection /
regime switching," treating "independently-published systems" as an
engineering detail.

**Non-negotiable conditions**: run the actual multi-baseline experiment
(fixed systems, equal-weight blend, rolling-performance selector,
regime-only router, ideally an oracle upper bound, transaction costs, strict
point-in-time splits) before resting the claim on framing alone. **Lead
with the shadow-policy sub-claim, not routing** — Phase C called it "the
stronger, more defensible half," less obviously covered by
FineFT/MM-DREX-style routing, provided the Q1/Q3/Q4 decomposition is
well-defined and causal rather than reading as post-hoc signal stacking.

---

## Candidate 5 — Contradiction-Aware Selective Prediction (Abstention)

**Status: FOLD INTO CANDIDATE 1 as an ablation arm — not standalone.**
Novelty: MEDIUM-LOW (5/10).

**What it is.** When cross-agent structural contradiction (e.g. one system
says BUY, another flags HIGH_RISK on the same ticker/date) or high
intra-adapter cross-Q incoherence is detected, respond by abstaining,
reducing position size, or increasing cash allocation — instead of fusing
the disagreeing signals (Candidate 1's response to the same signal).
Evaluated on drawdown/tail-risk reduction, not raw return.

**Why it's not standalone.** Both Phase B and Phase C (Codex thread
`019f7b50-cc8d-75b0-b2b4-920684cd0088`) read this as a plausible special
case of Candidate 1's fusion formula (a zero-weight branch) rather than a
distinct contribution with its own theory. Closest: When Alpha Breaks
(arXiv 2603.13252) for the risk-first evaluation philosophy (single-model
trigger, not cross-system); TrustTrade for the multi-agent setting
(continuous reweighting — confirmed via WebFetch, no full-abstention mode
documented).

**How it earns its place.** As an ablation arm inside Candidate 1: "given
the same contradiction/reliability diagnostic signal, when is it better to
fuse versus step aside?" Per Codex Phase C: "the stronger claim is that
structural contradiction is a useful risk signal beyond ordinary
uncertainty, confidence, or ensemble dispersion baselines" — this is the
specific empirical angle worth foregrounding inside the ablation.

---

## Net recommendation

**Two standalone-paper candidates (1, fusion; 4, routing/shadow-Q4), each
conditional on a specific named baseline experiment that has not yet been
run.** Three folded contributions (2, 3, 5) that strengthen 1 and 4 as
sections and ablations rather than standing alone.

No claim scored below 5/10 or above 7/10 — this project's novelty is real
but genuinely marginal, not a clear "no one has done this" gap. See
`NOVELTY_AUDIT.md` for the full cross-claim synthesis table and
`ICAIF_POSITIONING_REPORT.md` for the recommended overall paper structure,
including the option of combining Candidates 1 and 4 into one unified
"three decision-layer policies over one diagnostic substrate" paper versus
keeping them as two separate submissions.

Both **TrustTrade** (arXiv 2603.22567) and **FineFT** (arXiv 2512.23773,
confirmed ACM SIGKDD) are real, recent (2025–2026) papers that must be
cited prominently and differentiated explicitly in any submission, not
omitted.
