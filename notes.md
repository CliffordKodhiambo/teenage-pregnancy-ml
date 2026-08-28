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

## 17/08/26 — Phase 3 completed: model training and comparison

- Implemented src/train_models.py: trained logistic regression, random forest, XGBoost, and an Explainable Boosting Machine on train.csv, with 5-fold stratified cross-validation and class imbalance handled via class weighting (sklearn models) / scale_pos_weight (XGBoost).
- Evaluated all four on the held-out test.csv using F1, precision, recall, ROC-AUC, and PR-AUC (PR-AUC prioritized over ROC-AUC given the imbalanced target, ~15.8% positive rate).
- Results: EBM performed best on both ROC-AUC (0.958) and PR-AUC (0.789), consistent with the proposal's stated preference for interpretability-first models. XGBoost close behind (PR-AUC 0.763). Logistic regression's recall of 1.0 at default threshold is a class-balancing artifact, not a genuinely strong result.
- Identified a methodological issue worth addressing before final write-up: ever_had_sex is one of the strongest predictors, but this is close to tautological (girls who have never had sex are almost definitionally in the "never pregnant" group), not a genuine risk insight. Plan to also report a model restricted to the sexually active subgroup, since that is the more policy-relevant question for county health officers.
- Saved trained models to outputs/models/ (logistic_regression.joblib, random_forest.joblib, xgboost.joblib, ebm.joblib) and comparison table to outputs/model_comparison.csv.


## 26/08/26 — Adopted thesis template; confirmed DSR Type A

- Received the institution's thesis template (Chapters 3-7) and reviewed its structure. Confirmed this is a Design Science Research (DSR)
  format: Chapter 3 (Methodology) is planning-level only, Chapter 4
  (Artefact Design) holds model equations, Chapter 5 (Implementation)
  covers training setup, Chapter 6 (Evaluation) reports results, and
  Chapter 7 concludes.
- Confirmed with supervisor input that this project is Type A (DSR
  building an artefact), since it produces a decision-support framework
  and dashboard, not just a trained model. This means Chapter 4 requires
  numbered design requirements and Chapter 6 must evaluate the artefact
  against them.
- Noted that the existing Chapter 3 draft mixes in content that belongs
  in Chapters 4-6 per this template (model equations, preliminary
  results). Flagged for restructuring once further phases are complete,
  rather than redoing immediately.

## 28/08/26 — Phase 4 (part 1): explainability layer implemented

- Implemented src/explainability.py: EBM native global and local
  explanations (exact, not approximated, since EBM is additive by
  construction), plus SHAP (TreeExplainer) on the XGBoost model as a
  cross-check against a black-box model.
- Global feature importance from both EBM and XGBoost/SHAP agreed
  closely: ever_had_sex dominates by an order of magnitude over every
  other feature in the full-sample model, confirming the concern raised
  in the Methodology (Section 3.11.1).
- Ran a Samburu vs Nyeri comparison of mean SHAP contribution per
  feature. Found meaningful divergence: ever_had_sex has a stronger
  protective effect in Nyeri than Samburu; wealth quintile, marital
  status, and education also diverge between the two counties. Sample
  sizes in this comparison are small (23 Samburu, 18 Nyeri in the test
  split) - flagged to rerun against the full dataset rather than the
  test split alone for a more stable estimate.
- Saved figures to outputs/figures/ (ebm_global_importance.png,
  xgboost_shap_summary.png) and the county comparison table to
  outputs/samburu_nyeri_shap_comparison.csv.
- Updated src/train_models.py to also save data/processed/
  X_train_features.csv and X_test_features.csv, since explainability.py
  depends on the exact feature matrices used in training. train_models.py
  must now be run before explainability.py.

## 28/08/26 — Phase 4 (part 2): sexually active subset model

- Implemented src/train_subset_model.py: trained EBM and XGBoost on the subset of respondents who have ever had sex (1,671 train / 420 test), with ever_had_sex dropped as a feature since it is constant within this subset.
- Pregnancy rate within this subset is 48.5%, much higher than the 15.8% full-sample rate, as expected once the non-sexually-active majority is removed.
- With ever_had_sex no longer able to dominate, the EBM global importance ranking changed substantially: marital status (never married, married) ranked highest, followed by age at first sex, county, wealth quintile, and education. This is the result that directly answers the study's policy question, since these are the factors an intervention could plausibly target among girls already sexually active.
- Model performance on this subset is lower than the full-sample model (EBM ROC-AUC 0.792 vs 0.958 full-sample), which is expected and correct: the task is genuinely harder without the near-tautological predictor, not evidence of a worse model.
- Saved models to outputs/models/ (ebm_subset.joblib, xgboost_subset.joblib), results to outputs/subset_model_comparison.csv, and the feature importance table to outputs/subset_ebm_importance.csv.
- Next: counterfactual policy simulation (e.g. effect of secondary school completion on predicted risk), using the subset model as the basis.