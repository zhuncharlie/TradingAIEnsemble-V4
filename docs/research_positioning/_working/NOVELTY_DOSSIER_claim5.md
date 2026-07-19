# Novelty Dossier — Claim 5: Contradiction-Aware Selective Prediction (Abstention)

## Proposed method
When cross-agent contradiction (e.g. one real system says BUY while another
flags HIGH_RISK on the same ticker/date) or high internal (intra-adapter,
cross-Q) contradiction is detected across the same 26-system,
paradigm-heterogeneous (6+ paradigms) deployment used in claims 1-4, the
decision-layer response is to **abstain, reduce position size, or increase
cash allocation** — rather than fusing the disagreeing signals into one
decision (which is what claim 1 does instead). Evaluated primarily on
whether this reduces drawdown/tail risk, even if it does not improve raw
return — a distinct decision philosophy (abstain vs. combine) from claim 1,
intended to be tested as an alternative response to the same underlying
diagnostic signal (contradiction + reliability), not as a component nested
inside claim 1's fusion formula.

## Core claims to check
1. Selective prediction / abstention triggered specifically by **cross-agent
   structural contradiction** (not just single-model predictive uncertainty,
   and not just verbalized-probability disagreement among near-identical
   LLM instances) across independently-published, paradigm-heterogeneous
   real systems (6+ paradigms: RL policies, LLM agents, factor/ranking
   models, portfolio optimizers, sentiment/NLP models, etc.).
2. Evaluating abstention primarily on risk-reduction (drawdown/tail risk)
   rather than accuracy/return, as the deliberate framing.
3. Positioning abstention and fusion (claim 1) as two competing, directly
   comparable decision philosophies for the same underlying diagnostic
   signal, rather than treating abstention as one component of a larger
   fusion formula (i.e., is it a distinct contribution or a zero-weight
   special case of claim 1's fusion weights?).
4. Scale: contradiction/abstention signal computed over ~26 real deployed
   systems (not 3-5 LLM instances of the same/similar base model debating
   each other).

## Candidate papers found (Phase B, this session — WebSearch + WebFetch
abstract verification + verify_papers.py pre-search check)

All 9 candidates below passed `verify_papers.py` (arXiv-resolved, method=arxiv,
confidence=high, hallucination_rate=0.0, pending_rate=0.0, verdict=PASS).

- **TrustTrade: Human-Inspired Selective Consensus Reduces Decision
  Uncertainty in LLM Trading Agents** (arXiv 2603.22567, 2026-03, Harvard /
  Harvard Business School / DGIST). Full abstract fetched and confirmed this
  session: TrustTrade "dynamically weight[s] signals based on... semantic
  and numerical agreement. Consistent signals are prioritized, while
  divergent, weakly grounded, or temporally inconsistent inputs are
  **selectively discounted**." No full-abstention / hold-cash mode
  documented in the abstract; framed entirely as continuous reweighting
  toward a "mid-risk, mid-return" calibration target, not a discrete
  abstain-vs-act decision. LLM-only (single paradigm — multiple LLM agent
  instances, not 6+ heterogeneous system types). Evaluated on
  "risk-return performance" broadly; abstract does not confirm drawdown/tail
  risk as a named, isolated metric (unconfirmed either way from abstract
  alone — would need full text). **Still the closest single paper across
  both claims 1 and 5, but the reweighting-only mechanism and single-paradigm
  scope are a real, confirmed delta from claim 5's full-abstention +
  6-paradigm-diagnostic framing.**
- **When Alpha Breaks: Two-Level Uncertainty for Safe Deployment of
  Cross-Sectional Stock Rankers** (arXiv 2603.13252, 2026-03). Full abstract
  fetched and confirmed this session: single-model (LightGBM ranker),
  abstention/exposure-reduction triggered by the model's **own internal
  epistemic uncertainty** (DEUP-derived e-hat), not cross-agent
  contradiction — confirmed not multi-agent. Confirmed uses drawdown/
  tail-risk framing explicitly ("epistemic tail-risk cap," "tail-risk
  guard") — closest precedent for the *evaluation philosophy* (risk-focused
  over return-focused) but not for the *trigger mechanism* (single-model
  vs. cross-system contradiction).
- **Trading via Selective Classification** (arXiv 2110.14914, 2021).
  Classic selective-classification-with-reject-option applied to intraday
  futures trading — single-model, no multi-agent contradiction signal.
  Establishes the general "selective classification -> trading strategy"
  pattern this claim would need to differentiate from by being
  contradiction-triggered and cross-system.
