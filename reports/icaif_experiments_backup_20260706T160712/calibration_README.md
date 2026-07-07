# Calibration data availability

Total (adapter, question, ticker, date, horizon) rows attempted: 45
Rows with a realized future return: 15

## Per-horizon availability
- horizon=1: 15/15 rows have a realized future return
- horizon=5: 0/15 rows have a realized future return
- horizon=20: 0/15 rows have a realized future return

Decision dates present in results/: ['2026-07-02']
A horizon's rows stay `future_return=NaN` (marked insufficient_data downstream, never fabricated) until that many trading days have actually elapsed after the decision date — see analysis/icaif_data_loader.py:YFinanceFutureReturnProvider.