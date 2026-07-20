# Self-Audit: docs/adapter_management/* and configs/adapter_registry.yaml (2026-07-19)

**Auditor**: same session/coordinator that drafted the registry and
report. `experiment-audit`'s external-reviewer step (Codex MCP,
`mcp__codex__codex`) was attempted twice with an adapted prompt (the
skill's default checklist — ground-truth provenance, score normalization,
dead metric code — targets ML experiment results and does not apply to a
design/selection document with no evaluation metrics, so the prompt was
rewritten to the skill's stated spirit: adversarial, verify-everything,
file:line evidence). Both attempts failed identically: `stream
disconnected before completion: error sending request for url
https://chatgpt.com/backend-api/codex/responses` — a network-layer
failure, the same one logged in
`docs/research_reports/2026-07-19_experiment_protocol_self_review.md` for
the sibling `EXPERIMENT_PROTOCOL.md` review. This is therefore a
**self-critique, not an independent-model review** — flagged explicitly
per this project's honesty norms; do not present it as an external review
in any later summary.

Per this session's governance rule, this file is an independent report
under `docs/research_reports/`, not a direct edit of
`docs/adapter_management/ADAPTER_SELECTION_REPORT.md` or
`configs/adapter_registry.yaml`.

---

## 1. Traceability spot-check

Re-verified directly (not re-trusted from the report's own prose):

- **Star counts**: re-fetched live for 3 adapters (`microsoft/qlib`,
  `DulyHao/AlphaForge`, `TauricResearch/TradingAgents`) — all 3 match the
  registry's `stars_snapshot` exactly (46410, 402, 93683). Stable across
  two independent fetches taken ~2 hours apart during this design pass.
- **`upstream_repo` / `requires_env`**: spot-checked 5 adapters
  (`qlib`, `finbert`, `rdagent`, `skfolio`, `finclaw`) via direct `grep`
  against their registry entries — all 5 match exactly, including
  `finclaw`'s PyPI-URL special case.
- **Paper citations**: all 3 populated `paper` fields
  (`alphaforge`/AAAI 2025, `alphagen`/KDD 2023 arXiv:2306.12964,
  `prediction_arena`/arXiv:2604.07355) were independently re-confirmed via
  direct grep of the respective adapter docstrings for `arxiv|AAAI|
  NeurIPS|ICML|KDD 20|ACM DL|doi\.org|accepted by|published at|conference
  paper` across all 26 files — no additional hits were found beyond these
  3 files plus `atlas` (whose 2 arXiv mentions are about *rejected
  alternative candidates*, not the adapter's actual wrapped upstream —
  correctly excluded from `atlas`'s `paper` field, and the registry does
  not claim one for `atlas`).

**Verdict: PASS.** No claim checked was found to be untraceable.

## 2. Internal consistency (report ↔ registry ↔ tier YAMLs)

- Every adapter named in the report's §3.2 exclusion table
  (`agentictrading`, `finmem`, `finrobot`, `pgportfolio`) has a matching
  `live_status`/`category`/`notes` entry in the registry supporting the
  stated exclusion reason (native-coverage caveat, BLOCKED, thin coverage,
  crypto-only+BLOCKED respectively) — no mismatch found.
- Every adapter named in §3.3 as a deliberate low-popularity inclusion
  (`deepalpha`, `finclaw`, `universal_portfolios`) has the corresponding
  low/absent `stars_snapshot` in the registry (10, `null`, 859) —
  consistent.
- §3.4's three remediation-flagged adapters (`finagent`, `tradingagents`,
  `fingpt`) all show `live_status: FAILED` in the registry with a
  `notes` field describing the specific infra cause (timeout vs. env
  error) matching the report's text.
- `atlas`'s exclusion from `popular_full.yaml` matches its registry
  `notes` field (crypto-mislabeling) word-for-word in substance.

**Verdict: PASS.** No contradiction found between the report's claims and
the registry's underlying data.

## 3. Set nesting correctness

Computed directly (not asserted):
```
paper_core (21) ⊆ popular_full (25) ⊆ extended_all (26) == registry (26)
popular_full − paper_core = {agentictrading, finmem, finrobot, pgportfolio}
extended_all − popular_full = {atlas}
```
All match the report's stated set differences exactly.

**Verdict: PASS.**

## 4. Honesty of the disclosed fabrication incident (§0)

Directly re-verified, not re-trusted:
- `grep -c -iE "neurips|2310\.08144|arxiv" adapters/trademaster_adapter.py`
  → **0 matches** — confirms the claimed citation is genuinely absent from
  the file, not just under-quoted.
- `adapter_registry.yaml`'s `trademaster` entry: `paper: null` — confirms
  the fabricated citation was not propagated into the permanent artifact.
- The report's §0 names the specific wrong claim
  ("NeurIPS 2023, arXiv:2310.08144"), states plainly that it "appears to
  have supplied outside/general knowledge rather than reporting only what
  the file states, despite being explicitly instructed not to," and does
  not hedge on whether the underlying real-world fact might be true — it
  explicitly separates "this may be a real paper in the world" from "this
  adapter's own docstring does not say so" and applies the stricter rule.
  It additionally discloses two more errors from the same source (wrong
  `upstream_repo` URLs for `tradingagents` and `vibe_trading`) rather than
  only the one caught in the audit trail.

**Verdict: PASS.** This reads as an accurate, non-minimizing disclosure —
if anything it over-discloses (naming the exact wrong claim verbatim)
rather than vaguely gesturing at "some inaccuracies were corrected."

## 5. Additional findings

- **N1 (minor)**: `adapter_registry.yaml`'s `commit` field is populated
  with the literal string "HEAD of default branch as of snapshot_date" for
  25/26 adapters (only `trademaster` has a real pinned SHA). This is
  honest (it doesn't fabricate a commit hash) but means the registry's
  `commit` column is not actually useful for exact reproducibility on 25
  entries — worth a follow-up task to pin real commits per adapter if
  reproducibility becomes a stated paper requirement, not fixed here
  (would require touching `adapters/vendor/` checkouts, arguably still
  configs/docs-adjacent but not done in this pass).
- **N2 (minor)**: the `cost_tier` taxonomy (LOW/MEDIUM/HIGH) conflates two
  independent axes — "needs a paid API" and "needs heavy local compute" —
  into one ordinal scale, so an adapter that's both HIGH-API-cost and
  compute-heavy (none currently, but plausible for a future adapter) would
  have no way to be represented. Flagged as a modest schema limitation,
  not an error in the current 26 entries (report §5 already discloses this
  is a coarse 3-bucket estimate).
- No evidence of inflated claims, invented exclusion reasons, or
  mismatched set membership beyond what's already self-disclosed in the
  report.

## Overall

All 4 checks: **PASS**. No FAIL or WARN-level integrity issue found in
this self-audit. The one real integrity incident in this design pass (the
trademaster citation fabrication by an earlier research subagent) was
caught before it reached a permanent artifact and is disclosed accurately.
This is a self-audit, not a cross-model one — treat with the corresponding
lower confidence until a working external-reviewer backend is available to
re-run it.
