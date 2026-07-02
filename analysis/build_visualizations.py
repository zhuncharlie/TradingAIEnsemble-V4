"""
analysis/build_visualizations.py — build the 3 comparison charts (divergence
heatmap, cumulative returns vs SPY, confidence matrix) from collected
adapter results. Chart-building functions are imported by ui/app.py so the
Streamlit dashboard and the static-export path share one implementation.

Env: run in any env with pandas + plotly + kaleido (deepalpha_real has all
three already; no adapter-specific dependency needed here since this only
reads the JSON results, it never imports an adapter).

Usage:
    python analysis/build_visualizations.py --task-id comparison_2026-07-02
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]

ACTION_COLOR = {"BUY": "#2ca02c", "SELL": "#d62728", "HOLD": "#bdbdbd", "N/A": "#f0f0f0"}
ACTION_NUM = {"BUY": 1, "SELL": -1, "HOLD": 0, "N/A": None}

ADAPTER_ORDER = ["ai_hedge_fund", "fingpt", "deepalpha"]


def load_results(task_id: str, results_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load every {adapter}__{ticker}.json in results/{task_id}/ into one tidy
    DataFrame with a unified `implied_action` and `confidence_proxy` per row.

    implied_action derivation:
      - ai_hedge_fund, deepalpha: native Q1 action.
      - fingpt (Q2-only, no native Q1): derived from sentiment_score
        (>0.2 -> BUY, <-0.2 -> SELL, else HOLD) — marked `action_is_derived`.
      - ai_hedge_fund x {BTC-USD, SPY}: forced to N/A. Its data source
        (financialdatasets.ai) apparently doesn't cover crypto OR index
        ETFs — narrower coverage than expected (individual equities only).
        Detected generically, not hardcoded per-ticker: any result whose
        Q1 reasoning is literally "No valid trade available" is treated as
        a dead fallback (confirmed by ~2s latency vs ~14s for a real
        LLM-backed decision) rather than a genuine confidence=1.0 signal,
        which would otherwise be badly misleading in the confidence matrix.

    confidence_proxy: ai_hedge_fund/deepalpha -> Q1 confidence;
      fingpt -> abs(sentiment_score) (its only available conviction proxy).
    """
    results_dir = results_dir or (ROOT / "results" / task_id)
    rows = []

    for path in sorted(results_dir.glob("*__*.json")):
        adapter_name, ticker = path.stem.split("__")
        payload = json.loads(path.read_text(encoding="utf-8"))

        if "error" in payload:
            rows.append({
                "adapter": adapter_name, "ticker": ticker,
                "implied_action": "N/A", "action_is_derived": False,
                "confidence_proxy": None, "error": payload["error"],
            })
            continue

        q1 = payload.get("q1")
        q2 = payload.get("q2")
        q3 = payload.get("q3")

        is_dead_fallback = (
            adapter_name == "ai_hedge_fund"
            and q1 is not None
            and q1.get("reasoning") == "No valid trade available"
        )

        if is_dead_fallback:
            action, derived, conf = "N/A", False, None
        elif q1 is not None:
            action, derived, conf = q1["action"], False, q1["confidence"]
        elif q2 is not None:
            score = q2["sentiment_score"]
            action = "BUY" if score > 0.2 else "SELL" if score < -0.2 else "HOLD"
            derived, conf = True, abs(score)
        else:
            action, derived, conf = "N/A", False, None

        rows.append({
            "adapter": adapter_name,
            "ticker": ticker,
            "implied_action": action,
            "action_is_derived": derived,
            "confidence_proxy": conf,
            "q1_action": q1["action"] if q1 else None,
            "q1_confidence": q1["confidence"] if q1 else None,
            "q1_reasoning": q1["reasoning"] if q1 else None,
            "q2_sentiment_score": q2["sentiment_score"] if q2 else None,
            "q2_risk_level": q2["risk_level"] if q2 else None,
            "q3_direction": q3["direction"] if q3 else None,
            "q3_strength": q3["strength"] if q3 else None,
            "q3_expected_return": q3["expected_return"] if q3 else None,
            "q3_evidence": q3["supporting_evidence"] if q3 else None,
            "error": None,
        })

    return pd.DataFrame(rows)


def load_price_history(task_id: str, results_dir: Optional[Path] = None) -> pd.DataFrame:
    results_dir = results_dir or (ROOT / "results" / task_id)
    df = pd.read_csv(results_dir / "price_history.csv", parse_dates=["Date"])
    return df


