# Project Notes

A running log of key decisions, findings, and open questions during this project.

---

## 31/07/26 - Raw data structure issue identified

- Received `KENR8CFL.xlsx` as the raw KDHS dataset.
- Ran `src/diagnose_raw_data.py` to validate structure before cleaning.
- **Finding:** file contains 13,184 rows but only 11,195 unique women (CASEID).
  Column `PIDX` ("pregnancy column number") confirms the file is structured
  one row per PREGNANCY/BIRTH, not one row per woman.
- **Finding:** only ~1.6% of rows (5.2% among girls 15-19) show zero children
  ever born — meaning women who were never pregnant are almost entirely
  absent from this export.
- **Implication:** this file is unsuitable for a pregnancy-risk classifier,
  since there is effectively no "never pregnant" class to learn from.
- **Also found:** `V304` (contraceptive knowledge), listed in our own
  variable dictionary (Sheet1), does not exist in this export.
- **Decision:** request the DHS Individual Recode (IR) file instead
  (one row per interviewed woman, all pregnancy statuses included).

## 04/08/26 - Second raw file also unsuitable

- Received KEGR8CFL.xlsx as a second candidate raw file.
- Same structural issue as KENR8CFL.xlsx, at larger scale: 82,687 rows,
  only 23,601 unique women, PIDX values exceeding 10 (one row per birth
  event). Only 0.42% of rows (4.9% of teen rows) show zero children ever
  born.
- Checked DHS's official file-naming documentation: valid DHS dataset-type
  codes are HR, PR, IR, MR, CR, BR, KR only. "NR" and "GR" are not
  official DHS codes - both files provided appear to be non-standard,
  flattened exports of the birth-history section.
- Confirmed requirement: need the actual Individual Recode (IR) file,
  filename pattern KEIR8xFL - one row per woman, birth history stored as
  wide columns, not repeated rows.
- Still pending: request correct file from DHS Program.

## 05/08/26 - Attempting deduplication
Figured that perhaps the existence of duplicate PIDX values is what's causing (or at least significantly contributing) to the imbalance of pregnant against never-pregnant. 
Writing the code...

## 2026-08-05 — Tested deduplication as a possible fix

- Hypothesis: collapsing repeated PIDX (birth-history) rows into one row
  per woman might resolve the missing never-pregnant-girls problem.
- Wrote src/check_deduplication.py to test this directly on KENR8CFL.xlsx.
- Result: never-pregnant share among teens was 5.2% before deduplication,
  4.6% after - essentially unchanged.
- Conclusion: deduplication only removes EXTRA rows for women who already
  appear in the file; it cannot create rows for women who were never
  included in the export at all. The missing negative class is a data
  availability problem, not a duplication problem.
- Still need: the DHS Individual Recode (IR) file (KEIR8xFL).
