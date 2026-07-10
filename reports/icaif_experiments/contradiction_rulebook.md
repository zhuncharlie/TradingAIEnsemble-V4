# Contradiction Rulebook

Auto-generated from `RULE_REGISTRY` in `analysis/icaif_contradictions.py` — if this file and `contradiction_cases.csv`'s `limitation` column ever disagree, the registry is the bug, not the generator.

## cross_question

### BUY_WITH_HIGH_RISK
- **alignment**: exact_join
- **severity**: high
- **input fields**: q1.action, q2.risk_level
- **atoms used**: (none)
- **description**: Q1 BUY on (ticker, date) while another adapter's Q2 reports HIGH/EXTREME risk_level for the same (ticker, date).
- **limitation**: exact (ticker, date) join across Q1/Q2 — no approximation.

### LONG_WITH_WEAK_VALIDATION
- **alignment**: best_effort
- **severity**: medium
- **input fields**: q3.direction, q5.total_return, q5.sharpe, q5.max_drawdown, q5.win_rate
- **atoms used**: (none)
- **description**: Q3 LONG paired with a same-batch Q5 backtest classified weak/fail by classify_validation_strength.
- **limitation**: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id (upgraded to context_exact when analysis/icaif_alignment.py confirms the ticker is a member of the batch's known portfolio_universe) — never a guarantee the Q5 backtest is really about this adapter's strategy for this ticker.

### POSITIVE_SENTIMENT_BEAR_REGIME
- **alignment**: best_effort
- **severity**: low
- **input fields**: q2.sentiment_score, q4.regime
- **atoms used**: (none)
- **description**: Q2 sentiment_score > 0 paired with a same-date Q4 regime=BEAR.
- **limitation**: Q4Portfolio has no ticker field. Joined on (date, task_id) — a portfolio-level regime call is compared against per-ticker sentiment from any adapter on the same date.

### HIGH_WEIGHT_HIGH_DRAWDOWN
- **alignment**: best_effort
- **severity**: high
- **input fields**: q4.weights, q5.max_drawdown
- **atoms used**: (none)
- **description**: Q4 allocates >=high_weight_threshold to a ticker while a same-batch Q5 reports severe max_drawdown.
- **limitation**: Q4Portfolio and Q5Backtest are joined on task_id only (neither carries both ticker and date) — upgraded to universe-confirmed when the ticker is in the batch's known universe.

### ACTION_ALPHA_DIRECTION_CONFLICT
- **alignment**: exact_join
- **severity**: medium
- **input fields**: q1.action, q3.direction
- **atoms used**: (none)
- **description**: Q1 BUY vs Q3 SHORT, or Q1 SELL vs Q3 LONG, on the same (ticker, date) — same adapter or cross-adapter.
- **limitation**: exact (ticker, date) join across Q1/Q3 — no approximation.

## intra_record

### SENTIMENT_RISK_INTRA_CONFLICT
- **alignment**: single_record
- **severity**: medium
- **input fields**: q2.sentiment_score, q2.risk_level
- **atoms used**: (none)
- **description**: A single Q2 record reports sentiment_score > 0 while also reporting risk_level=EXTREME.
- **limitation**: single-record check, no join, no approximation.

### DIRECTION_RETURN_INTRA_CONFLICT
- **alignment**: single_record
- **severity**: medium
- **input fields**: q3.direction, q3.expected_return
- **atoms used**: (none)
- **description**: A single Q3 record reports direction=LONG with expected_return<0, or direction=SHORT with expected_return>0.
- **limitation**: single-record check, no join, no approximation.

### BULL_REGIME_HIGH_CASH
- **alignment**: single_record
- **severity**: medium
- **input fields**: q4.regime, q4.cash_ratio
- **atoms used**: (none)
- **description**: A single Q4 record reports regime=BULL while also holding a cash_ratio >= intra_record_high_cash_in_bull.
- **limitation**: single-record check, no join, no approximation.

### POSITIVE_RETURN_WEAK_RISK_ADJUSTED
- **alignment**: single_record
- **severity**: high
- **input fields**: q5.total_return, q5.sharpe, q5.max_drawdown
- **atoms used**: (none)
- **description**: A single Q5 record reports total_return>0 but sharpe below intra_record_weak_risk_adjusted_sharpe AND max_drawdown at or beyond intra_record_weak_risk_adjusted_drawdown.
- **limitation**: single-record check, no join, no approximation.

## evidence

### STRONG_SIGNAL_MISSING_EVIDENCE
- **alignment**: single_record
- **severity**: low
- **input fields**: q3.strength, q3.supporting_evidence
- **atoms used**: (none)
- **description**: Q3 strength >= strong_signal_strength_min with an empty/missing supporting_evidence list.
- **limitation**: single-record check, no join, no approximation.

### HEADLINE_EVIDENCE_MISMATCH
- **alignment**: single_record
- **severity**: medium
- **input fields**: q1.action, q1.reasoning, q3.direction, q3.supporting_evidence
- **atoms used**: (none)
- **description**: A bullish headline (BUY/LONG) whose own reasoning/evidence text is keyword-dominated by bearish language, or a bearish headline dominated by bullish language.
- **limitation**: keyword-heuristic text valence check (BEARISH_WORDS/BULLISH_WORDS), not semantic understanding — see icaif_metrics.py.

### SAME_DIRECTION_ZERO_ATOM_OVERLAP
- **alignment**: exact_join
- **severity**: low
- **input fields**: q1.action, q3.direction
- **atoms used**: evidence_atoms
- **description**: >=2 adapters agree on direction for the same (ticker, date) but share zero evidence-atom tags.
- **limitation**: exact (ticker, date) join; evidence atoms are a coarse 12-tag keyword vocabulary, not NLU.

### OPPOSITE_DIRECTION_ATOM_OVERLAP
- **alignment**: exact_join
- **severity**: medium
- **input fields**: q1.action, q3.direction
- **atoms used**: evidence_atoms
- **description**: Adapters disagree on direction for the same (ticker, date) yet share >=1 evidence-atom tag — they're reasoning about the same topic and still reaching opposite conclusions.
- **limitation**: exact (ticker, date) join; evidence atoms are a coarse 12-tag keyword vocabulary, not NLU.

### RISK_ATOMS_BUT_BULLISH_HEADLINE
- **alignment**: single_record
- **severity**: high
- **input fields**: q1.action, q3.direction
- **atoms used**: risk_atoms
- **description**: A record's own risk_atoms include a severe-risk tag (risk_level:EXTREME, severe_drawdown, or risk_language_in_reasoning) while its headline is still BUY/LONG.
- **limitation**: single-record check; risk_atoms themselves may draw on other Q's fields for the same (ticker, date) — see risk_atoms_from_record in icaif_metrics.py.

### VALIDATION_FAIL_BUT_STRONG_BULLISH
- **alignment**: best_effort
- **severity**: high
- **input fields**: q3.direction, q3.strength, q1.action, q1.confidence
- **atoms used**: validation_atoms
- **description**: A same-batch Q5 record's validation_atoms indicate validation_status:fail while a strong bullish Q1/Q3 signal exists (confidence/strength >= high_confidence_threshold).
- **limitation**: Q5Backtest has no ticker/date field — joined on task_id, upgraded to universe-confirmed when possible, same limitation as LONG_WITH_WEAK_VALIDATION.

## calibration

### HIGH_CONFIDENCE_POOR_CALIBRATION
- **alignment**: exact_join
- **severity**: high
- **input fields**: q1.confidence
- **atoms used**: (none)
- **description**: Q1 confidence >= high_confidence_threshold from an adapter formally flagged overconfident (Experiment 3's overconfidence_flags.csv: avg_confidence/hit_rate/sample_count gated).
- **limitation**: uses Experiment 3's overconfidence flags per (adapter, question, horizon) — no ticker/date approximation beyond that.

### CONFIDENCE_IN_POOR_CALIBRATION_BUCKET
- **alignment**: exact_join
- **severity**: high
- **input fields**: q1.confidence, q3.strength
- **atoms used**: (none)
- **description**: A record's own confidence/strength falls into a calibration bucket (adapter, question, horizon) whose calibration_error >= calibration_bucket_poor_error — catches adapters whose poor bucket has too few samples to trip the formally-gated overconfidence flag.
- **limitation**: exact join on (adapter, question, confidence bucket) against Experiment 3's calibration_table.csv; small buckets (see fig_16) make this noisier than HIGH_CONFIDENCE_POOR_CALIBRATION.

### SYSTEMATIC_OVERCONFIDENCE
- **alignment**: exact_join
- **severity**: high
- **input fields**: q1.confidence, q3.strength
- **atoms used**: (none)
- **description**: An adapter is formally flagged overconfident at >= systematic_overconfidence_min_horizons distinct horizons — every high-confidence record from that adapter is flagged.
- **limitation**: adapter-level pattern from Experiment 3's overconfidence_flags.csv, applied to every qualifying record from that adapter — not a per-record independent check.

## temporal

### TEMPORAL_FLIP_UNEXPLAINED
- **alignment**: best_effort
- **severity**: medium
- **input fields**: q1.action, q3.direction, date
- **atoms used**: (none)
- **description**: Same adapter, same ticker, flips BUY->SELL/LONG->SHORT (or reverse) within temporal_window_days, with no Q2/Q4/Q5 record in that window suggesting a regime, risk, or validation change that would explain it.
- **limitation**: best-effort: only checks whether *any* Q2/Q4/Q5 record exists in the window with a different risk_level/regime/validation_status, not that it *caused* the flip — and can't distinguish a genuine signal change from adapter-side non-determinism (see deepalpha's own same-day self-contradiction, found via ACTION_ALPHA_DIRECTION_CONFLICT).