- **From Debate to Decision: Conformal Social Choice for Safe Multi-Agent
  Deliberation** (arXiv 2604.07667, 2026-04, AWS GenAI Innovation Center /
  HSBC Technology Center) — NEW this session, not in prior pass. Full
  abstract fetched and confirmed: converts multi-agent LLM debate into
  calibrated act-vs-escalate decisions via conformal prediction over
  verbalized probability distributions from 3 heterogeneous **LLM** agents
  (Claude Haiku, DeepSeek-R1, Qwen-3 32B). Confirmed general QA/reasoning
  domain only (8 MMLU-Pro domains) — **not finance, not trading, no
  drawdown/risk metric at all** (evaluated on coverage/accuracy of
  intercepted wrong-consensus cases). Structurally the closest *mechanism*
  analog (contradiction -> abstain/escalate as a distinct decision layer
  from consensus-fusion) but zero domain overlap and zero risk-metric
  overlap. Notable because one of the authors' affiliations (HSBC) signals
  finance-adjacent interest even though this specific paper doesn't apply
  it to markets — worth watching for a fast finance follow-up.
- **Budgeted Act-or-Defer Multi-Agent LLM Deliberation with Local
  Reliability Bounds** (arXiv 2606.29654, 2026-06, AWS GenAI Innovation
  Center / General Motors) — NEW this session. Act-or-defer (to human)
  policy gated by a KNN lower-confidence-bound on state-conditional
  correctness from debate-prefix embeddings; evaluated on 6 general
  reasoning benchmarks against 9 baselines (accuracy/automation-rate
  metrics). Not finance, not cross-system-contradiction in the sense of
  independently-published heterogeneous systems (it's homogeneous debate
  rounds), no drawdown/risk metric. Same family as Conformal Social Choice:
  general-purpose "when to trust multi-agent LLM debate" line of work
  that has NOT yet been applied to finance or to non-LLM heterogeneous
  systems.
- **FinCom: A Financial Multi-Agent Demo with Disagree-or-Commit
  Deliberation** (arXiv 2606.00939, 2026-06) — NEW this session. Financial
  multi-agent **committee** system (research/quant/risk-management
  role-specialized LLM agents) with a lightweight Disagree-or-Commit
  deliberation protocol for producing better analysis reports and
  supporting interactive committee chat. This is a report-quality /
  analysis-quality system, not a live trading decision or position-sizing
  policy — no abstain-vs-act trading decision, no backtested drawdown/
  return evaluation described. Confirms finance-multi-agent-deliberation is
  an active area in mid-2026 but this specific paper is not a collision on
  the position-sizing/abstention behavior claim 5 is making.
- **AgentAbstain: Do LLM Agents Know When Not to Act?** (arXiv 2607.10059,
  2026-07, UIUC) — NEW this session, published within days of this dossier's
  writing. First systematic benchmark for general **tool-using agent**
  abstention (263 paired tasks, 8 abstention-scenario taxonomy, 42
  environments, 17 frontier LLMs; best model <60% pairs correct). This is
  the closest *general* prior art for "abstention as first-class agent
  behavior," but it is a benchmark of single-agent tool-use task execution
  (ambiguity, conflicting constraints, tool failure) — not finance, not
  cross-agent contradiction across independently-built heterogeneous
  systems, not evaluated on portfolio risk/drawdown. Establishes that
  agent-abstention-as-a-first-class-capability is a live, contested 2026
  research direction in the general agents literature, which is useful
  context but not a direct collision.
- **Predictor-Rejector Multi-Class Abstention: Theoretical Analysis and
  Algorithms** (arXiv 2310.14772). General ML theory for abstention with a
  predictor-rejector pair — foundational abstention theory, not finance or
  multi-agent-specific, worth citing as theoretical grounding rather than a
  collision.
- **Online Conformal Abstention for Factuality Control Under Adversarial
  Bandit Feedback** (arXiv 2506.14067). Conformal abstention method, but for
  LLM factuality control, non-finance, non-multi-agent.

## Search coverage this session
WebSearch queries run (Phase B, this session): TrustTrade re-verification;
cross-agent contradiction + drawdown; multi-agent disagreement + hold cash +
selective prediction; the two newly surfaced deliberation papers by name;
large-scale (20+ system) heterogeneous trading ensembles with
fusion-vs-abstain framing; selective classification + conformal reject
option in finance; "abstain as first-class action" + multi-agent trading
design principles; LLM trading agents + heterogeneous divergent decisions +
drawdown. No paper was found — across either the prior WebSearch-only pass
or this session's expanded search — that triggers abstention specifically
from a **structural-contradiction detector spanning 6+ independently-built,
paradigm-heterogeneous real financial systems at ~26-system scale**, evaluated
primarily on drawdown/tail-risk rather than accuracy/return. The two closest
mechanism analogs (Conformal Social Choice, Budgeted Act-or-Defer) are both
non-finance, both homogeneous-LLM-debate rather than heterogeneous-real-system,
and both evaluated on accuracy/coverage rather than portfolio risk.

