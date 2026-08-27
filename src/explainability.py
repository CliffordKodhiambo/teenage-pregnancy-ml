# explainability.py
# Phase 4: explains model predictions two ways - EBM's native additive
# explanations (no approximation needed) and SHAP for XGBoost (the
# strongest black-box model). Also compares feature contributions
# between Samburu and Nyeri to surface county-level differences.

import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
from pathlib import Path

MODEL_DIR = Path("outputs/models")
FIG_DIR = Path("outputs/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

SAMBURU_CODE = 25
NYERI_CODE = 19

X_train = pd.read_csv("data/processed/X_train_features.csv")
X_test = pd.read_csv("data/processed/X_test_features.csv")
test_df = pd.read_csv("data/processed/test.csv")  # has v024 (county) + caseid alongside features

ebm = joblib.load(MODEL_DIR / "ebm.joblib")
xgb = joblib.load(MODEL_DIR / "xgboost.joblib")

# ---------------------------------------------------------------------
# 1. EBM global explanation - each feature's function is exact, not
# approximated, since EBM is additive by construction.
# ---------------------------------------------------------------------
ebm_global = ebm.explain_global()
importances = pd.DataFrame({
    "feature": ebm_global.data()["names"],
    "importance": ebm_global.data()["scores"],
}).sort_values("importance", ascending=False)

print("=== EBM global feature importance (mean absolute contribution) ===")
print(importances.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(importances["feature"][:10][::-1], importances["importance"][:10][::-1], color="#1F4E78")
ax.set_xlabel("Mean absolute contribution to prediction")
ax.set_title("EBM: Top 10 Global Feature Importance")
plt.tight_layout()
plt.savefig(FIG_DIR / "ebm_global_importance.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------
# 2. EBM local explanation - two example respondents, one flagged
# high-risk, one flagged low-risk, from the test set.
# ---------------------------------------------------------------------
proba = ebm.predict_proba(X_test)[:, 1]
high_idx = proba.argmax()
low_idx = proba.argmin()

for label, idx in [("HIGHEST predicted risk", high_idx), ("LOWEST predicted risk", low_idx)]:
    local = ebm.explain_local(X_test.iloc[[idx]], test_df["ever_pregnant"].iloc[[idx]])
    data = local.data(0)
    contrib = pd.DataFrame({
        "feature": data["names"],
        "contribution": data["scores"],
    }).sort_values("contribution", key=abs, ascending=False)
    print(f"\n=== EBM local explanation: respondent with {label} (p={proba[idx]:.3f}) ===")
    print(contrib.head(8).to_string(index=False))

# ---------------------------------------------------------------------
# 3. SHAP for XGBoost - cross-check against a black-box model
# ---------------------------------------------------------------------
explainer = shap.TreeExplainer(xgb)
shap_values = explainer.shap_values(X_test)

mean_abs_shap = pd.DataFrame({
    "feature": X_test.columns,
    "mean_abs_shap": np.abs(shap_values).mean(axis=0),
}).sort_values("mean_abs_shap", ascending=False)

print("\n=== XGBoost SHAP global feature importance ===")
print(mean_abs_shap.to_string(index=False))

plt.figure(figsize=(8, 6))
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig(FIG_DIR / "xgboost_shap_summary.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------
# 4. Samburu vs Nyeri: compare mean SHAP contribution per feature
# ---------------------------------------------------------------------
county = test_df["v024"].values
samburu_mask = county == SAMBURU_CODE
nyeri_mask = county == NYERI_CODE

print(f"\nSamburu test respondents: {samburu_mask.sum()} | Nyeri test respondents: {nyeri_mask.sum()}")

if samburu_mask.sum() > 5 and nyeri_mask.sum() > 5:
    county_compare = pd.DataFrame({
        "feature": X_test.columns,
        "samburu_mean_shap": shap_values[samburu_mask].mean(axis=0),
        "nyeri_mean_shap": shap_values[nyeri_mask].mean(axis=0),
    })
    county_compare["difference"] = county_compare["samburu_mean_shap"] - county_compare["nyeri_mean_shap"]
    county_compare = county_compare.sort_values("difference", key=abs, ascending=False)
    print("\n=== Samburu vs Nyeri: mean SHAP contribution by feature ===")
    print(county_compare.to_string(index=False))
    county_compare.to_csv("outputs/samburu_nyeri_shap_comparison.csv", index=False)
else:
    print("Too few test-set respondents in one or both counties for a stable comparison; "
          "consider running this against the full dataset rather than the test split alone.")

print("\nSaved figures to outputs/figures/, comparison table to outputs/samburu_nyeri_shap_comparison.csv")