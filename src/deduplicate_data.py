"""
deduplicate_data.py

PURPOSE
-------
Performs the actual deduplication (not just a test) on a raw KDHS export:
collapses repeated birth-history rows (same CASEID, different PIDX) down
to exactly one row per woman, and saves the result as a new xlsx file.

This step is worth doing regardless of the missing-negative-class issue
(see check_deduplication.py) - once we have the correct IR file, or if
we end up working with any file that has repeated rows per woman for
other reasons, this is a standard, necessary cleaning step: one row per
person is a basic requirement before any modelling can happen.

WHAT THIS DOES NOT DO
----------------------
This does NOT fix the missing never-pregnant-girls problem documented in
diagnose_raw_data.py and check_deduplication.py. That requires the actual
DHS Individual Recode (IR) file. This script only removes duplicate rows
for women who already appear in the file more than once.

USAGE
-----
1. Set RAW_FILE below to the file you want to deduplicate.
2. Run from the project root, with the venv activated:
       python src/deduplicate_data.py
3. Output is saved to: data/processed/<original_name>_removed_duplications.xlsx
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------
# 0. Which raw file to deduplicate - change this line as needed
# ---------------------------------------------------------------------
RAW_FILE = Path("data/raw/KENR8CFL.xlsx")
# RAW_FILE = Path("data/raw/KEGR8CFL.xlsx")   # <- swap to this for the other file

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Could not find {RAW_FILE}. Make sure the raw KDHS export is "
        "saved at this exact path before running this script."
    )

# ---------------------------------------------------------------------
# 1. Build the output path
# ---------------------------------------------------------------------
# e.g. KENR8CFL.xlsx -> KENR8CFL_removed_duplications.xlsx, saved into
# data/processed/ (never data/raw/ - that folder is for untouched
# originals only).
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # create the folder if it somehow doesn't exist
OUTPUT_FILE = OUTPUT_DIR / f"{RAW_FILE.stem}_removed_duplications.xlsx"

print(f"Deduplicating: {RAW_FILE.name}")
print(f"Output will be saved to: {OUTPUT_FILE}\n")

# ---------------------------------------------------------------------
# 2. Load the data
# ---------------------------------------------------------------------
# Same 2-header-row structure as our other scripts:
#   row 1 = DHS variable codes (e.g. 'V012', 'V201')
#   row 2 = human-readable text labels - not needed for analysis, skip it
df = pd.read_excel(
    RAW_FILE,
    sheet_name="Rawdata",
    header=0,
    skiprows=[1],
)

n_rows_before = len(df)
n_women_before = df["CASEID"].nunique()
print(f"Loaded {n_rows_before:,} rows, {n_women_before:,} unique women.\n")

# ---------------------------------------------------------------------
# 3. Deduplicate: keep exactly one row per woman
# ---------------------------------------------------------------------
# Demographic/socioeconomic variables (age, education, wealth, county,
# etc.) are constant for a given woman across her repeated PIDX rows -
# they don't change depending on which birth is being described. So we
# sort by PIDX and keep the FIRST row per CASEID (her PIDX == 1 record),
# which carries her correct person-level values.
df_dedup = df.sort_values("PIDX").drop_duplicates(subset="CASEID", keep="first")

n_rows_after = len(df_dedup)

print("=== DEDUPLICATION RESULT ===")
print(f"Rows before: {n_rows_before:,}")
print(f"Rows after:  {n_rows_after:,}  (should equal {n_women_before:,} unique women)")
print(f"Rows removed: {n_rows_before - n_rows_after:,}\n")

# ---------------------------------------------------------------------
# 4. Save the deduplicated file
# ---------------------------------------------------------------------
df_dedup.to_excel(OUTPUT_FILE, sheet_name="Rawdata", index=False)

print(f"Saved deduplicated file to: {OUTPUT_FILE}")
print(
    "\nReminder: this fixes duplicate rows only. It does NOT add back "
    "women who were never pregnant and therefore never appeared in the "
    "original export - see check_deduplication.py / NOTES.md for that "
    "finding. The correct IR file is still needed for modelling."
)