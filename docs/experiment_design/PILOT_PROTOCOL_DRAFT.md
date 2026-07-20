# H1 Pre-Pilot Protocol Draft

**Status: DRAFT ONLY. Not approved for execution. No experiment code was
written and no pilot was run to produce this document — this is a
specification, nothing else.** Requires explicit human approval before
any of it is implemented or executed, per this session's own scope
limits and `EXPERIMENT_DEPENDENCY_MAP.md`'s Pilot-stage entry criteria.

**Framing, stated up front and non-negotiable**: given `H1_FRESH_REVIEW.md`'s
honest verdict (**REVISE**, twice, not PASS — see that file), this
pre-pilot is scoped as a **methodology dry run only**: does the pipeline
(alignment → labels → calibration features → `C` → pooled model →
robustness checks) execute end-to-end without a schema, causality, or
implementation-ambiguity failure? **It does not produce claim-bearing
evidence for H1 and must never be reported as if it does** — sample size
at this scale (§7) is almost certainly underpowered for any real
inference, and H1's own specification is not yet frozen (Round 2's
tuple-level model-specification gap, `H1_FRESH_REVIEW.md`, is exactly the
kind of thing this dry run exists to surface concretely, not paper over).

---

## 1. Target pipeline (minimal, per the task brief)

```
existing adapter outputs (pilot_core.yaml, already-produced/re-runnable
    via CONTRACT/adapter_runner.py — no retraining)
        |
        v
canonical aligned decision table  (one row per (ticker, as_of) tuple that
    at least 2 pilot_core adapters both answered)
        |
        v
1d / 5d forward-return labels  (NOT 20d — deliberately out of scope, per
    the task brief's explicit minimal-pilot instruction)
        |
        v
calibration features  (per-adapter, per-ConfidenceKind — L1.2's machinery,
    minimal form: raw hit-rate only, no full reliability-diagram fit)
        |
        v
binary structural contradiction C  (EXPERIMENT_PROTOCOL.md §2.2's current
    ontology draft, version-tagged — see §5 below)
        |
        v
generic disagreement (normalized Shannon entropy, §2.3.1) + missingness
    control
        |
        v
pooled H1 model  (logistic regression, see §8 — deliberately the simplest
    correctly-specified form the tiny pilot sample can support)
        |
        v
block bootstrap + leave-one-out  (sanity-check the mechanics run, not a
    powered robustness claim at this sample size)
```

**Explicitly out of scope for this pre-pilot** (per the task brief):
full learned router (L2.2), meta-fusion (L2.6), large-scale
hyperparameter tuning, all 26 adapters, full Q4 rolling execution, the
20d horizon, and any access to the final test set.

## 2. Pilot adapters and selection basis

From `configs/adapter_sets/pilot_core.yaml` (full reasoning there):
**`qlib`, `skfolio`, `finrl_x`, `deepalpha`** form the primary,
tuple-aligned core (shared universe, §3). **`trademaster`** is included
but run as a **separate, non-aligned Native-Capability-Track diagnostic**
(its own DJ30 2021 window, not pooled into the same `(ticker, as_of)`
tuples as the other four) — see §3's explicit reasoning for why forcing
it into alignment would itself be a data-integrity error, not a
methodology strength.

| Adapter | Role | Cost tier | Latency (observed) | Paid API? |
|---|---|---|---|---|
| `qlib` | Q3+Q4, gradient_boosted_ml | MEDIUM | 61.7s | No |
| `skfolio` | Q4, classical_optimization | LOW | 15.9s | No |
| `finrl_x` | Q2+Q3+Q4 | MEDIUM | 206.4s (dominant cost driver) | No |
| `deepalpha` | Q1+Q3 — **flagged exception**, sole Q1 source in the entire registry | MEDIUM | 18.0s | No |
| `trademaster` (native-track only) | Q4, second RL paradigm | MEDIUM | 45.4s | No |

**No adapter in this pilot requires a paid external API** — all five are
CPU/GPU-local-compute-only per `configs/adapter_registry.yaml`'s
`requires_paid_api: false`. This materially simplifies the cost estimate
(§10): the pre-pilot's cost is compute-time only, not metered dollar
spend.

## 3. Ticker / universe

**Primary aligned universe: `AAPL`, `MSFT`, `NVDA`** — reusing the exact
precedent already established and live-verified in
`NEW_ADAPTER_INTEGRATION.md`'s unified harness run
(`unified_harness_2026_07_18`), on which `qlib` and `skfolio` were already
directly exercised, and `deepalpha`'s own capability-recovery verification
used real `AAPL` predictions.

