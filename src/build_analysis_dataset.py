# build_analysis_dataset.py
# Phase 1: filters to girls 15-19, builds the ever_pregnant target,
# selects the variables needed for modelling, and saves a clean csv
# to data/processed/.

import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/raw/KEIR8CFL.DTA")
OUT_FILE = Path("data/processed/analysis_dataset.csv")

df = pd.read_stata(RAW_FILE, convert_categoricals=False)

# Restrict to adolescent girls
teens = df[(df["v012"] >= 15) & (df["v012"] <= 19)].copy()

# Target: ever pregnant (children ever born, currently pregnant, or
# ever had a terminated pregnancy). None of these are downstream of
# the outcome, so no leakage risk in how the target is built.
teens["ever_pregnant"] = (
    (teens["v201"].fillna(0) > 0) | (teens["v213"] == 1) | (teens["v228"] == 1)
).astype(int)

# v525 (age at first sex) uses DHS special codes: 0 = never had sex
# (not a literal age), 49 = inconsistent response (1 case here).
# Capture "ever had sex" as its own flag BEFORE recoding, since the
# 0 code carries real information that shouldn't just become NaN.
teens["ever_had_sex"] = (~teens["v525"].isin([0])).astype(int)
teens["v525"] = teens["v525"].replace({0: pd.NA, 49: pd.NA})

# Variables needed for modelling, per proposal's six categories
keep_cols = [
    "caseid", "v005", "v021", "v023",           # id + survey design/weight
    "v012", "v024", "v025",                      # demographics
    "v106", "v149", "v190",                      # education / wealth
    "v501", "v525", "ever_had_sex",                # marital status / age at first sex
    "v384a", "v384b", "v384c",                    # media exposure to FP messages
    "v301",                                       # FP knowledge (summary)
    "ever_pregnant",
]
analysis_df = teens[keep_cols].copy()

# Quick missingness check, printed for the record
missing = analysis_df.isna().mean().sort_values(ascending=False)
missing = missing[missing > 0]
print("Missingness by column:")
print(missing if len(missing) else "none")

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
analysis_df.to_csv(OUT_FILE, index=False)

print(f"\nSaved {len(analysis_df):,} rows, {len(keep_cols)} columns to {OUT_FILE}")
print(f"Ever-pregnant rate: {100 * analysis_df['ever_pregnant'].mean():.1f}%")