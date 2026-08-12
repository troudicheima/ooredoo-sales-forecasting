# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.theme import (
    apply_theme, render_header, render_kpi_card, render_prediction_card,
    render_badge, style_fig, render_sidebar_footer,
)
from utils.data_loader import load_latest_snapshot, load_series_history
from utils.model_utils import predict_next_day, load_model_metadata

apply_theme(page_title="Prévisions", page_icon="🔮")
render_header(
    title="Prévision des ventes",
    subtitle="Anticipez les ventes futures grâce à l'intelligence artificielle.",
    icon="🔮",
)
render_sidebar_footer()

metadata = load_model_metadata()
st.markdown(
    render_badge(
        f"Modèle LightGBM · validé sur les données à partir du {metadata['split_date']} · "
        f"MAE {metadata['MAE']} · RMSE {metadata['RMSE']} · MAPE {metadata['MAPE_%']}%",
        icon="🧠",
    ),
    unsafe_allow_html=True,
)
st.write("")

snapshot = load_latest_snapshot()
history = load_series_history()

# ---------------------------------------------------------------------
# Zone de sélection
# ---------------------------------------------------------------------
st.markdown('<div class="section-title">🎯 Paramètres de la prévision</div>', unsafe_allow_html=True)
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Région", sorted(snapshot["region"].unique()))
    with col2:
        produits_dispo = sorted(snapshot[snapshot["region"] == region]["product_name"].unique())
        product = st.selectbox("Produit", produits_dispo)

row = snapshot[(snapshot["region"] == region) & (snapshot["product_name"] == product)]

if row.empty:
    st.warning("Aucune donnée disponible pour cette combinaison région / produit.")
    st.stop()

row = row.iloc[0]
last_date = row["date"]
target_date = last_date + pd.Timedelta(days=1)

st.write("")

# ---------------------------------------------------------------------
# Prédiction
# ---------------------------------------------------------------------
generate = st.button("🔮 Générer la prévision", type="primary")

if generate:
    with st.spinner("Calcul de la prévision..."):
        prediction = predict_next_day(row)
    variation = (prediction - row["quantity_sold"]) / max(row["quantity_sold"], 1) * 100
    trend_icon = "📈" if variation >= 0 else "📉"

    col_pred, col_ctx = st.columns([1.3, 1])
    with col_pred:
        st.markdown(
            render_prediction_card(
                label=f"Prévision pour le {target_date.date()}",
                value=f"{prediction:.0f} unités",
                sub=f"{trend_icon} {variation:+.1f}% par rapport au dernier jour connu",
            ),
            unsafe_allow_html=True,
        )
    with col_ctx:
        st.markdown(render_kpi_card("📅", f"{last_date.date()}", "Dernière donnée connue"), unsafe_allow_html=True)
        st.write("")
        st.markdown(render_kpi_card("📊", f"{row['quantity_sold']:.0f} unités", "Ventes du dernier jour connu"), unsafe_allow_html=True)

    st.write("")

# ---------------------------------------------------------------------
# Historique de la série sélectionnée
# ---------------------------------------------------------------------
st.markdown(f'<div class="section-title">📉 Historique — {product} ({region})</div>', unsafe_allow_html=True)
serie = history[(history["region"] == region) & (history["product_name"] == product)].sort_values("date")
fig = px.line(serie, x="date", y="quantity_sold")
fig.update_traces(line_color="#E4032E", line_width=2)
style_fig(fig)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Voir les 30 derniers jours de cette série"):
    st.dataframe(serie.tail(30), use_container_width=True)