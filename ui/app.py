"""
ui/app.py — minimal Streamlit dashboard for the trading-ai-ensemble
comparison layer. Displays the three charts from
analysis/build_visualizations.py (imported, not duplicated) against a
selected results/{task_id}/ directory.

Run:
    conda activate deepalpha_real  # has streamlit + plotly + pandas already
    streamlit run ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.build_visualizations import (
    build_confidence_matrix,
    build_cumulative_returns,
    build_divergence_heatmap,
    load_price_history,
    load_results,
)

st.set_page_config(page_title="Trading AI Ensemble — Comparison", layout="wide")
st.title("Trading AI Ensemble — Adapter Comparison")
st.caption(
    "Same question, three frameworks. Consensus vs. divergence, side by side."
)

results_root = ROOT / "results"
task_ids = sorted(
    (p.name for p in results_root.iterdir() if p.is_dir() and any(p.glob("*__*.json"))),
    reverse=True,
) if results_root.exists() else []

if not task_ids:
    st.error(
        "No comparison results found under results/. Run "
        "`python analysis/collect_results.py --task-id <id>` first."
    )
    st.stop()

task_id = st.selectbox("Comparison run", task_ids)

df = load_results(task_id)
if df.empty:
    st.warning(f"No adapter results in results/{task_id}/.")
    st.stop()

price_path = results_root / task_id / "price_history.csv"

st.subheader("Q1 Action Divergence")
st.plotly_chart(build_divergence_heatmap(df), use_container_width=True)

st.subheader("Confidence Proxy")
st.plotly_chart(build_confidence_matrix(df), use_container_width=True)

st.subheader("Simplified Cumulative Return vs. SPY")
if price_path.exists():
    price_df = load_price_history(task_id)
    st.plotly_chart(build_cumulative_returns(df, price_df), use_container_width=True)
else:
    st.info(
        f"No price_history.csv in results/{task_id}/ — run "
        "analysis/fetch_price_history.py to enable this chart."
    )

with st.expander("Raw per-adapter results"):
    st.dataframe(df.drop(columns=["q3_evidence"], errors="ignore"))
