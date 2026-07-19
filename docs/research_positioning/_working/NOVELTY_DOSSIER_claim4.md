# Novelty Dossier — Claim 4: Reliability-Aware Routing and Shadow Q4 Policy Construction

## Proposed method
Using a newly-built causal stepwise execution harness (enforces point-in-time
information-cutoff causality and portfolio constraints — long-only,
max-weight, gross/net exposure, leverage, turnover — identically across
mechanistically different real policy systems: one genuinely-online
adaptive-weight learner, one rolling walk-forward re-optimizer, six
frozen-then-inferred learned-policy networks, one static single-shot
allocator), build an **evaluation-layer** router/shadow-policy construction
method (explicitly not a new adapter, not touching the shared schema) that
either (a) selects which underlying real system's decision to execute at
each step, conditioned on market regime and/or each system's own rolling
realized validation performance, or (b) constructs a "shadow" portfolio by
combining one system's asset *selection*, another's *ranking* signal, and a
third's *risk adjustment* into a single synthetic policy — compared against
each fixed underlying system individually and a naive equal-weight blend of
all of them.

## Core claims to check
1. A router that selects among **independently-developed, real, published**
   policy systems (not variants of one trained model, not one system's own
   internal strategy pool) at each causal decision step, using a harness that
   enforces identical point-in-time causality/constraints across all of them.
2. "Shadow policy" construction that synthesizes one system's Q1/Q3
   selection-and-ranking output with another system's Q4 risk-adjustment
   output into a new synthetic decision trajectory, evaluated causally.
3. The system-of-systems framing itself: routing/blending across
   *independently-authored real upstream projects*, as opposed to training
   one model with regime features or building one strategy pool internally.

## Candidate papers found (Phase B, WebSearch this session + direct-read follow-up)
- **FineFT: Efficient and Risk-Aware Ensemble Reinforcement Learning for
  Futures Trading** (arXiv 2512.23773, 2025-12). **Full abstract confirmed
  via direct WebFetch of arxiv.org/abs/2512.23773 this session (not
  synthesis).** Verbatim from the fetched abstract: "we propose the
  Efficient and Risk-Aware Ensemble Reinforcement Learning for Futures
  Trading (FineFT), a novel three-stage ensemble RL framework... In stage I,
  ensemble Q learners are selectively updated by ensemble TD errors... In
  stage II, we filter the Q-learners based on their profitabilities and
  train VAEs on market states to identify the capability boundaries of the
  learners. In stage III, we choose from the filtered ensemble and a
  conservative policy, guided by trained VAEs, to maintain profitability and
  mitigate risk with new market states."
  **Confirmed via direct read:**
  (a) ensemble composition — "ensemble Q learners," i.e. the entire pool is
  **self-trained within one RL framework by the same authors**; the fetched
  content contains no mention of independently-published, cross-paradigm,
  or externally-authored systems being routed among;
  (b) routing mechanism — explicitly "guided by trained VAEs" on market
  state, i.e. VAE-encoded market-state similarity/capability-boundary
  detection, NOT an agent track-record/calibration-reliability signal;
  (c) no mention anywhere in the fetched abstract of a point-in-time
  causality-enforcement harness or execution-constraint layer applied
  identically across systems.
  **Verdict on differentiators**: both (a) and (b) hold up after direct
  primary-source verification (WebFetch of the arXiv abstract, not
  WebSearch synthesis). This remains the closest single paper to the
  routing half of Claim 4, and the delta is now confirmed rather than
  inferred: FineFT routes within one self-trained homogeneous pool by
  market-state similarity; Claim 4 routes across independently-published,
  mechanistically different real systems by measured reliability, under an
  explicit causal point-in-time execution/constraint harness.
- **Deep Reinforcement Learning for Reliability Based Bi-Objective Portfolio
  Optimization** (arXiv 2607.06610). "Reliability" here appears to mean a
  risk/probabilistic-constraint objective inside one RL training procedure
  (bi-objective optimization), not agent-selection routing across multiple
  independent systems — needs a closer read to confirm this reading is
  correct, flagged as `[NEEDS FULL-TEXT CHECK]`.
- **MARS-DA: A Hierarchical Reinforcement Learning Framework for Risk-Aware
  Multi-Agent Bidding in Power Grids** (arXiv 2605.03142). Different domain
  (power-grid bidding), hierarchical RL agents, not directly comparable but
  shares "risk-aware hierarchical agent selection" vocabulary.
