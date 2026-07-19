# Novelty Dossier — Claim 2: Calibration and Stability Evaluation of Heterogeneous Financial Agents

Status: Phase A + Phase B (fresh, this session) complete. This file is the
input artifact for Phase C (Codex MCP cross-model review).

## Proposed method

Across 26 real financial AI systems in the `trading-ai-ensemble` harness
(4 capability layers: Q1=Action, Q2=State/Sentiment/Context, Q3=Signal/Alpha,
Q4=Policy), "confidence"/"strength" fields are computed via at least 6
mutually incompatible mechanisms:

1. LLM self-report on a 0-100 scale divided by 100
2. hardcoded action -> confidence lookup tables
3. 1 - minus cross-model-prediction-dispersion
4. cross-sectional percentile distance from median
5. internal 0-10 score distance from midpoint
6. static training-time IC (information coefficient) correlation

Two combined proposals:

**(a) Confidence-kind-conditioned calibration.** Group calibration-error
analysis by the *mechanism category itself* — using an open,
schema-native confidence-kind taxonomy already present in the project's own
CONTRACT (PROBABILITY / SELF_REPORTED / MODEL_MARGIN / SCORE_NORMALIZED /
ENTROPY_DERIVED / HEURISTIC) — rather than by adapter identity or model
identity. Test whether Q1 confidence / Q3 signal strength actually predicts
future 1d/5d/20d returns, broken out by *which kind* of confidence-producing
mechanism each adapter paradigm uses, across all 26 real adapters.

**(b) Repeated-identical-query stability/variance diagnostic.** Call each
of the 26 systems K times on frozen identical (ticker, date) inputs and
measure output variance: action-flip rate, weight-vector distance between
repeated calls, etc. Purpose: separate "miscalibrated but deterministic"
agents from "non-deterministic" agents. This is motivated by a real defect
already found by manual source-code reading in one adapter in this project:
unseeded per-call model retraining causing the *same* frozen query to return
different predictions on different calls.

Combined, across 26 heterogeneous **real, actually-deployed-here** adapters
spanning 6+ paradigms (LLM, RL, genetic programming, GBM, rule-based,
classical portfolio optimization).

## Core claims to check

1. Grouping calibration-error analysis by an open, schema-native
   confidence-mechanism taxonomy (not just per-model/per-adapter identity)
   across a large (~26), paradigm-diverse *real-system* deployment, testing
   against real forward 1d/5d/20d returns.
2. A repeated-identical-query stability/variance diagnostic specifically
   designed to separate non-determinism from miscalibration, applied across
   heterogeneous, non-LLM-included financial AI systems (i.e., not just
   LLM agents — also RL, GP, GBM, rule-based, optimizer paradigms).
