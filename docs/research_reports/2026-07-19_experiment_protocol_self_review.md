# Self-Review: docs/experiment_design/* (2026-07-19)

**Reviewer**: same session/coordinator that drafted the four protocol
documents (Codex MCP external review was requested per the task brief but
failed 3/3 attempts with `stream disconnected ... error sending request for
url https://chatgpt.com/backend-api/codex/responses` — a network-layer
failure, not a prompt issue; the `research-refine` skill was also tried
first but its workflow is built for turning a vague idea into a paper-style
method proposal via a Problem-Anchor/Method-Thesis scaffold, which doesn't
fit "critique an already-finished experiment-design document" and would
have produced mismatched artifacts). This is therefore a self-critique, not
an independent-model review — flagged explicitly per this project's honesty
norms; do not present it as an external review in any later summary.

Per this session's governance rule, this file is an independent report
under `docs/research_reports/`, not a direct edit of the four target
documents. The coordinator (same session) subsequently applied the
CRITICAL/IMPORTANT fixes below directly to the four documents; this file
records what was found and what was actually changed vs. left open.

---

## CRITICAL

### C1. Class-R TEST window (`DATA_SPLIT_PROTOCOL.md` §3.1) is already contaminated by existing pilot data

**Claim**: §3.1 nominally places Class R's TEST window at `2025-07` to
`2026-07`, described as "embargoed: touched at most once."

**Problem**: Verified directly against `results/observations/
observation_batch_day1_historical_extension/index.csv` — Class-R adapters
`deepalpha`, `alphagen`, `atlas` (and per the batch's own README, also
`finrl`, `qlib`) already have real, already-computed, already-read (by this
very design pass) decisions at `2026-05-15` through `2026-06-08`, and the
main pilot batch adds `2026-07-06`. All of these dates fall inside the
nominal `2025-07..2026-07` TEST window. The "touched at most once, frozen
before evaluation" guarantee is violated before the protocol even starts —
this reviewer (and the pilot study before it) has already seen Class-R
decisions and their surrounding analysis inside that window.

