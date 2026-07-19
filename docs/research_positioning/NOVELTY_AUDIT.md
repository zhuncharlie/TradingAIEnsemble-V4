# Novelty Audit — ICAIF Positioning

Produced from 5 real `novelty-check` skill invocations (one per candidate
claim), each running Phase B (WebSearch/WebFetch literature search,
hallucination-checked via `verify_papers.py`) and Phase C (independent
Codex MCP cross-model review, `mcp__codex__codex`, real completions with
recorded thread IDs — not simulated). Two claims (1 and 3) received a
second independent Codex pass that converged with the first. Full
per-claim reasoning trails are preserved at
`_working/NOVELTY_DOSSIER_claim{1..5}.md` and should be treated as the
source of record; this file is the synthesized audit.

---

## Q: Does a published paper already do what this project's core idea does?

**No direct hit for the project's central framing** — "take 20+
architecturally distinct real upstream financial-AI systems spanning
multiple capability layers (not one monolithic category like 'LLM trading
agents'), convert them into one auditable schema with explicit provenance
separation, and measure calibration/contradiction/reliability as a
precondition for studying fusion/routing quality" — after a systematic
multi-source search (ICAIF proceedings full-title scan across 286 real
2023–2025 titles, arXiv API, Semantic Scholar, OpenAlex, targeted
competitor-paper deep-reads). This is stated as "no positive evidence
found," not as a certainty — ICAIF review lag and closed CMT pre-prints
could hide a match.

**But the individual mechanisms are each anticipated, in narrower form, by
recent (2025–2026) work**, and this is the real risk surface:

- **TrustTrade** (arXiv 2603.22567) does cross-agent reliability-weighted
  fusion — but only across homogeneous LLM instances, weighted by
  agreement, not measured calibration.
- **ContestTrade** (arXiv 2508.00554, "Internal Contest Mechanism," v4
  ~2026-07) — surfaced by a separate, independent Codex Phase-C pass run in
  parallel with this audit (same trading-ai-ensemble task, different
  session) and cross-checked here against `verify_papers.py`
  (hallucination_rate 0.0). Scores LLM agents/factors by **delayed market
  outcomes** and allocates resources to agents with positive predicted
  future utility — closer than TrustTrade on the *outcome-based* (vs.
  agreement-based) weighting dimension specifically. Still LLM-agent-only
  (internal Data/Research teams within one framework), with no
  calibration-curve/hit-rate model and no cross-layer (Q1/Q2/Q3/Q4)
  contradiction-severity mechanism. **Now the single closest overall prior
  work on the outcome-weighting axis** and should be added alongside
  TrustTrade wherever Claim 1 is differentiated — see `CLAIM_CANDIDATES.md`
  Candidate 1 and `LITERATURE_MAP.md` §1.
- **FineFT** (arXiv 2512.23773, confirmed **ACM SIGKDD**, not ICAIF) does
  reliability-aware routing — but only within one self-trained RL
  ensemble, not across independently-published systems.
- **When Alpha Breaks** (arXiv 2603.13252) does uncertainty-triggered
  abstention with drawdown/tail-risk framing — but from single-model
  epistemic uncertainty, not cross-system structural contradiction.
- **Conditional Adversarial Fragility** (arXiv 2512.19935) does
  regime-conditioned post hoc reliability evaluation — but for adversarial
  robustness of one fixed architecture, and explicitly finds ordinary
  calibration is regime-*stable*.
- **The Confidence Dichotomy** (arXiv 2601.07264) and **Replayable
  Financial Agents/DFAH** (arXiv 2601.15322) do mechanism-conditioned
  calibration and repeated-query determinism testing — but single-paradigm
  (LLM tool-use) and (for DFAH) already in finance, which is a direct
  partial collision on Claim 2's stability half.

**Net picture**: every piece of this project's toolkit has a close
single-paradigm or single-metric analog published in the last 6–12 months.
The novelty case rests entirely on the **combination and scale**
(cross-paradigm, ~26 independently-developed real systems, one causal
execution harness) — not on any individual mechanism being unprecedented.
Both independent Codex reviewers were explicit that this combination
argument must be demonstrated empirically (head-to-head baselines), not
asserted.

---

## Per-claim audit

### Claim 1 — Reliability- and Contradiction-Aware Multi-View Fusion

- **Existing similar work?** Yes, close: TrustTrade (arXiv 2603.22567) and,
  per a parallel-session Codex Phase-C pass, **ContestTrade** (arXiv
  2508.00554 — see top-of-file bullet for detail). Two independent Codex
  Phase-C reviews on this session's own dossier (thread IDs
  `019f7b46-5195-7f42-add1-5f1076b76c56` and
  `019f7b4a-1461-71f2-9d00-33edd98ebe85`) both called this claim
  **"borderline but not dead," "in the danger zone" relative to
  TrustTrade**, revising the Phase-B-only assessment down from
  MEDIUM-HIGH to **MEDIUM (6/10)**. ContestTrade sharpens the same danger
  zone from a second angle (outcome-utility weighting, not just
  agreement-weighting) rather than opening a new one — it does not change
  the 6/10 score, but both competitors must now be named in the paper's
  related work, not TrustTrade alone.
