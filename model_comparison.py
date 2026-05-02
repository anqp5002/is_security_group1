"""
model_comparison.py — Aggregate and visualise results from all 5 ML models.

Loads pre-trained models from demo/ folder and compares performance:
  - Logistic Regression, Naive Bayes, SVM (TV3 models)
  - KNN, Random Forest (TV4 models - DEPLOYED)

Also displays training results from each member's notebooks:
  TV3 (N23DCCN001_DangKimAn): Logistic Regression, Naive Bayes, SVM
  TV4 (N23DCCN138_PhamQuocAn): KNN, Random Forest

Run:
    python model_comparison.py

Outputs (saved to outputs/comparison/):
  - comparison_table.csv        Raw metrics table
  - bar_accuracy.png            Accuracy bar chart
  - bar_all_metrics.png         Grouped bar chart (Acc / Prec / Rec / F1)
  - radar_chart.png             Radar / spider chart across all metrics
"""

import os
import sys
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings

warnings.filterwarnings("ignore")

# Fix encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUTPUT_DIR = os.path.join("outputs", "comparison")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "=" * 90)
print("  MODEL COMPARISON RESULTS")
print("=" * 90 + "\n")

# ---------------------------------------------------------------------------
# 1. Training Results from TV3 & TV4
# ---------------------------------------------------------------------------

RESULTS = [
        {
            "Model":     "Logistic Regression",
            "Member":    "TV3",
            "Accuracy":  0.93,
            "Precision": None,
            "Recall":    None,
            "F1":        0.71,   # macro
            "Note":      "Training: Smoothed class weights, outlier clipping",
        },
        {
            "Model":     "Naive Bayes",
            "Member":    "TV3",
            "Accuracy":  0.83,
            "Precision": None,
            "Recall":    None,
            "F1":        0.60,   # macro
            "Note":      "Training: CategoricalNB with equal-width binning",
        },
        {
            "Model":     "SVM (Nystroem)",
            "Member":    "TV3",
            "Accuracy":  0.97,
            "Precision": None,
            "Recall":    None,
            "F1":        0.64,   # macro
            "Note":      "Training: Nystroem RBF approximation for scalability",
        },
        {
            "Model":     "KNN (K=5)",
            "Member":    "TV4",
            "Accuracy":  0.9820,
            "Precision": 0.9820,
            "Recall":    0.9820,
            "F1":        0.9820,  # weighted
            "Note":      "Training: Weak on PortScan (84.8%) and Bot (62.4%)",
        },
        {
            "Model":     "Random Forest",
            "Member":    "TV4",
            "Accuracy":  0.9759,
            "Precision": 0.9759,
            "Recall":    0.9759,
            "F1":        0.9759,  # weighted
            "Note":      "Training: DEPLOYED — PortScan 99.9%, Bot 92.3%",
        },
    ]

print("Using TRAINING RESULTS from TV3 & TV4\n")

df = pd.DataFrame(RESULTS)
df_sorted = df.sort_values("Accuracy", ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 2. Print comparison table
# ---------------------------------------------------------------------------
print("=" * 90)
print("  MODEL COMPARISON — CIC-IDS2017 Network Intrusion Detection")
print("=" * 90)

display_cols = ["Model", "Accuracy", "Precision", "Recall", "F1", "Note"]
col_widths   = [22, 10, 10, 8, 8, 45]
header = "".join(f"{c:<{w}}" for c, w in zip(display_cols, col_widths))
print(header)
print("-" * 90)

for _, row in df_sorted.iterrows():
    def fmt(v):
        return f"{v:.4f}" if isinstance(v, float) else "  N/A  "

    line = (
        f"{row['Model']:<22}"
        f"{fmt(row['Accuracy']):<10}"
        f"{fmt(row['Precision']):<10}"
        f"{fmt(row['Recall']):<8}"
        f"{fmt(row['F1']):<8}"
        f"{row['Note']:<45}"
    )
    print(line)

print("=" * 90)
print("Note: TV3 F1 = macro average; TV4 Precision/Recall/F1 = weighted average.\n")

# Save CSV
csv_path = os.path.join(OUTPUT_DIR, "comparison_table.csv")
df_sorted.to_csv(csv_path, index=False)
print(f"Saved: {csv_path}")

# ---------------------------------------------------------------------------
# 3. Bar chart — Accuracy only
# ---------------------------------------------------------------------------
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]
model_names = df_sorted["Model"].tolist()
accuracy = df_sorted["Accuracy"].tolist()

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(model_names, accuracy, color=PALETTE, edgecolor="black", linewidth=0.6)

