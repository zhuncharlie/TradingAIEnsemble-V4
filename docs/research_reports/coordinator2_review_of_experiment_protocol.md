# Review note: EXPERIMENT_PROTOCOL.md (second coordinator pass)

Author: a second, independently-launched session working the same brief
("设计本项目的正式实验协议..."). Per the standing multi-agent instruction,
this is a supporting finding written to `docs/research_reports/`, not an
edit to any of the four files in `docs/experiment_design/`.

## Context

While drafting my own version of `EXPERIMENT_PROTOCOL.md`, I discovered
`DATA_SPLIT_PROTOCOL.md`, `BASELINE_DESIGN.md`, and `METRIC_DESIGN.md` had
already been written by a parallel session, and — moments before my own
write landed — `EXPERIMENT_PROTOCOL.md` was written too. My independent
research (three research forks + a live `mcp__massive__call_api` /
`yfinance` check) reached the same conclusions this document states:
26-adapter roster with Q1=6/Q2=7/Q3=10/Q4=13 coverage (including `qlib` as
Q3+Q4, confirmed via `grep questions_answered adapters/qlib_adapter.py`),
the same unreliable-adapter list (`finmem`, `pgportfolio` live-blocked;
`atlas` crypto-only mislabeling equity/ETF tickers; `agentictrading`/
`finrobot` low native coverage), and — independently verified, matching
exactly — `massive.com`'s current plan caps historical daily aggregates at
~2 years (`403 NOT_AUTHORIZED` before 2024-07-19) while `yfinance` genuinely
serves 10 years for this project's tickers. Given this level of convergence
and the existing document's completeness, I chose not to overwrite it;
this note records the one gap worth considering, not a competing draft.

## Possible gap: no standalone "raw Q4 policy validation" diagnostic

The task brief's reference list included **Exp4 Policy Validation**: for
each Q4 adapter, compute total return, annualized return, Sharpe, Sortino,
max drawdown, Calmar, and alpha *as a diagnostic on that adapter's own
native policy*, independent of any fusion/baseline-selection purpose.

In the current `EXPERIMENT_PROTOCOL.md`:
- **D6** (Risk & Exposure Audit) computes gross/net exposure, concentration,
  turnover, and constraint compliance — not return-based metrics.
- **M1** (Baseline Fusion Bench) runs `BASELINE_DESIGN.md` §3.4's
  "single-best-Q4-policy" baseline, which requires computing each
  candidate adapter's Sharpe on VAL to select the best one — but M1's
  stated output is the *baseline bank's* aggregate numbers, not a reported
  per-adapter leaderboard as a standalone diagnostic finding.

So the per-adapter return/Sharpe/Sortino/MDD/Calmar/alpha numbers will
exist as an intermediate byproduct of M1, but there's no experiment whose
*stated* hypothesis/expected-result/failure-interpretation is "how does
each of the 13 Q4 adapters perform on its own, before any fusion" — which
is a mildly different question from "which one should M1 pick as a
baseline." This may be an intentional simplification (folding it into M1
reduces experiment count, consistent with the brief's "不要形成16个散乱实验"
instruction) rather than an oversight — flagging for the coordinator's
judgment rather than asserting it needs a fix.

If judged worth adding, the smallest change would be: extend D6's method to
also compute `METRIC_DESIGN.md` §2.1 (return-based metrics), not just
§2.2–2.3 (risk/turnover), and add one sentence to D6's hypothesis covering
"per-adapter native-policy performance, independent of fusion." No new
experiment number needed.

## No other issues found

Structure, causality handling, adapter classification, and the
D1–D7/M1–M4/A1–A2/Ro1–Ro3 taxonomy are consistent with the three companion
documents (verified by reading all four in full) and consistent with the
repo state verified directly (schema fields, adapter roster, harness
causality guards, data availability). No factual errors found.
