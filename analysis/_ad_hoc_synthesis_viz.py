"""
analysis/_ad_hoc_synthesis_viz.py — supplementary charts synthesizing across
all 5 experiments, for the 3 cross-cutting research questions:
  1. Does Q1-Q5 cover the 15 real adapters' capabilities?
  2. What's lost when compressing to headline-only fields?
  3. Does secondary-field interweaving surface conflicts/risk/overconfidence
     that headline-only comparison can't see?

fig_17/18/19, saved alongside the pipeline's own numbered figures.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, ".")
OUT = Path("reports/icaif_experiments")

# fig_17: adapter coverage per Q (answers Q1)
cov = pd.read_csv(OUT / "coverage_matrix.csv", index_col=0)
counts = {q: len(cov[cov[q].str.contains("observed", na=False)]) for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]}
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(counts.keys(), counts.values(), color=["steelblue"] * 5)
for i, (q, v) in enumerate(counts.items()):
    ax.text(i, v, str(v), ha="center", va="bottom")
ax.set_ylabel("Number of adapters with observed data")
ax.set_title("Q1-Q5 Coverage Across 15 Real Adapters\n(every adapter maps to Q1-Q5, none orphaned, but coverage is uneven)", fontsize=11)
ax.set_ylim(0, 9)
fig.tight_layout()
fig.savefig(OUT / "fig_17_q1q5_adapter_coverage.png", dpi=150)
plt.close(fig)

# fig_18: what headline-only comparison would miss
labels = ["Unique BUY\n(ticker,date) calls", "...hiding a HIGH/EXTREME\nrisk flag elsewhere", ""]
fig, ax = plt.subplots(1, 2, figsize=(11, 5))
ax[0].bar(["Total unique\nBUY decisions", "Hide a hidden\nhigh-risk flag"], [11, 7], color=["gray", "indianred"])
ax[0].text(0, 11, "11", ha="center", va="bottom")
ax[0].text(1, 7, "7 (64%)", ha="center", va="bottom")
ax[0].set_title("Q1 BUY calls: headline says 'buy',\nsecondary Q2 says 'high risk'")
ax[0].set_ylabel("Count")

ev = pd.read_csv(OUT / "field_coverage.csv")
sec = ev[ev["kind"] == "secondary"].sort_values("coverage_ratio")
ax[1].barh(sec["question"] + "." + sec["field"], sec["coverage_ratio"], color="seagreen")
ax[1].set_xlabel("Coverage ratio (populated / eligible records)")
ax[1].set_title("Secondary fields actually populated\n(these are what headline-only view discards)")
ax[1].set_xlim(0, 1.05)
fig.tight_layout()
fig.savefig(OUT / "fig_18_headline_compression_loss.png", dpi=150)
plt.close(fig)

# fig_19: headline-only (0 detectable) vs interwoven (129 detected)
fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(["Headline-only comparison\n(action/direction labels alone)", "Secondary-field\ninterweaving (Exp. 4)"],
       [0, 129], color=["gray", "darkorange"])
ax.text(0, 0, "0\n(no risk/validation/\ncalibration fields to check)", ha="center", va="bottom", fontsize=8)
ax.text(1, 129, "129", ha="center", va="bottom")
ax.set_ylabel("Contradiction cases detectable")
ax.set_title("What Cross-Agent Interweaving Finds\nthat Headline-Only Comparison Structurally Cannot")
fig.tight_layout()
fig.savefig(OUT / "fig_19_headline_vs_interwoven_detection.png", dpi=150)
plt.close(fig)

print("Saved fig_17, fig_18, fig_19 under", OUT)
