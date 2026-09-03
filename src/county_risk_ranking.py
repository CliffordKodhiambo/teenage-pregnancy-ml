# county_risk_ranking.py
# Ranks all counties present in the data by mean predicted pregnancy
# risk, using the full-sample model (all teens, not just the sexually
# active subset), since this output is meant to help prioritise WHERE
# to focus interventions across the whole adolescent population.

import pandas as pd
import joblib

COUNTY_NAMES = {
    1: "Mombasa", 2: "Kwale", 3: "Kilifi", 4: "Tana River", 5: "Lamu",
    6: "Taita Taveta", 7: "Garissa", 8: "Wajir", 9: "Mandera", 10: "Marsabit",
    11: "Isiolo", 12: "Meru", 13: "Tharaka-Nithi", 14: "Embu", 15: "Kitui",
    16: "Machakos", 17: "Makueni", 18: "Nyandarua", 19: "Nyeri", 20: "Kirinyaga",
    21: "Murang'a", 22: "Kiambu", 23: "Turkana", 24: "West Pokot", 25: "Samburu",
    26: "Trans Nzoia", 27: "Uasin Gishu", 28: "Elgeyo-Marakwet", 29: "Nandi",
    30: "Baringo", 31: "Laikipia", 32: "Nakuru", 33: "Narok", 34: "Kajiado",
    35: "Kericho", 36: "Bomet", 37: "Kakamega", 38: "Vihiga", 39: "Bungoma",
    40: "Busia", 41: "Siaya", 42: "Kisumu", 43: "Homa Bay", 44: "Migori",
    45: "Kisii", 46: "Nyamira", 47: "Nairobi",
}

xgb = joblib.load("outputs/models/xgboost.joblib")

X_train = pd.read_csv("data/processed/X_train_features.csv")
X_test = pd.read_csv("data/processed/X_test_features.csv")
X_all = pd.concat([X_train, X_test], ignore_index=True)

X_all["predicted_risk"] = xgb.predict_proba(X_all)[:, 1]

ranking = (
    X_all.groupby("v024")
    .agg(n_respondents=("predicted_risk", "size"), mean_predicted_risk=("predicted_risk", "mean"))
    .reset_index()
    .rename(columns={"v024": "county_code"})
)
ranking["county_name"] = ranking["county_code"].map(COUNTY_NAMES)
ranking = ranking.sort_values("mean_predicted_risk", ascending=False)
ranking = ranking[["county_code", "county_name", "n_respondents", "mean_predicted_risk"]]

ranking.to_csv("outputs/county_risk_ranking.csv", index=False)

print("=== Top 10 highest predicted risk counties ===")
print(ranking.head(10).to_string(index=False))
print("\n=== Bottom 10 lowest predicted risk counties ===")
print(ranking.tail(10).to_string(index=False))

# Flag counties with very few respondents, where the ranking is unstable
thin = ranking[ranking["n_respondents"] < 10]
print(f"\n{len(thin)} counties have fewer than 10 adolescent respondents in this dataset "
      f"and should be treated as unstable estimates:")
print(thin.to_string(index=False))

samburu_rank = ranking.reset_index(drop=True)
samburu_rank["rank"] = samburu_rank.index + 1
print("\nSamburu and Nyeri specifically:")
print(samburu_rank[samburu_rank["county_name"].isin(["Samburu", "Nyeri"])].to_string(index=False))

print("\nSaved outputs/county_risk_ranking.csv")