# Milestone: schema v1 (5-question contract) — 2026-07-16

Recorded immediately before a breaking rewrite of `CONTRACT/schemas.py` from
the five-question contract (Q1 Decision / Q2 Sentiment / Q3 Signal / Q4
Portfolio / Q5 Backtest) to the four-layer **Canonical Adapter Contract
v2.0.0** (Q1 Action / Q2 State / Q3 Signal-Alpha / Q4 Policy, Q5 removed).

## Git anchor

```
git tag -l -n9 milestone/schema-v1-5q-icaif-suite
```

- Tag: `milestone/schema-v1-5q-icaif-suite`
- Commit: `219868bb04119ef43f073899d25c4cacaca76f37`
  ("update project instructions for schema v2" — CLAUDE.md only; the last
  commit with code still on schema v1 is `99126e3`, the 19-rule contradiction
  framework)
- Local tag only — not pushed to origin. Push with `git push origin
  milestone/schema-v1-5q-icaif-suite` if you want it preserved remotely too.

## What this snapshot contains

- `CONTRACT/schemas.py` v1: `Q1Decision`, `Q2Sentiment`, `Q3Signal` (old),
  `Q4Portfolio`, `Q5Backtest`, `AdapterResult(q1..q5)`.
- 16 adapters, all passing `python CONTRACT/test_harness.py --adapter ...`
  as of this commit.
- `reports/icaif_experiments/`: all 5 ICAIF experiments —
  coverage/compression (Exp1-2), calibration (Exp3), the 19-rule
  contradiction framework across 5 categories (Exp4, 335 cases / 264 real
  records), fusion ablation (Exp5) — 25 figures, `PAPER_FINDINGS.md`,
  `EXPERIMENT_REPORT.md`, `contradiction_rulebook.md`.
- `results/observations/`: the real observation batches these reports were
  computed from.

## How to get back to this exact state

```bash
# Just the old schema file, into a scratch location:
git show milestone/schema-v1-5q-icaif-suite:CONTRACT/schemas.py > /tmp/schemas_v1.py

# A full standalone working copy (doesn't disturb the current worktree):
git worktree add ../trading-ai-ensemble-v1-milestone milestone/schema-v1-5q-icaif-suite
```

## Why this exists

The v2 rewrite is intentionally destructive to `CONTRACT/schemas.py` (no v1
aliases kept) and will leave `CONTRACT/base_adapter.py` and all 16 adapters
import-broken until a later migration task updates them. This tag + note is
the rollback point so that later large-scope changes don't quietly bury the
v1 experiment record.
