# Catching Fraudsters Before They Strike: Building a FinTech Fraud Detection System

### Interim Report 1 — Data Analysis, Feature Engineering & Preprocessing
**Adey Innovations Inc. | Author: Maedot Amha | June 2026**

---

## The Problem: Why Fraud Detection Is Hard

Every year, e-commerce fraud and credit card fraud cost businesses billions. But detecting fraud is not as simple as building a model and deploying it — because fraudulent transactions are rare, buried in an ocean of legitimate activity.

At Adey Innovations, we serve two distinct client streams:

- **E-commerce platforms** with rich user, device, and behavioral context
- **Banking institutions** with anonymized, privacy-protected transaction records

This report documents the first phase of our fraud detection pipeline: **understanding the data, engineering meaningful features, and preparing balanced training sets**. The goal is not just to describe the setup — it is to demonstrate exactly what the data reveals about how fraud behaves.

---

## The Datasets

We work with three files:

| Dataset | Rows | Fraud Rate | Key Challenge |
|---------|------|-----------|---------------|
| `Fraud_Data.csv` (e-commerce) | 151,112 | **9.36%** | Geolocation, behavioral features |
| `creditcard.csv` (bank) | 283,726 | **0.17%** | Severe imbalance, PCA-anonymized |
| `IpAddress_to_Country.csv` | 138,846 | — | Range-based IP lookup |

The imbalance levels are radically different. The e-commerce dataset is moderately imbalanced — about 1 in 11 transactions is fraudulent. The credit card dataset is severely imbalanced — only 1 in 600 transactions is fraud. These differences require us to treat them as two entirely separate modeling problems.

---

## Part 1 — E-Commerce Fraud Analysis (`Fraud_Data.csv`)

### 1.1 Data Cleaning

After loading the dataset, we:

- Parsed `signup_time` and `purchase_time` as proper datetime objects
- Confirmed **zero missing values** and **zero duplicate rows**
- Fixed the data type of `ip_address` (stored as float, needed as integer for range lookup)

The dataset is clean out of the box — the real work is in feature engineering.

### 1.2 Class Imbalance

```
Legitimate (0):  136,961  →  90.64%
Fraud      (1):   14,151  →   9.36%
```

While 9.36% sounds small, it is large enough for initial model training. However, without intervention, models will still be biased toward predicting "legitimate" — so we apply SMOTE (detailed in Section 4).

### 1.3 Key Univariate Findings

- **Purchase value** is right-skewed: most transactions are under $100, but fraud occurs at all price points
- **Age** is normally distributed (mean ~33 years), with no strong age-based fraud signal alone
- **Source distribution**: SEO (45%), Direct (30%), Ads (25%)
- **Browser distribution**: Chrome leads, followed by IE, FireFox, Safari, Opera

### 1.4 Bivariate Analysis — What Predicts Fraud?

**Fraud rate by acquisition source:**

| Source | Fraud Rate |
|--------|-----------|
| Direct | **10.54%** |
| Ads | 9.21% |
| SEO | 8.93% |

Users who arrived directly (typed the URL or used a bookmark) have a slightly higher fraud rate — potentially indicating bot traffic or credential-stuffed accounts.

---

## Part 2 — Geolocation: IP Address to Country

This is one of the most technically interesting steps. The `IpAddress_to_Country.csv` file maps IP **ranges** (not exact IPs) to countries. A standard `merge` on exact match would fail — we need a range-based join.

### The Technique: `pd.merge_asof`

```python
# Convert IPs to integers
fraud_df['ip_int'] = fraud_df['ip_address'].astype(np.int64)
ip_df['lower_int'] = ip_df['lower_bound_ip_address'].astype(np.int64)
ip_df['upper_int'] = ip_df['upper_bound_ip_address'].astype(np.int64)

# Range join: find the largest lower_bound <= ip_int
merged = pd.merge_asof(
    fraud_sorted,
    ip_sorted[['lower_int', 'upper_int', 'country']],
    left_on='ip_int',
    right_on='lower_int',
    direction='backward'
)

# Validate: ip_int must also be <= upper_bound
merged['country'] = merged.apply(
    lambda r: r['country'] if r['ip_int'] <= r['upper_int'] else 'Unknown',
    axis=1
)
```

