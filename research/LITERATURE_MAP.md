# RELATED_WORK_MAP — ICAIF 2023–2025 + adjacent arXiv/venue work

**Status**: investigation-only. No production code, adapter, or `CONTRACT/` file
was read for the purpose of modification; this document and its sibling
reports (`ICAIF_POSITIONING.md`, `NOVELTY_AUDIT.md`,
`CANDIDATE_PAPER_DIRECTION.md`) are the entire deliverable.

**How this was built**: real accepted-paper title lists were fetched directly
from `icaif25.org/accepted-papers/` (169 papers, ICAIF'25), `ai-finance.org/
technical-program/` (100 papers, ICAIF'24), and `ai-finance.org/
icaif-23-accepted-papers/` (79 papers, ICAIF'23) — not reconstructed from
memory. Table below is a curated subset (titles that plausibly touch
calibration / robustness / trustworthy AI / risk-aware decision making /
agent reliability / interpretability / uncertainty quantification /
decision-focused learning / multi-agent finance / LLM finance agents),
plus a handful of non-ICAIF arXiv/venue papers found while checking whether
this project's candidate directions collide with existing work. Full raw
title lists (113/100/79 titles respectively) are preserved in this session's
tool output for the project lead to re-derive the table from, if needed —
not duplicated here in full to keep this document reviewable.

**Coverage caveats, stated plainly**: (1) ICAIF'25 has 169 accepted papers;
only 113 titles were retrievable from the single accepted-papers page fetch
in this session — the remaining ~56 are not represented below. (2) No
full-text PDF was opened for any paper in this table — classification is
from title (+ abstract snippet where the search engine surfaced one), so a
paper whose real method differs sharply from what its title implies could be
mis-bucketed; treat the "Difference from us" column as a first-pass filter,
not a substitute for reading the paper before final submission. (3) ICAIF
2026 (Milan) has no accepted-papers list published yet (conference is in the
future relative to this search) — not represented.

---

## Table

| Paper | Year | Problem | Method | Difference from us |
|---|---|---|---|---|
| Bayesian Networks Improve Out-of-Distribution Calibration for Agribusiness Delinquency Risk Assessment | 2023 (ICAIF) | Whether a single credit-risk model's predicted probabilities stay calibrated under distribution shift | Bayesian network probability calibration | Single model, single domain (credit delinquency), not cross-agent/cross-paradigm; closest ICAIF paper to our sense of "calibration" (ML confidence, not price-model calibration) |
| Calibration of Derivative Pricing Models: a Multi-Agent Reinforcement Learning Perspective | 2023 (ICAIF) | Fitting a pricing model's parameters to match observed market prices | MARL-driven parameter search | "Calibration" here means model-to-market-price fitting (financial-engineering sense), a different concept from ML confidence calibration; "multi-agent" here means RL agents cooperating on one optimization, not multiple independent trading systems being compared |
| Deep Calibration of Market Simulations using Neural Density Estimators and Embedding Networks | 2023 (ICAIF) | Same price-model-calibration sense as above | Simulation-based inference | Same terminology-trap note as above |
| Gradient-Assisted Calibration for Financial Agent-Based Models | 2023 (ICAIF) | ABM parameter calibration | Gradient-assisted search | Same terminology-trap note |
| Improving the Robustness of Financial Models through Identification of the Minimal Vulnerable Feature Set | 2023 (ICAIF) | Adversarial robustness of one predictive model | Minimal feature-set vulnerability analysis | Single-model robustness, not cross-agent reliability under real-world heterogeneity |
| Large Language Models in Finance: A Survey | 2023 (ICAIF) | Survey of LLM applications in finance | Literature synthesis | A survey, not an empirical multi-system study; worth citing for related-work framing, not a collision |
| Margin Trader: A Reinforcement Learning Framework for Portfolio Management with Margin and Constraints | 2023 (ICAIF) | Single-agent constrained portfolio RL | RL with margin constraints | Single system, not a cross-system comparison/fusion study |
| Numin: Weighted-Majority Ensembles for Intraday Trading | 2024 (ICAIF) | Whether weighted ensembling beats simple majority for intraday signals | Weighted-majority ensemble of (implicitly homogeneous) predictive models | Ensembles same-paradigm predictors (all quant signals), not heterogeneous system-TYPES (LLM debate vs. DRL vs. GA vs. GBM); no calibration/contradiction diagnosis layer; closest ICAIF paper to our Layer-2 fusion question but narrower scope |
| Dynamic Reinforced Ensemble using Bayesian Optimization for Stock Trading | 2024 (ICAIF) | Ensemble weight tuning via Bayesian optimization | BayesOpt over ensemble weights | Same "ensemble of homogeneous models" scope limit as Numin |
| Adaptive Sample Weighting with Regime-Aware Meta-Learning Framework for Financial Forecasting | 2024/2025 (ICAIF'25, KAIST) | Whether per-sample loss weights should vary by market regime, for one forecasting model | Regime-embedding + MLP-predicted sample weights | Single-model regime-adaptive training, not cross-agent regime-conditioned routing across independently-developed systems; closest ICAIF paper to our Direction C (routing) but at the wrong level (training-time sample weighting vs. inference-time system selection) |
| Enhanced Local Explainability and Trust Scores with Random Forest Proximities | 2024 (ICAIF) | Per-prediction trust score for one RF model | Proximity-based local explainability | Single-model trust score, not cross-agent reliability comparison |
| Reducing Return Volatility in Neural Network-Based Asset Allocation via Formal Verification and Certified Training | 2024 (ICAIF) | Certified robustness of one allocation network | Formal verification | Single-model formal guarantees, orthogonal to our empirical cross-system reliability question |
| FairNNV: The Neural Network Verification Tool For Certifying Fairness | 2024 (ICAIF) | Fairness certification tooling | Formal verification | Trustworthy-AI adjacent (fairness), not reliability/contradiction across heterogeneous agents |
| Recent Trends, GenAI Crime Wave & Co-Evolutionary AI: AI versus AI in Financial Crimes & Detection | 2024 (ICAIF) | Adversarial dynamics between generative fraud and detection AI | Position/survey-style | Different application (fraud), not trading-decision reliability |
| FactorMAD: A Multi-Agent Debate Framework Based on Large Language Models for Interpretable Stock Alpha Factor Mining | 2025 (ICAIF) | Whether LLM-agent debate improves interpretable alpha-factor discovery | Multi-agent LLM debate | All agents are LLM instances in one debate protocol (same paradigm); not a comparison across independently-published, architecturally-heterogeneous systems (LLM vs. RL vs. GP vs. GBM); no confidence-calibration or fusion-quality evaluation layer |
| A Role-Aware Multi-Agent Framework for Financial Education QA with LLMs | 2025 (ICAIF) | Multi-agent LLM roles for QA | Role-specialized LLM agents | Different task (QA, not trading decisions); same "multi-LLM-agent, one paradigm" scope limit |
| Large Language Model Agents for Investment Management: Foundations, Benchmarks, and Research Frontiers | 2025 (ICAIF) | Survey/position paper on LLM investment agents | Literature synthesis + benchmark survey | Survey, not an empirical cross-paradigm study; useful as a related-work anchor and to check whether it already names a research agenda that overlaps ours |
| Predictive Uncertainty Quantification for Financial DNN Using Regular Vine Copula | 2025 (ICAIF) | UQ for one DNN's point forecasts | Copula-based UQ | Single-model UQ method, not cross-agent calibration comparison; closest ICAIF paper to our "UQ" theme in the ML sense |
| Scaling Conditional Autoencoders for Portfolio Optimization via Uncertainty-Aware Factor Selection | 2025 (ICAIF) | UQ-guided factor selection for one portfolio-optimization pipeline | Conditional autoencoder + UQ | Single-pipeline, not multi-system |
| Similarity-based Conformal Prediction using Random Forest Proximities | 2025 (ICAIF) | Selective/conformal prediction for one RF model | Conformal prediction | Single-model abstention mechanism; closest ICAIF paper to our Layer-2 "abstention" idea, but not cross-agent |
| Estimating Covariance for Global Minimum Variance Portfolio: A Decision-Focused Learning Approach | 2025 (ICAIF) | Decision-focused learning for one covariance-estimation step | DFL | Single pipeline; decision-focused learning theme present at ICAIF but applied narrowly, not to cross-system fusion |
| Return Prediction for Mean-Variance Portfolio Selection: How Decision-Focused Learning Shapes Forecasting Models | 2025 (ICAIF) | Same DFL theme, forecasting side | DFL | Same scope note |
| ClauseLens: Clause-Grounded, CVaR-Constrained Reinforcement Learning for Trustworthy Reinsurance Pricing | 2025 (ICAIF) | Trustworthy/risk-constrained RL for one pricing task | CVaR-constrained RL | Different application (reinsurance pricing), single-system |
| Finguiniti: A Reinforced Multi-Agent Framework for Narrative-Enhanced Financial Valuation and Risk-Aware Decision Making | 2025 (ICAIF) | Risk-aware multi-agent valuation | Multi-agent RL + narrative features | Multi-agent but homogeneous-paradigm (RL agents within one framework), not a comparison across independently-developed heterogeneous systems |
| Unmasking Bias in Financial AI: A Robust Framework for Evaluating and Mitigating Hidden Biases in LLMs | 2025 (ICAIF) | Bias evaluation framework for financial LLMs | Framework/benchmark paper | Structurally the closest ICAIF *paper format* to what our project would submit (a framework/audit paper over multiple LLMs), but the axis being audited is bias, not calibration/contradiction/reliability — useful as a style/structure template, not a topical collision |
| Your AI, Not Your View: The Bias of LLMs in Investment Analysis | 2025 (ICAIF) | Whether LLM investment analyses encode systematic bias | Cross-model bias comparison | Compares multiple LLMs on one axis (bias), same "framework paper over several systems" structure as above but again bias-focused, not calibration/contradiction/fusion |
| StockBench: Can LLM Agents Trade Stocks Profitably In Real-world Markets? | 2025 (arXiv 2510.02209; not confirmed ICAIF) | Whether LLM trading agents beat buy-and-hold in real markets | Live multi-month simulation, cumulative return / max drawdown / Sortino | Backtest-performance leaderboard (LLM-only agents), explicitly the return/Sharpe/drawdown metric family this project's `CONTRACT/schemas.py` keeps out of the adapter contract by design; a genuine differentiator, not a collision |
| PortBench: A Correlation-Aware, Full-Pipeline Benchmark for LLM-Driven Portfolio Management | 2025 (arXiv 2605.27887; not confirmed ICAIF) | Portfolio-level LLM agent benchmarking with cross-asset correlation | Full-pipeline benchmark | Same backtest-performance framing as StockBench, LLM-only, no cross-paradigm (non-LLM) systems, no calibration/contradiction diagnosis |
| Agent Market Arena (AMA): Live Multi-Market Trading Benchmark for LLM Agents | 2025/2026 (arXiv 2510.11695; ACM Web Conf. 2026, not ICAIF) | Live, lifelong leaderboard for LLM trading agents across markets | 4 fixed agent architectures × multiple LLM backbones, Sharpe/return | Same performance-leaderboard framing; notably finds "agent framework matters more than LLM backbone" — a reliability-adjacent finding but still measured via backtest return, not via calibration/contradiction diagnostics; all 4 "agents" are LLM-backbone-swappable, not independently-published heterogeneous systems (RL/GP/GBM/etc.) |
| CLQT: A Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for Diagnostic Evaluation of LLM Portfolio-Management Agents | 2026 (arXiv 2606.29771; not confirmed ICAIF) | "Diagnostic" evaluation of LLM portfolio agents beyond raw return | Closed-loop, cost-aware, strategy-consistency diagnostics | Closest-titled non-ICAIF paper to our "Layer 1 diagnosis" framing — worth reading in full before finalizing Direction A/B's novelty claim, since "diagnostic evaluation" is exactly our vocabulary; still LLM-only agents, no cross-paradigm heterogeneity or explicit contradiction-detection rule framework found in the abstract-level description gathered here |
| When Alpha Breaks: Two-Level Uncertainty for Safe Deployment of Cross-Sectional Stock Rankers | 2026 (arXiv 2603.13252; venue unclear) | When should a single stock-ranking model be trusted enough to deploy today | Two-level uncertainty, selective deployment | Single-model abstention/selective-deployment — the closest single-model precedent for our Layer-2 "abstention" idea; our version would need to be explicitly cross-agent to differentiate |
| RegimeFolio: A Regime Aware ML System for Sectoral Portfolio Optimization in Dynamic Markets | 2025 (arXiv 2510.14986; venue unclear) | Regime-specific model training + "stability-weighted model selection" for one portfolio system | Regime-specific retraining, per-regime model rebalancing | Regime-conditioned model selection, but within one system's own model zoo, not across independently-developed heterogeneous financial-AI *projects*; closest non-ICAIF precedent for Direction C |
| A Risk-First Evaluation Framework for Multi-Agent LLM Systems | year/venue unconfirmed (OpenReview id frPFuji3Hz) | Risk-centric evaluation protocol for multi-agent LLM systems | Evaluation framework | Venue not confirmed as ICAIF during this search; flagged for a follow-up read since "risk-first evaluation framework" is close in spirit to our Layer-1 diagnostic framing — needs verification before ruling in or out as prior art |

---

## Addendum — verified during cross-check with `NOVELTY_AUDIT.md`/`CANDIDATE_PAPER_DIRECTION.md`

The following four items were surfaced by a separate research pass on this
same task (see note in `ICAIF_POSITIONING.md` on provenance) and independently
re-verified via WebSearch in this session before being trusted — all four are
real, non-fabricated papers:

| Paper | Year | Problem | Method | Difference from us |
|---|---|---|---|---|
| INVESTORBENCH: A Benchmark for Financial Decision-Making Tasks with LLM-based Agent | 2024/2025 (arXiv 2412.18174; ACL 2025, not ICAIF) | Standardized benchmark for LLM agents across stocks/crypto/ETFs | 13 LLMs evaluated on sequential financial decision tasks | Another backtest/performance-style LLM-only benchmark, same differentiation as StockBench/PortBench/AMA (§ above) — not a calibration/contradiction/fusion diagnostic study, and single-paradigm (LLM only) |
| Agentic Confidence Calibration | 2026 (arXiv 2601.15778; general-agent, not finance-specific) | Calibrating confidence for multi-step agent *trajectories*, not single-turn outputs | Holistic Trajectory Calibration (HTC) diagnostic framework + General Agent Calibrator | Not finance-domain; single-agent-type trajectory calibration, not cross-paradigm/cross-system calibration comparison. Useful as a methodological precedent for a trajectory-aware calibration metric if this project extends calibration analysis to the new Q4 stepwise trajectories, but no finance or multi-system claim to collide with |
| When Agents Disagree With Themselves: Measuring Behavioral Consistency in LLM-Based Agents | 2026 (arXiv 2602.11619) | Whether one LLM agent gives consistent outputs across repeated identical-input runs | Repeated-run action-sequence divergence measurement (ReAct-style agents, HotpotQA) | Not finance-domain; measures *self*-consistency of one agent, not cross-agent disagreement between different systems. Directly relevant as a precedent for this project's own "stability variance" idea (Direction B, §B2 in `CANDIDATE_PAPER_DIRECTION.md`) — cite as the closest methodological analogue, then differentiate by (a) finance domain, (b) non-LLM systems included, (c) cross-*system* rather than within-*one-agent* framing |
| The Confidence Dichotomy: Analyzing and Mitigating Miscalibration in Tool-Use Agents | 2026 (arXiv 2601.07264) | Whether an LLM agent's confidence is systematically miscalibrated depending on which external tool it used | Calibration Agentic RL (CAR) | Not finance-domain; single-agent, tool-type-conditioned calibration. Relevant precedent for the "calibration depends on mechanism-category, not just identity" framing this project's `ConfidenceKind` taxonomy already encodes — worth citing as convergent evidence from a different domain |

**Provenance caveat**: these four were not found independently by this
session's own primary literature search (see main table above); they were
found by a separate concurrent process working on the same task (see
`ICAIF_POSITIONING.md`) and are included here only after this session
independently re-ran a WebSearch for each exact title and confirmed a real,
matching arXiv/ACL record — none were taken on trust from an un-verified
source.

## What this table does NOT contain

- The other ~56 ICAIF'25 titles not retrieved in this session's single page
  fetch, and any ICAIF'24/'23 paper whose title gave no thematic signal
  (e.g. pure option-pricing PDE papers, pure fraud-detection GNN papers) —
  excluded as clearly out of scope, not because they were found and
  discarded for relevance.
- Anything behind ACM DL paywalled full text — every row above was
  classified from title (+ short abstract snippet where surfaced by the
  search engine), not from a full-text read. `NOVELTY_AUDIT.md` §3 lists
  which of these need a full-text read before this project's paper
  direction is finalized.
- ICAIF 2026 accepted papers (not yet published as of this search).

---

## Appendix: full ICAIF'25 accepted-paper title list (113 of 169), independently re-fetched

Independently re-verified in this same session via a direct `WebFetch` of
`icaif25.org/accepted-papers/` (same 113-title retrieval limit hit as the
pass that built the table above — the page appears to cap what a single
fetch surfaces relative to the site's own claimed 169-paper count). Kept in
full here, rather than only in a subagent transcript, so a future session
can re-derive additional table rows without re-fetching:

Continuous-Time Reinforcement Learning for Asset–Liability Management ·
Interpretable Market Simulations via Optimal Transport: Power Law
Decomposition and Implications for Market Design · Federated Financial
Reasoning Distillation: Training A Small Financial Expert by Learning From
Multiple Teachers · Regret-Optimized Portfolio Enhancement through Deep
Reinforcement Learning and Future Looking Rewards · Reasoning or
Overthinking: Evaluating Large Language Models on Financial Sentiment
Analysis · Leveraging Deep Learning Optimization for Monte Carlo Calibration
of (Rough) Stochastic Volatility Models · Norm-Salvaged Embedding: Improving
Condition Alignment of Synthetic Time Series Generation in Finance · IKNet:
Interpretable Stock Price Prediction via Keyword-Guided Integration of News
and Technical Indicators · Extracting the Structure of Press Releases for
Predicting Earnings Announcement Returns · A Role-Aware Multi-Agent
Framework for Financial Education QA with LLMs · ISEPT: Image-Based
Selection and Execution Framework for Pair Trading · ProtoHedge:
Interpretable Hedging with Market Prototypes · Natural-gas storage
modelling by deep reinforcement learning · LENS: Large Pre-trained
Transformer for Exploring Financial Time Series Regularities ·
Probability-Density-Consistent Physics-Informed Neural Networks for
Stochastic Local Volatility Model Calibration · Is BTC Enough? A New
Perspective on Cryptocurrency Price Formation · Quantum Optimization of
Currency Arbitrage via Graph-Informed Entanglement Strategies · A
Data-Driven Asset Relation Extraction and Portfolio Optimization Method
through Convolution · Query Generation Pipeline with Enhanced Answerability
Assessment for Financial Information Retrieval · Unmasking Bias in
Financial AI: A Robust Framework for Evaluating and Mitigating Hidden
Biases in LLMs · ClauseLens: Clause-Grounded, CVaR-Constrained
Reinforcement Learning for Trustworthy Reinsurance Pricing · Algorithmic
pricing with independent learners and relative experience replay ·
Constrained Tabular Diffusion for Finance · Unified Item Segmentation for
10-Q and 10-K Filings Using Item-Aware Document-Level Auxiliary Tasks ·
MacroVAE: Counterfactual Financial Scenario Generation via Macroeconomic
Conditioning · FinDER: Financial Dataset for Question Answering and
Evaluating Retrieval-Augmented Generation · FinAgentBench: A Benchmark
Dataset for Agentic Retrieval in Financial Question Answering · Structured
Agentic Workflows for Financial Time-Series Modelling with LLMs and
Reflective Feedback · FinReflectKG: Agentic Construction and Evaluation of
Financial Knowledge Graphs · FinResearchBench: A Logic Tree based
Agent-as-a-Judge Evaluation Framework for Financial Research Agents ·
FinMR: A Knowledge-Intensive Multimodal Benchmark for Advanced Financial
Reasoning · Positive-Unlabeled Learning for Financial Misstatement
Detection under Realistic Constraints · FinDPO: Financial Sentiment
Analysis for Algorithmic Trading through Preference Optimization of LLMs ·
Vision, Voice, and Text: Pioneering Zero-shot Multimodal LLMs for
Sentiment-driven Investment · FABS: An Extensible and High-Performance
Digital Twin Framework of AI-Driven Financial Systems · Neural
Network-Driven Volatility Drag Mitigation under Aggressive Leverage ·
Optimizing Large Language Models for ESG Activity Detection in Financial
Texts · Financial Statement Fraud Detection with a Categorical-to-Numerical
Data Representation · NeuralBeta: Estimating Beta Using Deep Learning ·
Adaptive Sample Weighting with Regime-Aware Meta-Learning Framework for
Financial Forecasting · Your AI, Not Your View: The Bias of LLMs in
Investment Analysis · Democratizing Alpha: LLM-Driven Portfolio
Construction for Retail Investors Using Public Financial Media · FactorMAD:
A Multi-Agent Debate Framework Based on Large Language Models for
Interpretable Stock Alpha Factor Mining · Estimating Covariance for Global
Minimum Variance Portfolio: A Decision-Focused Learning Approach ·
Similarity-based Conformal Prediction using Random Forest Proximities · A
Multimodal Alignment-Based Anomaly Detection Method for Bankruptcy
Prediction · Case-based Explainability for Random Forest: Prototypes,
Critics, Counter-factuals and Semi-factuals · Arbitrage-Free Implied
Volatility Surface Smoothing via Generative Adversarial Networks ·
FinSearch: A Temporal-Aware Search Agent Framework for Real-Time Financial
Information Retrieval with Large Language Models · AuditAgent:
Expert-Guided Multi-Agent Reasoning for Cross-Document Fraudulent Evidence
Discovery · Multilingual BERT-based Classification and Recommendation
Model for Supporting Innovation Finance Decisions · CMS-VAE: A
Strategy-aware Variational AutoEncoder for High-Fidelity Crypto Market
Simulation · Prompting for policy: Forecasting Macroeconomic Scenarios with
Synthetic LLM Personas · Repurposing Language Models for FX Volatility
Forecasting: A Data-Efficient and Context-Aware Approach · Large Language
Model Agents for Investment Management: Foundations, Benchmarks, and
Research Frontiers · Multi-Agent Reinforcement Learning for Market Making:
Competition without Collusion · Hypergraph Attention Network to Predict
Stock Movements By Exploring Higher-order Relationships · Learning to
Trade with Preferences: Interpretable Execution via Mixture-of-Experts ·
Predictive Uncertainty Quantification for Financial DNN Using Regular Vine
Copula · Robust time series generation via Schrödinger Bridge: a
comprehensive evaluation · Graph Neural Networks for Bridge Swap Link
Prediction in Uniswap v3 · TSTR for Financial Fraud: Learning to Detect
Manipulation Without Real Data · Tracing Positional Bias in Financial
Decision-Making: Mechanistic Insights from Qwen2.5 · FinGraphEx: High
Fidelity Financial Knowledge Graph Extraction · Learning to Scalp: A
Reinforcement Learning Agent-Based Study · Curriculum-Guided Reinforcement
Learning for Synthesizing Gas-Efficient Financial Derivatives Contracts ·
Attention Factors for Statistical Arbitrage · Contextual Time Series
Embedding: A State Space Perspective for Financial Data · Aligning
Language Models with Investor and Market Behavior for Financial
Recommendations · Demystifying TCFD Disclosures: An AI-Powered Framework
for Enhanced Transparency and Trust · Fast Monitoring of Systemic Risk in
Financial Networks with Credit Default Swaps · BForTFin: A Financial
Domain-Aware Multiscale Evaluation Method for Time-Series Foundation
Models · Quantifying Semantic Shift in Financial NLP: Robust Metrics for
Market Prediction Stability · Parametric Phi-Divergence-Based
Distributionally Robust Optimization for Insurance Pricing · Right Place,
Right Time: Market Simulation-based RL for Execution Optimisation · Deep
Mean-Reversion: A Physics-Informed Contrastive Approach to Pairs Trading ·
Time-Varying Factor-Augmented Models for Volatility Forecasting ·
ACT-Tensor: Tensor Completion Framework for Financial Dataset Imputation ·
On the Potential of Tool-Enhanced Small Language Models to Match Large
Models in Finance · LAS-GNN: A Graph Neural Network for Temporal Money
Laundering Motif Detection · Long-Term Financial Forecasting and Trading
via Multi-Agent Reinforcement Learning · Factor-Driven Network Informed
Restricted Vector Autoregression · DiffVolume: Diffusion Models for Volume
Generation in Limit Order Books · From News to Returns: A Granger-Causal
Hypergraph Transformer on the Sphere · Fusing Narrative Semantics for
Financial Volatility Forecasting · Scaling Conditional Autoencoders for
Portfolio Optimization via Uncertainty-Aware Factor Selection ·
JaxMARL-HFT: GPU-Accelerated Large-Scale Multi-Agent Reinforcement
Learning for High-Frequency Trading · Can AI Read Like a Financial
Analyst? A Financial Touchstone for Frontier Language Models such as
Gemini 2.5 Pro, o3, and Grok 4 on Long-Context Annual Report Comprehension
· Graph Learning for Foreign Exchange Rate Prediction and Statistical
Arbitrage · Market Selection with Midpoint Matching: A Strategic
Agent-Based Analysis · Online Ensemble Learning for Sector Rotation: A
Gradient-Free Framework · DeltaLag: Learning Dynamic Lead-Lag Patterns in
Financial Markets · BMI-GP: Unsupervised Breach Merchant Identification via
Adaptive Graph Pruning · Return Prediction for Mean-Variance Portfolio
Selection: How Decision-Focused Learning Shapes Forecasting Models · The
Accidental Pump and Dump: When Agentic AI Meets Autonomous Trading ·
Decoding the Beige Book: LLM-Powered Sentiment Analysis for Real-Time
Recession Forecasting · Learning to Manage Investment Portfolios beyond
Simple Utility Functions · Mean Variance Efficient Collaborative Filtering
for Stock Recommendations · LatentGraph: From Latent States to Rule-based
Expressions for Explainable Financial Forecasting · TF-GAN:
Topology-Aware Generative Adversarial Network for Financial Time Series
Forecasting · Attention-Based Multi-Asset Order Flow Networks for
Enhanced Mid-Price Prediction · Shock-Biased Attention: Enhancing
Transformer Hawkes Processes with Amplitude-Driven Temporal Kernels · From
Constituents to Index: Interpretable Price Movement Prediction via
Cross-Asset Order Flow · FAITH: A Framework for Assessing Intrinsic
Tabular Hallucinations in finance · Data-Driven Trade Flow Decomposition
for Exchange-Traded Funds and their Constituents · Two Sides of the Same
Coin: How LLMs Reveal Dual Narratives in Annual Reports · Behavioural
Reinforcement Learning (Beyond Rationality: RL Under Investor Bias) · LLM
Embedding for Regression Priors · Language Models for Automated Market
Commentary from Corporate Disclosures · Evaluating the Ethical Judgment of
Large Language Models in Financial Market Abuse Cases · Adaptive Quantum
Channels as Long-Memory Generative Models · Finguiniti: A Reinforced
Multi-Agent Framework for Narrative-Enhanced Financial Valuation and
Risk-Aware Decision Making · Discrete Flow Matching is an Effective
Post-training Method for Addressing Compound Error in Autoregressive
Models.

(This list and the fetched-table list above were produced by two
independent fetches in the same session and agree on every title that
overlaps — cross-check increases confidence in both.)
