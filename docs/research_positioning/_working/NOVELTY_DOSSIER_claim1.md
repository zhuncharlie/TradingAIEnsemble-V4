# Novelty Dossier — Claim 1: Reliability- and Contradiction-Aware Multi-View Fusion

## Proposed method
A fusion rule for combining Q1(action)/Q3(signal) outputs across **26 real,
independently-published, mechanistically heterogeneous financial AI systems**
(LLM multi-agent debate frameworks, FinBERT/FinGPT sentiment classifiers,
Qlib/RD-Agent/AlphaGen/AlphaForge alpha-factor-mining systems spanning
genetic programming / RL search / LLM-agent research loops / curated-factor
gradient-boosted pipelines, and FinRL/TradeMaster/skfolio/DeepDow/PGPortfolio/
EarnMore/Universal-Portfolios portfolio-RL/online-learning systems) behind one
shared output schema. The fusion weight for each system's vote is set by (a)
its *measured, out-of-sample* calibration reliability — realized hit rate vs.
self-reported confidence, tracked causally over time, NOT the self-reported
confidence value itself — plus (b) a penalty when a cross-agent contradiction
rule fires (e.g. one system says BUY while another flags HIGH_RISK on the same
ticker/date) or when the same single agent's own Q1/Q2/Q3/Q4 outputs are
internally incoherent (e.g. its own Q2 state is bearish while its own Q1
action is BUY). Compared against unweighted majority vote and naive
confidence-weighted vote as baselines.

## Core claims to check
1. Fusion weighted by *measured* (not self-reported) calibration reliability,
   applied across **paradigm-heterogeneous** (not just multiple LLM instances)
   real financial AI systems.
2. A contradiction-penalty term combining both cross-agent structural
   contradiction rules AND intra-agent cross-question (Q1/Q2/Q3/Q4)
   incoherence, in one fusion formula.
3. The empirical framing: that naive confidence-weighted fusion is unsafe
   specifically because "confidence" means different, incompatible things
   across mechanism types (LLM self-report, model-margin, heuristic score
   normalization), and that this can be fixed by substituting measured
   reliability for self-reported confidence.

## Pre-search verification (this session)
Ran `verify_papers.py --arxiv-ids 2603.22567,2502.17518` (3-layer arXiv/
CrossRef/Semantic Scholar fallback, per shared-references/citation-discipline.md
Pre-Search Verification Protocol). Result: `"verdict": "PASS"`,
`"hallucination_rate": 0.0`, `"pending_rate": 0.0`, both papers
`"status": "verified"`, `"method": "arxiv"`, `"confidence": "high"`. Neither
ID is fabricated; both resolve to the exact titles/authors used throughout
this dossier.

## Candidate papers found (Phase B — re-verified this session via WebFetch/WebSearch)

- **TrustTrade: Human-Inspired Selective Consensus Reduces Decision
  Uncertainty in LLM Trading Agents** (arXiv 2603.22567, Minghan Li, Rachel
  Gonsalves, Weiyue Li, Sunghoon Yoon, Mengyu Wang, submitted 2026-03-23).
  **Full abstract confirmed via WebFetch this session, direct arxiv.org/abs
  fetch (not synthesis).** Multi-agent selective-consensus framework
  ("Trust-Rectified Unified Selective Trader") that replaces "uniform trust"
  with cross-agent consistency: aggregates info from multiple *independent
  LLM agents*, dynamically weights signals by their **semantic and numerical
  cross-agent agreement**; divergent/weakly-grounded/temporally-inconsistent
  inputs are discounted. Adds deterministic temporal anchors and a test-time
  reflective memory for risk-preference adaptation. Evaluated on 2024 Q1 /
  2026 Q1 high-noise backtests, showing a shift from extreme risk-return
  regimes to a mid-risk/mid-return profile.
  **Confirmed mechanism facts, this session, via direct WebFetch of
  arxiv.org/abs/2603.22567 (verbatim abstract quote obtained):**
  > "TrustTrade replaces uniform trust with cross-agent consistency by
  > aggregating information from multiple independent LLM agents and
  > dynamically weighting signals based on their semantic and numerical
  > agreement. Consistent signals are prioritized, while divergent, weakly
  > grounded, or temporally inconsistent inputs are selectively discounted."
  (a) all agents are LLM-based — the abstract and fetched page content
  contain no mention of non-LLM systems, RL agents, factor models, or
  classical ML components being integrated into the ensemble; the paper
  explicitly frames the contribution as addressing an LLM-specific "uniform
  trust" bias;
  (b) the reliability/weighting signal is **cross-agent agreement**
  (semantic + numerical consistency), confirmed verbatim above — not an
  independently-measured, realized-outcome calibration score anywhere in the
  fetched abstract/page. This is a structural mechanism difference, not just
  framing: an agreement-based scheme mathematically down-weights a lone
  correct dissenter (by construction, since weight is a function of
  similarity to the pack), whereas a calibration-based scheme weights each
  source by its own track record independent of what others say, so a
  consistently well-calibrated lone dissenter is not penalized for
  disagreeing.
  **Verdict on differentiators**: both (a) and (b) now confirmed by direct
  primary-source read (WebFetch of the arXiv abstract page), not just
  WebSearch synthesis. This is the single closest prior work and must be
  cited and explicitly differentiated, not omitted.