This is an efficient O(n log n) range lookup — much faster than iterating row-by-row.

### Fraud Rate by Country (Top 5)

| Country | Transactions | Fraud | Fraud Rate |
|---------|-------------|-------|-----------|
| Luxembourg | 72 | 28 | **38.9%** |
| Ecuador | 106 | 28 | **26.4%** |
| Tunisia | 118 | 31 | **26.3%** |
| Peru | 119 | 31 | **26.1%** |
| Bolivia | 53 | 13 | **24.5%** |

> **Business Insight:** Transactions from Luxembourg, Ecuador, Tunisia, Peru, and Bolivia show fraud rates 2.5–4x the global average. These countries warrant additional verification steps, particularly for new users.

---

## Part 3 — Feature Engineering

Raw timestamps and IPs don't mean much to a machine learning model. We engineered three categories of new features:

### 3.1 Time-Based Features

**`time_since_signup`** — hours between account creation and purchase:

| Metric | Value |
|--------|-------|
| Mean | 1,370 hours (~57 days) |
| Min | 0.0003 hours (~1 minute) |
| 25th percentile | 607 hours (~25 days) |
| Median | 1,368 hours (~57 days) |

The most critical finding came from segmenting this feature into buckets:

**Fraud rate by time since signup:**

| Time Since Signup | Fraud Rate |
|-------------------|-----------|
| **< 1 hour** | **99.52%** |
| 1–6 hours | 3.33% |
| 6–24 hours | 4.10% |
| 1–7 days | 4.46% |
| > 7 days | 4.57% |

> **This is the single strongest fraud signal in the dataset.** Transactions placed within 1 hour of account creation are fraudulent 99.5% of the time. This feature alone could serve as a near-perfect rule-based filter for the highest-risk transactions.

**`hour_of_day`** — hour of the purchase (0–23)  
**`day_of_week`** — day of the week (0=Monday, 6=Sunday)  

These capture temporal fraud patterns, e.g., fraud spikes during off-hours when fraud teams have less coverage.

### 3.2 Transaction Velocity

**`tx_count_24h`** — number of prior transactions the user has made.

High velocity (many transactions in a short window) is a classic fraud pattern: stolen credentials are often used for a burst of purchases before being detected.

### 3.3 Why These Features Matter

These three families of features address different fraud mechanisms:

| Feature | Fraud Mechanism Captured |
|---------|------------------------|
| `time_since_signup` | Account creation fraud, synthetic identities |
| `tx_count_24h` | Account takeover, credential stuffing |
| `hour_of_day` | Off-hours automated attacks |
| `country` | Geographic risk concentration |

---

## Part 4 — Credit Card Data (`creditcard.csv`)

### 4.1 Data Quality

- **283,726 rows**, **31 columns** (V1–V28 + Time + Amount + Class)
- **Zero missing values**
- **Duplicates removed**: a small number of exact duplicate rows were dropped

### 4.2 Class Imbalance — Much More Severe

```
Legitimate (0):  283,253  →  99.83%
Fraud      (1):      473  →   0.17%
```

This is a 600:1 class ratio. A naive model that predicts "legitimate" for every transaction would achieve **99.83% accuracy** — but would miss every fraud. This is why accuracy is useless here, and why we use **AUC-PR and F1-Score** as our primary metrics.

### 4.3 What Stands Out in the Data

**Transaction amount:**

| Class | Mean Amount | Median Amount |
|-------|------------|---------------|
| Legitimate | $88.41 | $22.00 |
| **Fraud** | **$123.87** | **$9.82** |

Fraudulent transactions have a higher mean but lower median — suggesting that fraud clusters around small-value "test" transactions AND includes some large outliers.

**Top features correlated with fraud (absolute Pearson correlation):**

| Feature | |Correlation| |
|---------|------------|
| V17 | 0.3135 |
| V14 | 0.2934 |
| V12 | 0.2507 |
| V10 | 0.2070 |
| V16 | 0.1872 |
| V3 | 0.1823 |
| V7 | 0.1723 |

