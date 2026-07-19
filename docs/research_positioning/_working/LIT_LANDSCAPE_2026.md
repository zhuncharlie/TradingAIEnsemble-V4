# Literature Landscape 2026 — ICAIF Positioning (Reliability-Aware Fusion & Routing)

Generated via genuine invocation of ARIS skills `research-lit`, `semantic-scholar`, and
`openalex` (helpers resolved at `.aris/tools/{arxiv_fetch,semantic_scholar_fetch,openalex_fetch}.py`).
Every paper below was independently retrieved and, where marked ✅, cross-verified via a live
API call (arXiv API and/or Semantic Scholar `paper` lookup and/or OpenAlex `work`/`search`).
No paper is listed from memory alone. Sibling `novelty-check` audits are running deep
per-claim checks in parallel — this document is breadth/trend-mapping only, not a
per-claim adjudication.

---

## 1. ICAIF 2023–2026 Theme Trend Ranking

Methodology: OpenAlex + Semantic Scholar search anchored on ICAIF-adjacent venues
(`dl.acm.org` ICAIF proceedings, e.g. DOI prefix `10.1145/3604237.*` for ICAIF'23) plus
arXiv theme sweeps. Semantic Scholar's live venue-filtered ICAIF query was rate-limited
(HTTP 429) after repeated retries; ranking below is therefore triangulated from
OpenAlex venue hits, arXiv volume/recency per theme, and known ICAIF program patterns
(FinRL/quant-trading and multi-agent LLM tracks are consistently present across
ICAIF'23–'25 proceedings pages visible via the DOI prefix). Flagged where confidence is
lower.

| Rank | Theme | Evidence of representation | Confidence |
|---|---|---|---|
| 1 | **Trustworthy AI agents** (safety/robustness/hallucination in LLM finance agents) | Largest and fastest-growing arXiv volume found (TrustTrade, TradingAgents, FinCon, FinPos, StockBench, InvestorBench, PortBench, CLQT, "When Agents Trade" all 2024–2026); matches ICAIF's recent emphasis on agentic evaluation/benchmarks | High |
| 2 | **Multi-agent finance** | Heavily overlaps with #1 — TradingAgents, FinCon, TrustTrade, CLQT's "committee of specialized roles" all multi-agent; this is the dominant *architecture* pattern even when the paper's stated theme is trust/robustness | High |
| 3 | **Risk-aware AI** | FineFT (KDD, not ICAIF, but same research community/authors as ICAIF risk-RL papers e.g. DeepScalper, Bo An's group), Bayesian Robust Financial Trading (2601.17008), FINRS (2511.12599) — steady, well-established sub-theme since ICAIF's founding | High |
| 4 | **Decision-focused learning** | Real but narrower: "Estimating Covariance for GMV Portfolio: A Decision-Focused Learning Approach" (2508.10776), "Decision-focused Sparse Tangent Portfolio Optimization" (2607.00581) — active but smaller volume, more OR/finance-math flavored than AI-agent flavored | Medium |
| 5 | **Robustness** (distribution shift / adversarial) | Present but mostly folded into "trustworthy agents" or risk-RL papers rather than standalone; dedicated distribution-shift-for-trading papers are comparatively rare | Medium |
| 6 | **Interpretability** | Weakest standalone signal in finance-specific search — general XAI surveys (e.g. Hassija et al., Cognitive Computation, 1822 citations) dominate but are not finance-specific; finance-specific hit was "Trade-offs in Financial AI: Explainability in a Trilemma with Accuracy and Compliance" (2602.01368) — thin, mostly framed as compliance/regulatory rather than ML-XAI | Medium-Low |
| 7 | **Calibration** (ML confidence calibration) | Weakest and most confusable theme — see §3 below. Very little dedicated ML-confidence-calibration work specific to trading agents; most "calibration" hits are actually pricing-model/simulation calibration | Low |

**Headline for positioning**: the field is converging hard on *agentic trust/robustness/multi-agent* as the dominant 2024–2026 ICAIF-adjacent theme — exactly where this project's fusion/routing claim sits. That is good for relevance but bad for novelty margin: this is now a crowded corner, and the two closest anchors (TrustTrade, FineFT) are both from 2025–2026, i.e. very recent and squarely in this space. Calibration and interpretability remain comparatively under-served **as ML-specific themes**, which could be a differentiation lever if the project's reliability/consistency signals are framed explicitly as calibration/interpretability contributions rather than just "fusion."

---

## 2. Load-Bearing Paper Re-Verification (full abstract, not just title)

### TrustTrade — arXiv 2603.22567 ✅ VERIFIED (via arXiv API + Semantic Scholar `paper` lookup)

- **Full title**: "TrustTrade: Human-Inspired Selective Consensus Reduces Decision Uncertainty in LLM Trading Agents"
- **Authors**: Minghan Li, Rachel Gonsalves, Weiyue Li, Sung-Hoon Yoon, Mengyu Wang
- **Institution**: not disclosed in arXiv/S2 metadata (no affiliation field populated by either API); would need PDF header check to confirm — **not verified**, do not assert an institution in the positioning report.
- **Venue**: arXiv preprint only (S2 record: `venue: "arXiv.org"`, 0 citations, no DOI beyond the arXiv DOI). **Not confirmed as ICAIF-accepted** — treat as an unreviewed preprint until/unless proceedings inclusion is separately confirmed.
- **Exact mechanism** (from abstract): multiple *independent LLM agents* (same underlying paradigm — LLM instances) produce signals; TrustTrade aggregates them via cross-agent semantic/numerical **consistency-weighted consensus** (discount divergent/weakly-grounded/temporally-inconsistent inputs), plus deterministic temporal anchors and a test-time reflective memory for risk-preference adaptation. Evaluated via backtesting in 2024 Q1 / 2026 Q1 high-noise regimes.
- **Crux check — does it span multiple heterogeneous real-world paradigms?** **No.** The abstract explicitly frames the problem as "aggregating information from multiple independent LLM agents" — it is a homogeneous-paradigm ensemble (multiple LLM instances/roles), not a fusion across genuinely different system classes (LLM agent + classical RL policy + portfolio optimizer + sentiment model, etc.). This confirms the project's differentiation claim survives against TrustTrade **as long as the paper's fusion claim is specifically "heterogeneous real-world paradigms," not just "multi-source."**

### FineFT — arXiv 2512.23773 ✅ VERIFIED (via arXiv API + Semantic Scholar `paper` lookup)

- **Full title**: "FineFT: Efficient and Risk-Aware Ensemble Reinforcement Learning for Futures Trading"
- **Authors**: Molei Qin, Xinyu Cai, Yewen Li, Haochong Xia, Chuqiao Zong, Shuo Sun, Xinrun Wang, Bo An
- **Institution**: authorship pattern (Shuo Sun, Bo An, Xinrun Wang) matches the Nanyang Technological University (NTU Singapore) quant-RL group also behind DeepScalper (2201.09058) and "Reinforcement Learning for Quantitative Trading" (ACM TIST, DOI 10.1145/3582560) — consistent group, high confidence, but not an official affiliation string from the API.
- **IMPORTANT CORRECTION vs. prior pass**: Semantic Scholar's `publicationVenue` field resolves FineFT to **"Knowledge Discovery and Data Mining" (ACM SIGKDD), DOI 10.1145/3770854.3780187** — i.e. this paper is (or is slated to be) a **KDD** paper, not an ICAIF paper. If the prior positioning pass cited it as ICAIF prior art, that venue attribution needs correcting.
- **Exact mechanism** (from abstract): three-stage **ensemble of Q-learners within a single RL framework** — (I) ensemble TD-error-guided selective updates for training stability, (II) profitability-based filtering + VAE-based market-regime/capability-boundary modeling, (III) VAE-guided dynamic routing between the filtered ensemble and a conservative fallback policy. Evaluated on high-leverage crypto futures.
- **Crux check — does it span multiple heterogeneous real-world paradigms?** **No.** This is explicitly "ensemble reinforcement learning" — a self-trained pool of Q-learners from one RL framework/algorithm family, routed via VAE-based regime detection. It does **not** combine an RL policy with an LLM agent, a classical portfolio optimizer, or a sentiment model. The project's differentiation claim (fusion/routing across *heterogeneous real-world systems*, not one framework's internally-trained ensemble) survives against FineFT too, and the "routing via VAE capability-boundary detection" mechanism is close enough in *spirit* (reliability/regime-aware routing) that it should be cited as the closest routing-methodology precedent, even though it is single-paradigm.

**Net effect on differentiation claim**: both anchors hold up under full-abstract re-verification. The crux distinction ("heterogeneous real-world paradigms" vs. "multiple instances of one paradigm") is real and should be stated explicitly and prominently in any related-work section, because both papers use the word "ensemble"/"consensus" in ways a careless reader could conflate with this project's cross-paradigm fusion claim.

---

## 3. "Calibration" Terminology Trap — Confirmed

Re-checked via arXiv + OpenAlex searches on "calibration" in finance/AI contexts. **The trap is real and confirmed still active in 2025–2026 literature**:

- Searches for "confidence calibration LLM financial prediction" returned mostly **generic NLP calibration papers** (e.g. "Calibrating the Confidence of Large Language Models by Eliciting Fidelity", 2404.02655; "VL-Calibration" for vision-language models, 2604.09529) — not finance-specific ML-confidence-calibration work.
- Meanwhile, "calibration" in finance/ICAIF-adjacent venues overwhelmingly means **fitting a pricing or simulation model's parameters to market data** (e.g., stochastic volatility model calibration, market-simulator calibration, agent-based-model calibration to historical order flow) — a completely different sense than "is the model's stated confidence/probability well-calibrated to its empirical accuracy."
- TrustTrade itself uses "calibrates" in its abstract in a third, colloquial sense ("TrustTrade calibrates LLM trading behavior from extreme risk-return regimes toward a human-aligned... profile") — i.e., "calibration" as behavioral adjustment, not statistical calibration either.

**Recommendation for the positioning report's wording**: Do not use the bare word "calibration" to describe this project's reliability/confidence-scoring contribution without immediately disambiguating — e.g. write "**probabilistic/confidence calibration** (in the statistical sense of predicted-confidence-matches-empirical-accuracy, as distinct from ICAIF's more common usage of 'calibration' for pricing/simulation-model fitting to market data)." This should be a standing footnote or parenthetical wherever "calibration" appears in the paper draft, not just in related work.

---

## 4. Literature Table

Legend: ✅ = live-verified this session (arXiv API and/or S2 `paper`/`search` and/or OpenAlex); all rows below are ✅ unless noted. Citation value = expected usefulness as a citation anchor for this project's related-work section (high = must-cite/closest prior art; medium = useful contrast/context; low = tangential/background).

| # | Paper | Venue | Year | Problem | Method | Difference from this project | Citation value |
|---|---|---|---|---|---|---|---|
| 1 | TrustTrade: Human-Inspired Selective Consensus Reduces Decision Uncertainty in LLM Trading Agents (arXiv 2603.22567) | arXiv preprint (not confirmed ICAIF-accepted) | 2026 | LLM trading agents' "uniform trust" in noisy multi-source info | Cross-agent consistency-weighted consensus among multiple LLM agent instances + temporal anchors + test-time reflective memory | Homogeneous paradigm (LLM-only ensemble), not cross-paradigm fusion; no formal reliability/confidence calibration framework | High (closest prior art, routing/consensus) |
| 2 | FineFT: Efficient and Risk-Aware Ensemble RL for Futures Trading (arXiv 2512.23773) | ACM SIGKDD (DOI 10.1145/3770854.3780187) | 2025/2026 | RL instability + lack of capability-boundary awareness under high leverage | 3-stage ensemble Q-learners + VAE-based regime/capability-boundary routing | Homogeneous paradigm (single RL framework's self-trained ensemble), not heterogeneous systems; venue is KDD not ICAIF | High (closest prior art, reliability-aware routing) |
| 3 | TradingAgents: Multi-Agents LLM Financial Trading Framework (arXiv 2412.20138) | arXiv preprint | 2024 | Single-agent LLM systems lack collaborative-firm-like structure | Role-specialized LLM agents (fundamental/sentiment/technical analysts, bull/bear researchers, risk team, trader) with debate-based synthesis | Multi-agent but all LLM-paradigm; no explicit reliability scoring or fusion of non-LLM system outputs | High |
| 4 | FinCon: Synthesized LLM Multi-Agent System with Conceptual Verbal Reinforcement (arXiv 2407.06567) | arXiv preprint | 2024 | Multi-source financial info synthesis + episodic belief updating | Manager-analyst hierarchy, self-critique risk-control component, verbal reinforcement propagation | LLM-only paradigm; belief propagation is intra-framework, not cross-paradigm reliability weighting | Medium-High |
| 5 | FinPos: A Position-Aware Trading Agent System for Real Financial Markets (arXiv 2510.27251) | arXiv preprint | 2025 | Existing agents lack continuous position-awareness | Dual-agent (directional reasoning vs. risk-aware position adjustment) + multi-timescale rewards | Position management focus, not reliability/fusion; single LLM-agent paradigm | Medium |
| 6 | StockBench: Can LLM Agents Trade Stocks Profitably In Real-world Markets? (arXiv 2510.02209) | arXiv preprint | 2025 | Lack of rigorous, contamination-controlled LLM trading benchmarks | Live/real-market backtesting benchmark for LLM trading agents | Benchmark, not a method; useful as an evaluation-protocol citation, not a competing fusion method | Medium (benchmark) |
| 7 | INVESTORBENCH: A Benchmark for Financial Decision-Making Tasks with LLM-based Agent (arXiv 2412.18174) | arXiv preprint | 2024 | No standardized benchmark spanning multiple financial decision task types for LLM agents | Multi-task benchmark suite (single stock, portfolio, crypto) for LLM-agent evaluation | Benchmark, not method | Medium (benchmark) |
| 8 | PortBench: A Correlation-Aware, Full-Pipeline Benchmark for LLM-Driven Portfolio Management (arXiv 2605.27887) | arXiv preprint | 2026 | Existing portfolio benchmarks ignore cross-asset correlation / full pipeline realism | Correlation-aware, full-pipeline evaluation protocol for LLM portfolio agents | Benchmark, not method | Medium (benchmark) |
| 9 | CLQT: A Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for Diagnostic Evaluation of LLM Portfolio-Management Agents (arXiv 2606.29771) | arXiv preprint | 2026 | Return-only ranking of LLM portfolio agents doesn't diagnose *why* agents succeed/fail; look-ahead leakage issues | 5-stage closed-loop cycle (gather/synthesize/allocate/execute/reflect), hash-chained audit trail, 5-axis capability scorecard (Coherence/Acuity/Composure/Discipline/Reliability), held-out LLM judge for self-preference-bias control | Benchmark/diagnostic tool, not a fusion method — but its "Reliability" axis and causal/audit-trail design overlap conceptually with this project's provenance requirements; worth citing for evaluation-protocol alignment | Medium-High (benchmark, methodologically adjacent) |
| 10 | When Agents Trade: Live Multi-Market Trading Benchmark for LLM Agents (arXiv 2510.11695) | arXiv preprint | 2025 | Static/single-market benchmarks don't capture live multi-market agent behavior | Live multi-market trading benchmark for LLM agents | Note: this is the closest verified match to a prior pass's "Agent-Market-Arena" reference; **that exact title does not verify** — treat "Agent-Market-Arena" as unconfirmed/possibly misremembered and use this paper's real title instead | Medium (benchmark; replaces unverified "Agent-Market-Arena") |
| 11 | Large Language Models in Finance: A Survey (DOI 10.1145/3604237.3626869) | **ICAIF 2023** (ACM) | 2023 | State of LLM applications in finance | Practical survey of two aspects: existing LLM applications, techniques for building finance-specific LLMs | Survey/background, not competing method; useful as an anchor confirming ICAIF's LLM-in-finance track lineage since 2023 | Medium (background, confirmed ICAIF venue) |
| 12 | Reinforcement Learning for Quantitative Trading (DOI 10.1145/3582560) | ACM Trans. Intelligent Systems and Technology | 2023 | Survey/framework gap in RL-for-QT | Survey + taxonomy (Bo An's group, same lineage as FineFT/DeepScalper) | Survey/background on RL-for-trading; confirms risk-aware-RL is an established, not novel, sub-theme | Medium (background) |
| 13 | DeepScalper: Risk-Aware RL Framework for Intraday Trading (arXiv 2201.09058) | ICAIF-adjacent / q-fin.TR | 2021/2022 | Existing RL misses fleeting intraday opportunities, needs risk-awareness | Dueling Q-network + action branching, hindsight-bonus reward, multi-modality market embedding, risk-aware auxiliary task | Single RL paradigm, risk-aware but not reliability-fusion across heterogeneous systems; establishes risk-aware-RL as a mature ICAIF-adjacent sub-theme (predates FineFT by ~4 yrs, same author lineage) | Medium |
| 14 | Bayesian Robust Financial Trading with Adversarial Synthetic Market Data (arXiv 2601.17008) | arXiv preprint | 2026 | Trading strategies fail under distribution shift / adversarial market regimes | Bayesian robustness + adversarially-generated synthetic market scenarios | Robustness via synthetic data augmentation, not multi-system reliability fusion | Medium |
| 15 | Estimating Covariance for GMV Portfolio: A Decision-Focused Learning Approach (arXiv 2508.10776) | arXiv preprint | 2025 | Two-stage covariance-estimation-then-optimize pipelines are suboptimal | End-to-end decision-focused learning of covariance estimator for min-variance portfolios | Decision-focused learning for one optimizer, not cross-system fusion/routing | Medium |
| 16 | Decision-focused Sparse Tangent Portfolio Optimization (arXiv 2607.00581) | arXiv preprint | 2026 | Sparse portfolio construction under decision-focused objectives | Decision-focused learning + sparsity-inducing tangent portfolio formulation | Same DFL sub-theme, single-optimizer scope | Low-Medium |
| 17 | Trade-offs in Financial AI: Explainability in a Trilemma with Accuracy and Compliance (arXiv 2602.01368) | arXiv preprint | 2026 | Explainability, accuracy, and regulatory compliance are in tension in financial AI | Framing/positional analysis of the trilemma | Interpretability framed as compliance issue, not technical XAI method; useful to show interpretability track is thin/compliance-flavored at ICAIF-adjacent venues | Low-Medium |
| 18 | Harnessing Multiple Large Language Models: A Survey on LLM Ensemble (arXiv 2502.18036) | arXiv preprint | 2025 | No systematic taxonomy of LLM-ensemble methods | Taxonomy: ensemble-before/-during/-after-inference | General-domain (not finance-specific); useful as the generic-ML-ensemble anchor to contrast against this project's domain-specific, cross-paradigm fusion | Medium (general ML background) |
| 19 | Towards Trustworthy Agentic AI: comprehensive survey of safety, robustness, privacy, system security (arXiv 2605.23989) | arXiv preprint | 2026 | No unified framework for trustworthy agentic AI evaluation | Survey + unified metrics/benchmark hub for agentic safety/robustness/privacy | General-domain trustworthy-agent survey, not finance-specific; useful to show "trustworthy AI agents" is a broader 2026 trend that finance/ICAIF work is downstream of | Medium (general background) |
| 20 | Reinforcement Learning for Quantitative Trading — recent advances (Mathematical Finance, DOI 10.1111/mafi.12382) | Mathematical Finance | 2023 | Survey of RL-in-finance methods and theory | Survey | Background/survey only | Low |
| 21 | Robust Risk-Sensitive Reinforcement Learning Agents for Trading Markets (arXiv 2107.08083) | arXiv preprint | 2021 | Multi-agent trading markets need risk-awareness + robustness to adversarial perturbation | Risk-averse objectives + variance reduction + adversarial multi-agent RL | Older (2021) foundational risk-RL work; single-paradigm | Low |
| 22 | FinPT: Financial Risk Prediction with Profile Tuning on Pretrained Foundation Models (arXiv 2308.00065) | arXiv preprint | 2023 | Financial risk prediction under-uses foundation model profile-tuning | Profile-tuning paradigm applied to financial risk prediction | Tangential (risk prediction, not agent fusion/routing) | Low |

**Papers explicitly NOT included** (searched, no verified match — flag for the sibling novelty-check audits and for correcting any prior-pass assumption): a title exactly matching **"Agent-Market-Arena"** did not verify via arXiv/OpenAlex search; the closest real paper is row 10 above. All other four named benchmarks (StockBench, InvestorBench, PortBench, CLQT) verified as real, existing papers with the titles as previously used — no corrections needed there.

---

## 5. Summary of Key Findings for the Report-Back

- Confirmed real, with corrected venue: **FineFT is a KDD paper (DOI 10.1145/3770854.3780187), not ICAIF** — correct this if asserted elsewhere.
- **TrustTrade** is arXiv-only, not confirmed as ICAIF-accepted; 0 citations as of this check.
- Both anchors, on full-abstract re-read, are confirmed **single-paradigm ensembles** (LLM-only for TrustTrade; one RL framework's Q-learner pool for FineFT) — the project's "heterogeneous real-world paradigms" differentiation claim holds, but must be stated precisely to avoid conflation.
- **"Calibration" terminology trap confirmed live**: ICAIF/finance-AI literature uses "calibration" predominantly for pricing/simulation-model fitting (and TrustTrade even uses it colloquially for behavioral adjustment) — this project must disambiguate "confidence calibration" explicitly wherever used.
- New closest-prior-art / collision-risk candidate surfaced: **CLQT (arXiv 2606.29771)** — its 5-axis scorecard includes an explicit "Reliability" axis and a hash-chained causal audit trail, conceptually adjacent to this project's provenance/reliability requirements (CONTRACT §4). It's a diagnostic benchmark, not a fusion method, but should be cited and distinguished.
- Benchmark corrections: StockBench, InvestorBench, PortBench, CLQT all verified real. **"Agent-Market-Arena" does not verify** as an exact title — closest real analog is "When Agents Trade: Live Multi-Market Trading Benchmark for LLM Agents" (arXiv 2510.11695); recommend replacing the unverified name in any prior draft.
