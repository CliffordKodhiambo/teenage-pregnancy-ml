# feature_engineering.py
# Phase 2: takes analysis_dataset.csv (Phase 1 output) and produces a
# model-ready feature matrix, plus a stratified 80/20 train/test split.

import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

IN_FILE = Path("data/processed/analysis_dataset.csv")
OUT_DIR = Path("data/processed")

df = pd.read_csv(IN_FILE)

# --- Education: ordinal (0=none ... higher=more), values already
# ordinal-coded by DHS, so kept as-is
df["education"] = df["v106"]

# --- Wealth: DHS wealth index quintile is already ordinal (1-5)
df["wealth_quintile"] = df["v190"]

# --- Residence: binary urban/rural (DHS: 1=urban, 2=rural)
df["urban"] = (df["v025"] == 1).astype(int)

# --- Marital status: few categories, not inherently ordered -> one-hot
marital_dummies = pd.get_dummies(df["v501"], prefix="marital", dtype=int)
df = pd.concat([df, marital_dummies], axis=1)

# --- Age at first sex: keep as numeric (NaN = never had sex or
# inconsistent response, already flagged via ever_had_sex)
df["age_at_first_sex"] = df["v525"]

# --- Media exposure: 3-level category (0=No, 1=Yes, -1=Not administered)
# Encoded as a single ordinal-like column per DHS design intent (this
# is not a true ordinal scale, but the 3-level flag is compact and
# interpretable for SHAP; documented explicitly in the methodology).
for col in ["v384a", "v384b", "v384c"]:
    new_col = col.replace("v384", "heard_fp_") 
    df[new_col] = df[col].fillna(-1).astype(int)

# --- Contraceptive knowledge (v301: 0=none, 2=traditional only, 3=modern)
df["knows_modern_contraception"] = (df["v301"] == 3).astype(int)

# --- Final feature set
feature_cols = [
    "education", "wealth_quintile", "urban", "v024",
    "age_at_first_sex", "ever_had_sex",
    "heard_fp_a", "heard_fp_b", "heard_fp_c",
    "knows_modern_contraception",
] + list(marital_dummies.columns)

model_df = df[["caseid", "v005", "v021", "v023"] + feature_cols + ["ever_pregnant"]]

# --- Stratified 80/20 train-test split on the target
train_df, test_df = train_test_split(
    model_df, test_size=0.2, stratify=model_df["ever_pregnant"], random_state=42
)

train_df.to_csv(OUT_DIR / "train.csv", index=False)
test_df.to_csv(OUT_DIR / "test.csv", index=False)

print(f"Train: {len(train_df):,} rows ({100*train_df['ever_pregnant'].mean():.1f}% pregnant)")
print(f"Test:  {len(test_df):,} rows ({100*test_df['ever_pregnant'].mean():.1f}% pregnant)")
print(f"Features: {feature_cols}")