"""
harness/observations.py — real market-data acquisition and rebalance-schedule
resolution for the Q4 stepwise harness.

This is the ONE place in the unified harness that decides "what data is
visible at each real step" and "when is a legal rebalance point" (§三 of the
Q4 stepwise infrastructure task: the harness, not the adapter, owns test-time
advancement, per-step visible data, and the rebalance calendar).

No adapter imports here — this module only fetches real market data (via
yfinance, matching the exact per-ticker fetch pattern already used by
adapters/universal_portfolios_adapter.py::_fetch_prices and
adapters/deepalpha_adapter.py) and turns it into a real, ordered list of
harness/q4_protocol.py::MarketObservation objects plus a matching rebalance
schedule. It performs the point-in-time / causality checks required by §九:
generation_window.end <= test_window.start, and every constructed
observation's information_cutoff never exceeds its own timestamp (enforced
both here, defensively, and again downstream by
harness/execution_engine.py::enforce_causality against the adapter's actual
returned decisions).
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import pandas as pd
from pydantic import ValidationError

from harness.q4_protocol import MarketObservation, Q4CausalityViolation


def fetch_price_panel(tickers: Sequence[str], start: str, end: str) -> "pd.DataFrame":
    """Real yfinance daily close prices over [start, end] inclusive.

    Same per-ticker `yf.Ticker(t).history()` pattern already verified working
    in this repo (adapters/universal_portfolios_adapter.py::_fetch_prices) —
    `yf.download()`'s batch API was empirically found to return empty frames
    for the same valid ranges in this sandbox, so it is deliberately avoided.
    """
    import yfinance as yf

    end_inclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    series = {}
    for t in tickers:
        hist = yf.Ticker(t).history(start=start, end=end_inclusive, interval="1d")
        if hist.empty:
            raise RuntimeError(f"yfinance returned no data for {t!r} in [{start},{end}]")
        s = hist["Close"]
        s.index = s.index.tz_localize(None)
        series[t] = s
    prices = pd.DataFrame(series)
    prices = prices.dropna(how="all").ffill().dropna()
    if prices.empty:
        raise RuntimeError(f"No overlapping real trading days for {list(tickers)} in [{start},{end}]")
    return prices


def resolve_test_window_dates(
    prices: "pd.DataFrame",
    test_start: str,
    test_end: str,
) -> List[str]:
    """Real trading-day timestamps (as 'YYYY-MM-DD' strings) inside
    [test_start, test_end], drawn only from the already-fetched real price
    panel's own index — never invented or interpolated."""
    idx = prices.index
    mask = (idx >= pd.Timestamp(test_start)) & (idx <= pd.Timestamp(test_end))
    dates = [d.strftime("%Y-%m-%d") for d in idx[mask]]
    if not dates:
        raise RuntimeError(
            f"No real trading days found in test_window [{test_start},{test_end}] "
            f"within the fetched price panel's real date range "
            f"[{idx.min()},{idx.max()}]."
        )
    return dates


def resolve_rebalance_schedule(
    test_dates: Sequence[str],
    frequency: str = "daily",
) -> List[str]:
    """A subset of `test_dates` that are legal rebalance points, per the
    harness-owned rebalance calendar (§三: adapters do not choose their own
    rebalance timing). "daily" uses every real test date; "weekly"/"monthly"
    keep the first real trading day of each real ISO week/calendar month —
    still drawn only from the real observed dates, never a synthetic
    calendar that could fall on a non-trading day."""
    if frequency == "daily":
        return list(test_dates)

    if frequency not in ("weekly", "monthly"):
        raise ValueError(f"Unknown rebalance frequency: {frequency!r}")

    schedule: List[str] = []
    seen_periods = set()
    for d in test_dates:
        ts = pd.Timestamp(d)
        key = (ts.isocalendar()[0], ts.isocalendar()[1]) if frequency == "weekly" else (ts.year, ts.month)
        if key not in seen_periods:
            seen_periods.add(key)
            schedule.append(d)
    return schedule


def build_observations(
    test_dates: Sequence[str],
    universe: Sequence[str],
    rebalance_schedule: Optional[Sequence[str]] = None,
    prices: Optional["pd.DataFrame"] = None,
) -> List[MarketObservation]:
    """
    Build one real, causally-ordered MarketObservation per test date.

    information_cutoff convention: for step i>0, information_cutoff is the
    PREVIOUS real test date (i.e. the adapter may act on information known
    as of the prior close, deciding the CURRENT day's target weights before
    that day's own close is known — the standard "decide at open using data
    through yesterday's close" backtest convention). For step 0 there is no
    real prior test-window date, so information_cutoff == timestamp for that
    one row only (honestly reflecting "no real prior in-test-window signal
    exists yet" rather than fabricating an earlier date) — this exact
    convention already appears, independently derived, in
    adapters/vibe_trading_adapter.py's own causality handling.

    If `prices` is supplied, each observation's `bar` field is populated with
    that real date's real per-ticker close price (only real fetched data,
    never invented) — else `bar` is left None and the adapter is expected to
    already hold its own loaded dataset (the common case for the adapters
    migrated so far in this repo, which load their own price history inside
    q4_initialize()).
    """
    if not test_dates:
        raise ValueError("test_dates must be non-empty")
    schedule_set = set(rebalance_schedule) if rebalance_schedule is not None else None

    observations: List[MarketObservation] = []
    for i, ts in enumerate(test_dates):
        cutoff = test_dates[i - 1] if i > 0 else ts
        bar = None
        if prices is not None:
            row = prices.loc[pd.Timestamp(ts)]
            bar = {t: {"close": float(row[t])} for t in universe if t in row.index}
        try:
            obs = MarketObservation(
                step_index=i,
                timestamp=ts,
                information_cutoff=cutoff,
                universe=list(universe),
                is_rebalance_point=(schedule_set is None or ts in schedule_set),
                bar=bar,
            )
        except ValidationError as e:
            # A non-monotonic test_dates input (e.g. an out-of-order or
            # duplicated real date) can make the computed `cutoff` (the
            # PRIOR date in the input list) land after `ts` itself —
            # MarketObservation's own per-row validator catches this first.
            # Re-raised as Q4CausalityViolation so every causality failure
            # in this module surfaces through one consistent exception type.
            raise Q4CausalityViolation(
                f"Cannot build a causally valid observation at step {i} "
                f"(timestamp={ts!r}, computed cutoff={cutoff!r}) — check "
                f"test_dates is strictly increasing: {e}"
            ) from e
        observations.append(obs)

    # Defensive re-check (§九): strictly non-decreasing, no observation's
    # cutoff ever after its own timestamp — MarketObservation's own validator
    # already enforces the per-row invariant; this additionally enforces
    # cross-row monotonicity, which no single-row validator can see.
    for prev, cur in zip(observations, observations[1:]):
        if cur.timestamp < prev.timestamp:
            raise Q4CausalityViolation(
                f"Non-monotonic observation timestamps: {prev.timestamp!r} "
                f"followed by {cur.timestamp!r}"
            )
    return observations


def check_generation_test_split(generation_end: str, test_start: str) -> None:
    """§九's first required automatic check: generation_window.end <=
    test_window.start. Raises Q4CausalityViolation (a hard stop, not a log
    line) on violation — a generation window that extends into or past the
    test window would let training see future-relative-to-test data."""
    if pd.Timestamp(generation_end) > pd.Timestamp(test_start):
        raise Q4CausalityViolation(
            f"generation_window.end ({generation_end!r}) must be <= "
            f"test_window.start ({test_start!r}); a later generation end "
            f"would let training data leak into the test window."
        )