- **Additional Phase B refresh this session (WebSearch, 2026 H1 sweep)**: no
  new paper found that displaces TrustTrade as closest prior art. Scanned:
  "Toward Reliable Evaluation of LLM-Based Financial Multi-Agent Systems"
  (arXiv 2603.27539, hierarchical manager-arbitrates-specialists framing,
  notes debate architectures "improve calibration under signal ambiguity"
  but this is about deliberation quality, not an outcome-calibration fusion
  weight); "PolySwarm" (arXiv 2604.03888, heterogeneous LLM *personas*,
  still single-paradigm/all-LLM); "AlphaCrafter" (arXiv 2605.05580,
  regime-adaptive signal-ensemble reconfiguration, single framework). None
  combine paradigm-heterogeneous real systems with outcome-calibration
  fusion weighting.
- **Ensemble RL through Classifier Models: Enhancing Risk-Return Trade-offs
  in Trading Strategies** (arXiv 2502.17518, Zheli Xiong, submitted
  2025-02-23, 16pp). **Re-confirmed via WebSearch this session.** Combines RL
  algorithms (A2C/PPO/SAC) with classical classifiers (SVM/Decision
  Tree/Logistic Regression) in an ensemble; selection driven by
  variance-threshold filtering of classifier confidence scores; evaluated on
  cumulative return/Sharpe/Calmar/MDD. Same-paradigm ensemble (RL + classical
  ML voting/selection within one experimental framework, not cross-system
  real published projects); no cross-agent/intra-agent contradiction-rule
  taxonomy; no calibration-vs-self-report distinction — variance of
  classifier confidence is used directly as the selection signal, not
  validated against realized-outcome calibration.
- **Crowd-Calibrator: Can Annotator Disagreement Inform Calibration in
  Subjective Tasks?** (arXiv 2408.14141). Uses disagreement as a calibration
  signal, but in a crowd-annotation NLP setting, not multi-system finance —
  weak overlap, background reference only.
- **PolySwarm: A Multi-Agent Large Language Model Framework for Prediction
  Market Trading and Latency Arbitrage** (arXiv 2604.03888). Independently
  re-checked this session via direct WebFetch of the HTML full text (not just
  the earlier WebSearch scan). Uses confidence-weighted averaging
  (`p_swarm = Σw_i p_i / Σw_i`) across 50 agents, but **all 50 agents are
  diverse LLM personas** (macro economist, technical analyst, etc.) —
  mechanistically homogeneous, same limitation as TrustTrade. Critically, the
  paper's own Section VIII lists "adaptive calibration systems that update
  per-agent reliability weights using track records of resolved predictions"
  as **unimplemented future work**, and explicitly states there is **no
  contradiction-detection mechanism** — only a swarm-standard-deviation
  disagreement filter (trade only if std < 30%), which measures spread, not
  logical/structural inconsistency. Useful corroborating evidence that the
  field has *identified* the outcome-calibration gap but not yet closed it;
  does not threaten claim 1's novelty and does not displace TrustTrade as
  closest prior art.
