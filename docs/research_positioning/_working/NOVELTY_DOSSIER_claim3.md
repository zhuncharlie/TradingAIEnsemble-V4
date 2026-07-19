# Novelty Dossier — Claim 3: Regime-Conditioned Reliability Audit

## Proposed method / claim under test

An open empirical question, not an assumed finding: across a large (~26),
paradigm-diverse deployment of *independently-developed, real* (not
author-trained) financial AI / trading systems behind one shared adapter
schema, does measured **reliability** — calibration error, hit-rate
stability, and cross-adapter contradiction rate — vary systematically by
market regime (bull / bear / sideways / high-volatility)? This is distinct
from asking whether *accuracy* or *returns* vary by regime (well-established).
No experiment anywhere in this project's own history has tested the
regime-dependence of reliability itself. The claim explicitly allows for a
null result (no significant regime effect on reliability) rather than
assuming one.

## Core claims to check

1. "Does reliability itself (calibration error, hit rate, contradiction
   rate) — not just raw predictive accuracy or returns — vary by market
   regime" as a dedicated empirical study, measured across a cross-paradigm,
   multi-system (~26 independently-developed real systems) deployment.
2. Framing regime-conditioned reliability as a property to *measure/audit*
   post hoc across independently-developed systems, distinct from
   regime-conditioned *retraining*, *model selection*, or *conformal
   recalibration* (which are well-established, single-model or
   single-framework literatures).
3. The scale/heterogeneity claim itself: is a ~26-system, cross-paradigm
   reliability audit (spanning rule-based, ML, RL, LLM-agent, and portfolio-
   optimization paradigms under one schema) itself an unusual evaluation
   surface, independent of the regime-conditioning question?

## Candidate papers found (Phase B, this session — re-verified + expanded)

All arXiv-ID entries below passed `verify_papers.py` (7/8 `verified` via
direct arXiv API match, hallucination_rate = 0.0; the MDPI LightGBM paper has
no arXiv ID and returned Semantic-Scholar `verify_pending`, not a
hallucination signal — see `verified_papers_claim3.json` in this session's
scratch output).

- **RegimeFolio: A Regime Aware ML System for Sectoral Portfolio
  Optimization in Dynamic Markets** (arXiv 2510.14986, 2025-10). Regime-
  specific retraining + stability-weighted model selection within one
  system's own model zoo; optimizes performance *for* regime, does not
  audit *whether reliability varies by* regime across independently-
  published systems. **Not colliding** — retraining/selection, not
  reliability audit; single system.

- **Taming Tail Risk in Financial Markets: Conformal Risk Control for
  Nonstationary Portfolio VaR** (arXiv 2602.03903, 2026-02, aka
  "regime-weighted conformal calibration"). Regime-weighted conformal
  calibration of VaR risk buffers for one predictive pipeline. **Not
  colliding** — single-model, single-metric (VaR coverage), not a
  cross-system reliability audit; conformal *correction*, not audit of
  pre-existing systems' reliability.

- **Test-Time Adaptation for Non-stationary Time Series: From Synthetic
  Regime Shifts to Financial Markets** (arXiv 2602.00073, 2026-02).
  Regime-shift *adaptation* mechanism for one forecasting model. **Not
  colliding** — adaptation method, not a reliability measurement study, and
  single-model.

- **Conditional Adversarial Fragility in Financial Machine Learning under
  Macroeconomic Stress** (arXiv 2512.19935, 2025-12). Closest new find this
  pass. Introduces a regime-aware evaluation framework (calm vs. stress,
  via volatility-based segmentation) but (a) holds model architecture fixed
  across the comparison rather than surveying many independently-developed
  systems, (b) the regime-dependent property measured is *adversarial
  robustness* (attack success / fragility), not calibration, hit-rate
  stability, or cross-model contradiction rate, and (c) explicitly finds
  *baseline* predictive performance/calibration is regime-stable — it is
  adversarial vulnerability specifically that is regime-fragile. **Not
  colliding** — different reliability construct (adversarial fragility vs.
  calibration/hit-rate/contradiction), different scope (single architecture
  vs. ~26 real systems), but this is the closest work found and should be
  cited as the nearest analog for the general "reliability is regime-
  conditional" thesis.

- **Cross-Model Disagreement as a Label-Free Correctness Signal** (arXiv
  2603.25450, 2026-03). Relevant to the "contradiction rate" sub-metric —
  uses inter-model disagreement (cross-model perplexity/entropy) as a
  correctness proxy. **Not colliding** — general LLM correctness detection
  (MMLU/TriviaQA/GSM8K), no financial application, no regime conditioning at
  all. Useful as a methodological precedent for treating disagreement as a
  reliability signal, not as prior art on the claim itself.

