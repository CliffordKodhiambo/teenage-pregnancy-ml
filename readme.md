# Interpretable Machine Learning for Targeting Teenage Reproductive Health Interventions Using Kenya's 2022 Demographic and Health Survey: A Case Study of Nyeri and Samburu Counties

## Overview

This project develops an interpretable machine learning framework for supporting the targeting of adolescent reproductive health interventions in Kenya using data from the **2022 Kenya Demographic and Health Survey (KDHS)**.

The study focuses on adolescent females aged **15–19 years** and examines characteristics associated with whether a respondent has **ever experienced pregnancy**. The project goes beyond predictive performance by examining how the selected model arrives at its predictions and how the resulting patterns can be translated into county-level decision support.

The national adolescent sample is used for model development, while **Nyeri and Samburu counties** form a comparative case study representing contrasting county contexts.

The study is **cross-sectional and observational**. The models identify statistical associations in the survey data; they do not establish causal relationships between individual characteristics and pregnancy.

---

## Research Question

The project asks, in practical terms:

> **Can interpretable machine learning identify and explain patterns associated with adolescent pregnancy history in Kenya, and can those patterns support more targeted county-level reproductive health interventions?**

The framework is designed to move through four broad stages:

**Prediction → Explanation → Comparative Analysis → Decision Support**

---

## Data

The project uses the **2022 Kenya Demographic and Health Survey (KDHS) Individual Recode (IR) file** in Stata format.

### Source dataset

`KEIR8CFL.DTA`

* 32,156 interviewed women aged 15–49
* One record per woman
* 5,925 variables
* Unique respondent identifier: `CASEID`

The source file is obtained from the DHS Program and is **not included in this repository** because the individual-level survey data are subject to DHS data-use restrictions.

### Analytical population

The national IR file is restricted to respondents aged **15–19**, producing:

* **6,404 adolescent respondents**

The working dataset retains the DHS individual sample weight (`V005`), primary sampling unit (`V021`), and sampling stratum (`V023`) for later design-aware analysis.

---

## Outcome Variable

The primary binary outcome is:

`ever_pregnant`

The outcome is constructed from three DHS indicators:

* children ever born;
* current pregnancy status; and
* history of a terminated pregnancy.

A respondent is classified as `ever_pregnant = 1` if any of these indicators shows that a pregnancy has occurred. Otherwise, the respondent is classified as `0`.

The resulting prevalence of the positive outcome among adolescents is approximately **15.8%**.

This distinction is important: the model estimates the likelihood of belonging to the **observed pregnancy-history group**. It should not be interpreted as a guaranteed prediction of whether an individual will become pregnant in the future.

---

## Why the Individual Recode File Was Used

Two pregnancy-related candidate files were examined before the correct source dataset was identified.

Those files were structured around pregnancy or birth events rather than individual women. Consequently, women could appear in multiple records and respondents who had never experienced pregnancy were substantially underrepresented.

Such a structure is unsuitable for the binary classification task because the model requires both positive and negative examples.

The KDHS Individual Recode file was therefore selected because it contains one record per interviewed woman and includes respondents regardless of pregnancy history.

---

## Feature Engineering

The analysis uses variables representing several domains relevant to adolescent reproductive health.

### Demographic

* Age
* County of residence
* Urban/rural residence

### Socioeconomic

* Highest education level
* Household wealth quintile

### Behavioural and reproductive

* Age at first sexual intercourse
* Whether the respondent has ever had sexual intercourse
* Marital status

### Information exposure

* Family-planning message exposure through radio
* Family-planning message exposure through television
* Family-planning message exposure through print

### Contraceptive knowledge

* Knowledge of a modern contraceptive method

Variables are transformed according to their substantive meaning. Ordinal variables such as education and wealth retain their ordering, while nominal categories such as marital status are one-hot encoded.

Special DHS codes are handled explicitly. For example, `V525 = 0` represents never having had sexual intercourse rather than age zero, while `V525 = 49` represents an inconsistent response rather than a literal age.

The media exposure variables contain substantial missingness because the corresponding questions were administered to only a subset of respondents. These values are therefore treated as a distinct **not administered** category rather than being treated as ordinary missing observations.

---

## Train/Test Design

The 6,404 adolescent respondents are divided using an **80/20 stratified split**:

* Training set: **5,123 respondents**
* Test set: **1,281 respondents**

Stratification preserves the distribution of the binary outcome between the two subsets.