- **Biggest risk.** A reviewer reads the paper as "TrustTrade but with more
  agents," because both papers can be summarized in one sentence as
  "reliability-weighted multi-agent trading consensus." If the paper leads
  with "selective consensus" language rather than the specific mechanism
  delta, this risk is realized.
- **How to avoid it.**
  1. **Implement and benchmark a TrustTrade-style agreement-weighting
     baseline head-to-head** — both reviewers called this non-optional,
     not a nice-to-have.
  2. **Run an ablation/case-study isolating a "correct lone dissenter"
     scenario** where calibration-weighting and agreement-weighting
     provably diverge (agreement-weighting mathematically penalizes a
     dissenter by construction; calibration-weighting need not) — this is
     the sharpest, most defensible empirical hook, and should lead the
     paper's framing.
  3. **Do not lead with** "confidence means incompatible things across
     mechanism types" — both reviewers independently flagged this as
     likely to read as obvious/motivational, not a novelty anchor. Use it
     as background, not the headline.
  4. Cite TrustTrade and ContestTrade prominently and early; do not let a
     reviewer discover either one independently.

### Claim 2 — Calibration and Stability Evaluation of Heterogeneous Financial Agents

- **Existing similar work?** No direct collision, but dense partial
  overlap: The Confidence Dichotomy (2601.07264, mechanism-conditioned
  calibration, non-finance) and Replayable Financial Agents/DFAH
  (2601.15322, finance-domain stability/determinism, but LLM-only).
  Score: **5/10 (MEDIUM)**.
- **Biggest risk.** A reviewer cites DFAH for the stability half and The
  Confidence Dichotomy for the calibration-by-mechanism half, then asks
  "so what's new besides the dataset?"
- **How to avoid it.** Do not present this as two novel diagnostic
  methods. Position it explicitly as the **empirical motivation section
  for Claim 1's fusion design** — "naive per-adapter calibration hides a
  structural pattern that only appears when you condition on *how*
  confidence is computed and *whether it's reproducible*, and this pattern
  is what justifies calibration-aware, stability-aware fusion weights
  rather than a naive confidence-weighted ensemble." **Recommendation:
  fold into Claim 1 as a full section, not a standalone claim.**

### Claim 3 — Regime-Conditioned Reliability Audit

- **Existing similar work?** No direct hit on the exact question (does
  *reliability*, not accuracy/returns, vary by regime, across many
  independently-developed heterogeneous real systems). Closest: Conditional
  Adversarial Fragility (2512.19935) — regime-conditioned, but for
  adversarial robustness of one architecture, and it explicitly finds
  ordinary calibration is regime-*stable*, which a reviewer could
  (mis)cite as "this question is already answered, and the answer is no."
  Score: **6/10 (MEDIUM-HIGH)**.
- **Biggest risk.** A null result (no regime effect on reliability) reads
  as "we ran an ablation and found nothing" at a venue where reviewers
  expect a positive finding. Two independent search passes (Phase B and
  Phase C) converge on this being the load-bearing risk, distinct from a
  collision risk.
