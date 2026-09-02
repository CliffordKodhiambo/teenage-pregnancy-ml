# county_comparison_full.py
# Reruns the Samburu vs Nyeri SHAP comparison from explainability.py,
# but on the full dataset (train + test combined, 6,404 respondents)
# rather than the 1,281-row test split alone, since the county
# subgroups in the test split were too small for a stable estimate
# (23 Samburu, 18 Nyeri).

import pandas as pd
import numpy as np
import shap
import joblib
from pathlib import Path

SAMBURU_CODE = 25
NYERI_CODE = 19

xgb = joblib.load("outputs/models/xgboost.joblib")

X_train = pd.read_csv("data/processed/X_train_features.csv")
X_test = pd.read_csv("data/processed/X_test_features.csv")
X_all = pd.concat([X_train, X_test], ignore_index=True)

county = X_all["v024"].values
samburu_mask = county == SAMBURU_CODE
nyeri_mask = county == NYERI_CODE
print(f"Samburu respondents (full dataset): {samburu_mask.sum()}")
print(f"Nyeri respondents (full dataset):   {nyeri_mask.sum()}")

explainer = shap.TreeExplainer(xgb)
shap_values = explainer.shap_values(X_all)

county_compare = pd.DataFrame({
    "feature": X_all.columns,
    "samburu_mean_shap": shap_values[samburu_mask].mean(axis=0),
    "nyeri_mean_shap": shap_values[nyeri_mask].mean(axis=0),
})
county_compare["difference"] = county_compare["samburu_mean_shap"] - county_compare["nyeri_mean_shap"]
county_compare = county_compare.sort_values("difference", key=abs, ascending=False)

print("\n=== Samburu vs Nyeri: mean SHAP contribution by feature (full dataset, full-sample model) ===")
print(county_compare.to_string(index=False))

county_compare.to_csv("outputs/samburu_nyeri_shap_comparison_full.csv", index=False)
print("\nSaved outputs/samburu_nyeri_shap_comparison_full.csv")