- **HARLF: Hierarchical Reinforcement Learning and Lightweight LLM-Driven
  Sentiment Integration for Financial Portfolio Optimization** (arXiv
  2507.18560). Checked this session via WebFetch and ruled out: it is a
  single internally-trained three-layer architecture (base RL agents +
  meta-agents + super-agent, all custom-built with Stable Baselines 3 /
  PyTorch) fusing two *data modalities* (price + NLP sentiment) inside one
  training pipeline via simple concatenation — not a fusion of independently
  published, externally heterogeneous systems, and has no calibration-based
  or contradiction-detection weighting mechanism.
- **"Building a 26-Model Ensemble Trading Council" (Medium, 2026-06,
  ashutosh38agg)** — surfaced by this session's WebSearch due to a coincidental
  keyword match on "26" and "calibration bug"; checked via WebFetch and ruled
  out. Not peer-reviewed; describes 26 in-house model variants (LSTM/GRU/
  Transformer/GBM) trained on one proprietary EUR/USD tick dataset — one data
  modality, one experimental framework, not independently published
  cross-paradigm systems. The "calibration bug" is a voting-confidence-cap
  implementation bug (confidence capped at exactly 50%), not a
  calibration-vs-agreement methodological distinction. No overlap with claim
  1's core mechanism; logged here only to document it was checked.

## Phase C — Codex MCP cross-model verification

**Status: completed successfully this session, via a real `mcp__codex__codex`
call.** Note on process integrity: an earlier draft of this section in this
same session was written *before* the real call succeeded and has been
discarded — it was a placeholder, not a genuine model output, and per this
skill's anti-fabrication policy it must not be presented as a verdict. The
content below is the actual response text returned by the tool call.
Model note: `gpt-5.6-sol` was rejected by this Codex CLI version
(`400 invalid_request_error: "The 'gpt-5.6-sol' model requires a newer
version of Codex"`); the call was re-issued without a model override
(CLI default model) at `model_reasoning_effort: xhigh`, `sandbox: read-only`.
Thread id `019f7b46-5195-7f42-add1-5f1076b76c56`. The reviewer was pointed at
this dossier file and explicitly instructed to ignore this file's own
(then-placeholder) Phase C/verdict sections and answer independently.

**Reviewer response (paraphrased from the actual tool output, condensed):**
- **(1) Already covered?** Not fully, but TrustTrade is close enough to put
  this claim "in the danger zone." TrustTrade already has the "multi-agent
  trading fusion with selective trust" flavor (cross-agent semantic/numerical
  agreement weighting, discounting divergent/inconsistent inputs) — that
  framing alone is not available as this proposal's novelty anchor. The real
  delta is narrower than the full method description suggests: it is
  specifically (a) weighting by *measured out-of-sample calibration* (realized
  hit rate vs. self-reported confidence over time) rather than confidence or
  agreement itself, and (b) spanning heterogeneous real published systems
  rather than LLM agents only. The RL/classifier ensemble (2502.17518) and
  Crowd-Calibrator are both weaker threats than TrustTrade for the reasons
  already in the dossier.
- **(2) Closest prior work / precise delta**: TrustTrade. Delta, stated
  precisely: TrustTrade spans multiple *independent LLM agents* only; this
  proposal spans 26 heterogeneous published systems (LLM debate, sentiment
  classifiers, alpha-factor mining, RL/search, gradient-boosted pipelines,
  portfolio RL, online learning). TrustTrade weights by cross-agent
  semantic/numerical agreement; this proposal weights by realized calibration
  tracked out-of-sample over time. Mechanically, agreement-weighting can
  penalize a correct lone dissenter (disagreement lowers its weight by
  construction), while calibration-weighting can preserve that source's
  weight if its own historical track record is strong. This proposal also
  adds an explicit *dual* contradiction mechanism — cross-agent contradiction
  rules plus intra-agent Q1/Q2/Q3/Q4 incoherence — in one fusion formula,
  which TrustTrade does not have.
- **(3) Is the "confidence means incompatible things across mechanism types"
  framing itself novel?** No — not as a standalone novelty claim. It is true
  and useful as motivation (self-report, classifier margin, and heuristic
  score normalization are not commensurate objects) but a reviewer will
  likely read it as "obvious calibration hygiene." The reviewer's assessment:
  the stronger contribution is the operational one — replacing incompatible
  self-reported scores with measured realized reliability across
  heterogeneous systems — not the framing point by itself.