- **How to avoid it.** Two options, both compatible with the same
  underlying experiment:
  1. **Fold into Claims 1 and 4 as a regime-stratified ablation** (the
     project's working scoping call, confirmed by Phase C as correct — "if
     Claims 1 and 4 depend on reliability-aware fusion/routing,
     regime-stratified reliability is a natural supporting analysis").
  2. **Only if the finding is strong, well-powered, and reproducible**,
     consider releasing the ~26-system regime-stratified reliability
     benchmark itself as a standalone reusable artifact — this is the one
     path to standalone status a reviewer would accept, per Phase C.
  3. Position explicitly against Conditional Adversarial Fragility: "does
     the regime-dependence pattern established for adversarial robustness
     in one architecture *also* hold for ordinary calibration/hit-rate/
     contradiction metrics in a heterogeneous deployment" — report a null
     result as informative (e.g., "reliability degradation is
     regime-invariant across paradigms, which has direct implications for
     fusion/routing policy design"), not as a failed experiment.

### Claim 4 — Reliability-Aware Routing and Shadow Q4 Policy Construction

- **Existing similar work?** Yes, but with a confirmed, structural
  delta: FineFT (arXiv 2512.23773, confirmed ACM SIGKDD via Semantic
  Scholar, **not ICAIF**). Codex Phase C (thread
  `019f7b4a-1d93-7333-bb05-8c836c5c23e5`) scored this **7/10
  (MEDIUM-HIGH)**, the highest of the 5 claims, and stated it is "not
  obviously preempted by FineFT, MM-DREX, or Look-Ahead-Freedom."
- **Biggest risk.** Two distinct risks, per Phase C: (a) a reviewer
  dismisses the routing sub-claim as "standard dynamic ensemble
  selection / regime switching / mixture-of-experts" with the
  "independently-published systems" framing treated as an engineering
  detail rather than a contribution; (b) **this is the least-implemented
  of the 5 claims** — zero large-scale multi-regime routing experiment
  exists yet, so the novelty case is currently argument-only.
- **How to avoid it.**
  1. **Run the actual multi-baseline experiment** — fixed systems,
     equal-weight blend, rolling-performance selector, regime-only router,
     ideally an oracle upper bound, all under transaction costs and strict
     point-in-time splits — before resting the claim on the systems-framing
     argument alone. Non-optional per Phase C.
  2. **Lead with the shadow-policy sub-claim, not the routing sub-claim.**
     Phase C was explicit that combining one system's Q1/Q3
     selection-and-ranking with another system's Q4 risk-adjustment
     "is less obviously covered by FineFT/MM-DREX-style routing than the
     routing sub-claim is" — it is the stronger, more defensible half of
     the contribution, provided the Q1/Q3/Q4 decomposition is well-defined
     and causal rather than reading as post-hoc signal stacking.
  3. Frame the contribution as a **systems/infrastructure novelty as much
     as an algorithmic one**: routing across genuinely independent,
     externally-authored real projects under one shared causal
     point-in-time execution/constraint harness (`harness/q4_protocol.py`,
     `execution_engine.py`) is not something FineFT, MM-DREX, or any
     found paper does.

### Claim 5 — Contradiction-Aware Selective Prediction (Abstention)

- **Existing similar work?** Partially anticipated by ingredients (ensemble
  disagreement as reject signal, uncertainty-triggered no-trade, act-vs-
  defer policies) but not the exact combination. Closest: When Alpha
  Breaks (2603.13252) for evaluation philosophy; TrustTrade for the
  multi-agent framing; Conformal Social Choice (2604.07667) for the
  general "contradiction → abstain/escalate as distinct from fusion"
  mechanism pattern (zero finance/domain overlap). Score: **5/10
  (MEDIUM-LOW)**.
- **Biggest risk.** Both Phase B and Phase C agree this reads as a trivial
  special case of Claim 1's fusion formula (a zero-weight branch), not a
  standalone contribution, unless it has its own theory or materially
  different optimization target.
- **How to avoid it.** **Fold into Claim 1 as an ablation arm** ("fuse vs.
  abstain given the same diagnostic signal") — confirmed correct by Phase
  C ("I agree with folding it into claim 1... lets the paper ask a
  sharper question: given the same contradiction signal, when is it better
  to fuse versus step aside?"). The one empirical angle worth keeping
  prominent inside that ablation: that *structural cross-system
  contradiction* is a useful risk-reduction signal in its own right,
  distinct from ordinary single-model uncertainty/confidence/ensemble
  dispersion baselines — this is the specific comparison the ablation
  should be designed to demonstrate, per Phase C.

---

## Cross-claim synthesis: what survives as standalone vs. what folds in

| Claim | Score | Standalone-worthy? | Recommended role |
|---|---|---|---|
| 1 — Fusion | 6/10 MEDIUM | Yes, conditionally | Lead claim, contingent on TrustTrade baseline + lone-dissenter ablation |
| 2 — Calibration/stability | 5/10 MEDIUM | No | Diagnostic section inside Claim 1 |
| 3 — Regime-conditioned reliability | 6/10 MEDIUM-HIGH | Only as a reusable benchmark artifact | Regime-stratified ablation feeding Claims 1 & 4 (default); standalone only if released as a benchmark |
| 4 — Routing/shadow-Q4 | 7/10 MEDIUM-HIGH | Yes, conditionally | Second lead claim, contingent on multi-baseline experiment; lead with shadow-policy framing over routing framing |
| 5 — Abstention | 5/10 MEDIUM-LOW | No | Ablation arm inside Claim 1 ("fuse vs. abstain") |

**No claim scored below 5/10 or above 7/10.** All five sit in a narrow
MEDIUM band — this project's novelty is real but genuinely marginal, not a
clear "no one has done this" gap. Every claim's viability is conditional on
running specific, named baseline experiments, not on the framing argument
alone. This is the single most important message for `CLAIM_CANDIDATES.md`
and `ICAIF_POSITIONING_REPORT.md` to carry forward without softening.

## Standing terminology risk (applies across all claims)

Do not use the bare word "calibration" as a standalone headline term. Of 7
ICAIF 2023–2025 titles containing "calibrat-," 6/7 mean pricing/simulation
model parameter-fitting, not ML confidence calibration; TrustTrade itself
uses "calibrates" in a third, behavioral sense. Every instance must be
qualified on first use. See `LITERATURE_MAP.md` cross-cutting note.
