# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from utils.theme import apply_theme, render_header, render_kpi_card, render_sidebar_footer
from utils.data_loader import load_full_dataset
from utils.model_utils import load_model_metadata

apply_theme(page_title="Accueil", page_icon="📡")

render_header(
    title="Ooredoo Sales Intelligence",
    subtitle="Plateforme de prévision et d'analyse des ventes télécoms, pilotée par l'intelligence artificielle.",
    icon="📡",
)

st.markdown(
    """
    <div class="section-card">
        <p style="margin:0; font-size:14.5px; color:#374151; line-height:1.7;">
        Utilisez le menu à gauche pour naviguer :<br><br>
        📊&nbsp;&nbsp;<b>Dashboard</b> — vue d'ensemble analytique des ventes historiques (KPIs, tendances, saisonnalité)<br>
        🔮&nbsp;&nbsp;<b>Prévisions</b> — prédiction des ventes du lendemain par région et par produit (modèle LightGBM)<br>
        🤖&nbsp;&nbsp;<b>Assistant IA</b> — posez des questions en langage naturel et générez des rapports (RAG)
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    df = load_full_dataset()
    metadata = load_model_metadata()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_kpi_card("🗂️", f"{len(df):,}".replace(",", " "), "Lignes dans le dataset"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_kpi_card("📅", f"{df['date'].min().year}–{df['date'].max().year}", "Période couverte"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_kpi_card("💰", f"{df['revenue'].sum():,.0f}".replace(",", " ") + " DT", "Chiffre d'affaires total"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_kpi_card("🎯", f"{metadata['MAPE_%']:.1f} %", "MAPE du modèle (validation)"), unsafe_allow_html=True)

except FileNotFoundError as e:
    st.warning(
        "⚠️ Certains fichiers de données ou de modèle sont introuvables. "
        "Avez-vous bien exécuté `python train_and_save_model.py` avant de lancer l'application ?\n\n"
        f"Détail : {e}"
    )

render_sidebar_footer()