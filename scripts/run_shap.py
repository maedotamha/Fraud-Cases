"""
SHAP explainability for both fraud detection models.
Generates summary plots, waterfall plots for TP/FP/FN cases.
"""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings, joblib
from pathlib import Path
warnings.filterwarnings('ignore')

import shap

plt.rcParams.update({'figure.dpi': 150, 'savefig.bbox': 'tight',
                     'savefig.facecolor': 'white'})

BASE   = Path(__file__).parent.parent
MODELS = BASE / 'models'
VIS    = BASE / 'report/visuals'
PROC   = BASE / 'data/processed'

print("=" * 60)
print("  SHAP EXPLAINABILITY ANALYSIS")
print("=" * 60)

# ---------------------------------------------------------------------------
# Load data + models
# ---------------------------------------------------------------------------
print("\n[1/6] Loading data and models...")
X_test_f  = pd.read_csv(PROC / 'fraud_X_test.csv')
y_test_f  = pd.read_csv(PROC / 'fraud_y_test.csv').squeeze()
X_test_cc = pd.read_csv(PROC / 'cc_X_test.csv')
y_test_cc = pd.read_csv(PROC / 'cc_y_test.csv').squeeze()

xgb_f  = joblib.load(MODELS / 'xgb_ecommerce.pkl')
xgb_cc = joblib.load(MODELS / 'xgb_creditcard.pkl')
print("  Done.")

# ---------------------------------------------------------------------------
# SHAP explainers  (use a 2000-row background subsample for speed)
# ---------------------------------------------------------------------------
print("\n[2/6] Building SHAP explainers...")
rng = np.random.RandomState(42)

# Cast to float64 to avoid dtype('O') error with SHAP
X_test_f  = X_test_f.astype(np.float64)
X_test_cc = X_test_cc.astype(np.float64)

bg_idx_f  = rng.choice(len(X_test_f),  min(500, len(X_test_f)),  replace=False)
bg_idx_cc = rng.choice(len(X_test_cc), min(500, len(X_test_cc)), replace=False)

# tree_path_dependent avoids needing a background dataset
explainer_f  = shap.TreeExplainer(xgb_f,  feature_perturbation='tree_path_dependent')
explainer_cc = shap.TreeExplainer(xgb_cc, feature_perturbation='tree_path_dependent')
print("  Done.")

# Compute SHAP on subsample for summary plots
print("\n[3/6] Computing SHAP values (subsample for summary)...")
shap_vals_f  = explainer_f.shap_values(X_test_f.iloc[bg_idx_f])
shap_vals_cc = explainer_cc.shap_values(X_test_cc.iloc[bg_idx_cc])
print("  Done.")

# ---------------------------------------------------------------------------
# Fig S1 - SHAP Summary (beeswarm) for both datasets
# ---------------------------------------------------------------------------
print("\n[4/6] Figure S1: SHAP summary beeswarm...")
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

for ax, (shap_v, X_bg, title) in zip(axes, [
    (shap_vals_f,  X_test_f.iloc[bg_idx_f],  'E-Commerce XGBoost'),
    (shap_vals_cc, X_test_cc.iloc[bg_idx_cc], 'Credit Card XGBoost'),
]):
    plt.sca(ax)
    shap.summary_plot(shap_v, X_bg, plot_type='dot', show=False,
                      max_display=15, color_bar=True)
    ax.set_title(f'SHAP Summary - {title}', fontsize=13, fontweight='bold', pad=10)

fig.tight_layout()
fig.savefig(VIS / 'figS1_shap_summary.png')
plt.close('all')
print("  figS1 saved")

# ---------------------------------------------------------------------------
# Fig S2 - SHAP bar (mean |SHAP|) side by side
# ---------------------------------------------------------------------------
print("\n[5/6] Figure S2: Feature importance (mean |SHAP|)...")

