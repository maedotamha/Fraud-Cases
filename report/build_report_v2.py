"""
Build Interim 1 report v2 — includes all visualizations, full creditcard
preprocessing detail, and expanded next-steps section.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path

VISUALS = Path("report/visuals")
doc = Document()

# ── Page margins ──────────────────────────────────────────────
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(2.2)
    s.left_margin = s.right_margin = Cm(2.8)

# ── Colour palette ────────────────────────────────────────────
GREEN  = RGBColor(0x1A, 0x89, 0x17)
RED    = RGBColor(0xC0, 0x39, 0x2B)
BLUE   = RGBColor(0x0D, 0x6E, 0xFD)
GREY   = RGBColor(0x9B, 0x9B, 0x9B)
DARK   = RGBColor(0x1A, 0x1A, 0x1A)
ORANGE = RGBColor(0xB0, 0x7D, 0x1A)

def shade_para(para, hex_color="FFF8E7"):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    pPr.append(shd)

def shade_cell(cell, hex_color="F7F7F7"):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def add_table(doc, headers, rows, col_widths=None, highlight=None, header_color="2D6A4F"):
    highlight = highlight or []
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Table Grid'
    hc = t.rows[0].cells
    for i, h in enumerate(headers):
        hc[i].text = h
        p = hc[i].paragraphs[0]
        p.runs[0].bold = True; p.runs[0].font.size = Pt(9.5)
        p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade_cell(hc[i], header_color)
    for ri, row in enumerate(rows):
        rc = t.rows[ri+1].cells
        hi = ri in highlight
        for ci, val in enumerate(row):
            rc[ci].text = str(val)
            p = rc[ci].paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            if hi:
                shade_cell(rc[ci], "FFF3CD")
                p.runs[0].bold = True
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t

def add_image(doc, fname, width=6.0, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(VISUALS / fname), width=Inches(width))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].italic = True
        cap.runs[0].font.color.rgb = GREY
    doc.add_paragraph()

def callout(doc, label, text, bg="FFF8E7", label_color=None):
    p = doc.add_paragraph()
    shade_para(p, bg)
    r = p.add_run(label + "  ")
    r.bold = True
    if label_color: r.font.color.rgb = label_color
    p.add_run(text)
    doc.add_paragraph()

def h1(doc, text):
    h = doc.add_heading(text, level=1)
    h.runs[0].font.color.rgb = GREEN
    return h

def h2(doc, text):
    h = doc.add_heading(text, level=2)
    h.runs[0].font.color.rgb = DARK
    return h

def h3(doc, text):
    h = doc.add_heading(text, level=3)
    h.runs[0].font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    return h

def body(doc, text):
    p = doc.add_paragraph(text)
    for run in p.runs:
        run.font.size = Pt(10.5)
    return p

def rule(doc):
    p = doc.add_paragraph("─" * 80)
    p.runs[0].font.size = Pt(7)
    p.runs[0].font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

# ══════════════════════════════════════════════════════════════
# COVER
# ══════════════════════════════════════════════════════════════
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Catching Fraudsters Before They Strike")
r.bold = True; r.font.size = Pt(26); r.font.color.rgb = GREEN

p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("Building a FinTech Fraud Detection System")
r2.font.size = Pt(15); r2.italic = True; r2.font.color.rgb = GREY

p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run("Interim Report 1 — Data Analysis, Feature Engineering & Preprocessing")
r3.font.size = Pt(12); r3.bold = True

p4 = doc.add_paragraph(); p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
r4 = p4.add_run("Maedot Amha  ·  Adey Innovations Inc.  ·  June 2026")
r4.font.size = Pt(10); r4.font.color.rgb = GREY

doc.add_paragraph()
p = doc.add_paragraph(); shade_para(p, "F2FDF2")
r = p.add_run(
    "This report documents Phase 1 of Adey Innovations' fraud detection pipeline: "
    "understanding the data, engineering features that capture how fraud actually manifests, "
    "and preparing balanced training sets. All analysis is executed and reproducible — "
    "full notebook outputs are available on GitHub."
)
r.italic = True; r.font.size = Pt(11)
doc.add_page_break()

# ══════════════════════════════════════════════════════════════
# 1 — THE PROBLEM
# ══════════════════════════════════════════════════════════════
h1(doc, "1.  The Problem: Why Fraud Detection Is Hard")
body(doc,
    "Fraud detection sits at the intersection of two painful trade-offs. "
    "False positives — flagging legitimate purchases as fraud — frustrate real customers "
    "and erode trust. False negatives — missing actual fraud — cause direct financial loss. "
    "Getting the balance right requires deep data understanding, not just a good algorithm."
)
body(doc, "We operate two independent pipelines:")
for b in ["E-commerce transactions — rich behavioral context: device IDs, signup times, IP addresses, browser fingerprints.",
          "Bank credit card transactions — PCA-anonymized features (V1–V28) for regulatory compliance."]:
    p = doc.add_paragraph(style='List Bullet'); p.add_run(b).font.size = Pt(10.5)

# ══════════════════════════════════════════════════════════════
# 2 — DATASETS
# ══════════════════════════════════════════════════════════════
h1(doc, "2.  The Datasets")
add_table(doc,
    headers=["Dataset", "Rows", "Fraud Rate", "Key Challenge"],
    rows=[
        ["Fraud_Data.csv (e-commerce)", "151,112", "9.36%",  "Geolocation, behavioral features"],
        ["creditcard.csv (bank)",       "283,726", "0.17%",  "Severe imbalance, PCA-anonymized"],
        ["IpAddress_to_Country.csv",    "138,846", "—",      "Range-based IP lookup"],
    ],
    col_widths=[2.1, 0.85, 0.85, 2.3], highlight=[1]
)

add_image(doc, "fig1_class_imbalance.png", width=6.0,
          caption="Figure 1 — Class distribution in both datasets. The credit card imbalance (0.17%) is 55× more severe than e-commerce (9.36%).")

callout(doc,
    "⚠️  Why accuracy is misleading:",
    "A model predicting 'legitimate' for every credit card transaction achieves 99.83% accuracy "
    "while catching zero fraudulent cases. We evaluate on AUC-PR and F1-Score instead.",
    bg="FFE8E8", label_color=RED)

# ══════════════════════════════════════════════════════════════
# 3 — E-COMMERCE EDA
# ══════════════════════════════════════════════════════════════
h1(doc, "3.  E-Commerce Fraud Analysis (Fraud_Data.csv)")

h2(doc, "3.1  Data Cleaning")
add_table(doc,
    headers=["Issue Checked", "Finding", "Action Taken"],
    rows=[
        ["Missing values",     "Zero nulls across all 11 columns",             "None required"],
        ["Duplicate rows",     "Zero duplicate records",                        "None required"],
        ["Data types",         "signup_time / purchase_time stored as strings", "Parsed to datetime64"],
        ["ip_address format",  "Stored as float (e.g. 732758705.0)",            "Cast to int64 for range lookup"],
        ["Target encoding",    "class column is int (0/1)",                     "Confirmed — no changes"],
    ],
    col_widths=[1.7, 2.4, 1.9]
)

h2(doc, "3.2  Univariate Distributions")
add_image(doc, "fig2_ecomm_distributions.png", width=6.0,
          caption="Figure 2 — Purchase value is right-skewed; fraud occurs at all price points. Age is normally distributed (~33 years mean) with no standalone fraud signal.")

h2(doc, "3.3  Fraud Rate by Categorical Features")
add_image(doc, "fig3_fraud_by_category.png", width=6.2,
          caption="Figure 3 — Fraud rate by source, browser, and sex. Direct-channel users commit fraud at the highest rate (10.54%); no browser or sex shows extreme divergence.")
add_table(doc,
    headers=["Source", "Fraud Rate"],
    rows=[["Direct","10.54%"],["Ads","9.21%"],["SEO","8.93%"]],
    col_widths=[1.8, 1.2], highlight=[0]
)

# ══════════════════════════════════════════════════════════════
# 4 — GEOLOCATION
# ══════════════════════════════════════════════════════════════
h1(doc, "4.  Geolocation Enrichment — IP Address to Country")
body(doc,
    "IpAddress_to_Country.csv maps 138,846 IP ranges to countries. An exact-match join fails — "
    "we need a range-based lookup. The approach: convert IPs to 64-bit integers, sort both tables "
    "on the lower bound, apply pd.merge_asof (O(n log n)), then validate the IP falls within the "
    "matched upper bound."
)

add_image(doc, "fig5_fraud_by_country.png", width=6.2,
          caption="Figure 4 — Top 15 countries by fraud rate (minimum 50 transactions). The dashed line marks the global average (9.36%).")

add_table(doc,
    headers=["Country", "Transactions", "Fraud Cases", "Fraud Rate", "vs. Global Avg"],
    rows=[
        ["Luxembourg","72","28","38.9%","4.2×"],
        ["Ecuador","106","28","26.4%","2.8×"],
        ["Tunisia","118","31","26.3%","2.8×"],
        ["Peru","119","31","26.1%","2.8×"],
        ["Bolivia","53","13","24.5%","2.6×"],
        ["Global average","151,112","14,151","9.36%","1.0×"],
    ],
    col_widths=[1.3, 1.1, 1.1, 1.0, 1.1], highlight=[0,1,2,3,4]
)

callout(doc,
    "🌍  Business Insight:",
    "Transactions from Luxembourg, Ecuador, Tunisia, Peru, and Bolivia show fraud rates 2.6–4.2× "
    "the global average. A risk-tiered verification layer for these origins would intercept a "
    "disproportionate share of fraud at minimal friction to legitimate customers.",
    bg="FFF8E7", label_color=ORANGE)

# ══════════════════════════════════════════════════════════════
# 5 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════
h1(doc, "5.  Feature Engineering (E-Commerce)")

h2(doc, "5.1  time_since_signup — The Single Most Powerful Signal")
body(doc, "Elapsed hours between account creation and the purchase transaction:")
add_table(doc,
    headers=["Statistic", "Value"],
    rows=[["Mean","1,370 hrs (~57 days)"],["Minimum","0.0003 hrs (~1 min)"],
          ["25th pct","607 hrs (~25 days)"],["Median","1,368 hrs (~57 days)"]],
    col_widths=[2.0, 2.5]
)

add_image(doc, "fig4_fraud_by_signup_time.png", width=5.8,
          caption="Figure 5 — Fraud rate collapses after the first hour of signup. The <1h bucket is nearly 100% fraud.")

p = doc.add_paragraph(); shade_para(p, "FFE8E8")
r = p.add_run("★  Critical Finding:  "); r.bold = True; r.font.color.rgb = RED
p.add_run(
    "Transactions placed within 1 hour of account creation are fraudulent 99.52% of the time. "
    "This pattern reflects throwaway accounts created specifically for a single fraudulent purchase. "
    "This feature alone could serve as an immediate rule-based filter before any model is deployed."
)
doc.add_paragraph()

h2(doc, "5.2  Transaction Velocity — tx_count_24h")
body(doc,
    "Cumulative transaction count per user, computed via expanding window. "
    "Legitimate users transact infrequently; a burst of purchases in a short window "
    "signals credential stuffing or account takeover attacks."
)

h2(doc, "5.3  Temporal Features")
add_table(doc,
    headers=["Feature", "Derivation", "Fraud Mechanism Captured"],
    rows=[
        ["hour_of_day",       "purchase_time.dt.hour",         "Off-hours automated attacks"],
        ["day_of_week",       "purchase_time.dt.dayofweek",    "Weekend/holiday low-coverage windows"],
        ["time_since_signup", "(purchase - signup) / 3600",   "Throwaway accounts, synthetic identities"],
        ["tx_count_24h",      "Expanding user tx count",       "Account takeover, credential stuffing"],
        ["country",           "IP range → country lookup",     "Geographic risk concentration"],
    ],
    col_widths=[1.5, 2.0, 2.6]
)

# ══════════════════════════════════════════════════════════════
# 6 — CREDIT CARD EDA (EXPANDED)
# ══════════════════════════════════════════════════════════════
h1(doc, "6.  Credit Card Data — Full Analysis (creditcard.csv)")

h2(doc, "6.1  Data Cleaning")
body(doc,
    "The credit card dataset required more active cleaning than the e-commerce data."
)
add_table(doc,
    headers=["Issue Checked", "Finding", "Action Taken"],
    rows=[
        ["Missing values",    "Zero nulls across all 31 columns",                "None required"],
        ["Duplicate rows",    "1,081 exact duplicate rows detected",              "Dropped — reset index"],
        ["Final row count",   "283,726 rows after deduplication (from 284,807)", "Confirmed clean"],
        ["Data types",        "All numeric (float64/int64)",                      "No type fixes needed"],
        ["Feature scale",     "V1–V28: PCA-scaled; Amount and Time: not scaled", "StandardScaler on Amount, Time"],
        ["Target column",     "Class (capital C) — 0/1 integer",                 "Confirmed, no encoding needed"],
    ],
    col_widths=[1.6, 2.5, 2.0]
)

add_image(doc, "fig9_cc_cleaning.png", width=6.2,
          caption="Figure 6 — Left: missing value heatmap (all zeros — no nulls). Right: Amount before and after StandardScaler — the scaled distribution is zero-centred and unit-variance.")

h2(doc, "6.2  Class Imbalance")
add_table(doc,
    headers=["Class", "Count", "Percentage", "Imbalance Ratio"],
    rows=[
        ["Legitimate (0)", "283,253", "99.83%", "600:1 vs Fraud"],
        ["Fraud (1)",           "473",  "0.17%", "Minority class"],
    ],
    col_widths=[1.6, 1.1, 1.1, 1.6], highlight=[1]
)

h2(doc, "6.3  Transaction Amount Analysis")
add_image(doc, "fig6_cc_amount.png", width=6.2,
          caption="Figure 7 — Left: log-scale amount distributions; fraudulent transactions cluster at very low values. Right: boxplot (outliers removed) — fraud has a much lower median ($9.82 vs $22.00).")
add_table(doc,
    headers=["Class", "Mean Amount", "Median Amount", "Interpretation"],
    rows=[
        ["Legitimate (0)", "$88.41",  "$22.00", "Normal purchasing pattern"],
        ["Fraud (1)",      "$123.87", "$9.82",  "Card-testing micro-transactions"],
    ],
    col_widths=[1.4, 1.2, 1.2, 2.3], highlight=[1]
)
callout(doc,
    "💳  Card-Testing Pattern:",
    "Fraud median ($9.82) is far below legitimate median ($22.00), while fraud mean ($123.87) "
    "exceeds legitimate mean ($88.41). This bimodal signature reflects card testing: fraudsters "
    "validate stolen cards with micro-transactions, then escalate to large purchases.",
    bg="FFF8E7", label_color=ORANGE)

h2(doc, "6.4  Temporal Analysis")
add_image(doc, "fig7_cc_time.png", width=6.2,
          caption="Figure 8 — Left: Time distributions are similar for both classes, suggesting fraud is not concentrated in specific hours in this dataset. Right: hourly volume overlay.")

h2(doc, "6.5  PCA Feature Correlation with Fraud")
add_image(doc, "fig8_cc_correlations.png", width=6.2,
          caption="Figure 9 — Pearson correlations of all features with the fraud label. V17, V14, V12, V10 carry the strongest signal and are expected to dominate model feature importance.")
add_table(doc,
    headers=["Feature", "|Pearson r|", "Direction", "Priority"],
    rows=[
        ["V17", "0.3135", "Positive → fraud",   "★★★ Highest"],
        ["V14", "0.2934", "Negative → fraud",   "★★★ Highest"],
        ["V12", "0.2507", "Negative → fraud",   "★★★ High"],
        ["V10", "0.2070", "Negative → fraud",   "★★  High"],
        ["V16", "0.1872", "Negative → fraud",   "★★  Moderate"],
        ["V3",  "0.1823", "Negative → fraud",   "★★  Moderate"],
        ["V7",  "0.1723", "Negative → fraud",   "★   Moderate"],
    ],
    col_widths=[0.8, 0.9, 1.6, 1.4], highlight=[0,1,2]
)

h2(doc, "6.6  Data Transformation Summary")
add_table(doc,
    headers=["Step", "Action", "Rationale"],
    rows=[
        ["1. Deduplication",  "Drop 1,081 duplicate rows",            "Prevents training bias from repeated samples"],
        ["2. Scaling Amount", "StandardScaler → zero mean, unit var", "Amount is on a very different scale to V features"],
        ["3. Scaling Time",   "StandardScaler → zero mean, unit var", "Time range (0–172,792s) dwarfs PCA features"],
        ["4. V1–V28",         "No scaling applied",                    "Already PCA-transformed and normalized"],
        ["5. No encoding",    "No categorical columns present",        "All features are numeric post-PCA"],
    ],
    col_widths=[1.4, 2.2, 2.5]
)

# ══════════════════════════════════════════════════════════════
# 7 — PREPROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════
h1(doc, "7.  Preprocessing Pipeline — Both Datasets")

h2(doc, "7.1  The Golden Rule: Split Before Resampling")
body(doc,
    "Applying SMOTE before the train/test split causes data leakage: "
    "synthetic minority samples appear in both training and test sets, "
    "making performance metrics artificially optimistic. "
    "Our strict rule: stratified 80/20 split first — test set is never touched by any resampling."
)

h2(doc, "7.2  Why SMOTE?")
add_table(doc,
    headers=["Method", "Mechanism", "Weakness", "Our Choice"],
    rows=[
        ["Random Oversampling", "Duplicate minority rows",         "Overfitting on exact copies",   "✗"],
        ["Random Undersampling","Remove majority rows",            "Discards real legitimate data",  "✗"],
        ["SMOTE",               "Interpolate new synthetic rows",  "Slightly slower at scale",      "✓"],
    ],
    col_widths=[1.7, 1.8, 1.9, 0.7], highlight=[2]
)

h2(doc, "7.3  SMOTE Results")
add_image(doc, "fig10_smote_comparison.png", width=6.0,
          caption="Figure 10 — Before and after SMOTE on training splits. Both datasets reach a balanced 1:1 ratio. The test sets are left untouched.")
add_table(doc,
    headers=["Dataset", "Before SMOTE (train)", "After SMOTE (train)", "Test Set"],
    rows=[
        ["E-commerce",  "0: 109,568  /  1: 10,304",  "0: 109,568  /  1: 109,568", "Untouched (stratified split)"],
        ["Credit card", "0: 226,602  /  1:    374",   "0: 226,602  /  1: 226,602", "Untouched (stratified split)"],
    ],
    col_widths=[1.2, 1.9, 1.9, 1.8]
)

# ══════════════════════════════════════════════════════════════
# 8 — KEY FINDINGS
# ══════════════════════════════════════════════════════════════
h1(doc, "8.  Summary of Key Findings")

findings = [
    ("FFE8E8", RED,  "Finding 1 — The 1-Hour Rule (E-Commerce)",
     "Transactions placed within 1 hour of account creation are fraudulent 99.52% of the time. "
     "Actionable immediately as a rule-based trigger requiring no model."),
    ("FFF8E7", ORANGE, "Finding 2 — Geographic Concentration",
     "Luxembourg (38.9%), Ecuador (26.4%), Tunisia (26.3%), Peru (26.1%), Bolivia (24.5%) show "
     "fraud rates 2.6–4.2× the global average."),
    ("F7F9FF", BLUE, "Finding 3 — Direct Traffic Anomaly",
     "Direct-channel users commit fraud at 10.54% vs 8.93% for SEO users — consistent with "
     "automated bot traffic bypassing referral attribution."),
    ("F7F9FF", BLUE, "Finding 4 — Card-Testing Signature (Credit Card)",
     "Fraud median amount ($9.82) is far below legitimate median ($22.00), while fraud mean "
     "exceeds legitimate mean. This is the fingerprint of card-testing behavior."),
    ("F7F9FF", BLUE, "Finding 5 — PCA Feature Hierarchy (Credit Card)",
     "V17, V14, V12, V10 are the dominant fraud signals. SHAP analysis in Phase 3 will decode "
     "their behavioral interpretation."),
]
for bg, color, title, text in findings:
    p = doc.add_paragraph(); shade_para(p, bg)
    r = p.add_run(title + "\n"); r.bold = True; r.font.color.rgb = color
    p.add_run(text).font.size = Pt(10.5)
    doc.add_paragraph()

# ══════════════════════════════════════════════════════════════
# 9 — NEXT STEPS (EXPANDED)
# ══════════════════════════════════════════════════════════════
h1(doc, "9.  Next Steps — Interim 2 & Final Submission")

body(doc,
    "With clean, feature-engineered, balanced datasets in place, the pipeline moves to model "
    "building. Two key principles govern Phase 2: separate pipelines for each dataset, and "
    "evaluation metrics designed for imbalanced data."
)

h2(doc, "9.1  Separate Modeling Pipelines")
body(doc,
    "The e-commerce and credit card datasets have fundamentally different feature structures, "
    "imbalance ratios, and fraud mechanisms. They must be trained, tuned, and evaluated "
    "independently — a shared pipeline would mask the unique characteristics of each."
)
add_table(doc,
    headers=["", "E-Commerce Pipeline", "Credit Card Pipeline"],
    rows=[
        ["Features",       "194 (after OHE + engineering)", "30 (V1–V28, Amount, Time)"],
        ["Fraud rate",     "9.36%",                          "0.17%"],
        ["SMOTE ratio",    "1:1 balanced",                   "1:1 balanced"],
        ["Primary signal", "time_since_signup, country",     "V17, V14, V12"],
        ["Baseline model", "Logistic Regression",            "Logistic Regression"],
        ["Ensemble model", "XGBoost or LightGBM",            "XGBoost or LightGBM"],
    ],
    col_widths=[1.5, 2.2, 2.2]
)

h2(doc, "9.2  Hyperparameter Tuning Strategy")
body(doc,
    "We will perform systematic hyperparameter tuning on the ensemble models using "
    "RandomizedSearchCV (for efficiency on large datasets). The search space covers:"
)
add_table(doc,
    headers=["Parameter", "Search Range", "Why It Matters"],
    rows=[
        ["n_estimators",     "100 – 1,000",          "More trees reduce variance; diminishing returns after ~500"],
        ["max_depth",        "3 – 10",               "Controls overfitting; shallow trees generalize better on imbalanced data"],
        ["learning_rate",    "0.01 – 0.3",           "Lower rates + more trees often outperform high-rate configurations"],
        ["min_child_weight", "1 – 10",               "Prevents splits on tiny fraud-minority nodes"],
        ["scale_pos_weight", "1 – 600",              "XGBoost's built-in class weight parameter — critical for 600:1 imbalance"],
        ["subsample",        "0.6 – 1.0",            "Row sampling per tree — reduces overfitting on synthetic SMOTE samples"],
        ["colsample_bytree", "0.6 – 1.0",            "Feature sampling per tree — improves generalization"],
    ],
    col_widths=[1.5, 1.2, 3.1]
)

h2(doc, "9.3  Cross-Validation Strategy")
body(doc,
    "We will use Stratified K-Fold cross-validation (k=5) to get reliable, unbiased performance "
    "estimates. Standard K-Fold risks putting all fraud cases in one fold; stratification "
    "guarantees each fold preserves the class ratio."
)
add_table(doc,
    headers=["CV Setting", "Value", "Rationale"],
    rows=[
        ["Method",   "StratifiedKFold",  "Preserves fraud class ratio in every fold"],
        ["k (folds)","5",                "Standard for large datasets; balances bias-variance"],
        ["Scoring",  "average_precision","AUC-PR is the correct metric for imbalanced classification"],
        ["Reported", "Mean ± Std Dev",   "Std Dev flags instability — wide spread = unreliable model"],
        ["SMOTE",    "Inside each fold", "SMOTE applied only to training portion of each fold via Pipeline"],
    ],
    col_widths=[1.5, 1.5, 3.0]
)

h2(doc, "9.4  Evaluation Metrics")
add_table(doc,
    headers=["Metric", "Why It's Used", "What Bad Looks Like"],
    rows=[
        ["AUC-PR",         "Precision-Recall curve area; best metric for imbalanced classes",   "< 0.50 = worse than random for fraud"],
        ["F1-Score",       "Harmonic mean of precision and recall; penalises both FP and FN",   "< 0.60 = too many missed fraud cases"],
        ["Confusion Matrix","Shows absolute TP, FP, TN, FN counts",                             "High FN = fraud slipping through"],
        ["NOT Accuracy",   "Misleading — 99.83% achievable by predicting all-legitimate",       "Any score near 99% is a red flag"],
    ],
    col_widths=[1.3, 2.8, 1.9]
)

h2(doc, "9.5  Phase Roadmap")
add_table(doc,
    headers=["Phase", "Task", "Key Deliverable"],
    rows=[
        ["Interim 2",  "Logistic Regression baseline",            "AUC-PR, F1, confusion matrix for both datasets"],
        ["Interim 2",  "XGBoost / LightGBM ensemble",            "Hyperparameter-tuned results, CV mean ± std"],
        ["Interim 2",  "Model comparison table",                  "Justified selection of best model per dataset"],
        ["Final",      "SHAP summary plots",                      "Global feature importance (both datasets)"],
        ["Final",      "SHAP force plots — 3 cases each",        "TP, FP, FN predictions explained individually"],
        ["Final",      "Business recommendations",                "≥3 actionable insights tied to SHAP findings"],
    ],
    col_widths=[1.0, 2.4, 2.6]
)

# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
rule(doc)
p = doc.add_paragraph()
r = p.add_run(
    "GitHub: https://github.com/maedotamha/Fraud-Cases   ·   "
    "Built with Python 3.11 · pandas · scikit-learn · imbalanced-learn · matplotlib · seaborn\n"
    "All Task 1 notebooks are fully executed with outputs.  Interim Report 1  ·  June 2026"
)
r.font.size = Pt(8.5); r.font.color.rgb = GREY

doc.save("report/interim1_report_v2.docx")
print("Saved: report/interim1_report_v2.docx")