- **Additional Phase B refresh this session (WebSearch, 2026 H1 sweep)**:
  two new candidates surfaced and directly WebFetched to rule out as closer
  prior art than FineFT:
  - **MM-DREX: Multimodal-Driven Dynamic Routing of LLM Experts for
    Financial Trading** (arXiv 2509.05080). Direct WebFetch confirms the
    routed "experts" (trend/reversal/breakout/positioning) are "purpose-
    built sub-strategies within the unified system," trained jointly via an
    "SFT-RL hybrid training paradigm" — same monolithic-framework pattern
    as FineFT (homogeneous internal components, not independent real
    systems), routed by a VLM chart-pattern signal, not track-record
    reliability. Does not displace FineFT.
  - **Look-Ahead-Freedom as Temporal Non-Interference** (arXiv 2607.04958).
    Direct WebFetch confirms this is a formal verification/type-system
    contribution for detecting look-ahead bias in a *single* backtesting
    pipeline — no routing, no ensembling, no multi-system orchestration.
    Not competing prior art for the routing claim, but worth citing as
    adjacent methodology reinforcing why causal point-in-time correctness
    matters as an evaluation-harness property.
- No paper found in this search (now including direct-read verification of
  the two closest candidates) that routes/blends across independently-
  published real financial-AI systems spanning multiple *paradigms* (RL +
  LLM + GP + GBM) under one shared causal-execution/constraint harness.

## Questions for the reviewer
1. Is routing/blending across multiple *independently-published, real*
   financial-AI systems (not one system's internal strategy pool, not one
   model retrained with regime features) already covered by FineFT or any
   other paper you can find?
2. Is the specific mechanism — a point-in-time-causal, constraint-enforcing
   execution harness that multiple mechanistically different real policy
   systems are driven through identically, with routing decisions made by
   an evaluation-layer component outside any of the systems themselves —
   novel as a systems contribution, independent of whether the empirical
   routing result itself is positive?
3. What is the single closest prior work, and what precisely is the delta?
4. This is explicitly the least-implemented of the 5 claims (the enabling
   harness exists and is tested, but no large-scale multi-regime routing
   experiment has been run yet). Given that, is the *idea* itself worth the
   implementation risk, or does the novelty evaporate once implemented
   because the result is likely to look too similar to known
   regime-switching/ensemble-selection results regardless of the
   cross-system framing?

## Phase C — Codex MCP cross-model verification

**Status: completed successfully this session, real `mcp__codex__codex`
call against this dossier's current content.** Two earlier attempts with an
explicit `model` override failed deterministically before this succeeded:
`model: "gpt-5.6-sol"` → `400 invalid_request_error: "The 'gpt-5.6-sol'
model requires a newer version of Codex"`; `model: "gpt-5.2"` → `400
invalid_request_error: "The 'gpt-5.2' model is not supported when using
Codex with a ChatGPT account"`. Both are explicit, deterministic
model-string rejections from the backend, not the transient/flaky 3/3
connectivity failures flagged as a known false-negative pattern in a prior
session — no blind retry-in-a-loop was applied; instead the model override
was dropped after the second distinct rejection, letting the Codex MCP
server use its own configured default model, which succeeded on the first
try (`sandbox: read-only`, `model_reasoning_effort: high`, thread id
`019f7b4a-1d93-7333-bb05-8c836c5c23e5`). As with claim 1's dossier, this
session did not learn the exact default model string Codex substituted
(not echoed in the response) — flagged as a config-drift item for ARIS
maintainers, since SKILL.md's `REVIEWER_MODEL = gpt-5.6-sol` constant is
currently unreachable from this account/CLI.

