# Case Study: SPY

## 2026-07-02

### Headline signals
- **ai_hedge_fund** (Q1): action=HOLD, confidence=1.00
- **deepalpha** (Q1): action=HOLD, confidence=0.98
- **fingpt** (Q2): sentiment_score=-0.60, risk_level=HIGH
- **deepalpha** (Q3): direction=LONG, strength=0.02

### Secondary fields / evidence
- ai_hedge_fund reasoning: No valid trade available
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on SPY's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of +0.0840%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.98.
- deepalpha supporting_evidence: ['close_max_5 (importance=0.0889)', 'bb_middle (importance=0.0802)', 'volume_mean_20 (importance=0.0631)']

### Detected contradictions
- none detected

### Fusion decision
- majority_vote: BUY
- confidence_weighted_vote: HOLD
- interwoven_calibrated_fusion: **HOLD** (score=0.004; risk_mult=0.60, validation_mult=0.80, contradiction_mult=1.00, boost=no)
- **Differs from majority vote** because of the multipliers above.
- realized future return (h=1): 0.0082