- **Deep Learning for Financial Time Series: A Large-Scale Benchmark of
  Risk-Adjusted Performance** (arXiv 2603.01820, 2026-03). Benchmarks five
  architecture families (linear, RNN, Transformer, SSM, sequence-
  representation variants: VSN+LSTM, VSN+xLSTM, LSTM+PatchTST, xLSTM) over
  2010-2025 multi-asset data, and does include a "reliability and
  calibration" metric family (parse-failure rate, expected calibration
  error) in its ten-dimension panel, plus qualitative note that "generic
  transformers and SSMs displayed heterogeneous, regime-sensitive behavior."
  This is the closest *scale/panel-design* analog found. **Not colliding**
  — on inspection the benchmarked variants are architecture families
  trained by the authors within one unified framework, not independently-
  developed, separately-published real systems (RegimeFolio/FinAgent/
  FinMem/PGPortfolio-style adapters); and the abstract/available text gives
  no evidence of ECE explicitly *stratified and reported per regime* as a
  dedicated cross-regime reliability comparison — regime-sensitivity is
  reported as a qualitative behavioral note on returns, not a calibration-
  by-regime table.

- **RareCP: Regime-Aware Retrieval for Efficient Conformal Prediction**
  (arXiv 2605.08857, 2026-05). Single integrated conformal-prediction model
  with a mixture-of-experts calibration mechanism that adapts to "distinct
  error regimes" via retrieval. **Not colliding** — regime-aware *method*
  for producing calibrated intervals from one model, not an audit of
  whether reliability varies by regime across many pre-existing systems.

- **Regime-Aware LightGBM for Stock Market Forecasting: A Validated
  Walk-Forward Framework with Statistical Rigor and Explainable AI
  Analysis** (MDPI Electronics, 2026; no arXiv ID —
  `verify_pending`/Semantic-Scholar, tag **[UNVERIFIED-PENDING]**).
  Single-model regime-aware forecasting + explainability. **Not colliding**
  — single model, no cross-system reliability audit.

### Additional negative-result context found this pass

Several 2026 benchmark/survey papers explicitly note the gap this claim
targets without filling it: one search hit observed that "most evaluations
[of LLM-based trading agents] cover six to twelve months within a single
market regime, providing no cross-regime evidence," and another financial
multi-agent survey (Toward Reliable Evaluation of LLM-Based Financial
Multi-Agent Systems, arXiv 2603.27539) raises coordination/reliability
concerns for financial multi-agent systems generally but was not fetched in
full for this pass — flagged as a possible secondary reference, not
independently verified as colliding or non-colliding.

## Questions for the reviewer

1. Is "does calibration/reliability (not just accuracy or returns) vary by
   market regime, measured across many independently-developed,
   paradigm-diverse real financial AI systems (~26, spanning rule-based,
   ML, RL, LLM-agent, and portfolio-optimization paradigms) under one
   shared schema" already answered or closely attempted anywhere in the
   literature you can find, beyond the candidates listed above?
2. Is this defensibly distinct from (a) the regime-aware retraining/model-
   selection literature (RegimeFolio), (b) the regime-weighted conformal
   calibration literature (VaR conformal, RareCP), and (c) the closest
   analog found this pass — Conditional Adversarial Fragility (arXiv
   2512.19935), which shows *adversarial* robustness is regime-conditional
   for a single architecture but explicitly finds baseline calibration/
   accuracy is regime-stable?
3. Given this claim explicitly allows for a null result (no regime effect
   on reliability found), is a null/negative result here still a
   publishable finding at a finance-AI venue standing alone, or does it
   only carry weight as a supporting ablation feeding other claims (e.g.,
   claims about cross-system fusion or ensemble policy) in the same paper?
4. What is the single closest prior work overall, and what precisely is the
   delta versus this project's proposed claim?
5. Does the project's current scoping call — treat this as a probable
   regime-stratified ablation feeding Claims 1 and 4, rather than a
   standalone paper, specifically because of the real risk that a null
   result reads as thin on its own at a finance-AI venue — look correct
   given the literature found? Would you challenge that call in either
   direction (i.e., is it strong enough to stand alone, or is even the
   ablation framing generous)?

## Phase C — Cross-model verification (Codex MCP, gpt-5.5, xhigh reasoning)