## Questions for the reviewer
1. Is abstention/position-reduction triggered by detected **cross-agent
   structural contradiction** (rather than single-model uncertainty, and
   rather than verbalized-probability disagreement among near-identical LLM
   debate agents) already covered by TrustTrade, "When Alpha Breaks,"
   Conformal Social Choice (2604.07667), Budgeted Act-or-Defer (2606.29654),
   FinCom (2606.00939), AgentAbstain (2607.10059), or any other paper you
   can find?
2. Given claim 1 (fusion) and claim 5 (abstention) share the same underlying
   diagnostic signal (calibration reliability + contradiction detection),
   is it defensible to present them as two separate, directly-competing
   contributions, or would a reviewer see claim 5 as a trivial special case
   of claim 1 (i.e., "fusion with a zero-weight option") not worth a
   separate claim? Specifically: does the existence of Conformal Social
   Choice's "act-vs-escalate" framing (a non-finance precedent for treating
   consensus-fusion and abstain/escalate as two distinct decision layers
   fed by the same diagnostic signal) strengthen or weaken the case that
   claim 5 deserves standalone status in the finance/heterogeneous-real-
   system setting?
3. What is the single closest prior work, and what precisely is the delta?
4. Is "abstention reduces drawdown/tail risk even without improving return"
   itself a novel empirical claim in this setting, or an expected/obvious
   result not worth highlighting as a contribution on its own?
5. This project's working assumption is to fold claim 5 into claim 1 as an
   ablation arm ("fuse vs. abstain given the same diagnostic signal") rather
   than a standalone 5th claim. Given everything above, confirm or challenge
   that scoping call, and justify.

## Phase C — Codex MCP cross-model verification

**Status: completed, real `mcp__codex__codex` call, `sandbox: read-only`,
`model_reasoning_effort: high`, threadId `019f7b50-cc8d-75b0-b2b4-920684cd0088`.**

**Reviewer response (verbatim):**
> 1. **Not fully covered, but partially anticipated.** The exact combination
> is not covered by the listed work: structural contradiction across many
> independently built, paradigm-heterogeneous finance systems, with
> abstention/de-risking evaluated on drawdown and tail risk. However, the
> ingredients are individually familiar: ensemble disagreement as a reject
> signal, uncertainty-triggered no-trade/exposure reduction, and act-vs-defer
> policies.
>
> 2. **Standalone positioning is weak.** If claim 1 already uses the same
> contradiction/reliability diagnostic for fusion, reviewers may reasonably
> view abstention as a limiting case: assign zero weight, move to cash, or
> shrink exposure when contradiction exceeds a threshold. It is defensible as
> a **comparison policy** or **decision-layer variant**, but not as a
> separate directly competing contribution unless it has its own theory,
> calibration rule, or materially different optimization target.
>
> 3. **Closest prior work: _When Alpha Breaks_.** Delta: it already has the
> finance abstention/exposure-reduction framing and explicitly targets
> drawdown/tail-risk reduction. The proposed claim differs mainly in the
> **trigger**: cross-system structural contradiction across heterogeneous
> deployed systems, rather than single-model epistemic uncertainty.
> TrustTrade is closer to the multi-agent setting, but its delta is larger
> because it is LLM-homogeneous and reweighting/fusion-oriented rather than
> abstention-oriented.
>
> 4. **The empirical claim is not novel by itself.** "Abstention reduces
> drawdown/tail risk even without improving return" is expected in trading if
> abstention reduces exposure during uncertain or conflicted regimes. It is
> worth reporting, but not as the headline novelty. The stronger claim is
> that **structural contradiction is a useful risk signal beyond ordinary
> uncertainty, confidence, or ensemble dispersion baselines**.
>
> 5. **I agree with folding it into claim 1.** The cleanest scoping is: one
> core contribution is the contradiction/reliability diagnostic over
> heterogeneous financial agents; downstream policies include fusion,
> abstention, and exposure scaling. Presenting abstention as an ablation arm
> avoids overclaiming and lets the paper ask a sharper question: given the
> same contradiction signal, when is it better to fuse versus step aside?

**Novelty score: 5/10. Recommendation: FOLD INTO CLAIM 1.**

## Final verdict

**Confirmed — do not promote to standalone paper.** Both Phase B (dense,
partially-anticipated prior art: When Alpha Breaks for evaluation
philosophy, TrustTrade for multi-agent framing, Conformal Social Choice /
Budgeted Act-or-Defer for the general act-vs-abstain mechanism pattern) and
Phase C (independent Codex review) converge: fold claim 5 into claim 1 as a
"fuse vs. abstain given the same diagnostic signal" ablation arm, framed
around the sharper empirical question of when structural contradiction
should trigger fusion vs. de-risking — not as a standalone 5th claim. The
one empirical angle worth keeping prominent (per Phase C point 4): that
*structural cross-system contradiction* is a useful risk signal in its own
right, distinct from ordinary single-model uncertainty/confidence/ensemble
dispersion — this is the specific comparison this ablation should be
designed to demonstrate.
