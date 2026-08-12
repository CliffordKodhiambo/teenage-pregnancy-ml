# validate_ir_data.py
# Validates that keir8cfl.dta is structured correctly (one row per woman)
# and checks the derived pregnancy target for the 15-19 age group.

import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/raw/KEIR8CFL.DTA")

df = pd.read_stata(RAW_FILE, convert_categoricals=False)

print(f"Total rows: {len(df):,}")
print(f"Unique women: {df['caseid'].nunique():,}")

# Restrict to girls aged 15-19
teens = df[(df["v012"] >= 15) & (df["v012"] <= 19)].copy()
print(f"\nTeen rows: {len(teens):,}")

# Check share with zero children ever born (sanity check for negative class)
zero_share = 100 * (teens["v201"].fillna(0) == 0).mean()
print(f"Teens with 0 children ever born: {zero_share:.1f}%")

# Build the ever_pregnant target (V201, V213, V228 combined, per proposal)
teens["ever_pregnant"] = (
    (teens["v201"].fillna(0) > 0) | (teens["v213"] == 1) | (teens["v228"] == 1)
).astype(int)
print(f"Ever-pregnant rate among teens: {100 * teens['ever_pregnant'].mean():.1f}%")

# County counts for Samburu (25) and Nyeri (19)
county_counts = teens["v024"].value_counts()
print(f"\nSamburu teens: {county_counts.get(25, 0)}")
print(f"Nyeri teens: {county_counts.get(19, 0)}")

# Confirm key predictor variables are present
required_vars = ["v106", "v149", "v190", "v025", "v501", "v525",
                  "v384a", "v384b", "v384c", "v005", "v021", "v023"]
missing = [v for v in required_vars if v not in df.columns]
print(f"\nMissing predictor variables: {missing if missing else 'none'}")