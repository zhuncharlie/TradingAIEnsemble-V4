# Session handoff — Literature Review + Research Positioning task

Written 2026-07-19 mid-task, before a session restart to pick up newly
installed ARIS skills. If you're picking this up in a new session: read this
file first, then continue from "Next steps" below.

## Role / constraints (from the user's task brief)

- Role: Literature Review + Research Positioning **only**.
- Forbidden: modifying any Python file, adapters, schema, harness; creating
  experiment code.
- Allowed to write/modify **only** `docs/research_positioning/`.
- Final deliverables (exact filenames): `ICAIF_POSITIONING_REPORT.md`,
  `LITERATURE_MAP.md`, `NOVELTY_AUDIT.md`, `CLAIM_CANDIDATES.md`.
- Must genuinely invoke (via the `Skill` tool, not informal substitution)
  these ARIS skills, now installed at `.claude/skills/` in this project:
  `research-lit`, `semantic-scholar`, `openalex`, `idea-discovery`,
  `novelty-check`, `research-review`, `kill-argument`, `research-refine`.

## Known tooling issue (why this handoff exists)

ARIS skills were installed into `.claude/skills/` **mid-session** (via
`bash ~/aris-repo/tools/install_aris.sh . --all --quiet`, 81 skills
symlinked, global source at `~/aris-repo`, global pointer at
`~/.aris/repo`). Skill discovery in this harness appears to run once at
session start, so the running session never picked up the newly-installed
skills. A `research-lit`/`semantic-scholar` invocation attempt this session
confirmed the `Skill` tool doesn't recognize them. **A fresh session
(process restart, not just this same session resumed) is needed before any
of the 8 mandated skills can be genuinely invoked.**

## Progress so far

1. **5 candidate claims drafted** (non-mechanical evaluation of the user's
   18-item Exp1–Exp18 reference list — several were merged/dropped rather
   than adopted 1:1):
   1. Reliability- and Contradiction-Aware Multi-View Fusion (Exp3/4/10/11/18
      diagnostics feeding an Exp15/17-style fusion formula weighted by
      *measured* calibration reliability, not self-reported confidence, plus
      a cross-agent + intra-adapter cross-Q contradiction penalty).
   2. Calibration and Stability Evaluation of Heterogeneous Financial Agents
      (Exp3 + Exp8: confidence-kind-conditioned calibration + a
      repeated-identical-query stability/variance diagnostic that separates
      "miscalibrated" from "non-deterministic").
   3. Regime-Conditioned Reliability Audit (Exp9, framed as a genuinely open
      question — no experiment anywhere in this project's history has
      tested regime-dependence of reliability yet).
   4. Reliability-Aware Routing and Shadow Q4 Policy Construction (Exp13/14/16,
      built on the newly-finished causal Q4 stepwise harness —
      `harness/q4_protocol.py` / `execution_engine.py` — as an
      evaluation-layer router/shadow-policy construction, not a new adapter).
   5. Contradiction-Aware Selective Prediction / Abstention (Exp12/15) — a
      distinct decision philosophy from claim 1 (abstain/reduce-position
      rather than fuse), evaluated on drawdown/tail-risk reduction rather
      than raw return.

2. **Literature-search fork completed** (before the skill-discovery issue was
   fully understood, so it substituted equivalent direct methodology —
   OpenAlex REST API, Semantic Scholar Graph API, WebSearch — rather than
   genuine `Skill` tool calls, and disclosed this rather than fabricating
   invocations). Key findings, to be re-verified with real skill invocations
   in the new session:
   - Semantic Scholar API returned `429 Too Many Requests` on every attempt
     (no API key configured in this env) — zero usable results from that
     source. Worth checking whether the `semantic-scholar` *skill* (vs. the
     raw API) handles auth differently once it's actually invokable.
   - OpenAlex has no dedicated ICAIF venue/source entry — can't enumerate
     ICAIF papers directly through it, only useful for keyword collision
     checks.
   - New real papers found (WebSearch-verified): AlphaAgents (BlackRock,
     arXiv 2508.11152), MASS (arXiv 2505.10278), "Explainable Heterogeneous
     Anomaly Detection... Adaptive Expert Routing" (arXiv 2510.17088 — title
     sounds close to claim 4's "routing" language; different task/object,
     but flagged for a full read before finalizing wording to avoid a
     title-level confusion, not a substance collision), DeePM (arXiv
     2601.05975), a Springer IJDSA regime-aware agentic portfolio paper.
   - No collision found for any of the 5 candidate claims in this pass.
   - Also re-confirms the "calibration" terminology trap from the prior
     (now-deleted) `research/` pass: ICAIF papers often use "calibration"
     for pricing/simulation-model fitting, not ML confidence calibration.
   - Prior (now-deleted) `research/` pass's ICAIF'25 113-title sweep and the
     StockBench/PortBench/Agent-Market-Arena/InvestorBench/CLQT benchmark
     landscape are still valid background — not re-fetched this pass, worth
     re-verifying via the real `research-lit`/`semantic-scholar` skills once
     available rather than trusting memory of the deleted files.

