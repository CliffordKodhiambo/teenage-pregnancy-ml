# Interpretable Machine Learning Framework for Teenage Pregnancy Risk (Kenya)

## Overview
This project builds an interpretable machine learning framework to predict
teenage pregnancy risk among girls aged 15-19 in Kenya, using the 2022
Kenya Demographic and Health Survey (KDHS). Beyond prediction, the
framework explains *why* a girl is flagged as high-risk (via SHAP values),
and simulates "what-if" policy scenarios (via counterfactual analysis) -
for example, estimating how risk might shift if secondary school
completion increased in a given county.

The project focuses on a comparative case study between **Samburu County**
(high teenage pregnancy burden) and **Nyeri County** (low burden), while
training models on the full national sample.

## Goal
To help county-level health officers make more informed, data-driven
decisions about where and how to target teenage pregnancy interventions.

## Project Components
1. **Prediction models** - logistic regression, random forest, XGBoost,
   and an Explainable Boosting Machine (EBM)
2. **Explainability layer** - SHAP values, partial dependence plots,
   counterfactual explanations
3. **Decision-support outputs** - county-level risk rankings, an equity
   assessment across socioeconomic/regional subgroups, and policy
   scenario simulation
4. **Prototype dashboard** - the County Adolescent Pregnancy Risk
   Intelligence Dashboard (built with Streamlit)

## Data
Kenya Demographic and Health Survey (KDHS) 2022, Individual Recode (IR)
file, obtained via the DHS Program. Raw data is not committed to this
repository (see `.gitignore`) due to data usage restrictions.

## Project Structure
data/raw/ - original, untouched data (not tracked in git)
data/processed/ - cleaned, analysis-ready data
notebooks/ - exploratory analysis (Jupyter)
src/ - reusable Python scripts
outputs/models/ - saved trained models
outputs/figures/ - saved charts and plots
dashboard/ - Streamlit dashboard prototype
NOTES.md - running log of key decisions and findings

## Status
🚧 In progress. Currently in Phase 1 (data preparation).

## Author
Clifford Kodhiambo
