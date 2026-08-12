# -*- coding: utf-8 -*-
"""
utils/data_loader.py
Fonctions de chargement des données, mises en cache pour ne pas
recharger les fichiers à chaque interaction utilisateur.
"""

import pandas as pd
import streamlit as st


@st.cache_data
def load_series_history():
    """Historique complet (date, region, product_name, quantity_sold, revenue...)."""
    df = pd.read_csv("data/series_history.csv", parse_dates=["date"])
    return df


@st.cache_data
def load_latest_snapshot():
    """Dernière ligne connue pour chaque série région/produit (pour la prévision)."""
    df = pd.read_csv("data/latest_snapshot.csv", parse_dates=["date"])
    return df


@st.cache_data
def load_full_dataset():
    """Dataset complet (utilisé pour le Dashboard : filtres, agrégats détaillés)."""
    df = pd.read_csv("data/ooredoo_sales_synthetic_2022_2025.csv", parse_dates=["date"])
    return df