**Fix applied**: `DATA_SPLIT_PROTOCOL.md` §3.1 updated to explicitly carve
out and embargo the already-touched dates (`2026-05-15, 2026-05-21,
2026-05-27, 2026-06-02, 2026-06-08, 2026-07-06, 2026-07-18`) from the
Class-R TEST window, and to note the unified-harness run's `as_of=
2024-01-15` snapshot is *not* contaminated (it falls in the CAL window, not
TEST) and may still be used as CAL material.

### C2. `atlas` is misclassified as a straightforward Class-R adapter without disclosing its known ticker-substitution behavior

**Claim**: `DATA_SPLIT_PROTOCOL.md` §1 lists `atlas` in Class R (replay-
capable) with no caveat.

**Problem**: `results/observations/observation_batch_day1_historical_
extension/index.csv` documents, per-row, a **known limitation**: `atlas`'s
bundled dataset is crypto-perpetuals only (`2021-11-06..2024-08-14`); any
equity/ETF ticker requested causes it to silently report the *same BTCUSDT
signal* mislabeled under the requested ticker name (self-disclosed by the
adapter in `supporting_evidence`, per the index.csv note, so not a
fabrication by the harness — but consuming `atlas`'s Q3 output for any
non-crypto ticker without this caveat would silently treat 10 different
ticker labels as if they were 10 independent signals when they are the
same one value repeated). This is exactly the kind of "compression loss /
hidden inconsistency" D1/D4 are supposed to catch — but the caveat needs to
be visible *before* D1 runs, not discovered by it, since it affects the
Class-R/replay-capable classification and the universe design itself
(§2.1's 10-ticker universe assumes each ticker gets an independent signal).

**Fix applied**: `DATA_SPLIT_PROTOCOL.md` §1's `atlas` entry annotated with
this caveat; §2.1 (universe) cross-referenced so any experiment using
`atlas` on non-crypto tickers in the standard universe explicitly excludes
or flags it rather than silently averaging in 10 copies of one signal.

---

## IMPORTANT

### I1. D1's coverage hypothesis is close to tautological as worded

`EXPERIMENT_PROTOCOL.md` D1 hypothesis (a) — "the Q1-Q4 taxonomy
structurally covers all 26 adapters with no orphaned capability" — is
nearly guaranteed true by construction: every file under `adapters/*.py`
was written specifically to implement `BaseAdapter`'s `q1_action`/
`q2_state`/`q3_signal`/`q4_policy` methods, so "coverage" is close to
definitional, not an empirical finding. The genuinely testable part is
already hypothesis (b) (declared vs. implemented vs. observed mismatch).

**Fix applied**: reworded D1's hypothesis (a) in `EXPERIMENT_PROTOCOL.md`
to frame coverage as a sanity check the experiment reports but does not
treat as a real finding, with (b) — mismatch detection — as the actual
hypothesis under test.

### I2. "Single best adapter" baselines don't account for selection-on-noisy-VAL bias (winner's curse)

`BASELINE_DESIGN.md` §2.3/§3.4 selects the best adapter by VAL-window
performance, freezes it, evaluates on TEST — standard practice, but with 6
(Q1), 7 (Q2), 10 (Q3), or 13 (Q4) candidates and VAL samples that are
already known to be small in places (pilot: 28/39 calibration buckets had
n<10), the *selected* best-on-VAL adapter is expected, by construction, to
regress toward the mean on TEST relative to its VAL score — a textbook
winner's-curse effect. As written, the baseline design doesn't warn a
reader that "single best adapter underperforms its own VAL-window number on
TEST" is an expected artifact, not evidence the method under test is
unusually strong by comparison.

**Fix applied**: `BASELINE_DESIGN.md` §2.3/§3.4 given an explicit
winner's-curse note.

### I3. CVaR at 99% is asserted as a metric without a sample-size caveat

`METRIC_DESIGN.md` §2.1 lists "CVaR at 95% and 99% (historical, not
parametric)" without qualification. A historical CVaR@99% needs on the
order of hundreds to thousands of independent observations to be anything
but noise; the TEST window (§3.1, ~12 months, purged) will have on the
order of ~230 trading days at most, and far fewer independent Q4 rebalance
points for STEPWISE adapters with longer rebalance frequencies. A 99%
historical CVaR from ~230 daily points is estimating a tail with ~2-3
expected exceedances — not a reliable number.

**Fix applied**: `METRIC_DESIGN.md` §2.1 CVaR@99% flagged as
directional-only given expected sample size, consistent with how §1.2
already treats n<10 calibration buckets.

### I4. Contradiction severity weighting (D4/§1.7) is gestured at, not specified

`METRIC_DESIGN.md` §1.7 says severity should use "a documented,
non-fabricated weight per rule" with one worked example (risk-level
distance from threshold) but does not specify a concrete, general formula
usable across all redesigned D4 rules. As written this is not yet
executable — whoever implements D4 would have to invent the severity
function themselves, which is a bigger decision than this document should
leave implicit.

**Left open (not fixed)**: this needs a concrete design decision (e.g.
normalized distance-from-threshold per rule, min-max scaled to [0,1]) that
is more naturally made when D4's rulebook redesign actually happens (it
depends on what the Q4-constraint-violation/calibration-flag substitute
signals for the removed Q5-based rules end up looking like). Flagging here
so it isn't silently forgotten; `EXPERIMENT_PROTOCOL.md` D4 already notes
the rulebook needs redesign, extended with a pointer to this specific gap.

### I5. D5's hypothesis mixes a descriptive claim with M2's normative claim

`EXPERIMENT_PROTOCOL.md` D5 hypothesis says reliability is regime-dependent
"...and this is exploitable (motivates M2)" — but D5 itself never tests
exploitability, only measures regime-dependence. As worded, a reader could
mistake D5 for having tested something M2 alone actually tests, which
blurs the falsifiability boundary between the two experiments.

**Fix applied**: `EXPERIMENT_PROTOCOL.md` D5 hypothesis reworded to state
only the descriptive claim; "exploitability" language moved fully into the
already-existing M2 hypothesis (no new content needed there, just removed
the duplicate/blurred phrasing from D5).

---

## MINOR

### N1. Block-bootstrap block count is small

`METRIC_DESIGN.md` §4's block length (≥20 trading days) against a ~252-day
TEST window yields only ~12 non-overlapping blocks — usable for a
stationary bootstrap but on the low side for tight CIs. Not fixed (this is
a inherent small-sample constraint of a 1-year TEST window, not a design
error); noted here so it isn't rediscovered as a surprise later.

### N2. Ro1/Ro2's "post-hoc re-slicing doesn't count as a second TEST touch" argument deserves one more sentence

`EXPERIMENT_PROTOCOL.md` Ro1/Ro2 argue that re-slicing already-frozen TEST
results by regime/leave-one-adapter-out doesn't violate the single-TEST-
touch rule "since it's the same evaluation, sliced." This is defensible
but only for genuinely *post-hoc* slicing of results that already exist,
not if it triggers regenerating any adapter decision inside the TEST
window. Ro2 already partially acknowledges this ("a true LOO re-fit would
require touching CAL/VAL again"); not changed further, just flagged as a
place a future implementer must be careful, not a design flaw.

---

## (f) Internal consistency check across the four documents

Checked: every metric named in `EXPERIMENT_PROTOCOL.md`'s per-experiment
"Metric" line resolves to an actual subsection in `METRIC_DESIGN.md`, and
every "Baseline" line resolves to an actual subsection in
`BASELINE_DESIGN.md`. No dangling references found. One near-miss: M3's
metric line emphasizes Sortino/Calmar/CVaR "over raw Sharpe" — `METRIC_
DESIGN.md` §2.1 defines all of these but does not itself state a
weighting/priority order across metrics; this is fine as written since the
weighting is M3-specific framing, not a metric-definition gap, so no fix
needed.
