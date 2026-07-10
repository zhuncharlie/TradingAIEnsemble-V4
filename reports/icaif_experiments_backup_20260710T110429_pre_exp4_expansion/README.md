# ICAIF Experiment Suite — Outputs

## How to rerun

```
conda run -n deepalpha_real python -m analysis.icaif_experiments \
    --results-dir results --adapters-dir adapters \
    --out reports/icaif_experiments --horizons 1,5,20 --threshold-bps 20.0
```

`deepalpha_real` is used because it is the one conda env in this repo that
already carries pandas + matplotlib + yfinance (see analysis/build_visualizations.py's
own docstring) — this suite never imports an adapter module, so no other
adapter-specific env is needed.

## What data was used

- Adapters discovered by static source scan of `adapters/*.py`: **15**
  (excludes `example_stub_adapter.py` and `vendor/`; count is not hard-coded,
  see `adapter_inventory.csv`).
- Result records discovered under `results/**/*.json`: **264**
  (0 of which are error payloads from a failed `adapter.run()`).
- Forward/future prices: fetched live via yfinance on each run and cached under
  `data/cache/prices/{ticker}.csv`; never fabricated when unavailable.

## Where outputs are saved

All CSVs and PNGs land flat in `reports/icaif_experiments/`, named `fig_NN_*.png` / `*.csv`
per the experiment they belong to (1: coverage, 2: secondary-field value,
3: calibration, 4: contradictions, 5: fusion ablation), plus:

- `calibration_README.md` — which horizons had realized returns and why others didn't
- `case_study_NVDA.md`, `case_study_SPY.md`
- `PAPER_FINDINGS.md` — the narrative synthesis

## What was skipped because of missing data

See `calibration_README.md` for the exact per-horizon breakdown. In short:
any figure/table whose caption or first row says `insufficient_data` means
there were not yet enough realized trading days since the recorded decision
date(s) to compute a forward return at that horizon — this is expected the
first time this pipeline is run against a fresh comparison batch, and will
fill in as time passes and/or more `analysis/collect_results.py` runs are
added.
