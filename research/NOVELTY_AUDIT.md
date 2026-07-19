# Novelty Audit — trading-ai-ensemble → ICAIF

Generated 2026-07-19. This document does the thing the task brief explicitly
asked for: it does **not** assume the project's own stated research
hypotheses are correct, and it explicitly flags where a candidate direction's
contribution looks weak, collides with existing work, or cannot currently be
proven with the data on hand. See `LITERATURE_MAP.md` for the underlying
paper list and `CANDIDATE_PAPER_DIRECTION.md` for the full A/B/C/D writeups
this audit is scoring.

---

## 1.0 A terminology trap that must be resolved before writing an abstract

A parallel literature pass (see `LITERATURE_MAP.md`'s real ICAIF 2023–2025
title sweep, 169+100+79 accepted papers across three years) found that
**"calibration" at ICAIF overwhelmingly means fitting a pricing/simulation
model's parameters to match observed market prices** (option-pricing-model
calibration, stochastic-volatility calibration, agent-based-model
calibration — at least 5 ICAIF'23–'25 titles use the word exactly this way),
**not** ML confidence calibration in the sense directions A/B use it (does a
self-reported [0,1] value match empirical hit rate). Only one 2023 paper
(Bayesian-network out-of-distribution calibration for credit-risk
probabilities) and two 2025 UQ papers are close to this project's intended
sense. Any abstract, title, or intro for directions A/B must explicitly
disambiguate "confidence calibration of heterogeneous financial AI agents"
from "model-to-market calibration" in the first sentence that uses the word
— an ICAIF-fluent reviewer's first-pass reading will otherwise default to
the financial-engineering sense.

---

## 1. Testing the project's own six stated hypotheses against actual evidence

The project brief states six hypotheses (heterogeneity, reliability
variance, cross-agent contradiction, confidence miscalibration, regime
dependence, single-agent insufficiency). Before endorsing any paper
direction built on top of them, here is what the repo's **own existing data**
already shows versus what is still an unverified assumption:

| # | Hypothesis | Status | Evidence |
|---|---|---|---|
| 1 | Outputs are structurally heterogeneous | **Confirmed, structurally** | `PROJECT_SCHEMA_AUDIT.md` — 27 projects, each project's native output clusters by paradigm (LLM/RL/GP/ensemble), none natively covers all of Q1–Q4; schema v2's open-vocabulary `StateEstimate.dimension` / `ConfidenceKind` design exists *because* of this finding. |
| 2 | Reliability differs across agents | **Confirmed, but narrowly** | v1 calibration table: 9 adapters, 7 distinct confidence-computation mechanisms, one severe overconfidence case (deepalpha, 0.97 avg confidence vs. 0.32 hit rate at 5-day horizon). Narrow because only 39 (adapter, question, horizon, bucket) cells were computed and 28/39 had n<10 — directionally credible, not statistically established. |
| 3 | Agents contradict each other | **Confirmed, with a caveat** | 129 real contradiction cases across 8 (v1) / 19 (later-extended) rules; 37% of cases are only "best-effort" aligned because `Q4Portfolio`/`Q5Backtest` lacked ticker/date fields in v1 — this specific caveat is now *moot* in v2 (`Q4Policy.context` always carries a `QueryContext`), so v2 contradiction detection should have a materially higher exact-alignment rate. This is a concrete, checkable prediction the rebuild should validate. |
| 4 | Confidence may be miscalibrated | **Confirmed** | Same evidence as #2; additionally, `analysis/icaif_metrics.py`'s own documented `ATOM_KEYWORDS` heuristic and the 7-mechanism taxonomy jointly show "confidence" is not one construct across adapters, which is a stronger and more specific claim than generic miscalibration. |
| 5 | Reliability varies by regime | **Not tested at all** | No experiment in the v1 suite or anywhere else in the repo stratifies calibration or contradiction rate by market regime. This is the weakest-evidenced of the six hypotheses and should not be asserted as a finding in any paper abstract — it is a genuinely open experiment (A3/B3/C2 in `CANDIDATE_PAPER_DIRECTION.md`), and there is a real chance it comes back null given current sample sizes. |
| 6 | Single-agent information is insufficient | **Implied, not directly tested** | The fusion ablation (v1 Experiment 5) is the closest test and it produced a *null-to-negative* result for the "more information helps" claim — confidence-weighted and interwoven fusion **underperformed** simple majority vote (57.1% vs. 60.7% hit rate, unweighted). This actually cuts against a naive reading of hypothesis 6 as currently implemented; the diagnosed root cause (missing calibration-reliability weighting) is a specific, falsifiable fix, not a foregone conclusion that fixing it will confirm the hypothesis. |

