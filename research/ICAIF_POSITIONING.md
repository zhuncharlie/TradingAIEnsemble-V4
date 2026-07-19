# ICAIF Positioning — trading-ai-ensemble

**Status**: investigation-only, no code/`CONTRACT/` changes. This is the
top-level positioning document; `LITERATURE_MAP.md` has the paper table,
`NOVELTY_AUDIT.md` has the gap/collision analysis, and
`CANDIDATE_PAPER_DIRECTION.md` has the five full direction writeups
(A/B/C/D as scored by the audit, plus this document's own recommended
sequencing).

## A note on how this set of four documents came together

Partway through this task, two of the four required files
(`NOVELTY_AUDIT.md`, `CANDIDATE_PAPER_DIRECTION.md`) appeared in `research/`
already written, by a process other than this session's own direct writes —
this session had only written `LITERATURE_MAP.md` at that point. Before
relying on them, this session (1) read both files in full, (2) cross-checked
their central factual claims (adapter/experiment numbers, deepalpha
calibration figures, the 60.7%/57.1% fusion result, Q4-stepwise adapter
counts) against this session's own independent reading of the repo, and (3)
independently re-verified via live WebSearch every paper title cited in
those two files that this session's own literature pass had not already
found — all four turned out to be real, non-fabricated, correctly-described
papers (see the addendum in `LITERATURE_MAP.md`). Content is accurate and
methodologically consistent with this project's own no-fabrication
discipline, so it has been kept and built on rather than duplicated or
discarded. This is disclosed here rather than silently — the project lead
should be aware two of these four files were not authored end-to-end by
the interactive session they were talking to, in case that matters for how
the deliverable is reviewed.

---

## 1. What actually gets accepted at ICAIF (from real 2023–2025 proceedings)

Verified directly from `icaif25.org/accepted-papers/` (169 accepted, 113
titles retrieved), `ai-finance.org/technical-program/` (ICAIF'24, 100
titles), and `ai-finance.org/icaif-23-accepted-papers/` (ICAIF'23, 79
titles) — not reconstructed from memory or a survey paper.

- **Real data + a finance-native problem beats ML novelty-for-its-own-sake.**
  The large majority of accepted titles across all three years are narrow,
  concrete finance problems (option pricing, market making, fraud detection,
  portfolio construction, volatility forecasting) paired with a competent
  but not groundbreaking method (diffusion models, GNNs, transformers, RL) —
  not new-architecture papers using finance as an incidental benchmark. A
  paper's hook is almost always "here is a real finance decision problem
  practitioners actually face" first, "here is our model" second.
- **"Calibration" at ICAIF usually means model-to-market-price calibration**
  (option/volatility-surface/agent-based-model calibration), not ML
  confidence calibration — a genuine terminology trap for this project (see
  `NOVELTY_AUDIT.md` §1.2). Only one 2023 paper (Bayesian-network
  out-of-distribution calibration for credit risk) and two 2025 UQ papers
  are close to the ML sense this project means.
- **Multi-agent/LLM-agent papers are a growing but still narrow slice**
  (roughly 10–15 of ~100–170 accepted titles per year), and every one found
  in this search keeps its "agents" inside one paradigm — several LLM
  instances/roles/personas debating or dividing labor. None compare
  independently-developed, architecturally-different systems (RL vs. GP vs.
  gradient-boosted regression vs. LLM debate) under one shared evaluation
  harness — which is this project's actual structural position.