Five-fold stratified cross-validation is then performed on the training data for model evaluation and comparison.

The held-out test set is not used during model training or cross-validation and is reserved for final performance assessment.

---

## Models

Four classification models are compared.

### 1. Logistic Regression

Logistic regression provides an interpretable statistical baseline.

Its coefficients describe how predictors are associated with the log odds of the positive outcome.

It provides a simple reference against which the more flexible machine-learning models can be compared.

### 2. Random Forest

Random Forest combines many decision trees trained using bootstrap samples and randomly selected subsets of features.

It is included as a nonlinear tree-based benchmark for structured survey data.

### 3. XGBoost

XGBoost is a gradient-boosted tree ensemble in which trees are added sequentially to improve the errors of the existing ensemble.

It provides a strong predictive benchmark against which the more interpretable models can be evaluated.

### 4. Explainable Boosting Machine (EBM)

EBM is an interpretable boosting model that learns a separate function for each feature and combines these functions additively.

This allows the contribution of individual features to a prediction to be examined directly.

Because interpretability is central to this research, EBM is the **primary candidate model for the explainability phase**.

---

## Class Imbalance

Only approximately **15.8%** of adolescent respondents are classified as ever pregnant.

The outcome is therefore imbalanced, with the negative class substantially larger than the positive class.

Raw accuracy is consequently not used as the primary performance measure.

Class weighting is applied to logistic regression and random forest. XGBoost uses `scale_pos_weight` to increase the penalty associated with incorrectly classifying the minority positive class.

---

## Model Evaluation

The models are evaluated using:

* **Precision**
* **Recall**
* **F1 score**
* **ROC-AUC**
* **PR-AUC**

### Precision

Precision answers:

> Of the respondents the model flags as belonging to the positive/high-risk group, how many actually belong to the ever-pregnant group?

### Recall

Recall answers:

> Of the respondents who actually belong to the ever-pregnant group, how many does the model identify?

### F1 Score

F1 combines precision and recall into a single measure and is useful when both false positives and false negatives matter.

### ROC-AUC

ROC-AUC measures how well the model separates and ranks positive and negative cases across different classification thresholds.

A ROC-AUC of 0.958, for example, can be interpreted as the model assigning a higher predicted score to a randomly selected ever-pregnant respondent than to a randomly selected never-pregnant respondent approximately 95.8% of the time.

### PR-AUC

PR-AUC summarises the relationship between precision and recall across classification thresholds.

Because the positive class is relatively uncommon in this study, **PR-AUC is treated as the primary model-selection metric**, rather than relying on accuracy or ROC-AUC alone.

---

## Current Model Results

Current held-out test-set results are:

| Model               |        F1 | Precision | Recall |   ROC-AUC |    PR-AUC |
| ------------------- | --------: | --------: | -----: | --------: | --------: |
| **EBM**             | **0.680** | **0.852** |  0.567 | **0.958** | **0.787** |
| XGBoost             |     0.677 |     0.621 |  0.744 |     0.949 |     0.763 |
| Logistic Regression |     0.656 |     0.488 |  1.000 |     0.954 |     0.747 |
| Random Forest       |     0.675 |     0.599 |  0.773 |     0.947 |     0.703 |

EBM currently provides the strongest overall test performance, including the highest F1, precision, ROC-AUC and PR-AUC.

XGBoost and Random Forest achieve higher recall than EBM at the current classification threshold, but with lower precision.

The 100% recall obtained by logistic regression should not be interpreted as superior performance. The current result is associated with the combination of balanced class weighting and the default 0.5 classification threshold, which resulted in all test respondents being classified as positive.

---

## Explainability Layer

The next stage of the project focuses on explaining the selected model rather than treating its predictions as a black box.

### SHAP Analysis

SHAP will be used to examine:

* **Global explanations:** which features contribute most strongly to model predictions across the dataset.
* **Local explanations:** which features contribute to an individual prediction.

### Partial Dependence

Partial dependence plots will be used to examine how changes in important features relate to the model's predicted outcome across the population.

Potential variables of interest include education and household wealth.

### Counterfactual Analysis

Counterfactual analysis will examine hypothetical changes to respondent characteristics and ask:

> **What minimal change in the model inputs would cause the predicted classification or risk score to change?**

These are model-based scenarios and should not be interpreted as causal estimates.

---

## Nyeri and Samburu Case Study

The national adolescent sample is used for model development.

