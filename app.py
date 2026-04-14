# app.py — StreamVault LTV Scoring API
# Mirrors Netflix Metaflow Hosting REST endpoint

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path

# --- Load artifacts ---
BASE = Path(__file__).parent
churn_model   = joblib.load(BASE / 'models' / 'churn_model.pkl')
feature_cols  = joblib.load(BASE / 'models' / 'feature_cols.pkl')
km_curves     = joblib.load(BASE / 'models' / 'km_curves.pkl')
shap_df       = pd.read_csv(BASE / 'models' / 'shap_importance.csv')
subscribers   = pd.read_csv(BASE / 'models' / 'subscriber_features.csv')

with open(BASE / 'models' / 'markov_params.json') as f:
    markov_params = json.load(f)

# --- App ---
app = FastAPI(
    title       = "StreamVault LTV API",
    description = "Netflix-methodology iLTV scoring — Markov chain + XGBoost",
    version     = "1.0.0"
)

# --- Input schema ---
class SubscriberFeatures(BaseModel):
    total_ratings       : float
    avg_rating          : float
    rating_std          : float
    last_active_days    : float
    watch_frequency     : float
    genre_affinity_score: float
    genre_encoded       : int
    plan_encoded        : int
    acq_encoded         : int
    plan_price          : Optional[float] = 15.49

# --- Markov iLTV function ---
def compute_iltv(p_churn: float, p_rejoin: float, price: float) -> dict:
    discount_rate  = markov_params['discount_rate']
    horizon_months = markov_params['horizon_months']
    p_retain       = 1 - p_churn

    # On-service LTV
    ltv_on, p_alive = 0.0, 1.0
    for t in range(1, horizon_months + 1):
        ltv_on  += p_alive * price / (1 + discount_rate) ** t
        p_alive *= p_retain

    # Counterfactual off-service LTV
    ltv_off, p_still_off = 0.0, 1.0
    for t in range(1, horizon_months + 1):
        ltv_off     += p_still_off * p_rejoin * price / (1 + discount_rate) ** t
        p_still_off *= (1 - p_rejoin)

    return {
        'naive_ltv': round(ltv_on, 2),
        'iltv'     : round(max(ltv_on - ltv_off, 0), 2)
    }

# --- Campaign signal logic ---
def get_campaign_signal(churn_prob: float, plan_encoded: int, iltv: float) -> str:
    if churn_prob > 0.6 and iltv > 50:
        return "Win-back discount"
    elif churn_prob > 0.4:
        return "Personalised recommendation"
    elif plan_encoded == 1 and churn_prob < 0.2:
        return "Upsell to Standard"
    elif plan_encoded == 2 and churn_prob < 0.2:
        return "Upsell to Premium"
    elif churn_prob < 0.15:
        return "Loyalty reward"
    else:
        return "Watch reminder"

# --- Markov state ---
def get_markov_state(churn_prob: float, last_active_days: float) -> str:
    if churn_prob < 0.3:
        return "on_service"
    elif last_active_days < 0.16:
        return "off_service_recent"
    else:
        return "off_service_long"

# --- Churn risk label ---
def get_churn_risk(p: float) -> str:
    if p < 0.2:  return "low"
    elif p < 0.5: return "medium"
    else:         return "high"

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok", "model": "StreamVault LTV v1.0"}

@app.post("/score")
def score(sub: SubscriberFeatures):
    try:
        # Build feature vector
        X = pd.DataFrame([[
            sub.total_ratings, sub.avg_rating, sub.rating_std,
            sub.last_active_days, sub.watch_frequency,
            sub.genre_affinity_score, sub.genre_encoded,
            sub.plan_encoded, sub.acq_encoded
        ]], columns=feature_cols)

        # Churn model prediction
        churn_prob = float(churn_model.predict_proba(X)[0][1])

        # p(rejoin) — empirical from genre affinity
        p_rejoin = float(np.clip(0.15 + sub.genre_affinity_score * 0.001, 0.05, 0.45))

        # Markov iLTV
        ltv = compute_iltv(churn_prob, p_rejoin, sub.plan_price)

        # Derived signals
        markov_state    = get_markov_state(churn_prob, sub.last_active_days)
        campaign_signal = get_campaign_signal(churn_prob, sub.plan_encoded, ltv['iltv'])
        churn_risk      = get_churn_risk(churn_prob)

        return {
            "churn_probability" : round(churn_prob, 4),
            "churn_risk"        : churn_risk,
            "iltv"              : ltv['iltv'],
            "naive_ltv"         : ltv['naive_ltv'],
            "markov_state"      : markov_state,
            "campaign_signal"   : campaign_signal,
            "p_rejoin"          : round(p_rejoin, 4)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/winback")
def winback(top_n: int = 20):
    # Filter off-service subscribers
    off_service = subscribers[
        subscribers['markov_state'].isin(['off_service_recent', 'off_service_long'])
    ].copy()

    # Rank by iLTV × p_rejoin — Netflix win-back score
    off_service['winback_score'] = (
        off_service['iltv'] * off_service['p_rejoin']
    ).round(2)

    top = off_service.nlargest(top_n, 'winback_score')[[
        'userId', 'markov_state', 'iltv', 'p_rejoin',
        'winback_score', 'plan_tier', 'top_genre', 'churn_prob'
    ]].round(3)

    return top.to_dict(orient='records')

@app.get("/segments")
def segments():
    summary = subscribers.groupby('markov_state').agg(
        count        = ('userId',    'count'),
        avg_iltv     = ('iltv',      'mean'),
        avg_churn    = ('churn_prob','mean'),
        avg_p_rejoin = ('p_rejoin',  'mean')
    ).round(2).reset_index()

    return summary.to_dict(orient='records')

@app.get("/feature-importance")
def feature_importance():
    return shap_df.to_dict(orient='records')

@app.get("/km-curves")
def km_curves_endpoint():
    return km_curves