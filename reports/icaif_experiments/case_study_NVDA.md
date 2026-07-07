# Case Study: NVDA

## 2026-05-15

### Headline signals
- **deepalpha** (Q1): action=SELL, confidence=0.96
- **alphagen** (Q3): direction=NEUTRAL, strength=0.14
- **deepalpha** (Q3): direction=SHORT, strength=0.35
- **qlib** (Q3): direction=NEUTRAL, strength=0.14

### Secondary fields / evidence
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.0454 ranks 4/8 (57% percentile) across the real 8-ticker universe on 2026-05-15.", "Discovered alpha #0: 'Add(0.5,Log($volume))' (weight=-0.0763, single IC=0.0417)", "Discovered alpha #1: 'Sub(Sub(Add(-2.0,$low),5.0),Mean($close,5d))' (weight=-0.0716, single IC=-0.0204)", "Discovered alpha #2: 'Greater(Std(Add(-0.5,$vwap),40d),2.0)' (weight=0.2229, single IC=-0.0496)", "Discovered alpha #3: 'Mul(Log(Mul(30.0,Add(Sub(Greater($low,-10.0),0.01),Add($high,0.5)))),-0.01)' (weight=0.1062, single IC=0.1466)", "Discovered alpha #4: 'Mul(-1.0,$high)' (weight=0.2605, single IC=0.1377)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2081, 157 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of -1.4382%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.96.
- deepalpha supporting_evidence: ['ema_20 (importance=0.0870)', 'close_max_20 (importance=0.0853)', 'vwap (importance=0.0510)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score -0.05947 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 5/8 (43% percentile) across the real 8-ticker universe on 2026-05-15.", "Real Alpha158 factor 'RESI30': LightGBM importance=6", "Real Alpha158 factor 'STD20': LightGBM importance=5", "Real Alpha158 factor 'RSQR20': LightGBM importance=5", "Real Alpha158 factor 'BETA5': LightGBM importance=5", "Real Alpha158 factor 'RSQR5': LightGBM importance=4", "Real raw Alpha158 factor values for 'NVDA' on 2026-05-15: KMID=-0.0193, KLEN=0.0316, ROC5=0.9551, ROC20=0.8951, ROC60=0.8339, MA5=1.0005, MA20=0.9333, STD20=0.0491", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-03-04, 2025-12-29], validated on [2025-12-30, 2026-02-28], best/early-stopped iteration=16 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]

### Detected contradictions
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.96 on NVDA/2026-05-15, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_

### Fusion decision
- majority_vote: SELL
- confidence_weighted_vote: SELL
- interwoven_calibrated_fusion: **SELL** (score=-0.813; risk_mult=1.00, validation_mult=1.00, contradiction_mult=0.90, boost=yes)
- Same as majority vote for this case.
- realized future return (h=1): -0.0133

## 2026-05-21

### Headline signals
- **deepalpha** (Q1): action=SELL, confidence=0.97
- **alphagen** (Q3): direction=LONG, strength=1.00
- **deepalpha** (Q3): direction=SHORT, strength=0.31
- **qlib** (Q3): direction=NEUTRAL, strength=0.14

### Secondary fields / evidence
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.1978 ranks 1/8 (100% percentile) across the real 8-ticker universe on 2026-05-21.", "Discovered alpha #0: 'Sub(Mean(Med(Mul(Abs(Greater(-10.0,$volume)),Add($high,0.01)),10d),5d),$low)' (weight=-0.4514, single IC=0.0090)", "Discovered alpha #1: 'Std(Abs(Add(Add(Mul(1.0,$high),0.5),Med(Mean($volume,5d),1d))),10d)' (weight=0.2009, single IC=0.0891)", "Discovered alpha #2: 'Med(Add(-1.0,Mad(Mul($vwap,2.0),40d)),1d)' (weight=0.2103, single IC=-0.0337)", "Discovered alpha #3: 'Mul(Sub(EMA(Mul(Sub(-30.0,$vwap),0.5),5d),0.01),0.5)' (weight=0.1792, single IC=0.1290)", "Discovered alpha #4: 'Add(Add(Mean(Abs(Add(Add(Add($close,$volume),2.0),10.0)),5d),-5.0),0.01)' (weight=0.2825, single IC=0.0587)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2202, 130 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of -1.7141%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.97.
- deepalpha supporting_evidence: ['close_max_20 (importance=0.0806)', 'ema_20 (importance=0.0774)', 'ema_50 (importance=0.0737)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score 0.01681 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 4/8 (57% percentile) across the real 8-ticker universe on 2026-05-21.", "Real Alpha158 factor 'KLOW': LightGBM importance=2", "Real Alpha158 factor 'STD60': LightGBM importance=2", "Real Alpha158 factor 'CORD10': LightGBM importance=2", "Real Alpha158 factor 'SUMP10': LightGBM importance=2", "Real Alpha158 factor 'QTLD5': LightGBM importance=2", "Real raw Alpha158 factor values for 'NVDA' on 2026-05-21: KMID=-0.0125, KLEN=0.0426, ROC5=1.0739, ROC20=0.9095, ROC60=0.8908, MA5=1.0125, MA20=0.9767, STD20=0.0485", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-03-10, 2026-01-04], validated on [2026-01-05, 2026-03-06], best/early-stopped iteration=5 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]

### Detected contradictions
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.97 on NVDA/2026-05-21, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=SELL vs alphagen direction=LONG on NVDA/2026-05-21 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_

### Fusion decision
- majority_vote: SELL
- confidence_weighted_vote: HOLD
- interwoven_calibrated_fusion: **HOLD** (score=-0.102; risk_mult=1.00, validation_mult=1.00, contradiction_mult=0.80, boost=yes)
- **Differs from majority vote** because of the multipliers above.
- realized future return (h=1): -0.0190

## 2026-05-27

### Headline signals
- **deepalpha** (Q1): action=SELL, confidence=0.98
- **alphagen** (Q3): direction=LONG, strength=0.71
- **deepalpha** (Q3): direction=SHORT, strength=0.34
- **qlib** (Q3): direction=NEUTRAL, strength=0.43

### Secondary fields / evidence
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.1488 ranks 2/8 (86% percentile) across the real 8-ticker universe on 2026-05-27.", "Discovered alpha #0: 'Med(Sum(Sub(Std($high,20d),-5.0),1d),5d)' (weight=0.0995, single IC=-0.0471)", "Discovered alpha #1: 'Sub(0.5,$volume)' (weight=-0.1598, single IC=-0.0640)", "Discovered alpha #2: 'Add(Add(Std(Add($vwap,2.0),40d),-10.0),-0.01)' (weight=0.2107, single IC=-0.0342)", "Discovered alpha #3: 'Log(Sub(Add(Med(Mul(Mul(Add(2.0,$vwap),5.0),2.0),1d),-0.5),-1.0))' (weight=-0.1183, single IC=-0.1316)", "Discovered alpha #4: 'Mul(Sub($open,0.5),Add(Mul($open,Add(-30.0,$volume)),0.5))' (weight=-0.2286, single IC=-0.1020)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2250, 153 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of -1.9703%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.98.
- deepalpha supporting_evidence: ['close_max_20 (importance=0.0823)', 'ema_20 (importance=0.0751)', 'vwap (importance=0.0578)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score -0.01138 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 6/8 (29% percentile) across the real 8-ticker universe on 2026-05-27.", "Real Alpha158 factor 'CORD5': LightGBM importance=2", "Real Alpha158 factor 'RSQR20': LightGBM importance=2", "Real Alpha158 factor 'STD5': LightGBM importance=1", "Real Alpha158 factor 'STD10': LightGBM importance=1", "Real Alpha158 factor 'KLEN': LightGBM importance=1", "Real raw Alpha158 factor values for 'NVDA' on 2026-05-27: KMID=-0.0071, KLEN=0.0251, ROC5=1.0377, ROC20=1.0027, ROC60=0.8583, MA5=1.0214, MA20=1.0095, STD20=0.0496", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-03-16, 2026-01-10], validated on [2026-01-11, 2026-03-12], best/early-stopped iteration=3 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]

### Detected contradictions
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.98 on NVDA/2026-05-27, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=SELL vs alphagen direction=LONG on NVDA/2026-05-27 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_

### Fusion decision
- majority_vote: SELL
- confidence_weighted_vote: HOLD
- interwoven_calibrated_fusion: **HOLD** (score=-0.217; risk_mult=1.00, validation_mult=1.00, contradiction_mult=0.80, boost=yes)
- **Differs from majority vote** because of the multipliers above.
- realized future return (h=1): 0.0078

## 2026-06-02

### Headline signals
- **deepalpha** (Q1): action=SELL, confidence=0.98
- **alphagen** (Q3): direction=LONG, strength=0.71
- **deepalpha** (Q3): direction=SHORT, strength=0.39
- **qlib** (Q3): direction=LONG, strength=0.71

### Secondary fields / evidence
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.2351 ranks 2/8 (86% percentile) across the real 8-ticker universe on 2026-06-02.", "Discovered alpha #0: 'Add(Add(Std(Add($vwap,2.0),40d),-10.0),-0.01)' (weight=0.2187, single IC=-0.0325)", "Discovered alpha #1: 'Mul(Sub(EMA(Mul(Sub(-30.0,$vwap),0.5),5d),0.01),0.5)' (weight=0.2470, single IC=0.1214)", "Discovered alpha #2: 'Add(-30.0,Log(EMA($vwap,5d)))' (weight=-0.1046, single IC=-0.1307)", "Discovered alpha #3: 'Delta(Add(Mean(Add(5.0,Log($low)),1d),-2.0),10d)' (weight=-0.1029, single IC=-0.0809)", "Discovered alpha #4: 'Med(Mul(Sub(Std($high,20d),-5.0),5.0),5d)' (weight=0.0840, single IC=-0.0488)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2237, 144 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of -1.5771%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.98.
- deepalpha supporting_evidence: ['ema_20 (importance=0.0937)', 'close_max_20 (importance=0.0915)', 'vwap (importance=0.0745)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score 0.00362 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 2/8 (86% percentile) across the real 8-ticker universe on 2026-06-02.", "Real Alpha158 factor 'CORD5': LightGBM importance=3", "Real Alpha158 factor 'RSQR20': LightGBM importance=3", "Real Alpha158 factor 'CORD10': LightGBM importance=3", "Real Alpha158 factor 'RESI30': LightGBM importance=2", "Real Alpha158 factor 'KLOW': LightGBM importance=2", "Real raw Alpha158 factor values for 'NVDA' on 2026-06-02: KMID=-0.0192, KLEN=0.0481, ROC5=0.9643, ROC20=0.8908, ROC60=0.7980, MA5=0.9740, MA20=0.9782, STD20=0.0369", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-03-22, 2026-01-16], validated on [2026-01-17, 2026-03-18], best/early-stopped iteration=5 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]

### Detected contradictions
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.98 on NVDA/2026-06-02, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=SELL vs alphagen direction=LONG on NVDA/2026-06-02 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=SELL vs qlib direction=LONG on NVDA/2026-06-02 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_

### Fusion decision
- majority_vote: HOLD
- confidence_weighted_vote: HOLD
- interwoven_calibrated_fusion: **HOLD** (score=0.014; risk_mult=1.00, validation_mult=1.00, contradiction_mult=0.70, boost=yes)
- Same as majority vote for this case.
- realized future return (h=1): -0.0362

## 2026-06-08

### Headline signals
- **deepalpha** (Q1): action=SELL, confidence=0.97
- **alphagen** (Q3): direction=LONG, strength=1.00
- **deepalpha** (Q3): direction=SHORT, strength=0.36
- **qlib** (Q3): direction=NEUTRAL, strength=0.43

### Secondary fields / evidence
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.3106 ranks 1/8 (100% percentile) across the real 8-ticker universe on 2026-06-08.", "Discovered alpha #0: 'Abs(Mul(Add(Sub($volume,30.0),10.0),Sub($vwap,5.0)))' (weight=-0.4792, single IC=0.0204)", "Discovered alpha #1: 'Abs(Add(5.0,Mad($volume,10d)))' (weight=0.2095, single IC=0.0908)", "Discovered alpha #2: 'Min(Sub(Mean($low,5d),$low),5d)' (weight=0.1192, single IC=0.1268)", "Discovered alpha #3: 'Mul(Abs(Mul(Add(Mul(Mul(-5.0,Mul($volume,-30.0)),1.0),2.0),0.01)),-2.0)' (weight=-0.3488, single IC=-0.0754)", "Discovered alpha #4: 'Add(Add(Var(Mul($vwap,2.0),40d),-10.0),-0.01)' (weight=0.1515, single IC=-0.0434)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2306, 185 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of -1.7190%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.97.
- deepalpha supporting_evidence: ['ema_20 (importance=0.0871)', 'close_max_20 (importance=0.0855)', 'vwap (importance=0.0481)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score 0.00502 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 6/8 (29% percentile) across the real 8-ticker universe on 2026-06-08.", "Real Alpha158 factor 'ROC30': LightGBM importance=1", "Real Alpha158 factor 'SUMP10': LightGBM importance=1", "Real Alpha158 factor 'SUMN30': LightGBM importance=1", "Real Alpha158 factor 'CORD5': LightGBM importance=1", "Real Alpha158 factor 'IMAX20': LightGBM importance=1", "Real raw Alpha158 factor values for 'NVDA' on 2026-06-08: KMID=-0.0073, KLEN=0.0213, ROC5=1.0741, ROC20=1.0302, ROC60=0.8768, MA5=1.0252, MA20=1.0475, STD20=0.0331", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-03-28, 2026-01-22], validated on [2026-01-23, 2026-03-24], best/early-stopped iteration=1 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]

### Detected contradictions
- **LONG_WITH_WEAK_VALIDATION**: alphagen LONG on NVDA; finrl validation_status=weak (task observation_batch_day1_historical_extension__2026-06-08) _(limitation: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id only: 'this adapter's LONG signal for ticker X' is compared against 'some Q5 backtest reported in the same comparison run', which may not be the same strategy or period.)_
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.97 on NVDA/2026-06-08, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=SELL vs alphagen direction=LONG on NVDA/2026-06-08 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_

### Fusion decision
- majority_vote: SELL
- confidence_weighted_vote: HOLD
- interwoven_calibrated_fusion: **HOLD** (score=-0.061; risk_mult=1.00, validation_mult=0.65, contradiction_mult=0.70, boost=yes)
- **Differs from majority vote** because of the multipliers above.
- realized future return (h=1): -0.0022

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
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.95 on NVDA/2026-07-02, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_

### Fusion decision
- majority_vote: BUY
- confidence_weighted_vote: BUY
- interwoven_calibrated_fusion: **BUY** (score=0.792; risk_mult=1.00, validation_mult=0.80, contradiction_mult=0.90, boost=yes)
- Same as majority vote for this case.
- realized future return (h=1): 0.0037

## 2026-07-06

### Headline signals
- **ai_hedge_fund** (Q1): action=HOLD, confidence=0.16
- **deepalpha** (Q1): action=BUY, confidence=0.99
- **tradingagents** (Q1): action=BUY, confidence=0.65
- **fingpt** (Q2): sentiment_score=0.20, risk_level=HIGH
- **nofx** (Q2): sentiment_score=-0.19, risk_level=HIGH
- **prediction_arena** (Q2): sentiment_score=-0.64, risk_level=LOW
- **tradingagents** (Q2): sentiment_score=0.30, risk_level=MEDIUM
- **alphagen** (Q3): direction=LONG, strength=1.00
- **deepalpha** (Q3): direction=SHORT, strength=0.07
- **finclaw** (Q3): direction=NEUTRAL, strength=0.13
- **finrl_x** (Q3): direction=SHORT, strength=0.72
- **qlib** (Q3): direction=NEUTRAL, strength=0.14
- **rdagent** (Q3): direction=NEUTRAL, strength=0.00
- **vibe_trading** (Q3): direction=NEUTRAL, strength=0.00

### Secondary fields / evidence
- ai_hedge_fund reasoning: Neutral signal, low confidence. Hold.
- alphagen supporting_evidence: ["'NVDA' real RL-discovered ensemble alpha value 0.3885 ranks 1/8 (100% percentile) across the real 8-ticker universe on 2026-07-06.", "Discovered alpha #0: 'Sub($high,-0.5)' (weight=-0.4962, single IC=-0.1635)", "Discovered alpha #1: 'Abs(Mul(Add(Sub($volume,30.0),10.0),Sub($vwap,-1.0)))' (weight=-0.3765, single IC=0.0470)", "Discovered alpha #2: 'Mean(Mul(Mul(-0.5,Mul(Std($low,40d),-0.5)),-10.0),1d)' (weight=-0.2812, single IC=0.0703)", "Discovered alpha #3: 'Mul(Add($volume,Abs(Greater(Add($low,Add(Var($open,40d),-1.0)),0.01))),-1.0)' (weight=-0.4322, single IC=-0.1074)", "Discovered alpha #4: 'Sub(-1.0,$vwap)' (weight=-0.2078, single IC=0.1637)", "Real upstream MaskablePPO/AlphaEnv search: best ensemble IC=0.2391, 151 distinct expressions evaluated over 4000 RL timesteps (see adapter header, 'RL training budget', for why this is scoped down from upstream's own 200k-350k timestep experiments)."]
- deepalpha reasoning: XGBoost+LightGBM ensemble (upstream's SimpleEnsemble, freshly trained on NVDA's own 3y yfinance history — no pretrained Kaggle-sourced artifacts were available) predicts a 5-day forward return of +0.3165%, against a transaction-cost-based signal threshold of 0.1500%. Model agreement (1 - normalised prediction dispersion) is 0.99.
- deepalpha supporting_evidence: ['ema_20 (importance=0.0700)', 'close_max_5 (importance=0.0663)', 'close_max_20 (importance=0.0558)']
- finclaw supporting_evidence: ["Real score_stock() = 5.66/10 for 'NVDA' as of the last point-in-time trading day on/before 2026-07-06, from the real evolved winning StrategyDNA (fitness=104.18).", 'Top evolved factor weight: w_revenue_yoy = 0.1492', 'Top evolved factor weight: w_profit_yoy = 0.1098', 'Top evolved factor weight: w_support = 0.1057', 'Walk-forward OOS: 3/4 windows profitable, annual_return=43.8%, sharpe=0.52, win_rate=51.8%, trades=77 (real upstream walk-forward metrics, not reimplemented).', "Evolved over 41 real factor weights (technical + fundamental) in a 74-field DNA genome, per upstream's own code — NOT the 484 figure in upstream's marketing README, which does not match the actual executed engine (see adapter header, 'the marketed 484 factors figure...')."]
- finrl_x supporting_evidence: ['cur_ratio (importance=0.157, model=Stacking)', 'operating_margin (importance=0.142, model=Stacking)', 'pb (importance=0.123, model=Stacking)']
- qlib supporting_evidence: ["'NVDA' real LGBModel-predicted score -0.00380 (upstream's own real regression output for label 'Ref($close, -2)/Ref($close, -1) - 1') ranks 4/8 (57% percentile) across the real 8-ticker universe on 2026-07-06.", "Real Alpha158 factor 'RSQR10': LightGBM importance=3", "Real Alpha158 factor 'HIGH0': LightGBM importance=2", "Real Alpha158 factor 'CORR60': LightGBM importance=2", "Real Alpha158 factor 'CORD5': LightGBM importance=2", "Real Alpha158 factor 'BETA30': LightGBM importance=2", "Real raw Alpha158 factor values for 'NVDA' on 2026-07-06: KMID=0.0103, KLEN=0.0183, ROC5=0.9803, ROC20=1.1134, ROC60=0.9261, MA5=1.0019, MA20=1.0305, STD20=0.0303", "Real Qlib pipeline: Alpha158 (158 real pre-defined factors) over 8 real tickers, real LGBModel trained on [2025-04-25, 2026-02-19], validated on [2026-02-20, 2026-04-21], best/early-stopped iteration=3 (see adapter header, 'LightGBM training budget', for why this is scoped down from upstream's own CSI300-scale benchmark config)."]
- rdagent supporting_evidence: ["RD-Agent real LLM-proposed research hypothesis: We hypothesize that simple momentum, volatility, and volume-based factors derived from daily price and volume data can effectively predict short-term returns. Specifically, we propose three factors: 5-day price momentum (return over 5 trading days), 10-day historical volatility (standard deviation of daily returns over 10 days), and volume ratio (today's volume divided by 5-day average volume). These factors capture trend, risk, and liquidity effects, which are known to contain predictive power in equity markets.", 'Reason: Starting with simple and interpretable factors is essential to build a robust factor library. Momentum factors are well-documented in finance literature, volatility captures risk premium, and volume indicates market participation. These factors are easy to compute from the provided daily price and volume data and are likely to exhibit some predictive ability in a machine learning model like LightGBM. If successful, they provide a baseline for more complex combinations.', "Real LLM-formulated factor '5_day_price_momentum': [Momentum Factor] The 5-day price momentum is the simple return over the past 5 trading days. It captures short-term trends. [formulation: \\text{Momentum}_{t} = \\frac{\\$close_{t}}{\\$close_{t-5}} - 1]", "Real CoSTEER round did not converge on an accepted implementation within the bounded 2-round loop -- upstream's own real rejection feedback: All tasks are failed:\n- feedback01:\n  - execution: Execution succeeded without error.\nExpected output file found.\n  - return_checking: value feedback: value feedback: The source dataframe has only one column which is correct.\nThe source dataframe does not have any infinite values.\nThe output format is correct.\nThe generated dataframe is daily.\n\nshape feedback: None\n\nshape feedback: value feedback: The source dataframe has only one column which is correct.\nThe source dataframe does not have any infinite values.\nThe output format is correct.\nThe generated dataframe is daily.\n\nshape feedback: None\n  - code: critic 1: The result DataFrame’s index levels are in the order `['instrument', 'datetime']` (inherited from the source data), but the factor output specification expects `['datetime', 'instrument']` (as illustrated in the example). This mismatch may cause compatibility issues when the system processes the factor values. Consider reordering the index levels (e.g., `result = result.reorder_levels(['datetime', 'instrument'])`) before saving."]
- tradingagents reasoning: **Rating**: Overweight

**Executive Summary**: Initiate NVDA at Overweight using a disciplined 30-30-40 scaling framework: deploy 30% of the target add at current levels (~$190), 30% on any dip to $180-185, and reserve 40% for confirmed catalyst (Samsung earnings beat, Kyber supply-chain validation, or next product event). Hard stop-loss at $158 protects against thesis-disrupting breakdown. Target position 20-30% above benchmark weight. The bull's fundamental case — $130B+ revenue, 60%+ operating margins, 30x forward earnings on 50% Data Center growth, $300B+ hyperscaler commitments — commands conviction, but the bear's Kyber uncertainty and institutional/retail sentiment divergence warrant patience. Reassess within 30 days or post-catalyst.

**Investment Thesis**: The decision rests on four pillars drawn directly from the analysts' debate and the Research Manager's guidance.

**Pillar 1: Fundamentals dominate, and they are exceptional.** The Aggressive Analyst is correct that NVDA's current reality — not future fears — should carry the most weight. Revenue trajectory of $130B+, 60%+ operating margins, and $300B+ in hyperscaler commitments through 2027 represent locked-in demand that even a Kyber delay cannot meaningfully dent in the near term. At 30x forward earnings on 50% Data Center growth, the PEG ratio sits below 0.6. The Conservative Analyst's concern about "paying a premium on a cliff" is a tail-risk scenario, not a base case. The Research Manager explicitly noted that the bear's $100-120 scenario requires both growth collapse and multiple compression to 15x — conditions that show no sign of materializing.

**Pillar 2: Kyber uncertainty is real but over-weighted by the market.** The Conservative Analyst scored a genuine point: NVDA's +0.8% on a day the SOX surged 3.2% is a divergence that institutional skepticism explains better than "overreaction." A company denial is indeed a PR statement, not proof. However, the Aggressive Analyst correctly counters that SemiAnalysis cited no named sources, and the Research Manager identified the bear's reliance on a single day's price action as "the weakest part of their case." The Neutral Analyst's framing is the most persuasive: the Kyber story introduces a risk premium that demands position-sizing discipline but does not invalidate the bull thesis.

**Pillar 3: The CUDA moat and competitive dynamics are asymmetric.** The Conservative Analyst's Intel/AMD analogy was judged "clever but flawed" by the Research Manager. CUDA is not a manufacturing or architecture moat — it is a decades-deep software ecosystem with libraries, developer habits, and optimization that in-house chips (Maia, TPU, Trainium) cannot replicate for the highest-value training and complex inference workloads. The Aggressive Analyst is right: hyperscalers are "desperate to stop paying Nvidia prices" precisely because they have no viable alternative. The in-house threat is a slow-burn structural headwind over a multi-year horizon, not an imminent risk. It argues for vigilance, not avoidance.

**Pillar 4: The AAPL lesson demands respect for market signals and proximate catalysts.** The prior Underweight call on AAPL delivered +4.2% alpha against us because we over-weighted structural narratives and under-weighted time-bound catalysts and momentum signals. Applied here: Samsung earnings (July 7) is a proximate, high-impact catalyst that could validate the AI CapEx thesis and resolve Kyber uncertainty. The 30-30-40 framework directly incorporates this lesson — it avoids front-running the catalyst with excessive size (the Aggressive Analyst's error) while also avoiding paralysis that leaves us chasing a rally (the Conservative Analyst's error).

The Neutral Analyst's 30-30-40 adjustment to the Trader's original 40-30-30 plan is the right calibration. It reduces initial exposure ahead of unresolved Kyber uncertainty, maintains the dip-buying discipline, and ties the largest tranche to confirmatory evidence. The stop-loss at $158 — the 52-week low — provides a hard floor: a break below that level would signal structural damage warranting immediate exit. The Research Manager's Overweight rating, rather than Buy, correctly reflects that the bull wins the debate but the bear landed enough blows to counsel prudence in position sizing.

**Price Target**: 225.0

**Time Horizon**: 3-6 months
- vibe_trading supporting_evidence: ["DeepSeek-generated SignalEngine (upstream's real strategy-generate skill + build_llm(), single live call) implementing: Go long NVDA when its 10-day moving average crosses above its 50-day moving average, flat otherwise (trend-following momentum crossover).", 'Real backtest over 2025-12-18/2026-07-06: sharpe=0.488, trades=2, total_return=0.0493']

### Detected contradictions
- **BUY_WITH_HIGH_RISK**: deepalpha says BUY on NVDA/2026-07-06; fingpt reports risk_level=HIGH _(limitation: exact (ticker, date) join across Q1/Q2 — no approximation.)_
- **BUY_WITH_HIGH_RISK**: deepalpha says BUY on NVDA/2026-07-06; nofx reports risk_level=HIGH _(limitation: exact (ticker, date) join across Q1/Q2 — no approximation.)_
- **BUY_WITH_HIGH_RISK**: tradingagents says BUY on NVDA/2026-07-06; fingpt reports risk_level=HIGH _(limitation: exact (ticker, date) join across Q1/Q2 — no approximation.)_
- **BUY_WITH_HIGH_RISK**: tradingagents says BUY on NVDA/2026-07-06; nofx reports risk_level=HIGH _(limitation: exact (ticker, date) join across Q1/Q2 — no approximation.)_
- **LONG_WITH_WEAK_VALIDATION**: alphagen LONG on NVDA; agentictrading validation_status=weak (task observation_batch_day1__2026-07-06) _(limitation: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id only: 'this adapter's LONG signal for ticker X' is compared against 'some Q5 backtest reported in the same comparison run', which may not be the same strategy or period.)_
- **LONG_WITH_WEAK_VALIDATION**: alphagen LONG on NVDA; finrl validation_status=weak (task observation_batch_day1__2026-07-06) _(limitation: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id only: 'this adapter's LONG signal for ticker X' is compared against 'some Q5 backtest reported in the same comparison run', which may not be the same strategy or period.)_
- **LONG_WITH_WEAK_VALIDATION**: alphagen LONG on NVDA; prediction_arena validation_status=fail (task observation_batch_day1__2026-07-06) _(limitation: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id only: 'this adapter's LONG signal for ticker X' is compared against 'some Q5 backtest reported in the same comparison run', which may not be the same strategy or period.)_
- **LONG_WITH_WEAK_VALIDATION**: alphagen LONG on NVDA; vibe_trading validation_status=weak (task observation_batch_day1__2026-07-06) _(limitation: Q5Backtest has no ticker/date field in CONTRACT/schemas.py. Joined on task_id only: 'this adapter's LONG signal for ticker X' is compared against 'some Q5 backtest reported in the same comparison run', which may not be the same strategy or period.)_
- **HIGH_CONFIDENCE_POOR_CALIBRATION**: deepalpha confidence=0.99 on NVDA/2026-07-06, but is flagged overconfident historically _(limitation: uses Experiment 3's overconfidence flags per (adapter, horizon) — no ticker/date approximation beyond that.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=BUY vs deepalpha direction=SHORT on NVDA/2026-07-06 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: deepalpha action=BUY vs finrl_x direction=SHORT on NVDA/2026-07-06 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: tradingagents action=BUY vs deepalpha direction=SHORT on NVDA/2026-07-06 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_
- **ACTION_ALPHA_DIRECTION_CONFLICT**: tradingagents action=BUY vs finrl_x direction=SHORT on NVDA/2026-07-06 _(limitation: exact (ticker, date) join across Q1/Q3 — no approximation.)_

### Fusion decision
- majority_vote: BUY
- confidence_weighted_vote: BUY
- interwoven_calibrated_fusion: **HOLD** (score=0.063; risk_mult=0.60, validation_mult=0.40, contradiction_mult=0.50, boost=yes)
- **Differs from majority vote** because of the multipliers above.
- realized future return: insufficient_data (not enough trading days elapsed yet)
