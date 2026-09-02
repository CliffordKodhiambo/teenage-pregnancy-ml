# partial_dependence.py
# Partial dependence for the sexually active subset model. EBM's shape
# functions ARE partial dependence by construction (each feature's
# function shows exactly how the prediction changes as that feature
# varies, holding all others fixed) - no approximation needed, unlike
# PDP for a black-box model.

import joblib
import matplotlib.pyplot as plt
from pathlib import Path

FIG_DIR = Path("outputs/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

ebm = joblib.load("outputs/models/ebm_subset.joblib")
global_exp = ebm.explain_global()
names = global_exp.data()["names"]

# Continuous/ordinal features worth a partial dependence curve;
# one-hot marital dummies are binary and not informative here
target_features = ["age_at_first_sex", "wealth_quintile", "education", "v024"]

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
axes = axes.flatten()

for ax, feat in zip(axes, target_features):
    idx = names.index(feat)
    data = global_exp.data(idx)
    x = data["names"]  # bin edges
    y = data["scores"]  # contribution at each bin
    # x may be bin edges (one longer than y) for continuous features
    x_plot = x[:-1] if len(x) == len(y) + 1 else x
    ax.step(x_plot, y, where="post", color="#1F4E78", linewidth=2)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_title(feat)
    ax.set_xlabel(feat)
    ax.set_ylabel("Contribution to predicted risk (log-odds)")

plt.suptitle("Partial Dependence: Sexually Active Subset Model (EBM)")
plt.tight_layout()
plt.savefig(FIG_DIR / "partial_dependence_subset.png", dpi=150)
plt.close()

print("Saved outputs/figures/partial_dependence_subset.png")

for feat in target_features:
    idx = names.index(feat)
    data = global_exp.data(idx)
    print(f"\n{feat}:")
    x = data["names"]
    y = data["scores"]
    x_plot = x[:-1] if len(x) == len(y) + 1 else x
    for xi, yi in zip(x_plot, y):
        print(f"  {xi}: {yi:+.3f}")