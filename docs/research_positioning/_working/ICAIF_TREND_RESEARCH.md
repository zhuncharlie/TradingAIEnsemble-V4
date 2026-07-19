# ICAIF 2023–2026 Trend Research (working notes for positioning report)

Status: literature-review-only substrate. Written by a research-substrate
session; the coordinating session is responsible for the final positioning
report. All claims below are backed by real tool calls (Crossref API,
OpenAlex API, Semantic Scholar API, WebSearch/WebFetch on arXiv and ACM DL).
No fabricated titles, venues, or IDs.

Date of research: 2026-07-19.

---

## Method / provenance

- ACM DL blocks direct WebFetch (HTTP 403 on `dl.acm.org/doi/proceedings/...`).
- Worked around via the **Crossref REST API** (`api.crossref.org/works`),
  querying `query.container-title="ACM International Conference on AI in
  Finance"` with `filter=type:proceedings-article`, then filtering results
  whose DOI prefix matches the specific proceedings volume:
  - ICAIF'23 → proceedings DOI `10.1145/3604237` (4th ACM ICAIF, Brooklyn NY,
    Nov 27–29 2023) — **79 papers** recovered.
  - ICAIF'24 → proceedings DOI `10.1145/3677052` (5th ACM ICAIF, NYU Tandon,
    Nov 14–17 2024) — **96 papers** recovered.
  - ICAIF'25 → proceedings DOI `10.1145/3768292` (6th ACM ICAIF, Singapore,
    Nov 15–18 2025) — **111 papers** recovered (title records already
    registered via Crossref/DOI pre-assignment even though the conference
    itself is in Nov 2025 — i.e., accepted-paper titles, real DOIs).
  - Total: **286 real, DOI-verified ICAIF paper titles** across 3 years.
  - Confirmed via WebSearch that these DOI prefixes are legitimate ACM
    proceedings records (titles: "4th ACM International Conference on AI in
    Finance", "Proceedings of the 5th ACM International Conference on AI in
    Finance", "Proceedings of the 6th ACM International Conference on AI in
    Finance").
- OpenAlex (`openalex_fetch.py`) and Semantic Scholar
  (`semantic_scholar_fetch.py`) were also queried but returned generic
  "AI in finance" survey/review noise rather than ICAIF-venue-tagged
  records (S2 hit rate-limit HTTP 429; OpenAlex has no indexed `source` for
  these ACM proceedings DOIs) — Crossref was the reliable source of ground
  truth here and is cited accordingly.
- Full paper-title lists (with DOIs) are reproducible from the Crossref
  queries above; representative titles are quoted throughout this document.

---

## Q1. Dominant ICAIF paper themes, 2023–2026 — ranked

Regex keyword-matched all 286 real titles against the 7 candidate themes
(title-only signal — undercounts themes that don't appear in the title, but
titles are what a program-committee/reviewer skims first, so this is a
reasonable proxy for "acceptance-friendliness" of a *framing*).

**Aggregate ranking across ICAIF'23+'24+'25 (n=286):**

| Rank | Theme | Count | % of corpus |
|---|---|---|---|
| 1 | Interpretability / explainability | 15 | 5.2% |
| 2 | Trustworthy AI (fairness/bias/ethics/trust, title-level) | 12 | 4.2% |
| 3 | Multi-agent finance | 9 | 3.1% |
| 4 | Robustness | 8 | 2.8% |
| 5 (tie) | Calibration (title match) | 7 | 2.4% |
| 5 (tie) | Risk-aware AI | 7 | 2.4% |
| 7 | Decision-focused learning | 4 | 1.4% |

**Important caveat on ranking:** these 7 themes are all niche relative to
the corpus's real center of gravity. The actual dominant ICAIF themes by
raw volume are not on this list of 7 at all:
- **LLM/agentic finance** (LLM, GPT, FinGPT, FinBERT, "agent"/"agentic" in
  title): by far the largest and fastest-growing bucket, especially
  ICAIF'24→'25 (FlowMind, FinDKG, HybridRAG, XBRL Agent, FinResearchBench,
  FinAgentBench, FinSearch, FinReflectKG, AuditAgent, FinDER, FinMR, etc.)
- **Generative modeling** (GANs, diffusion, synthetic data/time-series
  generation) — consistently large across all 3 years (market simulation,
  synthetic tabular/fraud data, LOB generation, correlation-matrix
  generation).
- **Reinforcement learning for trading/hedging/market-making** — a
  perennial ICAIF staple every year (deep hedging, market making, order
  execution, portfolio optimization via RL/DRL/MARL).
- **Fraud/AML/financial-crime detection** — a recurring cluster, especially
  ICAIF'24-'25 (graph-based fraud detection, money-laundering subgraphs,
  synthetic fraud augmentation).
- **Time-series forecasting / volatility modeling** (classical + deep) —
  large, steady cluster every year.

So: within the 7 candidate themes, ranking is
**interpretability > trustworthy-AI-framing > multi-agent > robustness >
{calibration, risk-aware} > decision-focused-learning** — but all 7 are
minority themes at ICAIF. The conference's true majority themes are
LLM/agentic systems, generative modeling, RL for execution/hedging, and
fraud detection, none of which are on the candidate-theme list. A
positioning report claiming any one of the 7 candidate themes is
"the dominant ICAIF theme" would be overstating it — it is at best a
"visible, growing minority theme."

Notable ICAIF'25-specific shift: interpretability (8 titles) and
trustworthy-AI-language (7 titles, e.g. "Unmasking Bias in Financial AI",
"Your AI, Not Your View: The Bias of LLMs in Investment Analysis",
"Evaluating the Ethical Judgment of Large Language Models in Financial
Market Abuse Cases") and multi-agent framing (6 titles) all roughly
doubled/tripled vs '23–'24 in relative share — this is the one theme cluster
with genuine multi-year upward momentum, consistent with the maturing
LLM-agent-in-finance wave.

---

## Q2. Does a published ICAIF/adjacent paper already do "unify heterogeneous
financial-AI systems into one schema + audit reliability/calibration/
contradiction"? — Novelty risk check

**No direct hit found** after searching ICAIF proceedings (all 286 titles,
manually scanned), WebSearch across arXiv/ACM/general web, and targeted
arXiv-API queries. But several *adjacent* papers were found and should be
disclosed and distinguished carefully in the positioning report, because a
reviewer will likely surface them:

1. **"TradeTrap: Are LLM-based Trading Agents Truly Reliable and Faithful?"**
   (arXiv PDF: https://arxiv.org/pdf/2512.02261). Evaluates multiple
   **LLM-based trading agent repos** (AI-Trader, NOFX, ValueCell,
   TradingAgents, AutoGPT-based variants) for reliability/faithfulness
   under adversarial conditions (prompt injection, poisoned RAG,
   jailbreaking). **Scope is LLM-agents-only** — no RL portfolio managers,
   classic quant methods, or sentiment models as a separate capability
   layer; no explicit unified schema across capability layers (Action /
   State / Signal / Policy); focus is faithfulness/robustness under attack,
   not calibration or contradiction-auditing in the ECE/reliability-diagram
   sense. Closest conceptual neighbor found, but materially narrower scope
   (single paradigm: LLM agents) than this project's cross-paradigm
   (LLM + RL + sentiment + classic quant) design.

2. **"When Agents Trade: Live Multi-Market Trading Benchmark for LLM
   Agents"** (arXiv PDF: https://arxiv.org/pdf/2510.11695). Also
   **LLM-agents-only** (GPT-4, Claude, Gemini variants), live multi-market
   benchmark environment. No unified schema across heterogeneous system
   *types*; no explicit calibration/contradiction audit.

3. **"UniFinEval: Towards Unified Evaluation of Financial Multimodal
   Models across Text, Images and Videos"** (arXiv:2601.22162). Despite the
   "Unified" name, this is a **multimodal MLLM benchmark** (10 MLLMs on
   3,767 QA pairs spanning 5 financial-reasoning scenarios) — unifies
   *input modalities*, not heterogeneous *system paradigms* (no RL, no
   classic quant, no non-LLM sentiment models). Not a genuine competitor;
   worth a one-line disambiguating footnote only because of name collision
   risk ("unified... financial... benchmark").

4. General ML-calibration survey literature exists and is mature
   (e.g., "Calibration in Deep Learning: A Survey of the State-of-the-Art,"
   arXiv:2308.01222) but is domain-agnostic — it is not applied to
   heterogeneous financial-AI systems at ICAIF or NeurIPS-FinAI as a
   cross-paradigm audit.

5. Checked NeurIPS financial workshops (NeurIPS 2025 "Generative AI in
   Finance" workshop, FL@FM-NeurIPS'24 federated-foundation-models
   workshop) via WebSearch — no unified-schema/cross-paradigm reliability
   audit found there either; these workshops skew toward generative
   modeling and federated learning respectively, not adapter-style
   system unification.

**Best-guess verdict**: A paper doing exactly what this project does — take
20+ *architecturally distinct* real upstream systems (LLM trading agents,
RL portfolio managers, sentiment/NLP models, classic quant/optimization
methods) spanning multiple *capability layers* (not just "trading agents"
as one monolithic category), convert them into one auditable schema with
explicit provenance separation, and empirically measure
calibration/contradiction/reliability **as a precondition for studying
fusion/routing quality** — **has not been published at ICAIF 2023–2025,
its adjacent NeurIPS finance workshops, or in the broader arXiv/S2/OpenAlex
search surface as of this research date (2026-07-19)**. The closest works
(TradeTrap, When-Agents-Trade) are single-paradigm (LLM-agents-only)
reliability/faithfulness studies, not cross-paradigm schema-unification
audits. This is not a certainty — ICAIF review/publication lag and closed
CMT-only pre-prints could hide a match — but no positive evidence of prior
work was found across 4 independent search strategies (ICAIF proceedings
scan, arXiv API, WebSearch, targeted competitor-paper deep-reads). The
positioning report should state this as "no directly overlapping paper
found after a systematic multi-source search," not as an absolute
guarantee of novelty, and should explicitly cite TradeTrap and When-Agents-
Trade as the nearest neighbors to preempt a reviewer citing them.

---

## Q3. Which of the 7 candidate themes should the positioning report lead
with?

Given the actual frequency data above, recommend leading with a
**combination framing, not a single theme**, because no single one of the 7
is a strong ICAIF majority theme on its own (all are 1.4%–5.2% of titles).
Ranked recommendation:

1. **Trustworthy AI agents + multi-agent finance** (combined) — the
   two themes with real multi-year upward momentum at ICAIF (visible
   tripling of trust/fairness/bias-titled papers and multi-agent-titled
   papers from '23→'25), and the theme cluster most literally adjacent to
   this project's actual object of study (financial AI *agents*, plural,
   heterogeneous). This is also where ICAIF'25 program committees have
   shown clearest appetite (FinAgentBench challenge track, multiple
   multi-agent-debate / multi-agent-RL papers, several bias/fairness-in-
   LLM-agent papers).
2. **Interpretability** as a secondary supporting theme — largest single
   theme by title count (15/286) and growing, but it's a crowded
   local-explainability/XAI space at ICAIF (SHAP-adjacent, prototype-based,
   counterfactual methods) that this project does not directly contribute
   novel interpretability *methods* to — better used as a "related work"
   anchor than a headline claim.
3. **Calibration** should NOT be the lead framing term (see Q4) — use
   "reliability" or "confidence/consistency auditing" as the headline
   vocabulary instead, with calibration introduced only after explicitly
   scoping it to ML/forecast calibration.
4. **Robustness** and **risk-aware AI** are minority themes at ICAIF
   proper (2.4–2.8%) and are more strongly associated there with
   adversarial/attack-robustness (spoofing, market manipulation) and
   classical risk metrics (CVaR, tail risk) than with cross-model
   reliability audits — usable as supporting vocabulary, not a lead.
5. **Decision-focused learning** is real but rare at ICAIF (4/286,
   1.4%) — a legitimate niche (e.g., "Estimating Covariance for Global
   Minimum Variance Portfolio: A Decision-Focused Learning Approach,"
   ICAIF'25) that pairs well with this project's "fusion quality measured
   by downstream Sharpe/Sortino, not raw accuracy" angle, but too small a
   theme to lead with — good as a one-paragraph connection to Q4's policy
   layer.

**Bottom line recommendation**: lead with **"trustworthy, multi-agent
financial AI systems"** as the positioning frame (matches ICAIF's clearest
growth trend and its FinAgentBench-style challenge-track appetite), use
**reliability/calibration-of-heterogeneous-systems** as the technical
contribution inside that frame (being careful with the term — see Q4), and
cite **interpretability** and **decision-focused learning** as adjacent
literature this project's fusion/routing study connects to, not as the
lead claim.

---

## Q4. The "calibration" terminology trap — confirmed, with hard numbers

**This is a real and significant risk**, confirmed directly against the
ICAIF corpus, not assumed.

Of the **7 ICAIF papers (2023–2025) whose titles contain "calibrat-"**, all
7 are **pricing/simulation-model parameter-fitting calibration**, and
**zero** are **ML confidence/probability calibration** (ECE, reliability
diagrams, hit-rate-vs-confidence) in the sense this project would likely
mean:

| Year | Title | Type |
|---|---|---|
| ICAIF'23 | "Deep Calibration of Market Simulations using Neural Density Estimators and Embedding Networks" | market-simulation-model calibration |
| ICAIF'23 | "Gradient-Assisted Calibration for Financial Agent-Based Models" | agent-based-model (ABM) calibration |
| ICAIF'23 | "Reinforcement Learning for Combining Search Methods in the Calibration of Economic ABMs" | ABM calibration |
| ICAIF'23 | "Bayesian Networks Improve Out-of-Distribution Calibration for Agribusiness Delinquency Risk Assessment" | closest to ML-style calibration (OOD calibration of a risk-classification model) — **partial exception, worth reading directly** |
| ICAIF'23 | "Calibration of Derivative Pricing Models: a Multi-Agent Reinforcement Learning Perspective" | derivative-pricing-model calibration |
| ICAIF'25 | "Leveraging Deep Learning Optimization for Monte Carlo Calibration of (Rough) Stochastic Volatility Models" | stochastic-volatility-model calibration |
| ICAIF'25 | "Probability‑Density‑Consistent Physics-Informed Neural Networks for Stochastic Local Volatility Model Calibration" | local-volatility-model calibration |

**6 of 7 (86%) are unambiguously the pricing/simulation-parameter-fitting
sense of "calibration"** — fitting a stochastic-volatility, agent-based-
market, or derivative-pricing model's *parameters* to match observed market
data. Only 1 of 7 ("Bayesian Networks Improve Out-of-Distribution
Calibration...") plausibly uses "calibration" in something closer to the
ML-confidence sense (OOD calibration of a delinquency-risk classifier is
much closer to what this project means), and even that one is about a
single classification model's probability calibration, not cross-system
reliability auditing.

**Broader search evidence**: general WebSearch for "expected calibration
error financial machine learning" returns almost entirely domain-agnostic
ML-calibration survey literature (e.g., arXiv:2308.01222, "Calibration in
Deep Learning: A Survey of the State-of-the-Art") rather than
finance-specific applications — reinforcing that ML-confidence-calibration
is not yet a populated sub-area specifically *at* ICAIF; the term
"calibration" at ICAIF is almost entirely claimed by the quant-finance
sense.

**Recommendation for the positioning report**: never use the bare word
"calibration" as a standalone headline claim. Concretely:
- If leading with a calibration-flavored claim, explicitly qualify it every
  time: "ML/forecast-confidence calibration (expected calibration error,
  reliability diagrams) — as distinct from the pricing/simulation-model
  parameter-calibration sense common at ICAIF (deep hedging, ABM/stochastic-
  volatility calibration)."
- Consider avoiding the bare term in section headers/abstract sentences
  entirely, and prefer "confidence reliability," "predictive reliability
  auditing," or "trustworthiness auditing" — these don't collide with the
  ICAIF pricing-calibration sense and are also better aligned with the
  Q3 "trustworthy AI agents" lead framing.
- If a reviewer is a quant-finance person (very likely at ICAIF, given 6/7
  of the venue's own "calibration" papers are pricing/ABM calibration),
  an unqualified "we study calibration of financial AI systems" sentence
  in the abstract risks being read as "you calibrated a stochastic
  volatility model," which is not what this project does — this is a
  real misreading risk, not a pedantic one.

---

## Summary table: representative real ICAIF papers by theme (for citation)

(All titles verified via Crossref DOI records under proceedings
10.1145/3604237, 10.1145/3677052, 10.1145/3768292.)

**Interpretability/explainability:**
- "Mechanistic interpretability of large language models with applications
  to the financial services industry" (ICAIF'24)
- "ProtoHedge: Interpretable Hedging with Market Prototypes" (ICAIF'25)
- "Case-based Explainability for Random Forest: Prototypes, Critics,
  Counter-factuals and Semi-factuals" (ICAIF'25)

**Trustworthy AI / fairness / bias:**
- "Unmasking Bias in Financial AI: A Robust Framework for Evaluating and
  Mitigating Hidden Biases in LLMs" (ICAIF'25)
- "Your AI, Not Your View: The Bias of LLMs in Investment Analysis"
  (ICAIF'25)
- "Evaluating the Ethical Judgment of Large Language Models in Financial
  Market Abuse Cases" (ICAIF'25)
- "Evaluating Fairness in Transaction Fraud Models: Fairness Metrics, Bias
  Audits, and Challenges" (ICAIF'24)

**Multi-agent finance:**
- "Large Language Model Agents for Investment Management: Foundations,
  Benchmarks, and Research Frontiers" (ICAIF'25, DOI
  10.1145/3768292.3770387)
- "FactorMAD: A Multi-Agent Debate Framework Based on Large Language
  Models for Interpretable Stock Alpha Factor Mining" (ICAIF'25)
- "Multi-Agent Reinforcement Learning for Market Making: Competition
  without Collusion" (ICAIF'25)
- "FinVision: A Multi-Agent Framework for Stock Market Prediction"
  (ICAIF'24)

**Decision-focused learning:**
- "Optimizing Sequential Predictions for Order Execution: a Decision
  Focused Learning Approach" (ICAIF'24)
- "Estimating Covariance for Global Minimum Variance Portfolio: A
  Decision-Focused Learning Approach" (ICAIF'25)
- "Return Prediction for Mean-Variance Portfolio Selection: How
  Decision-Focused Learning Shapes Forecasting Models" (ICAIF'25)

**Nearest-neighbor prior work (for explicit related-work disambiguation):**
- TradeTrap (arXiv:2512.02261) — LLM-trading-agent reliability/faithfulness
  under adversarial conditions.
- When Agents Trade (arXiv:2510.11695) — live multi-market LLM-agent
  benchmark.
- UniFinEval (arXiv:2601.22162) — unified *multimodal* MLLM benchmark
  (name-collision risk only, not a scope competitor).

---

## Sources

- Crossref REST API (`api.crossref.org/works`), queried live, 2026-07-19 —
  primary source for all 286 ICAIF paper titles/DOIs.
- ACM DL proceedings landing pages (titles/metadata confirmed via
  WebSearch, direct fetch blocked with HTTP 403):
  - https://dl.acm.org/doi/proceedings/10.1145/3604237 (ICAIF'23)
  - https://dl.acm.org/doi/proceedings/10.1145/3677052 (ICAIF'24)
  - https://dl.acm.org/doi/proceedings/10.1145/3768292 (ICAIF'25)
- https://arxiv.org/pdf/2512.02261 (TradeTrap)
- https://arxiv.org/pdf/2510.11695 (When Agents Trade)
- https://arxiv.org/abs/2601.22162 (UniFinEval)
- https://arxiv.org/abs/2308.01222 (Calibration in Deep Learning: A Survey
  of the State-of-the-Art — general ML-calibration reference, not
  finance-specific)
- OpenAlex API (`api.openalex.org`) — queried, contributed general
  finance-AI survey context but no ICAIF-venue-tagged records.
- Semantic Scholar API — queried, rate-limited (HTTP 429) on this run;
  not a blocking gap given Crossref coverage was authoritative for ICAIF
  proceedings.
- WebSearch queries (verbatim, for reproducibility): "ICAIF 2025 accepted
  papers proceedings ACM International Conference on AI in Finance";
  "ICAIF 2024 accepted papers list"; "ICAIF 2023 proceedings dl.acm.org";
  "benchmark unified schema heterogeneous financial AI systems reliability
  calibration audit ICAIF"; "survey comparing LLM trading agents RL
  portfolio managers sentiment models unified interface reliability
  finance"; "NeurIPS workshop FinAI FMLA 2024 2025 heterogeneous financial
  models reliability audit contradiction"; "expected calibration error
  financial machine learning predictions confidence reliability diagram
  2024 2025".