**Bottom line**: hypotheses 1–4 have real, if small-sample, support already
in the repo. Hypothesis 5 has **zero** support and should be treated as an
open question, not a premise, in any paper framing. Hypothesis 6, as
currently implemented, is **contradicted** by the one experiment that tested
it — the project should not write a paper that assumes fusion self-evidently
helps; it should write a paper that investigates *why* the naive version
didn't help and whether a specific, principled fix changes that.

---

## 2. Where the contribution is currently too weak to submit

- **The entire quantitative record is stale.** Every number in
  `reports/icaif_experiments_backup_*` (calibration errors, 129 contradiction
  cases, 57%/61% hit rates) was computed against the v1 five-question schema
  and a 15-adapter roster that predates the v2 rewrite, the 11-adapter
  expansion, and the causal Q4 stepwise engine. None of it is citable as a
  current result. This is not a paper-direction problem, it is a blocking
  engineering prerequisite for *all* directions (see `ICAIF_POSITIONING.md`).
- **No statistical significance testing anywhere.** The v1 fusion result
  (60.7% vs. 57.1%) is a 30-sample comparison with no confidence interval or
  significance test reported. As currently evidenced, "majority vote beats
  confidence-weighted fusion" is not distinguishable from noise. Any paper
  claiming a fusion-method ordering must add bootstrap/permutation testing
  before submission — this is a hard requirement, not a nice-to-have.
- **Universe size is small and static across every past experiment**
  (3–12 tickers, mostly US large-cap + a few ETFs/commodities). An ICAIF
  reviewer familiar with Qlib/TradeMaster-scale backtests (CSI300, DJ30) will
  ask about generalization. The honest framing is "controlled diagnostic
  study of real, independently-verified systems," not "large-scale trading
  benchmark" — over-claiming scale is a concrete risk to flag, not just a
  stylistic choice.
- **No comparison to any external published benchmark.** `EXPERIMENT_REPORT.md`
  §10 already names this gap (AMA/PortBench/StockBench). These are real,
  recent (2025–2026) benchmarks and are discussed in `LITERATURE_MAP.md`; a
  paper that never positions itself against them will read as unaware of the
  field, even though (per the audit below) none of them occupy the same
  niche.
- **Adapter selection is a convenience sample, not a principled sample of
  "the space of financial AI paradigms."** The 26 adapters were chosen
  opportunistically across many sessions (see `DECISIONS.md`) based on what
  real, safe, non-brokerage-credential-requiring open-source projects could
  be found — a legitimate methodology for a systems paper, but it must be
  disclosed as such, not implied to be a designed stratified sample.

---

## 3. Per-direction novelty verdict

### A — Reliability- and Contradiction-Aware Multi-View Fusion
**Verdict: PLAUSIBLE, defensible novelty.** No ICAIF'25 accepted paper
targets cross-paradigm (LLM + RL + GP/GA + gradient-boosted-ensemble)
reliability-weighted fusion; the closest neighbors ("Online Ensemble
Learning for Sector Rotation," "FactorMAD," and ICAIF'24's "Numin:
Weighted-Majority Ensembles for Intraday Trading" / "Dynamic Reinforced
Ensemble using Bayesian Optimization for Stock Trading" — see
`LITERATURE_MAP.md`) are single-paradigm (numeric ensembling of one model
family, or LLM-only debate); none weight by measured calibration
reliability specifically. The specific hook —
closing a previously root-caused, previously-diagnosed-but-unimplemented gap
in the project's own prior fusion formula — is an unusually clean, falsifiable
framing that most ensembling papers don't have available. **Main risk to the
claim, not to the novelty**: see hypothesis 6 above; this direction must be
written so it can survive a null result.

