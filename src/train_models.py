# train_models.py
# Phase 3: trains logistic regression, random forest, XGBoost, and an
# Explainable Boosting Machine, with 5-fold CV on train.csv and a final
# evaluation on test.csv. Saves trained models to outputs/models/, and
# saves the exact feature matrices used so explainability.py (Phase 4)
# can load them directly.

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    average_precision_score,
)
from xgboost import XGBClassifier
from interpret.glassbox import ExplainableBoostingClassifier

TRAIN_FILE = Path("data/processed/train.csv")
TEST_FILE = Path("data/processed/test.csv")
MODEL_DIR = Path("outputs/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

non_feature_cols = ["caseid", "v005", "v021", "v023", "ever_pregnant"]
feature_cols = [c for c in train_df.columns if c not in non_feature_cols]

X_train = train_df[feature_cols]
y_train = train_df["ever_pregnant"]
X_test = test_df[feature_cols]
y_test = test_df["ever_pregnant"]

# Median imputation (age_at_first_sex is NaN for girls who never had
# sex; ever_had_sex already flags this separately). Test set uses
# TRAIN medians to avoid leakage.
X_train = X_train.fillna(X_train.median(numeric_only=True))
X_test = X_test.fillna(X_train.median(numeric_only=True))

pos_rate = y_train.mean()
scale_pos_weight = (1 - pos_rate) / pos_rate

models = {
    "logistic_regression": LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=42
    ),
    "random_forest": RandomForestClassifier(
        class_weight="balanced", n_estimators=300, random_state=42
    ),
    "xgboost": XGBClassifier(
        scale_pos_weight=scale_pos_weight, eval_metric="logloss",
        random_state=42, n_estimators=300,
    ),
    "ebm": ExplainableBoostingClassifier(random_state=42),
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
        "model": name,
        "cv_f1_mean": cv_scores["test_f1"].mean(),
        "cv_pr_auc_mean": cv_scores["test_pr_auc"].mean(),
        "cv_roc_auc_mean": cv_scores["test_roc_auc"].mean(),
        "test_f1": test_f1,
        "test_precision": test_precision,
        "test_recall": test_recall,
        "test_roc_auc": test_roc_auc,
        "test_pr_auc": test_pr_auc,
    })

    joblib.dump(model, MODEL_DIR / f"{name}.joblib")

results_df = pd.DataFrame(results).sort_values("test_pr_auc", ascending=False)
results_df.to_csv(Path("outputs") / "model_comparison.csv", index=False)

print("\n=== Model comparison (sorted by test PR-AUC) ===")
print(results_df.to_string(index=False))

# Save the exact feature matrices used for training/testing, so
# explainability.py (Phase 4) can load them directly without
# re-deriving features itself.
X_train.to_csv("data/processed/X_train_features.csv", index=False)
X_test.to_csv("data/processed/X_test_features.csv", index=False)
print("\nSaved feature matrices to data/processed/X_train_features.csv and X_test_features.csv")