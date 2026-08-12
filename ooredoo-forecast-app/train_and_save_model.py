# -*- coding: utf-8 -*-
"""
train_and_save_model.py

Ce script :
1. Charge le dataset de ventes
2. Ré-entraîne le modèle LightGBM (meilleur modèle identifié dans le notebook)
   sur l'intégralité des données disponibles
3. Sauvegarde tout ce dont l'application Streamlit a besoin :
   - le modèle entraîné (models/lightgbm_model.pkl)
   - les encodeurs de variables catégorielles (models/label_encoders.pkl)
   - la liste des colonnes attendues, dans l'ordre (models/feature_cols.json)
   - les métriques de validation du modèle (models/model_metadata.json)
   - un instantané des dernières valeurs connues par série région/produit
     (data/latest_snapshot.csv) -> utilisé par l'app pour prédire "demain"
   - l'historique complet agrégé par série (data/series_history.csv)
     -> utilisé par l'app pour tracer les courbes

À exécuter UNE FOIS (puis à ré-exécuter périodiquement pour ré-entraîner
avec des données plus récentes) depuis le dossier racine du projet :

    python train_and_save_model.py
"""

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb

CSV_PATH = "data/ooredoo_sales_synthetic_2022_2025.csv"
MODELS_DIR = "models"
DATA_DIR = "data"

CAT_COLS = [
    "region", "governorate", "city", "sales_channel", "customer_type",
    "product_category", "product_name", "technology", "offer_type",
    "payment_method", "network_usage_level", "weather", "campaign_name",
]

NUM_COLS = [
    "year", "month", "week", "day", "weekend", "quarter", "promotion",
    "promotion_discount", "unit_price", "quantity_sold", "stock_available",
    "competitor_campaign", "public_holiday", "school_holiday", "ramadan",
    "eid", "temperature", "unemployment_index", "inflation_index",
    "fuel_price", "customer_satisfaction", "complaints", "churn_rate",
    "active_users", "previous_day_sales", "previous_week_sales",
    "moving_average_7", "moving_average_30",
]

TARGET_COL = "target_sales_next_day"


def mape_score(y_true, y_pred):
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def main():
    print("Chargement des données...")
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df = df.sort_values(["region", "product_name", "date"]).reset_index(drop=True)
    print(f"  -> {len(df)} lignes chargées")

    # -----------------------------------------------------------------
    # Encodage des variables catégorielles (on sauvegarde les encoders)
    # -----------------------------------------------------------------
    print("Encodage des variables catégorielles...")
    label_encoders = {}
    for c in CAT_COLS:
        df[c] = df[c].astype(str).fillna("Inconnu")
        le = LabelEncoder()
        df[c + "_enc"] = le.fit_transform(df[c])
        label_encoders[c] = le

    feature_cols = [c + "_enc" for c in CAT_COLS] + NUM_COLS

    # -----------------------------------------------------------------
    # Split chronologique 80/20 pour mesurer la performance réelle
    # -----------------------------------------------------------------
    data_ml = df.dropna(subset=[TARGET_COL] + feature_cols).copy()
    all_dates = np.sort(data_ml["date"].unique())
    split_idx = int(len(all_dates) * 0.8)
    split_date = pd.Timestamp(all_dates[split_idx])

    train = data_ml[data_ml["date"] < split_date]
    test = data_ml[data_ml["date"] >= split_date]
    print(f"Entraînement : {len(train)} lignes | Test : {len(test)} lignes "
          f"(coupure au {split_date.date()})")

    X_train, y_train = train[feature_cols], train[TARGET_COL]
    X_test, y_test = test[feature_cols], test[TARGET_COL]

    # -----------------------------------------------------------------
    # Entraînement du modèle de validation (pour mesurer la performance)
    # -----------------------------------------------------------------
    print("Entraînement du modèle de validation (80/20)...")
    model_val = lgb.LGBMRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, n_jobs=-1,
        random_state=42, verbosity=-1,
    )
    model_val.fit(X_train, y_train)
    pred = model_val.predict(X_test)

    metrics = {
        "MAE": round(mean_absolute_error(y_test, pred), 2),
        "RMSE": round(mean_squared_error(y_test, pred) ** 0.5, 2),
        "MAPE_%": round(mape_score(y_test, pred), 2),
        "split_date": str(split_date.date()),
        "n_train": len(train),
        "n_test": len(test),
    }
    print("Métriques de validation :", metrics)

    # -----------------------------------------------------------------
    # Ré-entraînement FINAL sur 100% des données (pour la production)
    # -----------------------------------------------------------------
    print("Ré-entraînement final sur toutes les données disponibles...")
    X_all, y_all = data_ml[feature_cols], data_ml[TARGET_COL]
    model_final = lgb.LGBMRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, n_jobs=-1,
        random_state=42, verbosity=-1,
    )
    model_final.fit(X_all, y_all)

    # -----------------------------------------------------------------
    # Sauvegardes
    # -----------------------------------------------------------------
    print("Sauvegarde du modèle et des artefacts...")
    joblib.dump(model_final, f"{MODELS_DIR}/lightgbm_model.pkl")
    joblib.dump(label_encoders, f"{MODELS_DIR}/label_encoders.pkl")

    with open(f"{MODELS_DIR}/feature_cols.json", "w", encoding="utf-8") as f:
        json.dump({"cat_cols": CAT_COLS, "num_cols": NUM_COLS,
                   "feature_cols": feature_cols, "target_col": TARGET_COL}, f,
                  ensure_ascii=False, indent=2)

    with open(f"{MODELS_DIR}/model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # -----------------------------------------------------------------
    # Instantané des dernières valeurs connues par série (region+produit)
    # -> utilisé par Streamlit pour proposer une prédiction "demain"
    #    sans avoir à recalculer les lags depuis zéro
    # -----------------------------------------------------------------
    latest_snapshot = (
        df.sort_values("date")
          .groupby(["region", "product_name"])
          .tail(1)
          .reset_index(drop=True)
    )
    latest_snapshot.to_csv(f"{DATA_DIR}/latest_snapshot.csv", index=False)

    # -----------------------------------------------------------------
    # Historique agrégé par série -> pour tracer les courbes dans l'app
    # -----------------------------------------------------------------
    series_history = df[["date", "region", "product_name", "product_category",
                          "quantity_sold", "revenue", "unit_price"]].copy()
    series_history.to_csv(f"{DATA_DIR}/series_history.csv", index=False)

    print("\nTerminé ! Fichiers créés :")
    print(f"  - {MODELS_DIR}/lightgbm_model.pkl")
    print(f"  - {MODELS_DIR}/label_encoders.pkl")
    print(f"  - {MODELS_DIR}/feature_cols.json")
    print(f"  - {MODELS_DIR}/model_metadata.json")
    print(f"  - {DATA_DIR}/latest_snapshot.csv")
    print(f"  - {DATA_DIR}/series_history.csv")


if __name__ == "__main__":
    main()