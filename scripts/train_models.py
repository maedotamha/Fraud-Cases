"""
Standalone training script for both fraud detection pipelines.
Subsamples training data for hyperparameter search, then retrains on full data.
"""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings, joblib, time, json
from pathlib import Path
warnings.filterwarnings('ignore')

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, cross_validate
from sklearn.metrics import (
    average_precision_score, f1_score, confusion_matrix,
    precision_recall_curve, classification_report
)
from xgboost import XGBClassifier

sns.set_theme(style='whitegrid', font_scale=1.05)
plt.rcParams.update({'figure.dpi': 150, 'savefig.bbox': 'tight',
                     'savefig.facecolor': 'white'})

BASE   = Path(__file__).parent.parent
MODELS = BASE / 'models';        MODELS.mkdir(exist_ok=True)
VIS    = BASE / 'report/visuals'; VIS.mkdir(exist_ok=True)
PROC   = BASE / 'data/processed'

print("=" * 60)
print("  ADEY INNOVATIONS - FRAUD DETECTION TRAINING")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("\n[1/9] Loading data...")
X_train_f  = pd.read_csv(PROC / 'fraud_X_train.csv')
X_test_f   = pd.read_csv(PROC / 'fraud_X_test.csv')
y_train_f  = pd.read_csv(PROC / 'fraud_y_train.csv').squeeze()
y_test_f   = pd.read_csv(PROC / 'fraud_y_test.csv').squeeze()

X_train_cc = pd.read_csv(PROC / 'cc_X_train.csv')
X_test_cc  = pd.read_csv(PROC / 'cc_X_test.csv')
y_train_cc = pd.read_csv(PROC / 'cc_y_train.csv').squeeze()
y_test_cc  = pd.read_csv(PROC / 'cc_y_test.csv').squeeze()

print(f"  E-comm  train={X_train_f.shape}  test={X_test_f.shape}")
print(f"  CC      train={X_train_cc.shape} test={X_test_cc.shape}")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def evaluate(name, model, X_test, y_test):
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred  = (y_proba >= 0.5).astype(int)
    auc_pr  = average_precision_score(y_test, y_proba)
    f1      = f1_score(y_test, y_pred, zero_division=0)
    cm      = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"\n  {'-' * 50}")
    print(f"  {name}")
    print(f"  {'-' * 50}")
    print(f"  AUC-PR={auc_pr:.4f}  F1={f1:.4f}  TP={tp} FP={fp} FN={fn} TN={tn}")
    print(classification_report(y_test, y_pred,
                                target_names=['Legit', 'Fraud'],
                                zero_division=0))
    return dict(name=name, AUCPR=round(auc_pr, 4), F1=round(f1, 4),
                TP=int(tp), FP=int(fp), FN=int(fn), TN=int(tn),
                y_proba=y_proba, y_pred=y_pred, cm=cm)