Nyeri and Samburu are then examined as contrasting county cases.

The adolescent sample includes:

* **114 respondents from Samburu**
* **76 respondents from Nyeri**

The correct KDHS county codes are:

* Samburu = **25**
* Nyeri = **19**

The county analysis will examine whether the model's important predictors and explanatory patterns differ between the two settings.

---

## Policy and Decision-Support Layer

The project is designed to translate model outputs into information that can be interpreted by county-level health decision makers.

Planned outputs include:

### County-level risk profiles

Aggregate predicted risk patterns across Kenya's 47 counties, using appropriate weighting where applicable.

### Equity assessment

Examine model performance and predicted risk patterns across:

* wealth quintiles;
* education levels; and
* urban/rural residence.

The purpose is to identify whether the model performs differently across population subgroups or risks systematically under-serving particular groups.

### Policy scenario simulation

Hypothetical interventions can be simulated by modifying selected model inputs and observing the resulting change in predicted risk.

For example, the framework may simulate a scenario in which a specified proportion of respondents in Samburu are hypothetically shifted into the secondary-school-complete category.

These simulations represent **model-based scenarios, not causal impact estimates**.

---

## Important Modelling Limitation

The first round of modelling found that whether a respondent had ever had sexual intercourse was among the strongest predictors of the outcome.

This relationship is largely structural because pregnancy requires sexual intercourse.

Consequently, the strength of this predictor does not necessarily represent a novel behavioural discovery.

A supplementary model restricted to respondents who have had sexual intercourse is planned so that characteristics such as education, wealth, marital status and family-planning information exposure can be examined without the near-definitional sexual-activity relationship dominating the model.

---

## Project Structure

```text
data/
├── raw/                  # Original DHS data (not tracked)
└── processed/            # Cleaned and model-ready data (not tracked)

notebooks/                # Exploratory analysis

src/
├── build_analysis_dataset.py
├── feature_engineering.py
├── validate_ir_data.py
└── other reusable analysis scripts

outputs/
├── models/               # Saved trained models
└── figures/              # Generated charts and plots

dashboard/                # Streamlit dashboard prototype

presentation/             # Presentation-only demonstration materials

NOTES.md                  # Dated record of methodological decisions
```

Individual-level KDHS data and derived datasets are intentionally excluded from version control.

Only the code used to produce the datasets and analyses is tracked.

---

## Dataset Lineage

```text
KEIR8CFL.DTA
     |
     v
build_analysis_dataset.py
     |
     v
analysis_dataset.csv
     |
     v
feature_engineering.py
     |
     +------------------+
     |                  |
     v                  v
 train.csv           test.csv
     |
     v
 model training
     |
     +------------------------------+
     |              |               |
     v              v               v
Logistic        Random Forest     XGBoost
     |
     +------------------------------+
                    |
                    v
                  EBM
                    |
                    v
          Explainability layer
          /        |          \
       SHAP       PDP    Counterfactuals
                    |
                    v
          Nyeri / Samburu analysis
                    |
                    v
          Policy & decision support
                    |
                    v
             Dashboard prototype
```

---

## Reproducibility and Data Security

The project uses version-controlled Python scripts for data preparation, feature engineering and model development.

The individual-level KDHS data are **not committed to GitHub** because they are subject to DHS Program data-use restrictions.

The repository therefore contains the computational pipeline rather than the restricted respondent-level data.

The data dictionary documents the variables used in the analysis and their transformations, while `NOTES.md` records the dated methodological decisions made during development.

---

## Project Status

🚧 **In progress**

### Completed

* Project setup and repository structure
* Identification and validation of the correct KDHS Individual Recode file
* Construction of the adolescent analytical dataset
* Outcome construction
* Data cleaning
* Feature engineering
* Stratified train/test split
* Five-fold cross-validation
* Training of logistic regression
* Training of random forest
* Training of XGBoost
* Training of Explainable Boosting Machine
* Initial model evaluation
* Identification of EBM as the primary candidate for explainability
* Identification of the structural sexual-activity effect

### In progress / planned

* Supplementary modelling among respondents who have had sexual intercourse
* Global and local SHAP analysis
* Partial dependence analysis
* Counterfactual explanations
* Nyeri–Samburu comparative analysis
* Equity assessment
* County-level risk analysis
* Policy scenario simulation
* County Adolescent Pregnancy Risk Intelligence Dashboard
* Final validation and reporting

---

## Author

**Clifford Kodhiambo**
