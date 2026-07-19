# Literature Map — ICAIF Positioning

Compiled from genuine ARIS skill invocations this session: `research-lit`,
`semantic-scholar`, `openalex`, and `novelty-check` (5 runs, one per candidate
claim, each including a real Codex MCP Phase-C cross-model review). Sources
of record: live Crossref REST API queries against the three ACM ICAIF
proceedings DOI prefixes (`10.1145/3604237` ICAIF'23, `10.1145/3677052`
ICAIF'24, `10.1145/3768292` ICAIF'25 — 286 real DOI-verified titles scanned),
arXiv API, Semantic Scholar `paper`/`search` lookups, OpenAlex, and direct
WebFetch of abstracts for load-bearing comparisons. Working notes with full
methodology are preserved at `_working/ICAIF_TREND_RESEARCH.md` and
`_working/LIT_LANDSCAPE_2026.md`; per-claim search trails are in
`_working/NOVELTY_DOSSIER_claim{1..5}.md`.

**Venue-attribution caution**: several papers below are arXiv preprints only,
not confirmed accepted at ICAIF or any peer-reviewed venue as of this
research date (2026-07-19). Where a venue is confirmed, it is stated
precisely (e.g. "FineFT" resolves to ACM SIGKDD via Semantic Scholar's
`publicationVenue` field, **not** ICAIF, correcting an earlier assumption).

---

## 1. Must-cite closest prior art (direct competitive overlap)