def stratified_subsample(X, y, n=40000, random_state=42):
    """Take a balanced stratified subsample for fast hyperparameter search."""
    rng    = np.random.RandomState(random_state)
    idx0   = np.where(y == 0)[0]
    idx1   = np.where(y == 1)[0]
    n_each = min(n // 2, len(idx0), len(idx1))
    sel    = np.concatenate([
        rng.choice(idx0, n_each, replace=False),
        rng.choice(idx1, n_each, replace=False),
    ])
    rng.shuffle(sel)
    return (X.iloc[sel].reset_index(drop=True),
            y.iloc[sel].reset_index(drop=True))


skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

param_dist = {
    'n_estimators':     [150, 300],
    'max_depth':        [3, 5, 7],
    'learning_rate':    [0.05, 0.1, 0.2],
    'subsample':        [0.7, 0.9],
    'colsample_bytree': [0.7, 0.9],
    'min_child_weight': [1, 3],
}

# ===========================================================================
# E-COMMERCE PIPELINE
# ===========================================================================
print("\n\n[2/9] E-Commerce - Logistic Regression baseline...")
t0   = time.time()
lr_f = LogisticRegression(max_iter=1000, class_weight='balanced',
                           solver='saga', random_state=42, n_jobs=1)
lr_f.fit(X_train_f, y_train_f)
print(f"  Done in {time.time() - t0:.1f}s")
joblib.dump(lr_f, MODELS / 'lr_ecommerce.pkl')
res_lr_f = evaluate('LR - E-Commerce', lr_f, X_test_f, y_test_f)

print("\n[3/9] E-Commerce - XGBoost hyperparameter search (subsampled)...")
X_sub_f, y_sub_f = stratified_subsample(X_train_f, y_train_f, n=40000)
print(f"  Search subset: {X_sub_f.shape}  (full train: {X_train_f.shape})")
t0 = time.time()
search_f = RandomizedSearchCV(
    XGBClassifier(eval_metric='aucpr', random_state=42,
                  n_jobs=1, tree_method='hist'),
    param_dist, n_iter=8, scoring='average_precision',
    cv=skf, random_state=42, n_jobs=1, verbose=1
)
search_f.fit(X_sub_f, y_sub_f)
print(f"  Search done in {time.time() - t0:.1f}s")
print(f"  Best params : {search_f.best_params_}")
print(f"  Best CV AUC-PR (sub): {search_f.best_score_:.4f}")

print("\n[4/9] E-Commerce - Retrain best XGBoost on full training data...")
best_f = search_f.best_params_.copy()
t0     = time.time()
xgb_f  = XGBClassifier(**best_f, eval_metric='aucpr', random_state=42,
                         n_jobs=1, tree_method='hist')
xgb_f.fit(X_train_f, y_train_f)
print(f"  Full retrain done in {time.time() - t0:.1f}s")
joblib.dump(xgb_f, MODELS / 'xgb_ecommerce.pkl')
res_xgb_f = evaluate('XGBoost - E-Commerce', xgb_f, X_test_f, y_test_f)

print("\n[5/9] E-Commerce - 5-Fold CV on best XGBoost...")
t0   = time.time()
cv_f = cross_validate(xgb_f, X_train_f, y_train_f, cv=skf,
                      scoring={'auc_pr': 'average_precision', 'f1': 'f1'},
                      n_jobs=1)
print(f"  CV done in {time.time() - t0:.1f}s")
print(f"  AUC-PR : {cv_f['test_auc_pr'].mean():.4f} +/- {cv_f['test_auc_pr'].std():.4f}")
print(f"  F1     : {cv_f['test_f1'].mean():.4f} +/- {cv_f['test_f1'].std():.4f}")

# ===========================================================================
# CREDIT CARD PIPELINE
# ===========================================================================
print("\n\n[6/9] Credit Card - Logistic Regression baseline...")
t0    = time.time()
lr_cc = LogisticRegression(max_iter=1000, class_weight='balanced',
                            solver='saga', random_state=42, n_jobs=1)
lr_cc.fit(X_train_cc, y_train_cc)
print(f"  Done in {time.time() - t0:.1f}s")
joblib.dump(lr_cc, MODELS / 'lr_creditcard.pkl')
res_lr_cc = evaluate('LR - Credit Card', lr_cc, X_test_cc, y_test_cc)

print("\n[7/9] Credit Card - XGBoost hyperparameter search (subsampled)...")
X_sub_cc, y_sub_cc = stratified_subsample(X_train_cc, y_train_cc, n=40000)
print(f"  Search subset: {X_sub_cc.shape}  (full train: {X_train_cc.shape})")
t0 = time.time()
search_cc = RandomizedSearchCV(
    XGBClassifier(eval_metric='aucpr', random_state=42,
                  n_jobs=1, tree_method='hist'),
    param_dist, n_iter=8, scoring='average_precision',
    cv=skf, random_state=42, n_jobs=1, verbose=1
)
search_cc.fit(X_sub_cc, y_sub_cc)
print(f"  Search done in {time.time() - t0:.1f}s")
print(f"  Best params : {search_cc.best_params_}")
print(f"  Best CV AUC-PR (sub): {search_cc.best_score_:.4f}")

print("\n[8/9] Credit Card - Retrain best XGBoost on full training data...")
best_cc = search_cc.best_params_.copy()
t0      = time.time()
xgb_cc  = XGBClassifier(**best_cc, eval_metric='aucpr', random_state=42,
                          n_jobs=1, tree_method='hist')
xgb_cc.fit(X_train_cc, y_train_cc)
print(f"  Full retrain done in {time.time() - t0:.1f}s")
joblib.dump(xgb_cc, MODELS / 'xgb_creditcard.pkl')
res_xgb_cc = evaluate('XGBoost - Credit Card', xgb_cc, X_test_cc, y_test_cc)

print("\n[9/9] Credit Card - 5-Fold CV on best XGBoost...")
t0    = time.time()
cv_cc = cross_validate(xgb_cc, X_train_cc, y_train_cc, cv=skf,
                       scoring={'auc_pr': 'average_precision', 'f1': 'f1'},
                       n_jobs=1)
print(f"  CV done in {time.time() - t0:.1f}s")
print(f"  AUC-PR : {cv_cc['test_auc_pr'].mean():.4f} +/- {cv_cc['test_auc_pr'].std():.4f}")
print(f"  F1     : {cv_cc['test_f1'].mean():.4f} +/- {cv_cc['test_f1'].std():.4f}")

# ===========================================================================
# SAVE SUMMARY + FIGURES
# ===========================================================================
summary = pd.DataFrame([
    dict(Dataset='E-Commerce',  Model='Logistic Regression',
         AUCPR=res_lr_f['AUCPR'],   F1=res_lr_f['F1'],
         CV_AUCPR='baseline', CV_F1='baseline',
         TP=res_lr_f['TP'], FP=res_lr_f['FP'],
         FN=res_lr_f['FN'], TN=res_lr_f['TN']),
    dict(Dataset='E-Commerce',  Model='XGBoost (tuned)',
         AUCPR=res_xgb_f['AUCPR'],  F1=res_xgb_f['F1'],
         CV_AUCPR=f"{cv_f['test_auc_pr'].mean():.4f}+/-{cv_f['test_auc_pr'].std():.4f}",
         CV_F1=f"{cv_f['test_f1'].mean():.4f}+/-{cv_f['test_f1'].std():.4f}",
         TP=res_xgb_f['TP'], FP=res_xgb_f['FP'],
         FN=res_xgb_f['FN'], TN=res_xgb_f['TN']),
    dict(Dataset='Credit Card', Model='Logistic Regression',
         AUCPR=res_lr_cc['AUCPR'],  F1=res_lr_cc['F1'],
         CV_AUCPR='baseline', CV_F1='baseline',
         TP=res_lr_cc['TP'], FP=res_lr_cc['FP'],
         FN=res_lr_cc['FN'], TN=res_lr_cc['TN']),
    dict(Dataset='Credit Card', Model='XGBoost (tuned)',
         AUCPR=res_xgb_cc['AUCPR'], F1=res_xgb_cc['F1'],
         CV_AUCPR=f"{cv_cc['test_auc_pr'].mean():.4f}+/-{cv_cc['test_auc_pr'].std():.4f}",
         CV_F1=f"{cv_cc['test_f1'].mean():.4f}+/-{cv_cc['test_f1'].std():.4f}",
         TP=res_xgb_cc['TP'], FP=res_xgb_cc['FP'],
         FN=res_xgb_cc['FN'], TN=res_xgb_cc['TN']),
])
summary.to_csv(PROC / 'model_comparison.csv', index=False)

best_params = {'ecommerce': best_f, 'creditcard': best_cc}
with open(str(MODELS / 'best_params.json'), 'w') as fh:
    json.dump(best_params, fh, indent=2)

print("\n\n=== MODEL COMPARISON ===")
print(summary[['Dataset', 'Model', 'AUCPR', 'F1', 'CV_AUCPR', 'FN']].to_string(index=False))

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
print("\n\nGenerating figures...")
results_f  = [res_lr_f,  res_xgb_f]
results_cc = [res_lr_cc, res_xgb_cc]

# Fig M1 - metric bar charts
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for row, (results, title) in enumerate([
    (results_f, 'E-Commerce'), (results_cc, 'Credit Card')
]):
    for col, (key, metric) in enumerate([('AUCPR', 'AUC-PR'), ('F1', 'F1-Score')]):
        ax   = axes[row][col]
        vals = [r[key] for r in results]
        bars = ax.bar(['Logistic\nRegression', 'XGBoost'], vals,
                      color=['#4C9BE8', '#E8534C'], width=0.5, edgecolor='white')
        ax.set_ylim(0, 1)
        ax.set_title(f'{title} - {metric}', fontweight='bold')
        ax.set_ylabel(metric)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                    f'{v:.4f}', ha='center', va='bottom',
                    fontweight='bold', fontsize=11)
