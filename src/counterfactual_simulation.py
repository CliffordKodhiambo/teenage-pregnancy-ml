# counterfactual_simulation.py
# Simulates the proposal's stated policy question: "what would happen to
# risk if more girls completed secondary school", using the sexually
# active subset model (ebm_subset), since that model isolates the
# policy-relevant risk factors rather than being dominated by
# ever_had_sex. Compares Samburu vs Nyeri.

import pandas as pd
import joblib
import matplotlib.pyplot as plt
from pathlib import Path

SAMBURU_CODE = 25
NYERI_CODE = 19
SECONDARY_CODE = 2  # DHS v106 coding: 0=none, 1=primary, 2=secondary, 3=higher

FIG_DIR = Path("outputs/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

model = joblib.load("outputs/models/ebm_subset.joblib")

X_train = pd.read_csv("data/processed/X_train_subset_features.csv")
X_test = pd.read_csv("data/processed/X_test_subset_features.csv")
X_all = pd.concat([X_train, X_test], ignore_index=True)

# --- Baseline predictions ---
X_all["predicted_risk_baseline"] = model.predict_proba(X_all)[:, 1]

# --- Counterfactual: raise anyone below secondary up to secondary complete ---
X_cf = X_all.drop(columns=["predicted_risk_baseline"]).copy()
below_secondary = X_cf["education"] < SECONDARY_CODE
X_cf.loc[below_secondary, "education"] = SECONDARY_CODE
X_all["predicted_risk_counterfactual"] = model.predict_proba(X_cf)[:, 1]
X_all["affected_by_simulation"] = below_secondary.values

X_all["risk_change"] = X_all["predicted_risk_counterfactual"] - X_all["predicted_risk_baseline"]

# --- Report overall and by county ---
def summarize(df, label):
    n = len(df)
    n_affected = df["affected_by_simulation"].sum()
    print(f"\n{label} (n={n}, {n_affected} below secondary education)")
    print(f"  Mean predicted risk, baseline:       {df['predicted_risk_baseline'].mean():.3f}")
    print(f"  Mean predicted risk, counterfactual:  {df['predicted_risk_counterfactual'].mean():.3f}")
    print(f"  Mean change (whole group):            {df['risk_change'].mean():+.3f}")
    if n_affected > 0:
        affected = df[df["affected_by_simulation"]]
        print(f"  Mean change (affected girls only):    {affected['risk_change'].mean():+.3f}")
    return {
        "group": label, "n": n, "n_affected": int(n_affected),
        "baseline_risk": df["predicted_risk_baseline"].mean(),
        "counterfactual_risk": df["predicted_risk_counterfactual"].mean(),
        "mean_change_whole_group": df["risk_change"].mean(),
        "mean_change_affected_only": df[df["affected_by_simulation"]]["risk_change"].mean() if n_affected > 0 else None,
    }

summary_rows = []
summary_rows.append(summarize(X_all, "All sexually active respondents"))
summary_rows.append(summarize(X_all[X_all["v024"] == SAMBURU_CODE], "Samburu"))
summary_rows.append(summarize(X_all[X_all["v024"] == NYERI_CODE], "Nyeri"))

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("outputs/counterfactual_secondary_education.csv", index=False)

# --- Figure: baseline vs counterfactual mean risk, by group ---
fig, ax = plt.subplots(figsize=(7, 5))
x = range(len(summary_df))
width = 0.35
ax.bar([i - width/2 for i in x], summary_df["baseline_risk"], width, label="Baseline", color="#1F4E78")
ax.bar([i + width/2 for i in x], summary_df["counterfactual_risk"], width, label="If below-secondary raised to secondary+", color="#4C9F70")
ax.set_xticks(list(x))
ax.set_xticklabels(summary_df["group"], rotation=15)
ax.set_ylabel("Mean predicted pregnancy risk")
ax.set_title("Counterfactual: Secondary Education Completion")
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "counterfactual_secondary_education.png", dpi=150)
plt.close()

print("\nSaved outputs/counterfactual_secondary_education.csv and outputs/figures/counterfactual_secondary_education.png")