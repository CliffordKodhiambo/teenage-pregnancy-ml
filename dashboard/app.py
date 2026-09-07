# app.py
# County Adolescent Pregnancy Risk Intelligence Dashboard (prototype).
# Run from the project root with: streamlit run dashboard/app.py
#
# Four views: county risk ranking, a per-county explainability
# deep-dive, the equity assessment, and an interactive policy
# simulator built on the sexually-active subset model.

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt

st.set_page_config(page_title="County Adolescent Pregnancy Risk Dashboard", layout="wide")

SAMBURU_CODE = 25
NYERI_CODE = 19
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
EDU_LABELS = {0: "None", 1: "Primary", 2: "Secondary", 3: "Higher"}
MARITAL_LABELS = {"marital_0": "Never married", "marital_1": "Married",
                   "marital_2": "Living together", "marital_4": "Divorced/Separated",
                   "marital_5": "Widowed"}


@st.cache_resource
def load_models():
    return {
        "xgboost": joblib.load("outputs/models/xgboost.joblib"),
        "ebm_subset": joblib.load("outputs/models/ebm_subset.joblib"),
        "xgboost_subset": joblib.load("outputs/models/xgboost_subset.joblib"),
    }


@st.cache_data
def load_data():
    X_train = pd.read_csv("data/processed/X_train_features.csv")
    X_test = pd.read_csv("data/processed/X_test_features.csv")
    X_all = pd.concat([X_train, X_test], ignore_index=True)

    Xs_train = pd.read_csv("data/processed/X_train_subset_features.csv")
    Xs_test = pd.read_csv("data/processed/X_test_subset_features.csv")
    X_subset = pd.concat([Xs_train, Xs_test], ignore_index=True)

    ranking = pd.read_csv("outputs/county_risk_ranking.csv")
    ranking = ranking.sort_values("mean_predicted_risk", ascending=False).reset_index(drop=True)
    ranking["rank"] = ranking.index + 1

    equity = pd.read_csv("outputs/equity_assessment.csv")
    return X_all, X_subset, ranking, equity


models = load_models()
X_all, X_subset, ranking, equity = load_data()

st.title("County Adolescent Pregnancy Risk Intelligence Dashboard")
st.caption(
    "Prototype decision-support tool. Predictions reflect statistical association, "
    "not proven causation. Built on the 2022 KDHS Individual Recode."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["County Risk Ranking", "County Deep-Dive", "Equity Assessment", "Policy Simulator"]
)

# ---------------------------------------------------------------------
# TAB 1: County risk ranking
# ---------------------------------------------------------------------
with tab1:
    st.subheader("Predicted adolescent pregnancy risk, by county")
    st.write(
        "Mean predicted risk across all 15-19 year old respondents in each county, "
        "using the full-sample model. Samburu and Nyeri are highlighted as the "
        "study's focus counties."
    )

    display_ranking = ranking.copy()
    display_ranking["highlight"] = display_ranking["county_code"].map(
        lambda c: "Focus county" if c in (SAMBURU_CODE, NYERI_CODE) else ""
    )
    st.dataframe(
        display_ranking[["county_name", "n_respondents", "mean_predicted_risk", "highlight"]]
        .rename(columns={"county_name": "County", "n_respondents": "Respondents",
                          "mean_predicted_risk": "Mean Predicted Risk", "highlight": ""}),
        width='stretch', height=500,
    )
    st.bar_chart(display_ranking.set_index("county_name")["mean_predicted_risk"])