3. **`novelty-check` fork completed** (5 separate invocations, one per
   candidate claim above). **Phase C (Codex MCP cross-model verification)
   failed 3/3 times**: `stream disconnected before completion: error sending
   request for url https://chatgpt.com/backend-api/codex/responses` — a real
   backend-connectivity failure, distinct from the skill-discovery issue
   (note: `claude mcp list` shows the codex MCP server as "✔ Connected" —
   that only confirms the process is reachable, not that real completions
   succeed; re-verify with an actual call, not just the health check, before
   trusting Codex-MCP-backed skills in the new session). Per the skill's own
   anti-fabrication policy, no Codex verdict was simulated — every verdict
   below is Phase-B-only (real WebSearch, sources cited) and flagged
   `[PHASE-C-UNAVAILABLE]` with downgraded confidence. **Re-run Phase C once
   Codex MCP connectivity is confirmed working before finalizing
   `NOVELTY_AUDIT.md`** — this pass should not be treated as complete.

   Five dossier files were written to
   `docs/research_positioning/_working/NOVELTY_DOSSIER_claim{1..5}.md` (read
   those for full detail). Headline results:

   - **Claim 1** (fusion): MEDIUM-LOW novelty as currently stated. Closest
     prior art: **TrustTrade: Human-Inspired Selective Consensus Reduces
     Decision Uncertainty in LLM Trading Agents** (arXiv 2603.22567, Harvard
     AI & Robotics Lab/HBS/Kempner Institute, 2026-03) — multi-agent
     selective-consensus reweighting by **cross-agent agreement**. Close
     enough it must be cited and explicitly differentiated: (a) TrustTrade's
     agents are all LLM instances (one paradigm), claim 1 spans 6+
     mechanistically different real paradigms; (b) TrustTrade's reliability
     signal is cross-agent *agreement*, claim 1's is *independently measured
     calibration against realized outcomes* — agreement-based weighting
     structurally penalizes a correct lone dissenter, outcome-based
     weighting should not. Must be demonstrated empirically (benchmark
     against a TrustTrade-style agreement-weighting baseline), not just
     argued. Secondary: "Ensemble RL through Classifier Models" (arXiv
     2502.17518), same-paradigm RL+classifier ensemble.
   - **Claim 2** (calibration/stability): MEDIUM. No direct collision, but
     each technique exists elsewhere non-finance/single-paradigm: "The
     Confidence Dichotomy" (arXiv 2601.07264, tool-use LLM agents,
     mechanism-conditioned calibration) and "When Agents Disagree With
     Themselves" (arXiv 2602.11619, single-LLM self-consistency). Selling
     point must be the *empirical pattern found*, not "everything's
     miscalibrated." **Recommend folding into claim 1 as a diagnostic
     section**, not standalone.
   - **Claim 3** (regime-conditioned reliability): HIGH novelty on the
     specific question (nothing found audits *reliability* — not accuracy —
     by regime across a multi-system deployment), but real risk of a null
     result reading as thin at a finance-AI venue. Closest: RegimeFolio
     (arXiv 2510.14986, regime-aware retraining, not auditing), regime-
     weighted conformal VaR calibration (arXiv 2602.03903, single-model).
     **Recommend folding in as the regime-stratified ablation claims 1/4
     need anyway**, not standalone, unless the result is strongly positive.
   - **Claim 4** (routing/shadow-Q4): MEDIUM-HIGH novelty, highest
     implementation risk. Closest: **FineFT: Efficient and Risk-Aware
     Ensemble Reinforcement Learning for Futures Trading** (arXiv
     2512.23773) — routes across a strategy pool via VAE market-state
     similarity, but the pool is self-trained within one RL framework (same
     paradigm/authorship), no causal point-in-time execution harness. Real
     differentiator: routing across genuinely independent real upstream
     projects under one causal-execution/constraint harness. Zero
     large-scale experiment exists yet for this claim — pursue only with
     real multi-week budget.
   - **Claim 5** (abstention): MEDIUM-LOW, structurally fragile standalone.
     TrustTrade again closest (reweights rather than fully abstains — needs
     full-text confirmation), plus "When Alpha Breaks" (arXiv 2603.13252,
     single-model) and classic selective classification (arXiv 2110.14914).
     A reviewer could reasonably read this as "claim 1's fusion formula with
     a zero-weight special case." **Recommend folding into claim 1 as an
     ablation** ("fuse vs. abstain given the same diagnostic signal") rather
     than a standalone 5th claim.

   **Net scope conclusion from this pass**: only **claims 1 and 4** look
   standalone-paper-worthy; 2, 3, 5 become sections/ablations feeding into 1
   (3's regime angle can also feed 4). Both TrustTrade and FineFT are real,
   recent (2025-2026), well-institutioned papers that must be cited
   prominently in the final positioning report, not omitted.

## Next steps (in the new session)

1. Confirm `.claude/skills/research-lit`, `semantic-scholar`, `openalex`,
   `idea-discovery`, `novelty-check`, `research-review`, `kill-argument`,
   `research-refine` are now recognized by the `Skill` tool (try listing or
   invoking one).
2. **Separately**, verify Codex MCP actually completes a real request (not
   just `claude mcp list`'s connectivity check, which passed even though
   real calls failed 3/3 times this session) — try a trivial
   `mcp__codex__codex` call before relying on any of `novelty-check`
   Phase C / `research-review` / `kill-argument` / `research-refine`
   (all four depend on it per their own SKILL.md files).
3. Re-run `/research-lit`, `/semantic-scholar`, `/openalex` for real against
   the ICAIF 2023–2026 trend + 7 themes (calibration/robustness/risk-aware
   AI/decision-focused learning/interpretability/trustworthy AI
   agents/multi-agent finance) — the findings above are a starting point,
   not a substitute. Specifically re-verify **TrustTrade (arXiv 2603.22567)**
   and **FineFT (arXiv 2512.23773)** full text — both were found via
   WebSearch synthesis only (Phase C unavailable) and are load-bearing for
   the novelty verdicts on claims 1 and 4.
4. Re-run `/novelty-check` Phase C for real, once per candidate claim (5
   runs) — Phase B (WebSearch) results already exist in
   `docs/research_positioning/_working/NOVELTY_DOSSIER_claim{1..5}.md`;
   Phase C should update/confirm those, not restart from scratch.
5. Draft the 4 deliverables into `docs/research_positioning/`:
   `ICAIF_POSITIONING_REPORT.md`, `LITERATURE_MAP.md`, `NOVELTY_AUDIT.md`,
   `CLAIM_CANDIDATES.md`. Current working conclusion (subject to Phase C
   confirmation): lead with claims 1 and 4 as the two standalone-paper
   candidates; fold 2/3/5 in as sections/ablations.
6. Run `/research-review` and/or `/kill-argument` on the drafted positioning
   report for adversarial critique; incorporate findings.
7. Run `/research-refine` on the top recommended claim to sharpen it.
8. Finalize all 4 files, stop, and wait for human review (per the task
   brief — do not commit/push without being asked).

## Explicitly not done yet

- No file has been written under `docs/research_positioning/` other than
  this handoff note — the 4 required deliverables do not exist yet.
- `idea-discovery` has not been invoked at all yet. Note when invoking it:
  its own SKILL.md pipeline (Phase 4+) plans/runs pilot experiments — that
  is out of scope for this role (no experiment code). Use it only through
  its literature-survey/ideation/novelty-check phases, or explicitly
  instruct it to stop before any pilot-planning/experiment-code phase.
