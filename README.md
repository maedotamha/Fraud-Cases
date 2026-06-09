# Fraud Detection — Adey Innovations Inc.

End-to-end fraud detection system for e-commerce and bank credit card transactions, built for Adey Innovations Inc.

## Project Overview

Two independent pipelines:
- **E-commerce** (`Fraud_Data.csv`): rich behavioral, device, and geolocation features
- **Bank credit cards** (`creditcard.csv`): anonymized PCA features (V1–V28)

Both datasets are highly imbalanced. Models are evaluated on AUC-PR and F1-Score, not accuracy.

## Repository Structure

```
fraud-detection/
├── data/
│   ├── raw/          # Original CSVs (gitignored — add manually)
│   └── processed/    # Cleaned and feature-engineered outputs
├── notebooks/
│   ├── eda-fraud-data.ipynb         # EDA for e-commerce transactions
│   ├── eda-creditcard.ipynb         # EDA for credit card transactions
│   ├── feature-engineering.ipynb   # Feature engineering + preprocessing
│   ├── modeling.ipynb               # Model training and evaluation
│   └── shap-explainability.ipynb   # SHAP analysis and business insights
├── src/              # Reusable utility modules
├── tests/            # Unit tests
├── models/           # Saved model artifacts
├── scripts/          # Standalone scripts
└── requirements.txt
```

## Setup

```bash
# Clone the repo
git clone https://github.com/maedotamha/Fraud-Cases.git
cd Fraud-Cases

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Add raw data (not tracked by git)
# Place Fraud_Data.csv, IpAddress_to_Country.csv, creditcard.csv into data/raw/

# Launch Jupyter
jupyter notebook
```

## Data

| File | Description |
|------|-------------|
| `Fraud_Data.csv` | E-commerce transactions with user/device/behavioral context |
| `IpAddress_to_Country.csv` | IP address range → country mapping |
| `creditcard.csv` | Bank credit card transactions (PCA-anonymized features) |

Raw data files are **not committed** to this repository. Place them in `data/raw/` manually after cloning.

## Key Results

*(Populated after modeling — see `notebooks/modeling.ipynb`)*

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `eda-fraud-data.ipynb` | Univariate/bivariate EDA, IP-to-country mapping, class imbalance |
| `eda-creditcard.ipynb` | EDA on anonymized credit card data |
| `feature-engineering.ipynb` | Time features, velocity, scaling, SMOTE |
| `modeling.ipynb` | Logistic Regression baseline + ensemble models |
| `shap-explainability.ipynb` | SHAP summary plots, force plots, business recommendations |
