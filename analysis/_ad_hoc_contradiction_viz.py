"""
analysis/_ad_hoc_contradiction_viz.py — supplementary charts for Experiment 4,
answering follow-up questions not covered by the original fig_09/fig_10:
  - fig_14: exact vs best-effort alignment split
  - fig_15: which adapters appear most often across all 129 cases
  - fig_16: calibration sample-size distribution (noise vs signal argument)

Not part of the regular analysis.icaif_experiments pipeline — ad hoc, run
once, output saved under reports/icaif_experiments/ alongside the numbered
figures the pipeline itself produces.
"""
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, ".")
OUT = Path("reports/icaif_experiments")

c = pd.read_csv(OUT / "contradiction_cases.csv")
calib = pd.read_csv(OUT / "calibration_table.csv")

EXACT_RULES = {"BUY_WITH_HIGH_RISK", "HIGH_CONFIDENCE_POOR_CALIBRATION",
               "STRONG_SIGNAL_MISSING_EVIDENCE", "ACTION_ALPHA_DIRECTION_CONFLICT"}

# fig_14: exact vs best-effort
c["alignment"] = c["flag"].apply(lambda f: "Exact join\n(Q1/Q2/Q3, has ticker+date)" if f in EXACT_RULES
                                  else "Best-effort join\n(touches Q4/Q5, task_id only)")
counts = c["alignment"].value_counts()
fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(counts.index, counts.values, color=["steelblue", "indianred"])
for i, v in enumerate(counts.values):
    ax.text(i, v, str(v), ha="center", va="bottom")
ax.set_ylabel("Number of cases")
ax.set_title("129 Contradiction Cases: Exact vs. Best-Effort Alignment")
fig.tight_layout()
fig.savefig(OUT / "fig_14_alignment_precision_split.png", dpi=150)
plt.close(fig)

# fig_15: adapter involvement frequency
cnt = Counter()
for s in c["adapters_involved"]:
    for a in str(s).split(","):
        cnt[a] += 1
adapters, vals = zip(*sorted(cnt.items(), key=lambda x: x[1]))
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(adapters, vals, color="darkorange")
for i, v in enumerate(vals):
    ax.text(v, i, f" {v}", va="center")
ax.set_xlabel("Appearances across all 129 cases")
ax.set_title("Which Adapters Are Involved in the Most Cross-Agent Contradictions")
fig.tight_layout()
fig.savefig(OUT / "fig_15_adapter_involvement_frequency.png", dpi=150)
plt.close(fig)

# fig_16: calibration bucket sample-size distribution (small-sample noise argument)
fig, ax = plt.subplots(figsize=(7, 5))
ax.hist(calib["sample_count"], bins=range(0, int(calib["sample_count"].max()) + 3, 2), color="seagreen", edgecolor="white")
ax.axvline(10, color="red", linestyle="--", label="n=10 reference line")
ax.set_xlabel("Sample count per (adapter, question, horizon, confidence bucket)")
ax.set_ylabel("Number of buckets")
ax.set_title(f"Calibration Bucket Sample-Size Distribution "
             f"(n<10 in {(calib['sample_count']<10).sum()}/{len(calib)} buckets)")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "fig_16_calibration_sample_size_distribution.png", dpi=150)
plt.close(fig)

print("Saved fig_14, fig_15, fig_16 under", OUT)