3. The *combination* of (1) and (2) as a joint diagnostic battery, and the
   *cross-paradigm empirical pattern* this combination would reveal (e.g.,
   "SELF_REPORTED confidence from LLM adapters is uncalibrated AND high
   variance," vs. "static IC-derived confidence is well-calibrated but
   the underlying model is itself non-deterministic due to unseeded
   retraining" — a genuinely different failure mode per mechanism kind).

## Phase B — Literature search (this session, fresh; supersedes prior WebSearch-only pass)

All arXiv IDs below were passed through `verify_papers.py`
(3-layer arXiv/CrossRef/Semantic Scholar cross-check) — verdict **PASS**,
hallucination_rate 0.0, all 7 IDs resolved with high confidence via direct
arXiv lookup. No entries required `[UNVERIFIED]` tagging.

### Previously known (re-verified this session)

- **The Confidence Dichotomy: Analyzing and Mitigating Miscalibration in
  Tool-Use Agents** (arXiv 2601.07264, Xuan et al., 2026-01; accepted
  ACL 2026 long paper, `2026.acl-long.520`). Re-verified: finds a
  *mechanism-conditioned* calibration effect — Evidence tools (e.g. web
  search) induce systematic overconfidence, Verification tools (e.g. code
  interpreters) improve calibration — and proposes Calibration Agentic RL
  (CAR) to fix it. This is the closest conceptual precedent for "condition
  calibration analysis on mechanism/tool category rather than model
  identity." Confirmed: single paradigm (LLM tool-use agents only),
  non-finance, no repeated-query stability angle, and the taxonomy axis is
  "tool type" not "confidence production mechanism" — related but distinct
  axis of conditioning.
- **When Agents Disagree With Themselves: Measuring Behavioral Consistency
  in LLM-Based Agents** (arXiv 2602.11619, 2026-02). Re-verified: 3,000
  agent runs, 3 models, HotpotQA-style ReAct tasks; measures unique
  action-sequence count per 10 identical-input runs; finds consistency is
  strongly predictive of accuracy (69% of divergence at first tool call).
  Confirmed: closest single-agent methodological precedent for the
  stability-variance idea, but non-finance, single-paradigm (LLM ReAct
  only, no RL/GP/GBM/rule-based), and measures *within-one-agent*
  self-consistency on a QA task, not *across heterogeneous systems'*
  numeric-output stability (action-flip / weight-vector distance) on
  trading decisions.

### New this session (not found or not surfaced in prior pass — material to the verdict)

- **Replayable Financial Agents: A Determinism-Faithfulness Assurance
  Harness for Tool-Using LLM Agents** (arXiv 2601.15322, Khatchadourian,
  2026-01, rev. 2026-03). **Closest new collision candidate.** Finance-
  specific, explicitly measures decision determinism via repeated-input
  replay across 4,700+ agentic runs (7 models, 4 providers, 3 financial
  benchmarks, T=0.0), and reports the headline empirical finding that
  decision determinism and task accuracy are *not* detectably correlated
  (r=-0.11, 95% CI [-0.49, 0.31]) — i.e., models can be deterministic but
  inaccurate, or accurate but non-deterministic. This is structurally very
  close to proposal (b) (separating "miscalibrated" from "non-
  deterministic") and even reaches a similar-flavored conclusion in a
  finance setting. Key differences: (i) single paradigm — tool-using LLM
  agents only, no RL/GP/GBM/rule-based/classical-optimizer adapters;
  (ii) measures determinism vs. *task accuracy*, not determinism vs.
  *calibration* specifically, and has no confidence-mechanism-kind
  taxonomy at all; (iii) evaluates on benchmark QA/classification-style
  financial tasks, not real deployed trading-signal adapters against
  forward market returns. This paper is evidence that "financial +
  determinism-vs-accuracy decorrelation" is no longer an open finding in
  general — a reviewer would very likely cite this paper. It does *not*
  cover cross-paradigm adapters or confidence-kind-conditioned calibration
  against forward returns, so it narrows rather than eliminates novelty.
- **From Accuracy to Auditability: A Survey of Determinism in Financial AI
  Systems** (arXiv 2605.23955, Zhou et al./Amazon, 2026-05). Survey +
  first-party experiments covering reproducibility failures across three
  *modalities* (tabular models, graph networks, LLM agentic workflows) in
  regulated finance (credit risk, fraud, AML) — explanation-rank
  instability, GNN prediction flip rates, LLM trajectory drift. This is
  the broadest cross-modality determinism survey found and functionally
  adjacent to proposal (b), but: (i) not trading/alpha-signal focused
  (credit/fraud/AML, not price-prediction or portfolio actions);
  (ii) no confidence-calibration-vs-forward-returns angle at all;
  (iii) does not use a shared, harness-level repeated-query diagnostic
  applied uniformly across many real deployed systems — it's a survey plus
  three separate first-party experiments per modality. Raises the bar
  (this exact "survey the field" framing is taken) but does not collide
  directly with the trading-focused, calibration-plus-stability combined
  battery.
- **FinPersona-Bench: A Benchmark for Longitudinal Psychometric Stability
  of Autonomous Financial Agents** (arXiv 2606.31522, 2026-06). Measures
  a different kind of "stability" — behavioral-mandate drift over long
  horizons ("Mandate Salience Decay") in a synthetic market, 18 LLMs only.
  Not a collision: different notion of stability (long-horizon mandate
  adherence, not repeated-identical-query output variance), single
  paradigm (LLM), synthetic market not real adapters.
- **Counterfactual Graph for Multi-Agent LLM Calibration / CAGE-CAL**
  (arXiv 2605.30653, 2026-05). Multi-agent LLM calibration conditioned on
  *communication topology* (diversity-induced under-confidence vs.
  communication-induced over-confidence), for heterogeneous *panels of
  LLMs* with different knowledge boundaries. Conceptually adjacent
  ("heterogeneous agent calibration" is explicitly named as underexplored
  by this paper's own framing) but the heterogeneity axis is "different
  LLMs in a voting panel," not "different algorithmic paradigms with
  structurally different confidence-production mechanisms." No finance
  focus, no stability/repeated-query angle, no real trading adapters.
- **Agentic Confidence Calibration** (arXiv 2601.15778, 2026-01). Holistic
  trajectory calibration for multi-step LLM agents. Single-paradigm
  (LLM), general-agent, non-finance. Re-confirmed as before: not a
  collision, background-adjacent only.

### Net effect of fresh Phase B on prior verdict

The prior pass's MEDIUM verdict undersold the maturity of the *financial +
determinism* sub-literature specifically: "Replayable Financial Agents"
(2601.15322) already delivers a finance-domain, repeated-input,
determinism-vs-accuracy decorrelation result with real empirical scale
(4,700+ runs). A reviewer will very plausibly cite it as "this has been
done in finance already." However, it is LLM-only and accuracy-conditioned,
not cross-paradigm and not calibration-conditioned — so proposal (b) alone,
against this specific paper, has a narrower but still real delta: (i) cross-
paradigm (RL/GP/GBM/rule-based/optimizers, not just LLM tool-agents), and
(ii) paired with the confidence-kind calibration axis rather than raw task
accuracy. Proposal (a) remains without a direct single-paper collision
after this search pass; CAGE-CAL and Confidence Dichotomy are the nearest
neighbors on the "condition calibration by mechanism/category" axis but
neither is finance, cross-paradigm, or forward-return-conditioned.

## Questions for the reviewer (Phase C)

1. Given the newly found "Replayable Financial Agents" (arXiv 2601.15322,
   finance-domain, determinism vs. accuracy decorrelation, 4,700+ runs) —
   does this paper materially collide with proposal (b) (the repeated-
   query stability diagnostic)? Is "cross-paradigm instead of LLM-only,
   and calibration-conditioned instead of accuracy-conditioned" a
   sufficient delta, or is this now LOW novelty for the stability half
   specifically?
2. Is grouping calibration behavior by an open confidence-mechanism
   taxonomy (rather than by model/adapter identity or by tool-type as in
   the Confidence Dichotomy paper) already a known technique, inside or
   outside finance? Does applying it to a large real cross-paradigm
   financial-AI deployment, tested against real forward 1d/5d/20d returns,
   still carry a delta after this search?
3. Is the *combination* of (a) and (b) — confidence-kind-conditioned
   calibration AND repeated-query stability, run as one joint diagnostic
   battery on the same 26 real cross-paradigm systems — meaningfully more
   novel than either half alone? Or is "combine two known diagnostics on a
   new dataset" not a real contribution by itself?
4. Overall: is this closer to "a legitimate empirical audit paper with a
   modest but real methodological contribution" or "just measuring known
   things (calibration-by-category is known from Confidence Dichotomy /
   CAGE-CAL; stability-vs-accuracy-in-finance is known from Replayable
   Financial Agents) on a new dataset"? Be blunt about which, and say what
   the SPECIFIC surprising empirical finding would need to be to justify
   this as a standalone contribution (not just "everything's
   miscalibrated" — that's explicitly ruled out as insufficient).
5. What would a reviewer cite as the single closest paper overall, and
   what is the precise one-sentence delta this project would need to
   defend?

## Scoping question (also for Phase C — separate from novelty per se)

This project already has a separate Claim 1 about ensemble/fusion
combination across the same 26 real adapters (i.e., how to combine
heterogeneous Q1/Q3 outputs into a single trading decision). This project
currently treats Claim 2 (calibration + stability diagnostics) as a
*probable candidate to fold into Claim 1* as a diagnostic/motivating
section, rather than standing alone as its own paper/claim.

Please argue both sides and give a recommendation:

- **Standalone case**: Claim 2's contribution is a measurement/audit
  methodology (the taxonomy-conditioned calibration analysis + the
  stability diagnostic), which is orthogonal to *how* you fuse signals
  (Claim 1). A standalone paper can go deep on the diagnostic methodology,
  present the full calibration-by-mechanism-kind breakdown, and the
  stability/variance analysis, without being constrained by Claim 1's
  fusion-method framing or page budget.
- **Fold-in case**: Fusion (Claim 1) inherently needs to justify *why*
  naive equal-weight or naive confidence-weighted fusion is wrong — the
  calibration-by-mechanism finding is precisely the motivating diagnostic
  for why fusion needs to be calibration-aware, and the stability finding
  is precisely why fusion needs to filter/downweight non-deterministic
  adapters. Presenting them together lets Claim 1 use Claim 2's findings
  as direct justification for its design choices, and avoids two thin
  papers sharing one dataset and 26 real adapters (self-plagiarism /
  salami-slicing risk), especially since neither diagnostic alone survived
  this Phase B pass with strong stand-alone novelty (see Q1 and Q4 above).

Please weigh in on which framing is more defensible for a reviewer, and
whether there's a middle path (e.g., Claim 2 as a full section within
Claim 1's paper vs. a short separate workshop-scale paper vs. a full
standalone venue paper).

---

## Phase C — Codex MCP cross-model review (this session)

Reviewer: Codex MCP (`mcp__codex__codex`), reasoning effort `xhigh`,
sandbox `read-only`, cwd = repo root. threadId
`019f7b48-efb8-7c82-b2b4-2e84e838b9d8`.

**Attempt 1 (failed, retried per protocol):** explicit `model:
"gpt-5.6-sol"` override was rejected by the Codex backend — HTTP 400
`invalid_request_error`: *"The 'gpt-5.6-sol' model requires a newer version
of Codex. Please upgrade to the latest app or CLI and try again."* Traced
as `--status error` at `.aris/traces/novelty-check/2026-07-19_run01/004-claim2-phase-c-review`.

**Attempt 2 (succeeded):** identical prompt, same `xhigh` effort and
`read-only` sandbox, `model` field omitted so the Codex MCP backend
resolved its own default rather than the rejected explicit string. Full
review returned. Traced as `--status fallback_used` at
`.aris/traces/novelty-check/2026-07-19_run01/005-claim2-phase-c-review`.

### Reviewer verdict table

| Piece | Novelty | Blunt take |
|---|---:|---|
| Proposal (a): confidence-kind-conditioned calibration | **MEDIUM** | Real delta, but only if the result is by mechanism kind and survives adapter/paradigm/horizon controls. Otherwise it is just stratified calibration. |
| Proposal (b): repeated-identical-query stability | **LOW** | Materially collided. Repeated replay/stability is now known in finance LLM agents and in LLM-agent uncertainty/calibration work. Cross-paradigm trading adapters are a useful empirical extension, not strong method novelty. |
| Combination | **MEDIUM** | The joint 2D diagnostic battery is defensible as a modest empirical-audit contribution, not a high-novelty methods claim. |

### Reviewer answers (Q1-Q5)

1. **Yes, "Replayable Financial Agents" (arXiv 2601.15322) materially
   collides with proposal (b).** Already has finance-domain repeated-input
   replay, decision determinism, 4,700+ runs, and a determinism-vs-accuracy
   separation claim. Remaining delta is real but narrow: cross-paradigm
   (not just LLM tool-agents), trading-signal/portfolio-output oriented,
   and calibration-conditioned rather than benchmark-accuracy/faithfulness
   conditioned. Not enough for standalone stability-method novelty — enough
   for a Claim 1 diagnostic section.
2. **Calibration-by-category is known in principle** (classic calibration,
   subgroup/multicalibration, and the tool-type-conditioned Confidence
   Dichotomy paper already establish "condition calibration on meaningful
   strata"). The delta here is the specific schema-native confidence-kind
   axis plus real forward 1d/5d/20d trading returns across heterogeneous
   real adapters — reviewer scores this **MEDIUM, not HIGH**.
3. **The combination is more novel than either half alone, but only if it
   produces interaction findings** — e.g., stable-but-miscalibrated vs.
   calibrated-but-nondeterministic vs. high-confidence/high-variance
   adapters, and those distinctions changing downstream fusion decisions.
   "We ran ECE by kind and also ran K replays" alone is not sufficient.
4. **Closer to a legitimate empirical audit paper with a modest method
   contribution than a strong standalone method paper.** The needed
   surprising finding: confidence kind predicts calibration error better
   than adapter/model identity; repeated-query variance explains failures
   calibration misses; and using both signals changes downstream fusion
   performance/risk vs. naive baselines (confidence-weighted, majority
   vote, agreement-weighted). "Everything is miscalibrated" is explicitly
   table stakes, not a sellable result.
5. **Closest single paper overall: "Replayable Financial Agents"**
   (arXiv 2601.15322). One-sentence delta to defend: *"Unlike DFAH's
   LLM-only financial replay audit measuring determinism against task
   accuracy/faithfulness, this project jointly measures confidence-kind-
   conditioned calibration against realized 1d/5d/20d market returns and
   repeated-query output stability across LLM, RL, GP, GBM, rule-based,
   and optimizer adapters in one deployed trading harness."*

**Reviewer flag on 2602.11619:** per the reviewer, a later revision of
"When Agents Disagree With Themselves" (dated by the reviewer as revised
2026-07-15, reporting ~8,000 runs and framing repeated-run consistency
explicitly as an uncertainty/calibration signal) further weakens proposal
(b)'s standalone novelty beyond what the original Phase B pass captured.
This specific revision-date/run-count claim was not independently
re-verified via `verify_papers.py` in this session (the tool checks
paper *existence*, not version-level content claims) — treat as
reviewer-asserted and flag for a follow-up spot-check before citing the
8,000-run figure in any written paper.

### Reviewer scoping recommendation

- **Standalone case**: defensible only as a workshop-scale empirical audit
  paper, or as a full paper if the joint calibration/stability matrix
  yields a genuinely non-obvious cross-paradigm interaction result and
  ships a reusable diagnostic harness.
- **Fold-in case (reviewer's preferred path)**: stronger. Claim 1 already
  needs to justify why naive confidence-weighted fusion is wrong; Claim 2
  supplies that proof directly. This project's own Claim 1 dossier already
  uses incompatible confidence semantics as a core motivation. Splitting
  Claim 2 out risks two thin papers sharing one dataset and 26 adapters
  (salami-slicing risk), especially since neither diagnostic alone
  survived this Phase B/C pass with strong standalone novelty.
- **Recommendation**: fold Claim 2 into Claim 1 as a full
  diagnostic/motivation section, with appendix-level depth for the
  calibration-by-kind and repeated-query tables. Do not pitch Claim 2 as a
  standalone venue paper unless the joint interaction result is unusually
  sharp. A short workshop-scale audit paper is the only reasonable
  separate-publication path.

## Phase D — Novelty Check Report (final)

### Proposed Method
Cross-paradigm (6+ paradigms), 26-real-adapter diagnostic battery
combining (a) calibration-error analysis conditioned on an open
confidence-production-mechanism taxonomy, tested against real forward
1d/5d/20d returns, and (b) a repeated-identical-query output-stability/
variance diagnostic that separates non-determinism from miscalibration.

### Core Claims
1. Mechanism-kind-conditioned calibration (cross-paradigm, real forward
   returns) — Novelty: **MEDIUM** — Closest: The Confidence Dichotomy
   (arXiv 2601.07264); CAGE-CAL (arXiv 2605.30653).
2. Repeated-identical-query stability diagnostic separating non-
   determinism from miscalibration (cross-paradigm, real adapters) —
   Novelty: **LOW** — Closest: Replayable Financial Agents / DFAH
   (arXiv 2601.15322); When Agents Disagree With Themselves
   (arXiv 2602.11619).
3. Joint battery + cross-paradigm empirical interaction pattern —
   Novelty: **MEDIUM**, conditional on the interaction finding being
   genuinely surprising — Closest: From Accuracy to Auditability
   (arXiv 2605.23955, nearest "survey the determinism space" framing).

### Closest Prior Work

| Paper | Year | Venue | Overlap | Key Difference |
|-------|------|-------|---------|----------------|
| The Confidence Dichotomy (arXiv 2601.07264) | 2026 | ACL 2026 long (2026.acl-long.520) | Conditions LLM-agent calibration on mechanism category (tool type) | Single paradigm (LLM tool-use), non-finance, axis is tool-type not confidence-production-mechanism, no stability angle |
| When Agents Disagree With Themselves (arXiv 2602.11619) | 2026 | arXiv preprint | Repeated-run output-variance measurement as reliability signal | Non-finance, single paradigm (LLM ReAct), within-agent self-consistency on QA tasks, not cross-system numeric-output stability on trading decisions |
| Replayable Financial Agents / DFAH (arXiv 2601.15322) | 2026 | arXiv preprint | Finance-domain repeated-input determinism measurement; determinism-vs-accuracy decorrelation finding | Single paradigm (LLM tool-agents only), determinism-vs-accuracy not determinism-vs-calibration, benchmark tasks not real deployed trading adapters against forward returns |
| From Accuracy to Auditability (arXiv 2605.23955) | 2026 | arXiv preprint (survey + experiments) | Broadest cross-modality (tabular/GNN/LLM) financial determinism survey | Credit/fraud/AML focus not trading/alpha, no calibration-vs-forward-returns angle, no unified harness-level repeated-query diagnostic |
| CAGE-CAL (arXiv 2605.30653) | 2026 | arXiv preprint | Heterogeneous-agent calibration explicitly named as underexplored | Heterogeneity = different LLMs in a panel, not different algorithmic paradigms; no finance, no stability angle |
| FinPersona-Bench (arXiv 2606.31522) | 2026 | arXiv preprint | "Stability" framing in finance | Different construct (long-horizon behavioral-mandate drift, not repeated-identical-query variance); synthetic market, LLM-only |

### Overall Novelty Assessment
- Score: **5/10** (MEDIUM overall; component (b) alone is LOW after this
  session's fresh Phase B pass surfaced "Replayable Financial Agents" as a
  direct finance-domain collision; component (a) and the joint interaction
  pattern remain MEDIUM)
- Recommendation: **PROCEED WITH CAUTION** — proceed only as a diagnostic
  section folded into Claim 1 (fusion), not as a standalone venue-paper
  claim, unless the cross-paradigm interaction finding turns out to be
  unusually sharp and non-obvious
- Key differentiator: the *combination*, run uniformly across 26 real
  (not simulated/benchmark-only) adapters spanning 6+ structurally
  different confidence-production paradigms, tested against real forward
  1d/5d/20d market returns — no single found paper does calibration-by-
  mechanism-kind AND stability-vs-determinism together, cross-paradigm, in
  finance, against real returns
- Risk: a reviewer citing "Replayable Financial Agents" (2601.15322) as
  "this already exists in finance" for the stability half, and "The
  Confidence Dichotomy" / CAGE-CAL for the calibration-by-category half,
  then asking "so what's actually new besides the dataset?" — the answer
  must be the specific cross-paradigm interaction finding, not the
  existence of the diagnostics themselves

### Suggested Positioning
Do not sell this as two novel diagnostic methods. Sell it as: "naive
per-adapter or per-model calibration analysis hides a structural pattern
that only appears when you condition on *how* confidence is computed and
*whether it's reproducible* — and this pattern is what justifies [Claim
1's] calibration-aware, stability-aware fusion design, rather than a
naive confidence-weighted ensemble." Position as the empirical
motivation/diagnostic backbone of Claim 1's fusion paper, with the
calibration-by-kind and stability tables as a full section (not just a
footnote), reserving a standalone paper only if the joint interaction
result (e.g., a specific, reproducible failure-mode taxonomy across the
6+ paradigms) proves unusually strong once experiments are run.