def top_mean_shap(shap_v, X, n=12):
    mean_abs = np.abs(shap_v).mean(axis=0)
    idx = np.argsort(mean_abs)[-n:]
    return X.columns[idx].tolist(), mean_abs[idx]

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for ax, (shap_v, X_bg, title) in zip(axes, [
    (shap_vals_f,  X_test_f.iloc[bg_idx_f],  'E-Commerce'),
    (shap_vals_cc, X_test_cc.iloc[bg_idx_cc], 'Credit Card'),
]):
    names, vals = top_mean_shap(shap_v, X_bg)
    colors = ['#E8534C' if v == vals.max() else '#4C9BE8' for v in vals]
    ax.barh(names, vals, color=colors, edgecolor='white')
    ax.set_xlabel('Mean |SHAP value|')
    ax.set_title(f'Top Features by SHAP - {title}', fontweight='bold')
    for i, v in enumerate(vals):
        ax.text(v + vals.max() * 0.01, i, f'{v:.4f}', va='center', fontsize=8)

fig.tight_layout()
fig.savefig(VIS / 'figS2_shap_feature_importance.png')
plt.close('all')
print("  figS2 saved")

# ---------------------------------------------------------------------------
# Fig S3 - Waterfall plots for TP / FP / FN cases (e-commerce only)
# ---------------------------------------------------------------------------
print("\n[6/6] Figure S3: Waterfall plots (TP / FP / FN) for E-Commerce...")

y_proba_f = xgb_f.predict_proba(X_test_f)[:, 1]
y_pred_f  = (y_proba_f >= 0.5).astype(int)
y_true_f  = y_test_f.values

tp_idx = np.where((y_true_f == 1) & (y_pred_f == 1))[0]
fp_idx = np.where((y_true_f == 0) & (y_pred_f == 1))[0]
fn_idx = np.where((y_true_f == 1) & (y_pred_f == 0))[0]

# Pick the most "confident" representative for each case
tp_i = tp_idx[np.argmax(y_proba_f[tp_idx])]
fp_i = fp_idx[np.argmax(y_proba_f[fp_idx])]
fn_i = fn_idx[np.argmin(y_proba_f[fn_idx])]   # lowest proba among missed frauds

cases = [
    (tp_i, 'True Positive\n(Fraud caught)', '#2ecc71'),
    (fp_i, 'False Positive\n(Legit flagged as fraud)', '#e67e22'),
    (fn_i, 'False Negative\n(Fraud missed)', '#e74c3c'),
]

# Compute SHAP for individual cases
fig, axes = plt.subplots(1, 3, figsize=(21, 7))
for ax, (idx, label, color) in zip(axes, cases):
    row   = X_test_f.iloc[[idx]]
    sv    = explainer_f.shap_values(row)[0]
    exp_v = explainer_f.expected_value

    # Show top 10 features by absolute SHAP
    top_n  = 10
    order  = np.argsort(np.abs(sv))[-top_n:]
    feats  = X_test_f.columns[order].tolist()
    vals   = sv[order]
    bar_colors = ['#E8534C' if v > 0 else '#4C9BE8' for v in vals]

    ax.barh(feats, vals, color=bar_colors, edgecolor='white')
    ax.axvline(0, color='black', lw=0.8)
    ax.set_title(label, fontweight='bold', color=color, fontsize=11)
    ax.set_xlabel('SHAP value (impact on fraud probability)')
    pos = mpatches.Patch(color='#E8534C', label='Increases fraud prob')
    neg = mpatches.Patch(color='#4C9BE8', label='Decreases fraud prob')
    ax.legend(handles=[pos, neg], fontsize=8, loc='lower right')
    ax.text(0.02, 0.98, f'Pred prob: {y_proba_f[idx]:.3f}',
            transform=ax.transAxes, va='top', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

fig.suptitle('SHAP Waterfall - Representative Cases (E-Commerce XGBoost)',
             fontsize=13, fontweight='bold', y=1.01)
fig.tight_layout()
fig.savefig(VIS / 'figS3_shap_waterfall.png')
plt.close('all')
print("  figS3 saved")

print("\n\nSHAP analysis complete!")
print("Figures: figS1_shap_summary.png, figS2_shap_feature_importance.png, figS3_shap_waterfall.png")