- **Framework/audit papers over multiple existing systems do get accepted**
  (e.g. "Unmasking Bias in Financial AI: A Robust Framework for Evaluating
  and Mitigating Hidden Biases in LLMs", "Your AI, Not Your View: The Bias
  of LLMs in Investment Analysis" — both ICAIF'25) — this is the closest
  existing *paper format* to what this project would submit: several
  systems evaluated on one axis, with an explicit framework/methodology
  contribution, not just a leaderboard. Bias is their axis; calibration/
  contradiction/reliability would be ours.
- **Decision-focused learning, uncertainty quantification, and risk-aware RL
  are established, recurring ICAIF clusters**, but every instance found
  operates on one model/one pipeline (e.g. "Estimating Covariance for Global
  Minimum Variance Portfolio: A Decision-Focused Learning Approach",
  "Predictive Uncertainty Quantification for Financial DNN Using Regular
  Vine Copula") — the cross-system framing this project would bring is
  differentiated by scope, not by topic.
- **Resource/benchmark-style contributions are welcome** (FinDER,
  FinAgentBench, FinMR, and non-ICAIF-but-adjacent StockBench/PortBench/
  InvestorBench/AMA) — meaning a systems/infrastructure framing (Direction D)
  is a legitimate submission shape at this venue, not just full empirical
  papers.
- **Typical narrative structure**: motivation grounded in a concrete
  practitioner pain point → related work that is mostly finance-specific
  prior systems (not general ML theory) → method → real-data experiments
  with standard finance metrics (Sharpe, drawdown, hit rate, calibration
  error) or task-specific accuracy → an explicit limitations/threats-to-
  validity discussion is common in the stronger papers found (matches this
  project's own existing documentation discipline in `DECISIONS.md`/
  `EXPERIMENT_REPORT.md` closely). Code/data release is common but not
  universal; page length and structure follow standard ACM conference
  format (not verified page-by-page in this pass — recommend checking the
  most recent call for papers' formatting instructions before drafting).

## 2. Where this project's own story fits that landscape

This project is not a new model, not a new single-system benchmark, and not
a backtest-performance leaderboard (that niche is already occupied by
StockBench/PortBench/AMA/InvestorBench — all LLM-only, all judged by
Sharpe/return/drawdown, none doing calibration/contradiction diagnosis). Its
actual position is closer to the "framework/audit paper over multiple real
systems" cluster (bias-audit papers above), but on a different axis:
**information reliability** — is a system's self-reported confidence
trustworthy, do independently-developed systems contradict each other, and
does naively combining them help or hurt. That axis, applied across
genuinely heterogeneous *paradigms* (not just heterogeneous LLM
personas), and grounded in a causally-correct execution harness for the
policy (Q4) layer, is the part of the landscape this search did not find
already occupied.

## 3. Recommended sequencing

(Consistent with, and slightly expanded from, the sequencing note at the
end of `CANDIDATE_PAPER_DIRECTION.md`.)

1. **Engineering prerequisite, blocks everything**: rebuild
   `analysis/icaif_*.py` against `CONTRACT/schemas.py` v2.0.0 and the
   26-adapter roster. The entire existing quantitative record
   (`reports/icaif_experiments_backup_*`) is real but stale — computed
   against a schema (`Q1Decision`/`Q4Portfolio`/`Q5Backtest`) that no longer
   exists. No number from that record is directly citable in a new
   submission; it is citable only as "what the v1 pass found," motivating
   why the v2 rebuild matters.
2. **Direction A (reliability- and contradiction-aware fusion)** is the
   strongest standalone empirical candidate: it has a specific,
   previously-diagnosed-but-unfixed gap in the project's own prior fusion
   formula to close (a missing calibration-reliability multiplier), the
   richest existing real evidence trail (hypotheses 1–4 in
   `NOVELTY_AUDIT.md` §1), and no direct prior-art collision found in
   ICAIF 2023–2025 or the adjacent LLM-trading-benchmark literature.
3. **Direction B (calibration + stability)** is best positioned as a
   diagnostic section feeding into A rather than a fully separate
   submission, unless the new repeated-query stability-variance experiment
   (not present in the v1 suite at all) produces an unusually sharp,
   standalone result.
4. **Direction C (risk-aware routing over the Q4 causal harness)** is the
   most novel relative to prior art (no routing/selection experiment exists
   anywhere in this repo yet) but also the least mature — it requires a
   genuinely new, multi-week, multi-regime experiment on top of
   infrastructure that finished 2026-07-18 and has only been smoke-tested at
   20–70 steps per adapter so far. Worth pursuing only with a real
   multi-week budget, and only after A/B establish the reliability-scoring
   machinery C's router would consume.
5. **Direction D (the causal harness itself, as a resource/systems
   contribution)** is real and already largely written (see
   `HARNESS_INFRASTRUCTURE_FINAL.md`/`Q4_STEPWISE_MIGRATION.md`) but is
   strongest paired with C's actual experiment as evidence of "what we
   learned," not standing alone on architecture description.
6. **Hypothesis 5 (regime-dependent reliability) is currently
   unsubstantiated anywhere in this repo** and should not be asserted as a
   finding in any paper's abstract until a regime-stratified experiment
   (A3/B3/C2 across the three directions) actually runs and either confirms
   or refutes it. Treat it as an open experiment, not a premise, regardless
   of which direction is chosen.

## 4. What this task is explicitly not concluding

Per the task brief, this is a positioning/audit deliverable, not a decision.
No experiment was run and no code or `CONTRACT/` file was modified during
this task. The project lead should treat §3 above as a recommended
ordering to review, not an approved plan — in particular, the choice
between "ship A alone," "ship A+B combined," or "commit to the C/D
multi-week track first" is a scope/timeline call this document does not
make on the project lead's behalf.
