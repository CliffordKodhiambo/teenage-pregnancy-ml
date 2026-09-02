# counterfactual_marriage.py
# Second counterfactual: simulates the effect of delayed marriage, i.e.
# what predicted risk would look like for currently married or
# cohabiting girls if they were instead never married, holding all
# other features fixed. Uses the ebm_subset model, since marital
# status ranked as the top predictor once ever_had_sex was removed.

import pandas as pd
import joblib
import matplotlib.pyplot as plt
from pathlib import Path

SAMBURU_CODE = 25
NYERI_CODE = 19

FIG_DIR = Path("outputs/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

model = joblib.load("outputs/models/ebm_subset.joblib")

X_train = pd.read_csv("data/processed/X_train_subset_features.csv")
X_test = pd.read_csv("data/processed/X_test_subset_features.csv")
X_all = pd.concat([X_train, X_test], ignore_index=True)

X_all["predicted_risk_baseline"] = model.predict_proba(
    X_all.drop(columns=[c for c in ["predicted_risk_baseline"] if c in X_all.columns])
)[:, 1]

# Currently married (marital_1) or living together (marital_2)
currently_married = (X_all["marital_1"] == 1) | (X_all["marital_2"] == 1)

X_cf = X_all.drop(columns=["predicted_risk_baseline"]).copy()
X_cf.loc[currently_married, "marital_0"] = 1
X_cf.loc[currently_married, "marital_1"] = 0
X_cf.loc[currently_married, "marital_2"] = 0
X_cf.loc[currently_married, "marital_4"] = 0
X_cf.loc[currently_married, "marital_5"] = 0

X_all["predicted_risk_counterfactual"] = model.predict_proba(X_cf)[:, 1]
X_all["affected_by_simulation"] = currently_married.values
X_all["risk_change"] = X_all["predicted_risk_counterfactual"] - X_all["predicted_risk_baseline"]


def summarize(df, label):
    n = len(df)
    n_affected = df["affected_by_simulation"].sum()
    print(f"\n{label} (n={n}, {n_affected} currently married/cohabiting)")
    print(f"  Mean predicted risk, baseline:       {df['predicted_risk_baseline'].mean():.3f}")
    print(f"  Mean predicted risk, counterfactual:  {df['predicted_risk_counterfactual'].mean():.3f}")
    print(f"  Mean change (whole group):            {df['risk_change'].mean():+.3f}")
    mean_affected = df[df["affected_by_simulation"]]["risk_change"].mean() if n_affected > 0 else None
    if n_affected > 0:
        print(f"  Mean change (affected girls only):    {mean_affected:+.3f}")
    return {
        "group": label, "n": n, "n_affected": int(n_affected),
        "baseline_risk": df["predicted_risk_baseline"].mean(),
        "counterfactual_risk": df["predicted_risk_counterfactual"].mean(),
        "mean_change_whole_group": df["risk_change"].mean(),
        "mean_change_affected_only": mean_affected,
    }


summary_rows = [
    summarize(X_all, "All sexually active respondents"),
    summarize(X_all[X_all["v024"] == SAMBURU_CODE], "Samburu"),
    summarize(X_all[X_all["v024"] == NYERI_CODE], "Nyeri"),
]
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("outputs/counterfactual_delayed_marriage.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 5))
x = range(len(summary_df))
width = 0.35
ax.bar([i - width/2 for i in x], summary_df["baseline_risk"], width, label="Baseline", color="#1F4E78")
ax.bar([i + width/2 for i in x], summary_df["counterfactual_risk"], width, label="If married/cohabiting -> never married", color="#C0504D")
ax.set_xticks(list(x))
ax.set_xticklabels(summary_df["group"], rotation=15)
ax.set_ylabel("Mean predicted pregnancy risk")
ax.set_title("Counterfactual: Delayed Marriage")
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "counterfactual_delayed_marriage.png", dpi=150)
plt.close()

print("\nSaved outputs/counterfactual_delayed_marriage.csv and outputs/figures/counterfactual_delayed_marriage.png")