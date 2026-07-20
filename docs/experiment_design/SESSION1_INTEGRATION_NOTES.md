# Session 1 Integration Notes

Explicit record of how this session's experiment protocol absorbs, extends,
or declines to act on Session 1's ("Literature Review + Research
Positioning") outputs, per this session's required reporting obligation.
Session 1's files (`docs/research_positioning/ICAIF_POSITIONING_REPORT.md`,
`LITERATURE_MAP.md`, `NOVELTY_AUDIT.md`, `CLAIM_CANDIDATES.md`,
`_working/REFINED_CORE_CLAIM.md`) were read in full, read-only, before any
protocol design began, and are not modified by this session.

---

## 1. Session 1's currently recommended primary claim

A combined submission built on one shared reliability/contradiction
diagnostic substrate, with two conditional decision-layer contributions:
**reliability-/contradiction-weighted fusion** (Candidate 1, vs. TrustTrade
arXiv 2603.22567 and ContestTrade arXiv 2508.00554) and **reliability-aware
routing + shadow Q4 policy construction** (Candidate 4, vs. FineFT arXiv
2512.23773, confirmed ACM SIGKDD not ICAIF). After adversarial review
(`kill-argument`-adapted + `research-refine`-adapted), Session 1 sharpened
this into **one primary scientific claim independent of whether fusion or
routing individually succeed**: *schema-level structural contradiction
among heterogeneous financial-AI systems — restricted to a small,
pre-registered ontology of logically incompatible field combinations — is
an out-of-sample, model-agnostic leading indicator of degraded forecast and
policy quality, carrying incremental predictive information beyond each
system's own self-reported confidence* (`_working/REFINED_CORE_CLAIM.md`).

This is formalized as **H1** in `EXPERIMENT_PROTOCOL.md` §2.1, verbatim in
spirit, operationalized into a testable statistical claim.

## 2. Main competing prior work

| Work | Competes with | Session 1's finding | This session's response |
|---|---|---|---|
| TrustTrade (arXiv 2603.22567) | L2.1 fusion | Cross-agent agreement-weighted consensus, LLM-only paradigm; Codex Phase C called Candidate 1 "borderline... in the danger zone" relative to this paper, twice, independently | Made a **non-negotiable baseline** in `BASELINE_DESIGN.md` §1, not just a citation; the "correct lone dissenter" case-study Session 1 specified as mandatory is built into L2.1's method spec (`EXPERIMENT_PROTOCOL.md` §6) |
| ContestTrade (arXiv 2508.00554) | L2.1 fusion | Surfaced by a parallel Session-1 pass; closer than TrustTrade on the outcome-utility-weighting axis specifically | Also made non-negotiable in `BASELINE_DESIGN.md` §1, alongside TrustTrade, per Session 1's explicit "both must be cited and differentiated, not just one" |
| FineFT (arXiv 2512.23773, confirmed ACM SIGKDD not ICAIF) | L2.2 routing | Self-trained within-framework VAE routing; Session 1's non-negotiable condition for L2.2's novelty verdict to hold empirically | Made non-negotiable in `BASELINE_DESIGN.md` §3 as a baseline that must be **retrained on this project's own harness data**, not just cited — the single most expensive baseline in this protocol, flagged accordingly in `RISK_AND_FAILURE_PLAN.md`'s compute-budget section |
| When Alpha Breaks (arXiv 2603.13252) | L2.4 abstention | Single-model epistemic-uncertainty trigger; closest for evaluation philosophy (risk/drawdown-first), not trigger mechanism | Informed `BASELINE_DESIGN.md` §4's entropy/dispersion-rule baseline design (the general-uncertainty-trigger comparison point) |

## 3. Novelty risk carried into this protocol

Session 1's `NOVELTY_AUDIT.md` cross-claim synthesis: all 5 candidate
claims scored in a narrow 5–7/10 band, "real but genuinely marginal —
combination-and-scale, not a clean gap," and **every claim's viability is
conditional on running specific, named baseline experiments, not on
framing alone**. This is the single sentence this session treated as most
binding: `EXPERIMENT_PROTOCOL.md`'s baselines in §6 for L2.1/L2.2 are
exactly Session 1's named non-negotiable experiments, not a generic
baseline list this session invented independently.

## 4. Key adversarial-review findings absorbed

From Session 1's `kill-argument`-adapted pass (`ICAIF_POSITIONING_REPORT.md`
§6, computed verdict **WARN**, `reason_code:
partial_critical_or_repeated_major`):

