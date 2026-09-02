# explainability_subset.py
# Global SHAP and Samburu vs Nyeri comparison on the sexually active
# subset model (xgboost_subset), which is the model that actually
# answers the study's policy question, since ever_had_sex cannot
# dominate it. Complements the full-sample explainability.py.

import pandas as pd
import numpy as np
import shap
import joblib
import matplotlib.pyplot as plt
from pathlib import Path

SAMBURU_CODE = 25
NYERI_CODE = 19
FIG_DIR = Path("outputs/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

xgb_sub = joblib.load("outputs/models/xgboost_subset.joblib")

X_train = pd.read_csv("data/processed/X_train_subset_features.csv")
X_test = pd.read_csv("data/processed/X_test_subset_features.csv")
X_all = pd.concat([X_train, X_test], ignore_index=True)

# --- Global SHAP importance ---
explainer = shap.TreeExplainer(xgb_sub)
shap_values = explainer.shap_values(X_all)

mean_abs_shap = pd.DataFrame({
    "feature": X_all.columns,
    "mean_abs_shap": np.abs(shap_values).mean(axis=0),
}).sort_values("mean_abs_shap", ascending=False)

print("=== XGBoost (sexually active subset) SHAP global feature importance ===")
print(mean_abs_shap.to_string(index=False))
mean_abs_shap.to_csv("outputs/subset_xgboost_shap_importance.csv", index=False)

plt.figure(figsize=(8, 6))
shap.summary_plot(shap_values, X_all, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig(FIG_DIR / "subset_xgboost_shap_summary.png", dpi=150)
plt.close()

# --- Samburu vs Nyeri comparison, subset model ---
county = X_all["v024"].values
samburu_mask = county == SAMBURU_CODE
nyeri_mask = county == NYERI_CODE
print(f"\nSamburu (sexually active subset): {samburu_mask.sum()}")
print(f"Nyeri (sexually active subset):   {nyeri_mask.sum()}")

if samburu_mask.sum() > 5 and nyeri_mask.sum() > 5:
    county_compare = pd.DataFrame({
        "feature": X_all.columns,
        "samburu_mean_shap": shap_values[samburu_mask].mean(axis=0),
        "nyeri_mean_shap": shap_values[nyeri_mask].mean(axis=0),
    })
    county_compare["difference"] = county_compare["samburu_mean_shap"] - county_compare["nyeri_mean_shap"]
    county_compare = county_compare.sort_values("difference", key=abs, ascending=False)
    print("\n=== Samburu vs Nyeri: mean SHAP contribution, sexually active subset ===")
    print(county_compare.to_string(index=False))
    county_compare.to_csv("outputs/subset_samburu_nyeri_shap_comparison.csv", index=False)
else:
    print(f"\nToo few respondents in one or both counties within the sexually active "
          f"subset (Samburu={samburu_mask.sum()}, Nyeri={nyeri_mask.sum()}) for a stable "
          f"comparison. Reporting national subset results only.")

print("\nSaved outputs/subset_xgboost_shap_importance.csv, outputs/figures/subset_xgboost_shap_summary.png")