**Reviewer response (verbatim, condensed to the 5 requested points):**
> 1. **Novelty / Closest Prior.** Yes, conditionally novel, but not as a
> pure routing algorithm. The novelty is the combination: routing across
> independently-published, mechanistically different financial-AI systems,
> under one causal point-in-time execution and constraint harness. The
> closest prior work is FineFT... FineFT's pool is internally self-trained
> homogeneous Q-learners, not independently-published cross-paradigm
> systems, and it does not claim a shared causal execution harness across
> external systems.
>
> 2. **FineFT Differentiation.** Yes, the differentiation is sufficient,
> assuming the dossier's direct-read confirmations are accurate. FineFT:
> self-trained RL learner pool, VAE market-state routing, one framework.
> Claim 4: independently-authored systems across paradigms, evaluation-layer
> routing, realized reliability/performance signals, shared causal
> point-in-time harness, uniform constraints. MM-DREX does not erase the
> distinction because its routed experts are also internal purpose-built
> sub-strategies in one unified system. Look-Ahead-Freedom is adjacent for
> causality, but not routing or multi-system orchestration. Those two
> exclusions strengthen the claim. The caveat: FineFT was confirmed from
> the abstract, not necessarily full paper. A reviewer could still ask
> whether FineFT's implementation details include broader
> ensemble-selection machinery that weakens the contrast. Before
> submission, the FineFT full text should be read.
>
> 3. **Biggest Novelty Risk / Shadow Policy.** The biggest ICAIF reviewer
> risk is that this gets dismissed as standard dynamic ensemble selection /
> regime switching / mixture-of-experts, with "independently-published
> systems" treated as an engineering detail rather than a research
> contribution. A skeptical reviewer may say: "You are just selecting among
> strategies based on rolling validation performance under a backtest
> harness." The defense must be that the paper is not claiming a new
> generic router; it is claiming a system-of-systems financial-AI
> evaluation and execution construction where real external systems are
> made causally comparable and routable without retraining or schema
> mutation. The shadow policy sub-claim is more novel on its own than the
> routing sub-claim, but also riskier. Recombining one system's
> selection/ranking with another's risk adjustment across independent
> systems is less obviously covered by FineFT/MM-DREX-style routing.
> However, it needs a very careful framing: if it looks like arbitrary
> post-hoc signal stacking, reviewers may call it underprincipled. If the
> Q1/Q3/Q4 decomposition is well-defined, causal, and produces a real
> executable trajectory, it is a stronger standalone novelty angle.
>
> 4. **Worth Implementation Risk?** Yes, but only with caution. This is
> worth implementing if the paper can run a serious experiment against hard
> baselines: best fixed system, equal-weight blend, rolling-performance
> selector, regime-only router, maybe oracle upper bound, with transaction
> costs and strict point-in-time splits. If the result is weak or only
> marginally better than naive blending, the novelty will lean too heavily
> on systems framing. But if shadow recombination or reliability routing
> beats fixed systems under causal constraints, the claim becomes much more
> defensible.
>
> 5. **Score / Recommendation.** Novelty score: 7/10. Recommendation:
> PROCEED WITH CAUTION. The idea is not obviously preempted by FineFT,
> MM-DREX, or Look-Ahead-Freedom. The routing component alone is
> incremental-adjacent; the cross-system causal harness plus shadow policy
> construction is the stronger novelty package. The main risk is empirical
> and rhetorical: without a completed experiment, reviewers may see it as a
> clever backtesting orchestration layer rather than a new financial-AI
> method.

## Final novelty verdict for CLAIM_CANDIDATES.md / NOVELTY_AUDIT.md
**MEDIUM-HIGH.** Score: 7/10. Recommendation: **PROCEED WITH CAUTION**, with
two conditions the reviewer treated as necessary, not optional: (1) run the
actual multi-baseline experiment (fixed systems, equal-weight blend,
rolling-performance selector, regime-only router, ideally an oracle upper
bound, all under transaction costs and strict point-in-time splits) rather
than resting the claim on the systems-framing argument alone; (2) frame the
shadow-policy (cross-system Q1/Q3 selection+ranking recombined with a
different system's Q4 risk adjustment) sub-claim as the stronger, more
defensible half of the contribution — it is less obviously covered by
FineFT/MM-DREX-style routing than the routing sub-claim is, but needs the
Q1/Q3/Q4 decomposition to be well-defined and causal, not read as post-hoc
signal stacking. Confidence in this verdict: HIGH — FineFT's mechanism was
confirmed via direct WebFetch of the arXiv abstract (verbatim quote
obtained) rather than inherited from WebSearch synthesis, two additional
candidates (MM-DREX, Look-Ahead-Freedom) were also directly WebFetched and
ruled out, and the Phase C verdict is a real, independently-reasoned Codex
MCP response, not a placeholder. One residual gap the reviewer itself
flagged: FineFT was only confirmed from its abstract, not full text — a
full-text read of FineFT before submission would further de-risk this
claim.