- **P_1 (critical, "no defensible core contribution independent of
  experiments")** — Session 1 resolved this at the *positioning* level via
  `research-refine`-adapted sharpening into H1. This session's job was to
  make H1 **falsifiable and executable**, not just stated: §2.2's
  pre-registered contradiction ontology (explicitly flagged by Session 1 as
  "not yet done... out of this role's scope to produce") and §2.3/§2.4's
  operational `E` definition and statistical test are this session's direct
  response to P_1, carried one level deeper than Session 1 could go.
- **P_5 (critical, "FineFT differentiation cross-referenced but not
  inlined")** — Session 1 fixed this in its own report text; this session's
  response is structural, not textual: `BASELINE_DESIGN.md` §3 makes the
  FineFT-style baseline an executable, retrained comparison, not a citation
  at all.
- **P_6 (critical, "framing is experiment-contingent")** and the
  **structural gap** (fusion/routing/abstention did not yet share one real
  evaluation protocol, surfaced independently by Session 1's
  `research-review`-adapted pass) — this is `EXPERIMENT_PROTOCOL.md` §4's
  three-track Shared Evaluation Protocol and `DATA_SPLIT_PROTOCOL.md` §4's
  field-by-field specification, in full. This is the single largest piece
  of net-new design work this session contributes beyond formalizing what
  Session 1 already recommended.
- **Adapter-independence/provenance gap** (Session 1's risk table: "'26
  independently-published, heterogeneous systems' is asserted throughout
  but never exhibited") — this session did **not** build the provenance
  table itself (that is Session 3's registry, per this project's session
  boundaries), but formalized the exact requirement in
  `ADAPTER_REGISTRY_REQUIREMENTS.md` so Session 3 can build it, and made
  eligibility conditional on it in `DATA_SPLIT_PROTOCOL.md` §5.
- **Financial-evaluation hygiene gap** (survivorship bias, look-ahead
  beyond the Q4 harness's own claim, inconsistent transaction costs,
  regime-label arbitrariness, multiple-testing exposure) — absorbed
  directly into `RISK_AND_FAILURE_PLAN.md` and `DATA_SPLIT_PROTOCOL.md`
  §6's regime-labeling causality rule and §3's embargo rule.

## 5. What was absorbed into the experiment protocol

- The 5-candidate scoping (2 standalone, 3 folded-in) →
  `EXPERIMENT_PROTOCOL.md` §3's mapping table, preserved exactly (L2.1/L2.2
  kept standalone per Session 1, L1.2/L1.4/L2.4 folded in per Session 1).
- The two non-negotiable baseline experiments (TrustTrade/ContestTrade-style
  for fusion, FineFT-style for routing) → made literally non-negotiable,
  first-class rows in `BASELINE_DESIGN.md`, not optional citations.
- The "lead with shadow-policy over routing" framing (Session 1's Codex
  Phase C: shadow policy is "the stronger, more defensible half") →
  `EXPERIMENT_PROTOCOL.md` §6 marks L2.3 (shadow Q4) MUST-RUN and main-
  paper, same tier as L2.1/L2.2, rather than a minor sub-experiment of
  routing.
- The "calibration" terminology trap (6/7 ICAIF papers with "calibrat-" in
  the title mean pricing/simulation calibration, not ML confidence
  calibration) → not directly a protocol-design concern, but respected in
  this document set's own vocabulary (this session consistently writes
  "calibration" only in the ML-confidence sense already scoped by context,
  matching Session 1's own disambiguation discipline).
- The regime-conditional tolerance for H1/H4 (a null or regime-limited
  result is pre-registered as informative, not thin) →
  `EXPERIMENT_PROTOCOL.md` §2.4/§2.6 and `CLAIM_TO_EXPERIMENT_MATRIX.md`'s
  explicit distinction between "H4 supported" and "H4 null but reported."

## 6. What was NOT absorbed, and why

- **The exact numeric practical-significance threshold for H1** (what
  incremental-AUC/pseudo-R² gain counts as "practically meaningful") is
  deliberately left unset in `EXPERIMENT_PROTOCOL.md` §2.4, to be fixed at
  the pilot stage using real pilot data, not invented now from Session 1's
  purely qualitative positioning work — setting a fake-precise number today
  would itself be a form of fabrication this project's CLAUDE.md forbids.
- **Session 1's Alt B** (lead with Candidate 4/routing alone, drop fusion
  to future work, justified by routing's higher 7/10 vs. 6/10 novelty
  score) is **not** adopted as this protocol's structure — this protocol
  designs experiments for *both* L2.1 and L2.2 as co-equal MUST-RUN groups,
  because Session 1 itself did not resolve Alt A vs. the combined main line
  vs. Alt B, and choosing between them is a paper-strategy decision for
  whoever drafts the actual paper after results exist, not an experiment-
  design decision this session should make unilaterally. Both are designed
  so either choice remains available.
- **Session 1's Alt C** (benchmark-artifact fallback framing) is reflected
  only implicitly — L1.1–L1.5's diagnostics, if released, *would* constitute
  such a benchmark artifact, but this session did not design a separate
  "release as benchmark" experiment track, since that is a
  publication-packaging decision, not an experiment-design one.
- **The exact final adapter list** for the historical main experiment is
  explicitly not decided here (Session 3's registry query result, per
  `DATA_SPLIT_PROTOCOL.md` §5 and `ADAPTER_REGISTRY_REQUIREMENTS.md` §4) —
  Session 1's "26 real adapters" language is treated throughout this
  protocol as an upper bound subject to `DATA_SPLIT_PROTOCOL.md` §5's
  TIER-1 eligibility filter, not a fixed count.
- **L2.6 (full learned meta-fusion, Exp17's general form)** was demoted to
  optional-enhancement/appendix-only in `EXPERIMENT_PROTOCOL.md` §6,
  diverging from a literal reading of the user's original Exp17 description
  as co-equal to fusion — justified by `research-refine`'s "smallest
  adequate mechanism" principle and by Session 1 not having scored a
  full-meta-model variant as part of any of its 5 audited candidates; this
  session judged that promoting an unaudited 6th mechanism to main-paper
  status without its own novelty check would be scope creep beyond what
  Session 1 actually cleared.

## 7. A note on evidence-type discipline, inherited from Session 1

Session 1's `ICAIF_POSITIONING_REPORT.md` §2 explicitly distinguishes
"search found no collision" (scholarly evidence) from "a cross-model
reviewer agrees with our read" (process corroboration). This session
applies the same discipline to every real Codex MCP call made while
drafting this protocol (see `EXPERIMENT_PROTOCOL.md` §6,
`CLAIM_TO_EXPERIMENT_MATRIX.md`, `RISK_AND_FAILURE_PLAN.md`,
`EXPERIMENT_DEPENDENCY_MAP.md`): thread IDs are cited as **process
evidence** that a real, non-fabricated review occurred, never as
independent validation that the resulting design decision is correct.
