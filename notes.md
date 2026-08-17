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

## 05/08/26 - Attempting deduplication fix
Thought to self that perhaps the existence of duplicate PIDX values is what's causing (or at least significantly contributing) to the imbalance of pregnant against never-pregnant. 
Writing the code...

## Tested deduplication as a possible fix

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

Performed deduplication (does not resolve core issue)

- Wrote and ran src/deduplicate_data.py on KENR8CFL.xlsx. Yet to be committed because computer still running the code.
- Result: 13,184 rows -> 11,195 rows (1,989 duplicate birth-history rows removed), now exactly one row per woman.
- Output saved to data/processed/KENR8CFL_removed_duplications.xlsx. NOT committed to git - still individual-level KDHS data, restricted
  under DHS data usage terms even after deduplication.
- As established in check_deduplication.py: this does not resolve the missing never-pregnant-girls problem. The correct IR file is still
  required before modelling can proceed.



## 12/08/26 — Correct dataset obtained and validated

- Received the DHS document guide listing all available Kenya DHS-8
  recode files. Identified keir8cdt.zip (Individual Recode, Stata
  format) as the correct file - confirmed KENR8CFL and KEGR8CFL were
  actually "Pregnancy and Postnatal Care Recode" and "Pregnancies
  Recode," not the general women's file.
- Extracted keir8cfl.dta and loaded it directly with pandas.read_stata()
  - no dictionary file needed, since .dta is self-describing.
- Validated: 32,156 rows, 32,156 unique women (one row per woman,
  confirmed). 6,404 girls aged 15-19. 86.9% of teens show zero children
  ever born, consistent with known population patterns.
- Derived ever_pregnant target (V201>0 or V213==1 or V228==1): 15.8%
  of teens, consistent with published national statistics.
- Samburu: 114 teen respondents, Nyeri: 76 - workable sample for county
  comparison.
- All required predictor variables confirmed present.
- Closed GitHub issue on missing negative class.
- Data issue fully resolved. Proceeding to Phase 1 (data preparation).


## 17/08/26 — Phase 1 and Phase 2 completed

- Implemented src/build_analysis_dataset.py: filters keir8cfl.dta to 6,404 girls aged 15-19, builds ever_pregnant target from V201/V213/V228, recodes V525 special codes (0 = never had sex, 49 = inconsistent response) into a separate ever_had_sex flag plus clean numeric age, narrows to ~18 relevant columns. Output: data/processed/analysis_dataset.csv.
- Implemented src/feature_engineering.py: encodes analysis_dataset.csv into model-ready features - ordinal education/wealth, binary urban/ rural, one-hot marital status, 3-level media exposure category (No/Yes/Not administered), binary contraceptive knowledge flag. Produces stratified 80/20 train/test split. Output: data/processed/train.csv, data/processed/test.csv.
- Media exposure variables (V384a/b/c) confirmed ~48% missing, consistent with a DHS half-sample question design rather than a data quality issue - treated as a distinct "Not administered" category rather than imputed or dropped.

## 17/08/26 — Clarified relationship between dataset files

- Documented how each processed file relates to the original source (keir8cfl.dta, 32,156 women, 5,925 columns):
  - build_analysis_dataset.py -> analysis_dataset.csv: cleaned but not yet encoded for modelling.
  - feature_engineering.py -> train.csv / test.csv: encoded, model-ready features. These two files are what actually feed the models.
  - generate_demo_workbook.py -> presentation/Raw_and_Cleaned_Full_Dataset.xlsx: a separate, standalone for oral presentation purposes only, not part of the pipeline. Re-applies the same cleaning logic manually against keir8cfl.dta directly. Must be re-run manually if the pipeline scripts' cleaning logic changes.
- Added src/generate_demo_workbook.py to the repo.