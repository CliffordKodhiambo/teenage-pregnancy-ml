"""
check_deduplication.py

PURPOSE
-------
Tests a specific hypothesis: "if we collapse the repeated birth-history
rows (PIDX 1, 2, 3...) down to one row per woman, does that fix the
'missing never-pregnant girls' problem we found in diagnose_raw_data.py?"

This script does the actual deduplication, then re-checks the same
"never pregnant" presence metric from diagnose_raw_data.py, before vs.
after, so we can see directly whether it changes anything.

BACKGROUND
----------
Both raw files we've been given (KENR8CFL.xlsx, KEGR8CFL.xlsx) have a
PIDX column ("pregnancy/birth index") - meaning the SAME woman appears
on multiple rows, once per birth she's had. A woman with 4 births has
4 rows; a woman with 0 births has 0 rows (she's simply absent).

Deduplicating removes the EXTRA copies of women who appear more than
once - but it cannot create rows for women who never appeared in the
file to begin with. This script proves that concretely with numbers.

USAGE
-----
1. Set RAW_FILE below to point at whichever file you want to test
   (KENR8CFL.xlsx or KEGR8CFL.xlsx) - both should sit in data/raw/.
2. Run from the project root, with the venv activated:
       python src/check_deduplication.py
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------
# 0. Which raw file to test - change this line to try the other file
# ---------------------------------------------------------------------
RAW_FILE = Path("data/raw/KENR8CFL.xlsx")
# RAW_FILE = Path("data/raw/KEGR8CFL.xlsx")   # <- swap to this to test the other file

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Could not find {RAW_FILE}. Make sure the raw KDHS export is "
        "saved at this exact path before running this script."
    )

print(f"Testing deduplication on: {RAW_FILE.name}\n")

# ---------------------------------------------------------------------
# 1. Load the data (same 2-header-row structure as diagnose_raw_data.py)
# ---------------------------------------------------------------------
df = pd.read_excel(
    RAW_FILE,
    sheet_name="Rawdata",
    header=0,       # row 1 = DHS variable codes (e.g. 'V012', 'V201')
    skiprows=[1],   # row 2 = text labels - skip it, keep the data after
)

print(f"Loaded {len(df):,} rows, {df['CASEID'].nunique():,} unique women.\n")

# ---------------------------------------------------------------------
# 2. BEFORE dedup: restrict to teens (15-19), check zero-children rate
# ---------------------------------------------------------------------
teens_before = df[(df["V012"] >= 15) & (df["V012"] <= 19)]

n_rows_before = len(teens_before)
n_women_before = teens_before["CASEID"].nunique()
zero_rows_before = (teens_before["V201"].fillna(0) == 0).sum()

print("=== BEFORE DEDUPLICATION (raw, includes repeated birth rows) ===")
print(f"Teen rows:                {n_rows_before:,}")
print(f"Unique teen women:        {n_women_before:,}")
print(
    f"Rows with 0 children:     {zero_rows_before:,} "
    f"({100 * zero_rows_before / n_rows_before:.1f}% of rows)\n"
)

# ---------------------------------------------------------------------
# 3. Deduplicate: keep exactly one row per woman
# ---------------------------------------------------------------------
# V201, V213, V228, and all the demographic/socioeconomic variables
# (education, wealth, county, etc.) are constant for a given woman -
# they don't change across her different PIDX birth rows. So keeping
# any single row per CASEID (e.g. the first one, PIDX == 1) gives us
# her correct values without losing information.
teens_dedup = teens_before.sort_values("PIDX").drop_duplicates(
    subset="CASEID", keep="first"
)

# ---------------------------------------------------------------------
# 4. AFTER dedup: same checks, now on one-row-per-woman data
# ---------------------------------------------------------------------
n_rows_after = len(teens_dedup)
zero_rows_after = (teens_dedup["V201"].fillna(0) == 0).sum()

print("=== AFTER DEDUPLICATION (one row per woman) ===")
print(f"Rows (= unique women now): {n_rows_after:,}")
print(
    f"Rows with 0 children:      {zero_rows_after:,} "
    f"({100 * zero_rows_after / n_rows_after:.1f}% of rows)\n"
)

# ---------------------------------------------------------------------
# 5. Verdict: did deduplication actually fix the missing negative class?
# ---------------------------------------------------------------------
pct_before = 100 * zero_rows_before / n_rows_before
pct_after = 100 * zero_rows_after / n_rows_after

print("=== VERDICT ===")
print(f"Never-pregnant share BEFORE dedup: {pct_before:.1f}%")
print(f"Never-pregnant share AFTER dedup:  {pct_after:.1f}%")

if pct_after < 20:
    print(
        "\nDeduplication did NOT resolve the missing negative-class problem.\n"
        "This confirms the issue is not duplicate rows - it's that women who\n"
        "were never pregnant are largely absent from this export entirely.\n"
        "Deduplication only removes EXTRA copies of women who already have a\n"
        "row; it cannot create rows for women who were never included.\n"
        "\n"
        "CONCLUSION: we still need the DHS Individual Recode (IR) file,\n"
        "which includes every interviewed woman regardless of pregnancy\n"
        "history."
    )
else:
    print(
        "\nNever-pregnant women are reasonably represented after "
        "deduplication. Worth a closer look to confirm this holds up."
    )