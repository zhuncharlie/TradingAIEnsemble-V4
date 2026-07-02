"""
analysis/fetch_price_history.py — real yfinance OHLCV for the comparison
tickers over the past 3 months. Used by build_visualizations.py for the
cumulative-returns-vs-SPY chart. No adapter dependencies — just yfinance.

Usage:
    python analysis/fetch_price_history.py --out results/comparison_2026-07-02/price_history.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = ["AAPL", "NVDA", "TSLA", "BTC-USD", "SPY"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--period", default="3mo")
    parser.add_argument("--tickers", nargs="*", default=TICKERS)
    args = parser.parse_args()

    frames = []
    for ticker in args.tickers:
        hist = yf.Ticker(ticker).history(period=args.period, interval="1d")
        if hist.empty:
            print(f"WARNING: no history for {ticker}")
            continue
        hist = hist.reset_index()[["Date", "Close"]]
        hist["Ticker"] = ticker
        hist["Date"] = pd.to_datetime(hist["Date"]).dt.tz_localize(None)
        frames.append(hist)
        print(f"OK {ticker}: {len(hist)} rows, {hist['Date'].min().date()} -> {hist['Date'].max().date()}")

    df = pd.concat(frames, ignore_index=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
