# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.theme import apply_theme, render_header, render_kpi_card, style_fig, render_sidebar_footer
from utils.data_loader import load_full_dataset

apply_theme(page_title="Dashboard", page_icon="📊")
render_header(
    title="Dashboard",
    subtitle="Vue d'ensemble analytique des ventes historiques : tendances, saisonnalité, répartition.",
    icon="📊",
)

df = load_full_dataset()

# ---------------------------------------------------------------------
# Filtres (barre latérale)
# ---------------------------------------------------------------------
st.sidebar.markdown("### 🔎 Filtres")

regions = st.sidebar.multiselect(
    "Région(s)", sorted(df["region"].unique()), default=sorted(df["region"].unique())
)
categories = st.sidebar.multiselect(
    "Catégorie(s) de produit", sorted(df["product_category"].unique()),
    default=sorted(df["product_category"].unique())
)
date_range = st.sidebar.date_input(
    "Période",
    value=(df["date"].min(), df["date"].max()),
    min_value=df["date"].min(),
    max_value=df["date"].max(),
)

# Sécurité : tant que l'utilisateur n'a cliqué que sur UNE seule date dans le
# calendrier (avant de choisir la date de fin), date_range ne contient qu'une
# seule valeur -> on retombe temporairement sur la période complète pour
# éviter une erreur, le temps que l'utilisateur termine sa sélection.
if len(date_range) != 2:
    st.sidebar.info("Sélectionnez une date de fin pour appliquer le filtre de période.")
    date_start, date_end = df["date"].min(), df["date"].max()
else:
    date_start, date_end = date_range

render_sidebar_footer()

mask = (
    df["region"].isin(regions)
    & df["product_category"].isin(categories)
    & (df["date"] >= pd.Timestamp(date_start))
    & (df["date"] <= pd.Timestamp(date_end))
)
filtered = df[mask]

if filtered.empty:
    st.warning("Aucune donnée pour cette combinaison de filtres.")
    st.stop()

n_years_selected = filtered["year"].nunique()

# ---------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(render_kpi_card("📦", f"{filtered['quantity_sold'].sum():,.0f}".replace(",", " "), "Unités vendues"), unsafe_allow_html=True)
with col2:
    st.markdown(render_kpi_card("💰", f"{filtered['revenue'].sum():,.0f}".replace(",", " ") + " DT", "Chiffre d'affaires"), unsafe_allow_html=True)
with col3:
    st.markdown(render_kpi_card("💵", f"{filtered['unit_price'].mean():.2f} DT", "Prix moyen"), unsafe_allow_html=True)
with col4:
    st.markdown(render_kpi_card("⭐", f"{filtered['customer_satisfaction'].mean():.2f} / 5", "Satisfaction client moyenne"), unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------------
# Évolution temporelle
# ---------------------------------------------------------------------
st.markdown('<div class="section-title">📈 Évolution des ventes dans le temps</div>', unsafe_allow_html=True)
daily = filtered.groupby("date").agg(quantity_sold=("quantity_sold", "sum")).reset_index()
fig_trend = px.line(daily, x="date", y="quantity_sold")
fig_trend.update_traces(line_color="#E4032E", line_width=2.2)
style_fig(fig_trend)
st.plotly_chart(fig_trend, use_container_width=True)

# ---------------------------------------------------------------------
# Répartition par catégorie / région
# ---------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-title">🧩 Répartition par catégorie de produit</div>', unsafe_allow_html=True)
    cat_data = filtered.groupby("product_category")["quantity_sold"].sum().reset_index()
    fig_cat = px.pie(cat_data, names="product_category", values="quantity_sold", hole=0.55)
    style_fig(fig_cat)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">🗺️ Chiffre d\'affaires par région</div>', unsafe_allow_html=True)
    region_data = filtered.groupby("region")["revenue"].sum().sort_values(ascending=False).reset_index()
    fig_region = px.bar(region_data, x="region", y="revenue")
    fig_region.update_traces(marker_color="#E4032E")
    style_fig(fig_region)
    st.plotly_chart(fig_region, use_container_width=True)

# ---------------------------------------------------------------------
# Migration technologique
# ---------------------------------------------------------------------
st.markdown('<div class="section-title">📶 Évolution de la part de marché par technologie</div>', unsafe_allow_html=True)
if n_years_selected < 2:
    st.info(
        "ℹ️ Ce graphique compare les années entre elles — sélectionnez une période "
        "couvrant au moins 2 années civiles pour voir une évolution significative."
    )
tech_yearly = filtered.groupby(["year", "technology"])["quantity_sold"].sum().reset_index()
fig_tech = px.line(tech_yearly, x="year", y="quantity_sold", color="technology", markers=True)
style_fig(fig_tech)
st.plotly_chart(fig_tech, use_container_width=True)

# ---------------------------------------------------------------------
# Table détaillée
# ---------------------------------------------------------------------
with st.expander("📋 Voir les données détaillées"):
    st.dataframe(filtered.head(500), use_container_width=True)