### B — Calibration and Stability Evaluation of Heterogeneous Financial Agents
**Verdict: PLAUSIBLE but thinner novelty on its own.** Calibration
measurement itself is well-trodden at ICAIF (Vine Copula UQ,
uncertainty-aware factor selection are both ICAIF'25 accepted papers). What
is *not* already covered anywhere found in this audit is (i) grouping
calibration behavior by the schema's own `ConfidenceKind` taxonomy across a
real multi-paradigm deployment, and (ii) the repeated-query stability-variance
diagnostic (which catches the deepalpha-style non-determinism defect
class). A close single-agent methodological precedent for the
stability-variance idea specifically was found outside ICAIF: "When Agents
Disagree With Themselves: Measuring Behavioral Consistency in LLM-Based
Agents" (arXiv 2602.11619, general-agent, non-finance) — cite it and
differentiate on domain, non-LLM-system inclusion, and cross-*system* (not
within-one-agent) framing, per `LITERATURE_MAP.md`'s addendum. Standing
alone, B risks reading as "we measured 26 systems'
confidence and most of it was bad" — true, but not sufficient contribution
density for a full paper unless the `ConfidenceKind`-conditioned result is
unusually clean. Recommended as a strong section inside A rather than a
standalone submission (see `CANDIDATE_PAPER_DIRECTION.md`).

### C — Risk-Aware Routing and Policy Selection
**Verdict: PLAUSIBLE, strong differentiation, but least mature.** Two
non-ICAIF precedents are close enough to require explicit differentiation:
"RegimeFolio: A Regime Aware ML System for Sectoral Portfolio Optimization
in Dynamic Markets" (arXiv 2510.14986) does regime-conditioned model
selection, but within one system's own model zoo, not across
independently-developed real projects; "A Risk-First Evaluation Framework
for Multi-Agent LLM Systems" (OpenReview id frPFuji3Hz, venue unconfirmed)
is close in spirit to a risk-first framing but scoped to LLM-only
multi-agent systems and not independently verified as peer-reviewed — both
listed in `LITERATURE_MAP.md` and flagged there for a full read before
finalizing. The enabling infrastructure (causal Q4 stepwise harness) is
real, tested, and has literally never been exercised at the scale this
direction requires — meaning the paper's core experiment does not exist yet
in any form, only its
prerequisite plumbing does. Differentiates cleanly from the regime-aware/RL
cluster at ICAIF'25 by being a system-of-systems router over independently
authored real projects rather than one model trained with regime features.
**This is the direction most likely to collide with "contribution can't
currently be proven"** — not because of prior art, but because the
multi-regime data this needs does not exist yet and building it is a
real, multi-week undertaking with a non-trivial chance of hitting new
upstream bugs (base rate from this project's own history: real bugs found
in nearly every large real run attempted so far).

### D — Causally-Correct Harness (resource/systems framing)
**Verdict: Real artifact, honest but modest contribution on its own.**
Nothing else found in the literature review implements point-in-time
causality + constraint enforcement as an adapter-*external* layer over
independently-authored heterogeneous policy systems (existing benchmarks
either build their own single-paradigm environment from scratch — StockBench,
AMA — or evaluate a pipeline within one model family — PortBench). This is
genuinely different from those systems, but ICAIF reviewers evaluate
resource/infra submissions partly on "what did you learn," and D has no
standalone empirical finding without borrowing C's experiment. **Recommend
D only as a companion/infrastructure section, not a fully separate
submission**, unless the project specifically wants a resource-track-style
paper independent of the fusion/calibration research line.

---

## 4. Explicit collision check

No title in the verified ICAIF'25 accepted-paper list (113 titles — see
`LITERATURE_MAP.md`) matches any of A/B/C/D closely enough to be a direct
collision. The closest adjacent clusters (LLM-trading benchmarks:
StockBench/PortBench/Agent-Market-Arena/InvestorBench/CLQT; LLM
bias/disagreement: "Your AI, Not Your View," "Unmasking Bias in Financial
AI"; single-model UQ: Vine-Copula UQ, uncertainty-aware factor selection)
must each be explicitly cited and differentiated in related work — not
because they threaten novelty, but because a paper that doesn't mention them
will look like it missed the field, given how recent (mostly 2025–2026) and
directly adjacent they are.

**One item worth independent verification before final submission**: the
2026 arXiv-dated papers surfaced during this audit ("Agentic Confidence
Calibration," "When Agents Disagree With Themselves," "The Confidence
Dichotomy") are very recent (Jan–Feb 2026 arXiv IDs) and were found via
general web search, not ICAIF proceedings — their venue and peer-review
status should be re-checked closer to submission time, since they may be
concurrent, not prior, work.
