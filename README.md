# Streaming Subscriber LTV & Retention Intelligence

A production-grade product data science system that computes Incremental Lifetime Value (iLTV) for streaming subscribers using a Netflix-inspired Markov chain methodology, XGBoost churn prediction, and Kaplan-Meier survival analysis.

Live Dashboard: [https://huggingface.co/spaces/Darakhshannazir/Netflix-streaming-subscriber-ltv-dashboard](https://streaming-subscriber-ltv-system-rdphhhwfglfst4egcg6vxa.streamlit.app/)
Live API: https://huggingface.co/spaces/Darakhshannazir/Netflix-streaming-subscriber-ltv-api

---

## What is iLTV?

Standard naive LTV overstates subscriber value because it ignores the counterfactual — revenue earned anyway if the subscriber churned and later rejoined. Inspired by Badri & Tran (Netflix, WWW 22):

iLTV = V(on-service) minus V(counterfactual off-service)

Naive LTV overstates by 1.3x on this dataset, consistent with Netflix's reported 2-3x on real production data.

---

## Architecture

MovieLens 25M
     ↓
Feature engineering (RFM, genre affinity, plan tier, acquisition channel)
     ↓
XGBoost churn model (AUC 0.79) + Kaplan-Meier survival curves + SHAP
     ↓
Markov chain iLTV computation (beta=0.99, T=24 months)
     ↓
FastAPI — Hugging Face Spaces (Docker)
     ↓
Streamlit Dashboard — Hugging Face Spaces (Streamlit)

---

## Model Results

Metric                          Value
XGBoost churn AUC               0.79
Top churn signal                Days since last watch (SHAP 1.11)
iLTV vs naive overstatement     1.3x
Churn rate                      23.2%
Training subscribers            15,998
Markov states                   on-service, off-service-recent, off-service-long

---

## Dashboard Pages

Subscriber Intelligence
- KPIs: active subscribers, MRR, ARPU, avg iLTV, churn probability, revenue at risk
- Subscriber lifecycle funnel
- Markov state distribution
- Kaplan-Meier retention curves by acquisition channel
- SHAP feature importance
- Cohort revenue analysis by plan tier and acquisition channel
- Content genre tenure vs iLTV bubble chart

Lifetime Value Prediction Model
- Live iLTV scorer — adjust subscriber signals, get real-time Markov chain output
- LTV decomposition waterfall chart
- Business unit recommendations per campaign signal

Customer Win-back Intelligence
- Win-back targets ranked by iLTV x p(rejoin)
- Optimal discount tiers calibrated to price elasticity
- Expected monthly revenue recovery by Markov state
- Top genres at risk

---

## Tech Stack

Layer               Technology
Data                MovieLens 25M (20K users sampled)
Churn model         XGBoost, SHAP
Survival analysis   Kaplan-Meier (lifelines)
iLTV computation    Markov chain (numpy)
API                 FastAPI
Dashboard           Streamlit, Plotly
Model storage       Hugging Face Hub
Deployment          Hugging Face Spaces

---

## Run Locally

API
pip install fastapi uvicorn xgboost shap lifelines joblib
uvicorn app:app --reload

Dashboard
pip install streamlit requests plotly pandas numpy
streamlit run dashboard.py

---

## Methodology

Inspired by Badri & Tran, Netflix, WWW 22 — Beyond Customer Lifetime Valuation
https://allentran.github.io/static/bellmania.pdf

---

## Project Structure

01_data_features.ipynb      Data pipeline, feature engineering, Markov iLTV
02_models.ipynb             XGBoost churn model, SHAP, Kaplan-Meier survival
app.py                      FastAPI backend
dashboard.py                Streamlit dashboard
Dockerfile                  HF Spaces Docker config
requirements.txt            API dependencies
requirements-dashboard.txt  Dashboard dependencies
README.md

---

Data: MovieLens 25M. Synthetic billing signals layered on top. No real user data.
