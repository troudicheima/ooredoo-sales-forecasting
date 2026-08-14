# -*- coding: utf-8 -*-
"""
utils/data_loader.py
Fonctions de chargement des données, mises en cache pour ne pas
recharger les fichiers à chaque interaction utilisateur.
"""

import os
import pandas as pd
import streamlit as st

# Dossier racine de l'application (ooredoo-forecast-app/), calculé depuis
# l'emplacement de CE fichier -> fonctionne peu importe le répertoire depuis
# lequel Streamlit a été lancé (important pour le déploiement sur Streamlit
# Community Cloud, qui ne se place pas forcément dans ce sous-dossier).
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_ROOT, "data")


@st.cache_data
def load_series_history():
    """Historique complet (date, region, product_name, quantity_sold, revenue...)."""
    df = pd.read_csv(os.path.join(DATA_DIR, "series_history.csv"), parse_dates=["date"])
    return df


@st.cache_data
def load_latest_snapshot():
    """Dernière ligne connue pour chaque série région/produit (pour la prévision)."""
    df = pd.read_csv(os.path.join(DATA_DIR, "latest_snapshot.csv"), parse_dates=["date"])
    return df


@st.cache_data
def load_full_dataset():
    """Dataset complet (utilisé pour le Dashboard : filtres, agrégats détaillés)."""
    df = pd.read_csv(os.path.join(DATA_DIR, "ooredoo_sales_synthetic_2022_2025.csv"), parse_dates=["date"])
    return df