# ---------------------------------------------------------------------
# TAB 2: County deep-dive
# ---------------------------------------------------------------------
with tab2:
    st.subheader("Explain risk for a specific county")
    county_options = ranking.sort_values("county_name")["county_name"].tolist()
    default_idx = county_options.index("Samburu") if "Samburu" in county_options else 0
    selected_county_name = st.selectbox("Select a county", county_options, index=default_idx)
    selected_code = ranking.loc[ranking["county_name"] == selected_county_name, "county_code"].iloc[0]

    county_row = ranking[ranking["county_code"] == selected_code].iloc[0]
    col1, col2 = st.columns(2)
    col1.metric("Mean predicted risk", f"{county_row['mean_predicted_risk']:.2f}")
    col2.metric("Rank (of 47)", f"{int(county_row['rank'])}")

    county_mask = X_all["v024"] == selected_code
    n_in_county = county_mask.sum()

    if n_in_county >= 10:
        explainer = shap.TreeExplainer(models["xgboost"])
        shap_values = explainer.shap_values(X_all[county_mask])
        importance = pd.DataFrame({
            "feature": X_all.columns,
            "mean_shap": shap_values.mean(axis=0),
        }).sort_values("mean_shap", key=abs, ascending=False).head(8)

        fig, ax = plt.subplots(figsize=(7, 4))
        colors = ["#C0504D" if v > 0 else "#4C9F70" for v in importance["mean_shap"]]
        ax.barh(importance["feature"][::-1], importance["mean_shap"][::-1], color=colors[::-1])
        ax.axvline(0, color="grey", linewidth=0.8)
        ax.set_xlabel("Mean SHAP contribution (red = raises risk, green = lowers risk)")
        st.pyplot(fig)
    else:
        st.warning(f"Only {n_in_county} respondents in this county; explanation not shown due to small sample size.")

# ---------------------------------------------------------------------
# TAB 3: Equity assessment
# ---------------------------------------------------------------------
with tab3:
    st.subheader("Model performance across subgroups")
    st.write(
        "Recall (share of actually-pregnant girls the model correctly flags) "
        "should ideally be similar across subgroups. Large gaps indicate the "
        "model may under-serve some groups more than others."
    )
    dimension = st.radio("View by", equity["dimension"].unique(), horizontal=True)
    subset = equity[equity["dimension"] == dimension]
    st.dataframe(
        subset[["group", "n", "actual_pregnancy_rate", "mean_predicted_risk", "precision", "recall", "f1"]],
        width='stretch',
    )
    st.bar_chart(subset.set_index("group")[["recall", "precision"]])

# ---------------------------------------------------------------------
# TAB 4: Policy simulator (counterfactual, interactive)
# ---------------------------------------------------------------------
with tab4:
    st.subheader("What-if policy simulator")
    st.write(
        "Simulates predicted risk for a hypothetical girl, using the model trained "
        "on sexually active respondents (isolates factors beyond sexual activity itself)."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        edu = st.select_slider("Education level", options=[0, 1, 2, 3],
                                format_func=lambda x: EDU_LABELS[x], value=1)
        wealth = st.select_slider("Wealth quintile", options=[1, 2, 3, 4, 5], value=2)
    with col2:
        marital = st.selectbox("Marital status", list(MARITAL_LABELS.keys()),
                                format_func=lambda x: MARITAL_LABELS[x])
        age_first_sex = st.slider("Age at first sex", 10, 19, 16)
    with col3:
        urban = st.checkbox("Urban residence", value=False)
        county_sim = st.selectbox("County", ranking.sort_values("county_name")["county_name"].tolist(),
                                   index=county_options.index("Samburu") if "Samburu" in county_options else 0)

    profile = {c: 0 for c in X_subset.columns}
    profile["education"] = edu
    profile["wealth_quintile"] = wealth
    profile["urban"] = int(urban)
    profile["v024"] = ranking.loc[ranking["county_name"] == county_sim, "county_code"].iloc[0]
    profile["age_at_first_sex"] = age_first_sex
    profile["heard_fp_a"] = 0
    profile["heard_fp_b"] = 0
    profile["heard_fp_c"] = 0
    profile["knows_modern_contraception"] = 0
    profile[marital] = 1

    profile_df = pd.DataFrame([profile])[X_subset.columns]
    risk = models["ebm_subset"].predict_proba(profile_df)[0, 1]

    st.metric("Predicted pregnancy risk for this profile", f"{risk:.1%}")
    st.caption(
        "This reflects a statistical association learned from the data, not a "
        "guaranteed individual outcome. Use to compare scenarios, not to judge a real person."
    )