for bar, acc in zip(bars, accuracy):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.004,
        f"{acc:.2%}",
        ha="center", va="bottom",
        fontsize=11, fontweight="bold",
    )

# Highlight best model
best_idx = accuracy.index(max(accuracy))
bars[best_idx].set_edgecolor("gold")
bars[best_idx].set_linewidth(2.5)

ax.set_title("Model Accuracy Comparison — CIC-IDS2017", fontsize=14, fontweight="bold")
ax.set_ylabel("Accuracy", fontsize=12)
ax.set_ylim(max(0, min(accuracy) - 0.08), 1.05)
ax.set_xticklabels(model_names, rotation=25, ha="right", fontsize=11)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
ax.grid(axis="y", linestyle="--", alpha=0.4)

deploy_patch = mpatches.Patch(facecolor="white", edgecolor="gold", linewidth=2,
                               label="Best accuracy (gold border)")
ax.legend(handles=[deploy_patch], loc="lower right", fontsize=10)

plt.tight_layout()
path = os.path.join(OUTPUT_DIR, "bar_accuracy.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {path}")

# ---------------------------------------------------------------------------
# 4. Grouped bar chart — Accuracy / F1 (and Precision / Recall where available)
# ---------------------------------------------------------------------------
metrics      = ["Accuracy", "F1"]
metric_labels = ["Accuracy", "F1-Score"]

x     = np.arange(len(model_names))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
    values = [
        row[metric] if row[metric] is not None else 0
        for _, row in df_sorted.iterrows()
    ]
    offset = (i - (len(metrics) - 1) / 2) * width
    rects = ax.bar(x + offset, values, width, label=label,
                   color=PALETTE[i], edgecolor="black", linewidth=0.5)
    for rect, val in zip(rects, values):
        if val > 0:
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_height() + 0.005,
                f"{val:.2f}",
                ha="center", va="bottom", fontsize=8,
            )

ax.set_title("Accuracy vs F1-Score per Model — CIC-IDS2017", fontsize=14, fontweight="bold")
ax.set_ylabel("Score", fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=25, ha="right", fontsize=10)
ax.set_ylim(0, 1.12)
ax.legend(fontsize=11)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.text(0.98, 0.02,
        "TV3 F1 = macro avg\nTV4 F1 = weighted avg",
        transform=ax.transAxes, fontsize=8,
        ha="right", va="bottom", color="grey",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

plt.tight_layout()
path = os.path.join(OUTPUT_DIR, "bar_all_metrics.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {path}")

# ---------------------------------------------------------------------------
# 5. Radar / Spider chart — Accuracy & F1 across models
# ---------------------------------------------------------------------------
# Only use models that have both metrics
radar_data = df_sorted[["Model", "Accuracy", "F1"]].dropna().copy()

categories = ["Accuracy", "F1-Score"]
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]  # close the loop

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

for idx, (_, row) in enumerate(radar_data.iterrows()):
    values = [row["Accuracy"], row["F1"]]
    values += values[:1]
    ax.plot(angles, values, linewidth=2, linestyle="solid",
            label=row["Model"], color=PALETTE[idx % len(PALETTE)])
    ax.fill(angles, values, alpha=0.08, color=PALETTE[idx % len(PALETTE)])

ax.set_thetagrids(np.degrees(angles[:-1]), categories, fontsize=12)
ax.set_ylim(0.5, 1.05)
ax.set_title("Model Performance Radar — CIC-IDS2017",
             fontsize=13, fontweight="bold", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=9)
ax.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
path = os.path.join(OUTPUT_DIR, "radar_chart.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {path}")

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
best_row = df_sorted.iloc[0]
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Best overall accuracy : {best_row['Model']} ({best_row['Accuracy']:.2%})")
print(f"Deployed model        : Random Forest")
print(f"Reason for deployment : Highest attack-class recall")
print(f"                        PortScan: 99.9%  |  Bot: 92.3%")
print(f"Output charts saved in: {os.path.abspath(OUTPUT_DIR)}/")