**Known, disclosed risk (not resolved, surfaced deliberately)**:
`finrl_x`'s dynamic universe selection (ML-selected top-25% of its own
fixed 8-ticker pool) is real but **not caller-configurable**
(`configs/adapter_registry.yaml` notes). This pre-pilot cannot force
`finrl_x` onto `{AAPL, MSFT, NVDA}` specifically. **Mitigation for this
dry run only**: run `finrl_x` once at the pilot's `as_of` start date,
record which tickers its own top-25% selection actually returns, and
report the *actual overlap* with `{AAPL, MSFT, NVDA}` as a first-class
pilot output (§11's manifest) — if the overlap is empty, that is itself a
valid, informative pre-pilot finding ("finrl_x cannot be tuple-aligned
with this universe without an upstream modification," which would be a
real input to whether `finrl_x` belongs in the eventual claim-bearing
experiment's aligned core at all), not a pipeline failure to route
around silently.

`trademaster`'s native universe (real DJ30, 2021-01-04..2021-12-31, NVDA
absent/JNJ substituted) is fundamentally incompatible with
`{AAPL, MSFT, NVDA}` over the pilot's intended 2023-2024-era window (§4) —
this is exactly why it runs as a separate native-track diagnostic, not
force-aligned.

## 4. Calibration / validation windows and embargo

Per `DATA_SPLIT_PROTOCOL.md` §1/§1.1's interval discipline, scaled down to
pilot size:

| Interval | Window (draft) | Purpose |
|---|---|---|
| Calibration | `2023-06-01` .. `2023-11-30` (6 months) | Fit per-adapter hit-rate calibration features (minimal form, §1); fit the adapter-relative 90th-percentile risk threshold (`EXPERIMENT_PROTOCOL.md` §2.2) on this window only |
| **Embargo** | `2023-12-01` .. `2023-12-07` (5 trading days = the pilot's own max horizon, 5d — not 20d, since the 20d horizon is out of scope for this pilot per §1) | No tuple in this window is used for fitting or evaluation on either side |
| Validation | `2023-12-08` .. `2024-03-31` (~4 months) | Where the pooled H1 model itself is fit/evaluated for this dry run (there is no separate "test" interval for a non-claim-bearing pilot — see §1's framing: this pilot never touches, and is not part of, the project's real final test set) |

**`as_of`/`data_cutoff` sequence**: one shared daily trading-calendar
sequence across the validation window, reusing `DATA_SPLIT_PROTOCOL.md`
§4's Controlled-Scientific-Track discipline at pilot scale.

## 5. Contradiction ontology version

Uses `EXPERIMENT_PROTOCOL.md` §2.2's **current draft** (as revised through
this session's Task B consistency fixes) — explicitly version-tagged as
`v0.3-draft` (v0.1 = Session 2 original; v0.2 = post-adversarial-review
fixes, Session 2 §8; v0.3 = post-Task-A/B fixes, this session) in this
pilot's own output manifest (§11), **not** asserted as frozen. Any
contradiction event this pilot detects must be tagged with the ontology
version that produced it, so a future re-run against a revised ontology
(e.g. once `H1_FRESH_REVIEW.md`'s tuple-level model-specification gap is
resolved) is never confused with this run's output.

## 6. Generic disagreement metric and missingness control

Exactly `EXPERIMENT_PROTOCOL.md` §2.3.1's formula, no pilot-specific
simplification: normalized Shannon entropy (base-2, divided by log2(3))
of the `{-1, 0, +1}`-mapped directional-vote distribution across whichever
of `{qlib, skfolio, finrl_x, deepalpha}` are eligible (answer a
directional Q1/Q3 call) at a given tuple. Missingness control: binary
indicator, `1` if fewer than the modal count of eligible adapters are
present at a tuple (with only 4 adapters in the aligned core, "modal
count" will very likely just be a small integer like 3 or 4 — this small-N
degeneracy is itself worth recording as a pilot finding, not hidden).

## 7. Expected sample size (rough, not a power calculation)

3 tickers × ~80 trading days in the validation window (~4 months,
weekends/holidays excluded) × up to 4 aligned adapters ≈ **on the order of
a few hundred `(ticker, as_of)` tuples at most**, before any missingness
exclusion. This is almost certainly **underpowered** for §2.4's real
power-analysis procedure (which is itself only meant to run at full,
claim-bearing scale) — stated explicitly so no one mistakes this dry run's
output for a real H1 test. The pilot's own job is to confirm the pipeline
*produces* a well-formed sample of roughly this size without a schema/
causality break, not to produce a defensible p-value.

## 8. Pooled model specification (minimal, dry-run form)

Logistic regression: `E ~ confidence + C + disagreement_entropy +
missingness_indicator` — **no adapter-pair random-effect term in this
pilot**, a deliberate, disclosed simplification: `H1_FRESH_REVIEW.md`
Round 2 flagged that the tuple-level representation of a per-adapter/
per-pair effect term was not fully specified even in the main protocol;
attempting to fit a real random-effect structure on a 4-adapter,
few-hundred-tuple pilot sample would be close to non-identifiable and
would not actually test anything useful about the *real* claim-bearing
model. **This pilot's job regarding that gap is to surface it concretely**
(§12) for whoever next revises `EXPERIMENT_PROTOCOL.md` §2.3.1/§2.3.2's
tuple-level specification, not to prematurely resolve it under this
session's own tight scope.

## 9. Robustness checks run (mechanics only, not power-bearing)

- **Block bootstrap**: block length = 5 trading days (this pilot's own
  max horizon), on the pooled model's incremental-`C` coefficient — run to
  confirm the bootstrap code path executes correctly on real pilot data,
  not to produce a claim-bearing CI.
- **Leave-one-adapter-out**: 4 refits, each excluding one of
  `{qlib, skfolio, finrl_x, deepalpha}` — with only 4 adapters, this is a
  coarse sanity check (does the pipeline handle a shrunken adapter set
  without breaking?), not a real robustness claim.
- **Leave-one-ticker-out**: 3 refits, each excluding one of
  `{AAPL, MSFT, NVDA}` — same caveat.

## 10. Estimated compute cost, timeout, failure handling

- **No paid API cost** (§2) — all five pilot adapters are local-compute
  only.
- **Compute time estimate**: dominated by `finrl_x` (206.4s/call observed)
  and `qlib`/`trademaster` (61.7s/45.4s); across ~80 trading days ×
  4-5 adapters, a rough serial-execution upper bound is on the order of
  hours, not days, for the aligned core alone — an explicit, generous
  **per-adapter-call timeout of 300 seconds** is proposed (covers
  `finrl_x`'s 206.4s observed latency with ~45% margin; matches the
  already-established precedent that `finrl`'s own smoke test once needed
  a timeout budget above 250s per `ADAPTER_CAPABILITY_RECOVERY.md`).
- **Failure handling**: reuses `DATA_SPLIT_PROTOCOL.md` §4's shared
  missing-output policy uniformly across all five adapters — a failed/
  timed-out call at one `(ticker, as_of)` point is logged and excluded
  from that specific tuple's row, never silently imputed, and does not
  invalidate other tuples.

## 11. Output manifest schema

Reuses `RISK_AND_FAILURE_PLAN.md` §1 Category C's manifest design exactly
(the same schema the real claim-bearing experiment must use): one row per
pre-registered `(ticker, as_of, adapter)` cell, `status ∈ {computed,
ineligible, failed, excluded_by_predefined_rule}`, plus this pilot's own
additions: `ontology_version` (§5), and `finrl_x_universe_overlap` (§3's
disclosed risk, recorded once per run). Every number this pilot reports
must trace to a `computed` manifest row.

## 12. What this pre-pilot is specifically designed to surface

Not a list of hoped-for positive results — a list of **implementation
ambiguities this draft could not resolve on paper alone**, which is
exactly what a methodology dry run is for:
1. Whether `finrl_x`'s real top-25% ticker selection ever overlaps
   `{AAPL, MSFT, NVDA}` at all (§3).
2. Whether the "modal eligible-adapter count" for the missingness control
   (§6) is stable or degenerate at this small an adapter count.
3. Whether the minimal, no-random-effect pooled model (§8) is even
   well-behaved (convergence, separation) at pilot sample size — a
   concrete, empirical input to how `EXPERIMENT_PROTOCOL.md` §2.3.1/
   §2.3.2's fuller tuple-level specification should eventually be written.
4. Whether the 90th-percentile adapter-relative risk threshold (§2.2) is
   even computable from a 6-month calibration window per adapter, or needs
   a longer window at claim-bearing scale.

None of these are resolved by this document — they are the reason a
human-approved dry run, not a further paper exercise, is the right next
step, per `GO_NO_GO_FOR_PILOT.md`.
