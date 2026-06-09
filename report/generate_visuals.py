"""
Generate and save all EDA visualizations for the Interim 1 report.
Run from the fraud-detection/ root.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

OUT = Path("report/visuals")
OUT.mkdir(exist_ok=True)

PALETTE = {"legit": "#4C9BE8", "fraud": "#E8534C"}
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight",
                     "savefig.facecolor": "white"})

fraud = pd.read_csv("data/processed/fraud_data_clean.csv")
cc    = pd.read_csv("data/processed/creditcard_clean.csv")

# ─────────────────────────────────────────────────────────────
# FIG 1 – Class imbalance side by side
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

for ax, df, col, title, labels in [
    (axes[0], fraud, "class",  "E-Commerce Fraud Data",   ["Legit\n(90.64%)", "Fraud\n(9.36%)"]),
    (axes[1], cc,    "Class",  "Credit Card Fraud Data",  ["Legit\n(99.83%)", "Fraud\n(0.17%)"]),
]:
    counts = df[col].value_counts().sort_index()
    bars = ax.bar(labels, counts.values,
                  color=[PALETTE["legit"], PALETTE["fraud"]], width=0.5, edgecolor="white")
    ax.set_title(title, fontweight="bold", pad=10)
    ax.set_ylabel("Transaction Count")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + counts.values.max()*0.01,
                f"{v:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylim(0, counts.values.max() * 1.12)
    ax.tick_params(axis="x", labelsize=11)

fig.suptitle("Class Imbalance — Both Datasets", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig1_class_imbalance.png")
plt.close()
print("fig1 done")

# ─────────────────────────────────────────────────────────────
# FIG 2 – E-commerce: distributions of purchase_value and age
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

for ax, col, xlabel, bins in [
    (axes[0], "purchase_value", "Purchase Value ($)", 60),
    (axes[1], "age",            "User Age",            30),
]:
    for cls, label, color in [(0, "Legitimate", PALETTE["legit"]),
                               (1, "Fraud",      PALETTE["fraud"])]:
        ax.hist(fraud[fraud["class"] == cls][col], bins=bins,
                alpha=0.6, color=color, label=label, edgecolor="none", density=True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density")
    ax.set_title(f"Distribution of {xlabel}", fontweight="bold")
    ax.legend()

fig.suptitle("E-Commerce: Univariate Distributions by Class", fontsize=14,
             fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig2_ecomm_distributions.png")
plt.close()
print("fig2 done")

# ─────────────────────────────────────────────────────────────
# FIG 3 – Fraud rate by source / browser / sex
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(13, 4))

for ax, col in zip(axes, ["source", "browser", "sex"]):
    rates = fraud.groupby(col)["class"].mean().sort_values(ascending=False) * 100
    colors = [PALETTE["fraud"] if r == rates.max() else "#B0C4DE" for r in rates]
    bars = ax.bar(rates.index, rates.values, color=colors, edgecolor="white")
    ax.set_title(f"Fraud Rate by {col.title()}", fontweight="bold")
    ax.set_ylabel("Fraud Rate (%)")
    ax.set_ylim(0, rates.max() * 1.25)
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(bars, rates.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f"{v:.1f}%", ha="center", va="bottom", fontsize=9)

fig.suptitle("E-Commerce: Fraud Rate by Categorical Features", fontsize=14,
             fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig3_fraud_by_category.png")
plt.close()
print("fig3 done")

# ─────────────────────────────────────────────────────────────
# FIG 4 – Fraud rate by time_since_signup bucket
# ─────────────────────────────────────────────────────────────
fraud["signup_bucket"] = pd.cut(
    fraud["time_since_signup"],
    bins=[0, 1, 6, 24, 168, np.inf],
    labels=["<1h", "1–6h", "6–24h", "1–7d", ">7d"]
)
rates = fraud.groupby("signup_bucket", observed=True)["class"].mean() * 100

fig, ax = plt.subplots(figsize=(8, 4.5))
colors = [PALETTE["fraud"] if b == "<1h" else "#B0C4DE" for b in rates.index]
bars = ax.bar(rates.index.astype(str), rates.values, color=colors, edgecolor="white", width=0.6)
ax.set_xlabel("Time Since Signup", fontsize=12)
ax.set_ylabel("Fraud Rate (%)", fontsize=12)
ax.set_title("Fraud Rate by Time Since Account Signup", fontweight="bold", fontsize=13)
ax.set_ylim(0, 115)

for bar, v in zip(bars, rates.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{v:.1f}%", ha="center", va="bottom", fontweight="bold",
            color=PALETTE["fraud"] if v > 50 else "black", fontsize=11)

ax.annotate("99.5% of transactions\nwithin 1 hour are FRAUD",
            xy=(0, 99.5), xytext=(1.5, 85),
            arrowprops=dict(arrowstyle="->", color=PALETTE["fraud"], lw=2),
            color=PALETTE["fraud"], fontweight="bold", fontsize=10)

fig.tight_layout()
fig.savefig(OUT / "fig4_fraud_by_signup_time.png")
plt.close()
print("fig4 done")

# ─────────────────────────────────────────────────────────────
# FIG 5 – Top 15 countries by fraud rate
# ─────────────────────────────────────────────────────────────
cstats = (fraud.groupby("country")
               .agg(total=("class","count"), fraud=("class","sum"))
               .assign(rate=lambda x: x["fraud"]/x["total"]*100))
top = cstats[cstats["total"] >= 50].sort_values("rate", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(11, 5))
colors = [PALETTE["fraud"] if i < 5 else "#B0C4DE" for i in range(len(top))]
bars = ax.barh(top.index[::-1], top["rate"].values[::-1], color=colors[::-1], edgecolor="white")
ax.set_xlabel("Fraud Rate (%)", fontsize=12)
ax.set_title("Top 15 Countries by Fraud Rate (min 50 transactions)", fontweight="bold", fontsize=13)
ax.axvline(fraud["class"].mean()*100, color="navy", linestyle="--", linewidth=1.5,
           label=f"Global avg ({fraud['class'].mean()*100:.1f}%)")
for bar, v in zip(bars, top["rate"].values[::-1]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}%", va="center", fontsize=9)
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "fig5_fraud_by_country.png")
plt.close()
print("fig5 done")

# ─────────────────────────────────────────────────────────────
# FIG 6 – Credit card: Amount distribution by class
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

# Left: overlapping histograms (log scale on x)
for cls, label, color in [(0,"Legitimate",PALETTE["legit"]),(1,"Fraud",PALETTE["fraud"])]:
    data = cc[cc["Class"]==cls]["Amount"]
    data = data[data > 0]
    axes[0].hist(np.log1p(data), bins=60, alpha=0.55, color=color, label=label,
                 edgecolor="none", density=True)
axes[0].set_xlabel("log(Amount + 1)")
axes[0].set_ylabel("Density")
axes[0].set_title("Transaction Amount Distribution\n(log scale)", fontweight="bold")
axes[0].legend()

# Right: boxplot
cc_plot = cc[["Amount","Class"]].copy()
cc_plot["Class_Label"] = cc_plot["Class"].map({0:"Legitimate",1:"Fraud"})
sns.boxplot(data=cc_plot, x="Class_Label", y="Amount", ax=axes[1],
            palette={"Legitimate": PALETTE["legit"], "Fraud": PALETTE["fraud"]},
            showfliers=False)
axes[1].set_title("Amount by Class (outliers removed)", fontweight="bold")
axes[1].set_xlabel("")
axes[1].set_ylabel("Amount ($)")

fig.suptitle("Credit Card: Transaction Amount Analysis", fontsize=14,
             fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig6_cc_amount.png")
plt.close()
print("fig6 done")

# ─────────────────────────────────────────────────────────────
# FIG 7 – Credit card: Time distribution
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

for cls, label, color in [(0,"Legitimate",PALETTE["legit"]),(1,"Fraud",PALETTE["fraud"])]:
    axes[0].hist(cc[cc["Class"]==cls]["Time"]/3600, bins=60, alpha=0.55,
                 color=color, label=label, edgecolor="none", density=True)
axes[0].set_xlabel("Time (hours since first transaction)")
axes[0].set_ylabel("Density")
axes[0].set_title("Time Distribution by Class", fontweight="bold")
axes[0].legend()

# Hourly transaction density
cc["hour"] = (cc["Time"] / 3600).astype(int) % 48
hourly = cc.groupby(["hour","Class"]).size().unstack(fill_value=0)
hourly.columns = ["Legitimate","Fraud"]
hourly["Fraud_scaled"] = hourly["Fraud"] * (hourly["Legitimate"].max() / hourly["Fraud"].max())
axes[1].fill_between(hourly.index, hourly["Legitimate"], alpha=0.4,
                     color=PALETTE["legit"], label="Legitimate (left axis)")
ax2 = axes[1].twinx()
ax2.plot(hourly.index, hourly["Fraud"], color=PALETTE["fraud"],
         linewidth=2, label="Fraud (right axis)")
ax2.set_ylabel("Fraud Count", color=PALETTE["fraud"])
axes[1].set_xlabel("Hour Bucket (0–47)")
axes[1].set_ylabel("Legitimate Count")
axes[1].set_title("Hourly Transaction Volume", fontweight="bold")

fig.suptitle("Credit Card: Temporal Patterns", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig7_cc_time.png")
plt.close()
print("fig7 done")

# ─────────────────────────────────────────────────────────────
# FIG 8 – Credit card: PCA feature correlations
# ─────────────────────────────────────────────────────────────
v_cols = [f"V{i}" for i in range(1, 29)]
corrs = cc[v_cols + ["Amount","Time"]].corrwith(cc["Class"]).sort_values()

fig, ax = plt.subplots(figsize=(10, 7))
colors = [PALETTE["fraud"] if v > 0 else PALETTE["legit"] for v in corrs.values]
bars = ax.barh(corrs.index, corrs.values, color=colors, edgecolor="white")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Pearson Correlation with Fraud Label", fontsize=12)
ax.set_title("Credit Card: Feature Correlation with Fraud (Class=1)", fontweight="bold", fontsize=13)

legend_patches = [
    mpatches.Patch(color=PALETTE["fraud"], label="Positive correlation (→ fraud)"),
    mpatches.Patch(color=PALETTE["legit"], label="Negative correlation (→ legit)"),
]
ax.legend(handles=legend_patches)
for bar, v in zip(bars, corrs.values):
    if abs(v) >= 0.15:
        ax.text(v + (0.003 if v >= 0 else -0.003),
                bar.get_y() + bar.get_height()/2,
                f"{v:.3f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig8_cc_correlations.png")
plt.close()
print("fig8 done")

# ─────────────────────────────────────────────────────────────
# FIG 9 – Credit card: missing values heatmap + duplicate check
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Null heatmap (no nulls, but show it)
nulls = cc.isnull().sum().values.reshape(1, -1)
sns.heatmap(nulls, ax=axes[0], cmap="Reds", annot=True, fmt="d",
            xticklabels=cc.columns, yticklabels=["Null count"],
            linewidths=0.5, cbar=False)
axes[0].set_title("Missing Values per Column (creditcard.csv)", fontweight="bold")
axes[0].tick_params(axis="x", rotation=90, labelsize=7)

# Scaling comparison: Amount before vs after StandardScaler
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
amount_scaled = scaler.fit_transform(cc[["Amount"]]).flatten()

axes[1].hist(cc["Amount"], bins=80, alpha=0.5, color=PALETTE["legit"],
             label="Original Amount", density=True)
axes[1].hist(amount_scaled, bins=80, alpha=0.5, color=PALETTE["fraud"],
             label="Scaled Amount", density=True)
axes[1].set_title("Amount: Before vs After StandardScaler", fontweight="bold")
axes[1].set_xlabel("Value")
axes[1].set_ylabel("Density")
axes[1].legend()

fig.suptitle("Credit Card: Data Quality & Scaling", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig9_cc_cleaning.png")
plt.close()
print("fig9 done")

# ─────────────────────────────────────────────────────────────
# FIG 10 – SMOTE before / after
# ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

datasets = [
    ("E-Commerce", {"Before": {0:109568,1:10304}, "After": {0:109568,1:109568}}),
    ("Credit Card", {"Before": {0:226602,1:374},  "After": {0:226602,1:226602}}),
]

for ax, (name, data) in zip(axes, datasets):
    x = np.arange(2)
    w = 0.35
    b1 = ax.bar(x - w/2, [data["Before"][0], data["Before"][1]], w,
                color=[PALETTE["legit"], PALETTE["fraud"]], label=["Legit Before","Fraud Before"],
                alpha=0.5, edgecolor="white")
    b2 = ax.bar(x + w/2, [data["After"][0], data["After"][1]], w,
                color=[PALETTE["legit"], PALETTE["fraud"]], label=["Legit After","Fraud After"],
                alpha=1.0, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(["Legitimate","Fraud"])
    ax.set_title(f"{name}: SMOTE Effect", fontweight="bold")
    ax.set_ylabel("Count")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{int(v):,}"))
    ax.legend(["Before SMOTE","After SMOTE"], loc="upper right", fontsize=8)

fig.suptitle("Class Distribution Before and After SMOTE (Training Set Only)",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig10_smote_comparison.png")
plt.close()
print("fig10 done")

print("\nAll 10 figures saved to report/visuals/")
