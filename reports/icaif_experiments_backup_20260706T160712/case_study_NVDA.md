# Case Study: NVDA

## 2026-07-02

### Headline signals
- **ai_hedge_fund** (Q1): action=HOLD, confidence=0.00
- **deepalpha** (Q1): action=BUY, confidence=0.95
- **fingpt** (Q2): sentiment_score=0.40, risk_level=LOW
- **deepalpha** (Q3): direction=LONG, strength=0.09

### Secondary fields / evidence
- ai_hedge_fund reasoning: Neutral signal, no edge, hold with 0 shares.
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of +0.4512%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.95.
- deepalpha supporting_evidence: ['close_max_20 (importance=0.0789)', 'vwap (importance=0.0783)', 'ema_50 (importance=0.0470)']

### Detected contradictions
- none detected

### Fusion decision
- majority_vote: BUY
- confidence_weighted_vote: BUY
- interwoven_calibrated_fusion: **BUY** (score=0.880; risk_mult=1.00, validation_mult=0.80, contradiction_mult=1.00, boost=yes)
- Same as majority vote for this case.
- realized future return (h=1): 0.0123