| Paper | Venue | Problem | Method | Difference from this project | Citation value |
|---|---|---|---|---|---|
| **TrustTrade**: Human-Inspired Selective Consensus Reduces Decision Uncertainty in LLM Trading Agents (arXiv 2603.22567, 2026-03) | arXiv preprint (not confirmed ICAIF-accepted; 0 citations) | LLM trading agents give "uniform trust" to noisy multi-source info | Cross-agent **semantic + numerical agreement**-weighted consensus among multiple independent LLM agent instances; discounts divergent/inconsistent inputs; deterministic temporal anchors + reflective memory | **Single paradigm** (LLM instances only, confirmed via direct WebFetch of abstract) vs. this project's 26 systems across 6+ mechanistically distinct paradigms; reliability signal is **cross-agent agreement**, not independently-measured **realized-outcome calibration** — agreement-weighting structurally down-weights a correct lone dissenter, calibration-weighting need not | **Highest** — closest prior art for the fusion claim (Claim 1) and the abstention claim (Claim 5); must be cited, differentiated, and benchmarked against as a baseline, not just discussed |
| **ContestTrade** ("Internal Contest Mechanism") (arXiv 2508.00554, v4 ~2026-07) | arXiv preprint | Which LLM agents/factors in a multi-agent trading system deserve resources | Scores agents by **delayed market outcomes**, predicts future utility, allocates resources toward agents with positive predicted utility | LLM-agent-centric (internal Data/Research teams within one framework, not 26 real heterogeneous systems); no calibration-curve/hit-rate model; no cross-layer (Q1/Q2/Q3/Q4) contradiction-severity mechanism | **Highest** — found via a parallel-session Codex Phase-C pass, closest overall prior art to Claim 1 on the outcome-weighting axis specifically; cite alongside TrustTrade, not as a substitute |
| **FineFT**: Efficient and Risk-Aware Ensemble Reinforcement Learning for Futures Trading (arXiv 2512.23773) | **ACM SIGKDD** (DOI 10.1145/3770854.3780187) — confirmed **not** ICAIF | RL instability + lack of capability-boundary awareness under high leverage | 3-stage ensemble of **self-trained Q-learners within one RL framework**; VAE-based market-state/capability-boundary modeling; VAE-guided routing to filtered ensemble or conservative fallback | Homogeneous paradigm (one RL framework's internal Q-learner pool, confirmed via direct WebFetch) vs. this project's routing across **independently-published, cross-paradigm real systems**; no causal point-in-time execution/constraint harness | **Highest** — closest prior art for the routing/shadow-Q4 claim (Claim 4); same research lineage as DeepScalper (Bo An/NTU group) |
| **When Alpha Breaks**: Two-Level Uncertainty for Safe Deployment of Cross-Sectional Stock Rankers (arXiv 2603.13252, 2026-03) | arXiv preprint | Deploying a ranker without knowing when its uncertainty is untrustworthy | Single-model (LightGBM) DEUP-derived epistemic uncertainty triggers exposure reduction; explicit "epistemic tail-risk cap" / drawdown framing | Single-model uncertainty trigger vs. this project's **cross-system structural contradiction** trigger; closest analog for the *evaluation philosophy* (risk/drawdown-first) of the abstention claim (Claim 5), not the trigger mechanism | High — must cite for Claim 5's evaluation framing |
| CLQT: Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for Diagnostic Evaluation of LLM Portfolio-Management Agents (arXiv 2606.29771, 2026) | arXiv preprint | Return-only ranking of LLM portfolio agents doesn't diagnose *why* they succeed/fail; look-ahead leakage | 5-stage closed-loop cycle, hash-chained audit trail, 5-axis capability scorecard **including an explicit "Reliability" axis** | Diagnostic *benchmark*, not a fusion/routing method — but its audit-trail design and named "Reliability" axis are conceptually adjacent to this project's provenance requirements (CLAUDE.md §4) | Medium-High — cite for evaluation-protocol alignment, disambiguate from this project's contribution |
| Conditional Adversarial Fragility in Financial ML under Macroeconomic Stress (arXiv 2512.19935, 2025-12) | arXiv preprint | Is model *robustness* regime-conditional? | Regime-aware post hoc evaluation (calm vs. stress via volatility segmentation) of one fixed architecture's **adversarial fragility**; explicitly finds baseline calibration/accuracy is regime-**stable** | Different reliability construct (adversarial fragility vs. calibration/hit-rate/contradiction) and different scope (1 architecture vs. ~26 independent real systems) — but the single closest analog for Claim 3 (regime-conditioned reliability audit) and the paper most likely to be cited by a reviewer as "someone already showed this" | High — must cite and precisely distinguish for Claim 3 |

## 2. Multi-agent LLM finance systems & benchmarks

| Paper | Venue | Problem | Method | Difference | Citation value |
|---|---|---|---|---|---|
| TradingAgents: Multi-Agents LLM Financial Trading Framework (arXiv 2412.20138, 2024) | arXiv preprint | Single-agent LLM systems lack firm-like collaborative structure | Role-specialized LLM agents (analysts/researchers/risk team/trader) with debate synthesis | Multi-agent but all-LLM paradigm; no reliability scoring or non-LLM fusion | High |
| FinCon: Synthesized LLM Multi-Agent System with Conceptual Verbal Reinforcement (arXiv 2407.06567, 2024) | arXiv preprint | Multi-source synthesis + episodic belief updating | Manager-analyst hierarchy, self-critique risk control, verbal reinforcement propagation | LLM-only; belief propagation is intra-framework | Medium-High |
| PolySwarm: Multi-Agent LLM Framework for Prediction Market Trading and Latency Arbitrage (arXiv 2604.03888, 2026) | arXiv preprint | Aggregating many LLM-persona forecasts | Confidence-weighted averaging across 50 LLM personas; std-based disagreement filter | 50 agents, still all-LLM; own Section VIII lists "adaptive calibration using resolved-prediction track records" as **unimplemented future work** and states there is **no contradiction-detection mechanism** — corroborates this project's gap claim without closing it | Medium-High — strong corroborating citation |
| FinPos: Position-Aware Trading Agent System for Real Financial Markets (arXiv 2510.27251, 2025) | arXiv preprint | Agents lack continuous position-awareness | Dual-agent (directional reasoning vs. risk-aware position adjustment), multi-timescale rewards | Position management focus, single-paradigm | Medium |
| FinCom: Financial Multi-Agent Demo with Disagree-or-Commit Deliberation (arXiv 2606.00939, 2026-06) | arXiv preprint | Multi-agent analysis-report quality | Research/quant/risk-management role committee with disagree-or-commit protocol | Report-quality system, not a live trading/position-sizing decision; no drawdown evaluation | Medium |
| StockBench: Can LLM Agents Trade Stocks Profitably In Real-World Markets? (arXiv 2510.02209, 2025) | arXiv preprint (benchmark) | Lack of contamination-controlled LLM trading benchmarks | Live/real-market backtesting benchmark | Benchmark, not method | Medium |
| InvestorBench (arXiv 2412.18174, 2024) | arXiv preprint (benchmark) | No standardized multi-task financial decision benchmark for LLM agents | Multi-task benchmark suite (stock/portfolio/crypto) | Benchmark, not method | Medium |
| PortBench (arXiv 2605.27887, 2026) | arXiv preprint (benchmark) | Portfolio benchmarks ignore cross-asset correlation / pipeline realism | Correlation-aware, full-pipeline evaluation protocol | Benchmark, not method | Medium |
| When Agents Trade: Live Multi-Market Trading Benchmark for LLM Agents (arXiv 2510.11695, 2025) | arXiv preprint (benchmark) | Static/single-market benchmarks miss live multi-market behavior | Live multi-market trading benchmark | Benchmark; **note**: replaces an unverified prior-pass reference to "Agent-Market-Arena," which does not resolve to a real title | Medium |
| TradeTrap: Are LLM-based Trading Agents Truly Reliable and Faithful? (arXiv 2512.02261) | arXiv preprint | LLM trading-agent reliability/faithfulness under adversarial conditions | Evaluates multiple LLM-agent repos (AI-Trader, NOFX, ValueCell, TradingAgents, AutoGPT variants) under prompt injection / poisoned RAG / jailbreak | **Single paradigm** (LLM-agents-only); no unified schema across capability layers; focus is adversarial faithfulness, not calibration/contradiction auditing | High — closest conceptual neighbor to this project's *overall audit framing*, must be cited in the positioning report's related work |
| Toward Reliable Evaluation of LLM-Based Financial Multi-Agent Systems (arXiv 2603.27539, 2026) | arXiv preprint | Coordination/reliability concerns in financial multi-agent systems | Hierarchical manager-arbitrates-specialists evaluation framing | Notes debate architectures "improve calibration under signal ambiguity" but about deliberation quality, not outcome-calibration fusion weighting | Medium |
| What Twelve LLM Agent Benchmark Papers Disclose About Themselves (arXiv 2605.21404, 2026-05) | arXiv preprint (meta-audit) | Do financial/agent benchmark papers disclose enough methodology (cost, harness spec) to trust their claims? | Audits 12 benchmark papers on a disclosure rubric; finds financial/agent benchmarks score 0.38/1.0 vs. 0.66/1.0 for classical static benchmarks | Not a competing method — a motivating citation for why a reliability/provenance-audit framing (this project's CLAUDE.md §4 provenance rules) is needed in this sub-field | Medium — motivation citation, found via a parallel-session literature pass |
| UniFinEval: Unified Evaluation of Financial Multimodal Models across Text, Images and Videos (arXiv 2601.22162) | arXiv preprint | No unified benchmark across financial input modalities | 10 MLLMs on 3,767 QA pairs, 5 reasoning scenarios | Unifies input *modalities*, not system *paradigms* — name-collision risk only ("unified... financial... evaluation"), not a scope competitor | Low — one-line disambiguating footnote only |

## 3. Calibration, stability, and determinism literature

| Paper | Venue | Problem | Method | Difference | Citation value |
|---|---|---|---|---|---|
| The Confidence Dichotomy (arXiv 2601.07264, 2026, ACL 2026 long paper 2026.acl-long.520) | ACL 2026 | Tool-use LLM agent calibration varies by mechanism | Conditions calibration analysis on **tool-type/mechanism category** | Single paradigm (LLM tool-use), non-finance; axis is tool-type not confidence-production-mechanism; no stability angle | High — closest precedent for Claim 2's "confidence-kind-conditioned calibration" |
| When Agents Disagree With Themselves (arXiv 2602.11619, 2026) | arXiv preprint | Reliability of repeated LLM outputs | Repeated-run output-variance as a reliability signal, single-LLM self-consistency | Non-finance, single paradigm (LLM ReAct), within-agent QA self-consistency, not cross-system numeric-output stability on trading decisions | High — closest precedent for Claim 2's stability diagnostic |
| Replayable Financial Agents / DFAH (arXiv 2601.15322, 2026) | arXiv preprint | Determinism of financial LLM tool-agents | Repeated-input determinism measurement in finance; finds determinism-vs-accuracy **decorrelation** | Single paradigm (LLM tool-agents only), determinism-vs-accuracy not determinism-vs-calibration, benchmark tasks not real deployed adapters against forward returns | High — direct finance-domain collision on the stability half of Claim 2, must be cited and distinguished |
| From Accuracy to Auditability (arXiv 2605.23955, 2026) | arXiv preprint (survey + experiments) | Determinism across financial ML modalities | Broadest cross-modality (tabular/GNN/LLM) financial determinism survey | Credit/fraud/AML focus not trading/alpha; no calibration-vs-forward-returns angle; no unified harness-level repeated-query diagnostic | Medium-High |
| CAGE-CAL (arXiv 2605.30653, 2026) | arXiv preprint | Calibration across heterogeneous LLM panels | Names heterogeneous-agent calibration as underexplored | Heterogeneity = different LLMs in a panel, not different algorithmic paradigms; non-finance | Medium |
| FinPersona-Bench (arXiv 2606.31522, 2026) | arXiv preprint | Behavioral-mandate consistency in finance | "Stability" framing for long-horizon behavioral drift | Different construct (mandate drift, not repeated-identical-query variance); synthetic market, LLM-only | Medium |
| Calibration in Deep Learning: A Survey of the State-of-the-Art (arXiv 2308.01222) | arXiv survey | General ML confidence calibration | Survey (ECE, reliability diagrams, temperature scaling, etc.) | Domain-agnostic; not applied to finance or cross-paradigm systems — use as the generic ML-calibration citation anchor, distinct from ICAIF's pricing-calibration usage | Medium — background/terminology anchor |
| Cross-Model Disagreement as a Label-Free Correctness Signal (arXiv 2603.25450, 2026-03) | arXiv preprint | Using inter-model disagreement as a correctness proxy | Cross-model perplexity/entropy disagreement | General LLM correctness detection (MMLU/TriviaQA/GSM8K), no finance, no regime conditioning | Medium — methodological precedent for treating disagreement as a reliability signal |
| Harnessing Multiple Large Language Models: A Survey on LLM Ensemble (arXiv 2502.18036, 2025) | arXiv survey | No systematic LLM-ensemble taxonomy | Taxonomy: ensemble-before/-during/-after-inference | General-domain, not finance-specific | Medium — generic-ensemble background contrast |

## 4. Regime-conditioned reliability & risk literature

| Paper | Venue | Problem | Method | Difference | Citation value |
|---|---|---|---|---|---|
| Ovadia et al., "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift" | NeurIPS 2019 | General ML calibration under distribution shift | Benchmark of calibration methods under shift | Non-finance, single-model — establishes that the *general* claim (calibration degrades under distribution shift) is not novel; found via a parallel-session Codex Phase-C pass as a closer non-finance precedent than the finance-specific analogs below. The finance-specific, multi-*system*-audit framing (Claim 3) remains the open question this precedent narrows but does not close | High — must cite to preempt a reviewer citing it first |
| RegimeFolio: Regime Aware ML System for Sectoral Portfolio Optimization (arXiv 2510.14986, 2025-10) | arXiv preprint | Portfolio optimization under regime shifts | Regime-specific retraining + stability-weighted model selection within one system's model zoo | Optimizes *for* regime (builds), does not audit whether pre-existing systems' *reliability* varies *by* regime; single system | High — must cite and distinguish "audit vs. build" for Claim 3 |
| Taming Tail Risk in Financial Markets: Conformal Risk Control for Nonstationary Portfolio VaR (arXiv 2602.03903, 2026-02) | arXiv preprint | VaR coverage under regime shift | Regime-weighted conformal calibration of one predictive pipeline's VaR buffers | Single-model, single-metric (VaR coverage) *correction*, not a cross-system reliability *audit* | Medium-High |
| RareCP: Regime-Aware Retrieval for Efficient Conformal Prediction (arXiv 2605.08857, 2026-05) | arXiv preprint | Adapting conformal intervals to "distinct error regimes" | Retrieval-based mixture-of-experts calibration within one integrated conformal model | Regime-aware *method* for one model, not a cross-system audit | Medium |
| Test-Time Adaptation for Non-stationary Time Series (arXiv 2602.00073, 2026-02) | arXiv preprint | Adapting one forecasting model to regime shift | Test-time adaptation mechanism | Adaptation method, single-model, not a reliability measurement study | Medium |
| Deep Learning for Financial Time Series: Large-Scale Benchmark of Risk-Adjusted Performance (arXiv 2603.01820, 2026-03) | arXiv preprint | Benchmarking architecture families incl. a calibration/ECE metric panel | 5 architecture families, 2010–2025 multi-asset, 10-dimension panel incl. parse-failure rate + ECE; notes regime-sensitive behavior qualitatively | Author-trained architecture families within one framework, not independently-published real systems; regime-sensitivity is a qualitative note on returns, not an ECE-by-regime table | Medium-High — closest scale/panel-design analog for Claim 3's "26-system evaluation surface" framing |
| DeepScalper: Risk-Aware RL Framework for Intraday Trading (arXiv 2201.09058, 2021/22) | ICAIF-adjacent / q-fin.TR | Risk-aware intraday RL | Dueling Q-network + action branching, hindsight bonus, risk-aware auxiliary task | Single RL paradigm; establishes risk-aware RL as a mature ICAIF-adjacent sub-theme (same lineage as FineFT, ~4 yrs earlier) | Medium — background, establishes lineage |
| Bayesian Robust Financial Trading with Adversarial Synthetic Market Data (arXiv 2601.17008, 2026) | arXiv preprint | Strategy failure under distribution shift | Bayesian robustness + adversarial synthetic scenarios | Robustness via synthetic-data augmentation, not multi-system reliability fusion | Medium |

## 5. Selective prediction / abstention literature

| Paper | Venue | Problem | Method | Difference | Citation value |
|---|---|---|---|---|---|
| From Debate to Decision: Conformal Social Choice for Safe Multi-Agent Deliberation (arXiv 2604.07667, 2026-04, AWS/HSBC) | arXiv preprint | When to trust multi-agent LLM debate | Converts debate into calibrated act-vs-escalate decisions via conformal prediction over 3 heterogeneous LLM agents | General QA/reasoning (MMLU-Pro), zero finance/risk-metric overlap — but structurally the closest **mechanism** analog (contradiction → abstain/escalate as a distinct layer from fusion) | High — cite for mechanism precedent despite zero domain overlap; one author affiliation (HSBC) signals a plausible fast finance follow-up |
| Budgeted Act-or-Defer Multi-Agent LLM Deliberation with Local Reliability Bounds (arXiv 2606.29654, 2026-06, AWS/GM) | arXiv preprint | Deciding when to defer multi-agent debate to a human | KNN lower-confidence-bound act-or-defer policy | General reasoning benchmarks, homogeneous debate rounds, no finance/risk metric | Medium-High |
| AgentAbstain: Do LLM Agents Know When Not to Act? (arXiv 2607.10059, 2026-07, UIUC) | arXiv preprint (benchmark) | General tool-use agent abstention | 263 paired tasks, 8-scenario taxonomy, 42 environments, 17 frontier LLMs | Single-agent tool-use tasks, not finance, not cross-agent structural contradiction, not portfolio risk | Medium — establishes abstention-as-first-class-capability as a live 2026 research direction |
| Trading via Selective Classification (arXiv 2110.14914, 2021) | arXiv preprint | Reject-option classification for trading | Classic selective classification applied to intraday futures | Single-model, no multi-agent contradiction signal; foundational pattern to differentiate from | Medium — foundational citation |
| Predictor-Rejector Multi-Class Abstention: Theoretical Analysis and Algorithms (arXiv 2310.14772) | arXiv preprint (theory) | Formal abstention theory | Predictor-rejector pair formalism | General ML theory, not finance/multi-agent | Medium — theoretical grounding citation |
| Online Conformal Abstention for Factuality Control Under Adversarial Bandit Feedback (arXiv 2506.14067) | arXiv preprint | LLM factuality control | Conformal abstention method | Non-finance, non-multi-agent | Low-Medium |

## 6. ICAIF background / survey / establishing-lineage papers

| Paper | Venue | Problem | Method | Difference | Citation value |
|---|---|---|---|---|---|
| Large Language Models in Finance: A Survey (DOI 10.1145/3604237.3626869) | **ICAIF 2023** (confirmed via Crossref) | State of LLM applications in finance | Survey | Background; confirms ICAIF's LLM-in-finance lineage since 2023 | Medium — confirmed-venue background anchor |
| Reinforcement Learning for Quantitative Trading (DOI 10.1145/3582560) | ACM TIST, 2023 | RL-for-QT taxonomy gap | Survey (Bo An's group — same lineage as FineFT/DeepScalper) | Background; confirms risk-aware RL is an established sub-theme | Medium |
| Ensemble RL through Classifier Models: Enhancing Risk-Return Trade-offs (arXiv 2502.17518, 2025-02) | arXiv preprint | RL + classical-ML ensemble for trading | Combines RL (A2C/PPO/SAC) + classifiers (SVM/DT/LR), variance-threshold selection | Same-paradigm ensemble within one framework, not cross-system real published projects; no contradiction taxonomy or calibration-vs-self-report distinction | Medium — secondary prior art for Claim 1 |
| Trade-offs in Financial AI: Explainability in a Trilemma with Accuracy and Compliance (arXiv 2602.01368, 2026) | arXiv preprint | XAI/accuracy/compliance tension | Positional/framing analysis | Interpretability framed as compliance issue, not a technical XAI method; evidence that ICAIF's interpretability track is thin/compliance-flavored | Low-Medium |
| Towards Trustworthy Agentic AI: comprehensive survey (arXiv 2605.23989, 2026) | arXiv survey | No unified trustworthy-agentic-AI framework | Survey + unified metrics/benchmark hub | General-domain, not finance-specific; shows "trustworthy AI agents" is a broader 2026 trend this project's finance work sits downstream of | Medium — background |
| Crowd-Calibrator: Can Annotator Disagreement Inform Calibration in Subjective Tasks? (arXiv 2408.14141) | arXiv preprint | Disagreement as a calibration signal | Crowd-annotation NLP setting | Weak overlap — crowd-annotation, not multi-system finance | Low |
| HARLF: Hierarchical RL and Lightweight LLM-Driven Sentiment Integration for Portfolio Optimization (arXiv 2507.18560) | arXiv preprint | Multi-modal (price + sentiment) portfolio optimization | Single internally-trained 3-layer RL architecture, simple concatenation fusion of two data modalities | Fuses data *modalities* inside one training pipeline, not independently-published heterogeneous *systems*; no calibration/contradiction weighting | Low — ruled out as competing prior art, cite only if a reviewer might conflate "hierarchical fusion" language |

---

## Cross-cutting terminology note (load-bearing for the whole report)

**"Calibration" is a trap term at ICAIF.** Of 7 ICAIF 2023–2025 papers with
"calibrat-" in the title, 6/7 (86%) mean pricing/simulation/ABM **parameter**
calibration (fitting a stochastic-volatility or agent-based-market model to
observed data), not ML confidence calibration. TrustTrade itself uses
"calibrates" in a third, colloquial sense (behavioral risk-profile
adjustment). Every use of "calibration" in this project's paper draft must
be qualified on first use: *"probabilistic/confidence calibration (predicted
confidence vs. empirical accuracy), as distinct from ICAIF's more common
pricing/simulation-model parameter-calibration usage."* See
`NOVELTY_AUDIT.md` and `ICAIF_POSITIONING_REPORT.md` for how this shapes
headline vocabulary.

## Provenance

- Crossref REST API: 286 real, DOI-verified ICAIF 2023–2025 paper titles
  (proceedings DOIs `10.1145/3604237`, `10.1145/3677052`, `10.1145/3768292`).
- arXiv API, Semantic Scholar `paper`/`search`, OpenAlex: cross-verification
  of all arXiv-ID papers above; several load-bearing abstracts (TrustTrade,
  FineFT) were directly WebFetched, not taken from search-snippet synthesis.
- `verify_papers.py` pre-search hallucination check: run against the arXiv
  IDs cited in Claims 1, 3, and 5's dossiers — 0.0 hallucination rate in all
  runs.
- Full search-query logs and per-claim reasoning trails: see
  `_working/ICAIF_TREND_RESEARCH.md`, `_working/LIT_LANDSCAPE_2026.md`, and
  `_working/NOVELTY_DOSSIER_claim{1..5}.md`.