fig.suptitle('Model Comparison: Logistic Regression vs XGBoost',
             fontsize=14, fontweight='bold', y=1.01)
fig.tight_layout()
fig.savefig(VIS / 'figM1_model_comparison.png')
plt.close()
print("  figM1 saved")

# Fig M2 - Precision-Recall curves
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (results, X_test, y_test, title) in zip(axes, [
    (results_f,  X_test_f,  y_test_f,  'E-Commerce'),
    (results_cc, X_test_cc, y_test_cc, 'Credit Card'),
]):
    for res, color, ls in zip(results, ['#4C9BE8', '#E8534C'], ['-', '--']):
        p, r, _ = precision_recall_curve(y_test, res['y_proba'])
        label   = res['name'].split('-')[0].strip()
        ax.plot(r, p, color=color, lw=2, ls=ls,
                label=f"{label} (AUC-PR={res['AUCPR']:.4f})")
    ax.axhline(y_test.mean(), color='grey', lw=1, ls=':',
               label=f"Random ({y_test.mean():.4f})")
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(f'PR Curve - {title}', fontweight='bold')
    ax.legend(fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
fig.tight_layout()
fig.savefig(VIS / 'figM2_pr_curves.png')
plt.close()
print("  figM2 saved")

# Fig M3 - Confusion matrices
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
pairs = [
    (axes[0][0], res_lr_f,   'LR - E-Commerce'),
    (axes[0][1], res_xgb_f,  'XGBoost - E-Commerce'),
    (axes[1][0], res_lr_cc,  'LR - Credit Card'),
    (axes[1][1], res_xgb_cc, 'XGBoost - Credit Card'),
]
for ax, res, title in pairs:
    cm_n = res['cm'].astype(float) / res['cm'].sum(axis=1, keepdims=True)
    sns.heatmap(cm_n, annot=True, fmt='.2%', cmap='Blues', ax=ax,
                xticklabels=['Pred Legit', 'Pred Fraud'],
                yticklabels=['True Legit', 'True Fraud'],
                cbar=False, linewidths=0.5)
    for i in range(2):
        for j in range(2):
            ax.text(j + 0.5, i + 0.72,
                    f"n={res['cm'][i, j]:,}",
                    ha='center', va='center',
                    fontsize=9, color='dimgrey')
    ax.set_title(title, fontweight='bold')
fig.suptitle('Confusion Matrices - All Models',
             fontsize=14, fontweight='bold', y=1.01)
fig.tight_layout()
fig.savefig(VIS / 'figM3_confusion_matrices.png')
plt.close()
print("  figM3 saved")

# Fig M4 - CV fold scores
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (cv_res, title) in zip(axes, [
    (cv_f,  'E-Commerce XGBoost'),
    (cv_cc, 'Credit Card XGBoost'),
]):
    x     = np.arange(5)
    w     = 0.35
    aucpr = cv_res['test_auc_pr']
    f1    = cv_res['test_f1']
    ax.bar(x - w / 2, aucpr, w, color='#4C9BE8', label='AUC-PR',   edgecolor='white')
    ax.bar(x + w / 2, f1,    w, color='#E8534C', label='F1-Score', edgecolor='white')
    ax.axhline(aucpr.mean(), color='#2e6da4', lw=1.5, ls='--',
               label=f'AUC-PR {aucpr.mean():.4f}+/-{aucpr.std():.4f}')
    ax.axhline(f1.mean(),    color='#a83228', lw=1.5, ls=':',
               label=f'F1 {f1.mean():.4f}+/-{f1.std():.4f}')
    ax.set_xticks(x)
    ax.set_xticklabels([f'Fold {i + 1}' for i in x])
    ax.set_ylim(0, 1.1)
    ax.set_title(f'{title} - 5-Fold CV', fontweight='bold')
    ax.set_ylabel('Score')
    ax.legend(fontsize=8)
fig.suptitle('Stratified K-Fold Cross-Validation (k=5)',
             fontsize=14, fontweight='bold', y=1.01)
fig.tight_layout()
fig.savefig(VIS / 'figM4_cv_results.png')
plt.close()
print("  figM4 saved")

# Fig M5 - Feature importance
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, (model, X, title) in zip(axes, [
    (xgb_f,  X_train_f,  'E-Commerce'),
    (xgb_cc, X_train_cc, 'Credit Card'),
]):
    imp   = pd.Series(model.feature_importances_, index=X.columns)
    top10 = imp.sort_values(ascending=True).tail(10)
    colors = ['#E8534C' if v == top10.max() else '#4C9BE8'
              for v in top10.values]
    top10.plot(kind='barh', ax=ax, color=colors, edgecolor='white')
    ax.set_title(f'Top 10 Feature Importance - {title}', fontweight='bold')
    ax.set_xlabel('Gain Importance')
    for i, v in enumerate(top10.values):
        ax.text(v + top10.max() * 0.01, i,
                f'{v:.4f}', va='center', fontsize=8)
fig.tight_layout()
fig.savefig(VIS / 'figM5_feature_importance.png')
plt.close()
print("  figM5 saved")

print("\n\nTraining complete!")
print("Models saved:", [f.name for f in MODELS.iterdir() if f.suffix == '.pkl'])
print("Run:  python report/build_interim2_report.py")