def build_divergence_heatmap(df: pd.DataFrame) -> go.Figure:
    tickers = sorted(df["ticker"].unique())
    pivot = df.pivot(index="ticker", columns="adapter", values="implied_action").reindex(
        index=tickers, columns=ADAPTER_ORDER
    )
    z = pivot.map(lambda a: ACTION_NUM.get(a) if pd.notna(a) else None)
    text = pivot.fillna("N/A")

    derived_lookup = df.set_index(["ticker", "adapter"])["action_is_derived"].to_dict()
    hover = []
    for ticker in pivot.index:
        row = []
        for adapter in pivot.columns:
            action = pivot.loc[ticker, adapter]
            derived = derived_lookup.get((ticker, adapter), False)
            note = " (derived from Q2 sentiment — fingpt has no native Q1)" if derived else ""
            row.append(f"{adapter} / {ticker}: {action}{note}")
        hover.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z.values, x=pivot.columns, y=pivot.index, text=text.values,
        texttemplate="%{text}", hovertext=hover, hoverinfo="text",
        colorscale=[[0, "#d62728"], [0.5, "#bdbdbd"], [1, "#2ca02c"]],
        zmin=-1, zmax=1, showscale=False,
    ))
    fig.update_layout(
        title="Q1 Action Divergence — Consensus vs. Disagreement Across Frameworks<br>"
              "<sup>fingpt's action is derived from Q2 sentiment (no native Q1); "
              "ai_hedge_fund/{BTC-USD,SPY} is N/A (data source lacks crypto/ETF coverage)</sup>",
        xaxis_title="Adapter", yaxis_title="Ticker",
        template="plotly_white",
    )
    return fig


def build_confidence_matrix(df: pd.DataFrame) -> go.Figure:
    tickers = sorted(df["ticker"].unique())
    pivot = df.pivot(index="ticker", columns="adapter", values="confidence_proxy").reindex(
        index=tickers, columns=ADAPTER_ORDER
    )
    text = pivot.map(lambda v: f"{v:.2f}" if pd.notna(v) else "N/A")

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index, text=text.values,
        texttemplate="%{text}", colorscale="Blues", zmin=0, zmax=1,
        colorbar=dict(title="Confidence"),
    ))
    fig.update_layout(
        title="Confidence Proxy per Adapter × Ticker<br>"
              "<sup>ai_hedge_fund/deepalpha: Q1 confidence — fingpt: |sentiment_score| "
              "(no native confidence field)</sup>",
        xaxis_title="Adapter", yaxis_title="Ticker",
        template="plotly_white",
    )
    return fig


def build_cumulative_returns(df: pd.DataFrame, price_df: pd.DataFrame) -> go.Figure:
    """
    SIMPLIFIED BACKTEST, not a walk-forward daily re-decision backtest: each
    adapter's single point-in-time Q1 action (as of the collection date) is
    held as a STATIC position (+1 long / -1 short / 0 flat) across the
    entire 3-month price window, equal-weighted across tickers. Re-querying
    every adapter for every historical date was not practical here —
    ai_hedge_fund makes a real paid LLM call per query and fingpt reloads a
    6B-parameter model per call. This chart shows "what if you'd taken and
    held today's signal for the last 3 months", not a realistic historical
    P&L. See DECISIONS.md.
    """
    price = price_df.pivot(index="Date", columns="Ticker", values="Close").sort_index()
    daily_returns = price.pct_change(fill_method=None).fillna(0.0)

    fig = go.Figure()

    for adapter in ADAPTER_ORDER:
        sub = df[df["adapter"] == adapter].set_index("ticker")["implied_action"]
        positions = sub.map(ACTION_NUM.get)
        tickers = [t for t in positions.index if t in daily_returns.columns and pd.notna(positions[t])]
        if not tickers:
            continue
        weighted = sum(daily_returns[t] * positions[t] for t in tickers) / len(tickers)
        cumulative = (1 + weighted).cumprod() - 1
        fig.add_trace(go.Scatter(
            x=cumulative.index, y=cumulative.values * 100,
            mode="lines", name=adapter,
        ))

    if "SPY" in daily_returns.columns:
        spy_cum = (1 + daily_returns["SPY"]).cumprod() - 1
        fig.add_trace(go.Scatter(
            x=spy_cum.index, y=spy_cum.values * 100,
            mode="lines", name="SPY (buy & hold)",
            line=dict(dash="dash", color="black"),
        ))

    fig.update_layout(
        title="Simplified Cumulative Return: Today's Signal Held Static Over 3 Months<br>"
              "<sup>NOT a walk-forward backtest — a single current decision per adapter, "
              "held long/short/flat for the whole window. See DECISIONS.md.</sup>",
        xaxis_title="Date", yaxis_title="Cumulative Return (%)",
        template="plotly_white", hovermode="x unified",
    )
    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--out-dir", default=str(ROOT / "plots"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.task_id)
    price_df = load_price_history(args.task_id)

    charts = {
        "divergence_heatmap": build_divergence_heatmap(df),
        "confidence_matrix": build_confidence_matrix(df),
        "cumulative_returns": build_cumulative_returns(df, price_df),
    }

    for name, fig in charts.items():
        html_path = out_dir / f"{name}.html"
        png_path = out_dir / f"{name}.png"
        fig.write_html(str(html_path))
        fig.write_image(str(png_path), width=1000, height=600, scale=2)
        print(f"Saved {html_path} and {png_path}")


if __name__ == "__main__":
    main()
