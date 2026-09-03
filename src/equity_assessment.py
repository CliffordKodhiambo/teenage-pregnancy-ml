# equity_assessment.py
# Checks whether the full-sample model performs consistently across
# wealth, residence, and education subgroups, and whether predicted
# risk patterns by subgroup match the known descriptive pattern in the
# data. A model that performs well overall but poorly for a specific
# subgroup would be a real equity concern for a decision-support tool.

import pandas as pd
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score

xgb = joblib.load("outputs/models/xgboost.joblib")

X_test = pd.read_csv("data/processed/X_test_features.csv")
test_df = pd.read_csv("data/processed/test.csv")
y_test = test_df["ever_pregnant"]

X_test["predicted_risk"] = xgb.predict_proba(X_test)[:, 1]
X_test["predicted_class"] = xgb.predict(X_test.drop(columns=["predicted_risk"]))
X_test["actual"] = y_test.values


def subgroup_report(df, group_col, group_labels=None):
    rows = []
    for val, g in df.groupby(group_col):
        if len(g) < 15:
            continue  # too few for a meaningful subgroup metric
        label = group_labels.get(val, val) if group_labels else val
        precision = precision_score(g["actual"], g["predicted_class"], zero_division=0)
        recall = recall_score(g["actual"], g["predicted_class"], zero_division=0)
        f1 = f1_score(g["actual"], g["predicted_class"], zero_division=0)
        rows.append({
            "group": label, "n": len(g),
            "actual_pregnancy_rate": g["actual"].mean(),
            "mean_predicted_risk": g["predicted_risk"].mean(),
            "precision": precision, "recall": recall, "f1": f1,
        })
    return pd.DataFrame(rows)


print("=== By wealth quintile ===")
wealth_report = subgroup_report(X_test, "wealth_quintile")
print(wealth_report.to_string(index=False))

print("\n=== By urban/rural ===")
urban_report = subgroup_report(X_test, "urban", {0: "Rural", 1: "Urban"})
print(urban_report.to_string(index=False))

print("\n=== By education level ===")
edu_report = subgroup_report(X_test, "education", {0: "None", 1: "Primary", 2: "Secondary", 3: "Higher"})
print(edu_report.to_string(index=False))

all_reports = pd.concat([
    wealth_report.assign(dimension="wealth_quintile"),
    urban_report.assign(dimension="urban_rural"),
    edu_report.assign(dimension="education"),
], ignore_index=True)
all_reports.to_csv("outputs/equity_assessment.csv", index=False)

# Flag the largest recall gap within each dimension - the metric most
# relevant to equity here, since a low recall subgroup means the model
# is systematically failing to flag at-risk girls in that group
print("\n=== Recall range within each dimension (equity flag) ===")
for dim, group in all_reports.groupby("dimension"):
    print(f"{dim}: recall ranges from {group['recall'].min():.2f} to {group['recall'].max():.2f}")

print("\nSaved outputs/equity_assessment.csv")