"""Build the Interim 1 report as a formatted .docx file."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3)
    section.right_margin  = Cm(3)

# ── Helper: paragraph shading ─────────────────────────────────────────────────
def shade_paragraph(para, hex_color="FFF8E7"):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    pPr.append(shd)

# ── Helper: table cell shading ────────────────────────────────────────────────
def shade_cell(cell, hex_color="FFF8E7"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)

# ── Helper: set cell borders ──────────────────────────────────────────────────
def set_cell_border(cell, **kwargs):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            tag = OxmlElement(f'w:{edge}')
            for k, v in kwargs[edge].items():
                tag.set(qn(f'w:{k}'), v)
            tcBorders.append(tag)
    tcPr.append(tcBorders)

def add_table(doc, headers, rows, col_widths=None, highlight_rows=None):
    highlight_rows = highlight_rows or []
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(10)
        shade_cell(hdr_cells[i], "E8E8E8")

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        is_highlight = r_idx in highlight_rows
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = str(val)
            p = row_cells[c_idx].paragraphs[0]
            p.runs[0].font.size = Pt(10)
            if is_highlight:
                shade_cell(row_cells[c_idx], "FFF3CD")
                p.runs[0].bold = True

    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)

    doc.add_paragraph()
    return table

# ══════════════════════════════════════════════════════════════════════════════
# COVER / TITLE
# ══════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Catching Fraudsters Before They Strike")
run.bold      = True
run.font.size = Pt(26)
run.font.color.rgb = RGBColor(0x1A, 0x69, 0x17)

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("Building a FinTech Fraud Detection System")
r2.font.size  = Pt(15)
r2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
r2.italic = True

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run("Interim Report 1 — Data Analysis, Feature Engineering & Preprocessing")
r3.font.size  = Pt(12)
r3.bold = True

p4 = doc.add_paragraph()
p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
r4 = p4.add_run("Maedot Amha  ·  Adey Innovations Inc.  ·  June 2026")
r4.font.size  = Pt(10)
r4.font.color.rgb = RGBColor(0x9B, 0x9B, 0x9B)

doc.add_paragraph()

# Lead callout
lead = doc.add_paragraph()
shade_paragraph(lead, "F2FDF2")
lead_run = lead.add_run(
    "Fraudulent transactions are rare, sneaky, and expensive. In this first phase of Adey Innovations' "
    "fraud detection system, we analyzed 434,000 real-world transactions across two data domains — "
    "and found signals so strong they could catch fraud before a single model is trained."
)
lead_run.italic    = True
lead_run.font.size = Pt(12)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
h = doc.add_heading("The Problem: Why Fraud Detection Is Hard", level=1)
h.runs[0].font.color.rgb = RGBColor(0x1A, 0x69, 0x17)

doc.add_paragraph(
    "Fraud detection sits at the intersection of two painful trade-offs. "
    "False positives — flagging a legitimate purchase as fraud — frustrate real customers "
    "and erode trust. False negatives — missing actual fraud — cause direct financial loss. "
    "Getting the balance right requires understanding the data deeply enough to build features "
    "that speak directly to how fraudsters actually behave."
)
doc.add_paragraph(
    "At Adey Innovations, we are building a unified detection capability across two very different "
    "transaction streams:"
)
p = doc.add_paragraph(style='List Bullet')
p.add_run("E-commerce transactions").bold = True
p.add_run(" with rich behavioral context — device IDs, signup times, IP addresses, browser fingerprints.")
p = doc.add_paragraph(style='List Bullet')
p.add_run("Bank credit card transactions").bold = True
p.add_run(" where features are anonymized via PCA for regulatory compliance.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — DATASETS
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("The Datasets: Two Very Different Imbalance Problems", level=1)

add_table(doc,
    headers=["Dataset", "Rows", "Fraud Rate", "Key Challenge"],
    rows=[
        ["Fraud_Data.csv (e-commerce)", "151,112", "9.36%",  "Geolocation, behavioral features"],
        ["creditcard.csv (bank)",        "283,726", "0.17%",  "Severe imbalance, PCA-anonymized"],
        ["IpAddress_to_Country.csv",     "138,846", "—",      "Range-based IP lookup"],
    ],
    col_widths=[2.2, 0.9, 0.9, 2.2],
    highlight_rows=[1]
)

doc.add_paragraph(
    "These two datasets have radically different imbalance profiles. At 9.36%, the e-commerce data is "
    "moderately imbalanced. The credit card data, at 0.17%, is a 600:1 ratio. A model that predicts "
    "'legitimate' for every transaction achieves 99.83% accuracy while catching zero fraudulent cases. "
    "This is precisely why overall accuracy is useless here — we evaluate on AUC-PR and F1-Score instead."
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — E-COMMERCE EDA
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 1 — E-Commerce Fraud: What the Data Reveals", level=1)

doc.add_heading("1.1  Data Cleaning", level=2)
doc.add_paragraph(
    "After loading Fraud_Data.csv: zero missing values confirmed, zero duplicates. "
    "signup_time and purchase_time parsed as datetime objects. ip_address converted from "
    "float to 64-bit integer for the geolocation range join."
)

doc.add_heading("1.2  Class Imbalance", level=2)
add_table(doc,
    headers=["Class", "Count", "Percentage"],
    rows=[
        ["Legitimate (0)", "136,961", "90.64%"],
        ["Fraud (1)",       "14,151",   "9.36%"],
    ],
    col_widths=[1.8, 1.2, 1.2]
)

doc.add_heading("1.3  Fraud Rate by Acquisition Channel", level=2)
add_table(doc,
    headers=["Source", "Fraud Rate"],
    rows=[
        ["Direct", "10.54%"],
        ["Ads",     "9.21%"],
        ["SEO",     "8.93%"],
    ],
    col_widths=[1.8, 1.2],
    highlight_rows=[0]
)
doc.add_paragraph(
    "Users arriving via Direct traffic commit fraud at a notably higher rate — "
    "consistent with bot traffic or credential-stuffing attacks bypassing referral tracking."
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — GEOLOCATION
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 2 — Geolocation: IP Address to Country", level=1)

doc.add_paragraph(
    "The IpAddress_to_Country.csv file maps IP ranges (not exact IPs) to countries. "
    "A standard exact-match join would fail. We use pd.merge_asof — an O(n log n) "
    "range-based join that finds the largest lower_bound still ≤ each transaction IP, "
    "then validates the IP falls within the matched upper bound."
)

doc.add_heading("Fraud Rate by Country — Top 5", level=2)
add_table(doc,
    headers=["Country", "Transactions", "Fraud Cases", "Fraud Rate"],
    rows=[
        ["Luxembourg", "72",  "28", "38.9%"],
        ["Ecuador",    "106", "28", "26.4%"],
        ["Tunisia",    "118", "31", "26.3%"],
        ["Peru",       "119", "31", "26.1%"],
        ["Bolivia",     "53", "13", "24.5%"],
        ["Global average", "—", "—", "9.36%"],
    ],
    col_widths=[1.5, 1.2, 1.2, 1.2],
    highlight_rows=[0, 1, 2, 3, 4]
)

callout = doc.add_paragraph()
shade_paragraph(callout, "FFF8E7")
r = callout.add_run("Business Insight: ")
r.bold = True
callout.add_run(
    "Transactions from these five countries show fraud rates 2.5–4× the global average. "
    "A risk-tiered verification system — requiring additional authentication for high-risk-origin IPs — "
    "could intercept a significant portion of fraud at near-zero cost to legitimate users."
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 3 — Feature Engineering", level=1)

doc.add_heading("3.1  time_since_signup — The Dominant Fraud Signal", level=2)
doc.add_paragraph(
    "Elapsed hours between account creation and purchase. Distribution summary:"
)
add_table(doc,
    headers=["Metric", "Value"],
    rows=[
        ["Mean",           "1,370 hours (~57 days)"],
        ["Minimum",        "0.0003 hours (~1 minute)"],
        ["25th percentile","607 hours (~25 days)"],
        ["Median",         "1,368 hours (~57 days)"],
    ],
    col_widths=[2.0, 2.5]
)

doc.add_heading("Fraud Rate by Time Since Signup", level=3)
add_table(doc,
    headers=["Time Since Signup", "Fraud Rate"],
    rows=[
        ["< 1 hour",  "99.52% 🚨"],
        ["1 – 6 hours",  "3.33%"],
        ["6 – 24 hours", "4.10%"],
        ["1 – 7 days",   "4.46%"],
        ["> 7 days",     "4.57%"],
    ],
    col_widths=[2.2, 1.5],
    highlight_rows=[0]
)

key_finding = doc.add_paragraph()
shade_paragraph(key_finding, "FFE8E8")
r = key_finding.add_run("★  Key Finding: ")
r.bold = True
r.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)
key_finding.add_run(
    "Transactions placed within 1 hour of account creation are fraudulent 99.52% of the time. "
    "This is a direct observation from the data — not a model prediction. It represents throwaway "
    "accounts created specifically for a one-time fraudulent purchase."
)

doc.add_heading("3.2  Transaction Velocity — tx_count_24h", level=2)
doc.add_paragraph(
    "Cumulative transaction count per user up to each purchase. A burst of transactions "
    "in a short window signals account takeover or credential-stuffing attacks."
)

doc.add_heading("3.3  Temporal Features", level=2)
add_table(doc,
    headers=["Feature", "Fraud Mechanism Captured"],
    rows=[
        ["time_since_signup", "Throwaway accounts, synthetic identities"],
        ["tx_count_24h",      "Account takeover, credential stuffing"],
        ["hour_of_day",       "Off-hours automated attacks"],
        ["day_of_week",       "Weekend/holiday low-coverage windows"],
        ["country",           "Geographic risk concentration"],
    ],
    col_widths=[1.8, 3.5]
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CREDIT CARD
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 4 — Credit Card Data", level=1)

doc.add_heading("4.1  Severe Class Imbalance", level=2)
add_table(doc,
    headers=["Class", "Count", "Percentage"],
    rows=[
        ["Legitimate (0)", "283,253", "99.83%"],
        ["Fraud (1)",           "473",  "0.17%"],
    ],
    col_widths=[1.8, 1.2, 1.2],
    highlight_rows=[1]
)

doc.add_heading("4.2  Card-Testing Pattern in Transaction Amounts", level=2)
add_table(doc,
    headers=["Class", "Mean Amount", "Median Amount"],
    rows=[
        ["Legitimate (0)", "$88.41",  "$22.00"],
        ["Fraud (1)",      "$123.87", "$9.82"],
    ],
    col_widths=[1.8, 1.5, 1.5],
    highlight_rows=[1]
)
doc.add_paragraph(
    "Fraud has a higher mean but much lower median. This is the fingerprint of card testing: "
    "fraudsters validate stolen cards with micro-transactions ($9.82 median), then escalate. "
    "The high mean reflects the larger follow-up purchases."
)

doc.add_heading("4.3  Strongest PCA Features (Correlation with Fraud)", level=2)
add_table(doc,
    headers=["Feature", "|Pearson Correlation with Fraud|"],
    rows=[
        ["V17", "0.3135"],
        ["V14", "0.2934"],
        ["V12", "0.2507"],
        ["V10", "0.2070"],
        ["V16", "0.1872"],
        ["V3",  "0.1823"],
        ["V7",  "0.1723"],
    ],
    col_widths=[1.2, 2.8],
    highlight_rows=[0, 1, 2]
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — PREPROCESSING
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 5 — Preprocessing Pipeline", level=1)

doc.add_heading("The Golden Rule: Split Before You Resample", level=2)
doc.add_paragraph(
    "Applying SMOTE before the train/test split causes data leakage — synthetic test samples "
    "appear in training, making every metric artificially optimistic. Our rule: "
    "stratified 80/20 split first, SMOTE only on the training portion, test set untouched."
)

doc.add_heading("Why SMOTE?", level=2)
add_table(doc,
    headers=["Method", "Mechanism", "Problem"],
    rows=[
        ["Random Oversampling", "Duplicates minority rows",               "Overfitting on exact rows"],
        ["Random Undersampling","Removes majority rows",                  "Discards real data"],
        ["SMOTE (chosen) ✓",   "Interpolates new synthetic minority rows","Slightly slower; best choice"],
    ],
    col_widths=[1.8, 2.0, 2.0],
    highlight_rows=[2]
)

doc.add_heading("Class Distribution Before and After SMOTE", level=2)
add_table(doc,
    headers=["Dataset", "Before SMOTE (train)", "After SMOTE (train)"],
    rows=[
        ["E-commerce",  "Legit: 109,568  /  Fraud: 10,304", "Legit: 109,568  /  Fraud: 109,568 ✓"],
        ["Credit card", "Legit: 226,602  /  Fraud: 374",    "Legit: 226,602  /  Fraud: 226,602 ✓"],
    ],
    col_widths=[1.3, 2.5, 2.5]
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Part 6 — Five Key Findings", level=1)

findings = [
    ("Finding 1 — The 1-Hour Rule",
     "Transactions within 1 hour of signup are fraudulent 99.52% of the time. "
     "Actionable as an immediate rule-based flag with no model required."),
    ("Finding 2 — Geographic Concentration",
     "Luxembourg, Ecuador, Tunisia, Peru, and Bolivia show fraud rates 3–4× the global average. "
     "Country-of-origin is a high-signal, low-cost feature."),
    ("Finding 3 — Direct Traffic Anomaly",
     "Direct-channel users commit fraud at 10.54% vs 8.93% for SEO. Suggests automated "
     "account creation bypassing referral tracking."),
    ("Finding 4 — Card-Testing Signature",
     "Credit card fraud median amount ($9.82) is far below the legitimate median ($22.00). "
     "Classic card-testing behavior pattern confirmed."),
    ("Finding 5 — PCA Feature Hierarchy",
     "V17, V14, V12, V10 are the dominant fraud signals in credit card data. "
     "SHAP will decode their behavioral meaning in Phase 3."),
]
for title, body in findings:
    p = doc.add_paragraph()
    shade_paragraph(p, "F7F9FF")
    run = p.add_run(title + "\n")
    run.bold = True
    run.font.color.rgb = RGBColor(0x0D, 0x6E, 0xFD)
    p.add_run(body)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — WHAT'S NEXT
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("What Comes Next", level=1)

add_table(doc,
    headers=["Phase", "Task", "Primary Metrics"],
    rows=[
        ["Interim 2", "Logistic Regression baseline + XGBoost/LightGBM ensemble", "AUC-PR, F1, Confusion Matrix"],
        ["Final",     "SHAP summary plots, force plots for TP/FP/FN, recommendations", "Feature importance, business impact"],
    ],
    col_widths=[1.2, 3.0, 2.1]
)

doc.add_paragraph(
    "GitHub: https://github.com/maedotamha/Fraud-Cases\n"
    "All three Task 1 notebooks are executed with full outputs."
)

# ── Footer note ──────────────────────────────────────────────────────────────
p = doc.add_paragraph()
r = p.add_run("Built with Python 3.11 · pandas · scikit-learn · imbalanced-learn · matplotlib · seaborn")
r.font.size = Pt(9)
r.font.color.rgb = RGBColor(0x9B, 0x9B, 0x9B)

doc.save("report/interim1_report.docx")
print("Saved: report/interim1_report.docx")
