# -*- coding: utf-8 -*-
"""
utils/model_utils.py
Chargement du modèle LightGBM sauvegardé + fonction de prédiction.
"""

import json
import joblib
import pandas as pd
import streamlit as st


@st.cache_resource
def load_model():
    return joblib.load("models/lightgbm_model.pkl")


@st.cache_resource
def load_encoders():
    return joblib.load("models/label_encoders.pkl")


@st.cache_data
def load_feature_config():
    with open("models/feature_cols.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_model_metadata():
    with open("models/model_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def predict_next_day(row: pd.Series) -> float:
    """
    Prédit les ventes du jour suivant à partir d'une ligne de données
    (typiquement une ligne de latest_snapshot.csv), en réappliquant
    exactement le même encodage que lors de l'entraînement.
    """
    model = load_model()
    encoders = load_encoders()
    config = load_feature_config()

    row = row.copy()
    for cat_col, encoder in encoders.items():
        value = str(row[cat_col])
        if value in encoder.classes_:
            row[cat_col + "_enc"] = encoder.transform([value])[0]
        else:
            # valeur jamais vue à l'entraînement -> on prend la catégorie la plus fréquente (index 0)
            row[cat_col + "_enc"] = 0

    X = pd.DataFrame([row[config["feature_cols"]]])
    prediction = model.predict(X)[0]
    return max(0.0, float(prediction))