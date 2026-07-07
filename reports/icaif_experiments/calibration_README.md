# Calibration data availability

Total (adapter, question, ticker, date, horizon) rows attempted: 621
Rows with a realized future return: 278

## Per-horizon availability
- horizon=1: 109/207 rows have a realized future return
- horizon=5: 94/207 rows have a realized future return
- horizon=20: 75/207 rows have a realized future return

Decision dates present in results/: ['2026-05-15', '2026-05-21', '2026-05-27', '2026-06-02', '2026-06-08', '2026-07-02', '2026-07-06']
A horizon's rows stay `future_return=NaN` (marked insufficient_data downstream, never fabricated) until that many trading days have actually elapsed after the decision date — see analysis/icaif_data_loader.py:YFinanceFutureReturnProvider.