V17, V14, V12, and V10 are the strongest signals — though since these are PCA components, their business interpretation requires SHAP analysis (Task 3).

---

## Part 5 — Preprocessing Pipeline

### 5.1 E-Commerce Pipeline

1. **Drop** non-predictive columns: `user_id`, `device_id`, `ip_address`, raw timestamps
2. **One-hot encode** categoricals: `source`, `browser`, `sex`, `country` → **194 total features** after encoding
3. **StandardScaler** applied to: `purchase_value`, `age`, `time_since_signup`, `tx_count_24h`
4. **Stratified 80/20 split** to preserve class balance in both sets

### 5.2 Credit Card Pipeline

1. **StandardScaler** on `Amount` and `Time` only (V1–V28 are already PCA-scaled)
2. **Stratified 80/20 split**

### 5.3 Handling Class Imbalance — Why SMOTE?

We applied **SMOTE (Synthetic Minority Oversampling Technique)** to the **training set only**.

**Why SMOTE instead of simple oversampling or undersampling?**

| Method | Pros | Cons |
|--------|------|------|
| Random Oversampling | Simple | Creates exact duplicates → overfitting |
| Random Undersampling | Fast | Discards legitimate majority data |
| **SMOTE** | Creates synthetic samples via interpolation | Slightly slower; chosen approach |

SMOTE generates new minority samples by interpolating between real fraud cases in feature space, rather than duplicating existing ones. This results in a more diverse fraud representation and better generalization.

> **Critical rule enforced**: SMOTE was applied only after the train/test split. Applying it before splitting would leak synthetic test-set information into training — a form of data leakage that artificially inflates performance metrics.

**Class distributions after SMOTE:**

| Dataset | Before SMOTE (train) | After SMOTE (train) |
|---------|---------------------|-------------------|
| E-commerce | 0: 109,568 / 1: 10,304 | **0: 109,568 / 1: 109,568** |
| Credit card | 0: 226,602 / 1: 374 | **0: 226,602 / 1: 226,602** |

---

## Part 6 — Summary of Key Findings

### What We Know About Fraud After Interim 1

1. **Time since signup is the dominant signal** for e-commerce fraud: 99.5% of transactions within 1 hour of signup are fraudulent. This is actionable as an immediate rule-based trigger.

2. **Geographic concentration**: Luxembourg, Ecuador, Tunisia, Peru, and Bolivia have fraud rates 3–4x the global average.

3. **Acquisition channel matters**: Direct-traffic users commit fraud at a slightly higher rate (10.5%) than SEO users (8.9%), suggesting some bot/automated-account activity.

4. **Credit card fraud prefers small amounts**: Median fraud transaction is $9.82 vs $22.00 for legitimate — consistent with "card testing" patterns where fraudsters verify stolen cards with small purchases first.

5. **V17, V14, V12, V10 are the strongest PCA signals** correlated with credit card fraud, guiding which latent factors to watch in model explanation.

---

## What Comes Next (Interim 2 & Final)

| Phase | Task | Deliverable |
|-------|------|-------------|
| **Interim 2** | Model training | Logistic Regression + XGBoost/LightGBM, evaluated on AUC-PR and F1 |
| **Final** | SHAP explainability | Feature importance plots, force plots for TP/FP/FN, business recommendations |

The preprocessing splits are ready — saved and versioned in `data/processed/`. The next step is training classifiers on balanced data and comparing them using metrics designed for imbalanced problems.

---

## Repository

All code, executed notebooks, and processed data splits are available at:  
**https://github.com/maedotamha/Fraud-Cases**

```
notebooks/
├── eda-fraud-data.ipynb        ← executed ✓
├── eda-creditcard.ipynb        ← executed ✓
├── feature-engineering.ipynb  ← executed ✓
├── modeling.ipynb              ← Task 2, coming
└── shap-explainability.ipynb  ← Task 3, coming
```

---

*Built with Python 3.11 · pandas · scikit-learn · imbalanced-learn · matplotlib · seaborn*
