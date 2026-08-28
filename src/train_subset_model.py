# train_subset_model.py
# Supplementary model restricted to girls who have ever had sex, per the
# limitation noted in the Methodology (Section 3.11.1). With ever_had_sex
# held constant, this isolates which OTHER factors predict pregnancy
# among the population interventions can actually reach.

import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score, average_precision_score,
)
from xgboost import XGBClassifier
from interpret.glassbox import ExplainableBoostingClassifier

MODEL_DIR = Path("outputs/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

train_df = pd.read_csv("data/processed/train.csv")
test_df = pd.read_csv("data/processed/test.csv")

# Restrict to sexually active respondents; drop ever_had_sex itself
# since it is now constant (=1) and carries no information here
train_sub = train_df[train_df["ever_had_sex"] == 1].copy()
test_sub = test_df[test_df["ever_had_sex"] == 1].copy()

non_feature_cols = ["caseid", "v005", "v021", "v023", "ever_pregnant", "ever_had_sex"]
feature_cols = [c for c in train_sub.columns if c not in non_feature_cols]

X_train = train_sub[feature_cols].fillna(train_sub[feature_cols].median(numeric_only=True))
y_train = train_sub["ever_pregnant"]
X_test = test_sub[feature_cols].fillna(train_sub[feature_cols].median(numeric_only=True))
y_test = test_sub["ever_pregnant"]

print(f"Sexually active subset - train: {len(train_sub):,} | test: {len(test_sub):,}")
print(f"Pregnancy rate in this subset - train: {100*y_train.mean():.1f}% | test: {100*y_test.mean():.1f}%")

pos_rate = y_train.mean()
scale_pos_weight = (1 - pos_rate) / pos_rate

models = {
    "ebm_subset": ExplainableBoostingClassifier(random_state=42),
    "xgboost_subset": XGBClassifier(
        scale_pos_weight=scale_pos_weight, eval_metric="logloss",
        random_state=42, n_estimators=300,
    ),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = {"f1": "f1", "pr_auc": "average_precision", "roc_auc": "roc_auc"}
results = []

for name, model in models.items():
    print(f"\n=== {name} ===")
    cv_scores = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring)
    print(
        f"CV  F1: {cv_scores['test_f1'].mean():.3f} | "
        f"PR-AUC: {cv_scores['test_pr_auc'].mean():.3f} | "
        f"ROC-AUC: {cv_scores['test_roc_auc'].mean():.3f}"
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    test_f1 = f1_score(y_test, y_pred)
    test_precision = precision_score(y_test, y_pred)
    test_recall = recall_score(y_test, y_pred)
    test_roc_auc = roc_auc_score(y_test, y_proba)
    test_pr_auc = average_precision_score(y_test, y_proba)

    print(
        f"Test  F1: {test_f1:.3f} | Precision: {test_precision:.3f} | "
        f"Recall: {test_recall:.3f} | ROC-AUC: {test_roc_auc:.3f} | PR-AUC: {test_pr_auc:.3f}"
    )

    results.append({
        "model": name, "cv_f1_mean": cv_scores["test_f1"].mean(),
        "cv_pr_auc_mean": cv_scores["test_pr_auc"].mean(),
        "test_f1": test_f1, "test_precision": test_precision,
        "test_recall": test_recall, "test_roc_auc": test_roc_auc, "test_pr_auc": test_pr_auc,
    })
    joblib.dump(model, MODEL_DIR / f"{name}.joblib")

results_df = pd.DataFrame(results)
results_df.to_csv("outputs/subset_model_comparison.csv", index=False)
print("\n=== Subset model comparison ===")
print(results_df.to_string(index=False))

# EBM global importance for this subset - the ranking of interest,
# now that ever_had_sex can no longer dominate
ebm = models["ebm_subset"]
ebm_global = ebm.explain_global()
importances = pd.DataFrame({
    "feature": ebm_global.data()["names"],
    "importance": ebm_global.data()["scores"],
}).sort_values("importance", ascending=False)
print("\n=== EBM global feature importance, sexually active subset ===")
print(importances.to_string(index=False))
importances.to_csv("outputs/subset_ebm_importance.csv", index=False)

X_train.to_csv("data/processed/X_train_subset_features.csv", index=False)
X_test.to_csv("data/processed/X_test_subset_features.csv", index=False)