- **(4) Blunt ICAIF-reviewer verdict**: "Borderline but not dead." If framed
  as "selective consensus / trust-weighted trading agents," it reads as too
  close to TrustTrade and incremental. If the paper compares only against
  majority vote and naive confidence weighting, a reviewer can reasonably say
  the key nearest-neighbor baseline (TrustTrade-style agreement weighting) is
  missing. It becomes defensible as a separate contribution **only if** the
  paper makes the mechanism difference unavoidable: outcome-calibration vs.
  agreement weighting, heterogeneous real systems vs. LLM-only agents, and
  explicit cross-agent + intra-agent contradiction penalties — and only with
  a TrustTrade-style agreement-weighting baseline plus ablations isolating
  the contradiction penalty. Without those, the reviewer states plainly they
  "would expect a serious reviewer to call this under-differentiated from
  TrustTrade."

## Questions for the reviewer (answered above, from the real Phase C call)
1. Not fully covered by TrustTrade, but close enough to be a real risk if
   the framing leans on "selective consensus" language rather than the
   calibration-vs-agreement mechanism delta.
2. Closest prior work = TrustTrade (2603.22567); delta = realized-outcome
   calibration vs. cross-agent agreement as the reliability signal, plus
   paradigm-heterogeneity (26 real heterogeneous systems) vs.
   single-LLM-paradigm ensemble, plus the dual (cross-agent + intra-agent)
   contradiction mechanism TrustTrade lacks.
3. The "incompatible confidence semantics" framing alone is not a strong
   novelty hook and risks reading as obvious; the mechanism delta and the
   heterogeneous-system scope are the stronger, defensible hooks.
4. Reviewer's blunt take: "borderline but not dead" — defensible only on the
   explicit condition that a TrustTrade-style agreement-weighting baseline is
   implemented and benchmarked directly, with an ablation isolating the
   contradiction penalty; without that, expect a reviewer to call it
   under-differentiated from TrustTrade.

## Phase C cross-check — second independent Codex call, same session
A second, independently-issued `mcp__codex__codex` call was made against this
same dossier (thread `019f7b4a-1461-71f2-9d00-33edd98ebe85`, CLI default model
since `gpt-5.6-sol` and `gpt-5.2` were both rejected by this ChatGPT-account
Codex CLI — see Model note above; `model_reasoning_effort: xhigh`,
`sandbox: read-only`). This was a genuine second reviewer pass, not a repeat
of the same call. It independently converged on the same load-bearing
conclusions: novelty score **6/10**, closest prior work = TrustTrade,
delta = calibration-vs-agreement mechanism + paradigm heterogeneity (the
"correct lone dissenter" argument stated in the same terms), and the same
mandatory requirement that a TrustTrade-style agreement-weighting baseline be
implemented head-to-head rather than only discussed, plus an explicit
ablation/case-study isolating the lone-dissenter divergence. It also
independently flagged the "confidence means incompatible things across
mechanism types" framing as motivational, not a standalone novelty hook.
Two independent Codex calls this session agree; this is not a single
reviewer's idiosyncratic read.
Trace note: per this task's explicit scope restriction (only the dossier
path at `docs/research_positioning/_working/NOVELTY_DOSSIER_claim1.md` may be
modified), the mandatory `.aris/traces/novelty-check/...` forensic trace
artifacts for this second Codex call were **not** written to disk this
session — recorded here inline instead (thread id, model/effort actually
used, full verdict) so the omission is visible rather than silent.

## Final novelty verdict for CLAIM_CANDIDATES.md / NOVELTY_AUDIT.md
**MEDIUM** (Phase C, run for real via Codex MCP this session — twice,
independently, via two separate calls that converged — is notably more
skeptical than the Phase-B-only WebSearch pass. Both calls explicitly warn
this claim is "in the danger zone" / "borderline but not dead" relative to
TrustTrade and would likely be read as under-differentiated without further
work; this is not a confirmed MEDIUM-HIGH). Recommendation: **PROCEED WITH
CAUTION**, with two mandatory, non-optional scope additions before this can
stand as a paper-worthy claim:
(1) implement and benchmark a TrustTrade-style agreement-weighting baseline
head-to-head, not just discuss it; (2) run an ablation/case-study that
isolates a "correct lone dissenter" scenario where calibration-weighting and
agreement-weighting provably diverge, and lead the contribution with that
empirical mechanism delta rather than the "incompatible confidence semantics"
framing point, which both reviewer calls flagged as likely to read as
obvious/motivational rather than a novelty anchor.