**Attempt 1** (`model: gpt-5.6-sol`) failed hard: Codex MCP returned
`400 invalid_request_error` — "The 'gpt-5.6-sol' model requires a newer
version of Codex. Please upgrade to the latest app or CLI and try again."
Confirmed against the installed client's own model cache
(`/mnt/beegfs/xqinag/.codex/models_cache.json`, `client_version: 0.139.0`):
only `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `codex-auto-review` are listed —
`gpt-5.6-sol` is genuinely absent from this client, not a transient backend
error. Traced as `status: error` in
`.aris/traces/novelty-check/2026-07-19_run01/008-claim3-phaseC-attempt1-model-unavailable/`.

**Attempt 2** (`model: gpt-5.5`, the highest-priority model actually
available) succeeded — full Codex session, xhigh reasoning, real
completion, threadId `019f7b49-7338-79b0-93ac-22f7d0fafa27`. Traced as
`status: fallback_used` in
`.aris/traces/novelty-check/2026-07-19_run01/009-claim3-phaseC-resolved/`.

### Reviewer's answers (verbatim, gpt-5.5 xhigh)

1. **No direct prior answer found.** The full claim — regime-stratified
   calibration/reliability across many independently developed,
   heterogeneous real financial AI/trading systems under one schema,
   including contradiction rate — appears unoccupied. Component pieces are
   well covered (RegimeFolio conditions forecasting/allocation on regime
   rather than auditing existing systems' reliability by regime; conformal
   work uses regime weighting as a correction method for one pipeline;
   recent regime-split forecasting papers report calibration metrics but
   within one authored framework, not a 26-system audit).
2. **Yes, defensibly distinct, but only if phrased narrowly.** Distinct
   from RegimeFolio-style retraining/selection (that literature *builds*
   regime-aware systems; this proposal *audits* pre-existing ones);
   distinct from conformal VaR/RareCP (those *improve/localize* calibration
   intervals rather than measuring whether heterogeneous systems' reliability
   degrades by regime); distinct from Conditional Adversarial Fragility
   (that paper studies regime-conditioned *adversarial* vulnerability for a
   fixed architecture and explicitly finds baseline performance/calibration
   is regime-stable). Reviewer's explicit caution: "Do not claim novelty for
   'regime-conditioned reliability' broadly; claim novelty for a
   regime-stratified reliability audit across heterogeneous real trading
   systems."
3. **A null result is probably not strong enough as a standalone finance-AI
   paper unless the evaluation artifact is itself a benchmark
   contribution.** Publishable standing alone only if well powered,
   preregistered, reproducible, and surprising against a clear prior;
   otherwise reads as a useful robustness check. The reviewer states plainly:
   "The method is not novel: stratify reliability metrics by regime and test
   differences. The potential novelty is the empirical finding on a rare
   multi-system deployment."
4. **Closest prior work overall: Conditional Adversarial Fragility in
   Financial Machine Learning under Macroeconomic Stress (arXiv
   2512.19935)** — closest because it is a post hoc regime-aware
   model-risk evaluation, not merely a regime-aware trading method. Precise
   delta: it tests adversarial robustness under calm/stress regimes for one
   architecture; this project would test ordinary reliability metrics
   (calibration, hit-rate stability, cross-adapter contradiction) across
   ~26 independently developed heterogeneous systems. Large financial
   benchmarks and LLM-agent arenas are the closest scale analogs but do not
   close the regime-conditioned reliability-audit gap.
5. **Yes, the scoping call is correct.** The reviewer would not challenge it
   upward unless results are strong and the adapter benchmark itself is
   released as a reusable evaluation artifact, and explicitly does not
   consider the ablation framing generous: "if Claims 1 and 4 depend on
   reliability-aware fusion/routing, regime-stratified reliability is a
   natural supporting analysis. Standalone treatment is risky, especially if
   the answer is null or weakly powered."

**Reviewer's explicit score/recommendation:** Novelty score **6/10**.
Recommendation **PROCEED WITH CAUTION**. Verdict: **fold in as a
regime-stratified ablation/supporting empirical section, not a standalone
paper**; standalone only becomes defensible if the finding is strong,
statistically powered, and packaged as a reusable heterogeneous-system
reliability benchmark.

## Phase D — Novelty Check Report

### Proposed Method

A regime-stratified reliability audit (calibration error, hit-rate
stability, cross-adapter contradiction rate — not accuracy/returns) across
~26 independently-developed, paradigm-diverse real financial AI/trading
systems under one shared schema, framed as an open empirical question that
explicitly tolerates a null result.

### Core Claims

1. Regime-conditioned **reliability** (not accuracy/returns) as a dedicated
   cross-system empirical question — Novelty: **MEDIUM-HIGH** — Closest:
   Conditional Adversarial Fragility (arXiv 2512.19935), which is
   regime-conditioned but for adversarial robustness, single architecture.
2. Auditing reliability *across independently-developed systems* (vs.
   regime-aware retraining/selection/conformal correction within one
   system) — Novelty: **HIGH** — Closest: RegimeFolio (arXiv 2510.14986),
   which builds rather than audits.
3. Scale/heterogeneity of the evaluation surface itself (~26 real,
   cross-paradigm systems under one schema, at all — independent of
   regime-conditioning) — Novelty: **MEDIUM** — Closest: Deep Learning for
   Financial Time Series large-scale benchmark (arXiv 2603.01820), which is
   large-scale but single-framework/author-trained, not independently
   published systems.

### Closest Prior Work

| Paper | Year | Venue | Overlap | Key Difference |
|-------|------|-------|---------|-----------------|
| Conditional Adversarial Fragility in Financial ML under Macroeconomic Stress (arXiv 2512.19935) | 2025-12 | arXiv (cs.LG/cs.AI/cs.CR) | Regime-conditioned, post hoc model-risk evaluation framework | Adversarial robustness metric, not calibration/hit-rate/contradiction; single fixed architecture, not ~26 independent systems; explicitly finds baseline calibration regime-*stable* |
| RegimeFolio (arXiv 2510.14986) | 2025-10 | arXiv | Regime-aware evaluation across market states | Retraining/model-selection to optimize for regime, not an audit of pre-existing systems' reliability |
| Taming Tail Risk / regime-weighted conformal VaR (arXiv 2602.03903) | 2026-02 | arXiv | Regime-weighted calibration | Single-model conformal correction of VaR coverage, not multi-system reliability audit |
| RareCP (arXiv 2605.08857) | 2026-05 | arXiv | Regime-aware calibration via retrieval | Single integrated conformal model with mixture-of-experts, not cross-system audit |
| Deep Learning for Financial Time Series large-scale benchmark (arXiv 2603.01820) | 2026-03 | arXiv | Large-scale panel incl. calibration/ECE metric family, notes regime-sensitive behavior | Author-trained architecture families within one framework, not independently-developed real systems; regime-sensitivity reported qualitatively on returns, not as an ECE-by-regime table |
| Cross-Model Disagreement as a Label-Free Correctness Signal (arXiv 2603.25450) | 2026-03 | arXiv | Methodological precedent for disagreement-as-reliability-signal | General LLM correctness detection, no finance, no regime conditioning |

### Overall Novelty Assessment

- **Score: 6/10** (reviewer-assigned; independently consistent with the
  Phase B search — no direct collision found across 10+ targeted queries,
  but the surrounding literature (regime-aware retraining, regime-weighted
  conformal calibration, regime-conditioned adversarial fragility) is dense
  enough that the specific delta must be argued precisely rather than
  assumed).
- **Recommendation: PROCEED WITH CAUTION.**
- **Key differentiator (if pursued):** the audit framing (measuring
  reliability across many *independently-developed, already-published*
  systems under one schema) rather than building or correcting one system;
  this is the load-bearing distinction from every close paper found.
- **Risk:** a reviewer at a finance-AI venue could reasonably cite
  Conditional Adversarial Fragility (2512.19935) as "someone already showed
  reliability is regime-conditional" unless the paper is explicit that (a)
  the reliability construct differs (calibration/hit-rate/contradiction vs.
  adversarial fragility) and (b) the evaluation surface differs (~26
  independent systems vs. one architecture). A null result, presented
  alone, risks reading as "we ran an ablation and found nothing" rather
  than a contribution.

### Suggested Positioning

Do not position as "first to show reliability is regime-conditional in
finance" (overclaim risk against 2512.19935). Position as: the first
*cross-system, cross-paradigm* reliability audit at this scale (~26
independently-developed real systems), testing whether the regime-
dependence pattern established for adversarial robustness in a single
architecture *also* holds for ordinary calibration/hit-rate/contradiction
metrics in a heterogeneous deployment — and explicitly report the null
result as informative if it occurs (e.g., "reliability degradation is
regime-invariant across paradigms, suggesting X," which itself has decision
implications for fusion/routing policy).

## Final Verdict on the Project's Scoping Call

**Confirmed — do not promote to standalone paper.** Both the independent
Phase B literature search and the Codex Phase C cross-model review
converge on the same recommendation: fold Claim 3 into Claims 1 and 4 as a
regime-stratified reliability ablation, not a standalone paper. The
distinguishing angle (audit vs. build/correct, cross-system vs.
single-system) is real but narrow, and a null result would not carry a
paper alone without the adapter benchmark itself being positioned as a
reusable artifact — which is a separate (Claim-1/2-adjacent) contribution,
not this claim's job to carry.

